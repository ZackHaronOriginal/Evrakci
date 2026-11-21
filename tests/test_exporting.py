import shutil

import openpyxl
import pytest
from fakes import make_pdf, qr_page, text_page

from evrakci.pipeline.exporting import ExportError, export_job, may_delete_after_export
from evrakci.pipeline.ocr.engine import EngineUnavailable
from evrakci.pipeline.ocr.textlayer import TextLayerResult
from evrakci.pipeline.store import JobStore


class Ok:
    def available(self):
        return None


class Missing:
    def available(self):
        return "Tesseract programı bulunamadı"


def _job(tmp_path):
    pdf = make_pdf(tmp_path / "in.pdf", [text_page("A"), qr_page(), text_page("B")])
    store = JobStore(tmp_path / "jobs")
    job = store.create_job("İş", [pdf])
    return store, job


def test_export_writes_documents_and_index_with_progress(tmp_path):
    store, job = _job(tmp_path)
    seen = []
    result = export_job(job, store.batch_files(job), {}, tmp_path / "out", with_layer=False,
                        progress=lambda stage, done, total: seen.append((stage, done, total)))
    assert [p.name for p in result.paths] == ["belge_001.pdf", "belge_002.pdf"]
    assert (tmp_path / "out" / "index.xlsx").is_file()
    assert ("write", 2, 2) in seen


def test_layer_results_are_recorded_and_failures_name_what_was_done(tmp_path):
    store, job = _job(tmp_path)
    calls = []

    def flaky(src, dst, tessdata=None, **kwargs):
        calls.append(dst.name)
        if len(calls) == 2:
            raise EngineUnavailable("disk dolu")
        shutil.copy(src, dst)
        return TextLayerResult(dst, False, "PDF/A doğrulanamadı")

    with pytest.raises(ExportError) as error:
        export_job(job, store.batch_files(job), {}, tmp_path / "out", engine=Ok(),
                   add_layer=flaky, tessdata=None)
    assert "belge_002.pdf: disk dolu" in str(error.value) and "belge_001.pdf" in str(error.value)


def test_missing_engine_stops_before_anything_is_written(tmp_path):
    store, job = _job(tmp_path)
    with pytest.raises(EngineUnavailable):
        export_job(job, store.batch_files(job), {}, tmp_path / "out", engine=Missing())
    assert not (tmp_path / "out").exists()


def test_folder_with_an_earlier_export_is_refused(tmp_path):
    store, job = _job(tmp_path)
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "eski.pdf").write_bytes(b"x")
    with pytest.raises(ExportError, match="boş bir klasör"):
        export_job(job, store.batch_files(job), {}, tmp_path / "out", with_layer=False)


def test_pdfa_failure_is_a_note_not_a_check(tmp_path):
    store, job = _job(tmp_path)

    def not_pdfa(src, dst, tessdata=None, **kwargs):
        shutil.copy(src, dst)
        return TextLayerResult(dst, False, "PDF/A doğrulanamadı")

    result = export_job(job, store.batch_files(job), {}, tmp_path / "out", engine=Ok(),
                        add_layer=not_pdfa)
    assert result.items
    for item in result.items:
        assert item.pdfa is False and item.pdfa_note == "PDF/A doğrulanamadı"
        assert not any("PDF/A" in c for c in item.checks)
    assert result.needing_check == 0
    assert may_delete_after_export(result)
    sheet = openpyxl.load_workbook(tmp_path / "out" / "index.xlsx")["Belgeler"]
    assert [row[4].value for row in sheet.iter_rows(min_row=2)] == ["hayır", "hayır"]
    assert [row[5].value for row in sheet.iter_rows(min_row=2)] == ["hayır", "hayır"]
