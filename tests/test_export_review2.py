"""Plan 4 second fresh review (2026-11-09): every finding, red first."""

import shutil

import pytest
from fakes import a4_300, job_from_kinds, make_pdf

from evrakci.cli import main
from evrakci.pipeline.cuts import compute_documents, current_values, record_values
from evrakci.pipeline.export import plan_export
from evrakci.pipeline.exporting import (
    ExportError,
    ExportResult,
    export_job,
    may_delete_after_export,
)
from evrakci.pipeline.naming import build_name_kept, fit_names, safe_filename
from evrakci.pipeline.review import accept_suggestion, revert_value, set_value
from evrakci.pipeline.settings import Settings, SettingsError, load_settings
from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.model import Section, Template
from evrakci.pipeline.templates.values import VariableValue


def ok(text):
    return VariableValue(text, 0.95, 0, False)


# --- 2: forbidden characters in the pattern's own text ---------------------------------------

@pytest.mark.parametrize("pattern,expected", [
    ("Fatura: {No}", "Fatura 123"),
    ('{A} "x" {No}', "aa x 123"),
    ("  {No}", "123"),
    ("Fatura   {No}", "Fatura 123"),
])
def test_forbidden_text_in_the_pattern_keeps_the_real_name(pattern, expected):
    values = {"No": ok("123"), "A": ok("aa")}
    name, checks, keep = build_name_kept(pattern, values, {"No"})
    assert name == expected and not checks
    assert name[:keep].endswith("123")


# --- 3: reserved device names, also with a dot or a space ---------------------------------

@pytest.mark.parametrize("text,expected", [
    ("Aux.Ltd", "Aux_.Ltd"),
    ("nul.tar", "nul_.tar"),
    ("CON .x", "CON_.x"),
    ("con", "con_"),
    ("COM1.belge", "COM1_.belge"),
    ("Konya.Ltd", "Konya.Ltd"),
])
def test_reserved_names_are_made_safe_before_the_first_dot(text, expected):
    assert safe_filename(text) == expected


def test_reserved_name_from_a_pattern_keeps_required_spans():
    name, checks, keep = build_name_kept("{A}.{No}", {"A": ok("aux"), "No": ok("55")}, {"No"})
    assert name == "aux_.55" and not checks and name[:keep] == "aux_.55"


# --- 8: names cut to the length limit are marked; optional values give way first ----------

def test_an_optional_value_cut_at_the_length_limit_is_marked():
    values = {"No": ok("101"), "Aciklama": ok("x" * 200)}
    name, checks, _ = build_name_kept("{No}_{Aciklama}", values, {"No"})
    assert name.startswith("101_") and len(name) == 120
    assert "dosya adı kısaltıldı" in checks


def test_a_long_optional_value_before_a_required_one_is_shortened_instead():
    values = {"No": ok("101"), "Aciklama": ok("x" * 200)}
    name, checks, keep = build_name_kept("{Aciklama}_{No}", values, {"No"})
    assert name is not None and name.endswith("_101") and len(name) <= 120
    assert "dosya adı kısaltıldı" in checks and name[:keep].endswith("101")


# --- 17: numbering and path length --------------------------------------------------------

def test_a_read_value_never_takes_another_documents_number():
    template = Template("t1", "T")
    no = template.add_variable("No")
    template.add_section("No", Section(1, (1, 1, 5, 5)))
    template.set_pattern("{No}")
    job = job_from_kinds({"a": "ppp"})
    job.apply_filter(job.ordered_page_ids(), 1)
    job.apply_template(["a/0"], "t1")
    docs = compute_documents(job)
    record_values(job, docs[0], "t1", {no.key: ok("belge_002")})
    names = [i.name for i in plan_export(job, {"t1": template})]
    assert names[1] == "belge_002" and names[0] == "belge_002 (2)"


def test_path_budget_counts_utf16_units(tmp_path):
    long = "😀" * 60  # 2 UTF-16 units each on Windows
    (fitted,) = fit_names([long], tmp_path)
    budget = 250 - len(str(tmp_path.resolve())) - len(" (999).pdf.gecici") - 1
    assert len(fitted.encode("utf-16-le")) // 2 <= budget


# --- 9, 16, 18: values -------------------------------------------------------------------

@pytest.fixture
def one_document():
    job = job_from_kinds({"a": "p"})
    job.apply_template(["a/0"], "t1")
    document = compute_documents(job)[0]
    record_values(job, document, "t1", {"k": VariableValue("", 0.2, None, True,
                                                           "  Örnek   A.Ş. ", (), False)})
    return job, document


def test_a_variable_added_after_reading_can_be_set(one_document):
    job, document = one_document
    set_value(job, document, "yeni", "Değer")
    assert current_values(job, document)["yeni"].value == "Değer"


def test_accepted_suggestions_are_normalised(one_document):
    job, document = one_document
    accept_suggestion(job, document, "k")
    assert current_values(job, document)["k"].value == "Örnek A.Ş."


def test_a_correction_can_be_undone(one_document):
    job, document = one_document
    set_value(job, document, "k", "")
    revert_value(job, document, "k")
    value = current_values(job, document)["k"]
    assert not value.edited and value.flagged and value.suggestion == "  Örnek   A.Ş. "


# --- 5: job ids --------------------------------------------------------------------------

def test_a_copied_job_folder_is_its_own_job(tmp_path):
    store = JobStore(tmp_path)
    scan = make_pdf(tmp_path / "t.pdf", [a4_300([])], dpi=72)
    job = store.create_job("İş", [scan])
    shutil.copytree(tmp_path / job.id, tmp_path / "kopya")
    copy = store.load("kopya")
    assert copy.id == "kopya"
    store.delete(copy.id)
    assert (tmp_path / job.id / "job.json").is_file()
    assert not (tmp_path / "kopya").exists()


@pytest.mark.parametrize("bad", ["..", ".", "a/b", "/etc", "a\\b", ""])
def test_job_ids_must_be_plain_folder_names(tmp_path, bad):
    store = JobStore(tmp_path / "isler")
    (tmp_path / "job.json").write_text("{}")
    with pytest.raises(KeyError):
        store.delete(bad)
    with pytest.raises(KeyError):
        store.load(bad)
    assert (tmp_path / "job.json").exists()


# --- 6, 7: settings ------------------------------------------------------------------------

@pytest.mark.parametrize("content", ["[]", '"x"', "3", '{"saklama": 5}'])
def test_a_settings_file_that_is_not_an_object_is_reported(tmp_path, content):
    path = tmp_path / "settings.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(SettingsError):
        load_settings(path)


@pytest.mark.parametrize("value", ["³", "١٢", "0", "-1", " 5"])
def test_odd_digits_are_refused(value):
    with pytest.raises(SettingsError):
        Settings(value)


# --- 4, 15: CLI ---------------------------------------------------------------------------

def run(tmp_path, *args):
    return main(["--kok", str(tmp_path / "isler"), "--sablon-kok", str(tmp_path / "s"), *args])


@pytest.fixture
def templated_job(tmp_path, capsys):
    from evrakci.pipeline.templates.store import TemplateStore

    template = TemplateStore(tmp_path / "s").create("Rapor")
    template.add_variable("No", required=True)
    template.add_section("No", Section(1, (1, 1, 5, 5)))
    template.set_pattern("{No}")
    TemplateStore(tmp_path / "s").save(template)
    scan = make_pdf(tmp_path / "t.pdf", [a4_300([]), a4_300([])], dpi=72)
    run(tmp_path, "is", "olustur", "İş", str(scan))
    job_id = capsys.readouterr().out.strip().splitlines()[-1]
    gone = TemplateStore(tmp_path / "s").create("Silinecek")
    run(tmp_path, "is", "kes", job_id, "2")
    run(tmp_path, "is", "sablon-uygula", job_id, "1-1", template.id)
    run(tmp_path, "is", "sablon-uygula", job_id, "2-2", gone.id)
    TemplateStore(tmp_path / "s").delete(gone.id)  # its template is gone
    capsys.readouterr()
    return job_id


def test_kontrol_lists_what_export_would_mark(tmp_path, capsys, templated_job):
    assert run(tmp_path, "is", "degerler", templated_job, "--kontrol") == 0
    out = capsys.readouterr().out
    assert "1. belge" in out and "2. belge" in out
    assert run(tmp_path, "is", "goster", templated_job) == 0
    out = capsys.readouterr().out
    assert "değerler okunmadı" in out and "şablon bulunamadı" in out


def test_value_and_suggestion_together_are_refused(tmp_path, capsys, templated_job):
    assert run(tmp_path, "is", "deger", templated_job, "1", "No", "5", "--oneri") == 2
    assert "--oneri" in capsys.readouterr().err


# --- 11, 12, 13: writing --------------------------------------------------------------------

def plain_job(tmp_path):
    store = JobStore(tmp_path / "isler")
    scan = make_pdf(tmp_path / "t.pdf", [a4_300([]), a4_300([])], dpi=72)
    job = store.create_job("İş", [scan])
    return store, job


def test_an_earlier_export_with_other_letter_case_is_seen(tmp_path):
    store, job = plain_job(tmp_path)
    out = tmp_path / "cikti"
    out.mkdir()
    (out / "Eski.PDF").write_bytes(b"%PDF")
    with pytest.raises(ExportError, match="önceki"):
        export_job(job, store.batch_files(job), {}, out, with_layer=False)
    (out / "Eski.PDF").unlink()
    (out / "INDEX.XLSX").write_bytes(b"x")
    with pytest.raises(ExportError, match="önceki"):
        export_job(job, store.batch_files(job), {}, out, with_layer=False)


def test_an_output_path_that_is_a_file_is_explained(tmp_path):
    store, job = plain_job(tmp_path)
    out = tmp_path / "dosya"
    out.write_text("x")
    with pytest.raises(ExportError, match="klasör değil"):
        export_job(job, store.batch_files(job), {}, out, with_layer=False)


def test_a_damaged_batch_file_is_an_export_error(tmp_path):
    store, job = plain_job(tmp_path)
    files = store.batch_files(job)
    path = next(iter(files.values()))
    path.write_bytes(b"bozuk")
    with pytest.raises(ExportError, match="Yazılanlar"):
        export_job(job, files, {}, tmp_path / "cikti", with_layer=False)


def test_delete_after_export_only_with_the_text_layer(tmp_path):
    store, job = plain_job(tmp_path)
    result = export_job(job, store.batch_files(job), {}, tmp_path / "cikti", with_layer=False)
    assert result.index_written and not result.needing_check
    assert not may_delete_after_export(result)
    full = ExportResult(result.items, result.paths, index_written=True, with_layer=True)
    assert may_delete_after_export(full)
