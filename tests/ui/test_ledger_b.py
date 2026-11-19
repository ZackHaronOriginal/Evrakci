"""Repro tests for ledger rows B-001 to B-009 (Yükle, Dışa Aktar, Rehber).

Each test asserts the EXPECTED behaviour and is an xfail(strict=True): when a bug is fixed the
test XPASSes, the suite goes red, and the fixer removes the marker.
"""
from __future__ import annotations

import ast
import dataclasses
import os
import shutil
import threading
import time
from pathlib import Path

import pikepdf
import pytest
from fakes import make_pdf, qr_page, text_page
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import QFileDialog, QLabel

from evrakci.pipeline.exporting import export_job
from evrakci.pipeline.ocr.textlayer import TextLayerResult
from evrakci.pipeline.settings import DELETE_AFTER_EXPORT, Settings, save_settings
from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.ui import actions
from evrakci.ui import disa_aktar as disa_aktar_module
from evrakci.ui import rehber_print as printing
from evrakci.ui.disa_aktar_model import file_rows
from evrakci.ui.main_window import MainWindow
from evrakci.ui.prefs import Prefs
from evrakci.ui.yukle import YukleScreen


@pytest.fixture
def pdfs(tmp_path):
    (tmp_path / "in").mkdir()
    a = make_pdf(tmp_path / "in" / "tarama-1.pdf", [text_page("A"), qr_page(), text_page("B")])
    b = make_pdf(tmp_path / "in" / "tarama-2.pdf", [text_page("C"), text_page("D")])
    c = make_pdf(tmp_path / "in" / "tarama-3.pdf", [text_page("E"), text_page("F")])
    return [a, b, c]


def _window(qtbot, tmp_path) -> MainWindow:
    window = MainWindow(JobStore(tmp_path / "jobs"), TemplateStore(tmp_path / "tpl"),
                        settings_path=tmp_path / "ayar.json", prefs=Prefs(tmp_path / "p.ini"))
    qtbot.addWidget(window)
    window.show()
    qtbot.waitUntil(lambda: window.yukle.window_ is window, timeout=3000)
    return window


# B-001 / F-yukle-17 fixed: choose_batch goes through add_paths, which queues during a read
def test_b001_choosing_files_while_a_read_runs_queues_them_or_says_why(qtbot, tmp_path, pdfs,
                                                                      monkeypatch):
    window = _window(qtbot, tmp_path)
    screen = window.yukle
    screen.open_job(window.store.load(window.store.create_job("İş", pdfs[:1]).id))
    gate = threading.Event()
    real = window.store.prepare_batch

    def held(job, path, progress=None):
        gate.wait(5)
        return real(job, path, progress)

    monkeypatch.setattr(window.store, "prepare_batch", held)
    monkeypatch.setattr(QFileDialog, "getOpenFileNames",
                        staticmethod(lambda *a, **k: ([str(pdfs[2])], "")))
    seen = {}
    try:
        with qtbot.waitSignal(screen.task_finished, timeout=20000):
            screen.add_paths([pdfs[1]])  # a read is now running
            assert screen.busy()
            before = screen.last_message
            screen.choose_batch()  # Ctrl+O: the dialog returns a file
            seen["queued"] = list(screen._queued)
            seen["message"] = screen.last_message != before
            gate.set()
        assert seen["queued"] or seen["message"]
        qtbot.waitUntil(lambda: not screen.busy(), timeout=60000)  # the queued file is read next
    finally:  # never leave a read running: the window's close question would block the teardown
        gate.set()
        screen._queued.clear()
        if screen.busy():
            screen.cancel()
        qtbot.waitUntil(lambda: not screen.busy(), timeout=60000)


@pytest.mark.xfail(strict=True, reason="B-002: a batch split by a filter is still 'Kontrol' "
                   "(no QR) while the inspector says Hazır (yukle_info.py summarize)")
def test_b002_batch_status_and_inspector_agree_after_a_filter_split(qtbot, tmp_path):
    pdf = make_pdf(tmp_path / "t.pdf", [text_page(c) for c in "ABCD"])
    screen = YukleScreen(JobStore(tmp_path / "s"))
    qtbot.addWidget(screen)
    screen.open_job(screen.store.load(screen.store.create_job("İş", [pdf]).id))
    controller = screen.controller
    batch = controller.job.batches[0]
    assert controller.apply_filter([f"{batch.id}/{i}" for i in range(4)], 2)
    screen._show_batches()
    assert len(controller.documents()) == 2
    assert screen.side.state_row.value.text() == "Hazır"
    assert screen._info.batches[0].status == "hazir"


class _Ok:
    def available(self):
        return None


@pytest.mark.xfail(strict=True, reason="B-003: 'PDF/A değil' is Bilgi in the list but counted as "
                   "a check by ExportResult.needing_check, the outcome card, index and deletion")
def test_b003_pdfa_failure_is_one_rule_in_list_and_outcome_count(tmp_path):
    pdf = make_pdf(tmp_path / "in.pdf", [text_page("A"), qr_page(), text_page("B")])
    store = JobStore(tmp_path / "jobs")
    job = store.create_job("İş", [pdf])

    def not_pdfa(src, dst, tessdata=None, **kwargs):
        shutil.copy(src, dst)
        return TextLayerResult(dst, False, "PDF/A doğrulanamadı")

    result = export_job(job, store.batch_files(job), {}, tmp_path / "out", engine=_Ok(),
                        add_layer=not_pdfa)
    rows = file_rows(job, result.items)
    assert any(r.why == "PDF/A değil" for r in rows)
    assert result.needing_check == sum(1 for r in rows if r.state == "kontrol")


@pytest.mark.xfail(strict=True, reason="B-005: 'Dışa aktarılan iş ... saklansın' but the day "
                   "limit also deletes never-exported jobs (store.delete_older_than)")
def test_b005_day_limit_keeps_a_job_that_was_never_exported(qtbot, tmp_path):
    from evrakci.app import build_window

    pdf = make_pdf(tmp_path / "t.pdf", [text_page()])
    store = JobStore(tmp_path / "jobs")
    old = store.create_job("Hiç dışa aktarılmadı", [pdf])
    stamp = time.time() - 40 * 86400
    os.utime(tmp_path / "jobs" / old.id / "job.json", (stamp, stamp))
    save_settings(Settings("30"), tmp_path / "ayar.json")
    window = build_window(tmp_path / "jobs", tmp_path / "tpl", tmp_path / "ayar.json")
    qtbot.addWidget(window)
    assert [j.id for j in JobStore(tmp_path / "jobs").list_jobs()] == [old.id]


@pytest.mark.xfail(strict=True, reason="B-006: the guide promises a job setting for blank "
                   "pages but no window action sets drop_empty (only the CLI does)")
def test_b006_a_window_command_exists_for_dropping_blank_pages():
    found = [s.id for s in actions.SPECS
             if "boş" in (s.text + " ".join(s.keywords) + s.tooltip).casefold()]
    assert found


@pytest.mark.xfail(strict=True, reason="B-007: 'Kaç adet ... sayfa' counts sheets but prints "
                   "twice as many pages (rehber_print.print_separators)")
def test_b007_the_count_unit_matches_what_is_printed(qtbot, tmp_path):
    from evrakci.ui.rehber import RehberScreen

    screen = RehberScreen()
    qtbot.addWidget(screen)
    screen.show()
    screen.count.setValue(3)
    printer = QPrinter()
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(str(tmp_path / "ayirac.pdf"))
    printing.print_separators(printer, screen.count.value())
    with pikepdf.open(tmp_path / "ayirac.pdf") as out:
        pages = len(out.pages)
    unit = {lab.text() for lab in screen.count.parentWidget().findChildren(QLabel)}
    assert "sayfa" not in unit or pages == screen.count.value()


def test_b008_the_open_job_closes_when_the_export_deleted_it(qtbot, tmp_path, pdfs, monkeypatch):
    window = _window(qtbot, tmp_path)
    job = window.store.create_job("İş", pdfs[:1])
    save_settings(Settings(DELETE_AFTER_EXPORT), tmp_path / "ayar.json")
    window.yukle.open_job(window.store.load(job.id))
    window.show_tab("disa_aktar")
    screen = window.disa_aktar
    real = disa_aktar_module.export_job
    monkeypatch.setattr(disa_aktar_module, "export_job", lambda *a, **k: dataclasses.replace(
        real(*a, **k), with_layer=True))  # as if the text layer was added: a full export
    screen.folder.setText(str(tmp_path / "out"))
    screen.layer.setChecked(False)
    with qtbot.waitSignal(screen.finished, timeout=30000):
        screen.export_button.click()
    assert job.id not in {j.id for j in window.store.list_jobs()}  # it really was deleted
    assert window.controller() is None


def _runs_an_export(func: ast.FunctionDef, source: str) -> bool:
    text = ast.get_source_segment(source, func) or ""
    return ".finished" in text and ("export_button.click()" in text or ".export()" in text)


@pytest.mark.xfail(strict=True, reason="B-009: every window export test unchecks the text-layer "
                   "box, so the default (OCR on) window path has no test")
def test_b009_some_window_export_test_keeps_the_default_text_layer():
    here = Path(__file__).parent
    default_path_tests = []
    for path in sorted(here.glob("test_*.py")):
        if path.name == Path(__file__).name:
            continue
        source = path.read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_") \
                    and _runs_an_export(node, source):
                text = ast.get_source_segment(source, node) or ""
                if "layer.setChecked(False)" not in text:
                    default_path_tests.append(f"{path.name}::{node.name}")
    assert default_path_tests
