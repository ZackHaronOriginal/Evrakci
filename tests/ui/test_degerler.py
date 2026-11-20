"""Değerler (direction A): the values table linked to the page crop, the Kontrol queue
(Enter = accept and go on, Tab = next value, F2 / Esc), Tümünü incele, Örnek kontrol, bulk
accept with undo, empty states, persistence and the window wiring."""

import threading

import pytest
from fakes import job_from_kinds, make_pdf, text_page
from PySide6.QtCore import QByteArray, QEvent, QPointF, Qt
from PySide6.QtGui import QFontMetrics, QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QAbstractButton, QApplication, QComboBox, QLabel, QLineEdit, QWidget

from evrakci.pipeline.cuts import current_values, record_values
from evrakci.pipeline.ocr.engine import Reading
from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.model import Section
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.pipeline.templates.values import SectionReading, VariableValue
from evrakci.ui.controller import JobController
from evrakci.ui.degerler import DegerlerScreen, build_rows_fast
from evrakci.ui.degerler_model import build_rows
from evrakci.ui.prefs import Prefs

GOOD = VariableValue("48197", 0.95, 0, False)
BAD = VariableValue("", 0.0, None, True, "48213",
                    (SectionReading(0, "482I3", 0.41), SectionReading(1, "48213", 0.55)))


def _job(tmp_path, pages=3):
    pdf = make_pdf(tmp_path / "b1.pdf", [text_page(c) for c in "ABCDEF"[:pages]])
    store = JobStore(tmp_path / "jobs")
    job = job_from_kinds({"b1": "p" * pages})
    target = store.batch_file(job, job.batches[0])
    target.parent.mkdir(parents=True)
    target.write_bytes(pdf.read_bytes())
    store.save(job)
    return store, job


def _template(tmp_path):
    templates = TemplateStore(tmp_path / "tpl")
    template = templates.create("Kapasite Raporu")
    sicil = template.add_variable("Sicil_No", required=True)
    firma = template.add_variable("Firma")
    template.add_section("Sicil_No", Section(1, (10, 10, 60, 20)))
    template.add_section("Sicil_No", Section(1, (10, 10, 60, 20)))
    template.add_section("Firma", Section(1, (10, 30, 90, 40)))
    template.set_pattern("{Sicil_No}")
    templates.save(template)
    return templates, template, sicil, firma


def _fill(ctl, template, sicil, firma, values=(GOOD, BAD, GOOD)):
    ctl.add_cut("b1/1")
    ctl.add_cut("b1/2")
    ctl.apply_template(ctl.job.ordered_page_ids(), template.id)
    for n, (doc, value) in enumerate(zip(ctl.documents(), values, strict=True)):
        record_values(ctl.job, doc, template.id,
                      {sicil.key: value, firma.key: VariableValue(f"Firma {n}", 0.97, 0, False)})
    ctl.job_changed.emit()


@pytest.fixture
def setup(qtbot, tmp_path):
    store, job = _job(tmp_path)
    ctl = JobController(store, job)
    templates, template, sicil, firma = _template(tmp_path)
    _fill(ctl, template, sicil, firma)
    return ctl, templates, template, sicil


def _screen(qtbot, ctl, templates, engine=None):
    screen = DegerlerScreen(lambda: ctl, lambda: {t.id: t for t in templates.list()}, engine=engine)
    qtbot.addWidget(screen)
    screen.resize(1366, 700)
    screen.refresh()
    return screen


def _value(ctl, n, key):
    return current_values(ctl.job, ctl.documents()[n])[key]


# -- views, counts, search ----------------------------------------------------------------
def test_views_show_their_rows_and_value_counts(qtbot, setup):
    ctl, templates, _, _ = setup
    screen = _screen(qtbot, ctl, templates)
    assert screen.view() == "tumu" and screen.model.rowCount() == 3
    counts = {v: i.count for v, i in screen.selector.items.items()}
    assert counts["kontrol"] == 1 and counts["tumu"] == 6 and counts["incelenmemis"] == 6
    screen.set_view("kontrol")
    assert screen.model.rowCount() == 1
    assert screen.model.row_at(0).number == 2
    assert screen.selector.items["kontrol"].accessibleName() == "Kontrol gerekenler: 1 değer"


def test_the_first_kontrol_value_is_current_and_described(qtbot, setup):
    ctl, templates, _, sicil = setup
    screen = _screen(qtbot, ctl, templates)
    assert screen.current_value() == (2, sicil.key)
    card = screen.side.value
    assert card.read.text == "482I3" and card.read.marks == (3,)  # the I is uncertain
    assert card.suggestion.text == "48213" and card.suggestion.marks == (3,)
    assert card.level.level == "kontrol" and card.level.percent == 55
    assert "1 karakter belirsiz" in card.level.accessibleName()
    assert card.why.text() == "Varyant 2 ile okundu: I yerine 1."
    assert screen.side.source.title.text() == "Sicil No"
    assert screen.side.source.meta.text() == "Belge 2, sayfa 2"


def test_search_filters_and_its_empty_state_clears_it(qtbot, setup):
    ctl, templates, _, _ = setup
    screen = _screen(qtbot, ctl, templates)
    screen.search.setText("firma 2")
    assert screen.model.rowCount() == 1 and screen.model.row_at(0).number == 3
    screen.search.setText("yok böyle")
    assert screen.model.rowCount() == 0 and not screen.empty.isHidden()
    assert screen.empty.title.text() == "Aramayla eşleşen değer yok"
    screen.empty.primary.click()
    assert screen.search.text() == "" and screen.model.rowCount() == 3


def test_the_search_hint_names_the_template_s_words(qtbot, setup):
    ctl, templates, _, _ = setup
    screen = _screen(qtbot, ctl, templates)
    assert screen.search.placeholderText() == "Firma, sicil no ara"
    assert screen.template_combo.currentText() == "Kapasite Raporu"


def test_sorting_by_a_column(qtbot, setup):
    ctl, templates, _, _ = setup
    screen = _screen(qtbot, ctl, templates)
    guven = len(screen.model.columns) - 1
    screen.table.sortByColumn(guven, Qt.SortOrder.AscendingOrder)
    assert screen.model.row_at(0).number == 2  # Kontrol first
    screen.table.sortByColumn(1, Qt.SortOrder.DescendingOrder)
    assert [screen.model.row_at(r).number for r in range(3)] == [3, 2, 1]


def test_fast_rows_match_the_core_lookups(setup):
    ctl, templates, _, _ = setup
    by_id = {t.id: t for t in templates.list()}
    fast = build_rows_fast(ctl.job, ctl.documents(), by_id)
    slow = build_rows(ctl.job, ctl.documents(), by_id)
    assert [(r.number, r.cells, r.first, r.last) for r in fast] == \
        [(r.number, r.cells, r.first, r.last) for r in slow]


# -- fixing values --------------------------------------------------------------------------
def test_enter_accepts_and_moves_to_the_next_kontrol(qtbot, tmp_path):
    store, job = _job(tmp_path)
    ctl = JobController(store, job)
    templates, template, sicil, firma = _template(tmp_path)
    _fill(ctl, template, sicil, firma, values=(BAD, GOOD, BAD))
    screen = _screen(qtbot, ctl, templates)
    assert screen.current_value() == (1, sicil.key)
    screen.table.setFocus()
    QTest.keyClick(screen.table, Qt.Key.Key_Return)
    value = _value(ctl, 0, sicil.key)
    assert value.value == "48213" and value.edited and not value.flagged
    assert screen.current_value() == (3, sicil.key)
    assert ctl.undo_stack.undoText() == "Öneriyi kabul et"


def test_accepting_in_the_kontrol_view_moves_to_the_row_that_takes_its_place(qtbot, tmp_path):
    store, job = _job(tmp_path)
    ctl = JobController(store, job)
    templates, template, sicil, firma = _template(tmp_path)
    _fill(ctl, template, sicil, firma, values=(BAD, GOOD, BAD))
    screen = _screen(qtbot, ctl, templates)
    screen.set_view("kontrol")
    screen.select_value(1, sicil.key)
    screen.accept_current()
    assert screen.model.rowCount() == 1
    assert screen.current_value() == (3, sicil.key)


def test_onayla_on_an_emin_value_marks_it_reviewed_and_keeps_its_confidence(qtbot, setup):
    ctl, templates, _, sicil = setup
    screen = _screen(qtbot, ctl, templates)
    screen.select_value(1, sicil.key)
    screen.side.accept_button.click()
    value = _value(ctl, 0, sicil.key)
    assert value.edited and value.value == "48197" and value.confidence == 0.95
    assert screen.model.row_at(0).cell(sicil.key).reviewed


def test_f2_edits_in_place_and_enter_stores_and_moves_on(qtbot, tmp_path):
    store, job = _job(tmp_path)
    ctl = JobController(store, job)
    templates, template, sicil, firma = _template(tmp_path)
    _fill(ctl, template, sicil, firma, values=(BAD, GOOD, BAD))
    screen = _screen(qtbot, ctl, templates)
    screen.show()
    screen.type_current()
    editor = screen.table.open_editor_widget()
    assert editor is not None and editor.text() == "48213"  # starts at the suggestion
    assert not editor.hasSelectedText() and editor.cursorPosition() == 5
    assert screen.table.hint.isVisible()
    assert "Enter onayla, sonraki kontrol" in screen.table.hint.accessibleName()
    editor.setText("48299")
    editor.setModified(True)
    QTest.keyClick(editor, Qt.Key.Key_Return)
    qtbot.waitUntil(lambda: not screen.table.is_editing())
    qtbot.waitUntil(lambda: _value(ctl, 0, sicil.key).value == "48299")
    assert _value(ctl, 0, sicil.key).edited
    qtbot.waitUntil(lambda: screen.current_value() == (3, sicil.key))


def test_esc_in_the_editor_drops_the_change(qtbot, setup):
    ctl, templates, _, sicil = setup
    screen = _screen(qtbot, ctl, templates)
    screen.show()
    screen.type_current()
    editor = screen.table.open_editor_widget()
    QTest.keyClicks(editor, "99")
    QTest.keyClick(editor, Qt.Key.Key_Escape)
    qtbot.waitUntil(lambda: not screen.table.is_editing())
    assert _value(ctl, 1, sicil.key).flagged and _value(ctl, 1, sicil.key).value == ""


def test_tab_moves_from_value_to_value(qtbot, setup):
    ctl, templates, _, sicil = setup
    screen = _screen(qtbot, ctl, templates)
    screen.show()
    screen.select_value(1, sicil.key)
    screen.table.setFocus()
    firma = screen.rows[0].cells[1].key
    QTest.keyClick(screen.table, Qt.Key.Key_Tab)
    assert screen.current_value() == (1, firma)
    QTest.keyClick(screen.table, Qt.Key.Key_Tab)
    assert screen.current_value() == (2, sicil.key)
    QTest.keyClick(screen.table, Qt.Key.Key_Backtab)
    assert screen.current_value() == (1, firma)


def test_tab_from_an_untouched_editor_does_not_accept(qtbot, setup):
    ctl, templates, _, sicil = setup
    screen = _screen(qtbot, ctl, templates)
    screen.show()
    screen.type_current()  # the Kontrol value of document 2
    editor = screen.table.open_editor_widget()
    QTest.keyClick(editor, Qt.Key.Key_Tab)
    qtbot.wait(50)
    assert _value(ctl, 1, sicil.key).flagged


def test_editing_a_cell_stores_an_edited_value(qtbot, setup):
    ctl, templates, _, sicil = setup
    screen = _screen(qtbot, ctl, templates)
    index = screen.cell(1, "Sicil_No")
    assert screen.model.setData(index, "48190")
    value = _value(ctl, 0, sicil.key)
    assert value.value == "48190" and value.edited


def test_okunamadi_opens_the_editor_instead_of_accepting(qtbot, tmp_path):
    store, job = _job(tmp_path)
    ctl = JobController(store, job)
    templates, template, sicil, firma = _template(tmp_path)
    empty = VariableValue("", 0.0, None, True, "", (SectionReading(0, "", 0.0),))
    _fill(ctl, template, sicil, firma, values=(GOOD, empty, GOOD))
    screen = _screen(qtbot, ctl, templates)
    screen.show()
    row = screen.model.row_at(1)
    assert row.level == "okunamadi" and screen.model.data(screen.cell(2, "Sicil_No")) == "boş"
    screen.accept_current()
    assert screen.table.is_editing()


def test_accept_selected_is_one_step_with_a_count(qtbot, setup):
    ctl, templates, _, sicil = setup
    screen = _screen(qtbot, ctl, templates)
    said = []
    screen.status.connect(said.append)
    screen.select_all()
    screen.accept_selected()
    assert said[-1] == "6 değer onaylandı"
    assert all(_value(ctl, n, sicil.key).edited for n in range(3))
    assert ctl.undo_stack.undoText() == "6 değeri onayla"
    ctl.undo()
    assert _value(ctl, 1, sicil.key).flagged


def test_next_and_previous_kontrol_wrap(qtbot, tmp_path):
    store, job = _job(tmp_path)
    ctl = JobController(store, job)
    templates, template, sicil, firma = _template(tmp_path)
    _fill(ctl, template, sicil, firma, values=(BAD, GOOD, BAD))
    screen = _screen(qtbot, ctl, templates)
    screen.next_check()
    assert screen.current_value() == (3, sicil.key)
    screen.next_check()
    assert screen.current_value() == (1, sicil.key)
    screen.next_check(-1)
    assert screen.current_value() == (3, sicil.key)


def test_review_all_steps_through_every_unreviewed_value(qtbot, setup):
    ctl, templates, _, sicil = setup
    screen = _screen(qtbot, ctl, templates)
    screen.set_review_all(True)
    assert screen.view() == "incelenmemis"
    firma = screen.rows[0].cells[1].key
    assert screen.current_value() == (1, sicil.key)
    screen.accept_current()
    assert screen.current_value() == (1, firma)  # an Emin value too
    screen.set_review_all(False)
    assert screen.view() == "tumu"


def test_sample_checks_emin_values_and_an_error_sends_the_variable_to_kontrol(qtbot, tmp_path):
    store, job = _job(tmp_path, pages=6)
    ctl = JobController(store, job)
    templates, template, sicil, firma = _template(tmp_path)
    for pid in ("b1/1", "b1/2", "b1/3", "b1/4", "b1/5"):
        ctl.add_cut(pid)
    ctl.apply_template(ctl.job.ordered_page_ids(), template.id)
    for n, doc in enumerate(ctl.documents()):
        record_values(ctl.job, doc, template.id,
                      {sicil.key: VariableValue(f"4819{n}", 0.95, 0, False),
                       firma.key: VariableValue(f"Firma {n}", 0.97, 0, False)})
    ctl.job_changed.emit()
    screen = _screen(qtbot, ctl, templates)
    screen.set_sample(True)
    assert screen.view() == "ornek" and screen.model.rowCount() == 12
    assert screen.selector.items["ornek"].isVisibleTo(screen)
    assert [c.title for c in screen.model.columns][3:5] == ["Değişken", "Okunan değer"]
    first = screen.model.items[0]
    screen.accept_current()
    assert first[0].cell(first[1].key).reviewed or _value(
        ctl, first[0].number - 1, first[1].key).edited
    # A wrong sample value: corrected, and its variable's other values go to Kontrol
    row, cell = next((r, c) for r, c in screen.model.items if c.key == sicil.key
                     and not c.reviewed)
    screen.model.setData(screen.model.value_index(row.number, cell.key), "00000")
    flagged = [_value(ctl, n, sicil.key).flagged for n in range(6)]
    assert _value(ctl, row.number - 1, sicil.key).value == "00000"
    assert sum(flagged) >= 1 and not flagged[row.number - 1]
    screen.refresh()
    assert screen._sample_errors() == 1
    screen.set_sample(False)
    assert screen.view() == "tumu" and screen.selector.items["ornek"].isHidden()


# -- empty states ---------------------------------------------------------------------------
def test_values_not_read_yet(qtbot, tmp_path):
    store, job = _job(tmp_path)
    ctl = JobController(store, job)
    templates, template, _, _ = _template(tmp_path)
    ctl.add_cut("b1/1")
    ctl.apply_template(ctl.job.ordered_page_ids(), template.id)
    screen = _screen(qtbot, ctl, templates)
    assert screen.model.rowCount() == 0 and not screen.empty.isHidden()
    assert screen.empty.title.text() == "Değerler henüz okunmadı"
    assert screen.empty.text.text() == "Okuyunca sicil no ve firma burada listelenir."
    assert screen.empty.primary.text().strip() == "2 belgeyi oku"
    assert screen.empty.secondary.text().strip() == "Şablonlar'a git"
    assert screen.side.source.title.text() == "Değer seçilmedi"
    assert not screen.side.accept_button.isEnabled()
    assert not screen.search.isEnabled() and not screen.missing_button.isEnabled()
    assert screen.read_button.isEnabled()


def test_no_job_and_no_template(qtbot, tmp_path):
    templates = TemplateStore(tmp_path / "tpl")
    screen = DegerlerScreen(lambda: None, lambda: {})
    qtbot.addWidget(screen)
    gone = []
    screen.go_tab.connect(gone.append)
    assert screen.empty.title.text() == "Henüz açık iş yok"
    screen.empty.primary.click()
    assert gone == ["yukle"]
    store, job = _job(tmp_path)
    ctl = JobController(store, job)
    screen = _screen(qtbot, ctl, templates)
    assert screen.empty.title.text() == "Şablonlu belge yok"


def test_an_empty_kontrol_view_offers_tumu(qtbot, tmp_path):
    store, job = _job(tmp_path)
    ctl = JobController(store, job)
    templates, template, sicil, firma = _template(tmp_path)
    _fill(ctl, template, sicil, firma, values=(GOOD, GOOD, GOOD))
    screen = _screen(qtbot, ctl, templates)
    screen.set_view("kontrol")
    assert screen.empty.title.text() == "Kontrol bekleyen değer yok"
    screen.empty.primary.click()
    assert screen.view() == "tumu" and screen.model.rowCount() == 3


# -- the crop, linked both ways -----------------------------------------------------------
def test_crop_follows_the_table_and_a_box_click_selects_the_value(qtbot, setup):
    ctl, templates, _, sicil = setup
    screen = _screen(qtbot, ctl, templates)
    crop = screen.side.source.view.crop
    assert crop.pid == "b1/1" and crop.box == (10, 10, 60, 20)
    firma = screen.rows[0].cells[1].key
    assert [o[0] for o in crop.others] == [firma]
    screen.side.source.view.box_clicked.emit(firma)
    assert screen.current_value() == (2, firma)
    qtbot.waitUntil(lambda: screen.images.get("b1/1", screen.side.source.view._dpi())
                    is not None, timeout=5000)


def test_space_shows_the_whole_page_and_toggles_it_off(qtbot, setup):
    ctl, templates, _, _ = setup
    screen = _screen(qtbot, ctl, templates)
    screen.show()
    screen.toggle_whole_page()
    assert screen.loupe is not None and screen.loupe.is_open()
    screen.dismiss()
    qtbot.waitUntil(lambda: not screen.loupe.isVisible(), timeout=2000)


# -- accessibility --------------------------------------------------------------------------
def test_every_control_has_a_name(qtbot, setup):
    ctl, templates, _, _ = setup
    screen = _screen(qtbot, ctl, templates)
    screen.show()
    for widget in screen.findChildren(QWidget):
        if not widget.isVisible() or widget.focusPolicy() == Qt.FocusPolicy.NoFocus:
            continue
        if isinstance(widget, QAbstractButton | QLineEdit | QComboBox):
            name = widget.accessibleName() or (
                widget.text() if isinstance(widget, QAbstractButton) else "")
            assert name.strip(), type(widget).__name__
    assert screen.table.accessibleName() == "Değerler tablosu"
    spoken = screen.model.data(screen.cell(2, "Sicil_No"), Qt.ItemDataRole.AccessibleTextRole)
    assert spoken == "Sicil No: 482I3, Kontrol, 1 karakter belirsiz"


# -- reading (kept from before) ------------------------------------------------------------
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
    screen.read_button.click()
    assert screen.busy() and screen.cancel_button.isVisibleTo(screen)
    screen.model.setData(screen.cell(1, "Sicil_No"), "12345")  # while the read runs
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
    assert screen.progress_label.text() == "3 belge okundu."


# -- in the window: actions, status bar, toast, persistence ---------------------------------
@pytest.fixture
def window(qtbot, tmp_path):
    from evrakci.ui.main_window import MainWindow

    store, job = _job(tmp_path)
    templates, template, sicil, firma = _template(tmp_path)
    prefs = Prefs(tmp_path / "p.ini")
    win = MainWindow(store, templates, settings_path=tmp_path / "ayar.json", prefs=prefs)
    qtbot.addWidget(win)
    with qtbot.waitSignal(win.yukle.job_opened, timeout=10000):
        win.yukle.open_job(store.load(job.id))
    _fill(win.controller(), template, sicil, firma)
    win.resize(1366, 768)
    win.show()
    win.show_tab("degerler")
    qtbot.waitUntil(lambda: win.degerler.window_ is win)
    win.activateWindow()
    qtbot.waitUntil(win.isActiveWindow)  # activation is asynchronous; the N / Enter keys need it
    return win, sicil


def test_window_actions_are_wired_and_enabled_when_usable(window):
    win, _ = window
    r = win.registry
    for action_id in ("degerler.onayla", "degerler.elle_yaz", "degerler.varyant",
                      "degerler.vazgec", "degerler.tumunu_sec", "degerler.tum_sayfa",
                      "degerler.sonraki_kontrol", "degerler.onceki_kontrol",
                      "degerler.tumunu_incele", "degerler.ornek_kontrol", "degerler.oku",
                      "degerler.eksikleri_oku"):
        assert r.is_enabled(action_id), action_id
    assert not r.is_enabled("degerler.durdur")  # nothing is being read
    win.degerler.table.selectRow(0)
    assert r.is_enabled("degerler.secilenleri_onayla")
    r.action("degerler.ornek_kontrol").trigger()
    assert win.degerler.view() == "ornek" and r.action("degerler.ornek_kontrol").isChecked()
    win.degerler.set_view("tumu")
    assert not r.action("degerler.ornek_kontrol").isChecked()
    assert win.zoom_controller("degerler") is win.degerler.zoom


def test_status_slot_counts(window):
    win, _ = window
    items = win.degerler._status_items
    assert items["doc"].accessibleName() == "Belge 2 / 3"
    assert items["kontrol"].accessibleName() == "1 değer kontrol bekliyor"
    assert items["seen"].accessibleName() == "0 / 6 incelendi"
    assert items["bad"].isHidden()


def test_bulk_accept_shows_a_toast_with_undo(qtbot, window):
    win, sicil = window
    screen = win.degerler
    screen.select_all()
    win.registry.action("degerler.secilenleri_onayla").trigger()
    assert win.toaster.current_text() == "6 değer onaylandı"
    toast = win.toaster._current
    undo = next(b for b in toast.findChildren(QAbstractButton) if b.text() == "Geri al")
    undo.click()
    assert current_values(win.controller().job, win.controller().documents()[1])[
        sicil.key].flagged


def test_old_toast_never_undoes_a_newer_step_after_ctrl_z(qtbot, window):
    """B-023 on Değerler: the toast's Geri al is bound to its own step (index and command), so
    after Ctrl+Z and a new edit at the same index it must not undo the new edit."""
    win, sicil = window
    screen, ctl = win.degerler, win.controller()
    screen.select_all()
    win.registry.action("degerler.secilenleri_onayla").trigger()
    toast = win.toaster._current
    buttons = [b for b in toast.findChildren(QAbstractButton) if b.text() == "Geri al"]
    assert buttons
    ctl.undo_stack.undo()  # Ctrl+Z
    index = ctl.undo_stack.index()
    from evrakci.pipeline.review import set_value

    document = ctl.documents()[0]
    ctl.run("başka bir adım", lambda job: set_value(job, document, sicil.key, "999"))
    assert ctl.undo_stack.index() == index + 1
    for button in buttons:
        button.click()
    assert ctl.undo_stack.index() == index + 1  # the new step is not undone


def test_zoom_header_and_splitter_are_remembered(qtbot, window):
    win, _ = window
    screen = win.degerler
    assert screen.zoom.zoom() == 200
    screen.zoom.zoom_in()
    assert win.prefs.zoom("degerler") == 225
    screen.table.horizontalHeader().resizeSection(2, 140)
    screen._save_header()
    state = win.prefs.header_state(screen._header_key.split("|")[0])
    assert isinstance(state, QByteArray) and not state.isEmpty()
    screen.splitter.splitterMoved.emit(500, 1)
    assert len(win.prefs.splitter_sizes("degerler")) == 2


def test_header_state_is_restored(qtbot, window):
    win, _ = window
    screen = win.degerler
    header = screen.table.horizontalHeader()
    header.resizeSection(2, 141)
    screen._save_header()
    screen._header_key = ""
    header.resizeSection(2, 60)
    screen.refresh()
    assert header.sectionSize(2) == 141


def test_keys_in_the_window_enter_n_space_esc(qtbot, window):
    win, sicil = window
    screen = win.degerler
    win.activateWindow()
    screen.select_value(1, sicil.key)
    screen.table.setFocus()
    QTest.keyClick(screen.table, Qt.Key.Key_N)  # Sonraki kontrol
    assert screen.current_value() == (2, sicil.key)
    QTest.keyClick(screen.table, Qt.Key.Key_Return)  # Onayla ve sonrakine geç
    job = win.controller().job
    assert current_values(job, win.controller().documents()[1])[sicil.key].value == "48213"
    QTest.keyClick(screen.table, Qt.Key.Key_Space)  # Tüm sayfayı göster
    assert screen.loupe is not None and screen.loupe.is_open()
    QTest.keyClick(QApplication.focusWidget() or screen.loupe, Qt.Key.Key_Escape)
    qtbot.waitUntil(lambda: not screen.loupe.isVisible(), timeout=2000)
    win.registry.action("app.geri_al").trigger()  # Ctrl+Z goes to the job's stack
    qtbot.waitUntil(lambda: current_values(job, win.controller().documents()[1])[
        sicil.key].flagged)


def test_right_click_lists_the_value_commands_with_their_keys(qtbot, window):
    win, _ = window
    screen = win.degerler
    rect = screen.table.visualRect(screen.cell(1, "Sicil_No"))
    menu = screen.context_menu(rect.center())
    texts = [a.text().replace("&", "") for a in menu.actions() if not a.isSeparator()]
    assert texts[0] == "Onayla ve sonrakine geç" and "Elle yaz" in texts
    assert screen.current_value()[0] == 1
    assert screen.table.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu


# -- F-degerler-46 / B-056 / Q-12: what is stored must equal what the cell shows ---------------
# Every Q-12 option leads to the same rule; today confirm stores the Öneri while the cell shows
# the Okunan text, so these fail until the owner's decision is implemented.
_B056 = pytest.mark.xfail(strict=True, reason="B-056 / Q-12: confirm stores the suggestion "
                                              "while the cell shows the read text")


def _shown_and_stored(qtbot, setup, how):
    ctl, templates, _, sicil = setup
    screen = _screen(qtbot, ctl, templates)
    assert screen.current_value() == (2, sicil.key)
    index = screen.table.currentIndex()
    shown = screen.model.data(index, Qt.ItemDataRole.DisplayRole)
    how(screen)
    return shown, _value(ctl, 1, sicil.key).value


@_B056
def test_f46_enter_stores_what_the_cell_showed(qtbot, setup):
    def press_enter(screen):
        screen.table.setFocus()
        QTest.keyClick(screen.table, Qt.Key.Key_Return)

    shown, stored = _shown_and_stored(qtbot, setup, press_enter)
    assert stored == shown


@_B056
def test_f46_the_accept_button_stores_what_the_cell_showed(qtbot, setup):
    shown, stored = _shown_and_stored(qtbot, setup, lambda s: s.side.accept_button.click())
    assert stored == shown


# -- F-degerler-01: N / Sonraki kontrol through the action must step, not restart ------------
def _three_kontrol(win, sicil):
    ctl = win.controller()
    for doc in ctl.documents():
        current_values(ctl.job, doc)[sicil.key] = BAD
    ctl.job_changed.emit()
    screen = win.degerler
    screen.refresh()
    win.show_tab("degerler")
    return screen


def _routes(win):
    from contract_helpers import run_via_menu, run_via_palette

    from evrakci.ui.main_window import MainWindow  # noqa: F401

    def key(screen):
        screen.table.setFocus()
        QTest.keyClick(screen.table, Qt.Key.Key_N)

    def menu(screen):
        run_via_menu(win, "degerler.sonraki_kontrol")

    def palette(screen):
        run_via_palette(win, "degerler", "degerler.sonraki_kontrol")

    def trigger(screen):
        win.registry.action("degerler.sonraki_kontrol").trigger()

    def button(screen):
        from evrakci.ui.chrome import ActionButton
        action = win.registry.action("degerler.sonraki_kontrol")
        bar = win.command_bars.currentWidget()
        next(b for b in bar.findChildren(ActionButton) if b.action_ is action).click()

    return {"key": key, "menu": menu, "palette": palette, "trigger": trigger, "button": button}


@pytest.mark.parametrize("route", ["key", "menu", "palette", "trigger", "button"])
def test_f01_next_kontrol_steps_through_every_route(window, route):
    win, sicil = window
    screen = _three_kontrol(win, sicil)
    first = next(c for c in screen.model.value_columns()
                 if screen.model.cell_at(screen.model.index(0, c)).needs_check)
    screen.table.setCurrentIndex(screen.model.index(1, first))
    step = _routes(win)[route]
    step(screen)
    assert (screen.table.currentIndex().row(), screen.table.currentIndex().column()) == (2, first)
    step(screen)
    assert screen.table.currentIndex().row() == 0  # wrapped, then it keeps stepping
    step(screen)
    assert screen.table.currentIndex().row() == 1


def test_f01_shift_n_steps_back_by_key(window):
    win, sicil = window
    screen = _three_kontrol(win, sicil)
    first = next(c for c in screen.model.value_columns()
                 if screen.model.cell_at(screen.model.index(0, c)).needs_check)
    screen.table.setCurrentIndex(screen.model.index(1, first))
    screen.table.setFocus()
    QTest.keyClick(screen.table, Qt.Key.Key_N, Qt.KeyboardModifier.ShiftModifier)
    assert screen.table.currentIndex().row() == 0
    QTest.keyClick(screen.table, Qt.Key.Key_N, Qt.KeyboardModifier.ShiftModifier)
    assert screen.table.currentIndex().row() == 2


# -- F-degerler-02: a long variable name elides in the inspector instead of widening it --------
@pytest.mark.parametrize("scale", [100, 150])
@pytest.mark.parametrize("name", ["Sicil_No_" + "uzun_degisken_adi_" * 3 + "son",
                                  "S" * 52])
def test_f02_long_variable_name_elides_and_the_cards_stay_inside_the_panel(
        qtbot, setup, name, scale):
    from evrakci.ui import theme

    old = theme.manager().text_scale()
    theme.manager().set_text_scale(scale)
    try:
        _f02(qtbot, setup, name)
    finally:
        theme.manager().set_text_scale(old)


def _f02(qtbot, setup, name):
    ctl, templates, template, sicil = setup
    template.rename_variable("Sicil_No", name)
    templates.save(template)
    screen = _screen(qtbot, ctl, templates)
    screen.show()
    qtbot.waitUntil(lambda: screen.side.source.title.text() != "", timeout=3000)
    qtbot.wait(100)
    title = screen.side.source.title
    assert title.full_text().replace(" ", "").replace("_", "") == name.replace("_", "")
    assert title.toolTip() == title.full_text()
    viewport = screen.side.scroll.viewport().width()
    assert screen.side.source.width() <= viewport
    assert screen.side.value.width() <= viewport
    assert title.width() <= screen.side.source.width()


# -- F-degerler-03: a double click on "Onayla ve sonrakine geç" confirms one value -------------
def test_f03_double_click_on_the_accept_button_confirms_one_value(qtbot, tmp_path):
    store, job = _job(tmp_path)
    ctl = JobController(store, job)
    templates, template, sicil, firma = _template(tmp_path)
    _fill(ctl, template, sicil, firma, values=(GOOD, GOOD, GOOD))
    screen = _screen(qtbot, ctl, templates)
    screen.show()
    screen.table.setCurrentIndex(screen.model.index(0, screen.model.value_columns()[0]))
    button = screen.side.accept_button
    pos = QPointF(button.rect().center())
    for kind in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease,
                 QEvent.Type.MouseButtonDblClick, QEvent.Type.MouseButtonRelease):
        down = kind != QEvent.Type.MouseButtonRelease
        QApplication.sendEvent(button, QMouseEvent(
            kind, pos, button.mapToGlobal(pos), Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton if down else Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier))
    edited = [v.edited for d in ctl.documents() for v in current_values(ctl.job, d).values()]
    assert sum(edited) == 1, edited


# -- F-degerler-08: no Geri al / Yinele while a read runs ---------------------------------------
def _stop_read(qtbot, win, gate):
    """Always leave no read running: it would block the window's teardown."""
    gate.set()
    win.degerler.cancel()
    qtbot.waitUntil(lambda: not win.degerler.busy(), timeout=20000)


class BrokenEngine(GatedEngine):
    def read_region(self, image):
        self.gate.wait(5)
        raise OSError("sahte hata")


@pytest.mark.parametrize("how", ["finish", "cancel", "error"])
def test_f08_undo_and_redo_are_off_while_a_read_runs(qtbot, window, how):
    win, _ = window
    r = win.registry
    ctl = win.controller()
    assert r.is_enabled("app.geri_al")
    gate = threading.Event()
    engine = BrokenEngine if how == "error" else GatedEngine
    win.degerler.engine = lambda: engine(gate)
    win.degerler.read_button.click()
    try:
        assert win.degerler.busy()
        assert not r.is_enabled("app.geri_al") and not r.is_enabled("app.yinele")
        before = ctl.undo_stack.index()
        win.undo()  # a route that does not look at the action's state
        win.redo()
        assert ctl.undo_stack.index() == before
        if how == "cancel":
            win.degerler.cancel()
        gate.set()
        qtbot.waitUntil(lambda: not win.degerler.busy(), timeout=20000)
        assert r.is_enabled("app.geri_al"), how
    finally:
        _stop_read(qtbot, win, gate)


# -- F-degerler-09: focus does not fall to the title tabs when its button goes away -------------
def test_f09_space_on_the_read_button_keeps_focus_in_the_table(qtbot, window):
    from evrakci.ui.chrome import ActionButton

    win, _ = window
    win.activateWindow()
    assert QTest.qWaitForWindowActive(win)
    action = win.registry.action("degerler.oku")
    button = next(b for b in win.command_bars.currentWidget().findChildren(ActionButton)
                  if b.action_ is action)
    gate = threading.Event()
    win.degerler.engine = lambda: GatedEngine(gate)
    button.setFocus(Qt.FocusReason.TabFocusReason)
    assert QApplication.focusWidget() is button
    try:
        QTest.keyClick(button, Qt.Key.Key_Space)
        qtbot.waitUntil(win.degerler.busy, timeout=3000)
        assert QApplication.focusWidget() is win.degerler.table
        gate.set()
        qtbot.waitUntil(lambda: not win.degerler.busy(), timeout=20000)
        assert QApplication.focusWidget() is win.degerler.table
    finally:
        _stop_read(qtbot, win, gate)


def test_f09_clearing_the_search_keeps_focus_in_the_table(qtbot, setup):
    ctl, templates, _, _ = setup
    screen = _screen(qtbot, ctl, templates)
    screen.show()
    screen.search.setText("yok böyle")
    assert not screen.empty.isHidden()
    screen.activateWindow()
    assert QTest.qWaitForWindowActive(screen)
    screen.empty.primary.setFocus(Qt.FocusReason.TabFocusReason)
    assert QApplication.focusWidget() is screen.empty.primary
    screen.empty.primary.click()
    assert QApplication.focusWidget() is screen.table


def test_f12_the_long_review_toast_is_not_cut(qtbot, window):
    win, _ = window
    text = "Kontrol gereken değer kalmadı; 5 değer incelenmedi. Enter sıradakini onaylar."
    toaster = win.toaster
    toaster.show(text, kind="info")
    qtbot.wait(150)
    label = next(w for w in toaster._current.findChildren(QLabel) if w.text() == text)
    need = label.fontMetrics().boundingRect(label.rect(), int(Qt.TextFlag.TextWordWrap),
                                            text).height()
    assert label.wordWrap() or label.fontMetrics().horizontalAdvance(text) <= label.width()
    assert label.height() >= need


# -- more F-01 / F-03 edges, and Enter on the panel buttons ------------------------------------
def test_n_with_no_kontrol_value_says_so_and_stays(qtbot, tmp_path):
    store, job = _job(tmp_path)
    ctl = JobController(store, job)
    templates, template, sicil, firma = _template(tmp_path)
    _fill(ctl, template, sicil, firma, values=(GOOD, GOOD, GOOD))
    screen = _screen(qtbot, ctl, templates)
    said = []
    screen.status.connect(said.append)
    screen.table.setCurrentIndex(screen.model.index(1, screen.model.value_columns()[0]))
    here = screen.table.currentIndex().row()
    screen.next_check()
    assert said[-1] == "Kontrol bekleyen değer yok."
    assert screen.table.currentIndex().row() == here


def _double_click(button):
    pos = QPointF(button.rect().center())
    for kind in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease,
                 QEvent.Type.MouseButtonDblClick, QEvent.Type.MouseButtonRelease):
        down = kind != QEvent.Type.MouseButtonRelease
        QApplication.sendEvent(button, QMouseEvent(
            kind, pos, button.mapToGlobal(pos), Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton if down else Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier))


def test_f03_double_click_on_a_disabled_accept_button_confirms_nothing(qtbot, setup):
    ctl, templates, _, _ = setup
    screen = _screen(qtbot, ctl, templates)
    screen.show()
    button = screen.side.accept_button
    button.setEnabled(False)
    _double_click(button)
    assert not any(v.edited for d in ctl.documents() for v in current_values(ctl.job, d).values())


def test_enter_on_the_focused_accept_button_presses_it_once(qtbot, window):
    win, _ = window
    win.activateWindow()
    assert QTest.qWaitForWindowActive(win)
    screen = win.degerler
    screen.table.setCurrentIndex(screen.model.index(0, screen.model.value_columns()[0]))
    button = screen.side.accept_button
    button.setFocus(Qt.FocusReason.TabFocusReason)
    assert QApplication.focusWidget() is button
    ctl = win.controller()
    QTest.keyClick(button, Qt.Key.Key_Return)
    edited = [v.edited for d in ctl.documents() for v in current_values(ctl.job, d).values()]
    assert sum(edited) == 1, edited


# -- I-19: every section's reading in the value card ------------------------------------------
def _many(n):
    return VariableValue("", 0.0, None, True, "48213", tuple(
        SectionReading(i, "48213" if i == 1 else f"4821{i}", 0.4 + i / 100) for i in range(n)))


def _card_screen(qtbot, tmp_path, value):
    store, job = _job(tmp_path)
    ctl = JobController(store, job)
    templates, template, sicil, firma = _template(tmp_path)
    _fill(ctl, template, sicil, firma, values=(value, GOOD, GOOD))
    return ctl, _screen(qtbot, ctl, templates), sicil


def test_i19_two_readings_are_listed_and_the_suggestion_is_tagged(qtbot, tmp_path):
    _, screen, _ = _card_screen(qtbot, tmp_path, BAD)
    card = screen.side.value
    assert card.readings_label.text() == "Tüm okumalar" and not card.readings_box.isHidden()
    rows = card.reading_rows
    assert [r.name.text() for r in rows] == ["Bölüm 1", "Varyant 2"]
    assert [r.text.text for r in rows] == ["482I3", "48213"]
    assert rows[0].text.marks == (3,)
    assert [r.percent.text() for r in rows] == ["%41", "%55"]
    assert [r.tag.text() for r in rows] == ["", "Öneri"]
    assert all(r.height() >= 32 for r in rows) and card.more.isHidden()


def test_i19_a_single_reading_shows_no_block(qtbot, tmp_path):
    one = VariableValue("", 0.0, None, True, "48213", (SectionReading(1, "48213", 0.55),))
    _, screen, _ = _card_screen(qtbot, tmp_path, one)
    assert screen.side.value.readings_box.isHidden()


def test_i19_six_readings_are_four_rows_and_n_more(qtbot, tmp_path):
    _, screen, _ = _card_screen(qtbot, tmp_path, _many(6))
    card = screen.side.value
    assert len(card.reading_rows) == 4
    assert card.more.text() == "+2 daha" and not card.more.isHidden()


def test_i19_clicking_a_row_fills_the_editor_and_enter_is_one_undo_step(qtbot, tmp_path):
    ctl, screen, sicil = _card_screen(qtbot, tmp_path, BAD)
    screen.show()
    steps = ctl.undo_stack.index()
    QTest.mouseClick(screen.side.value.reading_rows[0], Qt.MouseButton.LeftButton)
    editor = screen.table.open_editor_widget()
    assert editor is not None and editor.text() == "482I3"
    QTest.keyClick(editor, Qt.Key.Key_Return)
    qtbot.waitUntil(lambda: _value(ctl, 0, sicil.key).value == "482I3")
    assert ctl.undo_stack.index() == steps + 1
    assert ctl.undo_stack.undoText() == "Değeri düzelt"
    ctl.undo()
    assert _value(ctl, 0, sicil.key).flagged and ctl.undo_stack.index() == steps


def test_i19_alt_2_in_the_editor_takes_reading_two(qtbot, tmp_path):
    ctl, screen, sicil = _card_screen(qtbot, tmp_path, _many(3))
    screen.show()
    screen.type_current()
    editor = screen.table.open_editor_widget()
    QTest.keyClick(editor, Qt.Key.Key_3, Qt.KeyboardModifier.AltModifier)
    assert editor.text() == "48212"
    QTest.keyClick(editor, Qt.Key.Key_2, Qt.KeyboardModifier.AltModifier)
    assert editor.text() == "48213"  # reading 2 (index 1)
    QTest.keyClick(editor, Qt.Key.Key_4, Qt.KeyboardModifier.AltModifier)
    assert editor.text() == "48213"  # no fourth reading: nothing changes
    assert _value(ctl, 0, sicil.key).flagged  # taking a reading alone stores nothing


def test_i19_rows_do_not_overlap_at_150_percent_and_long_text_is_elided(qtbot, tmp_path):
    from evrakci.ui import theme
    manager = theme.manager()
    manager.set_text_scale(150)
    try:
        long = "48213" * 12
        value = VariableValue("", 0.0, None, True, "48213", (
            SectionReading(0, "482I3", 0.41, "1 karakter belirsiz"),
            SectionReading(1, "48213", 0.55), SectionReading(2, long, 0.30),
            SectionReading(3, "48218", 0.45)))
        _, screen, _ = _card_screen(qtbot, tmp_path, value)
        screen.resize(1100, 700)
        screen.show()
        card = screen.side.value
        qtbot.waitUntil(lambda: card.reading_rows and card.reading_rows[0].height() > 0)
        rows = card.reading_rows
        label_bottom = card.readings_label.geometry().bottom()
        boxes = [r.geometry() for r in rows]
        assert boxes[0].top() > label_bottom
        for a, b in zip(boxes, boxes[1:], strict=False):
            assert a.bottom() < b.top(), (a, b)
        assert all(r.height() >= 32 for r in rows)
        for r in rows:
            assert r.text.height() <= r.height()
            right = r.text.geometry().right()
            assert right < r.percent.geometry().left()
            assert r.name.geometry().right() < r.text.geometry().left()
            for note in (r.tag, r.problem):  # the second line sits below the first
                if note.isVisible():
                    assert note.geometry().top() >= r.text.geometry().bottom()
            assert r.geometry().right() <= card.readings_box.rect().right() + 1
        assert rows[2].toolTip() == long and rows[2].text.toolTip() == long
        metrics = QFontMetrics(rows[2].text.font_())
        assert metrics.horizontalAdvance(long) > rows[2].text.width()  # elided when painted
    finally:
        manager.set_text_scale(100)


def test_i19_an_empty_reading_is_shown_but_cannot_be_picked(qtbot, tmp_path):
    value = VariableValue("", 0.0, None, True, "48213", (
        SectionReading(0, "", 0.0), SectionReading(1, "48213", 0.55)))
    ctl, screen, sicil = _card_screen(qtbot, tmp_path, value)
    screen.show()
    row = screen.side.value.reading_rows[0]
    assert row.text.text == "boş" and not row.pickable
    QTest.mouseClick(row, Qt.MouseButton.LeftButton)
    assert screen.table.open_editor_widget() is None
    screen.type_current()
    editor = screen.table.open_editor_widget()
    before = editor.text()
    QTest.keyClick(editor, Qt.Key.Key_1, Qt.KeyboardModifier.AltModifier)
    assert editor.text() == before


def test_i19_every_row_equal_to_the_suggestion_is_tagged(qtbot, tmp_path):
    value = VariableValue("", 0.0, None, True, "48213", (
        SectionReading(0, "48213", 0.40), SectionReading(1, "482I3", 0.41),
        SectionReading(2, "48213", 0.55)))
    _, screen, _ = _card_screen(qtbot, tmp_path, value)
    assert [r.tag.text() for r in screen.side.value.reading_rows] == ["Öneri", "", "Öneri"]


def test_i19_building_the_rows_opens_no_stray_window(qtbot, tmp_path):
    from evrakci.ui.degerler_side import ReadingItem, ReadingRow
    before = {id(w) for w in QApplication.topLevelWidgets() if w.isVisible()}
    ReadingRow(ReadingItem("Bölüm 1", "48213", (), 55, True, "boş olabilir"))
    after = {id(w) for w in QApplication.topLevelWidgets() if w.isVisible()}
    assert after == before


def _cell_image(screen, row, key, width=220):
    from PySide6.QtCore import QRect
    from PySide6.QtGui import QColor, QImage, QPainter
    from PySide6.QtWidgets import QStyleOptionViewItem

    table = screen.table
    column = next(i for i, c in enumerate(screen.model.columns) if c.key == key)
    index = screen.model.index(row, column)
    background = QColor("#ffffff")
    image = QImage(width, 40, QImage.Format.Format_ARGB32)
    image.fill(background)
    option = QStyleOptionViewItem()
    option.rect = QRect(0, 0, width, 40)
    painter = QPainter(image)
    table.itemDelegate().paint(painter, option, index)
    painter.end()
    return image, index, image.pixelColor(width - 1, 20)  # the row fill (selected or not)


def _ink_columns(image, background):
    return {x for x in range(image.width()) for y in range(4, 34)
            if image.pixelColor(x, y) != background}


def test_a_kontrol_cell_paints_an_icon_left_of_its_text_and_an_emin_cell_none(qtbot, setup):
    ctl, templates, _, sicil = setup
    screen = _screen(qtbot, ctl, templates)
    kontrol, index, bg = _cell_image(screen, 1, sicil.key)
    emin, _, bg_emin = _cell_image(screen, 0, sicil.key)
    left = _ink_columns(kontrol, bg)
    left_emin = _ink_columns(emin, bg_emin)
    start = min(left_emin)  # where text starts without a mark
    assert min(left) == start and any(x < start + 16 for x in left)
    assert not any(start + 18 <= x <= start + 21 for x in left)  # the gap after the icon
    assert min(x for x in left if x >= start + 18) >= start + 22  # text moved right
    tooltip = index.data(Qt.ItemDataRole.ToolTipRole)
    assert tooltip.splitlines()[0] == "Bu değere bakın: okuma emin değil."
    assert "Kontrol" in tooltip and "Öneri: 48213" in tooltip
    assert "Kontrol" in index.data(Qt.ItemDataRole.AccessibleTextRole)
    assert "Kontrol" not in (screen.model.index(0, index.column()).data(
        Qt.ItemDataRole.ToolTipRole) or "")


def test_an_okunamadi_cell_paints_its_own_icon(qtbot, tmp_path):
    """I-17: a value nothing was read for gets the circle-x mark too (not only Kontrol)."""
    store, job = _job(tmp_path)
    ctl = JobController(store, job)
    templates, template, sicil, firma = _template(tmp_path)
    nothing = VariableValue("", 0.0, None, True)
    _fill(ctl, template, sicil, firma, values=(GOOD, nothing, GOOD))
    screen = _screen(qtbot, ctl, templates)
    blank, index, bg = _cell_image(screen, 1, sicil.key)
    assert index.data(Qt.ItemDataRole.ToolTipRole).splitlines()[0] != (
        "Bu değere bakın: okuma emin değil.")  # that line is for Kontrol only
    assert "Okunamadı" in index.data(Qt.ItemDataRole.ToolTipRole)
    emin, _, bg_emin = _cell_image(screen, 0, sicil.key)
    start = min(_ink_columns(emin, bg_emin))
    assert any(x < start + 16 for x in _ink_columns(blank, bg))  # the mark is drawn
