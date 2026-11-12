import threading

import pytest
from fakes import job_from_kinds, make_pdf, text_page

from evrakci.pipeline.cuts import current_values, record_values
from evrakci.pipeline.ocr.engine import Reading
from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.model import Section
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.pipeline.templates.values import VariableValue
from evrakci.ui.controller import JobController
from evrakci.ui.degerler import DegerlerScreen


@pytest.fixture
def setup(qtbot, tmp_path):
    pdf = make_pdf(tmp_path / "b1.pdf", [text_page("A"), text_page("B"), text_page("C")])
    store = JobStore(tmp_path / "jobs")
    job = job_from_kinds({"b1": "ppp"})
    target = store.batch_file(job, job.batches[0])
    target.parent.mkdir(parents=True)
    target.write_bytes(pdf.read_bytes())
    store.save(job)
    ctl = JobController(store, job)
    ctl.add_cut("b1/1")
    ctl.add_cut("b1/2")
    templates = TemplateStore(tmp_path / "tpl")
    template = templates.create("Kapasite Raporu")
    sicil = template.add_variable("Sicil_No", required=True)
    template.add_section("Sicil_No", Section(1, (10, 10, 60, 20)))
    template.set_pattern("{Sicil_No}")
    templates.save(template)
    ctl.apply_template(job.ordered_page_ids(), template.id)
    docs = ctl.documents()
    good = VariableValue("48197", 0.95, 0, False)
    bad = VariableValue("", 0.0, None, True, "48213", (), False)
    for doc, value in zip(docs, (good, bad, good), strict=True):
        record_values(ctl.job, doc, template.id, {sicil.key: value})
    ctl.job_changed.emit()
    return ctl, templates, template, sicil


def _screen(qtbot, ctl, templates, engine=None):
    screen = DegerlerScreen(lambda: ctl, lambda: {t.id: t for t in templates.list()}, engine=engine)
    qtbot.addWidget(screen)
    screen.resize(1366, 700)
    screen.refresh()
    return screen


def test_filter_shows_only_documents_that_need_a_check(qtbot, setup):
    ctl, templates, _, _ = setup
    screen = _screen(qtbot, ctl, templates)
    screen.only_checks.setChecked(False)
    assert screen.table.rowCount() == 3
    screen.only_checks.setChecked(True)
    assert screen.table.rowCount() == 1
    assert screen.table.item(0, 0).text() == "2"
    assert "(1)" in screen.only_checks.text()


def test_editing_a_cell_stores_an_edited_value(qtbot, setup):
    ctl, templates, _, sicil = setup
    screen = _screen(qtbot, ctl, templates)
    screen.only_checks.setChecked(False)
    column = screen.column_of("Sicil_No")
    screen.table.item(0, column).setText("48190")
    value = current_values(ctl.job, ctl.documents()[0])[sicil.key]
    assert value.value == "48190" and value.edited


def test_accepting_the_suggestion(qtbot, setup):
    ctl, templates, _, sicil = setup
    screen = _screen(qtbot, ctl, templates)
    screen.table.setCurrentCell(0, screen.column_of("Sicil_No"))
    assert "48213" in screen.side.suggestion.text()
    screen.side.accept_button.click()
    value = current_values(ctl.job, ctl.documents()[1])[sicil.key]
    assert value.value == "48213" and value.edited and not value.flagged


class GatedEngine:
    name = "sahte"

    def __init__(self, gate):
        self.gate = gate

    def available(self):
        return None

    def read_region(self, image):
        self.gate.wait(5)
        return Reading("99999", 0.9)


def test_an_edit_made_while_reading_wins(qtbot, setup):
    ctl, templates, _, sicil = setup
    gate = threading.Event()
    screen = _screen(qtbot, ctl, templates, engine=lambda: GatedEngine(gate))
    screen.only_checks.setChecked(False)
    screen.read_button.click()
    column = screen.column_of("Sicil_No")
    screen.table.item(0, column).setText("12345")  # while the read runs
    gate.set()
    qtbot.waitUntil(lambda: not screen.busy(), timeout=20000)
    docs = ctl.documents()
    assert current_values(ctl.job, docs[0])[sicil.key].value == "12345"
    assert current_values(ctl.job, docs[1])[sicil.key].value == "99999"


class FixedEngine:
    name = "sahte"

    def available(self):
        return None

    def read_region(self, image):
        return Reading("77777", 0.9)


def test_reading_only_missing_includes_documents_read_with_an_older_template(qtbot, setup):
    import dataclasses

    from evrakci.pipeline.templates.model import template_revision

    ctl, templates, template, sicil = setup
    for pid, source in list(ctl.job.value_sources.items()):  # read with this version
        ctl.job.value_sources[pid] = dataclasses.replace(
            source, revision=template_revision(template))
    template.add_section("Sicil_No", Section(1, (10, 30, 60, 40)))  # the template changed
    templates.save(template)
    screen = _screen(qtbot, ctl, templates, engine=FixedEngine)
    screen.read_values(only_missing=True)
    qtbot.waitUntil(lambda: not screen.busy(), timeout=20000)
    docs = ctl.documents()
    assert all(current_values(ctl.job, d)[sicil.key].value == "77777" for d in docs)
    source = ctl.job.value_sources[docs[0].page_ids[0]]
    assert source.revision == template_revision(templates.load(template.id))
