"""Phase 3, step 3C: docs/ui-goal/shortcut-contract.tsv as tests (harness + the app-wide rows).

One parametrized module reads the TSV. For every row whose action id starts with `app.` (every
tab where the key is active) there are three tests:

1. test_key_effect_and_feedback: demo window on the row's tab, the precondition set, the REAL key
   sent with QTest to the focus widget; asserts the effect (read from the model, controller or
   widget, never from UI text) and the feedback (status line, toast, focus, item text).
2. test_not_applicable: the precondition broken (no job, empty stack, nothing running...), the
   same key; asserts the row's not_applicable column. Where the column says "always enabled", the
   test proves the key still works with no job open.
3. test_same_through_menu_or_palette: the same action through Ctrl+K's list (or its menu item
   when it is not in the palette) gives the same effect and feedback as the key.

Where the steps live: the TSV is not changed; `tests/ui/contract_helpers.py` holds the mapping
table `PLANS` keyed by action id (or (action id, tab)) to the names of small helpers (`pre.*`,
`snap.*`, `effect.*`, `feedback.*`, `broken.*`, `na.*`), and `HELPERS` maps each name to its
function. Every generated test carries `pytest.mark.action(<action id>)`.

Rows whose INTENDED behaviour (the TSV) differs from today (docs/ui-goal/shortcut-mismatches.md)
assert the intended behaviour and are `xfail(strict=True)` with the M-id; "Q-08" in the reason
means the fix waits for owner-approved Turkish text. Never today's wrong behaviour.

Tab-specific rows (every action id that does not start with `app.`) come in a later step.

Window: one shared demo job (tools/screenshots.py build()) and one shared window with no job; a
test whose action changes the job, closes the window or creates a job builds a fresh demo
window. Synthetic data only.

The audit script finds tests by action id in the source text, so the ids covered here are also
listed in the comment below; test_marker_comment_lists_every_app_action keeps it in step.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QMessageBox

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import screenshots  # noqa: E402
from contract_helpers import (  # noqa: E402
    HELPERS,
    PLANS,
    Ctx,
    load_rows,
    on_modal,
    plan_for,
    press,
    reset,
    settle,
    via,
)

# action: app.sekme.yukle, app.sekme.kontrol, app.sekme.sablonlar, app.sekme.degerler
# action: app.sekme.disa_aktar, app.sekme.rehber, app.sonraki_sekme, app.onceki_sekme
# action: app.sonraki_bolge, app.onceki_bolge, app.git, app.yeni_is, app.dosya_ekle
# action: app.kaydet, app.disa_aktar, app.isi_kapat, app.cikis, app.geri_al, app.yinele
# action: app.bul, app.sonraki_sonuc, app.onceki_sonuc, app.yakinlastir, app.uzaklastir
# action: app.sigdir, app.yazi_buyut, app.yazi_kucult, app.tam_ekran, app.yan_panel
# action: app.yenile, app.ayarlar, app.yardim, app.kisayollar, app.komut_ara

ROWS = load_rows("app.")


def _id(row: dict[str, str]) -> str:
    return f"{row['action_id']}[{row['tab']}]{row['key']}"


def _params(kind: str):
    out = []
    for row in ROWS:
        plan = plan_for(row["action_id"], row["tab"], row["key"])
        marks = [pytest.mark.action(row["action_id"])]
        if kind in plan.xfail:
            marks.append(pytest.mark.xfail(strict=True, reason=plan.xfail[kind]))
        out.append(pytest.param(row, id=_id(row), marks=marks))
    return out


class Windows:
    """The shared windows (built on first use) and fresh ones for tests that change a job."""

    def __init__(self, tmp_path_factory) -> None:
        self._factory = tmp_path_factory
        self._made: list = []
        self._shared: dict[str, object] = {}

    def _show(self, window):
        window.resize(1366, 768)
        window.show()
        window.activateWindow()
        assert QTest.qWaitForWindowActive(window)
        settle()
        self._made.append(window)
        return window

    def fresh(self):
        return self._show(screenshots.build(self._factory.mktemp("demo")))

    def shared(self, which: str):
        if which not in self._shared:
            if which == "job":
                self._shared[which] = self.fresh()
            else:
                self._shared[which] = self.fresh_empty()
        window = self._shared[which]
        window.activateWindow()
        assert QTest.qWaitForWindowActive(window)
        return window

    def fresh_empty(self):
        return self._show(screenshots._empty_window(self._factory.mktemp("empty")))

    def fresh_closed(self):
        """A demo window whose job was closed: no job open, two jobs in 'Tüm işler'."""
        window = self.fresh()
        window.close_job()
        settle()
        return window

    def get(self, which: str):
        if which == "fresh":
            return self.fresh()
        if which == "fresh_closed":
            return self.fresh_closed()
        return self.fresh_empty() if which == "fresh_empty" else self.shared(which)

    def release(self, window) -> None:
        """A fresh window is closed (and forgotten) when its test is over."""
        if window in self._made and window not in self._shared.values():
            self._made.remove(window)
            self._quiet(window)
            window.close()
            window.deleteLater()
            settle()

    @staticmethod
    def _quiet(window) -> None:
        """Stop the thumbnail threads first: destroying a window under a running render
        thread can deadlock (the thread needs the GIL the destructor holds)."""
        if getattr(window, "thumbnails", None) is not None:
            window.thumbnails.stop()
        settle()

    def close(self) -> None:
        for window in self._made:
            self._quiet(window)
            window.close()
            window.deleteLater()
        settle()


@pytest.fixture(scope="module")
def windows(qapp, tmp_path_factory):
    patch = pytest.MonkeyPatch()
    patch.setenv("EVRAKCI_UI_AYARLAR", str(tmp_path_factory.mktemp("ui") / "ui-ayarlar.ini"))
    holder = Windows(tmp_path_factory)
    yield holder
    holder.close()
    patch.undo()


def _start(row, windows, which, tmp_path) -> Ctx:
    win = windows.get(which)
    ctx = Ctx(win, row["tab"], row["key"], row["action_id"], tmp=tmp_path)
    ctx.data["windows"] = windows
    reset(win, ctx.tab)
    return ctx


def _finish(ctx: Ctx) -> None:
    for undo in reversed(ctx.undo):
        undo()
    ctx.undo.clear()
    ctx.data["windows"].release(ctx.win)
    settle()


def _applicable(row, windows, tmp_path, how) -> None:
    plan = plan_for(row["action_id"], row["tab"], row["key"])
    ctx = _start(row, windows, plan.window, tmp_path)
    try:
        HELPERS[plan.pre](ctx)
        ctx.snap = HELPERS[plan.snap](ctx) or {}
        if how == "key":
            press(ctx.win, ctx.key)
        else:
            via(ctx.win, ctx.tab, ctx.action_id)
        HELPERS[plan.effect](ctx)
        HELPERS[plan.feedback](ctx)
    finally:
        _finish(ctx)


@pytest.mark.parametrize("row", _params("effect"))
def test_key_effect_and_feedback(row, windows, tmp_path):
    _applicable(row, windows, tmp_path, "key")


@pytest.mark.parametrize("row", _params("na"))
def test_not_applicable(row, windows, tmp_path):
    plan = plan_for(row["action_id"], row["tab"], row["key"])
    ctx = _start(row, windows, plan.na_window, tmp_path)
    try:
        HELPERS[plan.pre if plan.na_pre == "same" else plan.na_pre](ctx)
        HELPERS[plan.broken](ctx)
        ctx.snap = HELPERS[plan.snap](ctx) or {}
        press(ctx.win, ctx.key)
        HELPERS[plan.na](ctx)
    finally:
        _finish(ctx)


@pytest.mark.parametrize("row", _params("via"))
def test_same_through_menu_or_palette(row, windows, tmp_path):
    _applicable(row, windows, tmp_path, "via")


@pytest.mark.action("app.disa_aktar")
@pytest.mark.xfail(strict=True, reason="M-12: no job: Ctrl+E is disabled and silent on Dışa "
                                       "Aktar too; INTENDED status line 'Önce Yükle "
                                       "sekmesinden bir iş açın (Ctrl+1).'")
def test_export_key_with_no_job_on_the_export_tab(windows, tmp_path):
    """The no-job half of Ctrl+E on Dışa Aktar (its row's own not_applicable test covers a
    blocked export): the same status line as on the other five tabs."""
    row = {"tab": "disa_aktar", "key": "Ctrl+E", "action_id": "app.disa_aktar"}
    ctx = _start(row, windows, "empty", tmp_path)
    try:
        press(ctx.win, "Ctrl+E")
        HELPERS["na.says_no_job"](ctx)
    finally:
        _finish(ctx)


@pytest.mark.action("app.cikis")
def test_quit_asks_first_while_a_read_runs(windows, tmp_path):
    """Ctrl+Q with a read running: the question comes first; No keeps the window open."""
    row = {"tab": "yukle", "key": "Ctrl+Q", "action_id": "app.cikis"}
    ctx = _start(row, windows, "fresh_empty", tmp_path)
    try:
        ctx.win.yukle.task = object()  # busy(): a read is running
        ctx.undo.append(lambda: setattr(ctx.win.yukle, "task", None))

        def say_no(box) -> None:
            ctx.data["question"] = box.text()
            box.button(QMessageBox.StandardButton.No).click()

        on_modal(ctx, say_no)
        press(ctx.win, ctx.key)
        assert ctx.data.get("question") == ("Bir iş sürüyor. Durdurup kapatılsın mı? "
                                            "Yazılmış dosyalar klasörde kalır.")
        assert ctx.win.isVisible(), "No closed the window"
    finally:
        _finish(ctx)


def test_every_app_row_has_a_plan():
    for row in ROWS:
        assert ((row["action_id"], row["tab"], row["key"]) in PLANS
                or (row["action_id"], row["tab"]) in PLANS or row["action_id"] in PLANS), row
        plan = plan_for(row["action_id"], row["tab"], row["key"])
        for name in (plan.pre, plan.snap, plan.effect, plan.feedback, plan.broken, plan.na):
            assert name in HELPERS, (row["action_id"], row["tab"], name)


def test_marker_comment_lists_every_app_action():
    text = Path(__file__).read_text(encoding="utf-8")
    listed = {a for line in re.findall(r"^# action: (.+)$", text, re.M)
              for a in re.split(r",\s*", line.strip())}
    assert listed == {r["action_id"] for r in ROWS}
