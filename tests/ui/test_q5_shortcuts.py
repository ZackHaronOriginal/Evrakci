"""Q5 (Q-08 shortcut fixes): the labels and routes the contract rows do not show.

Ctrl+F reads "Belgeye veya sayfaya git…" on Kontrol, Ctrl+G picks a document or a page on
Şablonlar and Dışa Aktar, and Değerler' keys with a job open but nothing chosen say what to pick.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtTest import QTest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import screenshots  # noqa: E402
from contract_helpers import Ctx, on_modal, press, reset, settle  # noqa: E402

from evrakci.ui import refusals  # noqa: E402


@pytest.fixture(scope="module")
def win(qapp, tmp_path_factory):
    patch = pytest.MonkeyPatch()
    patch.setenv("EVRAKCI_UI_AYARLAR", str(tmp_path_factory.mktemp("ui") / "ui-ayarlar.ini"))
    window = screenshots.build(tmp_path_factory.mktemp("demo"))
    window.resize(1366, 768)
    window.show()
    window.activateWindow()
    assert QTest.qWaitForWindowActive(window)
    settle()
    yield window
    window.thumbnails.stop()
    window.close()
    window.deleteLater()
    settle()
    patch.undo()


def _answer(win, kind: str, number: int) -> Ctx:
    ctx = Ctx(win, win.current_tab(), "Ctrl+G", "app.git")

    def fill(dialog) -> None:
        (dialog.page if kind == "sayfa" else dialog.document).setChecked(True)
        dialog.number.setValue(number)
        dialog.accept()

    on_modal(ctx, fill)
    return ctx


def test_b026_ctrl_f_on_kontrol_is_labelled_for_what_it_does(win):
    find = win.registry.action("app.bul")
    reset(win, "kontrol")
    assert find.text().replace("&", "") == "Belgeye veya sayfaya git…"
    assert "Belgeye veya sayfaya git" in find.toolTip() and "Ctrl+F" in find.toolTip()
    reset(win, "degerler")
    assert find.text().replace("&", "") == "Bul…"


def test_ctrl_g_on_sablonlar_with_a_page_number_picks_the_example_holding_it(win):
    reset(win, "sablonlar")
    docs = win.sablon._documents()
    job = win.controller().job
    first, last = (job.position_of(docs[2].page_ids[0]), job.position_of(docs[2].page_ids[-1]))
    ctx = _answer(win, "sayfa", last)
    try:
        press(win, "Ctrl+G")
    finally:
        for undo in ctx.undo:
            undo()
    assert first <= last and win.sablon.example == 3
    assert "3" in win.sablon.examples.currentText()


def test_ctrl_g_on_disa_aktar_with_a_page_number_chooses_the_file_holding_it(win):
    reset(win, "disa_aktar")
    screen = win.disa_aktar
    row = screen.model.all_rows()[0]  # the list is sorted by name: any row will do
    page = int(row.pages.partition("–")[0])
    ctx = _answer(win, "sayfa", page)
    try:
        press(win, "Ctrl+G")
    finally:
        for undo in ctx.undo:
            undo()
    chosen = screen.model.row_at(screen.results.currentIndex().row())
    assert chosen.number == row.number


def test_degerler_keys_with_a_job_but_nothing_chosen_say_what_to_pick(win):
    reset(win, "degerler")
    screen = win.degerler
    screen.table.clearSelection()
    screen.table.setCurrentIndex(QModelIndex())
    screen._sync_actions()
    settle()
    win.title_tabs.setFocus(Qt.FocusReason.TabFocusReason)
    cases = (("Return", "degerler.onayla", "Önce bir değer seçin."),
             ("Shift+Return", "degerler.okunanla_onayla", "Önce bir değer seçin."),
             ("Ctrl+Return", "degerler.secilenleri_onayla", "Önce satırları seçin."),
             ("F2", "degerler.elle_yaz", "Önce bir değer seçin."),
             ("Space", "degerler.tum_sayfa", "Önce bir değer seçin."),
             ("V", "degerler.varyant", "Önce şablonu olan bir belge seçin."))
    for key, action_id, text in cases:
        win.message.setText("")
        assert not win.registry.is_enabled(action_id), action_id
        assert win.registry.action(action_id).toolTip() == text
        press(win, key)
        assert win.message.text() == text, (key, win.message.text())


def test_ctrl_g_with_a_page_no_file_row_holds_says_so_on_disa_aktar(win, monkeypatch):
    reset(win, "disa_aktar")
    screen = win.disa_aktar
    rows = screen.model.all_rows()
    monkeypatch.setattr(screen.model, "all_rows", lambda: rows[:1])
    page = 1 + max(int(r.pages.partition("–")[2] or r.pages) for r in rows)
    page = min(page, len(win.controller().job.ordered_page_ids()))
    ctx = _answer(win, "sayfa", page)
    win.message.setText("")
    try:
        press(win, "Ctrl+G")
    finally:
        for undo in ctx.undo:
            undo()
    assert win.message.text() == f"Sayfa {page} bu görünümde yok."


def test_ctrl_g_with_a_page_no_example_holds_says_so_on_sablonlar(win, monkeypatch):
    reset(win, "sablonlar")
    docs = win.sablon._documents()
    monkeypatch.setattr(win.sablon, "_documents", lambda: docs[:1])
    page = len(win.controller().job.ordered_page_ids())
    ctx = _answer(win, "sayfa", page)
    win.sablon.message.setText("")
    try:
        press(win, "Ctrl+G")
    finally:
        for undo in ctx.undo:
            undo()
    assert win.sablon.message.text() == f"Sayfa {page} bu görünümde yok."


def test_reasons_are_the_approved_wording():
    assert refusals.NO_HITS == "Sonuç yok."
    assert refusals.NO_CORRECTED_VALUE == "Düzeltilmiş bir değer yok."
    assert refusals.NO_DOCUMENT == "Gidilecek bir belge yok."
    assert refusals.NO_VARIABLE_TO_FIND == "Aranacak değişken yok."


def test_button_tooltips_follow_the_reason_when_the_state_it_reads_changes(win, monkeypatch):
    """A read is running (reason 'Okuma sürüyor.'); it ends and no document has a template: the
    button stays greyed all along, yet its tooltip moves to the new reason."""
    reset(win, "degerler")
    screen = win.degerler
    button = win.command_bar("degerler").button_for("degerler.oku")
    monkeypatch.setattr(screen, "task", object())
    screen._sync_actions()
    assert not button.isEnabled() and button.toolTip() == "Okuma sürüyor."
    monkeypatch.setattr(screen, "task", None)
    monkeypatch.setattr(screen, "rows", [])
    screen._sync_actions()
    assert not button.isEnabled()
    assert button.toolTip() == "Okunacak, şablonu olan bir belge yok."
    monkeypatch.undo()
    screen._sync_actions()
