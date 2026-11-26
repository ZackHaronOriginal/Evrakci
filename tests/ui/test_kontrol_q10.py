"""Q-10 (owner-approved Kontrol proposals K-2 .. K-12): selection mark, selection after Del,
Enter on a flagged document, page names in toasts, the overview's second signal, command bar
labels, the separator caption, the save-failure toast and the screen reader text."""

from pathlib import Path

from fakes import job_from_kinds
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.ui import kontrol_overview, theme
from evrakci.ui import kontrol_paint as kp
from evrakci.ui.kontrol_overview import TRACK_H, OverviewStrip
from evrakci.ui.kontrol_review import SAVE_ERROR
from evrakci.ui.main_window import MainWindow
from evrakci.ui.prefs import Prefs

# doc 1 rows 0-2 | sep 3 | doc 2 rows 4-5 | sep 6 | doc 3 rows 7-10 | sep 11 | doc 4 row 12
SPEC = {"a": "pppqppqppppqp"}


def _window(qtbot, tmp_path, width=1366):
    store = JobStore(tmp_path / "jobs")
    job = job_from_kinds(SPEC)
    store.save(job)
    window = MainWindow(store, TemplateStore(tmp_path / "tpl"),
                        settings_path=tmp_path / "ayar.json", prefs=Prefs(tmp_path / "p.ini"))
    qtbot.addWidget(window)
    window.resize(width, 768)
    with qtbot.waitSignal(window.yukle.job_opened, timeout=10000):
        window.yukle.open_job(store.load(job.id))
    window.show_tab("kontrol")
    qtbot.wait(1)
    window.show()
    window.activateWindow()
    assert QTest.qWaitForWindowActive(window)
    window.kontrol.timeline.setFocus()
    return window


def _key(window, key, mods=Qt.KeyboardModifier.NoModifier):
    QTest.keyClick(QApplication.focusWidget() or window, key, mods)


# -- K-2: a selected page is not an approved page ----------------------------------------------
def test_k2_selection_is_a_corner_dot_not_a_check(qapp):
    assert not hasattr(kp, "paint_check_badge")
    image = QImage(60, 60, QImage.Format.Format_ARGB32)
    image.fill(QColor("white"))
    painter = QPainter(image)
    kp.paint_select_dot(painter, QPointF(30, 30))
    painter.end()
    accent = theme.manager().color("accent")
    assert image.pixelColor(30, 30) == accent  # a solid dot: nothing drawn over it (no check)


def test_k2_a_selected_deleted_page_draws_the_dot_and_no_check(qtbot, tmp_path, monkeypatch):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    screen.timeline.select_rows(0, 0, 0)
    screen.controller.run("Sayfayı sil", lambda j: j.delete_page("a/0"))
    screen.timeline.select_rows(0, 0, 0)  # the deleted page is selected again
    seen = []
    monkeypatch.setattr(kp, "paint_select_dot", lambda *a: seen.append("dot"))
    screen.timeline.viewport().grab()
    assert "dot" in seen


# -- K-3: after Del the screen agrees with itself ------------------------------------------------
def test_k3_del_moves_the_selection_to_the_next_page_that_stays(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    ctl = window.controller()
    screen.timeline.select_rows(4, 5, 5)  # all of document 2
    _key(window, Qt.Key.Key_Delete)
    assert ctl.job.deleted == {"a/4", "a/5"}
    # the separator at row 6 is not a page that stays: the first page of document 3 is
    assert screen.selected_rows() == [7]
    assert screen.current_row() == 7
    assert window.registry.action("kontrol.onayla").isEnabled()
    assert window.registry.action("kontrol.sil").text().replace("&", "") == "Sayfayı sil"
    assert window.toaster.current_text().startswith("Belge 2 (sayfa 5–6):")


def test_k3_at_the_end_the_selection_goes_back_to_the_page_before(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    screen.timeline.select_rows(12, 12, 12)  # the last page
    screen.toggle_delete()
    assert screen.selected_rows() == [10]


def test_k3_undo_brings_back_exactly_the_deleted_pages(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    ctl = window.controller()
    screen.timeline.select_rows(1, 2, 2)
    screen.toggle_delete()
    assert ctl.job.deleted == {"a/1", "a/2"}
    assert screen.selected_rows() == [4]
    steps = ctl.undo_stack.index()
    _key(window, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
    assert ctl.job.deleted == set()
    assert ctl.undo_stack.index() == steps - 1
    _key(window, Qt.Key.Key_Y, Qt.KeyboardModifier.ControlModifier)
    assert ctl.job.deleted == {"a/1", "a/2"}


def test_k3_restore_works_on_the_chosen_deleted_pages(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    ctl = window.controller()
    screen.timeline.select_rows(1, 2, 2)
    screen.toggle_delete()
    screen.timeline.select_rows(1, 2, 2)  # choose the deleted pages again
    assert window.registry.action("kontrol.sil").text().replace("&", "") == "2 sayfayı geri getir"
    screen.toggle_delete()
    assert ctl.job.deleted == set()


def test_k3_with_the_loupe_open_only_the_shown_page_goes_and_the_selection_stays(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    ctl = window.controller()
    screen.timeline.select_rows(0, 2, 2)
    screen.open_loupe(1)
    screen.toggle_delete()
    assert ctl.job.deleted == {"a/1"}
    assert 4 not in screen.selected_rows()  # the selection did not jump to another document


# -- K-4: Enter never passes a Kontrol flag silently ---------------------------------------------
def test_k4_enter_says_when_the_document_had_a_kontrol_flag(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    said = []
    screen.controller.status.connect(said.append)
    screen.model.set_checks({2: ["eksik sayfa"]})
    screen.go_to_document(2)
    _key(window, Qt.Key.Key_Return)
    assert said[-1] == "Belge 2 kontrol işaretiyle onaylandı."
    assert 2 in screen.model.reviewed and screen.current_document() == 3
    _key(window, Qt.Key.Key_Return)
    assert said[-1] == "Belge 3 onaylandı, Belge 4."


def test_k4_the_last_document_keeps_its_sentence_and_flag_is_still_named(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    said = []
    screen.controller.status.connect(said.append)
    screen.go_to_document(4)
    _key(window, Qt.Key.Key_Return)
    assert said[-1] == "Belge 4 onaylandı; bu son belge."
    screen.model.set_checks({3: ["eksik sayfa"]})
    screen.go_to_document(3)
    _key(window, Qt.Key.Key_Return)
    assert said[-1] == "Belge 3 kontrol işaretiyle onaylandı."


def test_k4_approving_again_says_nothing_new_and_undo_is_exact(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    ctl = window.controller()
    screen.go_to_document(1)
    steps = ctl.undo_stack.index()
    _key(window, Qt.Key.Key_Return)
    assert ctl.undo_stack.index() == steps + 1
    screen.go_to_document(1)
    said = []
    ctl.status.connect(said.append)
    _key(window, Qt.Key.Key_Return)  # already İncelendi: no second step, no second sentence
    assert ctl.undo_stack.index() == steps + 1
    assert not any("onaylandı" in text for text in said)
    ctl.undo_stack.undo()
    assert screen.model.reviewed == set()


# -- K-5: toasts name the pages, because document numbers move -------------------------------------
def test_k5_the_merge_toast_names_the_pages(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    screen.go_to_document(2)
    screen.merge_current()
    assert window.toaster.current_text() == "Belge 2, Belge 1 ile birleştirildi (sayfa 5–6)."


# -- K-7: the overview's second signal ---------------------------------------------------------
def test_k7_a_kontrol_square_stands_taller_than_the_track(qtbot, qapp):
    strip = OverviewStrip()
    qtbot.addWidget(strip)
    strip.resize(600, strip.height())
    strip.set_state(3, {2}, set())
    strip.show()
    image = strip.grab().toImage()
    track = strip.track_rect()
    first, second = strip._segment(1, track), strip._segment(2, track)
    above = int(track.y()) - 2  # inside the notch, above the track
    assert second.height() == TRACK_H
    assert not hasattr(kontrol_overview, "KONTROL_NOTCH")  # the notch is the s1 token
    notch = theme.manager().size("s1")
    assert image.pixelColor(int(second.center().x()), int(track.y()) - notch) != \
        image.pixelColor(int(first.center().x()), int(track.y()) - notch)
    assert image.pixelColor(int(second.center().x()), int(track.y()) - notch - 2) == \
        image.pixelColor(int(first.center().x()), int(track.y()) - notch - 2)
    assert image.pixelColor(int(second.center().x()), above) != \
        image.pixelColor(int(first.center().x()), above)


# -- K-8: labels only while the bar has room; the separator is captioned --------------------------
def test_k8_labels_show_when_the_bar_is_wide_and_give_way_when_it_is_narrow(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, width=1920)
    bar = window.command_bar("kontrol")
    qtbot.wait(20)
    merge = bar.button_for("kontrol.birlestir")
    delete = bar.button_for("kontrol.sil")
    nxt = bar.button_for("kontrol.sonraki_incelenmemis")
    assert merge.labelled() and merge.text() == "Birleştir"
    assert delete.labelled() and delete.text() == "Sil"
    assert nxt.labelled() and nxt.text() == "Sonraki incelenmemiş"
    window.resize(1000, 768)
    qtbot.wait(20)
    assert not (merge.labelled() and delete.labelled() and nxt.labelled())
    assert bar.minimumSizeHint().width() <= 1000  # labels give way, the window does not grow
    assert delete.accessibleName()  # the tooltip stays the name of an icon button


def test_k8_tab_focus_shows_the_tooltip_of_an_icon_button(qtbot, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QToolTip
    window = _window(qtbot, tmp_path)
    bar = window.command_bar("kontrol")
    button = bar.button_for("kontrol.saga_dondur")
    shown = []
    monkeypatch.setattr(QToolTip, "showText", lambda pos, text, *a: shown.append(text))
    button.setFocus(Qt.FocusReason.TabFocusReason)
    assert shown and shown[-1] == button.toolTip()
    shown.clear()
    button.clearFocus()
    button.setFocus(Qt.FocusReason.MouseFocusReason)
    assert not shown


def test_k8_the_separator_is_captioned_like_the_other_pages(qtbot, tmp_path, monkeypatch):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    texts = []
    original = QPainter.drawText

    def spy(self, *args):
        texts.append(args[-1] if isinstance(args[-1], str) else None)
        return original(self, *args)

    monkeypatch.setattr(QPainter, "drawText", spy)
    screen.timeline.viewport().grab()
    assert "Ayraç 4" in texts


# -- K-10: a failed save is a red toast with a way to try again -----------------------------------
def test_k10_a_failed_save_is_a_red_toast_that_can_be_retried(qtbot, tmp_path, monkeypatch):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    ctl = window.controller()
    real = Path.write_text
    state = {"fail": True}

    def write(self, *args, **kwargs):
        if state["fail"] and self.name == "incelendi.json":
            raise OSError("disk full")
        return real(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", write)
    screen.go_to_document(1)
    _key(window, Qt.Key.Key_Return)
    assert SAVE_ERROR == "Onay kaydedilemedi. İş klasörünü, boş yeri ve yazma iznini kontrol edin."
    assert window.toaster.current_text() == SAVE_ERROR
    toast = window.toaster._current
    assert toast.action_button.text() == "Yeniden dene"
    assert 1 in screen.model.reviewed  # the approval stays in memory, and Ctrl+Z still works
    state["fail"] = False
    toast.action_button.click()
    qtbot.waitUntil(lambda: window.toaster.current_text() == "Onay kaydedildi.", timeout=2000)
    saved = (Path(ctl.store.root) / ctl.job.id / "incelendi.json").read_text(encoding="utf-8")
    assert "a/0|a/1|a/2" in saved


def test_k10_a_second_failure_shows_a_fresh_toast(qtbot, tmp_path, monkeypatch):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    real = Path.write_text

    def write(self, *args, **kwargs):
        if self.name == "incelendi.json":
            raise OSError("read-only")
        return real(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", write)
    screen.go_to_document(1)
    _key(window, Qt.Key.Key_Return)
    window.toaster._current.action_button.click()
    qtbot.waitUntil(lambda: window.toaster.current_text() == SAVE_ERROR
                    and window.toaster.pending() == 0, timeout=2000)
    assert window.toaster._current.action_button.text() == "Yeniden dene"


# -- K-11: the page list tells a screen reader its main keys --------------------------------------
def test_k11_the_page_list_names_the_main_keys(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    text = window.kontrol.timeline.accessibleDescription()
    assert "K keser, M birleştirir, Del siler, R döndürür." in text
    assert "Enter belgeyi onaylar" in text


# -- K-9 (already built): the status bar slider follows the loupe's own zoom -----------------------
def test_k9_the_zoom_slider_drives_the_loupe_while_it_is_open(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    screen.open_loupe(0)
    entry = window._zoom["kontrol"]
    assert entry[0] is screen.loupe().zoom and entry[1] == "Önizleme"
    screen.close_loupe()
    qtbot.waitUntil(lambda: window._zoom["kontrol"][0] is screen.zoom, timeout=2000)


# -- review round 1 ------------------------------------------------------------------------------
def _fail_writes(monkeypatch):
    real = Path.write_text
    state = {"fail": True}

    def write(self, *args, **kwargs):
        if state["fail"] and self.name == "incelendi.json":
            raise OSError("disk full")
        return real(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", write)
    return state


def test_r1_two_deletes_in_a_row_show_the_newest_message_at_once(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    ctl = window.controller()
    screen.go_to_row(0)
    _key(window, Qt.Key.Key_Delete)
    assert window.toaster.current_text() == "Sayfa 1 silinecek."
    _key(window, Qt.Key.Key_Delete)  # the selection moved on: this deletes page 2
    assert window.toaster.current_text() == "Sayfa 2 silinecek."
    assert window.toaster.pending() == 0
    window.toaster._current.action_button.click()  # Geri al belongs to its own step
    assert ctl.job.deleted == {"a/0"}


def test_r1_a_restore_replaces_the_delete_toast(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    screen.go_to_row(0)
    screen.toggle_delete()
    screen.timeline.select_rows(0, 0, 0)
    screen.toggle_delete()
    assert window.toaster.current_text() == "Sayfa 1 geri getirildi."
    assert window.toaster.pending() == 0


def test_r1_an_error_toast_does_not_wait_behind_an_info_toast(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    window.toaster.show("Bilgi bir")
    window.toaster.show("Bilgi iki")
    window.toaster.show("Hata", kind="error")
    assert window.toaster.current_text() == "Hata"


def test_r1_a_failed_approve_is_not_worded_as_a_success(qtbot, tmp_path, monkeypatch):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    said = []
    screen.controller.status.connect(said.append)
    _fail_writes(monkeypatch)
    screen.go_to_document(1)
    _key(window, Qt.Key.Key_Return)
    assert said[-1] == SAVE_ERROR
    assert not any("onaylandı" in text for text in said)
    assert all("onaylandı" not in change.text for _i, change in screen._history)
    assert window.toaster.current_text() == SAVE_ERROR  # shown at once, not queued
    assert screen.current_document() == 2  # the flow goes on


def test_r1_the_title_band_keeps_the_failure_until_a_write_works(qtbot, tmp_path, monkeypatch):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    state = _fail_writes(monkeypatch)
    screen.go_to_document(1)
    _key(window, Qt.Key.Key_Return)
    band = window.job_switch.save_state
    assert band.state() == "failed" and band.toolTip() == SAVE_ERROR
    window.toaster.dismiss()  # the toast is gone, the failure is not
    window._saved()  # the job's own write succeeds meanwhile: still failed for the approvals
    assert band.state() == "failed"
    state["fail"] = False
    band._retry.click()
    assert band.state() == "saved"
    assert window.toaster.current_text() != SAVE_ERROR


def test_r1_recovery_removes_the_red_toast(qtbot, tmp_path, monkeypatch):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    state = _fail_writes(monkeypatch)
    screen.go_to_document(1)
    _key(window, Qt.Key.Key_Return)
    assert window.toaster.current_text() == SAVE_ERROR
    state["fail"] = False
    screen.go_to_document(2)
    _key(window, Qt.Key.Key_Return)  # the next approval writes both: the failure is over
    assert window.toaster.current_text() != SAVE_ERROR
    assert window.job_switch.save_state.state() == "saved"


def test_r1_closing_with_unsaved_approvals_retries_and_asks(qtbot, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    state = _fail_writes(monkeypatch)
    screen.go_to_document(1)
    _key(window, Qt.Key.Key_Return)
    window.toaster.dismiss()
    window.close_job()  # Ctrl+W: the retry fails again, the same question as for the job
    qtbot.waitUntil(window._question_open, timeout=3000)
    box = window._close_question
    assert box.text() == ("Değişiklikler kaydedilemedi. Yine de kapatılsın mı? "
                          "Son değişiklikler kaybolur.")
    box.button(QMessageBox.StandardButton.No).click()
    qtbot.waitUntil(lambda: not box.isVisible(), timeout=3000)
    assert window.controller() is not None
    state["fail"] = False  # the disk works: the retry saves, and the job closes silently
    window.close_job()
    qtbot.waitUntil(lambda: window.controller() is None, timeout=3000)


def test_r1_yes_lets_unsaved_approvals_go_and_the_window_closes(qtbot, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    _fail_writes(monkeypatch)
    screen.go_to_document(1)
    _key(window, Qt.Key.Key_Return)
    assert window._unsaved_pending()
    assert window.close() is False
    qtbot.waitUntil(window._question_open, timeout=3000)
    window._close_question.button(QMessageBox.StandardButton.Yes).click()
    qtbot.waitUntil(lambda: window._closed, timeout=3000)


def test_r1_select_all_and_del_leaves_no_selection_and_says_the_count(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    said = []
    screen.controller.status.connect(said.append)
    screen.select_all()
    screen.toggle_delete()
    assert screen._chosen_ids() == []
    assert said[-1] == "10 sayfa silinecek."
    assert screen.controller.job.deleted  # the pages are deleted, undoably
    screen.controller.undo_stack.undo()
    assert not screen.controller.job.deleted


def test_r1_the_merge_sentence_and_the_overview_tooltip_texts(qtbot, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QToolTip
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    screen.go_to_document(3)
    screen.merge_current()
    assert window.toaster.current_text() == "Belge 3, Belge 2 ile birleştirildi (sayfa 8–11)."
    shown = []
    monkeypatch.setattr(QToolTip, "showText", lambda pos, text, *a: shown.append(text))
    screen.strip.set_state(3, {2}, set())
    track = screen.strip.track_rect()
    from PySide6.QtGui import QMouseEvent
    point = screen.strip._segment(2, track).center()
    event = QMouseEvent(QMouseEvent.Type.MouseMove, point, screen.strip.mapToGlobal(point),
                        Qt.MouseButton.NoButton, Qt.MouseButton.NoButton,
                        Qt.KeyboardModifier.NoModifier)
    screen.strip.mouseMoveEvent(event)
    assert shown[-1] == "Belge 2, Kontrol bekliyor"
