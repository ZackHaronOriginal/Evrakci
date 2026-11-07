import json

import pytest
from fakes import job_from_kinds

from evrakci.pipeline.cuts import compute_documents, record_values
from evrakci.pipeline.job import job_to_dict
from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.values import VariableValue
from evrakci.ui.controller import JobController


@pytest.fixture
def ctl(qapp, tmp_path):
    job = job_from_kinds({"a": "ppqpppep"})
    store = JobStore(tmp_path)
    store.save(job)
    return JobController(store, job)


def _saved(ctl):
    return json.loads((ctl.store.root / ctl.job.id / "job.json").read_text(encoding="utf-8"))


EDITS = [
    lambda c: c.apply_filter(["a/3", "a/4", "a/5", "a/6"], 2),
    lambda c: c.add_cut("a/1"),
    lambda c: c.remove_cut("a/2"),
    lambda c: c.apply_template(["a/0", "a/1"], "t1"),
    lambda c: c.rotate("a/4", 90),
    lambda c: c.delete_page("a/5"),
    lambda c: c.set_drop_empty(True),
]


@pytest.mark.parametrize("edit", EDITS)
def test_each_edit_undoes_and_redoes_exactly_and_saves(ctl, edit):
    before = job_to_dict(ctl.job)
    edit(ctl)
    after = job_to_dict(ctl.job)
    assert after != before
    assert _saved(ctl) == after
    ctl.undo()
    assert job_to_dict(ctl.job) == before
    assert _saved(ctl) == before
    ctl.redo()
    assert job_to_dict(ctl.job) == after
    assert _saved(ctl) == after


def test_undelete_is_its_own_undoable_edit(ctl):
    ctl.delete_page("a/5")
    ctl.undelete_page("a/5")
    assert "a/5" not in ctl.job.deleted
    ctl.undo()
    assert "a/5" in ctl.job.deleted


def test_core_error_becomes_turkish_message_and_changes_nothing(ctl, qtbot):
    before = job_to_dict(ctl.job)
    with qtbot.waitSignal(ctl.status) as signal:
        ctl.add_cut("a/2")  # a QR page already cuts
    assert job_to_dict(ctl.job) == before
    assert not ctl.undo_stack.canUndo()
    assert "kesim" in signal.args[0].lower()


def test_unknown_page_error_is_turkish(ctl, qtbot):
    with qtbot.waitSignal(ctl.status) as signal:
        ctl.rotate("zz/9", 90)
    assert "sayfa" in signal.args[0].lower()


def test_documents_follow_edits_and_job_changed_fires(ctl, qtbot):
    assert ctl.documents() == compute_documents(ctl.job)
    with qtbot.waitSignal(ctl.job_changed):
        ctl.add_cut("a/1")
    assert ctl.documents() == compute_documents(ctl.job)
    assert ctl.documents()[0].page_ids == ("a/0",)


def test_set_value_marks_edited_and_undoes(ctl):
    ctl.apply_template(["a/0", "a/1"], "t1")
    doc = ctl.documents()[0]
    flagged = VariableValue("48Z13", 0.3, None, True, "48213", (), False)
    record_values(ctl.job, doc, "t1", {"k": flagged})
    ctl.set_value(doc, "k", "48213")
    assert ctl.job.values["a/0"]["k"].edited is True
    ctl.undo()
    assert ctl.job.values["a/0"]["k"].value == "48Z13"


def test_accept_suggestion_undoes(ctl):
    ctl.apply_template(["a/0", "a/1"], "t1")
    doc = ctl.documents()[0]
    flagged = VariableValue("48Z13", 0.3, None, True, "48213", (), False)
    record_values(ctl.job, doc, "t1", {"k": flagged})
    ctl.accept_suggestion(doc, "k")
    assert ctl.job.values["a/0"]["k"].value == "48213"
    ctl.undo()
    assert ctl.job.values["a/0"]["k"].value == "48Z13"
