"""Plan 4 fresh-review findings."""


import openpyxl
import pytest
from fakes import make_pdf, qr_page, text_page

from evrakci.pipeline.cuts import compute_documents, record_values
from evrakci.pipeline.exporting import ExportError, export_job
from evrakci.pipeline.naming import build_name
from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.model import Template
from evrakci.pipeline.templates.values import VariableValue


def _value(text):
    return VariableValue(text, 0.95, 0, False)


def _job_with_values(tmp_path, values, pattern, required=("no",)):
    pdf = make_pdf(tmp_path / "in.pdf", [text_page()])
    store = JobStore(tmp_path / "jobs")
    job = store.create_job("İş", [pdf])
    template = Template("abc123", "Rapor")
    for name in values:
        template.add_variable(name, required=name in required)
    template.set_pattern(pattern)
    job.apply_template(job.ordered_page_ids(), template.id)
    [doc] = compute_documents(job)
    record_values(job, doc, template.id,
                  {template.variable(n).key: _value(v) for n, v in values.items()})
    return store, job, {template.id: template}


def test_a_long_folder_never_cuts_a_required_value_silently(tmp_path):
    store, job, templates = _job_with_values(
        tmp_path, {"ad": "a" * 60, "no": "TC12345678901"}, "{ad}_{no}")
    out = tmp_path / ("x" * 150)
    result = export_job(job, store.batch_files(job), templates, out, with_layer=False)
    [item] = result.items
    assert "TC12345678901" not in item.name
    assert any("sığmadı" in c for c in item.checks)


def test_a_shortened_name_is_marked(tmp_path):
    store, job, templates = _job_with_values(
        tmp_path, {"no": "1", "ad": "b" * 90}, "{no}_{ad}")
    out = tmp_path / ("y" * 150)
    result = export_job(job, store.batch_files(job), templates, out, with_layer=False)
    [item] = result.items
    assert item.name.startswith("1_") and any("kısaltıldı" in c for c in item.checks)


def test_cut_check_looks_at_the_required_values_own_place():
    values = {"ad": _value("x12" + "a" * 125), "no": _value("12")}
    name, checks = build_name("{ad}_{no}", values, {"no"})
    assert name is None and any("sığmadı: no" in c for c in checks)


def test_delete_after_export_never_deletes_a_job_that_wrote_nothing(tmp_path, capsys,
                                                                    monkeypatch):
    from evrakci.cli import main
    from evrakci.pipeline.settings import Settings, save_settings

    root = tmp_path / "kok"
    pdf = make_pdf(tmp_path / "t.pdf", [qr_page()])  # only a separator: no documents
    monkeypatch.setenv("EVRAKCI_AYARLAR", str(tmp_path / "ayar.json"))
    save_settings(Settings("disa-aktarinca-sil"), tmp_path / "ayar.json")
    assert main(["--kok", str(root), "is", "olustur", "Boş", str(pdf)]) == 0
    job_id = capsys.readouterr().out.strip().splitlines()[-1]
    assert main(["--kok", str(root), "is", "disa-aktar", job_id, "--cikti",
                 str(tmp_path / "out"), "--metin-katmani-yok"]) == 0
    assert JobStore(root).load(job_id).id == job_id


def test_values_listing_marks_an_emptied_required_value(tmp_path):
    from evrakci.cli.jobs import _check_marks

    store, job, templates = _job_with_values(tmp_path, {"no": ""}, "{no}")
    [doc] = compute_documents(job)
    assert _check_marks(job, doc, templates)


def test_index_is_written_even_when_the_text_layer_fails(tmp_path):
    from evrakci.pipeline.ocr.engine import EngineUnavailable

    store, job, templates = _job_with_values(tmp_path, {"no": "5"}, "{no}")

    class Ok:
        def available(self):
            return None

    def broken(src, dst, tessdata=None, **kwargs):
        raise EngineUnavailable("disk dolu")

    with pytest.raises(ExportError) as error:
        export_job(job, store.batch_files(job), templates, tmp_path / "out", engine=Ok(),
                   add_layer=broken)
    assert (tmp_path / "out" / "index.xlsx").is_file()
    assert "index.xlsx" in str(error.value)


def test_variable_named_like_a_fixed_column_gets_its_own_heading(tmp_path):
    from evrakci.pipeline.export import plan_export
    from evrakci.pipeline.index import write_index

    store, job, templates = _job_with_values(tmp_path, {"Dosya": "x", "no": "1"}, "{no}")
    items = plan_export(job, templates)
    write_index(items, job, tmp_path / "index.xlsx")
    headings = [c.value for c in openpyxl.load_workbook(tmp_path / "index.xlsx").active[1]]
    assert len(headings) == len(set(headings))


def test_a_disk_error_while_writing_says_what_was_written(tmp_path, monkeypatch):
    import evrakci.pipeline.exporting as exporting

    store, job, templates = _job_with_values(tmp_path, {"no": "5"}, "{no}")

    def full(*args, progress=None, **kwargs):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(exporting, "write_documents", full)
    with pytest.raises(ExportError) as error:
        export_job(job, store.batch_files(job), templates, tmp_path / "out", with_layer=False)
    assert "yazılamadı" in str(error.value)
