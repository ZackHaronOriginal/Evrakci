"""Kontrol's rows of the shortcut contract (Phase 3, step 3D): steps and plans, registered into
`contract_helpers.HELPERS` and `contract_helpers.PLANS`.

The demo job has 15 pages in three documents: rows 0-2 (Belge 1), row 3 is a QR separator,
rows 4-10 (Belge 2, the one that needs a check), row 11 a separator, rows 12-14 (Belge 3).

Besides the three tests per row, `REFUSALS` lists the refusals that already work today (K on
the first page, Del on separators only...): test_kontrol_refusals in test_shortcut_contract.py
runs them, and `NO_JOB_KEYS` the no-job case of every Kontrol key (M-30).
"""
from __future__ import annotations

from contract_helpers import (
    NOJOB,
    PLANS,
    Ctx,
    Plan,
    _says,
    assert_focus_ring,
    heard,
    helper,
    on_modal,
    plain,
    said,
    settle,
    slot_texts,
)
from PySide6.QtCore import QItemSelectionModel, QModelIndex
from PySide6.QtWidgets import QApplication, QLabel, QPushButton

_SAYFA_SEC = "Önce bir sayfa seçin."
_SAYFALARI_SEC = "Önce sayfaları seçin."
_says("pick_page", _SAYFA_SEC)
_says("pick_pages", _SAYFALARI_SEC)
_says("no_checks", "Kontrol bekleyen belge yok.")
_says("all_reviewed", "Bütün belgeler incelendi.")
_says("last_document", "Bu son belge.")
_says("first_document", "Bu ilk belge.")
_says("first_page_cut", "İlk belgenin öncesi yok.")
_says("pick_pages_and_template", "Önce sayfaları ve bir şablonu seçin.")
_says("separators_only", "Ayraç sayfaları zaten dışa aktarılmaz. Kesimi kaldırmak için M.")

_Sel = QItemSelectionModel.SelectionFlag


def _k(c: Ctx):
    return c.win.kontrol


def _restore_stack(c: Ctx) -> None:
    stack = c.win.controller().undo_stack
    base = stack.index()
    c.undo.append(lambda: (stack.setIndex(base), settle()))


def pick(c: Ctx, rows: list[int], current: int | None = None) -> None:
    """Select `rows` (the first one is the anchor), make `current` (default the last) the
    current page, and give the timeline focus. No rows and no current: nothing chosen."""
    k = _k(c)
    sm = k.timeline.selectionModel()
    sm.clearSelection()
    if not rows and current is None:
        sm.setCurrentIndex(QModelIndex(), _Sel.NoUpdate)
    for n, row in enumerate(rows):
        sm.setCurrentIndex(k.model.index(row), _Sel.ClearAndSelect) if n == 0 else \
            sm.select(k.model.index(row), _Sel.Select)
    sm.setCurrentIndex(k.model.index(rows[-1] if current is None else current), _Sel.NoUpdate) \
        if rows or current is not None else None
    k.timeline.setFocus()
    settle()
    assert QApplication.focusWidget() is k.timeline


def selected(c: Ctx) -> list[int]:
    return sorted(i.row() for i in _k(c).timeline.selectionModel().selectedIndexes())


def _pids(c: Ctx, rows: list[int]) -> list[str]:
    return [_k(c).model.page_id(r) for r in rows]


def _docs(c: Ctx) -> int:
    return len(c.win.controller().documents())


def _history(c: Ctx) -> list[str]:
    return [change.text for _i, change in _k(c)._history]


def _status(c: Ctx) -> list[str]:
    return slot_texts(c.win, "kontrol")


def _snap(c: Ctx) -> dict:
    if c.win.controller() is None:  # no job: nothing but the status line to compare
        return {"status": c.win.message.text()}
    job = c.win.controller().job
    k = _k(c)
    return {"docs": _docs(c), "cuts": set(job.manual_cuts), "deleted": set(job.deleted),
            "rotations": dict(job.rotations), "reviewed": set(k.model.reviewed),
            "templates": len(job.templates), "filters": len(job.filters),
            "history": len(k._history), "row": k.current_row(), "selected": selected(c),
            "index": c.win.controller().undo_stack.index(), "status": c.win.message.text()}


helper("snap.kontrol")(_snap)


def _unchanged(c: Ctx) -> None:
    now = _snap(c)
    for name in ("docs", "cuts", "deleted", "rotations", "reviewed", "templates", "filters",
                 "index"):
        assert now[name] == c.snap[name], f"{name} changed"


def _in_view(c: Ctx, row: int) -> bool:
    tl = _k(c).timeline
    return tl.viewport().rect().intersects(tl.visualRect(_k(c).model.index(row)))


def _toast_undo(c: Ctx) -> bool:
    toast = c.win.toaster._current
    return toast is not None and any(b.text() == "Geri al" for b in toast.findChildren(QPushButton))


# -- Ctrl+A, Esc ------------------------------------------------------------------------------
@helper("pre.kontrol_one_page")
def _pre_one_page(c: Ctx) -> None:
    _restore_stack(c)
    pick(c, [1])


@helper("effect.kontrol_all_selected")
def _effect_all_selected(c: Ctx) -> None:
    assert selected(c) == list(range(_k(c).model.rowCount()))


@helper("feedback.kontrol_all_selected")
def _feedback_all_selected(c: Ctx) -> None:
    assert "15 sayfa seçili" in _status(c), _status(c)
    assert_focus_ring(c.win)


@helper("pre.kontrol_three_selected")
def _pre_three_selected(c: Ctx) -> None:
    _restore_stack(c)
    pick(c, [1, 2, 4])


@helper("effect.kontrol_cleared")
def _effect_cleared(c: Ctx) -> None:
    assert selected(c) == []
    assert _k(c).current_row() == c.snap["row"], "the current page moved"


@helper("feedback.kontrol_cleared")
def _feedback_cleared(c: Ctx) -> None:
    assert not any(t.endswith("sayfa seçili") for t in _status(c)), _status(c)
    assert QApplication.focusWidget() is _k(c).timeline


@helper("broken.kontrol_nothing_selected")
def _broken_nothing_selected(c: Ctx) -> None:
    pick(c, [], None)


@helper("broken.kontrol_selection_none_current_set")
def _broken_none_selected_current_set(c: Ctx) -> None:
    pick(c, [3])  # a page chosen
    _k(c).timeline.selectionModel().clearSelection()


@helper("na.kontrol_esc_quiet")
def _na_esc_quiet(c: Ctx) -> None:
    """Esc with nothing to dismiss stays quiet (owner may accept this, M-45): nothing changes
    and nothing is said."""
    _unchanged(c)
    assert selected(c) == []
    assert c.win.message.text() == c.snap["status"] and not c.win.toaster.current_text()


# -- K, M ------------------------------------------------------------------------------------
@helper("pre.kontrol_cut_here")
def _pre_cut_here(c: Ctx) -> None:
    _restore_stack(c)
    pick(c, [5])
    assert _k(c).model.page_id(5) not in c.win.controller().job.manual_cuts


@helper("effect.kontrol_cut_added")
def _effect_cut_added(c: Ctx) -> None:
    pid = _pids(c, [5])[0]
    assert pid in c.win.controller().job.manual_cuts
    assert _docs(c) == c.snap["docs"] + 1


@helper("feedback.kontrol_cut_added")
def _feedback_cut_added(c: Ctx) -> None:
    assert _history(c)[0] == "Kesim eklendi, sayfa 6", _history(c)
    assert any(t.startswith("Belge ") and t.endswith("/ 4") for t in _status(c)), _status(c)
    assert c.win.controller().undo_stack.undoText() == "Kesim ekle"
    assert _in_view(c, 5)


@helper("pre.kontrol_merge")
def _pre_merge(c: Ctx) -> None:
    _restore_stack(c)
    pick(c, [4])


@helper("effect.kontrol_merged")
def _effect_merged(c: Ctx) -> None:
    assert _docs(c) == c.snap["docs"] - 1


@helper("feedback.kontrol_merged")
def _feedback_merged(c: Ctx) -> None:
    assert c.win.toaster.current_text() == "Belge 2, Belge 1 ile birleştirildi.", heard(c.win)
    assert _toast_undo(c)
    assert _history(c)[0] == "Belge 2, Belge 1 ile birleşti"
    assert any(t.endswith("/ 2") for t in _status(c)), _status(c)


@helper("broken.kontrol_no_current_page")
def _broken_no_current_page(c: Ctx) -> None:
    pick(c, [], None)
    assert not _k(c).timeline.currentIndex().isValid()


@helper("na.kontrol_pick_page_says")
def _na_pick_page_says(c: Ctx) -> None:  # INTENDED (M-32)
    _unchanged(c)
    assert said(c.win, _SAYFA_SEC), f"nothing said: {heard(c.win)!r}"


@helper("na.kontrol_pick_pages_says")
def _na_pick_pages_says(c: Ctx) -> None:  # INTENDED (M-31)
    _unchanged(c)
    assert said(c.win, _SAYFALARI_SEC), f"nothing said: {heard(c.win)!r}"


# -- R, Shift+R, Del -------------------------------------------------------------------------
@helper("pre.kontrol_two_pages")
def _pre_two_pages(c: Ctx) -> None:
    _restore_stack(c)
    pick(c, [0, 1])


def _rotated(c: Ctx, degrees: int) -> None:
    job = c.win.controller().job
    for pid in _pids(c, [0, 1]):
        assert job.rotations.get(pid) == degrees % 360, (pid, job.rotations)
    assert c.win.controller().undo_stack.index() == c.snap["index"] + 1, "not one undo step"


@helper("effect.kontrol_rotated_right")
def _effect_rotated_right(c: Ctx) -> None:
    _rotated(c, 90)


@helper("effect.kontrol_rotated_left")
def _effect_rotated_left(c: Ctx) -> None:
    _rotated(c, -90)


@helper("feedback.kontrol_rotated_right")
def _feedback_rotated_right(c: Ctx) -> None:
    assert _history(c)[0] == "2 sayfa sağa döndürüldü", _history(c)
    assert c.win.controller().undo_stack.undoText() == "Döndür"


@helper("feedback.kontrol_rotated_left")
def _feedback_rotated_left(c: Ctx) -> None:
    assert _history(c)[0] == "2 sayfa sola döndürüldü", _history(c)
    assert c.win.controller().undo_stack.undoText() == "Döndür"


@helper("effect.kontrol_deleted")
def _effect_deleted(c: Ctx) -> None:
    assert _pids(c, [1])[0] in c.win.controller().job.deleted


@helper("feedback.kontrol_deleted")
def _feedback_deleted(c: Ctx) -> None:
    assert c.win.toaster.current_text() == "Sayfa 2 silinecek.", heard(c.win)
    assert _toast_undo(c)
    assert _history(c)[0] == "Sayfa 2 silinecek"
    assert c.win.registry.action("kontrol.sil").text().replace("&", "") == "Sayfayı geri getir"
    assert c.win.controller().undo_stack.undoText() == "Sayfayı sil"


# -- Enter ------------------------------------------------------------------------------------
@helper("pre.kontrol_first_document")
def _pre_first_document(c: Ctx) -> None:
    _restore_stack(c)
    pick(c, [0])


@helper("effect.kontrol_approved")
def _effect_approved(c: Ctx) -> None:
    assert _k(c).model.reviewed == {1}
    assert _k(c).current_document() == 2


@helper("feedback.kontrol_approved")
def _feedback_approved(c: Ctx) -> None:
    assert _history(c)[0] == "Belge 1 onaylandı", _history(c)
    assert "1 / 3 incelendi" in _status(c), _status(c)
    assert _k(c).current_row() == _k(c).model.first_row(2) and _in_view(c, _k(c).current_row())
    assert c.win.controller().undo_stack.undoText() == "Belgeyi onayla"


# -- F, T -------------------------------------------------------------------------------------
@helper("pre.kontrol_filter")
def _pre_filter(c: Ctx) -> None:
    _restore_stack(c)
    pick(c, [4, 5, 6, 7, 8, 9, 10])

    def answer(dialog) -> None:
        dialog.every_n.setValue(3)
        dialog.accept()

    on_modal(c, answer)


@helper("effect.kontrol_filtered")
def _effect_filtered(c: Ctx) -> None:
    assert c.data.get("modals"), "the dialog did not open"
    job = c.win.controller().job
    assert len(job.filters) == c.snap["filters"] + 1 and job.filters[-1].every_n == 3
    assert _docs(c) != c.snap["docs"]


@helper("feedback.kontrol_filtered")
def _feedback_filtered(c: Ctx) -> None:
    assert c.data["modals"][0].windowTitle() == "Filtre uygula"
    assert _history(c)[0] == "Filtre her 3 sayfa, sayfa 5–11", _history(c)
    assert c.win.controller().undo_stack.undoText() == "Filtre: her 3 sayfa"
    assert QApplication.focusWidget() is _k(c).timeline


@helper("pre.kontrol_template")
def _pre_template(c: Ctx) -> None:
    _restore_stack(c)
    pick(c, [0, 1, 2])
    c.data["template"] = next(i for i, t in _k(c).templates().items()
                              if t.name == "Kapasite Raporu")


@helper("effect.kontrol_templated")
def _effect_templated(c: Ctx) -> None:
    job = c.win.controller().job
    assert len(job.templates) == c.snap["templates"] + 1
    last = job.templates[-1]
    assert last.template_id == c.data["template"]
    assert set(last.page_ids) == set(_pids(c, [0, 1, 2]))


@helper("feedback.kontrol_templated")
def _feedback_templated(c: Ctx) -> None:
    assert _history(c)[0] == "Kapasite Raporu uygulandı, 3 sayfa", _history(c)
    assert c.win.controller().undo_stack.undoText() == "Şablon uygula"


# -- Shift+F, Shift+T -------------------------------------------------------------------------
@helper("pre.kontrol_filter_applied")
def _pre_filter_applied(c: Ctx) -> None:
    _restore_stack(c)
    assert c.win.controller().apply_filter(_pids(c, [4, 5, 6, 7, 8, 9, 10]), 3)
    settle()
    pick(c, [4, 5, 6, 7, 8, 9, 10])


@helper("effect.kontrol_filter_removed")
def _effect_filter_removed(c: Ctx) -> None:
    job = c.win.controller().job
    assert len(job.filters) == c.snap["filters"] - 1
    assert _docs(c) == c.snap["docs"] - 2  # the 7 pages (3 + 3 + 1) are one document again


@helper("feedback.kontrol_filter_removed")
def _feedback_filter_removed(c: Ctx) -> None:
    assert c.win.toaster.current_text() == "Filtre kaldırıldı, 7 sayfa."
    assert _toast_undo(c)
    assert _history(c)[0] == "Filtre kaldırıldı, 7 sayfa.", _history(c)
    assert c.win.controller().undo_stack.undoText() == "Filtreyi kaldır"
    assert _k(c).side.filter_button.value.text() == "Filtre yok"


@helper("pre.kontrol_template_applied")
def _pre_template_applied(c: Ctx) -> None:
    _restore_stack(c)
    template = next(i for i, t in _k(c).templates().items() if t.name == "Kapasite Raporu")
    assert c.win.controller().apply_template(_pids(c, [0, 1, 2]), template)
    settle()
    pick(c, [0, 1, 2])


@helper("effect.kontrol_template_removed")
def _effect_template_removed(c: Ctx) -> None:
    job = c.win.controller().job
    assert len(job.templates) == c.snap["templates"] + 1
    last = job.templates[-1]
    assert last.template_id == "" and set(last.page_ids) == set(_pids(c, [0, 1, 2]))


@helper("feedback.kontrol_template_removed")
def _feedback_template_removed(c: Ctx) -> None:
    assert c.win.toaster.current_text() == "Şablon kaldırıldı, 3 sayfa."
    assert _toast_undo(c)
    assert _history(c)[0] == "Şablon kaldırıldı, 3 sayfa.", _history(c)
    assert c.win.controller().undo_stack.undoText() == "Şablonu kaldır"


# -- S, B, Ctrl+Space, Alt+Left / Alt+Right ----------------------------------------------------
@helper("pre.kontrol_select_dialog")
def _pre_select_dialog(c: Ctx) -> None:
    pick(c, [5])  # Belge 2 (rows 4-10) is the current document

    def answer(dialog) -> None:
        c.data["counts"] = {k: label.text() for k, label in dialog._counts.items()}
        dialog._radios["tek"].setChecked(True)
        dialog.accept()

    on_modal(c, answer)


@helper("effect.kontrol_odd_selected")
def _effect_odd_selected(c: Ctx) -> None:
    assert c.data.get("modals"), "the dialog did not open"
    assert selected(c) == [0, 2, 4, 6, 8, 10, 12, 14], selected(c)  # 1st, 3rd ... of each document
    assert c.win.controller().undo_stack.index() == c.snap["index"]  # no undo step
    assert c.win.controller().job.deleted == c.snap["deleted"]


@helper("feedback.kontrol_odd_selected")
def _feedback_odd_selected(c: Ctx) -> None:
    assert c.data["modals"][0].windowTitle() == "Sayfaları seç"
    assert c.data["counts"] == {"belge": "7", "tek": "8", "cift": "5", "bos": "1",
                                "guven": "1", "farkli": "Hiç yok"}, \
            c.data["counts"]
    assert c.win.toaster.current_text() == "8 sayfa seçildi.", heard(c.win)
    assert "8 sayfa seçili" in _status(c), _status(c)
    assert QApplication.focusWidget() is _k(c).timeline


@helper("pre.kontrol_chips")
def _pre_chips(c: Ctx) -> None:
    """The template of the current page gets a saved filter (taken away again afterwards), so
    the chip row is on show; the timeline has focus."""
    pick(c, [5])
    k = _k(c)
    template_id = k._template_for_selection()
    assert template_id is not None
    assert c.win.edit_template(template_id, "Kayıtlı filtre ekle",
                               lambda t: t.add_saved_filter("Tekler", "tek"))

    def put_back() -> None:
        c.win.edit_template(template_id, "Kayıtlı filtre silindi",
                            lambda t: t.remove_saved_filter("Tekler"))
        c.win.sablon.undo_stack.clear()
        k._chips_invalidate()
        k._chips_sync()

    c.undo.append(put_back)
    k._chips_sync()
    assert not k.chips.isHidden()
    pick(c, [5])


@helper("effect.kontrol_chip_focused")
def _effect_chip_focused(c: Ctx) -> None:
    from evrakci.ui.kontrol_chips import FilterChip

    focus = QApplication.focusWidget()
    assert isinstance(focus, FilterChip) and focus.info.name == "Tekler", focus
    assert selected(c) == c.snap["selected"], selected(c)  # nothing selected or turned on
    assert not focus.isChecked()


@helper("feedback.kontrol_chip_focused")
def _feedback_chip_focused(c: Ctx) -> None:
    assert_focus_ring(c.win)
    assert QApplication.focusWidget().accessibleName() == "Tekler"
    assert c.win.controller().undo_stack.index() == c.snap["index"]  # focus move only


@helper("pre.kontrol_doc_page5")
def _pre_doc_page5(c: Ctx) -> None:
    pick(c, [5])


@helper("effect.kontrol_document_selected")
def _effect_document_selected(c: Ctx) -> None:
    assert selected(c) == list(range(4, 11)), selected(c)  # Belge 2, not the QR pages
    assert c.win.controller().undo_stack.index() == c.snap["index"]


@helper("feedback.kontrol_document_selected")
def _feedback_document_selected(c: Ctx) -> None:
    assert c.win.toaster.current_text() == "7 sayfa seçildi.", heard(c.win)
    assert "7 sayfa seçili" in _status(c), _status(c)
    assert QApplication.focusWidget() is _k(c).timeline


@helper("pre.kontrol_two_selected_current_page8")
def _pre_two_selected_current_page8(c: Ctx) -> None:
    pick(c, [0, 1], current=8)


@helper("effect.kontrol_page_toggled_in")
def _effect_page_toggled_in(c: Ctx) -> None:
    assert selected(c) == [0, 1, 8], selected(c)  # the others stay
    assert _k(c).current_row() == 8


@helper("feedback.kontrol_page_toggled_in")
def _feedback_page_toggled_in(c: Ctx) -> None:
    assert "3 sayfa seçili" in _status(c), _status(c)
    assert_focus_ring(c.win)


@helper("pre.kontrol_rows_4_to_6_current6")
def _pre_rows_4_to_6_current6(c: Ctx) -> None:
    pick(c, [4, 5, 6], current=6)


def _focus_moved(row: int):
    def step(c: Ctx) -> None:
        assert _k(c).current_row() == row, _k(c).current_row()
        assert selected(c) == [4, 5, 6], selected(c)  # the selection did not change

    return step


helper("effect.kontrol_focus_right")(_focus_moved(7))
helper("effect.kontrol_focus_left")(_focus_moved(5))


@helper("feedback.kontrol_focus_moved")
def _feedback_focus_moved(c: Ctx) -> None:
    assert _page_status(c) in _status(c), (_page_status(c), _status(c))
    assert _in_view(c, _k(c).current_row())
    assert_focus_ring(c.win)


@helper("broken.kontrol_selected_at_page14")
def _broken_selected_at_page14(c: Ctx) -> None:
    pick(c, [13, 14])


@helper("broken.kontrol_selected_at_page0")
def _broken_selected_at_page0(c: Ctx) -> None:
    pick(c, [0, 1], current=0)


@helper("na.kontrol_focus_and_selection_stay")
def _na_focus_and_selection_stay(c: Ctx) -> None:
    assert _k(c).current_row() == c.snap["row"] and selected(c) == c.snap["selected"]
    assert_focus_ring(c.win)


# -- Space ------------------------------------------------------------------------------------
@helper("pre.kontrol_loupe")
def _pre_loupe(c: Ctx) -> None:
    pick(c, [5])
    c.undo.append(_k(c).close_loupe)


@helper("effect.kontrol_loupe_open")
def _effect_loupe_open(c: Ctx) -> None:
    loupe = _k(c)._loupe
    assert loupe is not None and loupe.is_open()
    assert loupe.index() == 5


@helper("feedback.kontrol_loupe_open")
def _feedback_loupe_open(c: Ctx) -> None:
    k = _k(c)
    title = "Belge 2, Kapasite Raporu, 2. sayfa"
    assert any(plain(lb.text()) == title for lb in k._loupe.findChildren(QLabel)
               if lb.isVisibleTo(c.win)), title
    k.close_loupe()
    settle()
    assert QApplication.focusWidget() is k.timeline, "closing did not return focus"


# -- D ----------------------------------------------------------------------------------------
@helper("effect.kontrol_values_at_doc3")
def _effect_values_at_doc3(c: Ctx) -> None:
    assert c.win.current_tab() == "degerler"
    assert c.win.degerler.current_value()[0] == 3


@helper("feedback.kontrol_values_at_doc3")
def _feedback_values_at_doc3(c: Ctx) -> None:
    assert said(c.win, "Belge 3 seçildi."), f"nothing said: {heard(c.win)!r}"
    assert QApplication.focusWidget() is c.win.degerler.table, "focus is not in the table"


@helper("na.kontrol_stays_on_tab")
def _na_stays_on_tab(c: Ctx) -> None:
    assert c.win.current_tab() == "kontrol"
    assert not said(c.win, "Belge 3 seçildi.")


# -- N, Shift+N, U, Ctrl+Right, Ctrl+Left ------------------------------------------------------
def _at_document(c: Ctx, number: int) -> None:
    k = _k(c)
    assert k.current_document() == number, k.current_document()
    row = k.current_row()
    assert row == k.model.first_row(number), (row, number)
    assert _in_view(c, row)
    assert f"Belge {number} / 3" in _status(c), _status(c)
    assert_focus_ring(c.win)


@helper("pre.kontrol_doc1")
def _pre_doc1(c: Ctx) -> None:
    pick(c, [0])


@helper("pre.kontrol_doc3")
def _pre_doc3(c: Ctx) -> None:
    pick(c, [12])


@helper("effect.kontrol_at_doc2")
def _effect_at_doc2(c: Ctx) -> None:
    assert _k(c).current_document() == 2


@helper("feedback.kontrol_at_doc2")
def _feedback_at_doc2(c: Ctx) -> None:
    _at_document(c, 2)


@helper("broken.kontrol_no_checks")
def _broken_no_checks(c: Ctx) -> None:
    k = _k(c)
    pick(c, [0])
    k.model.set_checks({})
    k.strip.check_rows = []
    c.undo.append(k._job_changed)


@helper("broken.kontrol_all_reviewed")
def _broken_all_reviewed(c: Ctx) -> None:
    _restore_stack(c)
    k = _k(c)
    pick(c, [0])
    assert k.reviews.set_reviewed(c.win.controller().documents())
    settle()
    assert k.model.reviewed == {1, 2, 3}


@helper("broken.kontrol_last_document")
def _broken_last_document(c: Ctx) -> None:
    pick(c, [13])


@helper("broken.kontrol_first_document")
def _broken_first_document(c: Ctx) -> None:
    pick(c, [1])


@helper("na.kontrol_stays")
def _na_stays(c: Ctx) -> None:
    assert _k(c).current_row() == c.snap["row"]
    _unchanged(c)


def _na_says(text: str):
    def step(c: Ctx) -> None:
        _na_stays(c)
        assert said(c.win, text), f"expected {text!r}, saw {heard(c.win)!r}"

    return step


for _name, _text in (("no_checks", "Kontrol bekleyen belge yok."),
                     ("all_reviewed", "Bütün belgeler incelendi."),
                     ("last_document", "Bu son belge."), ("first_document", "Bu ilk belge."),
                     ("first_page_cut", "İlk belgenin öncesi yok."),
                     ("pick_pages", _SAYFALARI_SEC)):
    helper(f"na.kontrol_stays_and_says_{_name}")(_na_says(_text))


@helper("effect.kontrol_at_doc1_row0")
def _effect_at_doc1_row0(c: Ctx) -> None:
    assert _k(c).current_document() == 1


@helper("feedback.kontrol_at_doc1")
def _feedback_at_doc1(c: Ctx) -> None:
    _at_document(c, 1)


# -- local keys of the timeline ---------------------------------------------------------------
def _page_status(c: Ctx) -> str:
    return f"Sayfa {_k(c).current_row() + 1} / 15"


@helper("pre.kontrol_page5")
def _pre_page5(c: Ctx) -> None:
    pick(c, [5])


def _moved_to(row: int):
    def step(c: Ctx) -> None:
        assert _k(c).current_row() == row
        assert selected(c) == [row], selected(c)

    return step


helper("effect.kontrol_page6")(_moved_to(6))
helper("effect.kontrol_page4")(_moved_to(4))
helper("effect.kontrol_first_page")(_moved_to(0))
helper("effect.kontrol_last_page")(_moved_to(14))


@helper("feedback.kontrol_page_shown")
def _feedback_page_shown(c: Ctx) -> None:
    assert _page_status(c) in _status(c), (_page_status(c), _status(c))
    assert _in_view(c, _k(c).current_row())
    assert_focus_ring(c.win)


@helper("broken.kontrol_page0")
def _broken_page0(c: Ctx) -> None:
    pick(c, [0])


@helper("broken.kontrol_page14")
def _broken_page14(c: Ctx) -> None:
    pick(c, [14])


@helper("na.kontrol_page_stays")
def _na_page_stays(c: Ctx) -> None:
    row = c.snap["row"]
    assert _k(c).current_row() == row and selected(c) == [row]
    assert_focus_ring(c.win)


@helper("pre.kontrol_page7")
def _pre_page7(c: Ctx) -> None:
    pick(c, [7])


@helper("effect.kontrol_screen_down")
def _effect_screen_down(c: Ctx) -> None:
    assert _k(c).current_row() > c.snap["row"], "the current page did not move down"


@helper("effect.kontrol_screen_up")
def _effect_screen_up(c: Ctx) -> None:
    assert _k(c).current_row() < c.snap["row"], "the current page did not move up"


@helper("feedback.kontrol_screen_moved")
def _feedback_screen_moved(c: Ctx) -> None:
    assert _in_view(c, _k(c).current_row())
    assert _page_status(c) in _status(c), (_page_status(c), _status(c))


@helper("effect.kontrol_extended_right")
def _effect_extended_right(c: Ctx) -> None:
    assert selected(c) == [5, 6], selected(c)


@helper("effect.kontrol_extended_left")
def _effect_extended_left(c: Ctx) -> None:
    assert selected(c) == [4, 5], selected(c)


@helper("feedback.kontrol_extended")
def _feedback_extended(c: Ctx) -> None:
    assert "2 sayfa seçili" in _status(c), _status(c)
    assert_focus_ring(c.win)


@helper("na.kontrol_selection_stays")
def _na_selection_stays(c: Ctx) -> None:
    assert selected(c) == c.snap["selected"], selected(c)
    assert_focus_ring(c.win)


_M30 = "M-30: no job: every Kontrol key is disabled and silent; INTENDED status line " + NOJOB


def _plan(pre, effect, feedback, **kw):
    return Plan(pre=pre, snap="snap.kontrol", effect=effect, feedback=feedback, **kw)


PLANS["kontrol.tumunu_sec"] = _plan(
    "pre.kontrol_one_page", "effect.kontrol_all_selected", "feedback.kontrol_all_selected",
    na_pre="pre.none", na="na.says_no_job")
PLANS["kontrol.secimi_kaldir"] = _plan(
    "pre.kontrol_three_selected", "effect.kontrol_cleared", "feedback.kontrol_cleared",
    na_pre="pre.none", na_window="job", broken="broken.kontrol_selection_none_current_set",
    na="na.kontrol_esc_quiet")
PLANS["kontrol.kes"] = _plan(
    "pre.kontrol_cut_here", "effect.kontrol_cut_added", "feedback.kontrol_cut_added",
    na_pre="pre.none", na_window="job", broken="broken.kontrol_no_current_page",
    na="na.kontrol_pick_page_says")
PLANS["kontrol.birlestir"] = _plan(
    "pre.kontrol_merge", "effect.kontrol_merged", "feedback.kontrol_merged",
    na_pre="pre.none", na_window="job", broken="broken.kontrol_no_current_page",
    na="na.kontrol_pick_page_says")
PLANS["kontrol.saga_dondur"] = _plan(
    "pre.kontrol_two_pages", "effect.kontrol_rotated_right", "feedback.kontrol_rotated_right",
    na_pre="pre.none", na_window="job", broken="broken.kontrol_nothing_selected",
    na="na.kontrol_pick_pages_says")
PLANS["kontrol.sola_dondur"] = _plan(
    "pre.kontrol_two_pages", "effect.kontrol_rotated_left", "feedback.kontrol_rotated_left",
    na_pre="pre.none", na_window="job", broken="broken.kontrol_nothing_selected",
    na="na.kontrol_pick_pages_says")
PLANS["kontrol.sil"] = _plan(
    "pre.kontrol_one_page", "effect.kontrol_deleted", "feedback.kontrol_deleted",
    na_pre="pre.none", na_window="job", broken="broken.kontrol_nothing_selected",
    na="na.kontrol_pick_pages_says")
PLANS["kontrol.onayla"] = _plan(
    "pre.kontrol_first_document", "effect.kontrol_approved", "feedback.kontrol_approved",
    na_pre="pre.none", na_window="job", broken="broken.kontrol_no_current_page",
    na="na.kontrol_pick_page_says")
PLANS["kontrol.filtre"] = _plan(
    "pre.kontrol_filter", "effect.kontrol_filtered", "feedback.kontrol_filtered",
    na_pre="pre.none", na_window="job", broken="broken.kontrol_nothing_selected",
    na="na.kontrol_stays_and_says_pick_pages")
PLANS["kontrol.sablon"] = _plan(
    "pre.kontrol_template", "effect.kontrol_templated", "feedback.kontrol_templated",
    na_pre="pre.none", na_window="job", broken="broken.kontrol_nothing_selected",
    na="na.says.pick_pages_and_template")
PLANS["kontrol.filtre_kaldir"] = _plan(
    "pre.kontrol_filter_applied", "effect.kontrol_filter_removed",
    "feedback.kontrol_filter_removed", na_pre="pre.none", na_window="job",
    broken="broken.kontrol_nothing_selected", na="na.kontrol_pick_pages_says")
PLANS["kontrol.sablon_kaldir"] = _plan(
    "pre.kontrol_template_applied", "effect.kontrol_template_removed",
    "feedback.kontrol_template_removed", na_pre="pre.none", na_window="job",
    broken="broken.kontrol_nothing_selected", na="na.kontrol_pick_pages_says")
PLANS["kontrol.sec"] = _plan(
    "pre.kontrol_select_dialog", "effect.kontrol_odd_selected", "feedback.kontrol_odd_selected",
    na_pre="pre.none", na="na.says_no_job")
PLANS["kontrol.kayitli_filtreler"] = _plan(
    "pre.kontrol_chips", "effect.kontrol_chip_focused", "feedback.kontrol_chip_focused",
    na_pre="pre.none", na="na.says_no_job")
PLANS["kontrol.belgeyi_sec"] = _plan(
    "pre.kontrol_doc_page5", "effect.kontrol_document_selected",
    "feedback.kontrol_document_selected", na_pre="pre.none", na_window="job",
    broken="broken.kontrol_no_current_page", na="na.kontrol_pick_page_says")
PLANS["kontrol.sayfa_sec", "kontrol", "Ctrl+Space"] = _plan(
    "pre.kontrol_two_selected_current_page8", "effect.kontrol_page_toggled_in",
    "feedback.kontrol_page_toggled_in", na_pre="pre.none", na_window="job",
    broken="broken.kontrol_no_current_page", na="na.kontrol_pick_page_says")
PLANS["kontrol.git_secimsiz", "kontrol", "Alt+Right"] = _plan(
    "pre.kontrol_rows_4_to_6_current6", "effect.kontrol_focus_right",
    "feedback.kontrol_focus_moved", na_pre="pre.none", na_window="job",
    broken="broken.kontrol_selected_at_page14", na="na.kontrol_focus_and_selection_stay")
PLANS["kontrol.git_secimsiz_sol", "kontrol", "Alt+Left"] = _plan(
    "pre.kontrol_rows_4_to_6_current6", "effect.kontrol_focus_left",
    "feedback.kontrol_focus_moved", na_pre="pre.none", na_window="job",
    broken="broken.kontrol_selected_at_page0", na="na.kontrol_focus_and_selection_stay")
PLANS["kontrol.degerlerde_ac"] = _plan(
    "pre.kontrol_doc3", "effect.kontrol_values_at_doc3", "feedback.kontrol_values_at_doc3",
    na_pre="pre.none", na="na.kontrol_stays_on_tab")
PLANS["kontrol.onizle"] = _plan(
    "pre.kontrol_loupe", "effect.kontrol_loupe_open", "feedback.kontrol_loupe_open",
    na_pre="pre.none", na_window="job", broken="broken.kontrol_no_current_page",
    na="na.kontrol_pick_page_says")
for _id, _eff, _broken, _na in (
        ("kontrol.sonraki_kontrol", "effect.kontrol_at_doc2", "broken.kontrol_no_checks",
         "na.kontrol_stays_and_says_no_checks"),
        ("kontrol.onceki_kontrol", "effect.kontrol_at_doc2", "broken.kontrol_no_checks",
         "na.kontrol_stays_and_says_no_checks"),
        ("kontrol.sonraki_incelenmemis", "effect.kontrol_at_doc2", "broken.kontrol_all_reviewed",
         "na.kontrol_stays_and_says_all_reviewed"),
        ("kontrol.sonraki_belge", "effect.kontrol_at_doc2", "broken.kontrol_last_document",
         "na.kontrol_stays_and_says_last_document")):
    PLANS[_id] = _plan("pre.kontrol_doc1", _eff, "feedback.kontrol_at_doc2",
                       na_pre="pre.none", na_window="job", broken=_broken, na=_na)
PLANS["kontrol.onceki_belge"] = _plan(
    "pre.kontrol_doc3", "effect.kontrol_at_doc2", "feedback.kontrol_at_doc2",
    na_pre="pre.none", na_window="job", broken="broken.kontrol_first_document",
    na="na.kontrol_stays_and_says_first_document")


def _arrow(pre, effect, feedback, broken, na="na.kontrol_page_stays"):
    return _plan(pre, effect, feedback, na_pre="pre.none", na_window="job", broken=broken, na=na)


PLANS["kontrol.sayfa", "kontrol", "Right"] = _arrow(
    "pre.kontrol_page5", "effect.kontrol_page6", "feedback.kontrol_page_shown",
    "broken.kontrol_page14")
PLANS["kontrol.sayfa", "kontrol", "Left"] = _arrow(
    "pre.kontrol_page5", "effect.kontrol_page4", "feedback.kontrol_page_shown",
    "broken.kontrol_page0")
PLANS["kontrol.ilk_son", "kontrol", "Home"] = _arrow(
    "pre.kontrol_page7", "effect.kontrol_first_page", "feedback.kontrol_page_shown",
    "broken.kontrol_page0")
PLANS["kontrol.ilk_son", "kontrol", "End"] = _arrow(
    "pre.kontrol_page7", "effect.kontrol_last_page", "feedback.kontrol_page_shown",
    "broken.kontrol_page14")
PLANS["kontrol.ekran", "kontrol", "PgDown"] = _arrow(
    "pre.kontrol_page5", "effect.kontrol_screen_down", "feedback.kontrol_screen_moved",
    "broken.kontrol_page14")
PLANS["kontrol.ekran", "kontrol", "PgUp"] = _arrow(
    "pre.kontrol_page7", "effect.kontrol_screen_up", "feedback.kontrol_screen_moved",
    "broken.kontrol_page0")
PLANS["kontrol.secimi_genislet", "kontrol", "Shift+Right"] = _arrow(
    "pre.kontrol_page5", "effect.kontrol_extended_right", "feedback.kontrol_extended",
    "broken.kontrol_page14", "na.kontrol_selection_stays")
PLANS["kontrol.secimi_genislet", "kontrol", "Shift+Left"] = _arrow(
    "pre.kontrol_page5", "effect.kontrol_extended_left", "feedback.kontrol_extended",
    "broken.kontrol_page0", "na.kontrol_selection_stays")


# -- refusals that already work today, and the no-job case of every key (M-30) -----------------
@helper("setup.kontrol_first_page")
def _setup_first_page(c: Ctx) -> None:
    pick(c, [0])


@helper("setup.kontrol_first_document_page")
def _setup_first_document_page(c: Ctx) -> None:
    pick(c, [1])


@helper("setup.kontrol_separator_only")
def _setup_separator_only(c: Ctx) -> None:
    pick(c, [3])


@helper("setup.kontrol_last_document_page")
def _setup_last_document_page(c: Ctx) -> None:
    _restore_stack(c)
    pick(c, [13])


@helper("setup.kontrol_only_check_current")
def _setup_only_check_current(c: Ctx) -> None:
    pick(c, [5])  # Belge 2 is the only one that needs a check


@helper("setup.kontrol_filter_cut")
def _setup_filter_cut(c: Ctx) -> None:
    """Belge 2's first page was cut by a filter, not by a QR page."""
    _restore_stack(c)
    ctl = c.win.controller()
    assert ctl.apply_filter(_pids(c, [12, 13, 14]), 1)
    settle()
    pick(c, [13])


# (name, action id, key, setup, text said, what must not change)
REFUSALS = (
    ("cut_first_page", "kontrol.kes", "K", "setup.kontrol_first_page",
     "İlk belgenin öncesi yok."),
    ("merge_first_document", "kontrol.birlestir", "M", "setup.kontrol_first_document_page",
     "İlk belgenin öncesi yok."),
    ("delete_separator_only", "kontrol.sil", "Del", "setup.kontrol_separator_only",
     "Ayraç sayfaları zaten dışa aktarılmaz. Kesimi kaldırmak için M."),
    ("approve_last_document", "kontrol.onayla", "Return", "setup.kontrol_last_document_page",
     "Belge 3 onaylandı; bu son belge."),
    ("next_check_only_one", "kontrol.sonraki_kontrol", "N", "setup.kontrol_only_check_current",
     "Kontrol gereken tek belge bu."),
)
NO_JOB_KEYS = (
    ("kontrol.secimi_kaldir", "Esc"), ("kontrol.kes", "K"), ("kontrol.birlestir", "M"),
    ("kontrol.saga_dondur", "R"), ("kontrol.sola_dondur", "Shift+R"), ("kontrol.sil", "Del"),
    ("kontrol.onayla", "Return"), ("kontrol.onayla", "Enter"), ("kontrol.filtre", "F"),
    ("kontrol.sablon", "T"), ("kontrol.sec", "S"), ("kontrol.belgeyi_sec", "B"),
    ("kontrol.filtre_kaldir", "Shift+F"),
    ("kontrol.sablon_kaldir", "Shift+T"), ("kontrol.onizle", "Space"),
    ("kontrol.sonraki_kontrol", "N"),
    ("kontrol.onceki_kontrol", "Shift+N"), ("kontrol.sonraki_incelenmemis", "U"),
    ("kontrol.sonraki_belge", "Ctrl+Right"), ("kontrol.onceki_belge", "Ctrl+Left"),
)
