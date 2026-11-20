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


def test_cut_kinds_names_what_starts_each_document():
    from fakes import job_from_kinds

    from evrakci.pipeline.cuts import compute_documents, cut_kinds
    from evrakci.pipeline.job import page_id

    job = job_from_kinds({"a": "pqpppppp"})
    job.apply_filter([page_id("a", i) for i in (2, 3, 4, 5)], 2)
    job.add_cut(page_id("a", 7))
    docs = compute_documents(job)
    kinds = cut_kinds(job)
    assert [kinds[d.page_ids[0]] for d in docs] == ["start", "qr", "filter", "filter", "manual"]


def test_cut_kinds_first_document_after_a_leading_qr_page_is_qr():
    from fakes import job_from_kinds

    from evrakci.pipeline.cuts import cut_kinds

    assert cut_kinds(job_from_kinds({"a": "qpp"})) == {"a/1": "qr"}


def test_documents_after_a_filter_is_removed():
    job = job_from_kinds({"a": "pppppppqpp"})
    before = ids(compute_documents(job))
    job.apply_filter(job.ordered_page_ids(), 2)
    assert ids(compute_documents(job)) != before
    job.remove_filter(job.ordered_page_ids())
    assert ids(compute_documents(job)) == before  # everything between two cuts again


def test_removing_the_middle_of_a_filter_leaves_two_partial_ranges():
    job = job_from_kinds({"a": "pppppppp"})
    pids = job.ordered_page_ids()
    job.apply_filter(pids, 3)
    job.remove_filter(pids[3:5])
    docs = compute_documents(job)
    assert ids(docs) == [pids[:3], pids[3:5], pids[5:]]
    assert [d.flags for d in docs] == [set(), set(), set()]
    job.remove_filter(pids[:1] + pids[7:])  # the edges of the ranges: short groups are flagged
    assert any("leftover" in d.flags for d in compute_documents(job))


def test_a_template_removed_makes_the_unread_values_check_go_away():
    from test_export import make_template

    from evrakci.pipeline.export import plan_export

    job = job_from_kinds({"a": "pp"})
    job.apply_template(["a/0", "a/1"], "t1")
    templates = {"t1": make_template()}
    assert plan_export(job, templates)[0].checks == ["değerler okunmadı"]
    job.remove_template(["a/0", "a/1"])
    assert plan_export(job, templates)[0].checks == []
