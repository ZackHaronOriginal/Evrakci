"""Değerler without widgets: Güven levels, uncertain characters, the sample, confirming
values, and a refresh that stays quick at 1,000 documents."""

import time

from fakes import job_from_kinds

from evrakci.pipeline.cuts import current_values, record_values
from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.model import Section, Template, Variable
from evrakci.pipeline.templates.values import SectionReading, VariableValue
from evrakci.ui.controller import JobController
from evrakci.ui.degerler import DegerlerScreen
from evrakci.ui.degerler_model import (
    build_rows,
    changed_positions,
    column_kind,
    confirm,
    count,
    draw_sample,
    flag_variable,
    in_view,
    joined,
    make_cell,
    swaps,
    tr_lower,
    uncertain_positions,
)

VAR = Variable("Sicil_No", [Section(1, (10, 10, 60, 20))], True, key="k1")


def test_levels_and_percentages():
    assert make_cell(VAR, VariableValue("48197", 0.95, 0, False)).level == "emin"
    assert make_cell(VAR, VariableValue("48197", 0.84, 0, False)).level == "orta"
    edited = make_cell(VAR, VariableValue("48197", 0.84, 0, False, edited=True))
    assert edited.level == "emin" and edited.reviewed and edited.percent == 84
    flagged = make_cell(VAR, VariableValue("", 0.0, None, True, "48213",
                                            (SectionReading(0, "482I3", 0.4),
                                             SectionReading(1, "48213", 0.55))))
    assert (flagged.level, flagged.percent, flagged.text) == ("kontrol", 55, "482I3")
    assert flagged.uncertain == (3,) and flagged.suggestion_marks == (3,)
    assert flagged.source == 1 and flagged.edit_text() == "48213"
    unreadable = make_cell(VAR, VariableValue("", 0.0, None, True, "",
                                              (SectionReading(0, "", 0.0),)))
    assert unreadable.level == "okunamadi" and unreadable.percent is None
    assert make_cell(VAR, None).level == "okunmadi"


def test_uncertain_characters():
    assert uncertain_positions("34-0I72-K/B", ["34-0172-K/8"], True) == (4, 10)
    # One reading only: letters next to digits are the usual OCR mix-ups
    assert uncertain_positions("O4.11.2026", [], True) == (0,)
    assert uncertain_positions("O4.11.2026", [], False) == ()
    assert changed_positions("34-0I72-K/B", "34-0172-K/8") == (4, 10)
    assert swaps("34-0I72-K/B", "34-0172-K/8") == [("I", "1"), ("B", "8")]


def test_why_names_the_variant_and_the_swaps():
    cell = make_cell(VAR, VariableValue("", 0.0, None, True, "34-0172-K/8",
                                         (SectionReading(0, "34-0I72-K/B", 0.4),
                                          SectionReading(1, "34-0172-K/8", 0.55))))
    assert cell.why() == "Varyant 2 ile okundu: I yerine 1, B yerine 8."


def test_column_kinds_and_words():
    assert column_kind(["1.250", "840"]) == "number"
    assert column_kind(["48190", "48191"]) == "code"
    assert column_kind(["22.09.2026"]) == "date"
    assert column_kind(["35-0211-G/1"]) == "code"
    assert column_kind(["Gediz Tekstil San. A.Ş."]) == "text"
    assert tr_lower("SICIL İL") == "sıcıl il"
    assert joined(["firma", "sicil no", "tarih"]) == "firma, sicil no ve tarih"


def _job(n: int, flagged_every: int = 0):
    job = job_from_kinds({"b1": "qp" * n})
    template = Template("t1", "Rapor", [VAR, Variable("Firma", [Section(1, (10, 30, 90, 40))],
                                                      key="k2")])
    job.apply_template(job.ordered_page_ids(), template.id)
    from evrakci.pipeline.cuts import compute_documents

    for i, doc in enumerate(compute_documents(job)):
        flagged = flagged_every and i % flagged_every == 0
        sicil = (VariableValue("", 0.0, None, True, f"4{i:04d}", (SectionReading(0, f"4{i:04d}",
                                                                                 0.5),))
                 if flagged else VariableValue(f"4{i:04d}", 0.95, 0, False))
        record_values(job, doc, template.id, {"k1": sicil,
                                              "k2": VariableValue(f"Firma {i}", 0.97, 0, False)})
    return job, template


def test_counts_views_and_confirm():
    from evrakci.pipeline.cuts import compute_documents

    job, template = _job(6, flagged_every=3)
    documents = compute_documents(job)
    rows = build_rows(job, documents, {template.id: template})
    counts = count(rows)
    assert (counts.values, counts.kontrol, counts.reviewed) == (12, 2, 0)
    assert [r.number for r in rows if in_view(r, "kontrol")] == [1, 4]
    assert confirm(job, documents[0], "k1")  # accepts the suggestion
    assert current_values(job, documents[0])["k1"].value == "40000"
    assert confirm(job, documents[1], "k1")  # marks what was read as reviewed
    value = current_values(job, documents[1])["k1"]
    assert value.edited and value.confidence == 0.95


def test_sample_is_stable_and_an_error_flags_the_rest():
    from evrakci.pipeline.cuts import compute_documents

    job, template = _job(30)
    documents = compute_documents(job)
    rows = build_rows(job, documents, {template.id: template})
    first = draw_sample(rows, "job-1")
    assert len(first) == 20 and first == draw_sample(rows, "job-1")
    assert all(r.cell(s.key).level == "emin"
               for s in first for r in rows if r.document.page_ids[0] == s.first_page)
    assert flag_variable(job, documents[1:], "k1") == 29
    assert current_values(job, documents[2])["k1"].suggestion == "40002"


def test_refresh_stays_quick_at_1000_documents(qtbot, tmp_path):
    job, template = _job(1000, flagged_every=7)
    ctl = JobController(JobStore(tmp_path / "jobs"), job)
    screen = DegerlerScreen(lambda: ctl, lambda: {template.id: template})
    qtbot.addWidget(screen)
    screen.resize(1366, 700)
    started = time.perf_counter()
    screen.refresh()
    took = time.perf_counter() - started
    assert screen.model.rowCount() == 1000
    assert took < 1.5, took
    started = time.perf_counter()
    screen.accept_current()  # one undoable edit + refresh + move on
    assert time.perf_counter() - started < 3.0
    assert screen.current_value() == (8, "k1")
