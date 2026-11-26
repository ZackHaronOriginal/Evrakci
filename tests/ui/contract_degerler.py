"""Değerler' rows of the shortcut contract (Phase 3, step 3D): steps and plans, registered into
`contract_helpers.HELPERS` and `contract_helpers.PLANS`.

The tests of this tab share one demo window ("job_degerler"): three documents (rows 0-2), two
value columns (3 = Sicil_No, 4 = Firma_Adi), "Tüm değerler" view, nothing reviewed, and one
value that needs a check: row 1, column 3 ("48Z13", suggestion 48213). Every test puts the
job back through the undo stack.
"""
from __future__ import annotations

import re
import time
from unittest import mock

from contract_helpers import (
    PLANS,
    Ctx,
    Plan,
    assert_focus_ring,
    heard,
    helper,
    said,
    settle,
    slot_texts,
    wait_until,
)
from PySide6.QtCore import QItemSelectionModel, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from evrakci.ui import degerler
from evrakci.ui.degerler_model import confirm

P_NOTHING_RUNNING = "Şu an durdurulacak bir iş yok."
NO_CHECK = "Kontrol bekleyen değer yok."

_Sel = QItemSelectionModel.SelectionFlag


def _d(c: Ctx):
    return c.win.degerler


def _cur(c: Ctx) -> tuple[int, int]:
    index = _d(c).table.currentIndex()
    return (index.row(), index.column())


def restore_job(c: Ctx) -> None:
    """Whatever the test edits is undone when it ends."""
    stack = c.win.controller().undo_stack
    base = stack.index()
    d = _d(c)

    def back() -> None:
        stack.setIndex(base)
        d.refresh()
        settle()

    c.undo.append(back)


def pick(c: Ctx, row: int, column: int, rows: tuple[int, ...] = ()) -> None:
    """The value at (row, column) is current and the table has focus; `rows` are selected too."""
    d = _d(c)
    d.table.setFocus()
    d.table.setCurrentIndex(d.model.index(row, column))
    sm = d.table.selectionModel()
    if rows:
        sm.clearSelection()
        for r in rows:
            sm.select(d.model.index(r, 0), _Sel.Select | _Sel.Rows)
    settle()
    assert QApplication.focusWidget() is d.table and _cur(c) == (row, column)


def selected_rows(c: Ctx) -> list[int]:
    return sorted(i.row() for i in _d(c).table.selectionModel().selectedRows())


def _reviewed(c: Ctx) -> list[list[bool]]:
    d = _d(c)
    return [[d.model.cell_at(d.model.index(r, col)).reviewed for col in (3, 4)]
            for r in range(d.model.rowCount())]


def _in_view(c: Ctx, row: int, column: int) -> bool:
    d = _d(c)
    return d.table.viewport().rect().intersects(d.table.visualRect(d.model.index(row, column)))


def _snap(c: Ctx) -> dict:
    if c.win.controller() is None:
        return {"status": c.win.message.text()}
    return {"index": c.win.controller().undo_stack.index(), "cur": _cur(c),
            "reviewed": _reviewed(c), "selected": selected_rows(c),
            "status": c.win.message.text()}


helper("snap.degerler")(_snap)


def _toast_undo(c: Ctx) -> bool:
    toast = c.win.toaster._current
    return toast is not None and any(b.text() == "Geri al" for b in toast.findChildren(QPushButton))


# -- Enter, Ctrl+Enter ---------------------------------------------------------------------------
@helper("pre.degerler_flagged")
def _pre_flagged(c: Ctx) -> None:
    restore_job(c)
    pick(c, 1, 3)


@helper("effect.degerler_accepted")
def _effect_accepted(c: Ctx) -> None:
    d = _d(c)
    cell = d.model.cell_at(d.model.index(1, 3))
    assert cell.reviewed and not cell.value.flagged, "the suggestion was not accepted"
    assert _cur(c) == (1, 4), _cur(c)


@helper("feedback.degerler_accepted")
def _feedback_accepted(c: Ctx) -> None:
    assert "48213 kaydedildi (öneri)." in heard(c.win), heard(c.win)
    c.win.toaster.dismiss()  # the confirmation shows first; the hint about what is left follows
    text = heard(c.win)
    assert re.search(r"Kontrol gereken değer kalmadı; \d+ değer incelenmedi\. Enter sıradakini "
                     r"onaylar\.", text), text
    assert "1 / 6 incelendi" in slot_texts(c.win, "degerler"), slot_texts(c.win, "degerler")
    assert c.win.controller().undo_stack.undoText() == "Onayla"
    assert _in_view(c, 1, 4) and QApplication.focusWidget() is _d(c).table


@helper("effect.degerler_read_accepted")
def _effect_read_accepted(c: Ctx) -> None:
    d = _d(c)
    cell = d.model.cell_at(d.model.index(1, 3))
    assert cell.reviewed and not cell.value.flagged, "the read was not stored"
    assert cell.value.value == "48Z13" and cell.value.value != cell.value.suggestion, \
        cell.value
    assert _cur(c) == (1, 4), _cur(c)


@helper("feedback.degerler_read_accepted")
def _feedback_read_accepted(c: Ctx) -> None:
    assert "48Z13 kaydedildi (okunan)." in heard(c.win), heard(c.win)
    assert _toast_undo(c), "the confirmation has no Geri al"
    assert c.win.controller().undo_stack.undoText() == "Onayla"
    assert _in_view(c, 1, 4) and QApplication.focusWidget() is _d(c).table


@helper("pre.degerler_two_rows")
def _pre_two_rows(c: Ctx) -> None:
    restore_job(c)
    pick(c, 0, 3, rows=(0, 1))
    assert selected_rows(c) == [0, 1]


@helper("effect.degerler_rows_accepted")
def _effect_rows_accepted(c: Ctx) -> None:
    assert _reviewed(c) == [[True, True], [True, True], [False, False]], _reviewed(c)


@helper("feedback.degerler_rows_accepted")
def _feedback_rows_accepted(c: Ctx) -> None:
    assert c.win.toaster.current_text() == "4 değer onaylandı; 1 tanesi Kontrol'dü.", heard(c.win)
    assert _toast_undo(c)
    assert c.win.controller().undo_stack.undoText() == "4 değeri onayla"
    assert "4 / 6 incelendi" in slot_texts(c.win, "degerler"), slot_texts(c.win, "degerler")


# -- F2, V ---------------------------------------------------------------------------------------
@helper("pre.degerler_value")
def _pre_value(c: Ctx) -> None:
    restore_job(c)
    d = _d(c)

    def close_editor() -> None:
        editor = d.table.open_editor_widget()
        if d.table.is_editing() and editor is not None:
            QTest.keyClick(editor, Qt.Key.Key_Escape)
            settle()

    c.undo.append(close_editor)
    pick(c, 0, 3)


@helper("effect.degerler_editor_open")
def _effect_editor_open(c: Ctx) -> None:
    assert _d(c).table.is_editing()
    assert _d(c).table.open_editor_widget() is not None


@helper("feedback.degerler_editor_open")
def _feedback_editor_open(c: Ctx) -> None:
    d = _d(c)
    assert d.table.hint.isVisibleTo(c.win), "no key hint under the cell"
    editor = d.table.open_editor_widget()
    assert editor.text() == "48190" and QApplication.focusWidget() is editor


@helper("pre.degerler_corrected")
def _pre_corrected(c: Ctx) -> None:
    restore_job(c)
    d = _d(c)
    assert d.model.setData(d.model.index(0, 3), "99999")
    d.refresh()
    pick(c, 0, 3)


@helper("effect.degerler_reverted")
def _effect_reverted(c: Ctx) -> None:
    d = _d(c)
    value = d.model.cell_at(d.model.index(0, 3)).value
    assert value.flagged and not value.edited and value.suggestion, value
    assert _cur(c) == (0, 3), _cur(c)


@helper("feedback.degerler_reverted")
def _feedback_reverted(c: Ctx) -> None:
    assert re.fullmatch(r"Okunana dönüldü: .+\. Kontrol'e alındı\.",
                        c.win.toaster.current_text()), heard(c.win)
    assert c.win.controller().undo_stack.undoText() == "Okunana dön"


@helper("broken.degerler_uncorrected")
def _broken_uncorrected(c: Ctx) -> None:
    pick(c, 0, 3)


@helper("pre.degerler_variant")
def _pre_variant(c: Ctx) -> None:
    pick(c, 1, 4)

    def back() -> None:
        c.win.sablon.set_drawing(False)
        c.win.show_tab("degerler")
        settle()

    c.undo.append(back)


@helper("effect.degerler_variant")
def _effect_variant(c: Ctx) -> None:
    win = c.win
    assert win.current_tab() == "sablonlar"
    assert win.sablon.example == 2, win.sablon.example
    assert win.sablon.variable_name == "Firma_Adi"
    assert win.sablon.is_drawing()


@helper("feedback.degerler_variant")
def _feedback_variant(c: Ctx) -> None:
    assert c.win.sablon.canvas.viewport().cursor().shape() == Qt.CursorShape.CrossCursor
    assert c.win.registry.action("sablonlar.kutu_ciz").isChecked()


# -- Esc, Ctrl+A, Space --------------------------------------------------------------------------
@helper("pre.degerler_three_rows")
def _pre_three_rows(c: Ctx) -> None:
    pick(c, 1, 3, rows=(0, 1, 2))
    assert selected_rows(c) == [0, 1, 2]


@helper("effect.degerler_one_row")
def _effect_one_row(c: Ctx) -> None:
    assert selected_rows(c) == [1] and _cur(c) == (1, 3), (selected_rows(c), _cur(c))


@helper("feedback.degerler_one_row")
def _feedback_one_row(c: Ctx) -> None:
    sm = _d(c).table.selectionModel()
    assert not sm.isRowSelected(0, _d(c).model.index(0, 0).parent())
    assert not sm.isRowSelected(2, _d(c).model.index(0, 0).parent())
    assert QApplication.focusWidget() is _d(c).table


@helper("broken.degerler_one_row")
def _broken_one_row(c: Ctx) -> None:
    pick(c, 1, 3, rows=(1,))


@helper("na.degerler_quiet")
def _na_quiet(c: Ctx) -> None:
    """Esc with one row and no page view: nothing to dismiss, nothing changes, nothing is said
    (owner may accept this, M-45)."""
    now = _snap(c)
    for name in ("index", "cur", "reviewed", "selected"):
        assert now[name] == c.snap[name], name
    assert c.win.message.text() == c.snap["status"] and not c.win.toaster.current_text()


@helper("na.degerler_revert_says")
def _na_revert_says(c: Ctx) -> None:
    """R on a value that was never corrected says so (Q-09) and changes nothing."""
    now = _snap(c)
    for name in ("index", "cur", "reviewed", "selected"):
        assert now[name] == c.snap[name], name
    assert said(c.win, "Düzeltilmiş bir değer yok."), heard(c.win)


@helper("pre.degerler_one_row_selected")
def _pre_one_row_selected(c: Ctx) -> None:
    pick(c, 1, 3, rows=(1,))


@helper("effect.degerler_all_rows")
def _effect_all_rows(c: Ctx) -> None:
    assert selected_rows(c) == [0, 1, 2]


@helper("feedback.degerler_all_rows")
def _feedback_all_rows(c: Ctx) -> None:
    sm, d = _d(c).table.selectionModel(), _d(c)
    assert all(sm.isRowSelected(r, d.model.index(0, 0).parent()) for r in range(3))
    assert QApplication.focusWidget() is d.table


@helper("pre.degerler_row2")
def _pre_row2(c: Ctx) -> None:
    pick(c, 1, 3)
    c.undo.append(lambda: c.win.show_tab("degerler"))


@helper("effect.degerler_kontrol_at_doc2")
def _effect_kontrol_at_doc2(c: Ctx) -> None:
    assert c.win.current_tab() == "kontrol"
    assert c.win.kontrol.current_document() == 2


@helper("feedback.degerler_kontrol_at_doc2")
def _feedback_kontrol_at_doc2(c: Ctx) -> None:
    assert said(c.win, "Belge 2 seçildi."), f"nothing said: {heard(c.win)!r}"
    assert QApplication.focusWidget() is c.win.kontrol.timeline, "focus is not in the timeline"


@helper("na.degerler_stays_on_tab")
def _na_stays_on_tab(c: Ctx) -> None:
    assert c.win.current_tab() == "degerler"


@helper("pre.degerler_page_view")
def _pre_page_view(c: Ctx) -> None:
    pick(c, 1, 3)

    def close() -> None:
        d = _d(c)
        if d.loupe is not None and d.loupe.isVisible():
            d.loupe.close_loupe()
            wait_until(lambda: not d.loupe.isVisible())

    c.undo.append(close)


@helper("effect.degerler_page_view_open")
def _effect_page_view_open(c: Ctx) -> None:
    loupe = _d(c).loupe
    assert loupe is not None and loupe.is_open()


@helper("feedback.degerler_page_view_open")
def _feedback_page_view_open(c: Ctx) -> None:
    d = _d(c)
    row = d.model.row_at(1)
    title = f"Belge {row.number}, sayfa {row.first}"
    texts = [lb.text() for lb in d.loupe.findChildren(QLabel) if lb.isVisible()]
    assert title in texts, (title, texts)
    d.loupe.close_loupe()
    assert wait_until(lambda: not d.loupe.isVisible()), "the page view did not close"
    assert QApplication.focusWidget() is d.table, "closing did not return to the table"


# -- N, Shift+N, Tab, Shift+Tab ------------------------------------------------------------------
@helper("pre.degerler_before_check")
def _pre_before_check(c: Ctx) -> None:
    pick(c, 0, 3)


@helper("pre.degerler_after_check")
def _pre_after_check(c: Ctx) -> None:
    pick(c, 2, 4)


@helper("effect.degerler_at_check")
def _effect_at_check(c: Ctx) -> None:
    assert _cur(c) == (1, 3), _cur(c)


@helper("feedback.degerler_at_check")
def _feedback_at_check(c: Ctx) -> None:
    assert _in_view(c, 1, 3)
    assert QApplication.focusWidget() is _d(c).table
    assert_focus_ring(c.win)


@helper("broken.degerler_no_check")
def _broken_no_check(c: Ctx) -> None:
    restore_job(c)
    d = _d(c)
    row = d.model.row_at(1)
    cell = d.model.cell_at(d.model.index(1, 3))
    assert c.win.controller().run("Onayla", lambda job: confirm(job, row.document,
                                                                       cell.key))
    d.refresh()
    settle()
    pick(c, 0, 3)
    assert not c.win.registry.is_enabled("degerler.sonraki_kontrol")


@helper("na.degerler_no_check_says")
def _na_no_check_says(c: Ctx) -> None:  # INTENDED (M-42): the existing text, reachable by key
    assert said(c.win, NO_CHECK), f"nothing said: {heard(c.win)!r}"


@helper("effect.degerler_next_value")
def _effect_next_value(c: Ctx) -> None:
    assert _cur(c) == (0, 4), _cur(c)


@helper("effect.degerler_previous_value")
def _effect_previous_value(c: Ctx) -> None:
    assert _cur(c) == (0, 3), _cur(c)


@helper("pre.degerler_second_value")
def _pre_second_value(c: Ctx) -> None:
    pick(c, 0, 4)


@helper("feedback.degerler_value_moved")
def _feedback_value_moved(c: Ctx) -> None:
    r, col = _cur(c)
    assert _in_view(c, r, col) and QApplication.focusWidget() is _d(c).table
    assert_focus_ring(c.win)


@helper("broken.degerler_last_value")
def _broken_last_value(c: Ctx) -> None:
    pick(c, 2, 4)


@helper("broken.degerler_first_value")
def _broken_first_value(c: Ctx) -> None:
    pick(c, 0, 3)


@helper("na.degerler_focus_left")
def _na_focus_left(c: Ctx) -> None:
    """Past the last (before the first) value the key leaves the table to the next control."""
    focus = QApplication.focusWidget()
    assert focus is not None and focus is not _d(c).table, "focus stayed in the table"
    assert _d(c).table.currentIndex().isValid()


# -- Ctrl+. --------------------------------------------------------------------------------------
@helper("pre.degerler_reading")
def _pre_reading(c: Ctx) -> None:
    """A real read through the screen's own task, with a reader that takes its time; the job is
    put back afterwards (a cancelled read stores what it finished)."""
    restore_job(c)
    d = _d(c)

    class Engine:
        def available(self):
            return None

    def slow(*_args, **_kwargs):
        time.sleep(0.3)
        return {}

    patchers = [mock.patch.object(d, "_engine", lambda: Engine()),
                mock.patch.object(degerler, "read_document", slow)]
    for p in patchers:
        p.start()
        c.undo.append(p.stop)

    def finish() -> None:
        if d.task is not None:
            d.task.cancel()
            wait_until(lambda: d.task is None)

    c.undo.append(finish)
    d.read_values(False)
    assert wait_until(lambda: c.win.registry.is_enabled("degerler.durdur")), "no read is running"
    d.table.setFocus()
    settle()


@helper("effect.degerler_read_stopped")
def _effect_read_stopped(c: Ctx) -> None:
    d = _d(c)
    assert wait_until(lambda: d.task is None, 15000), "the read was not stopped"
    assert d.read_count() < 3, "every document was read: the read was not cut short"


@helper("feedback.degerler_read_stopped")
def _feedback_read_stopped(c: Ctx) -> None:
    d = _d(c)
    assert re.fullmatch(r"Okuma durduruldu: \d+ belge okundu ve kaydedildi, "
                        r"kalanlar henüz okunmadı\.",
                        c.win.toaster.current_text()), heard(c.win)
    assert not d.progress.isVisible() and not d.cancel_button.isVisible()
    assert d.read_button.isEnabled(), "the read buttons did not come back"


@helper("broken.degerler_nothing_running")
def _broken_nothing_running(c: Ctx) -> None:
    pick(c, 0, 3)
    assert _d(c).task is None


@helper("na.degerler_stop_says")
def _na_stop_says(c: Ctx) -> None:  # INTENDED (M-28, Q-08)
    assert said(c.win, P_NOTHING_RUNNING), f"nothing said: {heard(c.win)!r}"


_M41 = "M-41 Q-08: {why}: the key is disabled and silent; INTENDED status line {text!r}"


def _plan(pre, effect, feedback, **kw):
    return Plan(pre=pre, snap="snap.degerler", effect=effect, feedback=feedback,
                window="job_degerler", **kw)


for _id in ("degerler.onayla",):
    PLANS[_id] = _plan("pre.degerler_flagged", "effect.degerler_accepted",
                       "feedback.degerler_accepted", na_pre="pre.none",
                       na="na.says_no_job")
PLANS["degerler.okunanla_onayla"] = _plan(
    "pre.degerler_flagged", "effect.degerler_read_accepted",
    "feedback.degerler_read_accepted", na_pre="pre.none", na="na.says_no_job")
PLANS["degerler.secilenleri_onayla"] = _plan(
    "pre.degerler_two_rows", "effect.degerler_rows_accepted", "feedback.degerler_rows_accepted",
    na_pre="pre.none", na="na.says_no_job")
PLANS["degerler.elle_yaz"] = _plan(
    "pre.degerler_value", "effect.degerler_editor_open", "feedback.degerler_editor_open",
    na_pre="pre.none", na="na.says_no_job")
PLANS["degerler.okunana_don"] = _plan(
    "pre.degerler_corrected", "effect.degerler_reverted", "feedback.degerler_reverted",
    na_pre="pre.none", na_window="job_degerler", broken="broken.degerler_uncorrected",
    na="na.degerler_revert_says")
PLANS["degerler.varyant"] = _plan(
    "pre.degerler_variant", "effect.degerler_variant", "feedback.degerler_variant",
    na_pre="pre.none", na="na.says_no_job")
PLANS["degerler.vazgec"] = _plan(
    "pre.degerler_three_rows", "effect.degerler_one_row", "feedback.degerler_one_row",
    na_pre="pre.none", na_window="job_degerler", broken="broken.degerler_one_row",
    na="na.degerler_quiet")
PLANS["degerler.tumunu_sec"] = _plan(
    "pre.degerler_one_row_selected", "effect.degerler_all_rows", "feedback.degerler_all_rows",
    na_pre="pre.none", na="na.says_no_job")
PLANS["degerler.kontrolde_ac"] = _plan(
    "pre.degerler_row2", "effect.degerler_kontrol_at_doc2", "feedback.degerler_kontrol_at_doc2",
    na_pre="pre.none", na="na.degerler_stays_on_tab")
PLANS["degerler.tum_sayfa"] = _plan(
    "pre.degerler_page_view", "effect.degerler_page_view_open",
    "feedback.degerler_page_view_open", na_pre="pre.none", na="na.says_no_job")
PLANS["degerler.sonraki_kontrol"] = _plan(
    "pre.degerler_before_check", "effect.degerler_at_check", "feedback.degerler_at_check",
    na_pre="pre.none", na_window="job_degerler", broken="broken.degerler_no_check",
    na="na.degerler_no_check_says")
PLANS["degerler.onceki_kontrol"] = _plan(
    "pre.degerler_after_check", "effect.degerler_at_check", "feedback.degerler_at_check",
    na_pre="pre.none", na_window="job_degerler", broken="broken.degerler_no_check",
    na="na.degerler_no_check_says")
PLANS["degerler.durdur"] = _plan(
    "pre.degerler_reading", "effect.degerler_read_stopped", "feedback.degerler_read_stopped",
    na_pre="pre.none", na_window="job_degerler", broken="broken.degerler_nothing_running",
    na="na.degerler_stop_says")
PLANS["degerler.sonraki_deger", "degerler", "Tab"] = _plan(
    "pre.degerler_before_check", "effect.degerler_next_value", "feedback.degerler_value_moved",
    na_pre="pre.none", na_window="job_degerler", broken="broken.degerler_last_value",
    na="na.degerler_focus_left")
PLANS["degerler.sonraki_deger", "degerler", "Shift+Tab"] = _plan(
    "pre.degerler_second_value", "effect.degerler_previous_value",
    "feedback.degerler_value_moved", na_pre="pre.none", na_window="job_degerler",
    broken="broken.degerler_first_value", na="na.degerler_focus_left")


# -- Alt+1 .. Alt+4 (Okuma seç, Q-23) --------------------------------------------------------------
_FOUR = ("48Z13", "48213", "4B213", "48 213")  # the four readings given to row 1's Kontrol value


@helper("pre.degerler_editor_four_readings")
def _pre_editor_four_readings(c: Ctx) -> None:
    """Row 1's Kontrol value has four readings and its editor is open and focused."""
    from evrakci.pipeline.cuts import current_values, record_values
    from evrakci.pipeline.templates.values import SectionReading, VariableValue

    restore_job(c)
    d = _d(c)
    ctl = c.win.controller()
    row = d.model.row_at(1)
    key = d.model.cell_at(d.model.index(1, 3)).key
    readings = tuple(SectionReading(n, text, 0.4 + n / 20) for n, text in enumerate(_FOUR))

    def give_readings(job) -> None:
        values = dict(current_values(job, row.document))
        values[key] = VariableValue("48Z13", 0.41, 0, True, "48213", readings, False)
        record_values(job, row.document, degerler.document_template(job, row.document)[0],
                      values)

    assert ctl.run("Okumalar", give_readings)
    d.refresh()
    settle()

    def close_editor() -> None:
        editor = d.table.open_editor_widget()
        if d.table.is_editing() and editor is not None:
            QTest.keyClick(editor, Qt.Key.Key_Escape)
            settle()

    c.undo.append(close_editor)
    pick(c, 1, 3)
    d.type_current()
    settle()
    editor = d.table.open_editor_widget()
    assert editor is not None and QApplication.focusWidget() is editor


def _reading_effect(number: int):
    def effect(c: Ctx) -> None:
        editor = _d(c).table.open_editor_widget()
        assert editor is not None and editor.text() == _FOUR[number], editor and editor.text()
        # nothing is stored until Enter: the job did not change
        assert c.win.controller().undo_stack.index() == c.snap["index"]
    return effect


@helper("reopen.degerler_editor")
def _reopen_editor(c: Ctx) -> None:
    """The editor closed when the shortcut sheet took focus: open it again."""
    d = _d(c)
    if not d.table.is_editing():
        pick(c, 1, 3)
        d.type_current()
        settle()
    assert QApplication.focusWidget() is d.table.open_editor_widget()


@helper("feedback.degerler_reading_taken")
def _feedback_reading_taken(c: Ctx) -> None:
    editor = _d(c).table.open_editor_widget()
    assert editor.isModified() and editor.cursorPosition() == len(editor.text())
    assert QApplication.focusWidget() is editor


@helper("broken.degerler_no_editor")
def _broken_no_editor(c: Ctx) -> None:
    """The editor is closed and the table has focus."""
    pick(c, 1, 3)
    assert not _d(c).table.is_editing()


@helper("na.degerler_reading_key_idle")
def _na_reading_key_idle(c: Ctx) -> None:
    """Outside the open editor the key does nothing: no editor opens, nothing is stored."""
    d = _d(c)
    assert not d.table.is_editing()
    assert c.win.controller().undo_stack.index() == c.snap["index"]
    assert _cur(c) == c.snap["cur"]


for _n, _key in enumerate(("Alt+1", "Alt+2", "Alt+3", "Alt+4")):
    helper(f"effect.degerler_reading_{_n + 1}")(_reading_effect(_n))
    PLANS["degerler.okuma_sec", "degerler", _key] = _plan(
        "pre.degerler_editor_four_readings", f"effect.degerler_reading_{_n + 1}",
        "feedback.degerler_reading_taken", na_pre="pre.none", na_window="job_degerler",
        broken="broken.degerler_no_editor", na="na.degerler_reading_key_idle",
        reopen="reopen.degerler_editor")
