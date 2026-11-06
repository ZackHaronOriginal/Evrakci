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
