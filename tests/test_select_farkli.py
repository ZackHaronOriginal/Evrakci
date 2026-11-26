"""pipeline/select.py, the criterion `farkli`: pages whose size or orientation differs (I-04)."""

import time

from fakes import job_from_kinds

from evrakci.pipeline.analyze import PageInfo
from evrakci.pipeline.select import (
    Criterion,
    different_pages,
    evaluate,
    kinds,
    unknown_sizes,
)

SIZES = {
    "a": (210.0, 297.0),  # A4 portrait
    "j": (212.5, 299.0),  # A4 portrait, scanner jitter (about 1 %)
    "l": (297.0, 210.0),  # A4 landscape
    "f": (148.0, 210.0),  # A5 portrait
    "g": (210.0, 148.0),  # A5 landscape
    "u": (0.0, 0.0),  # unknown
}


def sized(spec: str, batch: str = "a"):
    """A job whose pages follow `spec`: a A4, j A4 with jitter, l A4 landscape, f A5, g A5
    landscape, u unknown size, q QR separator."""
    job = job_from_kinds({batch: "p" * len(spec)})
    for index, letter in enumerate(spec):
        if letter == "q":
            job.pages[f"{batch}/{index}"] = PageInfo(0.02, True, 210.0, 297.0)
        else:
            width, height = SIZES[letter]
            job.pages[f"{batch}/{index}"] = PageInfo(0.05, False, width, height)
    return job


def pick(job, by=("boyut", "yon"), reference="is"):
    return evaluate(job, Criterion("farkli", {"by": list(by), "reference": reference}))


def pids(*numbers):
    return tuple(f"a/{n}" for n in numbers)


def test_the_kind_is_registered_and_a_uniform_job_marks_nothing():
    assert "farkli" in kinds()
    assert pick(sized("aaaaa")).page_ids == ()
    assert different_pages(sized("aaaaa")) == {}


def test_a_page_of_another_size_is_marked_as_size():
    job = sized("aaafaa")
    assert different_pages(job) == {"a/3": "boyut"}
    assert pick(job).page_ids == pids(3)
    assert pick(job).reasons == {"boyut": 1}


def test_scanner_jitter_does_not_mark():
    assert pick(sized("ajajaja")).page_ids == ()
    assert pick(sized("jjjaaa")).page_ids == ()


def test_a_sideways_page_is_marked_as_landscape_not_as_size():
    job = sized("aalaa")
    assert different_pages(job) == {"a/2": "yatay"}
    assert pick(job).reasons == {"yon": 1}


def test_a_job_that_is_mostly_landscape_marks_the_portrait_page():
    assert different_pages(sized("llalll")) == {"a/2": "dikey"}


def test_a_size_and_an_orientation_difference_is_reported_as_size():
    assert different_pages(sized("aagaa")) == {"a/2": "boyut"}  # A5 landscape in an A4 pile


def test_each_check_box_alone():
    job = sized("aalfa")
    assert different_pages(job, by=("boyut",)) == {"a/3": "boyut"}
    assert different_pages(job, by=("yon",)) == {"a/2": "yatay"}
    assert different_pages(job, by=()) == {}
    assert different_pages(job) == {"a/2": "yatay", "a/3": "boyut"}


def test_a_rotation_that_stands_the_page_up_takes_the_mark_away():
    job = sized("aalaa")
    assert pick(job).page_ids == pids(2)
    job.rotate("a/2", 90)
    assert pick(job).page_ids == ()
    job.rotate("a/2", 90)  # a half turn from the scan: sideways again
    assert pick(job).page_ids == pids(2)


def test_a_user_rotation_of_an_upright_page_marks_it():
    job = sized("aaaaa")
    job.rotate("a/1", 90)
    assert different_pages(job) == {"a/1": "yatay"}
    job.rotate("a/1", -90)
    assert different_pages(job) == {}


def test_a_rotation_does_not_change_a_size_difference():
    job = sized("aafaa")
    job.rotate("a/2", 90)
    assert different_pages(job) == {"a/2": "boyut"}


def test_the_reference_is_the_most_frequent_size_of_the_pages_that_count():
    job = sized("aaffffa")
    assert different_pages(job) == {"a/0": "boyut", "a/1": "boyut", "a/6": "boyut"}
    for number in (2, 3, 4):  # deleted pages no longer count: A4 is the majority again
        job.delete_page(f"a/{number}")
    assert different_pages(job) == {"a/5": "boyut"}


def test_separators_do_not_count_and_never_match():
    job = sized("aqaqaf")
    assert different_pages(job) == {"a/5": "boyut"}
    assert unknown_sizes(job) == 0


def test_deleted_pages_and_dropped_blank_pages_never_match():
    job = sized("aaafaa")
    job.delete_page("a/3")
    assert pick(job).page_ids == ()
    job = sized("aaafaa")
    job.drop_empty = True
    job.pages["a/3"] = PageInfo(0.0, False, *SIZES["f"])  # blank: dropped, in no document
    assert pick(job).page_ids == ()


def test_pages_of_unknown_size_are_never_marked_and_are_counted():
    job = sized("aauuuf")
    assert different_pages(job) == {"a/5": "boyut"}
    assert unknown_sizes(job) == 3
    assert pick(job).reasons == {"boyut": 1, "bilinmiyor": 3}
    assert different_pages(sized("uuuu")) == {}


def test_a_tie_goes_to_the_size_that_comes_first():
    assert different_pages(sized("aaff")) == {"a/2": "boyut", "a/3": "boyut"}
    assert different_pages(sized("ffaa")) == {"a/2": "boyut", "a/3": "boyut"}


def test_the_reference_can_be_each_document():
    # an A4 document and an A5 document, cut by a QR page; the job's majority is A5
    job = sized("aaaqfffff")
    assert pick(job).page_ids == pids(0, 1, 2)
    assert pick(job, reference="belge").page_ids == ()
    odd = sized("aaaafqffff")
    assert pick(odd, reference="belge").page_ids == pids(4)
    assert pick(odd, reference="belge").documents == 1


def test_the_count_of_documents_is_the_documents_with_a_marked_page():
    job = sized("aafqaaafqaaa")
    match = pick(job)
    assert match.page_ids == pids(2, 7)
    assert match.documents == 2


def test_bad_parameters_fall_back_to_the_defaults():
    job = sized("aalfa")
    assert evaluate(job, Criterion("farkli")).page_ids == pids(2, 3)
    assert evaluate(job, Criterion("farkli", {"reference": "x"})).page_ids == pids(2, 3)
    assert evaluate(job, Criterion("farkli", {"by": ["x"]})).page_ids == ()


def test_the_result_is_in_job_order_across_batches():
    job = sized("aaf", "a")
    other = sized("faa", "b")
    job.batches.extend(other.batches)
    job.pages.update(other.pages)
    assert tuple(different_pages(job)) == ("a/2", "b/0")


def test_800_pages_are_marked_in_a_few_milliseconds():
    job = sized(("aaaaaaaal" * 100)[:800])
    start = time.perf_counter()
    marks = different_pages(job)
    elapsed = time.perf_counter() - start
    assert len(marks) == 88
    assert elapsed < 0.25, elapsed
