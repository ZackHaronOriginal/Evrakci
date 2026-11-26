"""R3 Şablonlar proposals (Q-14): whole-template commands (Ş-1), draw mode (Ş-2) and the rest.
Synthetic data only."""

import json

import pytest
from fakes import make_pdf, qr_page, text_page
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLabel, QPushButton

from evrakci.pipeline.ocr.engine import Reading
from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.ui.main_window import MainWindow
from evrakci.ui.sablon_nav import USER


class FakeEngine:
    name = "sahte"

    def available(self):
        return None

    def read_region(self, image):
        return Reading("48213", 0.95)


def _window(qtbot, tmp_path, job=True):
    store = JobStore(tmp_path / "jobs")
    templates = TemplateStore(tmp_path / "tpl")
    made = templates.create("Faaliyet belgesi")
    made.add_variable("Firma", required=True)
    made.add_variable("Sicil_No")
    templates.save(made)
    window = MainWindow(store, templates, settings_path=tmp_path / "ayar.json")
    qtbot.addWidget(window)
    window.sablon.engine = FakeEngine
    if job:
        pdf = make_pdf(tmp_path / "t.pdf", [text_page(), qr_page(), text_page()])
        with qtbot.waitSignal(window.yukle.job_opened, timeout=20000):
            window.yukle.create_job([pdf], "Kasım")
    window.resize(1366, 768)
    window.show()
    window.show_tab("sablonlar")
    window.sablon.attach(window)
    return window, made


@pytest.fixture
def win(qtbot, tmp_path):
    window, made = _window(qtbot, tmp_path)
    screen = window.sablon
    qtbot.waitUntil(lambda: screen._read_task is None, timeout=15000)
    screen.select_variable("Firma")
    screen.set_example(1)
    screen.add_box((20.0, 30.0, 80.0, 40.0))
    qtbot.waitUntil(lambda: screen._read_task is None, timeout=15000)
    screen.flush_save()
    return window, made


def _names(screen):
    return [screen.templates.item(r).text() for r in range(screen.templates.count())]


# -- Ş-1 -------------------------------------------------------------------------------------
def test_template_commands_are_in_menus_and_the_row_menu(win):
    window, _ = win
    registry = window.registry
    for action_id in ("sablon_adlandir", "sablon_cogalt", "sablon_sil", "sablon_disa",
                      "sablon_ice"):
        assert registry.is_enabled(f"sablonlar.{action_id}"), action_id
    from evrakci.ui.sablon_files import TEMPLATE_MENU

    assert all(i is None or i.startswith("sablonlar.sablon_") for i in TEMPLATE_MENU)


def test_rename_is_one_undoable_step_and_the_list_follows(win):
    window, made = win
    screen = window.sablon
    screen.rename_template("Beyan")
    assert screen.template.name == "Beyan"
    assert screen.store.load(made.id).name == "Beyan"
    assert _names(screen) == ["Beyan"]
    screen.undo_stack.undo()
    assert screen.store.load(made.id).name == "Faaliyet belgesi"
    for bad in ("", "a{b}", "x" * 3000, "a\x00b"):
        screen.rename_template(bad)
    assert screen.store.load(made.id).name == "Faaliyet belgesi"
    assert screen.message.text() == "Şablon adı geçersiz."


def test_copy_makes_a_new_file_with_the_same_content_and_opens_it(win):
    window, made = win
    screen = window.sablon
    before = screen.store.raw(made.id)
    screen.copy_template()
    assert screen.template.id != made.id
    assert screen.template.name == "Faaliyet belgesi (kopya)"
    assert [v.name for v in screen.template.variables] == ["Firma", "Sicil_No"]
    assert screen.template.variable("Firma").sections[0].box_mm == (20.0, 30.0, 80.0, 40.0)
    assert screen.store.raw(made.id) == before  # the original is untouched
    assert len(_names(screen)) == 2 and screen.undo_stack.count() == 0


def test_delete_goes_and_geri_al_brings_back_the_exact_bytes(qtbot, win):
    window, made = win
    screen = window.sablon
    screen.copy_template()  # a second template so the screen is not left empty
    first = screen.store.root / f"{made.id}.json"
    before = first.read_bytes()
    screen.templates.setCurrentRow(next(r for r in range(screen.templates.count())
                                        if screen.templates.item(r).data(USER) == made.id))
    assert screen.template.id == made.id
    screen.delete_template()
    assert not first.exists()
    assert screen.template is not None and screen.template.id != made.id
    assert "Faaliyet belgesi" not in _names(screen)
    toast = window.toaster._current
    assert "“Faaliyet belgesi” şablonu silindi." in [x.text() for x in toast.findChildren(QLabel)]
    undo = next(b for b in toast.findChildren(QPushButton) if b.text() == "Geri al")
    undo.click()  # the toast's Geri al
    assert first.read_bytes() == before
    assert screen.template.id == made.id
    assert not list(screen.store.root.glob(".sablon-*.tmp"))


def test_deleting_the_only_template_shows_the_empty_screen_and_undo_returns(win):
    window, made = win
    screen = window.sablon
    before = screen.store.raw(made.id)
    screen.delete_template()
    assert screen.template is None and screen.templates.count() == 0
    screen._restore_deleted(made.id, before)
    assert screen.template.id == made.id and screen.store.raw(made.id) == before


def test_restore_never_writes_over_an_existing_file(win):
    from evrakci.pipeline.templates.model import TemplateError

    window, made = win
    store = window.sablon.store
    with pytest.raises(TemplateError):
        store.restore(made.id, b"{}")
    assert json.loads(store.raw(made.id))["name"] == "Faaliyet belgesi"


def test_export_then_import_gives_a_new_template_and_never_overwrites(win, tmp_path):
    window, made = win
    screen = window.sablon
    target = tmp_path / "out" / "beyan.json"
    target.parent.mkdir()
    screen.export_template(target)
    assert target.is_file()
    screen.export_template(target)  # a file with that name exists: refused in words
    assert "zaten var" in screen.message.text()
    screen.import_template(target)
    assert screen.template.id != made.id
    assert screen.template.name == "Faaliyet belgesi (2)"
    assert len(_names(screen)) == 2
    screen.import_template(tmp_path / "yok.json")
    assert "bulunamadı" in screen.message.text()


def test_template_row_menu_lists_the_five_commands(win):
    window, _ = win
    screen = window.sablon
    menu = screen.box_menu(("sablonlar.sablon_adlandir", "sablonlar.sablon_cogalt",
                            "sablonlar.sablon_sil", None, "sablonlar.sablon_disa",
                            "sablonlar.sablon_ice"))
    texts = [a.text().replace("&", "") for a in menu.actions() if not a.isSeparator()]
    assert texts == ["Şablonu yeniden adlandır…", "Şablonu çoğalt", "Şablonu sil",
                     "Şablonu dışa aktar…", "Şablonu içe aktar…"]


# -- Ş-2 -------------------------------------------------------------------------------------
def _drag(canvas, a, b, mods=Qt.KeyboardModifier.NoModifier):
    from PySide6.QtCore import QPoint

    QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, mods, QPoint(*a))
    QTest.mouseMove(canvas.viewport(), QPoint(*b))
    QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, mods, QPoint(*b))


def _canvas_points(screen):
    canvas = screen.canvas
    top = canvas.mapFromScene(canvas.sceneRect().center())
    return (top.x() - 60, top.y() - 40), (top.x() + 60, top.y() - 10)


def test_kutu_ciz_switches_off_after_one_box_and_says_so_while_on(win):
    window, _ = win
    screen = window.sablon
    registry = window.registry
    screen.select_variable("Sicil_No")
    registry.action("sablonlar.kutu_ciz").trigger()
    assert screen.canvas.drawing
    part = screen._status["draw"]
    assert part.isVisible() and part.text() == "Kutu çiz açık: sayfada sürükleyin, Esc ile çıkın."
    button = next(b for b in window.command_bar("sablonlar").buttons()
                  if b.accessibleName().startswith("Kutu çiz"))
    assert button.property("accentOn") is True  # the on state is an accent fill
    a, b = _canvas_points(screen)
    _drag(screen.canvas, a, b)
    assert not screen.canvas.drawing and not registry.action("sablonlar.kutu_ciz").isChecked()
    assert not part.isVisible() and button.property("accentOn") is False
    assert len(screen.template.variable("Sicil_No").sections) == 1


def test_shift_keeps_kutu_ciz_on(win):
    window, _ = win
    screen = window.sablon
    screen.select_variable("Sicil_No")
    window.registry.action("sablonlar.kutu_ciz").trigger()
    a, b = _canvas_points(screen)
    _drag(screen.canvas, a, b, Qt.KeyboardModifier.ShiftModifier)
    assert screen.canvas.drawing
    _drag(screen.canvas, (a[0], a[1] + 30), (b[0], b[1] + 30))
    assert not screen.canvas.drawing
    assert len(screen.template.variable("Sicil_No").sections) == 2


def test_a_tiny_drag_says_so(win):
    window, _ = win
    screen = window.sablon
    screen.select_variable("Sicil_No")
    window.registry.action("sablonlar.kutu_ciz").trigger()
    a, _b = _canvas_points(screen)
    _drag(screen.canvas, a, (a[0] + 5, a[1] + 5))
    assert screen.message.text() == "Kutu çok küçük; daha büyük sürükleyin."
    assert screen.canvas.drawing  # nothing was drawn, the tool waits


# -- Ş-3, Ş-4, Ş-7 ---------------------------------------------------------------------------
def test_edits_of_one_box_merge_only_within_a_second(win, monkeypatch):
    from evrakci.ui import sablon_parts

    window, _ = win
    screen = window.sablon
    screen.select_section("Firma", 0)
    now = [100.0]
    monkeypatch.setattr(sablon_parts, "clock", lambda: now[0])
    screen.undo_stack.clear()
    screen._set_box("Firma", 0, (21.0, 30.0, 81.0, 40.0))
    now[0] += 0.4
    screen._set_box("Firma", 0, (22.0, 30.0, 82.0, 40.0))
    assert screen.undo_stack.count() == 1
    now[0] += 3.0
    screen._set_box("Firma", 0, (23.0, 30.0, 83.0, 40.0))
    assert screen.undo_stack.count() == 2
    screen.undo_stack.undo()
    assert screen.template.variable("Firma").sections[0].box_mm == (22.0, 30.0, 82.0, 40.0)


def test_a_page_the_example_does_not_have_is_kept_and_said(win):
    window, _ = win
    screen = window.sablon
    screen.select_section("Firma", 0)
    screen._page_edited(9)
    assert screen.message.text() == "Örnekte 1 sayfa var."
    assert screen.template.variable("Firma").sections[0].page == 9  # no silent change


def test_variant_origin_and_invalid_names():
    from evrakci.pipeline.templates.model import TemplateError
    from evrakci.pipeline.templates.store import clean_name
    from evrakci.ui.sablon_sync import drawn_on, locative

    assert drawn_on("Kasım · Belge 3 · s.7") == ", Örnek 3'te çizildi"
    assert drawn_on("Kasım · Belge 1 · s.1") == ", Örnek 1'de çizildi"
    assert drawn_on(None) == "" and drawn_on("elle") == ""
    assert [locative(n) for n in (6, 9, 10, 40, 100, 12)] == ["da", "da", "da", "ta", "de", "de"]
    assert clean_name("  Beyan ") == "Beyan"
    for bad in ("a\x00b", "x" * 3000, "a{b}", "a\nb"):
        with pytest.raises(TemplateError, match="Şablon adı geçersiz."):
            clean_name(bad)


def test_the_badge_is_drawn_for_the_first_section_and_the_chosen_one(win):
    window, _ = win
    screen = window.sablon
    screen.select_variable("Sicil_No")
    items = {}
    for n in range(3):
        screen.add_box((10.0 + 20 * n, 10.0, 25.0 + 20 * n, 20.0))
    screen.select_section("Sicil_No", 2)
    seen = []
    from evrakci.ui.sablon_canvas import BoxItem

    original = BoxItem._badge
    BoxItem._badge = lambda self, *a: seen.append((self.spec.index, self.selected))
    try:
        screen.canvas.viewport().grab()
    finally:
        BoxItem._badge = original
    assert (1, False) not in seen and {(0, False), (2, True)} <= set(seen), seen
    del items
