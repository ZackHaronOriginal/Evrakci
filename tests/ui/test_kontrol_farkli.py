"""I-04: pages whose size or orientation differs: the mark under the page, the jumps, the dialog
row and the sizes of an older job read when it opens.

Job of most tests: "aaaaaaaa" is eight A4 pages; pages 2 (sideways) and 5 (A5) look different.
"""

import json
import threading

import pytest
from fakes import a5_page, make_pdf, text_page, without_sizes
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtTest import QTest
from test_kontrol_a import _window

from evrakci.pipeline.analyze import PageInfo
from evrakci.pipeline.select import Criterion, evaluate
from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.ui import kontrol_paint as kp
from evrakci.ui import theme
from evrakci.ui.kontrol_dialogs import SelectDialog
from evrakci.ui.main_window import MainWindow
from evrakci.ui.prefs import Prefs
from evrakci.ui.timeline import Metrics, Roles, TimelineDelegate

SPEC = {"a": "pppppppp"}
A4, SIDEWAYS, A5 = (210.0, 297.0), (297.0, 210.0), (148.0, 210.0)


def _sized(window, odd=None):
    """Give every page a size: A4, except the pages in `odd` ({index: (w, h)})."""
    odd = {2: SIDEWAYS, 5: A5} if odd is None else odd
    job = window.controller().job
    for index in range(8):
        width, height = odd.get(index, A4)
        job.pages[f"a/{index}"] = PageInfo(0.05, False, width, height)
    window.controller().job_changed.emit()  # the timeline looks at the sizes again


def _marked_window(qtbot, tmp_path, odd=None):
    window = _window(qtbot, tmp_path, spec=SPEC)
    _sized(window, odd)
    return window


def _go(window, row):
    window.kontrol.go_to_row(row)


def _current(window):
    return window.kontrol.current_row()


# -- the marks ----------------------------------------------------------------------------------
def test_pages_that_look_different_are_marked_and_the_text_says_so(qtbot, tmp_path):
    window = _marked_window(qtbot, tmp_path)
    model = window.kontrol.model
    assert model.odd_rows() == [2, 5]
    assert [model.odd_kind(r) for r in range(8)] == [None, None, "yatay", None, None, "boyut",
                                                     None, None]
    assert model.index(5).data(Roles.ODD) == "boyut"
    assert model.describe(5) == "Sayfa 6, Belge 1, incelenmedi, farklı boyut"
    assert model.describe(2) == "Sayfa 3, Belge 1, incelenmedi, yatay"
    assert model.describe(0) == "Sayfa 1, Belge 1, incelenmedi"
    assert model.index(5).data(Qt.ItemDataRole.AccessibleTextRole) == model.describe(5)


def test_a_job_that_is_mostly_landscape_marks_the_portrait_page(qtbot, tmp_path):
    odd = {i: SIDEWAYS for i in range(8)}
    odd[4] = A4
    window = _marked_window(qtbot, tmp_path, odd)
    assert window.kontrol.model.odd_kind(4) == "dikey"
    assert window.kontrol.model.describe(4).endswith(", dikey")


def test_r_stands_a_sideways_page_up_and_the_mark_goes(qtbot, tmp_path):
    window = _marked_window(qtbot, tmp_path)
    screen = window.kontrol
    _go(window, 2)
    screen.timeline.selectionModel().select(screen.model.index(2),
                                            screen.timeline.selectionModel().SelectionFlag.Select)
    screen.rotate_selected(90)
    assert screen.model.odd_rows() == [5]  # fixed: no mark any more
    window.controller().undo()
    assert screen.model.odd_rows() == [2, 5]  # undone: the mark is back


def test_a_page_turned_by_the_user_is_marked(qtbot, tmp_path):
    window = _marked_window(qtbot, tmp_path, odd={})
    assert window.kontrol.model.odd_rows() == []
    window.controller().rotate("a/3", 90)
    assert window.kontrol.model.odd_rows() == [3]
    assert window.kontrol.model.describe(3).endswith(", yatay")


def test_a_deleted_page_shows_silinecek_and_no_mark(qtbot, tmp_path):
    window = _marked_window(qtbot, tmp_path)
    window.controller().delete_page("a/5")
    assert window.kontrol.model.odd_rows() == [2]
    assert window.kontrol.model.index(5).data(Roles.ODD) is None


def test_the_switch_is_a_checkable_view_command_and_is_kept(qtbot, tmp_path):
    window = _marked_window(qtbot, tmp_path)
    registry = window.registry
    action = registry.action("kontrol.farkli_isaretle")
    spec = registry.spec("kontrol.farkli_isaretle")
    assert spec.checkable and spec.shortcuts == () and spec.menu == "gorunum"
    assert action.text().replace("&", "") == "Farklı görünenleri işaretle"
    assert action.isChecked() and registry.is_enabled("kontrol.farkli_isaretle")
    action.trigger()
    model = window.kontrol.model
    assert not action.isChecked() and not model.marks_on
    assert model.index(5).data(Roles.ODD) is None
    assert model.describe(5) == "Sayfa 6, Belge 1, incelenmedi"
    assert model.odd_rows() == [2, 5]  # the pages are still found: the jumps work
    assert Prefs(tmp_path / "p.ini").flag("kontrol_farkli_isaretle", True) is False
    assert window.controller().undo_stack.index() == 0  # a view choice, not a job edit
    action.trigger()
    assert action.isChecked() and model.index(5).data(Roles.ODD) == "boyut"


def test_the_switch_is_remembered_by_the_next_window(qtbot, tmp_path):
    first = _marked_window(qtbot, tmp_path)
    first.registry.action("kontrol.farkli_isaretle").trigger()
    second = _window(qtbot, tmp_path / "again", spec=SPEC)
    Prefs(tmp_path / "again" / "p.ini")  # a different file: starts on
    assert second.registry.action("kontrol.farkli_isaretle").isChecked()
    assert second.kontrol.model.marks_on


# -- painting -----------------------------------------------------------------------------------
def _caption_image(kind, width=164, height=28, selected=False, number=72):
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(theme.manager().color("layer"))
    painter = QPainter(image)
    TimelineDelegate()._caption(painter, QRectF(0, 0, width, height), number - 1, "page",
                                selected, kind)
    painter.end()
    return image


def _colours(image):
    return {image.pixelColor(x, y).rgb() for x in range(image.width())
            for y in range(image.height())}


def _one_ink_colour(image, ink, background):
    """True when every pixel is the background, the ink or a blend of the two (anti-aliasing),
    and some pixel is the ink itself: nothing in the mark has any other colour."""
    solid = False
    for x in range(image.width()):
        for y in range(image.height()):
            pixel = image.pixelColor(x, y).getRgb()[:3]
            shares = [(p - b) / (i - b) for p, i, b in zip(pixel, ink, background, strict=True)
                      if abs(i - b) > 40]
            if not shares or max(shares) - min(shares) > 0.08:
                if pixel != background:
                    return False
                continue
            solid = solid or min(shares) > 0.95
    return solid


@pytest.mark.parametrize("mode", ["light", "dark", "hc"])
def test_the_mark_is_text_colour_never_orange_or_a_cut_colour(qapp, mode):
    manager = theme.manager()
    old = manager.theme()
    manager.set_mode(mode)
    try:
        background = manager.color("layer").getRgb()[:3]
        ink = manager.color("text" if mode == "hc" else "text-2").getRgb()[:3]
        for kind in ("boyut", "yatay", "dikey"):
            marked = _caption_image(kind)
            assert marked != _caption_image(None)
            assert _one_ink_colour(marked, ink, background), (mode, kind)
            # the same test fails for the orange rider colour: the check is not vacuous
            orange = manager.color("rider").getRgb()[:3]
            assert not _one_ink_colour(marked, orange, background) or orange == ink
    finally:
        manager.set_mode(old)


def test_the_mark_has_an_icon_and_the_word_next_to_the_number(qapp):
    image = _caption_image("boyut")
    plain = _caption_image(None)
    bg = theme.manager().color("layer").rgb()
    marked_cols = [x for x in range(image.width())
                   if any(image.pixelColor(x, y).rgb() != bg for y in range(image.height()))]
    plain_cols = [x for x in range(plain.width())
                  if any(plain.pixelColor(x, y).rgb() != bg for y in range(plain.height()))]
    assert max(marked_cols) - min(marked_cols) > max(plain_cols) - min(plain_cols) + 60
    assert kp.ODD_MARKS == {"boyut": ("ruler", "Farklı boyut"),
                            "yatay": ("rectangle-horizontal", "Yatay"),
                            "dikey": ("rectangle-vertical", "Dikey")}
    assert kp.ODD_ICON == 14 and theme.manager().inline_icon(kp.ODD_ICON) == 14


def test_at_150_percent_the_caption_wraps_to_two_lines_and_the_row_makes_room(
        qtbot, tmp_path):
    manager = theme.manager()
    window = _window(qtbot, tmp_path, spec={"a": "p" * 120})
    job = window.controller().job
    for index in range(120):
        width, height = A5 if index == 104 else A4
        job.pages[f"a/{index}"] = PageInfo(0.05, False, width, height)
    window.controller().job_changed.emit()
    timeline = window.kontrol.timeline
    assert window.kontrol.model.odd_rows() == [104]
    assert timeline.metrics.lines == 1  # at 100 % the number and the mark fit side by side
    assert kp.odd_caption_lines("105", "boyut", 164) == 1
    old = manager.text_scale()
    manager.set_text_scale(150)
    try:
        timeline.relayout()
        assert timeline.metrics.lines == 2
        assert timeline.metrics.caption_h == manager.size("lh-caption") * 2 + 10
        assert manager.inline_icon(kp.ODD_ICON) == 20
        assert kp.odd_caption_lines("105", "boyut", 164) == 2
        image = _caption_image("boyut", height=timeline.metrics.caption_h, number=105)
        # the second line carries pixels: the mark sits under the number, inside the caption
        bg = manager.color("layer").rgb()
        lower = image.copy(0, manager.size("lh-caption") + 6, image.width(), image.height() - (
            manager.size("lh-caption") + 6))
        assert any(lower.pixelColor(x, y).rgb() != bg for x in range(lower.width())
                   for y in range(lower.height()))
        upper = image.copy(0, 0, image.width(), manager.size("lh-caption") + 4)
        assert any(upper.pixelColor(x, y).rgb() != bg for x in range(upper.width())
                   for y in range(upper.height()))  # the number stays on the first line
    finally:
        manager.set_text_scale(old)
        timeline.relayout()
    assert timeline.metrics.lines == 1


def test_no_mark_means_the_row_keeps_its_height(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, spec=SPEC)
    timeline = window.kontrol.timeline
    assert timeline.metrics.caption_h == Metrics.at(100).caption_h
    _sized(window)
    window.registry.action("kontrol.farkli_isaretle").trigger()
    assert timeline.metrics.lines == 1


# -- jumps --------------------------------------------------------------------------------------
def test_the_jumps_are_in_menu_git_and_the_palette_with_no_key(qtbot, tmp_path):
    window = _marked_window(qtbot, tmp_path)
    registry = window.registry
    for action_id, text in (("kontrol.sonraki_farkli", "Sonraki farklı sayfa"),
                            ("kontrol.onceki_farkli", "Önceki farklı sayfa")):
        spec = registry.spec(action_id)
        assert spec.menu == "git" and spec.shortcuts == () and spec.palette
        assert spec.text.replace("&", "") == text
        assert registry.is_enabled(action_id)
        assert any(e.id == action_id for e in registry.palette_entries())


def test_next_and_previous_wrap_round(qtbot, tmp_path):
    window = _marked_window(qtbot, tmp_path)
    registry = window.registry
    _go(window, 0)
    registry.action("kontrol.sonraki_farkli").trigger()
    assert _current(window) == 2
    registry.action("kontrol.sonraki_farkli").trigger()
    assert _current(window) == 5
    registry.action("kontrol.sonraki_farkli").trigger()
    assert _current(window) == 2  # wrapped round
    registry.action("kontrol.onceki_farkli").trigger()
    assert _current(window) == 5  # wrapped back
    registry.action("kontrol.onceki_farkli").trigger()
    assert _current(window) == 2
    registry.action("kontrol.onceki_farkli").trigger()
    assert _current(window) == 5


def test_the_jumps_work_with_the_marks_hidden(qtbot, tmp_path):
    window = _marked_window(qtbot, tmp_path)
    window.registry.action("kontrol.farkli_isaretle").trigger()
    _go(window, 0)
    window.registry.action("kontrol.sonraki_farkli").trigger()
    assert _current(window) == 2


def test_no_different_page_says_so(qtbot, tmp_path):
    window = _marked_window(qtbot, tmp_path, odd={})
    _go(window, 3)
    window.registry.action("kontrol.sonraki_farkli").trigger()
    assert window.toaster.current_text() == "Farklı sayfa yok."
    window.registry.action("kontrol.onceki_farkli").trigger()
    assert window.toaster.current_text() == "Farklı sayfa yok."
    assert _current(window) == 3


# -- the dialog row -----------------------------------------------------------------------------
def _dialog(window, qtbot, kind="farkli"):
    dialog = SelectDialog(window.controller().job, 1, [], kind, parent=window)
    qtbot.addWidget(dialog)
    dialog.show()
    return dialog


def test_the_row_its_check_boxes_combo_and_live_count(qtbot, tmp_path):
    window = _marked_window(qtbot, tmp_path)
    dialog = _dialog(window, qtbot)
    assert dialog.kind() == "farkli"
    assert dialog._radios["farkli"].text() == "Farklı boyut veya yön"
    assert dialog.title.text() == "Farklı boyut veya yön"
    assert [b.text() for b in dialog.farkli_boxes.values()] == ["Boyut", "Yön"]
    assert all(b.isChecked() for b in dialog.farkli_boxes.values())
    assert [dialog.farkli_reference.itemText(i) for i in range(2)] == ["Bütün iş", "Her belge"]
    assert dialog.farkli_label.text() == "Karşılaştır"
    assert dialog.farkli_count.text() == "2 sayfa farklı görünüyor"
    assert dialog._counts["farkli"].text() == "2"
    assert dialog.criterion().params == {"by": ["boyut", "yon"], "reference": "is"}
    assert dialog.farkli_note.isHidden()  # every size is known


def test_the_live_count_follows_the_check_boxes_and_the_reference(qtbot, tmp_path):
    window = _marked_window(qtbot, tmp_path)
    dialog = _dialog(window, qtbot)
    dialog.farkli_boxes["yon"].setChecked(False)
    assert dialog.farkli_count.text() == "1 sayfa farklı görünüyor"
    assert dialog._counts["farkli"].text() == "1"
    dialog.farkli_boxes["boyut"].setChecked(False)
    assert dialog.farkli_count.text() == "0 sayfa farklı görünüyor"
    assert dialog._counts["farkli"].text() == "Hiç yok"
    dialog.farkli_boxes["yon"].setChecked(True)
    assert dialog.farkli_count.text() == "1 sayfa farklı görünüyor"
    dialog.farkli_reference.setCurrentIndex(1)
    assert dialog.criterion().params == {"by": ["yon"], "reference": "belge"}


def test_the_pane_shows_only_for_this_row(qtbot, tmp_path):
    window = _marked_window(qtbot, tmp_path)
    dialog = _dialog(window, qtbot, "belge")
    assert all(w.isHidden() for w in dialog.farkli_widgets)
    dialog._radios["farkli"].setChecked(True)
    assert not dialog.farkli_reference.isHidden() and not dialog.farkli_count.isHidden()
    dialog._radios["bos"].setChecked(True)
    assert all(w.isHidden() for w in dialog.farkli_widgets)


def test_pages_of_unknown_size_are_named_and_never_counted(qtbot, tmp_path):
    window = _marked_window(qtbot, tmp_path)
    job = window.controller().job
    job.pages["a/0"] = PageInfo(0.05, False)
    job.pages["a/1"] = PageInfo(0.05, False)
    dialog = _dialog(window, qtbot)
    assert dialog.farkli_note.text() == "Boyutu bilinmiyor (2)"
    assert not dialog.farkli_note.isHidden()
    assert dialog.farkli_count.text() == "2 sayfa farklı görünüyor"


def test_the_parameters_are_in_the_tab_chain_before_the_modes(qtbot, tmp_path):
    from PySide6.QtWidgets import QApplication

    window = _marked_window(qtbot, tmp_path)
    dialog = _dialog(window, qtbot, "farkli")
    dialog.activateWindow()
    qtbot.waitUntil(dialog.isActiveWindow)
    dialog._radios["farkli"].setFocus()
    stops = []
    for _ in range(5):
        QTest.keyClick(QApplication.focusWidget(), Qt.Key.Key_Tab)
        stops.append(QApplication.focusWidget())
    assert stops == [dialog.farkli_boxes["boyut"], dialog.farkli_boxes["yon"],
                     dialog.farkli_reference, dialog._mode_radios["replace"], dialog.ok]


def test_seç_selects_what_the_count_said_and_the_cli_gives_the_same_pages(
        qtbot, tmp_path, monkeypatch):
    window = _marked_window(qtbot, tmp_path)
    seen = {}

    def answer(dialog):
        dialog._radios["farkli"].setChecked(True)
        seen["count"] = dialog.farkli_count.text()
        seen["criterion"] = dialog.criterion()
        return True

    monkeypatch.setattr(SelectDialog, "exec", answer)
    ctl = window.controller()
    before = ctl.undo_stack.index()
    window.kontrol.select_by()
    chosen = sorted(i.row() for i in window.kontrol.timeline.selectionModel().selectedIndexes())
    job = ctl.job
    order = job.ordered_page_ids()
    by_core = [order.index(p) for p in evaluate(job, seen["criterion"]).page_ids]
    assert chosen == by_core == [2, 5]
    assert seen["count"].startswith(f"{len(chosen)} sayfa")
    assert ctl.undo_stack.index() == before  # a selection, not an edit


def test_the_dialog_and_the_cli_name_the_same_pages(qtbot, tmp_path, capsys):
    from evrakci.cli import main

    root = tmp_path / "kok"
    pdf = make_pdf(tmp_path / "t.pdf", [text_page(), text_page(), a5_page(), text_page()])
    assert main(["--kok", str(root), "is", "olustur", "İş", str(pdf)]) == 0
    job_id = capsys.readouterr().out.strip().splitlines()[-1]
    assert main(["--kok", str(root), "is", "sec", job_id, "farkli"]) == 0
    printed = next(x for x in capsys.readouterr().out.splitlines() if x.startswith("sayfa "))
    store = JobStore(root)
    window = MainWindow(store, TemplateStore(tmp_path / "tpl"), settings_path=tmp_path / "a.json",
                        prefs=Prefs(tmp_path / "p.ini"))
    qtbot.addWidget(window)
    job = store.load(job_id)
    dialog = SelectDialog(job, 1, [], "farkli", parent=window)
    qtbot.addWidget(dialog)
    order = job.ordered_page_ids()
    positions = [order.index(p) + 1 for p in evaluate(job, dialog.criterion()).page_ids]
    assert printed == "sayfa " + ", ".join(str(n) for n in positions) == "sayfa 3"


# -- an older job: the sizes are read when it opens ---------------------------------------------
def _old_job_window(qtbot, tmp_path, pages):
    store = JobStore(tmp_path / "jobs")
    job = store.create_job("Eski", [make_pdf(tmp_path / "a.pdf", pages)])
    path = store._job_file(job.id)
    path.write_text(json.dumps(without_sizes(json.loads(path.read_text(encoding="utf-8")))),
                    encoding="utf-8")
    window = MainWindow(store, TemplateStore(tmp_path / "tpl"),
                        settings_path=tmp_path / "ayar.json", prefs=Prefs(tmp_path / "p.ini"))
    qtbot.addWidget(window)
    window.resize(1366, 768)
    return window, store, job.id


def _open(qtbot, window, store, job_id):
    with qtbot.waitSignal(window.yukle.job_opened, timeout=10000):
        window.yukle.open_job(store.load(job_id))
    window.show_tab("kontrol")
    qtbot.wait(1)


def test_an_older_job_gets_its_sizes_when_it_opens_off_the_window_thread(
        qtbot, tmp_path, monkeypatch):
    threads = []
    real = JobStore.read_sizes

    def spy(requests, progress=None):
        threads.append(threading.current_thread() is threading.main_thread())
        return real(requests, progress)

    monkeypatch.setattr(JobStore, "read_sizes", staticmethod(spy))
    window, store, job_id = _old_job_window(
        qtbot, tmp_path, [text_page(), text_page(), a5_page(), text_page()])
    _open(qtbot, window, store, job_id)
    controller = window.controller()
    qtbot.waitUntil(lambda: controller.job.pages["b1/2"].has_size, timeout=10000)
    assert threads == [False]  # read in a worker
    assert [i.has_size for i in controller.job.pages.values()] == [True] * 4
    assert window.kontrol.model.odd_rows() == [2]  # the A5 page is marked
    assert controller.undo_stack.index() == 0 and not controller.undo_stack.canUndo()
    qtbot.waitUntil(lambda: not window.loading(), timeout=5000)
    assert window.message.text() != "Sayfa boyutları okunuyor"
    done = []
    controller.saver.when_idle(lambda ok, error: done.append(ok))
    qtbot.waitUntil(lambda: done == [True], timeout=5000)
    saved = json.loads(store._job_file(job_id).read_text(encoding="utf-8"))
    assert saved["pages"]["b1/2"]["width_mm"] > 0 and saved["version"] == 2


def test_the_status_line_says_so_while_the_sizes_are_read(qtbot, tmp_path, monkeypatch):
    gate = threading.Event()
    real = JobStore.read_sizes

    def slow(requests, progress=None):
        gate.wait(5)
        return real(requests, progress)

    monkeypatch.setattr(JobStore, "read_sizes", staticmethod(slow))
    window, store, job_id = _old_job_window(qtbot, tmp_path, [text_page(), a5_page()])
    _open(qtbot, window, store, job_id)
    assert window.message.text() == "Sayfa boyutları okunuyor"
    assert window.loading()  # the window thread is free; the work is in a worker
    gate.set()
    qtbot.waitUntil(lambda: window.controller().job.pages["b1/1"].has_size, timeout=10000)
    qtbot.waitUntil(lambda: window.message.text() != "Sayfa boyutları okunuyor", timeout=5000)


def test_a_job_that_knows_its_sizes_reads_nothing(qtbot, tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(JobStore, "read_sizes",
                        staticmethod(lambda *a, **k: calls.append(1) or {}))
    store = JobStore(tmp_path / "jobs")
    job = store.create_job("Yeni", [make_pdf(tmp_path / "a.pdf", [text_page(), a5_page()])])
    window = MainWindow(store, TemplateStore(tmp_path / "tpl"),
                        settings_path=tmp_path / "ayar.json", prefs=Prefs(tmp_path / "p.ini"))
    qtbot.addWidget(window)
    _open(qtbot, window, store, job.id)
    assert calls == [] and not window.loading()


def test_an_undo_after_the_fill_keeps_the_sizes_in_memory_and_in_the_file(qtbot, tmp_path):
    window, store, job_id = _old_job_window(
        qtbot, tmp_path, [text_page(), text_page(), a5_page()])
    _open(qtbot, window, store, job_id)
    controller = window.controller()
    qtbot.waitUntil(lambda: controller.job.pages["b1/2"].has_size, timeout=10000)
    controller.rotate("b1/0", 90)  # an edit made after the fill
    controller.undo()
    controller.redo()
    controller.undo()
    assert all(i.has_size for i in controller.job.pages.values())
    done = []
    controller.saver.when_idle(lambda ok, error: done.append(ok))
    qtbot.waitUntil(lambda: done == [True], timeout=5000)
    saved = json.loads(store._job_file(job_id).read_text(encoding="utf-8"))
    assert all(p["width_mm"] > 0 for p in saved["pages"].values())


def test_a_page_whose_file_is_gone_stays_unmarked(qtbot, tmp_path):
    window, store, job_id = _old_job_window(qtbot, tmp_path, [text_page(), a5_page()])
    (tmp_path / "jobs" / job_id / "batches" / "b1.pdf").unlink()
    _open(qtbot, window, store, job_id)
    qtbot.wait(100)
    assert not window.loading()
    assert window.kontrol.model.odd_rows() == []
    assert not any(i.has_size for i in window.controller().job.pages.values())


def test_a_result_for_a_job_that_was_closed_meanwhile_is_dropped(qtbot, tmp_path, monkeypatch):
    gate = threading.Event()
    real = JobStore.read_sizes
    monkeypatch.setattr(JobStore, "read_sizes", staticmethod(
        lambda requests, progress=None: (gate.wait(5), real(requests, progress))[1]))
    window, store, job_id = _old_job_window(qtbot, tmp_path, [text_page(), a5_page()])
    _open(qtbot, window, store, job_id)
    old = window.controller()
    window.yukle._controller = None  # the job is gone from the window
    gate.set()
    qtbot.waitUntil(lambda: not window.loading(), timeout=5000)
    assert not any(i.has_size for i in old.job.pages.values())


def test_the_criterion_is_the_one_the_core_evaluates(qtbot, tmp_path):
    window = _marked_window(qtbot, tmp_path)
    ctl = window.controller()
    assert window.kontrol.select_matching(Criterion("farkli", {"by": ["boyut"]})) == 1
    assert window.kontrol.select_matching(Criterion("farkli", {"by": ["yon"]})) == 1
    assert window.kontrol.select_matching(Criterion("farkli")) == 2
    assert ctl.undo_stack.index() == 0


def test_the_fill_card_waits_its_delay_even_when_the_open_card_was_up(
        qtbot, tmp_path, monkeypatch):
    import time

    gate = threading.Event()
    real_read, real_load = JobStore.read_sizes, JobStore.load

    def slow_read(requests, progress=None):
        gate.wait(5)
        return real_read(requests, progress)

    def slow_load(self, job_id):
        time.sleep(0.5)  # the open takes longer than 300 ms: its loading card is up
        return real_load(self, job_id)

    monkeypatch.setattr(JobStore, "read_sizes", staticmethod(slow_read))
    window, store, job_id = _old_job_window(qtbot, tmp_path, [text_page(), a5_page()])
    window.show()  # a card in a window that is not shown is never visible: the test would be empty
    monkeypatch.setattr(JobStore, "load", slow_load)
    window.yukle.open_job_id(job_id)
    qtbot.waitUntil(lambda: window.loading_card.isVisible(), timeout=3000)  # the open card
    qtbot.waitUntil(lambda: window.controller() is not None, timeout=10000)
    assert window.message.text() == "Sayfa boyutları okunuyor" and window.loading()
    card = window.loading_card
    qtbot.wait(150)  # long after the card would have been reused, far inside 1500 ms
    assert not card.isVisible()
    gate.set()
    qtbot.waitUntil(lambda: window.controller().job.pages["b1/1"].has_size, timeout=10000)
    qtbot.waitUntil(lambda: not window.loading(), timeout=5000)
    assert not card.isVisible()  # a fill that ends quickly never showed one


def test_a_slow_fill_shows_its_card_after_the_delay(qtbot, tmp_path, monkeypatch):
    from evrakci.ui import main_window

    monkeypatch.setattr(main_window, "FILL_CARD_MS", 100)
    gate = threading.Event()
    real = JobStore.read_sizes
    monkeypatch.setattr(JobStore, "read_sizes", staticmethod(
        lambda requests, progress=None: (gate.wait(5), real(requests, progress))[1]))
    window, store, job_id = _old_job_window(qtbot, tmp_path, [text_page(), a5_page()])
    window.show()
    _open(qtbot, window, store, job_id)
    qtbot.waitUntil(lambda: window.loading_card.isVisible(), timeout=3000)
    gate.set()
    qtbot.waitUntil(lambda: not window.loading(), timeout=5000)


def test_setting_the_model_again_connects_the_marks_signal_once(qtbot, tmp_path):
    window = _marked_window(qtbot, tmp_path)
    timeline, model = window.kontrol.timeline, window.kontrol.model
    before = model.receivers("2marks_changed()")
    timeline.setModel(model)
    timeline.setModel(model)
    assert model.receivers("2marks_changed()") == before == 1
