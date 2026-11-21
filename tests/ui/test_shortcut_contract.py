"""Phase 3, steps 3C and 3D: docs/ui-goal/shortcut-contract.tsv as tests (harness, the app-wide
rows, the tab-specific rows).

One parametrized module reads the TSV. For every row (every tab where a key is active; 319 rows:
252 `app.` rows and 67 tab-specific ones) there are three tests:

1. test_key_effect_and_feedback: demo window on the row's tab, the precondition set, the REAL key
   sent with QTest to the focus widget; asserts the effect (read from the model, controller or
   widget, never from UI text) and the feedback (status line, toast, focus, item text).
2. test_not_applicable: the precondition broken (no job, empty stack, nothing running...), the
   same key; asserts the row's not_applicable column. Where the column says "always enabled", the
   test proves the key still works with no job open.
3. test_same_through_menu_or_palette: the same action through Ctrl+K's list (or its menu item
   when it is not in the palette) gives the same effect and feedback as the key.

Where the steps live: the TSV is not changed; `tests/ui/contract_helpers.py` holds the mapping
table `PLANS` keyed by action id (or (action id, tab), or (action id, tab, key)) to the names of
small helpers (`pre.*`, `snap.*`, `effect.*`, `feedback.*`, `broken.*`, `na.*`), and `HELPERS`
maps each name to its function. The app-wide rows are filled there; the tab-specific rows in
`contract_yukle.py`, `contract_kontrol.py`, `contract_sablon.py`, `contract_degerler.py` and
`contract_export.py` (Dışa Aktar and Rehber), which register into the same two tables when this
module imports them. Every generated test carries `pytest.mark.action(<action id>)`.

A key with no menu item and no palette entry (`local`: the arrows, Tab, Esc in the guide's search
field, Space on the canvas) has one other route, the shortcut sheet: its third test checks the
sheet lists the key under its label for the tab, closes it, and presses the key again.

Rows whose INTENDED behaviour (the TSV) differs from today (docs/ui-goal/shortcut-mismatches.md)
assert the intended behaviour and are `xfail(strict=True)` with the M-id; "Q-08" in the reason
means the fix waits for owner-approved Turkish text. Never today's wrong behaviour.

Besides the rows, a few tests carry what a row cannot hold: `test_kontrol_refusals` (the refusals
that already say something today), `test_kontrol_key_with_no_job_says_it` (M-30, every Kontrol
key), the label items M-27 / M-34 / M-38 and Esc closing a loupe. Rows whose key only works
while a task runs start a real task with a slow stand-in for the reader or the writer (a
cancelled read keeps what it finished); the job is put back through the undo stack.

Window: one shared demo job (tools/screenshots.py build()) and one shared window with no job; the
Şablonlar, Değerler and Dışa Aktar tests each have a demo window of their own ("job_sablon",
"job_degerler", "job_disa"); a test whose action closes the window or creates a job builds a fresh
demo window. Synthetic data only. A window is never destroyed with thumbnails running (B-044).

The audit script finds tests by action id in the source text, so the ids covered here are also
listed in the comment below; test_marker_comment_lists_every_app_action keeps it in step (it
covers every action of the TSV now, tab-specific ones included).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import contract_degerler  # noqa: E402,F401  (registers Değerler' steps and plans)
import contract_export  # noqa: E402,F401  (registers Dışa Aktar's and Rehber's steps and plans)
import contract_kontrol  # noqa: E402,F401  (registers Kontrol's steps and plans)
import contract_sablon  # noqa: E402,F401  (registers Şablonlar' steps and plans)
import contract_yukle  # noqa: E402,F401  (registers Yükle's steps and plans)
import screenshots  # noqa: E402
from contract_helpers import (  # noqa: E402
    HELPERS,
    PLANS,
    Ctx,
    heard,
    load_rows,
    on_modal,
    plan_for,
    press,
    reset,
    said,
    settle,
    via,
    wait_until,
)

# action: app.sekme.yukle, app.sekme.kontrol, app.sekme.sablonlar, app.sekme.degerler
# action: app.sekme.disa_aktar, app.sekme.rehber, app.sonraki_sekme, app.onceki_sekme
# action: app.sonraki_bolge, app.onceki_bolge, app.git, app.yeni_is, app.dosya_ekle
# action: app.kaydet, app.disa_aktar, yukle.gezginde_goster, app.isi_kapat, app.cikis
# action: app.geri_al, app.yinele, app.bul, app.sonraki_sonuc, app.onceki_sonuc
# action: app.yakinlastir, app.uzaklastir, app.sigdir, app.yazi_buyut, app.yazi_kucult
# action: app.tam_ekran, app.yan_panel, app.yenile, app.ayarlar, app.yardim
# action: app.kisayollar, app.komut_ara, yukle.yukari, yukle.asagi, yukle.cikar
# action: yukle.yeniden_adlandir, yukle.iptal, kontrol.tumunu_sec
# action: kontrol.secimi_kaldir, kontrol.kes, kontrol.birlestir, kontrol.saga_dondur
# action: kontrol.sola_dondur, kontrol.sil, kontrol.onayla, kontrol.filtre
# action: kontrol.sablon, kontrol.onizle, kontrol.sonraki_kontrol
# action: kontrol.filtre_kaldir, kontrol.sablon_kaldir, kontrol.sec, kontrol.belgeyi_sec
# action: kontrol.sayfa_sec, kontrol.git_secimsiz
# action: kontrol.onceki_kontrol, kontrol.sonraki_incelenmemis, kontrol.sonraki_belge
# action: kontrol.onceki_belge, kontrol.sayfa, kontrol.ilk_son, kontrol.ekran
# action: kontrol.secimi_genislet, sablonlar.kutu_ciz, sablonlar.izgara
# action: kontrol.degerlerde_ac, degerler.kontrolde_ac
# action: sablonlar.sonraki_zayif, sablonlar.onceki_zayif, sablonlar.zayif_ornekler
# action: sablonlar.dene, sablonlar.kutu_sil, sablonlar.kutu_cogalt
# action: sablonlar.degisken_ekle, sablonlar.yukari, sablonlar.asagi, sablonlar.kaydir
# action: sablonlar.kaydir_1mm, sablonlar.el, degerler.onayla
# action: degerler.secilenleri_onayla, degerler.elle_yaz, degerler.okunana_don
# action: degerler.varyant
# action: degerler.vazgec, degerler.tumunu_sec, degerler.tum_sayfa
# action: degerler.sonraki_kontrol, degerler.onceki_kontrol, degerler.durdur
# action: degerler.sonraki_deger, disa_aktar.gezginde_goster, disa_aktar.yazdir
# action: disa_aktar.durdur, rehber.yazdir, rehber.aramayi_temizle

ROWS = load_rows("")


def _id(row: dict[str, str]) -> str:
    return f"{row['action_id']}[{row['tab']}]{row['key']}"


def _params(kind: str):
    out = []
    for row in ROWS:
        plan = plan_for(row["action_id"], row["tab"], row["key"])
        marks = [pytest.mark.action(row["action_id"]), *plan.marks]
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
            if which.startswith("job"):  # job_<tab>: a demo window of its own for that tab
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
            via(ctx.win, ctx.tab, ctx.action_id, ctx.key)
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


@pytest.mark.action("app.git")
@pytest.mark.xfail(strict=True, reason="M-02 Q-08: a job is open but Değerler has no rows: "
                                       "go_to() returns without a word; INTENDED status line "
                                       "'PROPOSED: Gidilecek bir belge yok.'")
def test_degerler_go_to_with_a_job_but_no_rows_says_so(windows, tmp_path):
    row = {"tab": "degerler", "key": "Ctrl+G", "action_id": "app.git"}
    ctx = _start(row, windows, "fresh", tmp_path)
    try:
        ctx.win.show_tab("degerler")
        settle()
        assert ctx.win.controller() is not None
        ctx.win.degerler.rows = []  # a job whose documents have no template
        ctx.win.degerler.table.setFocus()
        press(ctx.win, "Ctrl+G")
        assert said(ctx.win, "Gidilecek bir belge yok."), \
            f"nothing said: {heard(ctx.win)!r}"
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


@pytest.mark.parametrize("case", [pytest.param(case, id=case[0], marks=pytest.mark.action(case[1]))
                                  for case in contract_kontrol.REFUSALS])
def test_kontrol_refusals(case, windows, tmp_path):
    """The refusals the contract lists that already say something today (and so need no xfail):
    the key, with its precondition broken the way the column says, answers in words."""
    _name, action_id, key, setup, text = case
    row = {"tab": "kontrol", "key": key, "action_id": action_id}
    ctx = _start(row, windows, "fresh" if setup.endswith("filter_cut") else "job", tmp_path)
    try:
        HELPERS[setup](ctx)
        press(ctx.win, key)
        assert said(ctx.win, text), f"expected {text!r}, saw {heard(ctx.win)!r}"
    finally:
        _finish(ctx)


@pytest.mark.parametrize("case", [pytest.param(case, id=f"{case[0]}[kontrol]{case[1]}",
                                               marks=[pytest.mark.action(case[0]),
                                                      pytest.mark.xfail(
                                                          strict=True, reason="M-30: no job: "
                                                          "every Kontrol key is disabled and "
                                                          "silent")])
                                  for case in contract_kontrol.NO_JOB_KEYS])
def test_kontrol_key_with_no_job_says_it(case, windows, tmp_path):
    """No job open: the key says 'Önce Yükle sekmesinden bir iş açın (Ctrl+1).' (M-30)."""
    action_id, key = case
    ctx = _start({"tab": "kontrol", "key": key, "action_id": action_id}, windows, "empty",
                 tmp_path)
    try:
        press(ctx.win, key)
        HELPERS["na.says_no_job"](ctx)
    finally:
        _finish(ctx)


# -- labels and refusals the rows cannot show (M-27, M-34, M-38) and the loupe's Esc ---------------
@pytest.mark.action("sablonlar.kutu_sil")
def test_sablon_delete_item_names_a_variable(windows, tmp_path):
    row = {"tab": "sablonlar", "key": "Del", "action_id": "sablonlar.kutu_sil"}
    ctx = _start(row, windows, "job_sablon", tmp_path)
    try:
        contract_sablon.ensure_template(ctx)
        contract_sablon.choose(ctx, "Firma_Adi", None)
        assert ctx.win.registry.action("sablonlar.kutu_sil").text().replace("&", "") == \
            "Değişkeni sil"
        palette = {e.id: e.text for e in ctx.win.registry.palette_entries("sablonlar")}
        assert palette["sablonlar.kutu_sil"] == "Değişkeni sil", palette["sablonlar.kutu_sil"]
    finally:
        _finish(ctx)


@pytest.mark.action("sablonlar.kutu_sil")
def test_sablon_delete_removes_a_variable_that_has_no_box_chosen(windows, tmp_path):
    """Del with only a variable chosen removes the variable, says so and offers Geri al."""
    row = {"tab": "sablonlar", "key": "Del", "action_id": "sablonlar.kutu_sil"}
    ctx = _start(row, windows, "job_sablon", tmp_path)
    try:
        contract_sablon.ensure_template(ctx)
        contract_sablon.choose(ctx, "Firma_Adi", None)
        press(ctx.win, "Del")
        assert contract_sablon._names(ctx) == ["Sicil_No"]
        assert ctx.win.toaster.current_text() == "“Firma_Adi” değişkeni silindi (1 kutu)."
        assert contract_sablon._toast_undo(ctx)
        assert ctx.win.sablon.undo_stack.undoText() == "Değişkeni sil"
    finally:
        _finish(ctx)


@pytest.mark.parametrize("case", [
    pytest.param(("sablonlar.yukari", "Alt+Up", "Bölümü yukarı taşı"), id="Alt+Up",
                 marks=pytest.mark.action("sablonlar.yukari")),
    pytest.param(("sablonlar.asagi", "Alt+Down", "Bölümü aşağı taşı"), id="Alt+Down",
                 marks=pytest.mark.action("sablonlar.asagi"))])
@pytest.mark.xfail(strict=True, reason="M-38 Q-08: with a section of a multi-box variable chosen "
                                       "the item still reads 'Değişkeni yukarı/aşağı taşı' but "
                                       "the section moves; INTENDED 'PROPOSED: Bölümü yukarı / "
                                       "aşağı taşı'")
def test_sablon_move_item_names_a_section(case, windows, tmp_path):
    action_id, key, text = case
    row = {"tab": "sablonlar", "key": key, "action_id": action_id}
    ctx = _start(row, windows, "job_sablon", tmp_path)
    try:
        contract_sablon.ensure_template(ctx)
        contract_sablon.choose(ctx, "Sicil_No", 0)
        press(ctx.win, "Ctrl+D")  # a second box: now a section of several is chosen
        assert contract_sablon._sections(ctx, "Sicil_No") == 2
        item = ctx.win.registry.action(action_id).text().replace("&", "")
        assert item == text, item
    finally:
        _finish(ctx)


@pytest.mark.action("yukle.yeniden_adlandir")
@pytest.mark.xfail(strict=True, reason="M-27: the item reads 'Yeniden adlandır' next to a batch "
                                       "list but F2 renames the JOB; INTENDED 'İşi yeniden "
                                       "adlandır' (existing dialog title; the owner decides)")
def test_yukle_rename_item_names_the_job(windows, tmp_path):
    row = {"tab": "yukle", "key": "F2", "action_id": "yukle.yeniden_adlandir"}
    ctx = _start(row, windows, "job", tmp_path)
    try:
        assert ctx.win.registry.action("yukle.yeniden_adlandir").text().replace("&", "") == \
            "İşi yeniden adlandır"
    finally:
        _finish(ctx)


@pytest.mark.action("kontrol.secimi_kaldir")
def test_kontrol_escape_closes_the_loupe(windows, tmp_path):
    """Esc with the loupe open closes the loupe (not the selection) and focus goes back to the
    timeline."""
    row = {"tab": "kontrol", "key": "Esc", "action_id": "kontrol.secimi_kaldir"}
    ctx = _start(row, windows, "job", tmp_path)
    try:
        contract_kontrol.pick(ctx, [5])
        ctx.undo.append(ctx.win.kontrol.close_loupe)
        press(ctx.win, "Space")
        loupe = ctx.win.kontrol._loupe
        assert loupe is not None and loupe.is_open()
        press(ctx.win, "Esc")
        assert wait_until(lambda: not loupe.isVisible()), "the loupe stayed open"
        assert QApplication.focusWidget() is ctx.win.kontrol.timeline
        assert contract_kontrol.selected(ctx) == [5], "the selection was cleared as well"
    finally:
        _finish(ctx)


@pytest.mark.action("degerler.vazgec")
def test_degerler_escape_closes_the_page_view(windows, tmp_path):
    """Esc with the whole-page view open closes it and leaves the selection as it was."""
    row = {"tab": "degerler", "key": "Esc", "action_id": "degerler.vazgec"}
    ctx = _start(row, windows, "job_degerler", tmp_path)
    try:
        contract_degerler.pick(ctx, 1, 3, rows=(0, 1))
        d = ctx.win.degerler
        ctx.undo.append(lambda: d.loupe is not None and d.loupe.close_loupe())
        press(ctx.win, "Space")
        assert d.loupe is not None and d.loupe.is_open()
        press(ctx.win, "Esc")
        assert wait_until(lambda: not d.loupe.isVisible()), "the page view stayed open"
        assert contract_degerler.selected_rows(ctx) == [0, 1], "the selection was dropped too"
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
