"""Phase 4 whole-app review: M-1 (close refusal), M-2 (toast height), B-017 (template_map),
B-033 (R, Shift+R, Del with the loupe open)."""

from PySide6.QtWidgets import QLabel, QMainWindow, QMessageBox
from test_kontrol_a import _window
from test_main_window import _failed_save_window

from evrakci.ui import motion, theme
from evrakci.ui.feedback import Toaster


# -- M-1 ---------------------------------------------------------------------------------
def test_refused_close_clears_closing(qtbot, tmp_path, monkeypatch):
    window, _state = _failed_save_window(qtbot, tmp_path, monkeypatch)
    monkeypatch.setattr(QMessageBox, "question",
                        lambda *a, **k: QMessageBox.StandardButton.Yes)
    window.disa_aktar.task = object()  # an export is running
    monkeypatch.setattr(window.disa_aktar, "cancel", lambda: None)
    assert window.close() is False  # asked, answered Yes, waits for the task
    assert window._closing
    window.disa_aktar.task = None
    window._work_stopped()
    qtbot.waitUntil(lambda: window._close_warned, timeout=3000)  # the close retries the save
    assert window.controller() is not None  # it still fails: refused
    qtbot.waitUntil(lambda: not window._closing, timeout=3000)
    # Dışa Aktar follows undo again
    window.show_tab("disa_aktar")
    calls = []
    monkeypatch.setattr(window.disa_aktar, "refresh", lambda *a: calls.append(1))
    window._job_stack_changed()
    assert calls
    # a task that ends later does not close the window
    closed = []
    monkeypatch.setattr(window, "close", lambda: closed.append(1))
    window._work_stopped()
    qtbot.wait(50)
    assert not closed


# -- M-2 ---------------------------------------------------------------------------------
def test_long_toast_is_fully_visible_at_130_and_150(qapp):
    motion.set_reduced_motion_override(True)
    manager = theme.manager()
    text = ("Ayraç sayfası PDF dosyası yazılamadı: hedef klasör dolu ya da yazmaya kapalı, "
            "başka bir klasör seçip yeniden deneyin ya da diskte yer açın. " * 4)
    try:
        for scale in (130, 150):
            manager.set_text_scale(scale)
            win = QMainWindow()
            win.resize(900, 600)
            win.show()
            toaster = Toaster(win)
            toaster.show(text)
            toast = toaster._current
            label = next(w for w in toast.findChildren(QLabel) if w.text() == text)
            assert label.height() >= label.heightForWidth(label.width()), scale
            assert label.heightForWidth(label.width()) > 2 * label.fontMetrics().height()
            assert win.rect().contains(toast.geometry().adjusted(12, 12, -12, -12)), scale
            win.close()
    finally:
        manager.set_text_scale(100)
        motion.set_reduced_motion_override(None)


# -- B-017 -------------------------------------------------------------------------------
def test_template_map_names_a_damaged_template(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    store = window.template_store
    good = store.create("Sağlam")
    bad = store.create("Bozuk")
    store._path(bad.id).write_text("{ bozuk", encoding="utf-8")
    window.message.setText("")
    found = window.template_map()
    assert list(found) == [good.id]
    assert window.message.text() == f"Şablon dosyası okunamadı: {bad.id}"


# -- B-033 ------------------------------------------------------------------------------
def _loupe_over_three(window):
    screen = window.kontrol
    screen.timeline.select_rows(0, 2, 1)  # three selected, page 2 is the current one
    screen.open_loupe(1)
    assert screen._loupe.is_open() and screen.current_row() == 1
    screen.timeline.select_rows(0, 2, 1)
    return screen


def test_r_shift_r_del_act_on_the_loupe_page_only(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    ctl = window.controller()
    screen = _loupe_over_three(window)
    screen.rotate_selected(90)
    assert ctl.job.rotations == {"a/1": 90}
    screen.rotate_selected(-90)
    assert not ctl.job.rotations
    screen.toggle_delete()
    assert ctl.job.deleted == {"a/1"}


def test_r_shift_r_del_act_on_the_selection_without_the_loupe(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    ctl = window.controller()
    screen = window.kontrol
    screen.timeline.select_rows(0, 2, 1)
    screen.rotate_selected(90)
    assert ctl.job.rotations == {"a/0": 90, "a/1": 90, "a/2": 90}
    screen.rotate_selected(-90)
    screen.toggle_delete()
    assert ctl.job.deleted == {"a/0", "a/1", "a/2"}
