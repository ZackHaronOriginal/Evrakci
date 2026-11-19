"""Repro tests for ledger rows B-010 to B-019 (Değerler, Şablonlar). Each asserts the EXPECTED
behaviour and is an xfail(strict) until the bug is fixed; the fixer removes the marker."""

import dataclasses  # noqa: F401  (kept for ad-hoc edits)
import json

import pytest
from fakes import job_from_kinds, make_pdf, text_page
from PySide6.QtWidgets import QLabel

from evrakci.pipeline.cuts import current_values, record_read_error, record_values
from evrakci.pipeline.ocr.engine import Reading
from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.model import Section
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.pipeline.templates.values import SectionReading, VariableValue
from evrakci.ui.controller import JobController
from evrakci.ui.degerler import DegerlerScreen
from evrakci.ui.main_window import MainWindow
from evrakci.ui.prefs import Prefs
from evrakci.ui.sablon import SablonScreen

GOOD = VariableValue("48197", 0.95, 0, False)
BAD = VariableValue("", 0.0, None, True, "48213",
                    (SectionReading(0, "482I3", 0.41), SectionReading(1, "48213", 0.55)))


def _job(tmp_path, kinds="ppp"):
    pdf = make_pdf(tmp_path / "b1.pdf", [text_page(c) for c in "ABCDEF"[:len(kinds)]])
    store = JobStore(tmp_path / "jobs")
    job = job_from_kinds({"b1": kinds})
    target = store.batch_file(job, job.batches[0])
    target.parent.mkdir(parents=True)
    target.write_bytes(pdf.read_bytes())
    store.save(job)
    return store, job


def _template(templates, name, page=1):
    template = templates.create(name)
    sicil = template.add_variable("Sicil_No", required=True)
    firma = template.add_variable("Firma")
    template.add_section("Sicil_No", Section(page, (10, 10, 60, 20)))
    template.add_section("Firma", Section(page, (10, 30, 90, 40)))
    template.set_pattern("{Sicil_No}")
    templates.save(template)
    return template, sicil, firma


def _values(ctl, template, sicil, firma, doc, value):
    record_values(ctl.job, doc, template.id,
                  {sicil.key: value, firma.key: VariableValue("Firma", 0.97, 0, False)})


def _screen(qtbot, ctl, templates, engine=None):
    screen = DegerlerScreen(lambda: ctl, lambda: {t.id: t for t in templates.list()},
                            engine=engine)
    qtbot.addWidget(screen)
    screen.resize(1366, 700)
    screen.refresh()
    return screen


def _window(qtbot, tmp_path, kinds="ppp", prefs=True):
    store, job = _job(tmp_path, kinds)
    templates = TemplateStore(tmp_path / "tpl")
    win = MainWindow(store, templates, settings_path=tmp_path / "ayar.json",
                     prefs=Prefs(tmp_path / "p.ini") if prefs else None)
    qtbot.addWidget(win)
    return win, store, job, templates


# -- B-010 ------------------------------------------------------------------------------------
@pytest.mark.xfail(strict=True, reason="B-010: DegerlerScreen._fill resets the saved template "
                   "pick on the first job, so the one with most Kontrol values wins")
def test_b010_the_saved_template_pick_is_restored(qtbot, tmp_path):
    win, store, job, templates = _window(qtbot, tmp_path)
    first, sicil, firma = _template(templates, "Birinci")
    second, sicil2, firma2 = _template(templates, "Ikinci")
    win.yukle.open_job(store.load(job.id))
    ctl = win.controller()
    ctl.add_cut("b1/1")
    ctl.add_cut("b1/2")
    pids = ctl.job.ordered_page_ids()
    ctl.apply_template(pids[:2], first.id)
    ctl.apply_template(pids[2:], second.id)
    docs = ctl.documents()
    _values(ctl, first, sicil, firma, docs[0], GOOD)
    _values(ctl, first, sicil, firma, docs[1], BAD)  # "Birinci" has the value to check
    _values(ctl, second, sicil2, firma2, docs[2], GOOD)
    ctl.job_changed.emit()
    win.show_tab("degerler")
    win.degerler.template_combo.setCurrentIndex(win.degerler.template_combo.findData(second.id))
    assert win.degerler._template_id == second.id
    win.close()
    # next start: same prefs file, same job
    win2 = MainWindow(store, templates, settings_path=tmp_path / "ayar.json",
                      prefs=Prefs(tmp_path / "p.ini"))
    qtbot.addWidget(win2)
    win2.yukle.open_job(store.load(job.id))
    win2.show_tab("degerler")
    assert win2.degerler.template_combo.currentData() == second.id


# -- B-011 ------------------------------------------------------------------------------------
class BreakingEngine:
    """Reads 55555 for the first document, then raises something the reader does not expect."""
    name = "sahte"

    def __init__(self):
        self.calls = 0

    def available(self):
        return None

    def read_region(self, image):
        self.calls += 1
        if self.calls > 2:  # Sicil_No and Firma of the first document are one read each
            raise RuntimeError("beklenmedik")
        return Reading("55555", 0.99)


@pytest.mark.xfail(strict=True, reason="B-011: an unexpected reader error drops the values "
                   "already read (_read_failed never stores them; cancel does)")
def test_b011_values_read_before_an_unexpected_error_are_kept(qtbot, tmp_path):
    store, job = _job(tmp_path)
    ctl = JobController(store, job)
    templates = TemplateStore(tmp_path / "tpl")
    template, sicil, firma = _template(templates, "Kapasite Raporu")
    ctl.add_cut("b1/1")
    ctl.add_cut("b1/2")
    ctl.apply_template(ctl.job.ordered_page_ids(), template.id)
    ctl.job_changed.emit()
    engine = BreakingEngine()
    screen = _screen(qtbot, ctl, templates, engine=lambda: engine)
    screen.read_values(only_missing=False)
    qtbot.waitUntil(lambda: not screen.busy(), timeout=20000)
    assert engine.calls > 2  # the error really happened
    first = ctl.documents()[0]
    assert current_values(ctl.job, first) is not None
    assert current_values(ctl.job, first)[sicil.key].value == "55555"


# -- B-012 ------------------------------------------------------------------------------------
@pytest.mark.xfail(strict=True, reason="B-012: main_window drops the document number "
                   "(lambda _n: show_tab) so Değerler selects its own first value")
def test_b012_values_button_in_kontrol_selects_that_document(qtbot, tmp_path):
    win, store, job, templates = _window(qtbot, tmp_path, prefs=False)
    template, sicil, firma = _template(templates, "Kapasite Raporu")
    win.yukle.open_job(store.load(job.id))
    ctl = win.controller()
    ctl.add_cut("b1/1")
    ctl.add_cut("b1/2")
    ctl.apply_template(ctl.job.ordered_page_ids(), template.id)
    docs = ctl.documents()
    for doc, value in zip(docs, (GOOD, BAD, GOOD), strict=True):
        _values(ctl, template, sicil, firma, doc, value)  # Değerler would start at document 2
    ctl.job_changed.emit()
    win.resize(1366, 768)
    win.show()
    win.show_tab("kontrol")
    kontrol = win.kontrol
    kontrol.go_to_row(2)
    assert kontrol.current_document() == 3
    kontrol.open_in_values()
    assert win.degerler.current_value()[0] == 3


# -- B-013 ------------------------------------------------------------------------------------
@pytest.mark.xfail(strict=True, reason="B-013: _draw_variant calls sablon.set_example, which "
                   "always opens page 1, not the page the variable is read from")
def test_b013_variant_drawing_opens_the_variables_page(qtbot, tmp_path):
    win, store, job, templates = _window(qtbot, tmp_path, kinds="pppp", prefs=False)
    template, sicil, firma = _template(templates, "Kapasite Raporu", page=2)  # both read page 2
    win.yukle.open_job(store.load(job.id))
    ctl = win.controller()
    ctl.add_cut("b1/2")  # document 1 = pages 1-2, document 2 = pages 3-4
    ctl.apply_template(ctl.job.ordered_page_ids(), template.id)
    for doc in ctl.documents():
        _values(ctl, template, sicil, firma, doc, GOOD)
    ctl.job_changed.emit()
    win.resize(1366, 768)
    win.show()
    win._draw_variant(1, "Firma")
    assert win.sablon.page_number == 2


# -- B-014 ------------------------------------------------------------------------------------
@pytest.mark.xfail(strict=True, reason="B-014: a failed document is only a gap in the table; "
                   "Counts.unread_documents is never shown unless every document is unread")
def test_b014_a_failed_document_is_announced(qtbot, tmp_path):
    win, store, job, templates = _window(qtbot, tmp_path, prefs=False)
    template, sicil, firma = _template(templates, "Kapasite Raporu")
    win.yukle.open_job(store.load(job.id))
    ctl = win.controller()
    ctl.add_cut("b1/1")
    ctl.add_cut("b1/2")
    ctl.apply_template(ctl.job.ordered_page_ids(), template.id)
    docs = ctl.documents()
    for doc in docs[:2]:
        _values(ctl, template, sicil, firma, doc, GOOD)
    record_read_error(ctl.job, docs[2], template.id, "Tesseract durdu")  # document 3 failed
    ctl.job_changed.emit()
    win.resize(1366, 768)
    win.show()
    win.show_tab("degerler")
    screen = win.degerler
    texts = [i.accessibleName() for i in screen._status_items.values() if i.isVisible()]
    texts += [w.text() for w in screen.findChildren(QLabel) if w.isVisible()]
    assert any("okunmadı" in t.lower() or "okunamadı" in t.lower() for t in texts), texts


# -- B-015 ------------------------------------------------------------------------------------
def _sablon(qtbot, tmp_path, job_name="Kasım"):
    store, job = _job(tmp_path)
    job.name = job_name
    ctl = JobController(store, job)
    ctl.add_cut("b1/1")
    ctl.add_cut("b1/2")
    templates = TemplateStore(tmp_path / "tpl")
    template = templates.create("Kapasite Raporu")
    template.add_variable("Sicil_No", required=True)
    templates.save(template)
    screen = SablonScreen(templates, lambda: ctl, engine=lambda: None)
    qtbot.addWidget(screen)
    screen.resize(1366, 700)
    screen.open_template(template.id)
    screen.select_variable("Sicil_No")
    return screen, templates, template


@pytest.mark.xfail(strict=True, reason="B-015: Del on a chosen variable removes the whole "
                   "variable but the command is labelled Kutuyu sil (geri alınabilir)")
def test_b015_the_delete_command_names_what_it_deletes(qtbot, tmp_path):
    window, _store, _job_, templates = _window(qtbot, tmp_path, prefs=False)
    made = templates.create("Faaliyet")
    made.add_variable("Firma", required=True)
    templates.save(made)
    window.show_tab("sablonlar")
    screen = window.sablon
    screen.attach(window)
    screen.open_template(made.id)
    screen.select_variable("Firma")
    action = window.registry.action("sablonlar.kutu_sil")
    label = action.text().replace("&", "") + " " + action.toolTip()
    window.registry.action("sablonlar.kutu_sil").trigger()
    deleted_variable = screen.template.variables == []
    assert not deleted_variable or "Değişken" in label, label


# -- B-016 ------------------------------------------------------------------------------------
@pytest.mark.xfail(strict=True, reason="B-016: the inspector clamps X and width one by one, so "
                   "X + width can exceed the sheet and the box leaves it")
def test_b016_inspector_cannot_move_a_box_off_the_sheet(qtbot, tmp_path):
    screen, _templates, _template_ = _sablon(qtbot, tmp_path)
    screen.set_example(1)
    screen.add_box((10.0, 20.0, 60.0, 30.0))
    sheet_w, sheet_h = screen.canvas.page_mm()
    x, y, w, h = screen.side.spins
    w.setValue(sheet_w)  # the whole width
    x.setValue(sheet_w - 5.0)  # and then 5 mm from the right edge: x + w is far outside
    x0, y0, x1, y1 = screen.template.variable("Sicil_No").sections[0].box_mm
    assert x1 <= sheet_w + 0.01 and x0 >= 0


# -- B-017 ------------------------------------------------------------------------------------
@pytest.mark.xfail(strict=True, reason="B-017: SablonScreen.refresh_templates calls store.list() "
                   "without on_error, so a damaged template file is skipped silently")
def test_b017_a_damaged_template_file_is_reported(qtbot, tmp_path):
    screen, templates, _template_ = _sablon(qtbot, tmp_path)
    (templates.root / "abcdef1234.json").write_text("{ not json", encoding="utf-8")
    screen.refresh_templates()
    shown = [screen.message.text()] + [w.text() for w in screen.findChildren(QLabel)
                                       if w.isVisibleTo(screen)]
    assert any("abcdef1234" in t or "okunamadı" in t.lower() for t in shown), shown


# -- B-019 ------------------------------------------------------------------------------------
@pytest.mark.xfail(strict=True, reason="B-019: Section.example stores 'job name · Belge n · s.p' "
                   "and the export writes it into the shared template file")
def test_b019_exported_template_has_no_job_data(qtbot, tmp_path):
    screen, templates, template = _sablon(qtbot, tmp_path, job_name="GizliMusteriIsi")
    screen.select_variable("Sicil_No")
    screen.set_example(1)
    screen.add_box((10.0, 20.0, 60.0, 30.0))
    screen.flush_save()
    target = tmp_path / "disari.json"
    templates.export(template.id, target)
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["variables"], data
    assert "GizliMusteriIsi" not in target.read_text(encoding="utf-8")
