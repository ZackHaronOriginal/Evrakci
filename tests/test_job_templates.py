import json

from fakes import job_from_kinds

from evrakci.pipeline.cuts import compute_documents, document_template
from evrakci.pipeline.job import job_from_dict, job_to_dict
from evrakci.pipeline.templates.read import SectionReading, VariableValue


def test_last_applied_template_wins():
    job = job_from_kinds({"a": "pppp"})
    job.apply_template(job.ordered_page_ids(), "t1")
    job.apply_template(["a/2", "a/3"], "t2")
    job.apply_filter(job.ordered_page_ids(), 2)
    docs = compute_documents(job)
    assert [document_template(job, d) for d in docs] == [("t1", False), ("t2", False)]


def test_first_page_template_and_mixed_flag():
    job = job_from_kinds({"a": "pppp"})
    job.apply_template(["a/0", "a/1"], "t1")
    job.apply_template(["a/2"], "t2")
    [doc] = compute_documents(job)
    assert document_template(job, doc) == ("t1", True) and "mixed_templates" in doc.flags


def test_untemplated_pages():
    job = job_from_kinds({"a": "pp"})
    [doc] = compute_documents(job)
    assert document_template(job, doc) == (None, False) and doc.flags == frozenset()


def test_v1_job_loads():
    job = job_from_kinds({"a": "pp"})
    data = job_to_dict(job)
    data["version"] = 1
    for key in ("templates", "values", "read_errors"):
        data.pop(key)
    loaded = job_from_dict(data)
    assert loaded.templates == [] and loaded.values == {} and loaded.read_errors == {}


def test_values_round_trip():
    job = job_from_kinds({"a": "pp"})
    job.apply_template(["a/0", "a/1"], "t1")
    readings = (SectionReading(0, "Ornek", 0.4), SectionReading(1, "Örnek", 0.91))
    missing = (SectionReading(0, "", 0.0, "sayfa yok"),)
    job.values["a/0"] = {
        "Ünvan": VariableValue("Örnek", 0.91, 1, False, "", readings),
        "Kayıt No": VariableValue("", 0.0, None, True, "12", missing, True),
    }
    job.read_errors["a/0"] = "Şablon bulunamadı: t9"
    text = json.dumps(job_to_dict(job), ensure_ascii=False)
    assert job_from_dict(json.loads(text)) == job


def test_remove_batch_clears_template_data():
    job = job_from_kinds({"a": "pp", "b": "p"})
    job.apply_template(["a/0", "b/0"], "t1")
    job.values["b/0"] = {}
    job.read_errors["b/0"] = "x"
    job.remove_batch("b")
    assert job.templates[0].page_ids == frozenset({"a/0"})
    assert job.values == {} and job.read_errors == {}
