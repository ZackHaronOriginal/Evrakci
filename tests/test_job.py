import json

import pytest
from fakes import job_from_kinds

from evrakci.pipeline.job import job_from_dict, job_to_dict


def test_order_follows_batches():
    job = job_from_kinds({"a": "pp", "b": "p"})
    job.batches.reverse()
    assert job.ordered_page_ids() == ["b/0", "a/0", "a/1"]


def test_round_trip():
    job = job_from_kinds({"a": "pqep"})
    job.drop_empty = True
    job.manual_cuts.add("a/3")
    job.rotate("a/0", 90)
    job.apply_filter(["a/0", "a/3"], 2)
    assert job_from_dict(json.loads(json.dumps(job_to_dict(job)))) == job


def test_positions_and_cut_edits():
    job = job_from_kinds({"a": "pq", "b": "pp"})
    assert job.page_at(3) == "b/0" and job.position_of("b/1") == 4
    with pytest.raises(IndexError):
        job.page_at(5)
    job.remove_cut("a/1")
    assert job.removed_cuts == {"a/1"}
    job.add_cut("a/1")
    assert job.removed_cuts == set()
    job.add_cut("b/1")
    assert job.manual_cuts == {"b/1"}
    job.remove_cut("b/1")
    assert job.manual_cuts == set()
    with pytest.raises(ValueError):
        job.remove_cut("b/0")
    with pytest.raises(KeyError):
        job.delete_page("z/0")


def test_bad_inputs():
    job = job_from_kinds({"a": "p"})
    with pytest.raises(ValueError):
        job.apply_filter(["a/0"], 0)
    with pytest.raises(ValueError):
        job.rotate("a/0", 45)
    with pytest.raises(ValueError):
        job_from_dict({**job_to_dict(job), "version": 99})


def test_move_and_remove_batch():
    job = job_from_kinds({"a": "pp", "b": "pq", "c": "p"})
    job.move_batch("c", 0)
    assert [b.id for b in job.batches] == ["c", "a", "b"]
    job.manual_cuts.add("b/0")
    job.apply_filter(["a/0", "b/0"], 2)
    job.rotate("b/0", 90)
    job.remove_batch("b")
    assert [b.id for b in job.batches] == ["c", "a"]
    assert "b/0" not in job.pages and job.manual_cuts == set() and job.rotations == {}
    assert job.filters[0].page_ids == frozenset({"a/0"})
    with pytest.raises(KeyError):
        job.remove_batch("zz")
    with pytest.raises(IndexError):
        job.move_batch("a", 5)


def test_add_cut_refuses_where_a_cut_already_is():
    job = job_from_kinds({"a": "pqp"})
    with pytest.raises(ValueError):
        job.add_cut("a/1")  # active QR cut
    assert job.manual_cuts == set()
    job.add_cut("a/2")
    with pytest.raises(ValueError):
        job.add_cut("a/2")  # manual cut already there


def test_required_empty_state_needs_no_new_field_and_old_files_load():
    from evrakci.pipeline.templates.values import VariableValue

    job = job_from_kinds({"a": "pp"})
    job.values["a/0"] = {
        "k": VariableValue("", 0.0, None, True, "48213"),  # what an emptied required value is
        "old": VariableValue("", 1.0, None, False, "", (), True),  # an old emptied edit
    }
    data = job_to_dict(job)
    assert set(data["values"]["a/0"]["k"]) == {
        "value", "confidence", "section", "flagged", "suggestion", "edited", "readings"}
    assert job_from_dict(json.loads(json.dumps(data))) == job
    for value in data["values"]["a/0"].values():  # a file from before: only the old keys
        value.pop("suggestion"), value.pop("readings"), value.pop("edited")
    loaded = job_from_dict(data)
    assert loaded.values["a/0"]["old"].value == "" and loaded.values["a/0"]["old"].flagged is False


def test_remove_filter_on_part_of_a_range_splits_the_application():
    job = job_from_kinds({"a": "pppppppp"})
    ids = job.ordered_page_ids()
    job.apply_filter(ids, 2)
    job.remove_filter(ids[3:5])
    assert [(sorted(f.page_ids), f.every_n) for f in job.filters] == [
        (sorted(ids[:3] + ids[5:]), 2)]
    with pytest.raises(KeyError):
        job.remove_filter(["z/0"])


def test_remove_filter_on_every_page_drops_the_application_and_keeps_older_ones():
    job = job_from_kinds({"a": "pppp"})
    ids = job.ordered_page_ids()
    job.apply_filter(ids, 2)
    job.apply_filter(ids[:2], 1)
    job.remove_filter(ids[:2])  # both applications lose these pages; the second is gone
    assert [(sorted(f.page_ids), f.every_n) for f in job.filters] == [(ids[2:], 2)]
    job.remove_filter(ids)
    assert job.filters == []
    job.remove_filter(ids)  # nothing left to remove: no error
    assert job.filters == []


def test_remove_filter_writes_no_new_field():
    job = job_from_kinds({"a": "pppp"})
    before = set(job_to_dict(job))
    job.apply_filter(job.ordered_page_ids(), 2)
    job.remove_filter(job.ordered_page_ids())
    assert set(job_to_dict(job)) == before
    assert job_from_dict(json.loads(json.dumps(job_to_dict(job)))) == job
