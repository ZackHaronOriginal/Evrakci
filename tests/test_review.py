import pytest
from fakes import job_from_kinds

from evrakci.pipeline.cuts import compute_documents, current_values, record_values
from evrakci.pipeline.review import accept_suggestion, set_value
from evrakci.pipeline.templates.values import VariableValue


def values():
    return {
        "k1": VariableValue("Örnek", 0.9, 0, False),
        "k2": VariableValue("", 0.0, None, True, "12345"),
    }


def test_set_value_and_accept_suggestion():
    job = job_from_kinds({"a": "pp"})
    job.apply_template(job.ordered_page_ids(), "t1")
    [doc] = compute_documents(job)
    record_values(job, doc, "t1", values())
    set_value(job, doc, "k1", "  Örnek  Ltd. ")
    accept_suggestion(job, doc, "k2")
    got = current_values(job, doc)
    assert got["k1"] == VariableValue("Örnek Ltd.", 1.0, None, False, "", (), True)
    assert got["k2"].value == "12345" and got["k2"].edited and not got["k2"].flagged
    with pytest.raises(KeyError):
        set_value(job, doc, "yok", "x")
    with pytest.raises(ValueError):
        accept_suggestion(job, doc, "k1")  # nothing left to accept


def test_no_current_values():
    job = job_from_kinds({"a": "pp"})
    [doc] = compute_documents(job)
    with pytest.raises(KeyError):
        set_value(job, doc, "k1", "x")
