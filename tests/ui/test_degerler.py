"""Değerler (direction A): the values table linked to the page crop, the Kontrol queue
(Enter = accept and go on, Tab = next value, F2 / Esc), Tümünü incele, Örnek kontrol, bulk
accept with undo, empty states, persistence and the window wiring."""

import threading

import pytest
from fakes import job_from_kinds, make_pdf, text_page
from PySide6.QtCore import QByteArray, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QAbstractButton, QApplication, QComboBox, QLineEdit, QWidget

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
    win.yukle.open_job(store.load(job.id))
    _fill(win.controller(), template, sicil, firma)
    win.resize(1366, 768)
    win.show()
    win.show_tab("degerler")
    qtbot.waitUntil(lambda: win.degerler.window_ is win)
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
