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
    # What was read stays as the suggestion, so the correction can be undone.
    assert got["k1"] == VariableValue("Örnek Ltd.", 1.0, None, False, "Örnek", (), True)
    assert got["k2"].value == "12345" and got["k2"].edited and not got["k2"].flagged
    set_value(job, doc, "yeni", "x")  # a variable added to the template after reading
    assert current_values(job, doc)["yeni"].value == "x"
    with pytest.raises(ValueError):
        accept_suggestion(job, doc, "k1")  # nothing left to accept


def test_no_current_values():
    job = job_from_kinds({"a": "pp"})
    [doc] = compute_documents(job)
    with pytest.raises(KeyError):
        set_value(job, doc, "k1", "x")


def test_store_reading_keeps_the_users_corrections():
    from evrakci.pipeline.review import store_reading

    job = job_from_kinds({"a": "pp"})
    job.apply_template(job.ordered_page_ids(), "t1")
    [doc] = compute_documents(job)
    record_values(job, doc, "t1", values())
    set_value(job, doc, "k1", "Elle yazıldı")
    fresh = {"k1": VariableValue("Yeni", 0.95, 0, False), "k2": VariableValue("777", 0.9, 0, False)}
    store_reading(job, doc, "t1", fresh)
    got = current_values(job, doc)
    assert got["k1"].value == "Elle yazıldı" and got["k1"].edited
    assert got["k2"].value == "777"


def test_can_revert():
    from evrakci.pipeline.review import can_revert
    from evrakci.pipeline.templates.values import SectionReading

    assert not can_revert(VariableValue("Örnek", 0.9, 0, False))  # never corrected
    assert not can_revert(VariableValue("elle", 1.0, None, False, "", (), True))  # no reading
    assert can_revert(VariableValue("elle", 1.0, None, False, "okunan", (), True))
    assert can_revert(VariableValue("elle", 1.0, None, False, "", (SectionReading(0, "x", 0.5),),
                                    True))


def test_revert_after_set_value_and_after_accept_suggestion_keeps_the_reading():
    from evrakci.pipeline.review import can_revert, revert_value

    job = job_from_kinds({"a": "pp"})
    job.apply_template(job.ordered_page_ids(), "t1")
    [doc] = compute_documents(job)
    record_values(job, doc, "t1", values())
    set_value(job, doc, "k1", "Yanlış")
    accept_suggestion(job, doc, "k2")
    assert can_revert(current_values(job, doc)["k1"])
    assert can_revert(current_values(job, doc)["k2"])
    revert_value(job, doc, "k1")
    revert_value(job, doc, "k2")
    got = current_values(job, doc)
    assert got["k1"] == VariableValue("", 0.0, None, True, "Örnek", (), False)
    assert got["k2"] == VariableValue("", 0.0, None, True, "12345", (), False)
    assert not can_revert(got["k1"])


def test_an_emptied_required_value_waits_in_kontrol_with_its_reading():
    from evrakci.pipeline.review import can_revert, revert_value

    job = job_from_kinds({"a": "pp"})
    job.apply_template(job.ordered_page_ids(), "t1")
    [doc] = compute_documents(job)
    read = VariableValue("Örnek", 0.9, 0, False)
    record_values(job, doc, "t1", {"k1": read, "k2": read})
    assert set_value(job, doc, "k1", "Yeni", required=True) is True
    assert set_value(job, doc, "k1", "", required=True) is False
    got = current_values(job, doc)["k1"]
    # the state revert_value makes: flagged, unreviewed, the reading kept as the suggestion
    assert got == VariableValue("", 0.0, None, True, "Örnek", (), False)
    assert not can_revert(got)
    set_value(job, doc, "k2", "Yeni")
    revert_value(job, doc, "k2")  # a revert makes the very same state
    assert current_values(job, doc)["k2"] == got


def test_whitespace_counts_as_empty_for_a_required_value():
    job = job_from_kinds({"a": "pp"})
    job.apply_template(job.ordered_page_ids(), "t1")
    [doc] = compute_documents(job)
    record_values(job, doc, "t1", values())
    assert set_value(job, doc, "k1", " \t ", required=True) is False
    got = current_values(job, doc)["k1"]
    assert got.flagged and not got.edited and got.value == "" and got.suggestion == "Örnek"


def test_an_emptied_value_that_is_not_required_is_stored_as_before():
    job = job_from_kinds({"a": "pp"})
    job.apply_template(job.ordered_page_ids(), "t1")
    [doc] = compute_documents(job)
    record_values(job, doc, "t1", values())
    assert set_value(job, doc, "k1", "") is True
    assert set_value(job, doc, "k2", "  ", required=False) is True
    got = current_values(job, doc)
    assert got["k1"] == VariableValue("", 1.0, None, False, "Örnek", (), True)
    assert got["k2"].edited and not got["k2"].flagged
