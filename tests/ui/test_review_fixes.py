"""Regression tests for the Plan 5 whole-branch review findings."""

import shutil
import threading

import pytest
from fakes import job_from_kinds, make_pdf, qr_page, text_page
from PIL import Image
from PySide6.QtCore import QItemSelectionModel
from PySide6.QtWidgets import QLineEdit, QMessageBox

from evrakci.pipeline.cuts import current_values, record_values
from evrakci.pipeline.exporting import export_job
from evrakci.pipeline.ocr.engine import Reading
from evrakci.pipeline.ocr.textlayer import TextLayerResult
from evrakci.pipeline.settings import DELETE_AFTER_EXPORT, Settings, save_settings
from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.model import Section
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.pipeline.templates.values import VariableValue
from evrakci.pipeline.writer import write_documents
from evrakci.ui import disa_aktar as disa_aktar_module
from evrakci.ui.controller import JobController
from evrakci.ui.degerler import DegerlerScreen
from evrakci.ui.disa_aktar import DisaAktarScreen
from evrakci.ui.kontrol import KontrolScreen
from evrakci.ui.thumbnails import ThumbnailService, job_renderer


def _real_job(tmp_path, name="İş", pages=None):
    pdf = make_pdf(tmp_path / f"{name}.pdf", pages or [text_page(), qr_page(), text_page()])
    store = JobStore(tmp_path / "jobs")
    return store, store.create_job(name, [pdf])


# 1. The export finishes on the job it started with.
def test_export_result_is_applied_to_the_exported_job_not_the_open_one(qtbot, tmp_path,
                                                                       monkeypatch):
    store, job_a = _real_job(tmp_path, "A")
    _, job_b = _real_job(tmp_path, "B")
    current = {"c": JobController(store, job_a)}
    gate = threading.Event()
    real = disa_aktar_module.export_job

    def held(*args, **kwargs):
        gate.wait(5)
        return real(*args, **kwargs)

    monkeypatch.setattr(disa_aktar_module, "export_job", held)
    save_settings(Settings(DELETE_AFTER_EXPORT), tmp_path / "ayar.json")
    screen = DisaAktarScreen(lambda: current["c"], dict, settings_path=tmp_path / "ayar.json")
    qtbot.addWidget(screen)
    screen.folder.setText(str(tmp_path / "out"))
    screen.layer.setChecked(False)
    with qtbot.waitSignal(screen.finished, timeout=30000):
        screen.export_button.click()
        current["c"] = JobController(store, job_b)  # the user opens job B meanwhile
        gate.set()
    assert not screen.busy()
    ids = {j.id for j in store.list_jobs()}
    assert job_b.id in ids  # B is never deleted
    assert job_a.id not in ids  # A was exported in full with no checks, so it goes


# 2. The worker exports a copy of the job, never the live one.
def test_export_works_on_a_copy_of_the_job(qtbot, tmp_path, monkeypatch):
    store, job = _real_job(tmp_path)
    ctl = JobController(store, job)
    seen = []

    def spy(job_arg, *args, **kwargs):
        seen.append(job_arg)
        return export_job(job_arg, *args, **kwargs)

    monkeypatch.setattr(disa_aktar_module, "export_job", spy)
    screen = DisaAktarScreen(lambda: ctl, dict, settings_path=tmp_path / "ayar.json")
    qtbot.addWidget(screen)
    screen.folder.setText(str(tmp_path / "out"))
    screen.layer.setChecked(False)
    with qtbot.waitSignal(screen.finished, timeout=30000):
        screen.export_button.click()
    assert seen and seen[0] is not ctl.job


# 3. Writing reports progress per document, so cancel stops between files.
def test_write_documents_reports_each_document(tmp_path):
    store, job = _real_job(tmp_path)
    from evrakci.pipeline.cuts import compute_documents

    calls = []
    write_documents(compute_documents(job), store.batch_files(job), {}, tmp_path / "out",
                    progress=lambda done, total: calls.append((done, total)))
    assert calls == [(1, 2), (2, 2)]


def test_cancelled_export_says_what_was_written_and_that_index_is_missing(qtbot, tmp_path,
                                                                          monkeypatch):
    store, job = _real_job(tmp_path, pages=[text_page(), qr_page(), text_page(),
                                            qr_page(), text_page()])
    ctl = JobController(store, job)
    screen = DisaAktarScreen(lambda: ctl, dict, settings_path=tmp_path / "ayar.json")
    qtbot.addWidget(screen)

    def cancelling(*args, progress=None, **kwargs):
        def report(stage, done, total):
            progress(stage, done, total)
            if done >= 1:
                screen.cancel()  # İptal pressed after the first file

        return export_job(*args, progress=report, **kwargs)

    monkeypatch.setattr(disa_aktar_module, "export_job", cancelling)
    screen.folder.setText(str(tmp_path / "out"))
    screen.layer.setChecked(False)
    with qtbot.waitSignal(screen.finished, timeout=30000):
        screen.export_button.click()
    text = screen.message.text()
    written = len(list((tmp_path / "out").glob("*.pdf")))
    assert 0 < written < 3
    assert f"{written} dosya yazıldı" in text and "index.xlsx yazılmadı" in text
    assert not (tmp_path / "out" / "index.xlsx").exists()


def test_closing_during_export_waits_for_it_to_stop(qtbot, tmp_path, monkeypatch):
    from evrakci.ui.main_window import MainWindow

    window = MainWindow(JobStore(tmp_path / "jobs"), TemplateStore(tmp_path / "tpl"),
                        settings_path=tmp_path / "ayar.json")
    qtbot.addWidget(window)
    window.show()
    window.disa_aktar.task = object()
    stopped = []
    window.disa_aktar.cancel = lambda: stopped.append(1)
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    assert window.close() is False  # not yet: the export must stop first
    assert stopped and window.isVisible()
    window.disa_aktar.task = None
    window.disa_aktar.finished.emit()
    qtbot.waitUntil(lambda: not window.isVisible(), timeout=3000)


def test_closing_asks_while_values_are_being_read(qtbot, tmp_path, monkeypatch):
    from evrakci.ui.main_window import MainWindow

    window = MainWindow(JobStore(tmp_path / "jobs"), TemplateStore(tmp_path / "tpl"),
                        settings_path=tmp_path / "ayar.json")
    qtbot.addWidget(window)
    window.degerler.task = object()
    asked = []
    monkeypatch.setattr(QMessageBox, "question",
                        lambda *a, **k: asked.append(1) or QMessageBox.StandardButton.No)
    assert window.close() is False and asked
    window.degerler.task = None


# 4 / 5. Reading values never loses the user's work.
@pytest.fixture
def values_setup(qtbot, tmp_path):
    store, job = _real_job(tmp_path, pages=[text_page(), text_page()])
    ctl = JobController(store, job)
    ctl.add_cut(job.ordered_page_ids()[1])
    templates = TemplateStore(tmp_path / "tpl")
    template = templates.create("Rapor")
    variable = template.add_variable("Sicil_No", required=True)
    template.add_section("Sicil_No", Section(1, (10, 10, 60, 20)))
    template.set_pattern("{Sicil_No}")
    templates.save(template)
    ctl.apply_template(job.ordered_page_ids(), template.id)
    for doc in ctl.documents():
        record_values(ctl.job, doc, template.id,
                      {variable.key: VariableValue("", 0.0, None, True, "48213", (), False)})
    ctl.job_changed.emit()
    return ctl, templates, template, variable


class Unavailable:
    name = "yok"

    def available(self):
        return "Tesseract programı bulunamadı"


def test_read_with_no_engine_refuses_and_keeps_corrections(qtbot, values_setup):
    ctl, templates, _, variable = values_setup
    screen = DegerlerScreen(lambda: ctl, lambda: {t.id: t for t in templates.list()},
                            engine=Unavailable)
    qtbot.addWidget(screen)
    screen.refresh()
    doc = ctl.documents()[0]
    ctl.set_value(doc, variable.key, "11111")
    screen.read_button.click()
    assert not screen.busy()
    assert "Tesseract" in screen.progress_label.text()
    assert current_values(ctl.job, doc)[variable.key].value == "11111"


class Slow:
    name = "yavas"

    def __init__(self, gate):
        self.gate = gate

    def available(self):
        return None

    def read_region(self, image):
        self.gate.wait(5)
        return Reading("99999", 0.9)


def test_text_being_typed_survives_a_read_finishing(qtbot, values_setup):
    ctl, templates, _, variable = values_setup
    gate = threading.Event()
    screen = DegerlerScreen(lambda: ctl, lambda: {t.id: t for t in templates.list()},
                            engine=lambda: Slow(gate))
    qtbot.addWidget(screen)
    screen.only_checks.setChecked(False)
    screen.read_button.click()
    cell = screen.table.item(0, screen.column_of("Sicil_No"))
    screen.table.setCurrentItem(cell)
    screen.table.editItem(cell)
    editor = screen.table.findChild(QLineEdit)
    editor.setText("55555")
    gate.set()
    qtbot.waitUntil(lambda: not screen.busy(), timeout=20000)
    assert current_values(ctl.job, ctl.documents()[0])[variable.key].value == "55555"


def test_cancelled_read_keeps_what_was_read(qtbot, values_setup):
    ctl, templates, _, variable = values_setup
    gate = threading.Event()
    screen = DegerlerScreen(lambda: ctl, lambda: {t.id: t for t in templates.list()},
                            engine=lambda: Slow(gate))
    qtbot.addWidget(screen)
    screen.read_button.click()
    gate.set()
    qtbot.waitUntil(lambda: screen.read_count() >= 1, timeout=20000)
    screen.cancel()
    qtbot.waitUntil(lambda: not screen.busy(), timeout=20000)
    values = [current_values(ctl.job, d)[variable.key].value for d in ctl.documents()]
    assert "99999" in values


def test_stale_reading_is_dropped_when_the_template_changed(qtbot, values_setup):
    ctl, templates, _, variable = values_setup
    gate = threading.Event()
    other = templates.create("Başka")
    templates.save(other)
    screen = DegerlerScreen(lambda: ctl, lambda: {t.id: t for t in templates.list()},
                            engine=lambda: Slow(gate))
    qtbot.addWidget(screen)
    screen.read_button.click()
    ctl.apply_template(ctl.job.ordered_page_ids(), other.id)  # changed while reading
    gate.set()
    qtbot.waitUntil(lambda: not screen.busy(), timeout=20000)
    assert all(current_values(ctl.job, d) is None for d in ctl.documents())


def test_side_panel_clears_for_a_cell_without_a_value(qtbot, values_setup):
    ctl, templates, _, _ = values_setup
    screen = DegerlerScreen(lambda: ctl, lambda: {t.id: t for t in templates.list()})
    qtbot.addWidget(screen)
    screen.only_checks.setChecked(False)
    screen.table.setCurrentCell(0, screen.column_of("Sicil_No"))
    assert screen.side.suggestion.text() == "48213"
    screen.side.show_nothing()
    assert screen.side.suggestion.text() == "" and screen.side.read.text() == ""


# 6. Rotating refreshes the thumbnail; stale renders are thrown away.
class Counting:
    def __init__(self):
        self.calls = []

    def __call__(self, pid, height):
        self.calls.append(pid)
        return Image.new("RGB", (70, height), "white")


def test_rotating_drops_the_cached_thumbnail(qtbot, tmp_path):
    job = job_from_kinds({"a": "ppp"})
    store = JobStore(tmp_path)
    store.save(job)
    ctl = JobController(store, job)
    service = ThumbnailService(Counting(), height=50)
    screen = KontrolScreen(ctl, service)
    qtbot.addWidget(screen)
    screen.show()
    qtbot.waitUntil(lambda: "a/1" in service.cache, timeout=5000)
    screen.timeline.setCurrentIndex(screen.model.index(1))
    screen.rotate_button.click()
    assert "a/1" not in service.cache or service.calls.count("a/1") >= 2


def test_a_render_started_before_invalidate_is_not_cached(qtbot):
    gate = threading.Event()

    def slow(pid, height):
        gate.wait(5)
        return Image.new("RGB", (10, height), "white")

    service = ThumbnailService(slow, height=20, workers=1)
    service.request("a/0")
    service.invalidate("a/0")
    gate.set()
    qtbot.waitUntil(service.idle, timeout=5000)
    qtbot.wait(50)
    assert "a/0" not in service.cache


def test_stop_forgets_pending_work(qtbot):
    service = ThumbnailService(Counting(), height=20)
    service.stop()
    assert service.idle()


# 7. Actions on a selection are one edit, and edits keep the selection.
def test_rotating_a_selection_is_one_undo_step_and_keeps_the_selection(qtbot, tmp_path):
    job = job_from_kinds({"a": "pppp"})
    store = JobStore(tmp_path)
    store.save(job)
    ctl = JobController(store, job)
    screen = KontrolScreen(ctl, None)
    qtbot.addWidget(screen)
    selection = screen.timeline.selectionModel()
    for row in (1, 2, 3):
        selection.select(screen.model.index(row), QItemSelectionModel.SelectionFlag.Select)
    screen.timeline.selectionModel().setCurrentIndex(
        screen.model.index(2), QItemSelectionModel.SelectionFlag.NoUpdate)
    screen.rotate_button.click()
    assert set(ctl.job.rotations) == {"a/1", "a/2", "a/3"}
    assert screen.timeline.currentIndex().row() == 2
    assert {i.row() for i in selection.selectedIndexes()} == {1, 2, 3}
    ctl.undo()
    assert ctl.job.rotations == {}


# 8. Thumbnails follow batches added later.
def test_renderer_finds_batches_added_after_it_was_made(tmp_path):
    pdf = make_pdf(tmp_path / "b1.pdf", [text_page()])
    job = job_from_kinds({"b1": "p"})
    files = {"b1": pdf}
    render = job_renderer(job, lambda: files)
    later = make_pdf(tmp_path / "b2.pdf", [text_page()])
    files["b2"] = later
    assert render("b2/0", 40).height == 40


# 9. Background work never edits the live job.
def test_adding_a_batch_keeps_edits_made_while_it_was_analysed(qtbot, tmp_path, monkeypatch):
    from evrakci.ui.yukle import YukleScreen

    store, job = _real_job(tmp_path, pages=[text_page(), text_page()])
    screen = YukleScreen(store)
    qtbot.addWidget(screen)
    screen.open_job(job)
    screen.controller.rotate(job.ordered_page_ids()[0], 90)
    gate = threading.Event()
    real = store.prepare_batch

    def held(job_arg, path):
        gate.wait(5)
        return real(job_arg, path)

    monkeypatch.setattr(store, "prepare_batch", held)
    extra = make_pdf(tmp_path / "ek.pdf", [text_page()])
    with qtbot.waitSignal(screen.task_finished, timeout=20000):
        screen.add_batch(extra)
        qtbot.wait(50)
        screen.controller.undo()  # undo the rotation while the new batch is analysed
        gate.set()
    live = screen.controller.job
    assert len(live.batches) == 2
    assert live.rotations == {}
    saved = store.load(live.id)
    assert len(saved.batches) == 2 and saved.rotations == {}


# Minor: the text-layer note keeps whether the file is PDF/A.
def test_export_notes_keep_the_pdfa_flag(tmp_path):
    store, job = _real_job(tmp_path, pages=[text_page()])

    class Ok:
        def available(self):
            return None

    def plain(src, dst, tessdata=None, **kwargs):
        shutil.copy(src, dst)
        return TextLayerResult(dst, False, None)

    result = export_job(job, store.batch_files(job), {}, tmp_path / "out", engine=Ok(),
                        add_layer=plain)
    assert list(result.notes.values()) == [(False, None)]


def test_another_job_cannot_be_opened_while_work_runs(qtbot, tmp_path):
    from evrakci.ui.main_window import MainWindow

    store, job_a = _real_job(tmp_path, "A")
    _, job_b = _real_job(tmp_path, "B")
    window = MainWindow(store, TemplateStore(tmp_path / "tpl"),
                        settings_path=tmp_path / "ayar.json")
    qtbot.addWidget(window)
    window.yukle.open_job(job_a)
    window.disa_aktar.task = object()
    window.yukle.open_job(job_b)
    assert window.yukle.controller.job.id == job_a.id
    assert "sürüyor" in window.message.text()
    window.disa_aktar.task = None
