"""Yükle's rows of the shortcut contract (Phase 3, step 3D): steps and plans, registered into
`contract_helpers.HELPERS` and `contract_helpers.PLANS` (see the docstring there)."""
from __future__ import annotations

from pathlib import Path
from unittest import mock

from contract_helpers import (
    NOJOB,
    PLANS,
    Ctx,
    Plan,
    _make_pdf,
    _says,
    assert_focus_ring,
    heard,
    helper,
    plain,
    said,
    settle,
    wait_until,
)
from PySide6.QtCore import QModelIndex, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QInputDialog, QPushButton

PARTI_ILK = "Parti zaten ilk sırada."  # PROPOSED (Q-08)
PARTI_SON = "Parti zaten son sırada."  # PROPOSED (Q-08)
PARTI_SEC = "Önce bir parti seçin."  # PROPOSED (Q-08)
NOTHING_RUNNING = "Şu an durdurulacak bir iş yok."  # PROPOSED (Q-08)
_says("batch_first", PARTI_ILK)
_says("batch_last", PARTI_SON)
_says("pick_batch", PARTI_SEC)
_says("nothing_running", NOTHING_RUNNING)


def _ids(c: Ctx) -> list[str]:
    return [b.id for b in c.win.controller().job.batches]


def _restore_stack(c: Ctx) -> None:
    stack = c.win.controller().undo_stack
    base = stack.index()
    c.undo.append(lambda: (stack.setIndex(base), settle()))


def _add_second_batch(c: Ctx) -> None:
    """A second batch (two synthetic pages) so a batch can move, and be removed."""
    win = c.win
    pdf = _make_pdf(c, "ikinci.pdf", 2)
    ctl = win.controller()
    prepared = win.store.prepare_batch(ctl.job, pdf)
    _restore_stack(c)
    assert ctl.run("Parti ekle", lambda job: job.attach_batch(prepared.batch, prepared.pages))
    settle()
    assert len(_ids(c)) == 2
    c.data["new"] = _ids(c)[1]  # b2, or b3 when an undone batch left its file behind


def _focus_table(c: Ctx) -> None:
    c.win.yukle.table.setFocus()
    settle()
    assert QApplication.focusWidget() is c.win.yukle.table


def _select(c: Ctx, batch_id: str) -> None:
    c.win.yukle.table.select_batch(batch_id)
    _focus_table(c)


@helper("pre.yukle_move_up")
def _pre_yukle_move_up(c: Ctx) -> None:
    _add_second_batch(c)
    c.data["ids"] = _ids(c)
    _select(c, c.data["new"])


@helper("pre.yukle_move_down")
def _pre_yukle_move_down(c: Ctx) -> None:
    _add_second_batch(c)
    c.data["ids"] = _ids(c)
    _select(c, "b1")


@helper("effect.yukle_moved_up")
def _effect_yukle_moved_up(c: Ctx) -> None:
    assert _ids(c) == [c.data["new"], "b1"], _ids(c)
    assert c.win.yukle.table.selected_batch() == c.data["new"]


@helper("effect.yukle_moved_down")
def _effect_yukle_moved_down(c: Ctx) -> None:
    assert _ids(c) == [c.data["new"], "b1"], _ids(c)
    assert c.win.yukle.table.selected_batch() == "b1"


@helper("feedback.yukle_moved")
def _feedback_yukle_moved(c: Ctx) -> None:
    table = c.win.yukle.table
    row = table.currentIndex().row()
    assert table.selectionModel().isRowSelected(row, QModelIndex()), "the row lost its selection"
    assert table.viewport().rect().intersects(table.visualRect(table.currentIndex())), \
        "the moved row is not scrolled into view"
    assert c.win.controller().undo_stack.undoText() == "Partiyi taşı"
    assert_focus_ring(c.win)


@helper("broken.yukle_first_selected")
def _broken_yukle_first_selected(c: Ctx) -> None:
    c.data["ids"] = _ids(c)
    _select(c, "b1")  # the only batch of the demo job: first and last


@helper("na.yukle_first_says")
def _na_yukle_first_says(c: Ctx) -> None:  # INTENDED (M-25, Q-08)
    assert _ids(c) == c.data["ids"]
    assert said(c.win, PARTI_ILK), f"nothing said: {heard(c.win)!r}"


@helper("na.yukle_last_says")
def _na_yukle_last_says(c: Ctx) -> None:  # INTENDED (M-25, Q-08)
    assert _ids(c) == c.data["ids"]
    assert said(c.win, PARTI_SON), f"nothing said: {heard(c.win)!r}"


@helper("broken.yukle_nothing_selected")
def _broken_yukle_nothing_selected(c: Ctx) -> None:
    c.data["ids"] = _ids(c)
    table = c.win.yukle.table
    table.clearSelection()
    table.setCurrentIndex(QModelIndex())
    _focus_table(c)
    assert table.selected_batch() is None


@helper("na.yukle_pick_says")
def _na_yukle_pick_says(c: Ctx) -> None:  # INTENDED (M-25, Q-08)
    assert _ids(c) == c.data["ids"], "a batch moved or was removed"
    assert said(c.win, PARTI_SEC), f"nothing said: {heard(c.win)!r}"


@helper("pre.yukle_remove")
def _pre_yukle_remove(c: Ctx) -> None:
    _add_second_batch(c)
    _select(c, "b1")
    c.data["name"] = c.win.controller().job.get_batch("b1").file_name


@helper("effect.yukle_removed")
def _effect_yukle_removed(c: Ctx) -> None:
    assert _ids(c) == [c.data["new"]], _ids(c)
    assert c.win.yukle.table.selected_batch() == c.data["new"], "selection did not move"


@helper("feedback.yukle_removed")
def _feedback_yukle_removed(c: Ctx) -> None:
    win = c.win
    assert win.toaster.current_text() == f"{c.data['name']} işten çıkarıldı.", heard(win)
    assert any(b.text() == "Geri al" for b in win.toaster._current.findChildren(QPushButton))
    assert win.controller().undo_stack.undoText() == "Partiyi çıkar"


@helper("pre.yukle_rename")
def _pre_yukle_rename(c: Ctx) -> None:
    titles: list[str] = []

    def get_text(_parent, title, *_a, **_k):
        titles.append(title)
        return "Yeni iş adı", True

    patcher = mock.patch.object(QInputDialog, "getText", staticmethod(get_text))
    patcher.start()
    c.undo.append(patcher.stop)
    _restore_stack(c)
    c.data["titles"] = titles
    c.data["old"] = c.win.controller().job.name
    c.win.yukle.table.setFocus()
    settle()


@helper("effect.yukle_renamed")
def _effect_yukle_renamed(c: Ctx) -> None:
    assert c.data["titles"] == ["İşi yeniden adlandır"]
    assert c.win.controller().job.name == "Yeni iş adı"
    assert c.win.controller().job.name != c.data["old"]


@helper("feedback.yukle_renamed")
def _feedback_yukle_renamed(c: Ctx) -> None:
    win = c.win
    assert win.job_switch.name.text() == "Yeni iş adı"
    assert "Yeni iş adı" in win.windowTitle()
    assert win.controller().undo_stack.undoText() == "İşi yeniden adlandır"


@helper("pre.yukle_show")
def _pre_yukle_show(c: Ctx) -> None:
    opened: list[QUrl] = []
    patcher = mock.patch.object(QDesktopServices, "openUrl",
                                staticmethod(lambda url: opened.append(url) or True))
    patcher.start()
    c.undo.append(patcher.stop)
    # Windows selects the batch file in Explorer instead of opening the folder: the same
    # outcome (the file's folder is shown), through the one function the code uses there.
    from evrakci.ui import yukle as yukle_module
    selector = mock.patch.object(
        yukle_module, "select_in_explorer",
        lambda target: opened.append(QUrl.fromLocalFile(str(Path(target).parent))))
    selector.start()
    c.undo.append(selector.stop)
    c.data["opened"] = opened
    c.win.yukle.table.select_batch("b1")
    _focus_table(c)


@helper("effect.yukle_shown")
def _effect_yukle_shown(c: Ctx) -> None:
    ctl = c.win.controller()
    expected = c.win.store.batch_file(ctl.job, ctl.job.batches[0]).parent
    assert [u.toLocalFile() for u in c.data["opened"]] == [str(expected)], c.data["opened"]


@helper("feedback.yukle_shown")
def _feedback_yukle_shown(c: Ctx) -> None:
    from pathlib import Path

    assert len(c.data["opened"]) == 1 and Path(c.data["opened"][0].toLocalFile()).is_dir()
    assert not c.win.toaster.current_text(), heard(c.win)  # no 'Dosya bulunamadı'


@helper("pre.yukle_reading")
def _pre_yukle_reading(c: Ctx) -> None:
    """A real read that only ends when it is cancelled (it reports progress in a loop)."""
    import time

    y = c.win.yukle
    ctl = c.win.controller()
    pdf = c.win.store.batch_file(ctl.job, ctl.job.batches[0])
    c.data["ids"] = _ids(c)
    c.data["pages"] = len(ctl.job.ordered_page_ids())

    def make_work(total):
        def work(progress):
            for n in range(100000):
                progress(n % max(total, 1), total)
                time.sleep(0.01)
        return work

    y._begin([pdf], make_work, lambda result: None)

    def finish() -> None:
        if y.task is not None:
            y.task.cancel()
            wait_until(lambda: y.task is None)

    c.undo.append(finish)
    assert wait_until(lambda: c.win.registry.is_enabled("yukle.iptal"))
    settle()


@helper("effect.yukle_cancelled")
def _effect_yukle_cancelled(c: Ctx) -> None:
    y = c.win.yukle
    assert wait_until(lambda: y.task is None), "the read was not cancelled"
    assert _ids(c) == c.data["ids"]
    assert len(c.win.controller().job.ordered_page_ids()) == c.data["pages"]


@helper("feedback.yukle_cancelled")
def _feedback_yukle_cancelled(c: Ctx) -> None:
    y = c.win.yukle
    assert wait_until(lambda: "İptal edildi" in c.win.toaster.current_text()), heard(c.win)
    assert plain(c.win.toaster.current_text()) == "İptal edildi; hiçbir şey değişmedi."
    assert y.stack.currentWidget() is y.splitter, "the batch list did not come back"
    assert not y.progress.isVisible()


@helper("broken.yukle_nothing_running")
def _broken_yukle_nothing_running(c: Ctx) -> None:
    assert c.win.yukle.task is None


@helper("na.yukle_nothing_running_says")
def _na_yukle_nothing_running_says(c: Ctx) -> None:  # INTENDED (M-28, Q-08)
    assert said(c.win, NOTHING_RUNNING), f"nothing said: {heard(c.win)!r}"


PLANS["yukle.yukari"] = Plan(
    pre="pre.yukle_move_up", effect="effect.yukle_moved_up", feedback="feedback.yukle_moved",
    na_pre="pre.none", broken="broken.yukle_first_selected", na="na.yukle_first_says",
    na_window="job",
    xfail={"na": "M-25 Q-08: already first: Alt+Up is disabled and silent; INTENDED status "
                 f"line {PARTI_ILK!r}"})
PLANS["yukle.asagi"] = Plan(
    pre="pre.yukle_move_down", effect="effect.yukle_moved_down", feedback="feedback.yukle_moved",
    na_pre="pre.none", broken="broken.yukle_first_selected", na="na.yukle_last_says",
    na_window="job",
    xfail={"na": "M-25 Q-08: already last: Alt+Down is disabled and silent; INTENDED status "
                 f"line {PARTI_SON!r}"})
PLANS["yukle.cikar"] = Plan(
    pre="pre.yukle_remove", effect="effect.yukle_removed", feedback="feedback.yukle_removed",
    na_pre="pre.none", broken="broken.yukle_nothing_selected", na="na.yukle_pick_says",
    na_window="job",
    xfail={"na": "M-25 Q-08: no batch selected: Del is disabled and silent; INTENDED status "
                 f"line {PARTI_SEC!r}"})
PLANS["yukle.yeniden_adlandir"] = Plan(
    pre="pre.yukle_rename", effect="effect.yukle_renamed", feedback="feedback.yukle_renamed",
    na_pre="pre.none", na="na.says_no_job",
    xfail={"na": "M-26: no job: F2 is disabled and silent; INTENDED status line " + NOJOB
                 + "; conflicts with test_yukle_a.py::"
                   "test_yukle_actions_are_connected_and_follow_the_selection; owner Q-09"})
PLANS["yukle.gezginde_goster"] = Plan(
    pre="pre.yukle_show", effect="effect.yukle_shown", feedback="feedback.yukle_shown",
    na_pre="pre.none", na="na.says_no_job",
    xfail={"na": "M-26: no job: Ctrl+Shift+O is disabled and silent; INTENDED status line "
                 + NOJOB + "; conflicts with test_yukle_a.py::"
                   "test_yukle_actions_are_connected_and_follow_the_selection; owner Q-09"})
PLANS["yukle.iptal"] = Plan(
    pre="pre.yukle_reading", effect="effect.yukle_cancelled", feedback="feedback.yukle_cancelled",
    na_pre="pre.none", broken="broken.yukle_nothing_running", na="na.yukle_nothing_running_says",
    na_window="job",
    xfail={"na": "M-28 Q-08: nothing running: Ctrl+. is disabled and silent; INTENDED status "
                 f"line {NOTHING_RUNNING!r}"})
