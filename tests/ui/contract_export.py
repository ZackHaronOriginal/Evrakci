"""Dışa Aktar' and Rehber's rows of the shortcut contract (Phase 3, step 3D): steps and plans,
registered into `contract_helpers.HELPERS` and `contract_helpers.PLANS`.

Nothing is printed and no file manager is opened: the print dialog is replaced by one that
answers at once and sends the page to a PDF file under the test's tmp folder, and the file
manager call is recorded instead of made.
"""
from __future__ import annotations

import re
import time
from pathlib import Path
from unittest import mock

import PySide6.QtPrintSupport as qt_print
from contract_helpers import (
    PLANS,
    Ctx,
    Plan,
    _says,
    heard,
    helper,
    plain,
    said,
    settle,
    wait_until,
)
from PySide6.QtWidgets import QApplication, QDialog

from evrakci.ui import disa_aktar

P_NO_FOLDER = "Gösterilecek bir klasör yok."  
P_NO_INDEX = "Yazdırılacak dizin sayfası yok."
P_NOTHING_RUNNING = "Şu an durdurulacak bir iş yok."  
for _name, _text in (("no_folder", P_NO_FOLDER), ("no_index", P_NO_INDEX),
                     ("export_nothing_running", P_NOTHING_RUNNING)):
    _says(f"export_{_name}", _text)


def _x(c: Ctx):
    return c.win.disa_aktar


def _snap(c: Ctx) -> dict:
    return {"status": c.win.message.text()}


helper("snap.export")(_snap)


class FakePrintDialog:
    """Stands in for QPrintDialog: answers at once, printing to a PDF file; the titles it was
    given are kept in `titles`."""

    target = ""
    titles: list[str] = []

    def __init__(self, printer, parent=None) -> None:
        printer.setOutputFormat(qt_print.QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(FakePrintDialog.target)

    def setWindowTitle(self, title: str) -> None:  # noqa: N802
        FakePrintDialog.titles.append(title)

    def exec(self):
        return QDialog.DialogCode.Accepted


def _fake_printing(c: Ctx, name: str) -> Path:
    target = (c.tmp or Path(".")) / name
    FakePrintDialog.target, FakePrintDialog.titles = str(target), []
    return target


# -- Ctrl+Shift+O --------------------------------------------------------------------------------
@helper("pre.export_reveal")
def _pre_reveal(c: Ctx) -> None:
    d = _x(c)
    shown: list[Path] = []
    patcher = mock.patch.object(disa_aktar, "reveal_path", lambda path: shown.append(Path(path)))
    patcher.start()
    c.undo.append(patcher.stop)
    old = d.folder.text()
    folder = (c.tmp or Path(".")) / "hedef"
    folder.mkdir(exist_ok=True)
    d.folder.setText(str(folder))
    c.undo.append(lambda: d.folder.setText(old))
    c.data["shown"], c.data["folder"] = shown, folder
    d.results.setFocus()
    settle()
    assert c.win.registry.is_enabled("disa_aktar.gezginde_goster")


@helper("effect.export_revealed")
def _effect_revealed(c: Ctx) -> None:
    assert c.data["shown"] == [c.data["folder"]], c.data["shown"]


@helper("feedback.export_revealed")
def _feedback_revealed(c: Ctx) -> None:
    assert len(c.data["shown"]) == 1 and c.data["shown"][0].is_dir()
    assert not c.win.toaster.current_text(), heard(c.win)


# -- Ctrl+P (Dışa Aktar) -------------------------------------------------------------------------
@helper("pre.export_print")
def _pre_export_print(c: Ctx) -> None:
    """I-38: Ctrl+P opens "Baskı önizleme" (the HTML is built in a worker); Yazdır… prints."""
    c.data["pdf"] = _fake_printing(c, "dizin.pdf")
    patcher = mock.patch.object(qt_print, "QPrintDialog", FakePrintDialog)
    patcher.start()
    c.undo.append(patcher.stop)

    def close_preview() -> None:
        preview = _x(c)._preview
        if preview is not None:
            preview.close()
            settle()
    c.undo.append(close_preview)
    _x(c).results.setFocus()
    settle()
    assert _x(c).model.rowCount() > 0


@helper("effect.export_printed")
def _effect_printed(c: Ctx) -> None:
    assert wait_until(lambda: _x(c)._preview is not None), "the print preview did not open"
    assert _x(c)._preview.windowTitle() == "Baskı önizleme"
    assert not c.data["pdf"].exists(), "Ctrl+P must not print before Yazdır…"


@helper("feedback.export_printed")
def _feedback_printed(c: Ctx) -> None:
    preview = _x(c)._preview
    assert preview.print_button.text() == "Yazdır…" and preview.close_button.text() == "Kapat"
    preview.print_button.click()  # Yazdır…: the (stand-in) print dialog, then the pages
    assert c.data["pdf"].is_file() and c.data["pdf"].stat().st_size > 500, "nothing was printed"
    assert FakePrintDialog.titles == ["Dizini yazdır"], FakePrintDialog.titles
    html = _x(c).index_html()
    assert "<th align='left'>Durum</th>" in html and "belge" in html


# -- Ctrl+. (Dışa Aktar) -------------------------------------------------------------------------
@helper("pre.export_running")
def _pre_export_running(c: Ctx) -> None:
    """A real export through the screen's own task, with a writer that takes its time."""
    d = _x(c)

    def slow(job, files, templates, out_dir, with_layer=False, progress=None, **_kw):
        for n in range(100000):
            progress("write", n % 3, 3)
            time.sleep(0.02)

    patcher = mock.patch.object(disa_aktar, "export_job", slow)
    patcher.start()
    c.undo.append(patcher.stop)
    d.layer.setChecked(False)
    out = (c.tmp or Path(".")) / "disa"
    d.folder.setText(str(out))
    d.results.setFocus()
    settle()
    banner: list[str] = []
    original = d.run_banner.sub.setText
    d.run_banner.sub.setText = lambda text: (banner.append(text), original(text))
    c.undo.append(lambda: delattr(d.run_banner.sub, "setText"))
    c.data["banner"], c.data["out"] = banner, out

    def finish() -> None:
        if d.task is not None:
            d.task.cancel()
            wait_until(lambda: d.task is None)

    c.undo.append(finish)
    d.export()
    assert wait_until(lambda: c.win.registry.is_enabled("disa_aktar.durdur")), "no export runs"
    d.results.setFocus()
    settle()


@helper("effect.export_stopped")
def _effect_export_stopped(c: Ctx) -> None:
    d = _x(c)
    assert wait_until(lambda: d.task is None, 15000), "the export was not stopped"
    assert not (c.data["out"] / "index.xlsx").exists(), "index.xlsx was written"


@helper("feedback.export_stopped")
def _feedback_export_stopped(c: Ctx) -> None:
    d = _x(c)
    assert "Durduruluyor; o ana kadar yazılanlar kalır…" in c.data["banner"], c.data["banner"]
    assert d._outcome is not None and d._outcome["kind"] == "stopped"
    assert d._outcome["title"] == "Dışa aktarma durduruldu"
    assert re.fullmatch(r"Dışa aktarma durduruldu: \d+ dosya yazıldı, index\.xlsx yazılmadı\. "
                        r"Yeniden dışa aktarmak için boş bir klasör seçin\.",
                        d._outcome["message"]), d._outcome["message"]


@helper("na.export_stop_says")
def _na_export_stop_says(c: Ctx) -> None:  # INTENDED (M-28, Q-08)
    assert _x(c).task is None
    assert said(c.win, P_NOTHING_RUNNING), f"nothing said: {heard(c.win)!r}"


# -- Rehber: Ctrl+P ------------------------------------------------------------------------------
@helper("pre.rehber_print")
def _pre_rehber_print(c: Ctx) -> None:
    r = c.win.rehber
    c.data["pdf"] = _fake_printing(c, "ayirac.pdf")
    old = r._print_dialog
    r._print_dialog = FakePrintDialog
    c.undo.append(lambda: setattr(r, "_print_dialog", old))
    c.data["sheets"] = r.count.value()


@helper("effect.rehber_printed")
def _effect_rehber_printed(c: Ctx) -> None:
    assert c.data["pdf"].is_file() and c.data["pdf"].stat().st_size > 500, "nothing was printed"


@helper("feedback.rehber_printed")
def _feedback_rehber_printed(c: Ctx) -> None:
    assert FakePrintDialog.titles == ["Ayıraç sayfasını yazdır"], FakePrintDialog.titles
    text = c.win.toaster.current_text()
    assert re.fullmatch(rf"{c.data['sheets']} ayıraç sayfası \(\d+ sayfa\) yazıcıya "
                        r"gönderildi\.", text), text


# -- Rehber: Esc in the search field ---------------------------------------------------------------
@helper("pre.rehber_search_typed")
def _pre_search_typed(c: Ctx) -> None:
    r = c.win.rehber
    r.search.setText("sayfa")
    settle(10)
    assert r._hits, "the demo query has no hits"
    c.undo.append(r.search.clear)
    r.search.setFocus()
    settle()
    assert QApplication.focusWidget() is r.search


@helper("effect.rehber_search_cleared")
def _effect_search_cleared(c: Ctx) -> None:
    r = c.win.rehber
    assert r.search.text() == ""
    settle(10)
    assert not r._hits


@helper("feedback.rehber_search_cleared")
def _feedback_search_cleared(c: Ctx) -> None:
    r = c.win.rehber
    assert re.fullmatch(r"\d+ bölüm, \d+ dakikalık okuma", plain(r.result.text())), r.result.text()
    assert QApplication.focusWidget() is r.search


@helper("broken.rehber_search_empty")
def _broken_search_empty(c: Ctx) -> None:
    r = c.win.rehber
    r.search.clear()
    r.search.setFocus()
    settle(10)
    c.data["result"] = r.result.text()


@helper("na.rehber_quiet")
def _na_rehber_quiet(c: Ctx) -> None:
    """Esc with an empty field: nothing to clear, nothing changes, nothing is said (M-45)."""
    r = c.win.rehber
    assert r.search.text() == "" and r.result.text() == c.data["result"]
    assert c.win.message.text() == c.snap["status"] and not c.win.toaster.current_text()


_M44 = "M-44 Q-08: {why}: the key is disabled and silent; INTENDED status line {text!r}"

PLANS["disa_aktar.gezginde_goster"] = Plan(
    pre="pre.export_reveal", snap="snap.export", effect="effect.export_revealed",
    feedback="feedback.export_revealed", window="job_disa", na_pre="pre.none",
    na="na.says.export_no_folder")
# B-047 (fixed in 3E): print_index used to receive the QAction's checked flag as its printer.
PLANS["disa_aktar.yazdir"] = Plan(
    pre="pre.export_print", snap="snap.export", effect="effect.export_printed",
    feedback="feedback.export_printed", window="job_disa", na_pre="pre.none",
    na="na.says.export_no_index")
PLANS["disa_aktar.durdur"] = Plan(
    pre="pre.export_running", snap="snap.export", effect="effect.export_stopped",
    feedback="feedback.export_stopped", window="fresh", na_pre="pre.none", na_window="job_disa",
    na="na.export_stop_says")
PLANS["rehber.yazdir"] = Plan(
    pre="pre.rehber_print", snap="snap.export", effect="effect.rehber_printed",
    feedback="feedback.rehber_printed", window="job_disa", na_pre="same",
    na="na.same_as_effect")
PLANS["rehber.aramayi_temizle"] = Plan(
    pre="pre.rehber_search_typed", snap="snap.export", effect="effect.rehber_search_cleared",
    feedback="feedback.rehber_search_cleared", window="job_disa", na_pre="pre.none",
    na_window="job_disa", broken="broken.rehber_search_empty", na="na.rehber_quiet")


# -- Ctrl+Shift+C (Dışa Aktar): the name list (I-39) ---------------------------------------------
COPIED_TOAST = "Ad listesi panoya kopyalandı"
SENTINEL = "önceki pano"


@helper("pre.export_copy_list")
def _pre_copy_list(c: Ctx) -> None:
    QApplication.clipboard().setText(SENTINEL)
    _x(c).results.setFocus()
    settle()
    assert _x(c).model.all_rows()


@helper("effect.export_list_copied")
def _effect_list_copied(c: Ctx) -> None:
    lines = QApplication.clipboard().text().split("\n")
    rows = _x(c).model.all_rows()
    assert lines[0] == "Kaynak\tYazılacak dosya adı\tNot", lines[0]
    assert len(lines) == len(rows) + 1, (len(lines), len(rows))
    assert all(line.count("\t") == 2 for line in lines), lines


@helper("feedback.export_list_copied")
def _feedback_list_copied(c: Ctx) -> None:
    assert said(c.win, COPIED_TOAST), f"nothing said: {heard(c.win)!r}"


@helper("broken.export_clipboard_sentinel")
def _broken_clipboard(c: Ctx) -> None:
    QApplication.clipboard().setText(SENTINEL)


@helper("na.export_list_not_copied")
def _na_list_not_copied(c: Ctx) -> None:
    assert QApplication.clipboard().text() == SENTINEL, "the empty list was copied"


PLANS["disa_aktar.liste_kopyala"] = Plan(
    pre="pre.export_copy_list", snap="snap.export", effect="effect.export_list_copied",
    feedback="feedback.export_list_copied", window="job_disa", na_pre="pre.none",
    broken="broken.export_clipboard_sentinel", na="na.export_list_not_copied")
