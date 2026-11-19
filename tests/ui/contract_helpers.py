"""Helpers of tests/ui/test_shortcut_contract.py: the window, the key, and the small named steps
(precondition, effect, feedback, not-applicable) a contract row is made of.

How a row of docs/ui-goal/shortcut-contract.tsv finds its steps: through the `PLANS` table at the
bottom of this module, keyed by action id (every tab) or by (action id, tab) when one tab differs.
The TSV itself stays as the owner's document; the mapping lives here because the steps are code.
A `Plan` names steps by string; `HELPERS` maps each name to a function taking a `Ctx`. Names are
`pre.*` (set the precondition), `snap.*` (record what to compare with), `effect.*` and
`feedback.*` (assert what the key did and what the user sees), `broken.*` (break the precondition)
and `na.*` (assert the not_applicable column).

Effects are read from the model, controller or widgets, never from UI text; feedback is read from
what the user sees (status line, toast, focus, selection, the item's text).
"""
from __future__ import annotations

import csv
import os
import re
import struct
import time
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QWidget

from evrakci.ui import actions
from evrakci.ui.main_window import TAB_IDS, MainWindow, first_focusable
from evrakci.ui.palette import ID_ROLE

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs" / "ui-goal" / "shortcut-contract.tsv"
NOJOB = "Önce Yükle sekmesinden bir iş açın (Ctrl+1)."

HELPERS: dict[str, Callable[[Ctx], None]] = {}


def helper(name: str):
    def register(fn):
        HELPERS[name] = fn
        return fn

    return register


def settle(rounds: int = 5) -> None:
    for _ in range(rounds):
        QApplication.processEvents()


def wait_until(condition: Callable[[], bool], timeout_ms: int = 8000) -> bool:
    waited = 0
    while not condition() and waited < timeout_ms:
        QTest.qWait(20)
        waited += 20
    return condition()


@dataclass
class Ctx:
    """What a step gets: the window, the tab, the key of the row and what was recorded before."""

    win: MainWindow
    tab: str
    key: str
    action_id: str
    snap: dict[str, Any] = field(default_factory=dict)
    tmp: Path | None = None
    undo: list[Callable[[], None]] = field(default_factory=list)  # run after the test
    data: dict[str, Any] = field(default_factory=dict)  # set by `pre`, kept for the steps

    @property
    def action(self):
        return self.win.registry.action(self.action_id)

    def target(self) -> str:
        """The tab an `app.sekme.<tab>` action leads to."""
        return self.action_id.rsplit(".", 1)[1]


# -- the key and the other routes ------------------------------------------------------------
@contextmanager
def watchdog(ms: int = 4000):
    """A key that opens a modal dialog nobody answers would hang the run: reject it after `ms`."""
    def close_modal() -> None:
        modal = QApplication.activeModalWidget()
        if modal is not None:
            modal.reject() if hasattr(modal, "reject") else modal.close()

    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(close_modal)
    timer.start(ms)
    try:
        yield
    finally:
        timer.stop()


def on_modal(c: Ctx, handler: Callable[[QWidget], None]) -> None:
    """Answer the next modal dialog (a QDialog.exec or a static QMessageBox call) with `handler`;
    the dialogs seen are kept in c.data["modals"]."""
    seen = c.data.setdefault("modals", [])

    def tick() -> None:
        modal = QApplication.activeModalWidget()
        if modal is not None and modal not in seen:
            seen.append(modal)
            handler(modal)

    timer = QTimer()
    timer.timeout.connect(tick)
    timer.start(20)
    c.undo.append(timer.stop)
    c.data["_modal_timer"] = timer


def reactivate(win: QWidget) -> None:
    """A dialog that closed leaves no window active in the offscreen platform: take it back."""
    active = QApplication.activeWindow()
    if active is None or not active.isVisible():
        win.activateWindow()
        QTest.qWaitForWindowActive(win, 1000)
    QTest.qWait(30)  # the focus the closed popup gives back arrives a moment later
    settle()


def press_in(dialog: QWidget, key: str) -> None:
    """A key for a dialog that is open: to its own focus widget."""
    combo = actions.key_sequence(key)[0]
    with watchdog():
        QTest.keyClick(dialog.focusWidget() or dialog, combo.key(), combo.keyboardModifiers())
    settle()


def press(win: QWidget, key: str, rounds: int = 3) -> None:
    """The real key, sent to the widget that has focus (the window if none)."""
    combo = actions.key_sequence(key)[0]
    with watchdog():
        QTest.keyClick(QApplication.focusWidget() or win, combo.key(), combo.keyboardModifiers())
    settle(rounds)
    reactivate(win)


def run_via_palette(win: MainWindow, tab: str, action_id: str) -> None:
    """Ctrl+K's list: find the command, make it current, press Enter in the search field."""
    palette = win.command_palette
    palette.open_for(tab)
    settle()
    for row in range(palette.list.count()):
        if palette.list.item(row).data(ID_ROLE) == action_id:
            palette.list.setCurrentRow(row)
            break
    else:
        raise AssertionError(f"{action_id} is not in the command palette of {tab}")
    with watchdog():
        QTest.keyClick(palette.field, Qt.Key.Key_Return)
    settle()
    palette.close()
    reactivate(win)


def run_via_menu(win: MainWindow, action_id: str) -> None:
    """The menu item: the action a QMenu of the menu bar holds is the one triggered."""
    action = win.registry.action(action_id)
    menus = [a.menu() for a in win.menu_row.bar.actions() if a.menu() is not None]
    for menu in menus:
        menu.aboutToShow.emit()  # the menus fill themselves when they open
    assert any(action in m.actions() for m in menus), f"{action_id} is in no menu"
    assert action.isEnabled(), action_id
    with watchdog():
        action.trigger()
    settle()
    reactivate(win)


def run_via_sheet(win: MainWindow, tab: str, action_id: str, key: str) -> None:
    """A local key (arrows, Tab, Esc in the guide's search...) has no menu item and no palette
    entry; the one other route to it is the shortcut sheet that names it. The sheet must list
    the key under its label for this tab, and the key must still work once the sheet is shut
    (focus came back to where it was)."""
    spec = actions.spec(action_id)
    opener = QApplication.focusWidget()
    win.registry.action("app.kisayollar").trigger()
    settle()
    sheet = win.shortcut_sheet
    assert sheet.isVisible()
    label = actions.plain_text(spec.text).rstrip("…")
    shown = [(cmd, keys) for _g, cmd, keys in sheet.visible_rows() if cmd == label]
    assert shown, f"the sheet of {tab} does not list {label!r}"
    assert any(actions.key_text(key) in keys for _cmd, keys in shown), (shown, key)
    press_in(sheet, "Esc")
    reactivate(win)
    assert not sheet.isVisible()
    if opener is not None:
        assert QApplication.focusWidget() is opener, "focus did not return to where it was"
    press(win, key)


def via(win: MainWindow, tab: str, action_id: str, key: str | None = None) -> None:
    spec = actions.spec(action_id)
    if spec.local:
        assert key is not None, f"{action_id} is a local key: the route needs the key"
        run_via_sheet(win, tab, action_id, key)
    elif spec.palette:
        run_via_palette(win, tab, action_id)
    else:
        run_via_menu(win, action_id)


# -- the window ------------------------------------------------------------------------------
def reset(win: MainWindow, tab: str) -> None:
    """Back to a known state between two tests that share a window."""
    for dialog in (win.shortcut_sheet, win.command_palette, win.settings_dialog,
                   win.about_dialog):
        if dialog is not None and dialog.isVisible():
            dialog.close()
    full = win.registry.action("app.tam_ekran")
    if win.isFullScreen() or full.isChecked():
        win.showNormal()
        win.resize(1366, 768)
        full.blockSignals(True)
        full.setChecked(False)
        full.blockSignals(False)
    win.show_tab(tab)
    settle(2)
    side = win.inspector(tab)
    if side is not None and side.isHidden():
        side.show()
    win._sync_inspector()
    for _ in range(20):
        if not win.toaster.current_text():
            break
        win.toaster.dismiss()
    win.message.setText("")
    win.focus_work_area()
    settle()


def plain(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def slot_texts(win: MainWindow, tab: str) -> list[str]:
    """What the tab's own status-bar area says, rich text stripped."""
    return [plain(lb.text()) for lb in win.status_slot(tab).findChildren(QLabel)
            if lb.isVisibleTo(win)]


def said(win: MainWindow, text: str) -> bool:
    """The text is on screen as status line, the tab's own message, or toast."""
    shown = [win.message.text(), win.sablon.message.text(), win.toaster.current_text()]
    return any(text in s for s in shown)


def heard(win: MainWindow) -> str:
    return " | ".join(s for s in (win.message.text(), win.sablon.message.text(),
                                  win.toaster.current_text()) if s)


def focus_in(win: MainWindow, region: QWidget) -> bool:
    focus = QApplication.focusWidget()
    return focus is not None and (focus is region or region.isAncestorOf(focus))


def assert_focus_ring(win: MainWindow) -> None:
    focus = QApplication.focusWidget()
    assert focus is not None and focus.hasFocus() and focus.isVisible(), "no visible focus"


# -- rows and plans --------------------------------------------------------------------------
@dataclass(frozen=True)
class Plan:
    pre: str = "pre.none"
    snap: str = "snap.basic"
    effect: str = "effect.none"
    feedback: str = "feedback.none"
    na_pre: str = "same"       # step run before `broken` in the not-applicable test
    broken: str = "broken.none"
    na: str = "na.same_as_effect"
    window: str = "job"        # job: the shared demo window; fresh: a new one for this test
    na_window: str = "empty"   # window of the not-applicable test: empty (no job) | job | fresh
    xfail: dict[str, str] = field(default_factory=dict)  # test kind -> "M-xx: reason"
    marks: tuple = ()          # extra pytest marks of every test of the row (needs_tesseract)


def load_rows(prefix: str) -> list[dict[str, str]]:
    with CONTRACT.open(encoding="utf-8", newline="") as fh:
        return [r for r in csv.DictReader(fh, delimiter="\t")
                if r["action_id"].startswith(prefix)]


PLANS: dict[Any, Plan] = {}


def plan_for(action_id: str, tab: str, key: str = "") -> Plan:
    """The plan of a row: by (action, tab, key), else (action, tab), else the action."""
    return (PLANS.get((action_id, tab, key)) or PLANS.get((action_id, tab))
            or PLANS.get(action_id) or Plan())


# ==========================================================================================
# Steps. Names: pre.* snap.* effect.* feedback.* broken.* na.*
# ==========================================================================================
@helper("pre.none")
def _pre_none(c: Ctx) -> None:
    pass


@helper("broken.none")
def _broken_none(c: Ctx) -> None:
    """Rows whose not_applicable column says "always enabled": nothing to break, the key must
    simply keep working (the test runs it on the window with no job)."""


@helper("effect.none")
def _effect_none(c: Ctx) -> None:
    raise AssertionError(f"no effect step for {c.action_id} on {c.tab}")


@helper("feedback.none_needed")
def _feedback_none_needed(c: Ctx) -> None:
    """Rows whose effect step already asserts what the user sees (a status line)."""


@helper("feedback.none")
def _feedback_none(c: Ctx) -> None:
    raise AssertionError(f"no feedback step for {c.action_id} on {c.tab}")


@helper("snap.basic")
def _snap_basic(c: Ctx) -> dict:
    return {"tab": c.win.current_tab(), "status": c.win.message.text()}


@helper("na.same_as_effect")
def _na_same(c: Ctx) -> None:
    plan = plan_for(c.action_id, c.tab, c.key)
    HELPERS[plan.effect](c)
    HELPERS[plan.feedback](c)


# -- tabs, regions ---------------------------------------------------------------------------
@helper("pre.focus_title_tabs")
def _pre_focus_title_tabs(c: Ctx) -> None:
    c.win.title_tabs.setFocus(Qt.FocusReason.TabFocusReason)
    settle()
    assert QApplication.focusWidget() is c.win.title_tabs


@helper("effect.tab_shown")
def _effect_tab_shown(c: Ctx) -> None:
    assert c.win.current_tab() == c.target()
    focus = QApplication.focusWidget()
    assert focus is not None and c.win.tabs.currentWidget().isAncestorOf(focus), \
        "focus did not move to the tab's main view"


@helper("feedback.tab_shown")
def _feedback_tab_shown(c: Ctx) -> None:
    target = c.target()
    win = c.win
    assert win.title_tabs.currentIndex() == TAB_IDS.index(target)
    assert win.command_bars.currentWidget() is win.command_bar(target)
    assert win.command_bar(target).isVisibleTo(win)
    assert win.status_slot(target).isVisibleTo(win)
    assert_focus_ring(win)


def _cycled(c: Ctx, step: int) -> None:
    expected = TAB_IDS[(TAB_IDS.index(c.tab) + step) % len(TAB_IDS)]
    assert c.win.current_tab() == expected
    focus = QApplication.focusWidget()
    assert focus is not None and c.win.tabs.currentWidget().isAncestorOf(focus)


@helper("effect.tab_next")
def _effect_tab_next(c: Ctx) -> None:
    _cycled(c, 1)


@helper("effect.tab_previous")
def _effect_tab_previous(c: Ctx) -> None:
    _cycled(c, -1)


@helper("feedback.tab_cycled")
def _feedback_tab_cycled(c: Ctx) -> None:
    win = c.win
    assert win.title_tabs.currentIndex() == TAB_IDS.index(win.current_tab())
    assert win.command_bars.currentWidget() is win.command_bar(win.current_tab())
    assert_focus_ring(win)


@helper("pre.focus_command_bar")
def _pre_focus_command_bar(c: Ctx) -> None:
    target = first_focusable(c.win.command_bar(c.tab))
    assert target is not None, "the command bar has nothing focusable"
    target.setFocus(Qt.FocusReason.TabFocusReason)
    settle()
    assert focus_in(c.win, c.win.command_bar(c.tab))


@helper("effect.region_next")
def _effect_region_next(c: Ctx) -> None:
    assert focus_in(c.win, c.win.tabs.currentWidget()), "focus did not reach the work area"


@helper("effect.region_previous")
def _effect_region_previous(c: Ctx) -> None:
    assert focus_in(c.win, c.win.title_band), "focus did not reach the title band"


@helper("feedback.region")
def _feedback_region(c: Ctx) -> None:
    assert_focus_ring(c.win)
    focus = QApplication.focusWidget()
    area = c.win.tabs.currentWidget()
    if area.isAncestorOf(focus):  # scrolled into view: the widget lies inside the window
        assert c.win.rect().contains(focus.mapTo(c.win, focus.rect().center()))


# -- the job, saving, closing ----------------------------------------------------------------
PROPOSED_NO_DOCS = "Bu sekmede belge listesi yok. Kontrol sekmesinde Ctrl+G ile belgeye gidin."


@helper("na.says_no_job")
def _na_says_no_job(c: Ctx) -> None:
    assert said(c.win, NOJOB), f"the status line stayed silent: {heard(c.win)!r}"


def _go_to_dialog(c: Ctx, number: int = 2) -> None:
    def answer(dialog: QWidget) -> None:
        dialog.document.setChecked(True)
        dialog.number.setValue(number)
        dialog.accept()

    on_modal(c, answer)


@helper("pre.go_to_first_document")
def _pre_go_to_first_document(c: Ctx) -> None:
    win = c.win
    if c.tab == "kontrol":
        win.kontrol.go_to_document(1)
        win.kontrol.timeline.setFocus()
    elif c.tab == "degerler":
        win.degerler.select_value(1, "")
        win.degerler.table.setFocus()
    settle()
    _go_to_dialog(c)


@helper("effect.go_to_document_2")
def _effect_go_to_document_2(c: Ctx) -> None:
    assert c.data.get("modals"), "the go-to dialog did not open"
    win = c.win
    if c.tab == "kontrol":
        assert win.kontrol.current_document() == 2
    elif c.tab == "degerler":
        assert win.degerler.current_value()[0] == 2
    elif c.tab == "sablonlar":  # INTENDED (M-01): a document number picks that Örnek
        assert win.sablon.example == 2
    elif c.tab == "disa_aktar":  # INTENDED (M-01): the file row of that document
        assert win.disa_aktar.results.currentIndex().row() == 1


@helper("feedback.go_to_document_2")
def _feedback_go_to_document_2(c: Ctx) -> None:
    win = c.win
    focus = QApplication.focusWidget()
    if c.tab == "kontrol":
        assert focus is win.kontrol.timeline, f"focus did not return to the timeline: {focus!r}"
        labels = slot_texts(win, "kontrol")
        assert any(t.startswith("Belge 2 / ") for t in labels), labels
    elif c.tab == "degerler":
        assert focus is win.degerler.table, f"focus is {focus!r}"
        assert win.degerler.table.currentIndex().isValid()
    elif c.tab == "sablonlar":
        assert "2" in win.sablon.examples.currentText()
    elif c.tab == "disa_aktar":
        assert focus is win.disa_aktar.results


@helper("pre.job_tab_no_dialog")
def _pre_job_tab_no_dialog(c: Ctx) -> None:
    on_modal(c, lambda d: d.reject())


@helper("effect.go_to_says_no_documents")
def _effect_go_to_says_no_documents(c: Ctx) -> None:  # INTENDED (M-01, Q-08)
    assert said(c.win, PROPOSED_NO_DOCS), f"nothing said: {heard(c.win)!r}"


@helper("feedback.go_to_says_no_documents")
def _feedback_go_to_says_no_documents(c: Ctx) -> None:
    assert c.win.current_tab() == c.tab
    assert not c.data.get("modals"), "a dialog opened on a tab without a document list"
    assert_focus_ring(c.win)


def _saved_path(c: Ctx) -> Path:
    win = c.win
    if c.tab == "sablonlar":
        return win.template_store._path(win.sablon.template.id)
    return win._job_file(win.controller().job.id)


@helper("pre.saveable")
def _pre_saveable(c: Ctx) -> None:
    win = c.win
    if c.tab == "sablonlar":
        assert win.sablon.template is not None, "no template open on Şablonlar"
    path = _saved_path(c)
    old = time.time() - 86400
    os.utime(path, (old, old))
    c.data["path"], c.data["old"] = path, path.stat().st_mtime_ns
    win.job_switch.save_state.set_saving()


@helper("effect.written_now")
def _effect_written_now(c: Ctx) -> None:
    assert c.data["path"].stat().st_mtime_ns > c.data["old"], "the file was not written"


@helper("feedback.saved_said")
def _feedback_saved_said(c: Ctx) -> None:
    win = c.win
    if c.tab == "sablonlar":
        assert "Şablon kaydedildi." in win.toaster.current_text(), heard(win)
        texts = slot_texts(win, "sablonlar")
        assert any(re.fullmatch(r"Şablon kaydedildi \d\d:\d\d", t) for t in texts), texts
    else:
        assert re.search(r"İş kaydedildi \d\d:\d\d\. Değişiklikler zaten kendiliğinden "
                         r"kaydedilir\.", win.toaster.current_text()), heard(win)
        assert win.job_switch.save_state.state() == "saved"
        assert win.job_switch.save_state.text().startswith("Kaydedildi ")


@helper("effect.export_tab_shown")
def _effect_export_tab_shown(c: Ctx) -> None:
    assert c.win.current_tab() == "disa_aktar"


@helper("feedback.export_tab_shown")
def _feedback_export_tab_shown(c: Ctx) -> None:
    win = c.win
    assert win.disa_aktar.folder.isVisibleTo(win) and win.disa_aktar.results.isVisibleTo(win)
    assert win.title_tabs.currentIndex() == TAB_IDS.index("disa_aktar")


@helper("pre.export_ready")
def _pre_export_ready(c: Ctx) -> None:
    d = c.win.disa_aktar
    d.layer.setChecked(False)  # no text layer: no OCR in the test
    out = (c.tmp or Path(".")) / "disa"
    d.folder.setText(str(out))
    c.data["out"] = out
    d.results.setFocus()
    settle()
    assert d.can_export(), d._state


@helper("effect.export_written")
def _effect_export_written(c: Ctx) -> None:
    d = c.win.disa_aktar
    assert wait_until(lambda: d._written and d.task is None), "the export did not finish"
    out = c.data["out"]
    assert (out / "index.xlsx").is_file()
    assert len(list(out.glob("*.pdf"))) == 3


@helper("feedback.export_done")
def _feedback_export_done(c: Ctx) -> None:
    d = c.win.disa_aktar
    assert d._outcome is not None and d._outcome["kind"] == "done"
    assert d._outcome["title"] == "3 belge yazıldı"
    texts = [lb.text() for lb in d.findChildren(QLabel) if lb.isVisibleTo(c.win)]
    assert any("3 belge yazıldı" in t for t in texts), texts


@helper("broken.export_blocked")
def _broken_export_blocked(c: Ctx) -> None:
    """The target folder is not empty: the pre-flight has an engel and the export is blocked."""
    d = c.win.disa_aktar
    full = (c.tmp or Path(".")) / "dolu"
    full.mkdir(exist_ok=True)
    (full / "eski.pdf").write_bytes(b"%PDF-1.4\n")
    d.layer.setChecked(False)
    d.folder.setText(str(full))
    d.results.setFocus()
    settle()
    assert d._state == "blocked", d._state
    c.data["full"] = full


@helper("na.export_blocked_says_why")
def _na_export_blocked_says_why(c: Ctx) -> None:  # INTENDED (M-13): the existing toast
    assert "Dışa aktarılamıyor:" in c.win.toaster.current_text(), heard(c.win)


@helper("pre.job_open_state")
def _pre_job_open_state(c: Ctx) -> None:
    c.data["job_id"] = c.win.controller().job.id
    c.data["store"] = c.win.store


@helper("effect.job_closed")
def _effect_job_closed(c: Ctx) -> None:
    win = c.win
    assert win.controller() is None
    assert any(j.id == c.data["job_id"] for j in c.data["store"].list_jobs()), \
        "the job is gone from 'Tüm işler'"
    assert not win.registry.is_enabled("app.isi_kapat")
    assert win.yukle.controller is None if hasattr(win.yukle, "controller") else True


@helper("feedback.job_closed")
def _feedback_job_closed(c: Ctx) -> None:
    win = c.win
    assert win.windowTitle().startswith("Evrakçı ") and "kapasite" not in win.windowTitle()
    assert win.job_switch.name.text() == "İş açılmadı"
    assert not win.job_switch.save_state.isVisible()
    win.show_tab("kontrol")
    settle()
    texts = [lb.text() for lb in win.tabs.currentWidget().findChildren(QLabel)
             if lb.isVisibleTo(win)]
    assert "Henüz açık iş yok" in texts, texts


def _says(name: str, text: str) -> None:
    """Register effect.says.<name> and na.says.<name>: `text` is on screen (status line, the
    tab's message or toast)."""
    def step(c: Ctx) -> None:
        assert said(c.win, text), f"expected {text!r}, saw {heard(c.win)!r}"

    HELPERS[f"effect.says.{name}"] = HELPERS[f"na.says.{name}"] = step


_says("rehber_save", "Rehber'de kaydedilecek bir şey yok.")  # PROPOSED (Q-08)
_says("no_template_save", "Kaydedilecek bir şablon yok. Önce bir şablon oluşturun.")
_says("nothing_to_undo", "Geri alınacak bir şey yok.")  # PROPOSED (Q-08)
_says("nothing_to_redo", "Yinelenecek bir şey yok.")  # PROPOSED (Q-08)
_says("no_results", "Bu sekmede aranacak sonuç yok.")  # PROPOSED (Q-08)
_says("no_zoom", "Bu sekmede yakınlaştırılacak bir şey yok.")  # PROPOSED (Q-08)
_says("no_variable", "Aranacak değişken yok.")  # PROPOSED (Q-08)
_says("no_hits", "Sonuç yok")


# -- new job, add files, quit ----------------------------------------------------------------
def _make_pdf(c: Ctx, name: str, pages: int) -> Path:
    from fakes import make_pdf, text_page

    return make_pdf((c.tmp or Path(".")) / name, [text_page(str(n)) for n in range(pages)])


def _patch_pickers(c: Ctx, pdf: Path | None, name: str = "Yeni iş") -> list[str]:
    """The file picker returns `pdf` (cancelled when None) and the name dialog `name`; the
    titles they were opened with are returned in a list."""
    from unittest import mock

    from PySide6.QtWidgets import QFileDialog, QInputDialog

    titles: list[str] = []

    def files(_parent, title, *_a, **_k):
        titles.append(title)
        return ([str(pdf)] if pdf else []), ""

    def text(_parent, title, *_a, **_k):
        titles.append(title)
        return name, True

    for target, attr, fn in ((QFileDialog, "getOpenFileNames", files),
                             (QInputDialog, "getText", text)):
        patcher = mock.patch.object(target, attr, staticmethod(fn))
        patcher.start()
        c.undo.append(patcher.stop)
    return titles


@helper("pre.new_job_pickers")
def _pre_new_job_pickers(c: Ctx) -> None:
    c.data["titles"] = _patch_pickers(c, _make_pdf(c, "yeni.pdf", 2))


@helper("effect.new_job_opened")
def _effect_new_job_opened(c: Ctx) -> None:
    win = c.win
    assert wait_until(lambda: win.controller() is not None
                      and win.controller().job.name == "Yeni iş"), "the new job did not open"
    assert len(win.controller().job.ordered_page_ids()) == 2
    assert win.current_tab() == "yukle"


@helper("feedback.new_job_opened")
def _feedback_new_job_opened(c: Ctx) -> None:
    win = c.win
    assert c.data["titles"][:2] == ["Taranmış PDF'leri seçin", "Yeni iş"]
    assert win.job_switch.name.text() == "Yeni iş"
    assert win.registry.is_enabled("app.isi_kapat")


def _busy(c: Ctx) -> None:
    yukle = c.win.yukle
    yukle.task = object()  # busy() is "a task is set": a read is running
    c.undo.append(lambda: setattr(yukle, "task", None))


@helper("broken.read_running_no_job")
def _broken_read_running_no_job(c: Ctx) -> None:
    c.data["titles"] = _patch_pickers(c, None)
    _busy(c)


@helper("na.says_read_running")
def _na_says_read_running(c: Ctx) -> None:
    assert "Okuma sürüyor; bitince yeni iş oluşturun." in c.win.toaster.current_text(), \
        heard(c.win)
    assert c.data["titles"] == [], "a picker opened while a read is running"


@helper("pre.add_file_picker")
def _pre_add_file_picker(c: Ctx) -> None:
    pdf = _make_pdf(c, "ek.pdf", 2)
    c.data["pdf"] = pdf
    c.data["titles"] = _patch_pickers(c, pdf)
    c.data["batches"] = len(c.win.controller().job.batches)


@helper("effect.batch_added")
def _effect_batch_added(c: Ctx) -> None:
    ctl = c.win.controller()
    assert wait_until(lambda: len(ctl.job.batches) == c.data["batches"] + 1), "no batch added"
    assert c.win.current_tab() == "yukle"


@helper("feedback.batch_added")
def _feedback_batch_added(c: Ctx) -> None:
    win = c.win
    assert c.data["titles"] == ["Parti ekle"]
    assert wait_until(lambda: "ek.pdf eklendi." in win.toaster.current_text()), heard(win)
    toast = win.toaster._current
    assert any(b.text() == "Geri al" for b in toast.findChildren(QPushButton))
    assert win.controller().undo_stack.undoText() == "Parti ekle"


@helper("effect.window_closed")
def _effect_window_closed(c: Ctx) -> None:
    assert not c.win.isVisible()


QUIT_SIZE = (1111, 703)  # a size no earlier window in the module's ini can have saved


@helper("pre.quit_known_geometry")
def _pre_quit_known_geometry(c: Ctx) -> None:
    """Ctrl+Q: forget any geometry an earlier window saved in the shared ini, and give this
    window a known size, so only closing THIS window can put the key back."""
    from PySide6.QtCore import QSettings

    c.win.prefs._s.remove("window/geometry")
    c.win.prefs._s.sync()
    ini = QSettings(c.win.prefs._s.fileName(), QSettings.Format.IniFormat)
    assert not ini.contains("window/geometry"), "could not clear the stored geometry"
    c.win.showNormal()
    c.win.resize(*QUIT_SIZE)
    settle()
    assert (c.win.width(), c.win.height()) == QUIT_SIZE, (c.win.width(), c.win.height())


@helper("feedback.window_closed")
def _feedback_window_closed(c: Ctx) -> None:
    from PySide6.QtCore import QSettings
    saved = QSettings(c.win.prefs._s.fileName(), QSettings.Format.IniFormat)
    assert saved.contains("window/geometry"), "the window settings were not saved"
    data = bytes(saved.value("window/geometry"))
    # saveGeometry layout: magic(4) version(4) frame rect(16) normal-geometry rect(16) ...
    x1, y1, x2, y2 = struct.unpack(">4i", data[24:40])
    assert (x2 - x1 + 1, y2 - y1 + 1) == QUIT_SIZE, (x2 - x1 + 1, y2 - y1 + 1)


# -- undo, redo ------------------------------------------------------------------------------
def _stack(c: Ctx):
    win = c.win
    return win.sablon.undo_stack if c.tab == "sablonlar" else win.controller().undo_stack


def _push_steps(c: Ctx, names: tuple[str, ...]) -> None:
    """Real undoable edits: a rename of the job, or a new variable on Şablonlar."""
    win, stack = c.win, _stack(c)
    base = stack.index()
    c.undo.append(lambda: stack.setIndex(base))
    for name in names:
        if c.tab == "sablonlar":
            ok = win.sablon._edit(name, lambda t, n=name: t.add_variable(n.replace(" ", "_")))
        else:
            ok = win.controller().run(name, lambda job, n=name: setattr(job, "name", n))
        assert ok, name
    settle()


@helper("pre.undo_steps")
def _pre_undo_steps(c: Ctx) -> None:
    _push_steps(c, ("Deneme A", "Deneme B"))


@helper("pre.redo_steps")
def _pre_redo_steps(c: Ctx) -> None:
    _push_steps(c, ("Deneme A", "Deneme B"))
    _stack(c).undo()
    settle()


def _item(c: Ctx, action_id: str) -> str:
    """The menu item's text without its access key marker."""
    return c.win.registry.action(action_id).text().replace("&", "")


@helper("snap.stack")
def _snap_stack(c: Ctx) -> dict:
    if c.win.controller() is None and c.tab != "sablonlar":
        return {}  # no job: no undo stack
    stack = _stack(c)
    return {"index": stack.index(), "undo": stack.undoText(), "redo": stack.redoText(),
            "undo_item": _item(c, "app.geri_al"), "redo_item": _item(c, "app.yinele")}


def _has_variable(c: Ctx, name: str) -> bool:
    return any(v.name == name for v in c.win.sablon.template.variables)


@helper("effect.undone")
def _effect_undone(c: Ctx) -> None:
    stack = _stack(c)
    assert stack.index() == c.snap["index"] - 1
    if c.tab == "sablonlar":
        assert not _has_variable(c, "Deneme_B") and _has_variable(c, "Deneme_A")
    else:
        assert c.win.controller().job.name == "Deneme A"


@helper("effect.redone")
def _effect_redone(c: Ctx) -> None:
    stack = _stack(c)
    assert stack.index() == c.snap["index"] + 1
    if c.tab == "sablonlar":
        assert _has_variable(c, "Deneme_B")
    else:
        assert c.win.controller().job.name == "Deneme B"


@helper("feedback.undo_item")
def _feedback_undo_item(c: Ctx) -> None:
    win = c.win
    assert c.snap["undo_item"] == "Geri al: Deneme B"
    assert _item(c, "app.geri_al") == "Geri al: Deneme A"
    assert _item(c, "app.yinele") == "Yinele: Deneme B"
    assert "Geri al: Deneme A" in win.registry.action("app.geri_al").toolTip()
    if c.tab == "rehber":  # INTENDED (M-17): the step is announced, Rehber shows no job content
        assert said(win, "Geri alındı: Deneme B."), heard(win)


@helper("feedback.redo_item")
def _feedback_redo_item(c: Ctx) -> None:
    win = c.win
    assert c.snap["redo_item"] == "Yinele: Deneme B"
    assert _item(c, "app.yinele") == "Yinele"
    assert _item(c, "app.geri_al") == "Geri al: Deneme B"
    if c.tab == "rehber":  # INTENDED (M-17)
        assert said(win, "Yinelendi: Deneme B."), heard(win)


# -- find, next result -----------------------------------------------------------------------
@helper("pre.find_start")
def _pre_find_start(c: Ctx) -> None:
    win = c.win
    c.data["modals"] = []
    if c.tab == "rehber":
        win.rehber.side.hide()  # F9 hid it: Ctrl+F shows it again
    elif c.tab == "yukle":
        c.undo.append(lambda: (setattr(win.yukle, "_listing", False), win.yukle._sync_state()))
    elif c.tab == "kontrol":
        win.kontrol.go_to_document(1)
        _go_to_dialog(c)
    win.title_tabs.setFocus() if c.tab in ("yukle", "rehber") else None
    settle()


@helper("effect.find")
def _effect_find(c: Ctx) -> None:
    win, focus = c.win, QApplication.focusWidget()
    if c.tab == "yukle":
        assert win.yukle._listing is True
        assert focus is win.yukle.empty.search
    elif c.tab == "kontrol":
        assert c.data["modals"], "the go-to dialog did not open"
        assert win.kontrol.current_document() == 2
    elif c.tab == "sablonlar":
        assert focus is win.sablon.variables
        assert win.sablon.variables.currentItem() is not None
    elif c.tab == "degerler":
        assert focus is win.degerler.search
    elif c.tab == "disa_aktar":
        assert focus is win.disa_aktar.results
        assert win.disa_aktar.results.currentIndex().isValid()
    elif c.tab == "rehber":
        assert not win.rehber.side.isHidden()
        assert focus is win.rehber.search


@helper("feedback.find")
def _feedback_find(c: Ctx) -> None:
    win, focus = c.win, QApplication.focusWidget()
    assert_focus_ring(win)
    if c.tab == "yukle":
        assert win.yukle.stack.currentWidget() is win.yukle.empty
        press(win, "Esc")
        assert win.yukle._listing is False  # Esc goes back
    elif c.tab == "kontrol":
        assert focus is win.kontrol.timeline
        # INTENDED (M-03): the item says what it does
        assert win.registry.action("app.bul").text().replace("&", "") == \
            "Belgeye veya sayfaya git…"
    elif c.tab == "degerler":
        assert win.degerler.search.selectedText() == win.degerler.search.text()
    elif c.tab == "rehber":
        assert win.rehber.search.selectedText() == win.rehber.search.text()


@helper("pre.search_hits")
def _pre_search_hits(c: Ctx) -> None:
    rehber = c.win.rehber
    if c.tab == "rehber":
        rehber.search.setText("sayfa")
        settle(10)
        assert len(rehber._hits) >= 2, "the demo query has too few hits"
        c.data["query"] = rehber.search
        c.undo.append(lambda: rehber.search.clear())
        rehber.text.setFocus()
        settle()


@helper("snap.hit")
def _snap_hit(c: Ctx) -> dict:
    r = c.win.rehber
    return {"hit": r.text.current(), "hits": len(r._hits)}


def _stepped(c: Ctx, step: int) -> None:
    r = c.win.rehber
    assert r.text.current() == (c.snap["hit"] + step) % c.snap["hits"]


@helper("effect.hit_next")
def _effect_hit_next(c: Ctx) -> None:
    if c.tab != "rehber":  # INTENDED (M-07): the tab says there is nothing to step through
        assert said(c.win, "Bu sekmede aranacak sonuç yok."), heard(c.win)
        return
    _stepped(c, 1)


@helper("effect.hit_previous")
def _effect_hit_previous(c: Ctx) -> None:
    if c.tab != "rehber":
        assert said(c.win, "Bu sekmede aranacak sonuç yok."), heard(c.win)
        return
    _stepped(c, -1)


@helper("feedback.hit_shown")
def _feedback_hit_shown(c: Ctx) -> None:
    if c.tab != "rehber":
        return
    r = c.win.rehber
    assert plain(r.result.text()) == f"{c.snap['hits']} sonuç, {r.text.current() + 1} / " \
                                     f"{c.snap['hits']}"


@helper("broken.no_hits_rehber")
def _broken_no_hits_rehber(c: Ctx) -> None:
    c.win.rehber.search.clear()
    settle()


# -- zoom ------------------------------------------------------------------------------------
def _zoom(c: Ctx):
    ctl = c.win.zoom_controller()
    assert ctl is not None, f"{c.tab} has no zoom"
    return ctl


@helper("pre.zoom_mid")
def _pre_zoom_mid(c: Ctx) -> None:
    ctl = _zoom(c)
    old = ctl.zoom()
    c.undo.append(lambda: ctl.set_zoom(old))
    ctl.set_zoom((ctl.minimum() + ctl.maximum()) // 2)
    settle()


@helper("snap.zoom")
def _snap_zoom(c: Ctx) -> dict:
    ctl = c.win.zoom_controller()
    return {"zoom": ctl.zoom() if ctl is not None else None}


@helper("effect.zoom_in")
def _effect_zoom_in(c: Ctx) -> None:
    assert _zoom(c).zoom() > c.snap["zoom"]


@helper("effect.zoom_out")
def _effect_zoom_out(c: Ctx) -> None:
    assert _zoom(c).zoom() < c.snap["zoom"]


@helper("effect.zoom_fit")
def _effect_zoom_fit(c: Ctx) -> None:
    ctl = _zoom(c)
    assert ctl.zoom() != c.snap["zoom"]
    if c.tab in ("kontrol", "rehber"):
        assert ctl.zoom() == 100  # a reset, not a fit (M-20 is about the words)


@helper("feedback.zoom_shown")
def _feedback_zoom_shown(c: Ctx) -> None:
    win, ctl = c.win, _zoom(c)
    assert win.zoom_slider.isVisibleTo(win)
    assert win.zoom_slider.slider.value() == ctl.zoom()
    assert str(ctl.zoom()) in win.zoom_slider.label.text()


@helper("feedback.zoom_reset_named")
def _feedback_zoom_reset_named(c: Ctx) -> None:
    _feedback_zoom_shown(c)  # INTENDED (M-20, Q-08): the item says it resets
    assert c.win.registry.action("app.sigdir").toolTip() == "Varsayılan boyuta dön (Ctrl+0)"


@helper("broken.zoom_at_limit")
def _broken_zoom_at_limit(c: Ctx) -> None:
    ctl = _zoom(c)
    old = ctl.zoom()
    c.undo.append(lambda: ctl.set_zoom(old))
    spec = actions.spec(c.action_id)
    if c.action_id == "app.yakinlastir":
        ctl.set_zoom(ctl.maximum())
    elif c.action_id == "app.uzaklastir":
        ctl.set_zoom(ctl.minimum())
    else:
        ctl.fit()
    assert spec is not None
    settle()


@helper("na.zoom_unchanged")
def _na_zoom_unchanged(c: Ctx) -> None:
    ctl = _zoom(c)
    assert ctl.zoom() == c.snap["zoom"]
    assert c.win.zoom_slider.slider.value() == ctl.zoom()


# -- text size, full screen, side panel -------------------------------------------------------
def _scale():
    from evrakci.ui import theme

    return theme.manager()


def _bar_height(c: Ctx) -> int:
    """The body type size in px at the current text size: what every text and control uses."""
    settle(10)
    return _scale().size("fs-body")


@helper("pre.text_scale_base")
def _pre_text_scale_base(c: Ctx) -> None:
    m = _scale()
    old = m.text_scale()
    c.undo.append(lambda: m.set_text_scale(old))
    m.set_text_scale(100 if c.action_id == "app.yazi_buyut" else 130)
    settle()


@helper("snap.text")
def _snap_text(c: Ctx) -> dict:
    return {"scale": _scale().text_scale(), "height": _bar_height(c)}


@helper("effect.text_step")
def _effect_text_step(c: Ctx) -> None:
    from evrakci.ui.main_window import TEXT_STEPS

    step = 1 if c.action_id == "app.yazi_buyut" else -1
    assert _scale().text_scale() == TEXT_STEPS[TEXT_STEPS.index(c.snap["scale"]) + step]


@helper("feedback.text_rescaled")
def _feedback_text_rescaled(c: Ctx) -> None:
    height = _bar_height(c)
    if c.action_id == "app.yazi_buyut":
        assert height > c.snap["height"], "the text did not grow"
    else:
        assert height < c.snap["height"], "the text did not shrink"


@helper("broken.text_at_limit")
def _broken_text_at_limit(c: Ctx) -> None:
    from evrakci.ui.main_window import TEXT_STEPS

    m = _scale()
    old = m.text_scale()
    c.undo.append(lambda: m.set_text_scale(old))
    m.set_text_scale(TEXT_STEPS[-1] if c.action_id == "app.yazi_buyut" else TEXT_STEPS[0])
    settle()


@helper("na.text_unchanged")
def _na_text_unchanged(c: Ctx) -> None:
    assert _scale().text_scale() == c.snap["scale"]
    assert _bar_height(c) == c.snap["height"]


@helper("effect.full_screen")
def _effect_full_screen(c: Ctx) -> None:
    assert c.win.isFullScreen()


@helper("feedback.full_screen")
def _feedback_full_screen(c: Ctx) -> None:
    assert c.win.registry.action("app.tam_ekran").isChecked(), "no check mark on the item"


@helper("snap.panel")
def _snap_panel(c: Ctx) -> dict:
    side = c.win.inspector(c.tab)
    return {"hidden": side.isHidden() if side is not None else None}


@helper("effect.panel_toggled")
def _effect_panel_toggled(c: Ctx) -> None:
    side = c.win.inspector(c.tab)
    assert side is not None and side.isHidden() is (not c.snap["hidden"])


@helper("feedback.panel_tooltip")
def _feedback_panel_tooltip(c: Ctx) -> None:
    from evrakci.ui.main_window import PANEL_NAMES

    verb = "göster" if c.win.inspector(c.tab).isHidden() else "gizle"
    tip = c.win.registry.action("app.yan_panel").toolTip()
    assert tip == f"{PANEL_NAMES[c.tab]} {verb} ({actions.key_text('F9')})", tip


# -- refresh (F5) -----------------------------------------------------------------------------
@helper("pre.refresh_change")
def _pre_refresh_change(c: Ctx) -> None:
    """Change what the tab lists on disk behind its back, so F5 has something to show."""
    win, tab = c.win, c.tab
    if tab == "yukle":
        from fakes import make_pdf, text_page

        pdf = make_pdf((c.tmp or Path(".")) / "f5.pdf", [text_page("F")])
        job = win.store.create_job("Yenile denemesi", [pdf])
        c.data["job"] = job
        c.undo.append(lambda: win.store.delete(job.id))
    elif tab == "sablonlar":
        template = win.template_store.create("Yenile şablonu")
        c.data["template"] = template
        c.undo.append(lambda: win.template_store._path(template.id).unlink(missing_ok=True))
    elif tab == "disa_aktar":
        d = win.disa_aktar
        out = (c.tmp or Path(".")) / "f5-klasor"
        d.folder.setText(str(out))
        d._folder = type(d._folder)(*d._folder) if hasattr(d._folder, "_fields") else d._folder
        c.data["folder"] = out
        c.data["kind"] = d._folder.kind
        out.mkdir(exist_ok=True)  # the disk changes behind the screen's back
    elif tab == "degerler":
        from PySide6.QtTest import QSignalSpy

        spy = QSignalSpy(win.degerler.model.modelReset)
        c.data["spy"] = spy
        c.data["value"] = win.degerler.current_value()
    settle()


@helper("effect.refreshed")
def _effect_refreshed(c: Ctx) -> None:
    win, tab = c.win, c.tab
    if tab == "yukle":
        assert wait_until(lambda: "Yenile denemesi" in [e.name for e in win.yukle.empty.entries])
    elif tab == "sablonlar":
        assert wait_until(lambda: any(
            "Yenile şablonu" in win.sablon.templates.item(i).text()
            if hasattr(win.sablon.templates.item(i), "text") else False
            for i in range(win.sablon.templates.count())) or win.sablon.templates.count() >= 3)
    elif tab == "degerler":
        assert c.data["spy"].count() >= 1, "the table was not rebuilt"
    elif tab == "disa_aktar":
        assert win.disa_aktar._folder.kind != c.data["kind"], "the folder state was not read again"


@helper("feedback.refreshed")
def _feedback_refreshed(c: Ctx) -> None:
    win, tab = c.win, c.tab
    if tab == "degerler":
        assert win.degerler.current_value() == c.data["value"], "the current value moved"
    elif tab == "sablonlar":
        assert win.sablon.template is not None  # the open template stays selected
    elif tab == "disa_aktar":
        assert win.disa_aktar.folder.text() == str(c.data["folder"])
    assert win.registry.is_enabled("app.yenile")


@helper("effect.refresh_off_with_reason")
def _effect_refresh_off_with_reason(c: Ctx) -> None:  # INTENDED (M-22, Q-08)
    action = c.win.registry.action("app.yenile")
    assert not action.isEnabled(), "F5 is enabled and does nothing here"
    assert action.toolTip() == "Bu sekmede yenilenecek bir şey yok.", action.toolTip()


# -- settings, help, sheet, palette ------------------------------------------------------------
@helper("pre.remember_opener")
def _pre_remember_opener(c: Ctx) -> None:
    c.data["opener"] = QApplication.focusWidget()
    c.undo.append(lambda: c.win.settings_dialog.close() if c.win.settings_dialog else None)


@helper("effect.settings_open")
def _effect_settings_open(c: Ctx) -> None:
    dialog = c.win.settings_dialog
    assert dialog is not None and dialog.isVisible()


@helper("feedback.settings_focus")
def _feedback_settings_focus(c: Ctx) -> None:
    win, dialog = c.win, c.win.settings_dialog
    focus = dialog.focusWidget()
    assert focus is not None and dialog.isAncestorOf(focus), "focus is not inside the dialog"
    press_in(dialog, "Esc")
    reactivate(win)
    assert not dialog.isVisible()
    assert QApplication.focusWidget() is c.data["opener"], "focus did not return to the opener"


@helper("effect.help_shown")
def _effect_help_shown(c: Ctx) -> None:
    assert c.win.current_tab() == "rehber"
    if c.tab == "rehber":  # INTENDED (M-24): never a silent no-op: focus moves to the guide
        assert focus_in(c.win, c.win.rehber.text), "focus did not move to the guide text"


@helper("feedback.help_shown")
def _feedback_help_shown(c: Ctx) -> None:
    assert c.win.rehber.text.isVisibleTo(c.win)
    assert c.win.title_tabs.currentIndex() == TAB_IDS.index("rehber")


@helper("effect.sheet_open")
def _effect_sheet_open(c: Ctx) -> None:
    sheet = c.win.shortcut_sheet
    assert sheet.isVisible()
    rows = sheet.visible_rows()
    own = {actions.plain_text(s.text) for s in actions.SPECS
           if s.context == c.tab and s.shortcuts}
    shown = {command for _g, command, _k in rows}
    assert shown & own, "the sheet lists none of this tab's own keys"
    assert {"Yükle", "Kontrol"} <= shown, "the sheet lists no tab keys"


@helper("feedback.sheet_open")
def _feedback_sheet_open(c: Ctx) -> None:
    win, sheet = c.win, c.win.shortcut_sheet
    assert len({g for g, _c, _k in sheet.visible_rows()}) >= 2, "the keys are not grouped"
    opener = c.data.get("opener")
    press_in(sheet, "Esc")
    reactivate(win)
    assert not sheet.isVisible()
    if opener is not None:
        assert QApplication.focusWidget() is opener, "focus did not return to where it was"


@helper("pre.remember_focus")
def _pre_remember_focus(c: Ctx) -> None:
    c.data["opener"] = QApplication.focusWidget()
    c.undo.append(lambda: c.win.shortcut_sheet.close())


@helper("broken.in_text_field")
def _broken_in_text_field(c: Ctx) -> None:
    from PySide6.QtWidgets import QLineEdit

    edit = QLineEdit(c.win.tabs.currentWidget())
    edit.resize(120, 24)
    edit.show()
    c.undo.append(edit.deleteLater)
    edit.setFocus()
    settle()
    assert QApplication.focusWidget() is edit
    c.data["edit"] = edit


@helper("na.question_mark_typed")
def _na_question_mark_typed(c: Ctx) -> None:
    assert c.data["edit"].text() == "?", "the ? was not typed into the field"
    assert not c.win.shortcut_sheet.isVisible(), "the sheet opened while typing"


@helper("effect.palette_open")
def _effect_palette_open(c: Ctx) -> None:
    palette = c.win.command_palette
    assert palette.isVisible()
    ids = {e.id for e in palette.entries()} if hasattr(palette.entries()[0], "id") else set()
    names = [e.text for e in palette.entries()]
    assert "Ayarlar…" in names or ids, names[:5]
    assert any(c.tab in e.id or e.id.startswith("app.") for e in palette.entries())


@helper("feedback.palette_open")
def _feedback_palette_open(c: Ctx) -> None:
    win, palette = c.win, c.win.command_palette
    assert QApplication.focusWidget() is palette.field
    press(win, "Esc")
    assert not palette.isVisible()


# -- the plans -------------------------------------------------------------------------------
for _tab in TAB_IDS:
    PLANS[f"app.sekme.{_tab}"] = Plan(pre="pre.focus_title_tabs", effect="effect.tab_shown",
                                       feedback="feedback.tab_shown")
PLANS["app.sonraki_sekme"] = Plan(pre="pre.focus_title_tabs", effect="effect.tab_next",
                                  feedback="feedback.tab_cycled")
PLANS["app.onceki_sekme"] = Plan(pre="pre.focus_title_tabs", effect="effect.tab_previous",
                                 feedback="feedback.tab_cycled")
PLANS["app.sonraki_bolge"] = Plan(pre="pre.focus_command_bar", effect="effect.region_next",
                                  feedback="feedback.region")
PLANS["app.onceki_bolge"] = Plan(pre="pre.focus_command_bar", effect="effect.region_previous",
                                 feedback="feedback.region")


# kontrol and değerler answer the go-to dialog; the other tabs are INTENDED to route the key
# (M-01); Yükle and Rehber have no document list and are INTENDED to say so (Q-08).
_GIT_NOJOB = "M-01: Ctrl+G is disabled with no word on this tab; INTENDED status line"
PLANS["app.git"] = Plan(pre="pre.go_to_first_document", effect="effect.go_to_document_2",
                        feedback="feedback.go_to_document_2", na="na.says_no_job",
                        na_pre="pre.none")
for _tab in ("yukle", "rehber"):
    PLANS["app.git", _tab] = Plan(
        pre="pre.job_tab_no_dialog", effect="effect.go_to_says_no_documents",
        feedback="feedback.go_to_says_no_documents", na="na.says_no_job", na_pre="pre.none",
        xfail={k: "M-01 Q-08: Ctrl+G is disabled here; INTENDED status line 'PROPOSED: Bu "
                  "sekmede belge listesi yok...'" for k in ("effect", "via")})
for _tab in ("sablonlar", "disa_aktar"):
    PLANS["app.git", _tab] = Plan(
        pre="pre.go_to_first_document", effect="effect.go_to_document_2",
        feedback="feedback.go_to_document_2", na="na.says_no_job", na_pre="pre.none",
        xfail={k: "M-01: Ctrl+G is disabled on this tab; INTENDED to route the go-to dialog"
               for k in ("effect", "via")})
PLANS["app.git", "kontrol"] = Plan(
    pre="pre.go_to_first_document", effect="effect.go_to_document_2",
    feedback="feedback.go_to_document_2", na="na.says_no_job", na_pre="pre.none",
    xfail={"na": "M-30: no job: Kontrol keys are disabled and silent (Ctrl+G is not in "
                 "M-30's key list)"})
PLANS["app.git", "degerler"] = Plan(
    pre="pre.go_to_first_document", effect="effect.go_to_document_2",
    feedback="feedback.go_to_document_2", na="na.says_no_job", na_pre="pre.none")

PLANS["app.kaydet"] = Plan(pre="pre.saveable", effect="effect.written_now",
                           feedback="feedback.saved_said", na="na.says_no_job",
                           na_pre="pre.none")
PLANS["app.disa_aktar"] = Plan(
    pre="pre.none", effect="effect.export_tab_shown", feedback="feedback.export_tab_shown",
    na="na.says_no_job", na_pre="pre.none")
PLANS["app.isi_kapat"] = Plan(
    pre="pre.job_open_state", window="fresh", effect="effect.job_closed",
    feedback="feedback.job_closed", na="na.says_no_job", na_pre="pre.none",
    xfail={"na": "M-15: no job: Ctrl+W is disabled and silent"})

PLANS["app.kaydet", "rehber"] = Plan(
    pre="pre.none", effect="effect.says.rehber_save", feedback="feedback.none",
    na="na.says.rehber_save", na_pre="pre.none",
    xfail={k: "M-09 Q-08: Ctrl+S is off on Rehber with no word; INTENDED status line "
              "'PROPOSED: Rehber'de kaydedilecek bir şey yok.'" for k in ("effect", "via", "na")})
PLANS["app.kaydet", "sablonlar"] = Plan(
    pre="pre.saveable", effect="effect.written_now", feedback="feedback.saved_said",
    na="na.says.no_template_save", na_pre="pre.none",
    xfail={"na": "M-11: no template: Ctrl+S is disabled; INTENDED to show the existing text "
                 "'Kaydedilecek bir şablon yok...'; conflicts with "
                 "test_sablon_window.py::test_nothing_is_usable_without_a_template; owner Q-09"})
PLANS["app.disa_aktar", "disa_aktar"] = Plan(
    pre="pre.export_ready", window="fresh", effect="effect.export_written",
    feedback="feedback.export_done", na_window="fresh", na_pre="pre.none",
    broken="broken.export_blocked", na="na.export_blocked_says_why",
    xfail={"na": "M-13: blocked or running: Ctrl+E is disabled; INTENDED to show the toast "
                 "'Dışa aktarılamıyor: ...'"})
PLANS["app.yeni_is"] = Plan(
    pre="pre.new_job_pickers", window="fresh", effect="effect.new_job_opened",
    feedback="feedback.new_job_opened", na_pre="pre.none", na_window="empty",
    broken="broken.read_running_no_job", na="na.says_read_running")
PLANS["app.dosya_ekle"] = Plan(
    pre="pre.add_file_picker", window="fresh", effect="effect.batch_added",
    feedback="feedback.batch_added", na_pre="pre.none", na_window="empty",
    broken="broken.read_running_no_job", na="na.says_read_running")
PLANS["app.cikis"] = Plan(
    pre="pre.quit_known_geometry", window="fresh_empty", effect="effect.window_closed",
    feedback="feedback.window_closed", na_window="fresh_empty")

# undo, redo: the job's stack (Şablonlar: the template's own); Rehber shows no job content, so
# its step is INTENDED to be announced (M-17); with nothing to undo the key is INTENDED to say so.
PLANS["app.geri_al"] = Plan(
    pre="pre.undo_steps", snap="snap.stack", effect="effect.undone",
    feedback="feedback.undo_item", na_pre="pre.none", na="na.says.nothing_to_undo",
    xfail={"na": "M-16 Q-08: nothing to undo: Ctrl+Z is disabled and silent"})
PLANS["app.yinele"] = Plan(
    pre="pre.redo_steps", snap="snap.stack", effect="effect.redone",
    feedback="feedback.redo_item", na_pre="pre.none", na="na.says.nothing_to_redo",
    xfail={"na": "M-16 Q-08: nothing to redo: the key is disabled and silent"})
PLANS["app.geri_al", "rehber"] = Plan(
    pre="pre.undo_steps", snap="snap.stack", effect="effect.undone",
    feedback="feedback.undo_item", na_pre="pre.none", na="na.says.nothing_to_undo",
    xfail={"effect": "M-17 Q-08: Ctrl+Z on Rehber undoes out of sight; INTENDED status line "
                     "'PROPOSED: Geri alındı: <adım>.'",
           "via": "M-17 Q-08: the step is not announced on Rehber",
           "na": "M-16 Q-08: nothing to undo: Ctrl+Z is disabled and silent"})
for _key in ("Ctrl+Y", "Ctrl+Shift+Z"):
    PLANS["app.yinele", "rehber", _key] = Plan(
        pre="pre.redo_steps", snap="snap.stack", effect="effect.redone",
        feedback="feedback.redo_item", na_pre="pre.none", na="na.says.nothing_to_redo",
        xfail={"effect": "M-17 Q-08: redo on Rehber happens out of sight; INTENDED status line "
                         "'PROPOSED: Yinelendi: <adım>.'",
               "via": "M-17 Q-08: the step is not announced on Rehber",
               "na": "M-16 Q-08: nothing to redo: the key is disabled and silent"})

# find: each tab finds what it lists (page-specific, shortcuts.md)
PLANS["app.bul"] = Plan(
    pre="pre.find_start", effect="effect.find", feedback="feedback.find",
    na_pre="pre.none", na="na.says_no_job")
PLANS["app.bul", "kontrol"] = Plan(
    pre="pre.find_start", effect="effect.find", feedback="feedback.find",
    na_pre="pre.none", na="na.says_no_job",
    xfail={"effect": "M-03: Ctrl+F is labelled 'Bul…' but opens the go-to dialog",
           "via": "M-03: the palette item is labelled 'Bul…' but opens the go-to dialog"})
PLANS["app.bul", "sablonlar"] = Plan(
    pre="pre.find_start", effect="effect.find", feedback="feedback.find",
    na_pre="pre.none", na="na.says.no_variable",
    xfail={"na": "M-05 Q-08: no template: focus moves to an empty list, nothing said"})
PLANS["app.bul", "degerler"] = Plan(
    pre="pre.find_start", effect="effect.find", feedback="feedback.find",
    na_pre="pre.none", na="na.says_no_job")
PLANS["app.bul", "yukle"] = Plan(
    pre="pre.find_start", effect="effect.find", feedback="feedback.find", na_pre="pre.find_start",
    na_window="fresh_closed", na="na.same_as_effect")
PLANS["app.bul", "rehber"] = Plan(
    pre="pre.find_start", effect="effect.find", feedback="feedback.find", na_pre="pre.none",
    na="na.same_as_effect")
PLANS["app.bul", "disa_aktar"] = Plan(
    pre="pre.find_start", effect="effect.find", feedback="feedback.find",
    na_pre="pre.none", na="na.says_no_job")

# F3 / Shift+F3: only Rehber has results; elsewhere INTENDED to say so (M-07, Q-08)
PLANS["app.sonraki_sonuc"] = Plan(
    pre="pre.none", effect="effect.hit_next", feedback="feedback.hit_shown",
    na_pre="pre.none", na="na.says.no_results",
    xfail={k: "M-07 Q-08: F3 is disabled and silent on this tab; INTENDED status line "
              "'PROPOSED: Bu sekmede aranacak sonuç yok.'" for k in ("effect", "via", "na")})
PLANS["app.onceki_sonuc"] = Plan(
    pre="pre.none", effect="effect.hit_previous", feedback="feedback.hit_shown",
    na_pre="pre.none", na="na.says.no_results",
    xfail={k: "M-07 Q-08: Shift+F3 is disabled and silent on this tab; INTENDED status line "
              "'PROPOSED: Bu sekmede aranacak sonuç yok.'" for k in ("effect", "via", "na")})
PLANS["app.sonraki_sonuc", "rehber"] = Plan(
    pre="pre.search_hits", snap="snap.hit", effect="effect.hit_next",
    feedback="feedback.hit_shown", na_pre="pre.none", na_window="job",
    broken="broken.no_hits_rehber", na="na.says.no_hits",
    xfail={"na": "M-08: no query or no hits: F3 is disabled; INTENDED to announce 'Sonuç yok'"})
PLANS["app.onceki_sonuc", "rehber"] = Plan(
    pre="pre.search_hits", snap="snap.hit", effect="effect.hit_previous",
    feedback="feedback.hit_shown", na_pre="pre.none", na_window="job",
    broken="broken.no_hits_rehber", na="na.says.no_hits",
    xfail={"na": "M-08: no query or no hits: Shift+F3 is disabled; INTENDED to announce "
                 "'Sonuç yok'"})

# zoom: the tab's own zoom; Yükle and Dışa Aktar have none and are INTENDED to say so (M-18)
for _id, _eff in (("app.yakinlastir", "effect.zoom_in"), ("app.uzaklastir", "effect.zoom_out"),
                  ("app.sigdir", "effect.zoom_fit")):
    PLANS[_id] = Plan(pre="pre.zoom_mid", snap="snap.zoom", effect=_eff,
                      feedback="feedback.zoom_shown", na_pre="pre.none", na_window="job",
                      broken="broken.zoom_at_limit", na="na.zoom_unchanged")
    for _tab in ("yukle", "disa_aktar"):
        PLANS[_id, _tab] = Plan(
            pre="pre.none", effect="effect.says.no_zoom", feedback="feedback.none_needed",
            na_pre="pre.none", na="na.says.no_zoom",
            xfail={k: "M-18 Q-08: the zoom keys are disabled and silent here; INTENDED status "
                      "line 'PROPOSED: Bu sekmede yakınlaştırılacak bir şey yok.'"
                   for k in ("effect", "via", "na")})
    PLANS[_id, "sablonlar"] = Plan(
        pre="pre.zoom_mid", snap="snap.zoom", effect=_eff, feedback="feedback.zoom_shown",
        na_pre="pre.none", na="na.says.no_zoom",
        xfail={"na": "M-19 Q-08: no template or page: the zoom keys are disabled and silent"})
for _tab in ("kontrol", "rehber"):
    PLANS["app.sigdir", _tab] = Plan(
        pre="pre.zoom_mid", snap="snap.zoom", effect="effect.zoom_fit",
        feedback="feedback.zoom_reset_named", na_pre="pre.none", na_window="job",
        broken="broken.zoom_at_limit", na="na.zoom_unchanged",
        xfail={k: "M-20 Q-08: 'Sığdır' resets to 100 % and does not fit; INTENDED tooltip "
                  "'PROPOSED: Varsayılan boyuta dön (Ctrl+0)'" for k in ("effect", "via")})

# text size, full screen, side panel
for _id in ("app.yazi_buyut", "app.yazi_kucult"):
    PLANS[_id] = Plan(pre="pre.text_scale_base", snap="snap.text", effect="effect.text_step",
                      feedback="feedback.text_rescaled", na_pre="pre.none", na_window="job",
                      broken="broken.text_at_limit", na="na.text_unchanged")
PLANS["app.tam_ekran"] = Plan(effect="effect.full_screen", feedback="feedback.full_screen")
PLANS["app.yan_panel"] = Plan(snap="snap.panel", effect="effect.panel_toggled",
                              feedback="feedback.panel_tooltip")
PLANS["app.yan_panel", "kontrol"] = Plan(
    snap="snap.panel", effect="effect.panel_toggled", feedback="feedback.panel_tooltip",
    na_pre="pre.none", na="na.says_no_job",
    xfail={"na": "M-21: no job: Kontrol has no side panel and F9 is disabled, silent; "
                 "conflicts with test_shell.py::test_f9_hides_and_shows_the_side_panel; "
                 "owner Q-09"})

# refresh
PLANS["app.yenile"] = Plan(pre="pre.refresh_change", effect="effect.refreshed",
                           feedback="feedback.refreshed", na_pre="pre.refresh_change")
for _tab in ("kontrol", "rehber"):
    PLANS["app.yenile", _tab] = Plan(
        pre="pre.none", effect="effect.refresh_off_with_reason", feedback="feedback.none_needed",
        na_pre="pre.none", na_window="job", na="na.same_as_effect",
        xfail={k: "M-22 Q-08 (B-028): F5 is enabled and does nothing; INTENDED disabled with "
                  "tooltip 'PROPOSED: Bu sekmede yenilenecek bir şey yok.'"
               for k in ("effect", "via", "na")})
PLANS["app.yenile", "disa_aktar"] = Plan(
    pre="pre.refresh_change", effect="effect.refreshed", feedback="feedback.refreshed",
    na_pre="pre.none", na="na.says_no_job")

# dialogs and sheets
PLANS["app.ayarlar"] = Plan(pre="pre.remember_opener", effect="effect.settings_open",
                            feedback="feedback.settings_focus", na_pre="pre.remember_opener")
PLANS["app.yardim"] = Plan(pre="pre.focus_title_tabs", effect="effect.help_shown",
                           feedback="feedback.help_shown")
PLANS["app.yardim", "rehber"] = Plan(
    pre="pre.focus_title_tabs", effect="effect.help_shown", feedback="feedback.help_shown")
PLANS["app.kisayollar"] = Plan(pre="pre.remember_focus", effect="effect.sheet_open",
                               feedback="feedback.sheet_open", na_pre="pre.remember_focus")
for _tab in TAB_IDS:
    PLANS["app.kisayollar", _tab, "?"] = Plan(
        pre="pre.remember_focus", effect="effect.sheet_open", feedback="feedback.sheet_open",
        na_pre="pre.none", broken="broken.in_text_field", na_window="job",
        na="na.question_mark_typed")
PLANS["app.komut_ara"] = Plan(effect="effect.palette_open", feedback="feedback.palette_open")
