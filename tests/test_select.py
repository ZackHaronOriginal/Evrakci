"""pipeline/select.py: the criteria `belge`, `tek` and `cift`, and how a match joins a selection."""

import time

import pytest
from fakes import job_from_kinds

from evrakci.pipeline.select import Criterion, Match, combine, evaluate, kinds


def pids(*numbers):
    return tuple(f"a/{n}" for n in numbers)


def pick(job, kind, **params):
    return evaluate(job, Criterion(kind, params))


def test_kinds_of_this_step():
    assert {"belge", "tek", "cift"} <= set(kinds())


def test_criterion_round_trip():
    criterion = Criterion("tek", {"within": True})
    assert Criterion.from_dict(criterion.to_dict()) == criterion
    assert Criterion.from_dict({"kind": "cift"}) == Criterion("cift", {})


def test_unknown_kind_and_mode():
    job = job_from_kinds({"a": "ppp"})
    with pytest.raises(ValueError, match="unknown criterion kind"):
        evaluate(job, Criterion("yok"))
    with pytest.raises(ValueError, match="unknown mode"):
        combine((), Match(), "yok")


def test_belge_gives_the_pages_of_that_document():
    job = job_from_kinds({"a": "pppqppqp"})
    match = pick(job, "belge", number=2)
    assert match.page_ids == pids(4, 5) and match.documents == 1 and match.count() == 2
    assert pick(job, "belge", number=3).page_ids == pids(7)


def test_belge_out_of_range_matches_nothing():
    job = job_from_kinds({"a": "pppqpp"})
    for number in (0, 3, -1, "2", None):
        assert pick(job, "belge", number=number) == Match()
    assert pick(job, "belge") == Match()


def test_belge_never_has_separators_or_deleted_pages():
    job = job_from_kinds({"a": "ppqpppp"})
    job.delete_page("a/4")
    match = pick(job, "belge", number=2)
    assert match.page_ids == pids(3, 5, 6)
    assert "a/2" not in match.page_ids


def test_odd_and_even_count_from_each_documents_first_page():
    job = job_from_kinds({"a": "ppppq" + "ppp" + "q" + "pp"})  # documents of 4, 3 and 2 pages
    assert pick(job, "tek").page_ids == pids(0, 2, 5, 7, 9)
    assert pick(job, "cift").page_ids == pids(1, 3, 6, 10)
    assert pick(job, "tek").documents == 3 and pick(job, "cift").documents == 3


def test_counting_restarts_after_a_cut_and_skips_a_deleted_page():
    job = job_from_kinds({"a": "pppppqppppp"})
    job.delete_page("a/1")  # document 1 is pages 0, 2, 3, 4
    job.add_cut("a/9")  # document 3 starts at page 9
    assert pick(job, "tek").page_ids == pids(0, 3, 6, 8, 9)
    assert pick(job, "cift").page_ids == pids(2, 4, 7, 10)


def test_a_one_page_document_has_no_even_page():
    job = job_from_kinds({"a": "pqpp"})
    assert pick(job, "cift").page_ids == pids(3)
    assert pick(job, "cift").documents == 1
    assert pick(job, "tek").documents == 2


def test_separators_are_never_matched():
    job = job_from_kinds({"a": "qpqppq"})
    for kind in ("tek", "cift"):
        assert not {"a/0", "a/2", "a/5"} & set(pick(job, kind).page_ids)
    assert pick(job, "tek").page_ids == pids(1, 3) and pick(job, "cift").page_ids == pids(4)


def test_odd_even_within_the_selections_documents_only():
    job = job_from_kinds({"a": "pppqppqpp"})
    selection = pids(4)  # a page of document 2
    plain = evaluate(job, Criterion("tek", {"within": False}), selection=selection)
    inside = evaluate(job, Criterion("tek", {"within": True}), selection=selection)
    assert plain.page_ids == pids(0, 2, 4, 7) and plain.documents == 3
    assert inside.page_ids == pids(4) and inside.documents == 1
    # a selection that holds only a separator touches no document
    none = evaluate(job, Criterion("cift", {"within": True}), selection=pids(3))
    assert none.page_ids == () and none.documents == 0


def test_job_order_across_batches():
    job = job_from_kinds({"a": "ppp", "b": "ppp"})
    assert pick(job, "tek").page_ids == ("a/0", "a/2", "b/1")
    assert pick(job, "belge", number=1).page_ids == ("a/0", "a/1", "a/2", "b/0", "b/1", "b/2")


def test_combine_modes():
    match = Match(pids(1, 3, 5), 1)
    base = pids(3, 4)
    assert combine(base, match, "replace") == pids(1, 3, 5)
    assert combine(base, match, "add") == pids(3, 4, 1, 5)
    assert combine(base, match, "within") == pids(3)
    order = [f"a/{n}" for n in range(8)]
    assert combine(base, match, "add", order=order) == pids(1, 3, 4, 5)
    assert combine((), match, "within") == ()


def test_evaluate_800_pages_is_fast():
    job = job_from_kinds({"a": "pppq" * 200})  # 800 pages, 200 documents of 3
    start = time.perf_counter()
    for _ in range(20):
        pick(job, "tek")
        pick(job, "cift")
        pick(job, "belge", number=100)
    each_ms = (time.perf_counter() - start) * 1000 / 60
    assert each_ms < 5, each_ms  # the dialog may call it on the window thread
