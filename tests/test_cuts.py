from fakes import job_from_kinds

from evrakci.pipeline.cuts import compute_documents


def ids(docs):
    return [list(d.page_ids) for d in docs]


def test_qr_fences_and_is_dropped():
    job = job_from_kinds({"a": "ppqpppqpp"})
    assert ids(compute_documents(job)) == [["a/0", "a/1"], ["a/3", "a/4", "a/5"], ["a/7", "a/8"]]


def test_empty_pages_never_cut():
    job = job_from_kinds({"a": "pepep"})
    assert ids(compute_documents(job)) == [["a/0", "a/1", "a/2", "a/3", "a/4"]]
    job.drop_empty = True
    assert ids(compute_documents(job)) == [["a/0", "a/2", "a/4"]]
    job.restored.add("a/1")
    assert ids(compute_documents(job)) == [["a/0", "a/1", "a/2", "a/4"]]


def test_filter_only_on_selection_and_leftover_flagged():
    job = job_from_kinds({"a": "ppppppp"})
    job.apply_filter([f"a/{i}" for i in range(5)], 2)
    docs = compute_documents(job)
    assert ids(docs) == [["a/0", "a/1"], ["a/2", "a/3"], ["a/4"], ["a/5", "a/6"]]
    assert [d.flags for d in docs] == [set(), set(), {"leftover"}, set()]


def test_filter_restarts_after_qr_and_manual_cut():
    job = job_from_kinds({"a": "ppppqppppp"})
    job.apply_filter(job.ordered_page_ids(), 2)
    job.manual_cuts.add("a/8")
    assert ids(compute_documents(job)) == [
        ["a/0", "a/1"],
        ["a/2", "a/3"],
        ["a/5", "a/6"],
        ["a/7"],
        ["a/8", "a/9"],
    ]


def test_last_filter_wins():
    job = job_from_kinds({"a": "pppppp"})
    job.apply_filter(job.ordered_page_ids(), 3)
    job.apply_filter(["a/0", "a/1"], 1)
    assert ids(compute_documents(job)) == [["a/0"], ["a/1"], ["a/2", "a/3", "a/4"], ["a/5"]]


def test_removed_qr_cut_and_deleted_pages():
    job = job_from_kinds({"a": "ppqpp"})
    job.removed_cuts.add("a/2")
    job.deleted.add("a/0")
    assert ids(compute_documents(job)) == [["a/1", "a/3", "a/4"]]


def test_nothing_left():
    assert compute_documents(job_from_kinds({"a": "qqq"})) == []
    job = job_from_kinds({"a": "pp"})
    job.deleted |= {"a/0", "a/1"}
    assert compute_documents(job) == []


def test_filter_follows_pages_after_batch_reorder():
    job = job_from_kinds({"a": "pppp", "b": "pp"})
    job.apply_filter(["a/0", "a/1", "a/2", "a/3"], 2)
    job.batches.reverse()
    assert ids(compute_documents(job)) == [["b/0", "b/1"], ["a/0", "a/1"], ["a/2", "a/3"]]


def test_cut_survives_deleting_its_page():
    job = job_from_kinds({"a": "pppp"})
    job.manual_cuts.add("a/2")
    job.deleted.add("a/2")
    assert ids(compute_documents(job)) == [["a/0", "a/1"], ["a/3"]]


def test_cut_survives_dropping_its_empty_page():
    job = job_from_kinds({"a": "ppep"})
    job.manual_cuts.add("a/2")
    job.drop_empty = True
    assert ids(compute_documents(job)) == [["a/0", "a/1"], ["a/3"]]
