"""pipeline/select.py, the criterion `bos`: blank pages by their ink share (I-03)."""

import time

from fakes import job_from_kinds

from evrakci.pipeline.analyze import EMPTY_INK_RATIO, PageInfo
from evrakci.pipeline.select import Criterion, Match, evaluate, ink_range, kinds


def pids(*numbers):
    return tuple(f"a/{n}" for n in numbers)


def pick(job, **params):
    return evaluate(job, Criterion("bos", params))


def inks(spec: str, shares: dict[int, float]):
    """A job from `spec` whose pages have the ink shares in `shares` (page index -> share)."""
    job = job_from_kinds({"a": spec})
    for index, share in shares.items():
        job.pages[f"a/{index}"] = PageInfo(share, job.pages[f"a/{index}"].is_separator)
    return job


def test_the_default_limit_is_the_analysis_limit():
    job = inks("pepeppp", {1: 0.0, 3: EMPTY_INK_RATIO - 0.0001, 4: EMPTY_INK_RATIO})
    assert "bos" in kinds()
    assert pick(job).page_ids == pids(1, 3)  # the limit itself is not blank
    assert pick(job, ink=0.003).page_ids == pids(1, 3)


def test_a_lower_limit_selects_fewer():
    job = inks("ppppp", {0: 0.0, 1: 0.0004, 2: 0.002, 3: 0.0029})
    assert pick(job, ink=0.003).page_ids == pids(0, 1, 2, 3)
    assert pick(job, ink=0.0005).page_ids == pids(0, 1)
    assert pick(job, ink=0.0).page_ids == ()


def test_a_bad_limit_falls_back_to_the_default():
    job = inks("pepp", {1: 0.001})
    for ink in ("x", None, True, -1):
        assert pick(job, ink=ink).page_ids == pids(1)


def test_a_qr_page_never_matches_however_little_ink():
    job = inks("pqpep", {3: 0.0})
    job.pages["a/1"] = PageInfo(0.0, True)
    assert pick(job, ink=0.05).page_ids == pids(3)


def test_deleted_blanks_are_counted_apart_and_not_selected():
    job = inks("ppepepp", {2: 0.0, 4: 0.0})
    job.delete_page("a/4")
    match = pick(job)
    assert match.page_ids == pids(2) and match.reasons == {"silinmis": 1}
    assert pick(inks("ppep", {2: 0.0})).reasons == {}


def test_job_order_and_the_ink_range_of_the_match():
    job = inks("pppppp", {4: 0.002, 1: 0.0001, 2: 0.0})
    match = pick(job)
    assert match.page_ids == pids(1, 2, 4)
    assert ink_range(job, match) == (0.0, 0.002)
    assert ink_range(job, Match()) is None


def test_800_pages_evaluate_fast():
    job = inks("p" * 800, {i: 0.0 for i in range(0, 800, 2)})
    start = time.perf_counter()
    match = pick(job)
    assert match.count() == 400 and time.perf_counter() - start < 0.05
