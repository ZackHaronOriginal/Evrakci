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
    # the files and index.xlsx are on disk: the job records that, with the sheet's time
    from datetime import datetime

    from evrakci.pipeline.index import format_time

    assert job.last_export is not None and job.last_export.documents == 2
    from evrakci.pipeline.job import job_state

    assert job.last_export.state == job_state(job)  # Q-27: what the printed subtitle compares
    summary = openpyxl.load_workbook(tmp_path / "out" / "index.xlsx")["Özet"]
    cells = {row[0].value: row[1].value for row in summary.iter_rows()}
    assert cells["Dışa aktarma zamanı"] == format_time(
        datetime.fromisoformat(job.last_export.at))


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
    assert [row[5].value for row in sheet.iter_rows(min_row=2)] == ["hayır", "hayır"]
    assert [row[6].value for row in sheet.iter_rows(min_row=2)] == ["hayır", "hayır"]


def test_one_time_goes_to_the_sheet_and_the_job(tmp_path):
    from datetime import datetime

    store, job = _job(tmp_path)
    result = export_job(job, store.batch_files(job), {}, tmp_path / "out", with_layer=False)
    assert job.last_export is not None
    assert job.last_export.documents == len(result.items)
    assert job.last_export.needing_check == result.needing_check
    assert job.last_export.folder == str(tmp_path / "out")
    moment = datetime.fromisoformat(job.last_export.at)
    book = openpyxl.load_workbook(tmp_path / "out" / "index.xlsx")
    summary = {r[0].value: r[1].value for r in book["Özet"].iter_rows()}
    assert summary["Dışa aktarma zamanı"] == moment.strftime("%d.%m.%Y %H:%M")
    assert summary["İş adı"] == "İş"
    assert summary["Belge sayısı"] == str(len(result.items))


def test_check_sheet_rows_equal_needing_check_with_a_pdfa_failure(tmp_path):
    store, job = _job(tmp_path)

    def not_pdfa(src, dst, tessdata=None, **kwargs):
        shutil.copy(src, dst)
        return TextLayerResult(dst, False, "PDF/A doğrulanamadı")

    result = export_job(job, store.batch_files(job), {}, tmp_path / "out", engine=Ok(),
                        add_layer=not_pdfa)
    sheet = openpyxl.load_workbook(tmp_path / "out" / "index.xlsx")["Kontrol gerekenler"]
    rows = [[c.value for c in row] for row in sheet.iter_rows(min_row=2)]
    assert result.needing_check == 0
    assert rows == [["Kontrol gerektiren belge yok.", None, None, None]]


def _named_job(tmp_path):
    """Three documents with a template: two share a long name, one has a forbidden character."""
    from evrakci.pipeline.cuts import compute_documents, record_values
    from evrakci.pipeline.templates.model import Template
    from evrakci.pipeline.templates.values import VariableValue

    pdf = make_pdf(tmp_path / "in.pdf", [text_page("A"), qr_page(), text_page("B"), qr_page(),
                                         text_page("C")])
    store = JobStore(tmp_path / "jobs")
    job = store.create_job("İş", [pdf])
    template = Template(id="t1", name="Deneme")
    no = template.add_variable("Kayıt No")
    name = template.add_variable("Ünvan")
    template.set_pattern("{Kayıt No}_{Ünvan}")
    job.apply_template(job.ordered_page_ids(), "t1")
    texts = ["Ü" * 60, "Ü" * 60, "A/B"]
    for document, text in zip(compute_documents(job), texts, strict=True):
        record_values(job, document, "t1", {no.key: VariableValue("1", 0.9, 0, False),
                                            name.key: VariableValue(text, 0.9, 0, False)})
    return store, job, {"t1": template}


def test_plan_names_equals_the_names_export_job_writes(tmp_path):
    from evrakci.pipeline.exporting import plan_names

    store, job, templates = _named_job(tmp_path)
    from evrakci.pipeline import naming

    # a long folder path that still leaves 40 units for a name (the temp folder itself is
    # much deeper on Windows): the names are cut, then clash
    room = naming.PATH_LIMIT - len(str(tmp_path.resolve())) - len(naming._LONGEST_SUFFIX) - 2
    out = tmp_path / ("d" * (room - 40))
    planned = plan_names(job, templates, out)
    result = export_job(job, store.batch_files(job), templates, out, with_layer=False)
    assert [f"{i.name}.pdf" for i in planned] == [p.name for p in result.paths]
    assert [i.name_note for i in planned] == [i.name_note for i in result.items]
    assert planned[0].name_note == "Dosya adı kısaltıldı (klasör yolu uzun)"
    assert planned[1].name_note.startswith("Ad çakışması")
    assert len({p.name for p in result.paths}) == 3
