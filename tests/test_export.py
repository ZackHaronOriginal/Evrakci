from fakes import job_from_kinds

from evrakci.pipeline.cuts import compute_documents, record_values
from evrakci.pipeline.export import plan_export
from evrakci.pipeline.templates.model import Template
from evrakci.pipeline.templates.values import VariableValue


def ok(text):
    return VariableValue(text, 0.9, 0, False)


def unsure(suggestion=""):
    return VariableValue("", 0.0, None, True, suggestion)


def make_template():
    t = Template(id="t1", name="Deneme")
    t.add_variable("Kayıt No", required=True)
    t.add_variable("Ünvan")
    t.add_variable("Not")
    t.set_pattern("{Kayıt No}_{Ünvan}")
    return t


def test_plan_names_and_checks():
    t = make_template()
    k_no, k_unvan, k_not = (v.key for v in t.variables)
    job = job_from_kinds({"a": "pppppp"})
    job.apply_template(["a/0", "a/1", "a/2", "a/3"], "t1")
    job.apply_filter(job.ordered_page_ids(), 1)
    docs = compute_documents(job)
    record_values(job, docs[0], "t1", {k_no: ok("101"), k_unvan: ok("Örnek"), k_not: unsure()})
    record_values(job, docs[1], "t1", {k_no: unsure("102"), k_unvan: ok("Başka")})
    record_values(job, docs[2], "t1", {k_no: ok("101"), k_unvan: ok("örnek")})  # clash
    record_values(job, docs[3], "t1", {k_no: ok("103"), k_unvan: unsure()})
    items = plan_export(job, {"t1": t})
    assert [i.name for i in items] == [
        "101_Örnek",
        "belge_002",
        "101_örnek (2)",
        "103",
        "belge_005",
        "belge_006",
    ]
    assert items[0].checks == ["okunamadı: Not"]
    assert items[1].checks == ["zorunlu değer eksik: Kayıt No"]
    assert items[3].checks == ["okunamadı: Ünvan"]
    assert items[4].checks == [] and items[4].template_name is None
    assert items[0].values == {"Kayıt No": "101", "Ünvan": "Örnek", "Not": ""}


def test_plan_template_missing_and_unread():
    job = job_from_kinds({"a": "pp"})
    job.apply_template(["a/0"], "gone")
    job.apply_template(["a/1"], "t1")
    job.apply_filter(job.ordered_page_ids(), 1)
    first, second = plan_export(job, {"gone": None, "t1": make_template()})
    assert first.name == "belge_001" and first.checks == ["şablon bulunamadı"]
    assert second.name == "belge_002" and second.checks == ["değerler okunmadı"]


def test_leftover_mixed_and_read_error_reported():
    job = job_from_kinds({"a": "ppp"})
    job.apply_template(["a/0"], "t1")
    job.apply_template(["a/1", "a/2"], "t2")
    from evrakci.pipeline.cuts import record_read_error

    [doc] = compute_documents(job)
    record_read_error(job, doc, "t1", "Tesseract hata verdi")
    [item] = plan_export(job, {"t1": make_template(), "t2": make_template()})
    assert "karışık şablon" in item.checks and "Tesseract hata verdi" in item.checks


def test_empty_pattern_and_empty_name_are_marked():
    t = make_template()
    t.set_pattern("")
    job = job_from_kinds({"a": "p"})
    job.apply_template(["a/0"], "t1")
    [doc] = compute_documents(job)
    k_no, k_unvan, k_not = (v.key for v in t.variables)
    record_values(job, doc, "t1", {k_no: ok("1"), k_unvan: ok("x"), k_not: ok("y")})
    [item] = plan_export(job, {"t1": t})
    assert item.name == "belge_001" and "dosya adı kalıbı yok" in item.checks


def test_read_error_follows_its_document():
    job = job_from_kinds({"a": "pp"})
    job.apply_template(["a/0", "a/1"], "t1")
    from evrakci.pipeline.cuts import record_read_error

    [doc] = compute_documents(job)
    record_read_error(job, doc, "t1", "Tesseract hata verdi")
    assert "Tesseract hata verdi" in plan_export(job, {"t1": make_template()})[0].checks
    job.manual_cuts.add("a/1")
    first, _ = plan_export(job, {"t1": make_template()})
    assert "Tesseract hata verdi" not in first.checks
