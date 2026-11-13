"""Şablonlar inside the MainWindow: registry actions, command bar, status bar, zoom and splitter
persistence, F9, undo, the empty states."""

import pytest
from fakes import make_pdf, qr_page, text_page
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from evrakci.pipeline.ocr.engine import Reading
from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.ui import actions
from evrakci.ui.main_window import MainWindow


class FakeEngine:
    name = "sahte"

    def available(self):
        return None

    def read_region(self, image):
        return Reading("48213", 0.95)


def _window(qtbot, tmp_path, template=True, job=True):
    store = JobStore(tmp_path / "jobs")
    templates = TemplateStore(tmp_path / "tpl")
    if template:
        made = templates.create("Faaliyet belgesi")
        made.add_variable("Firma", required=True)
        made.add_variable("Sicil_No")
        templates.save(made)
    window = MainWindow(store, templates, settings_path=tmp_path / "ayar.json")
    qtbot.addWidget(window)
    window.sablon.engine = FakeEngine
    if job:
        pdf = make_pdf(tmp_path / "t.pdf", [text_page(), qr_page(), text_page(), qr_page(),
                                            text_page()])
        with qtbot.waitSignal(window.yukle.job_opened, timeout=20000):
            window.yukle.create_job([pdf], "Kasım")
    window.resize(1366, 768)
    window.show()
    window.show_tab("sablonlar")
    window.sablon.attach(window)  # the screen does this itself on the next event loop turn
    return window


@pytest.fixture
def window(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.sablon
    qtbot.waitUntil(lambda: screen._read_task is None, timeout=15000)
    screen.select_variable("Firma")
    screen.set_example(1)
    screen.add_box((20.0, 30.0, 80.0, 40.0))
    qtbot.waitUntil(lambda: screen._read_task is None, timeout=15000)
    return window


def _ids():
    return [s.id for s in actions.SPECS if s.context == "sablonlar"]


def test_every_command_of_the_tab_is_connected(window):
    registry = window.registry
    assert all(action_id in registry._connected for action_id in _ids())


def test_commands_are_usable_when_their_state_allows_it(window):
    registry = window.registry
    for action_id in ("kutu_ciz", "izgara", "dene", "kutu_sil", "kutu_cogalt", "degisken_ekle",
                      "okumalari_goster"):
        assert registry.is_enabled(f"sablonlar.{action_id}"), action_id
    assert registry.is_enabled("app.kaydet")
    # Firma is first of two and has one box, so its row moves as a variable: down, not up
    assert not registry.is_enabled("sablonlar.yukari") and registry.is_enabled("sablonlar.asagi")
    window.sablon.select_variable("Sicil_No")  # last, no box: up, not down
    assert registry.is_enabled("sablonlar.yukari") and not registry.is_enabled("sablonlar.asagi")
    assert not registry.is_enabled("sablonlar.kutu_cogalt")  # a variable without a box
    window.sablon.select_variable("Firma")


def test_nothing_is_usable_without_a_template(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, template=False)
    registry = window.registry
    for action_id in ("kutu_ciz", "izgara", "dene", "kutu_sil", "kutu_cogalt", "degisken_ekle",
                      "yukari", "asagi", "okumalari_goster"):
        assert not registry.is_enabled(f"sablonlar.{action_id}"), action_id
    assert not registry.is_enabled("app.kaydet")


def test_the_command_bar_is_as_the_mockup_draws_it(window):
    bar = window.command_bar("sablonlar")
    labelled = [b.text() for b in bar.buttons() if getattr(b, "labelled", lambda: False)()]
    assert labelled == ["Kutu çiz", "Bütün örneklerde dene"]
    names = [b.accessibleName() for b in bar.buttons()]
    assert "Geri al (Ctrl+Z)" in " ".join(names) or any(n.startswith("Geri al") for n in names)
    for name in ("Kutu çiz (B)", "Izgaraya oturt (G)", "Kutuyu çoğalt (Ctrl+D)",
                 "Kutuyu sil (geri alınabilir) (Del)", "Değişken ekle (Ctrl+Shift+N)",
                 "Okumaları sayfada göster"):
        assert name in names, name
    assert any(n.startswith("Ayrıntı panelini") for n in names)  # F9


def test_kutu_ciz_and_izgara_are_toggles_that_reach_the_canvas(window):
    registry, screen = window.registry, window.sablon
    registry.action("sablonlar.kutu_ciz").trigger()
    assert screen.canvas.drawing and registry.action("sablonlar.kutu_ciz").isChecked()
    screen.canvas.drawing_cancelled.emit()  # Esc on the canvas
    assert not screen.canvas.drawing and not registry.action("sablonlar.kutu_ciz").isChecked()
    registry.action("sablonlar.izgara").trigger()
    assert screen.canvas.snap and registry.action("sablonlar.izgara").isChecked()
    registry.action("sablonlar.okumalari_goster").trigger()
    assert screen.canvas.show_reads
    registry.action("sablonlar.okumalari_goster").trigger()
    assert not screen.canvas.show_reads


def test_the_status_bar_slot_reads_as_the_mockup(qtbot, window):
    screen = window.sablon
    parts = screen._status
    assert parts["example"].text() == "Örnek 1 / 3"
    assert parts["cursor"].text().startswith("İmleç ") and parts["cursor"].isVisible()
    assert not parts["box"].isVisible() and not parts["hint"].isVisible()
    assert parts["saved"].text().startswith("Şablon kaydedildi")
    screen.canvas.setFocus(Qt.FocusReason.TabFocusReason)  # the nudge state
    QTest.keyClick(screen.canvas, Qt.Key.Key_Right)
    assert parts["box"].isVisible() and parts["hint"].isVisible()
    assert not parts["cursor"].isVisible()
    assert parts["box"].text() == "Kutu x 20,25  y 30,0 mm"
    assert parts["hint"].text() == "Kaydır: ok tuşları 0,25 mm, Shift 1 mm"
    assert parts["saved"].text() == "Şablon kaydedilmedi"  # until the short pause has passed
    qtbot.waitUntil(lambda: parts["saved"].text().startswith("Şablon kaydedildi"), timeout=5000)
    screen.canvas.cursor_moved.emit((84.5, 41.0))
    screen.canvas.clearFocus()
    assert parts["cursor"].text() == "İmleç x 84,5  y 41,0 mm"


def test_the_windows_job_counts_give_way_to_this_tabs_status_line(window):
    for label in (window.counts, window.pages, window.checks):
        assert not label.isVisible()
    window.show_tab("yukle")
    assert not window.counts.isVisible()  # Yükle's mockup draws its own "parti sayfa" line
    window.show_tab("disa_aktar")
    assert window.counts.isVisible() or window.counts.text() == ""  # only Dışa Aktar shows them
    window.show_tab("sablonlar")
    assert not window.counts.isVisible()


def test_the_zoom_slider_drives_the_page_and_the_zoom_is_remembered(qtbot, tmp_path, window):
    screen = window.sablon
    controller = window.zoom_controller("sablonlar")
    assert controller is screen.zoom and window.zoom_slider.isVisible()
    controller.set_zoom(150)
    assert screen.canvas.zoom() == 150 and not screen.canvas.is_fitted()
    assert window.prefs.zoom("sablonlar") == 150
    QTest.keyClick(screen.canvas, Qt.Key.Key_Plus, Qt.KeyboardModifier.ControlModifier)
    assert screen.canvas.zoom() == 160
    QTest.keyClick(screen.canvas, Qt.Key.Key_0, Qt.KeyboardModifier.ControlModifier)
    assert screen.canvas.is_fitted() and screen.canvas.zoom() == screen.canvas.fit_zoom()
    controller.set_zoom(150)
    window.close()
    again = _window(qtbot, tmp_path, template=False, job=False)
    assert again.prefs.zoom("sablonlar") == 150
    assert again.sablon.canvas.zoom() == 150 and not again.sablon.canvas.is_fitted()


def test_ctrl_wheel_zooms_the_page(window):
    canvas = window.sablon.canvas
    window.sablon.zoom.set_zoom(100)
    pos = QPointF(200, 200)
    event = QWheelEvent(pos, canvas.viewport().mapToGlobal(pos), QPoint(0, 0), QPoint(0, 120),
                        Qt.MouseButton.NoButton, Qt.KeyboardModifier.ControlModifier,
                        Qt.ScrollPhase.NoScrollPhase, False)
    QApplication.sendEvent(canvas.viewport(), event)
    assert canvas.zoom() == 110


def test_the_splitter_is_remembered(qtbot, tmp_path, window):
    screen = window.sablon
    assert screen.splitter.objectName() == "sablonlar" and screen.splitter.count() == 3
    total = sum(screen.splitter.sizes())
    screen.splitter.setSizes([300, total - 300 - 280, 280])
    screen.splitter.splitterMoved.emit(300, 1)
    assert window.prefs.splitter_sizes("sablonlar") == screen.splitter.sizes()
    stored = window.prefs.splitter_sizes("sablonlar")
    window.close()
    again = _window(qtbot, tmp_path, template=False, job=False)
    assert again.prefs.splitter_sizes("sablonlar") == stored
    assert again.sablon.splitter.sizes()[0] == stored[0]


def test_f9_hides_and_shows_the_inspector_and_an_empty_screen_keeps_it_away(qtbot, tmp_path,
                                                                           window):
    screen = window.sablon
    assert window.inspector("sablonlar") is screen.side and screen.side.isVisible()
    window.registry.action("app.yan_panel").trigger()
    assert screen.side.isHidden() and not screen.side.isVisible()
    assert "göster" in window.registry.action("app.yan_panel").toolTip()
    window.registry.action("app.yan_panel").trigger()
    assert screen.side.isVisible()
    empty = _window(qtbot, tmp_path / "bos", template=False, job=False)
    assert not empty.sablon.side.isVisible()  # no template: nothing to inspect


def test_undo_and_redo_follow_the_page_edits(qtbot, window):
    screen, registry = window.sablon, window.registry
    screen.canvas.setFocus(Qt.FocusReason.TabFocusReason)
    QTest.keyClick(screen.canvas, Qt.Key.Key_Down, Qt.KeyboardModifier.ShiftModifier)
    assert screen.template.variable("Firma").sections[0].box_mm == pytest.approx(
        (20.0, 31.0, 80.0, 41.0))
    assert "Kutuyu taşı" in registry.action("app.geri_al").toolTip()
    registry.action("app.geri_al").trigger()
    assert screen.template.variable("Firma").sections[0].box_mm == (20.0, 30.0, 80.0, 40.0)
    registry.action("app.yinele").trigger()
    assert screen.template.variable("Firma").sections[0].box_mm == pytest.approx(
        (20.0, 31.0, 80.0, 41.0))


def test_a_template_without_variables_says_how_to_start(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, template=False)
    screen = window.sablon
    screen._ask_text = lambda *a: "Boş şablon"
    screen.new_template()
    assert screen.template.name == "Boş şablon" and screen.template.variables == []
    assert screen.side.title.full_text() == "Değişken yok"
    assert "Ctrl+Shift+N" in screen.side.sub.text()
    assert "henüz değişken yok" in screen.nav.foot.text()


def test_the_empty_state_is_the_mockups_and_its_actions_work(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, template=False)
    screen = window.sablon
    empty = screen.empty
    assert screen.stack.currentWidget() is screen.empty_frame
    assert (empty.title.text(), empty.text.text()) == (
        "Henüz şablon yok", "Örnek bir sayfada her bilginin çevresine kutu çizin.")
    assert empty.primary.accessibleName() == "Yeni şablon oluştur"
    assert empty.secondary.accessibleName() == "Rehber'i aç"
    assert empty.note.text() == "Örnek sayfalar açık işten gelir: Kasım."
    assert "bu bilgisayarda saklanır" in screen.nav.foot.text()
    assert not screen.nav.template_card.isVisible() and not screen.bar.isVisible()
    assert not window.zoom_slider.isVisible()
    empty.secondary.click()
    assert window.current_tab() == "rehber"
    window.show_tab("sablonlar")
    screen._ask_text = lambda *a: "Yeni belge"
    empty.primary.click()
    assert screen.template.name == "Yeni belge"
    assert screen.stack.currentWidget() is screen.well


def test_without_an_open_job_the_page_area_says_where_examples_come_from(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, job=False)
    screen = window.sablon
    assert screen.stack.currentWidget() is screen.empty_frame
    assert screen.empty.title.text() == "Örnek sayfa yok"
    assert screen.empty.primary.accessibleName() == "Yükle'ye git"
    screen.empty.primary.click()
    assert window.current_tab() == "yukle"
    assert screen.template is not None and screen.variables.topLevelItemCount() == 2


def test_the_context_menus_list_the_boxs_commands_with_their_keys(window):
    menu = window.sablon.box_menu()
    texts = [a.text().replace("&", "") for a in menu.actions() if not a.isSeparator()]
    assert texts[:3] == ["Kutuyu çoğalt", "Kutuyu sil", "Değişkeni yukarı taşı"]
    assert "Değişken ekle" in texts
    page = window.sablon.box_menu(("sablonlar.kutu_ciz", "sablonlar.izgara"))
    assert [a.text().replace("&", "") for a in page.actions()] == ["Kutu çiz", "Izgaraya oturt"]
    inspector_menu = window.sablon.side.more.menu()
    inspector_menu.aboutToShow.emit()
    assert [a.text().replace("&", "") for a in inspector_menu.actions() if not a.isSeparator()
            ][0] == "Kutuyu çoğalt"


def test_the_keys_of_the_tab_work_in_the_window(qtbot, window):
    """B, G, Ctrl+D and Del reach the registry actions from the canvas."""
    screen = window.sablon
    window.activateWindow()
    qtbot.waitUntil(lambda: window.isActiveWindow(), timeout=3000)
    screen.canvas.setFocus(Qt.FocusReason.TabFocusReason)
    QTest.keyClick(screen.canvas, Qt.Key.Key_B)
    assert screen.canvas.drawing
    QTest.keyClick(screen.canvas, Qt.Key.Key_B)
    assert not screen.canvas.drawing
    QTest.keyClick(screen.canvas, Qt.Key.Key_G)
    assert screen.canvas.snap
    QTest.keyClick(screen.canvas, Qt.Key.Key_D, Qt.KeyboardModifier.ControlModifier)
    assert len(screen.template.variable("Firma").sections) == 2
    QTest.keyClick(screen.canvas, Qt.Key.Key_Delete)
    assert len(screen.template.variable("Firma").sections) == 1
    window.registry.action("app.geri_al").trigger()
    assert len(screen.template.variable("Firma").sections) == 2


def test_typing_in_a_field_never_fires_the_single_key_commands(qtbot, window):
    screen = window.sablon
    window.activateWindow()
    screen.pattern.setFocus()
    qtbot.waitUntil(lambda: screen.pattern.hasFocus(), timeout=3000)
    QTest.keyClick(screen.pattern, Qt.Key.Key_B)
    assert not screen.canvas.drawing and screen.pattern.text().endswith("b")


def test_a_failed_save_after_an_edit_is_still_said(qtbot, window, monkeypatch):
    screen = window.sablon

    def broken(_template):
        raise OSError("disk dolu")

    monkeypatch.setattr(screen.store, "save", broken)
    screen._edit("Zorunlu", lambda t: t.set_required("Sicil_No", True))
    assert "kaydedilemedi" in screen.message.text()
    assert screen._status["saved"].text() == "Şablon kaydedilemedi"
    monkeypatch.undo()
    screen.save()
    assert screen.message.text() == "" and screen._status["saved"].text().startswith(
        "Şablon kaydedildi")


def test_hints_say_what_is_missing_instead_of_doing_nothing(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, job=False)
    screen = window.sablon
    screen.variable_name = None
    screen.add_box((10.0, 20.0, 60.0, 30.0))
    assert "değişken seçin" in screen.message.text()
    screen.select_variable("Firma")
    screen.add_box((10.0, 20.0, 60.0, 30.0))
    assert "iş açın" in screen.message.text()
    assert not window.registry.is_enabled("sablonlar.kutu_ciz")  # no page to draw on


def test_renaming_a_variable_keeps_its_box_chosen(qtbot, window):
    screen = window.sablon
    screen.select_section("Firma", 0)
    screen.side.name.setText("Firma_Unvani")
    screen.side.name.editingFinished.emit()
    assert (screen.variable_name, screen.section_index) == ("Firma_Unvani", 0)
    assert screen.canvas.selected() == ("Firma_Unvani", 0)


def test_what_is_read_is_read_again_only_when_it_changed(qtbot, window):
    from evrakci.pipeline.templates.model import Section

    screen = window.sablon
    qtbot.waitUntil(lambda: screen._read_task is None, timeout=15000)
    screen._read_timer.stop()
    screen._edit("Zorunlu", lambda t: t.set_required("Sicil_No", True))
    assert not screen._read_timer.isActive()  # a required mark does not change what is read
    screen._edit("Kutuyu çoğalt", lambda t: t.add_section(
        "Sicil_No", Section(1, (10.0, 10.0, 50.0, 20.0), None)))
    assert screen._read_timer.isActive()  # a new box does
    screen.undo_stack.undo()  # and so does taking it back
    assert screen._read_timer.isActive()
    qtbot.waitUntil(lambda: screen._read_task is None and not screen._read_timer.isActive(),
                    timeout=15000)
