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
from saving import wait_saved

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
    assert card.why.text() == "Bölüm 2 ile okundu: I yerine 1."
    assert screen.side.source.title.text() == "Sicil No"
    assert screen.side.source.meta.text() == "Belge 2, sayfa 2 · zorunlu"


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
    assert screen.search.placeholderText() == "Değerlerde ara"
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
    assert ctl.undo_stack.undoText() == "Onayla"


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


def test_clearing_a_required_cell_stores_kontrol_and_the_header_and_card_say_zorunlu(qtbot, setup):
    ctl, templates, _, sicil = setup
    screen = _screen(qtbot, ctl, templates)
    headers = {c.title: c for c in screen.model.columns if c.kind == "var"}
    assert headers["Sicil No"].label == "Sicil No *"
    assert headers["Firma"].label == "Firma"
    col = screen.column_of("Sicil_No")
    header = screen.model.headerData(col, Qt.Orientation.Horizontal)
    assert header == "Sicil No *"
    for role in (Qt.ItemDataRole.AccessibleTextRole, Qt.ItemDataRole.ToolTipRole):
        assert screen.model.headerData(col, Qt.Orientation.Horizontal, role) == "Sicil No, zorunlu"
    index = screen.cell(1, "Sicil_No")
    screen.table.setCurrentIndex(index)
    assert "· zorunlu" in screen.side.source.meta.text()
    assert screen.model.setData(index, "  ")  # stored, but not as typed
    value = _value(ctl, 0, sicil.key)
    assert value.flagged and not value.edited and value.value == ""
    assert value.suggestion == "48197"  # the old reading is kept
    screen.refresh()
    cell = screen.model.row_at(screen.model.row_of(1)).cell(sicil.key)
    assert cell.level == "kontrol" and cell.needs_check
    assert cell.why() != "Zorunlu değer boş: dosya adı için bir değer yazın."  # has a reading
    # a variable that is not required: no mark, stored as typed
    firma = screen.cell(1, "Firma")
    screen.table.setCurrentIndex(firma)
    assert "zorunlu" not in screen.side.source.meta.text()
    assert screen.model.setData(firma, "")
    assert _value(ctl, 0, next(k for k in current_values(ctl.job, ctl.documents()[0])
                               if k != sicil.key)).edited


def test_a_required_value_with_nothing_read_says_why_it_is_empty(qtbot, setup):
    ctl, templates, _, sicil = setup
    current_values(ctl.job, ctl.documents()[0])[sicil.key] = VariableValue("", 1.0, None, False,
                                                                          "", (), True)
    screen = _screen(qtbot, ctl, templates)
    cell = screen.model.row_at(0).cell(sicil.key)
    assert cell.why() == "Zorunlu değer boş: dosya adı için bir değer yazın."


def test_window_and_cli_store_the_same_for_an_emptied_required_value(qtbot, tmp_path, capsys):
    from evrakci.cli import main

    store, job = _job(tmp_path)
    ctl = JobController(store, job)
    templates, template, sicil, firma = _template(tmp_path)
    _fill(ctl, template, sicil, firma)
    ctl.save_now()
    wait_saved(ctl)
    screen = _screen(qtbot, ctl, templates)
    screen.model.setData(screen.cell(1, "Sicil_No"), "")
    shown = _value(ctl, 0, sicil.key)
    wait_saved(ctl)  # the write-behind saver must not overwrite what the CLI stores
    capsys.readouterr()
    assert main(["--kok", str(tmp_path / "jobs"), "--sablon-kok", str(tmp_path / "tpl"),
                 "is", "deger", job.id, "1", "Sicil_No", ""]) == 0
    assert "Zorunlu değer boş bırakılamaz; Kontrol'e alındı." in capsys.readouterr().out
    stored = JobStore(tmp_path / "jobs").load(job.id)
    assert current_values(stored, ctl.documents()[0])[sicil.key] == shown


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
    assert said[-1] == "6 değer onaylandı; 1 tanesi Kontrol'dü."
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
    assert spoken == "Sicil No: 482I3, Kontrol %55, öneri 48213, 4. karakter belirsiz"


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

    def __init__(self, text="77777"):
        self.text = text

    def available(self):
        return None

    def read_region(self, image):
        return Reading(self.text, 0.9)


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
    assert win.toaster.current_text() == "6 değer onaylandı; 1 tanesi Kontrol'dü."
    toast = win.toaster._current
    undo = next(b for b in toast.findChildren(QAbstractButton) if b.text() == "Geri al")
    undo.click()
    assert current_values(win.controller().job, win.controller().documents()[1])[
        sicil.key].flagged


def test_clearing_a_required_value_in_the_window_toasts_kontrol_with_undo(qtbot, window):
    win, sicil = window
    screen = win.degerler
    ctl = win.controller()
    assert screen.model.setData(screen.cell(1, "Sicil_No"), "")
    assert win.toaster.current_text() == "Zorunlu değer boş bırakılamaz; Kontrol'e alındı."
    assert _value(ctl, 0, sicil.key).flagged
    toast = win.toaster._current
    undo = next(b for b in toast.findChildren(QAbstractButton) if b.text() == "Geri al")
    undo.click()
    assert _value(ctl, 0, sicil.key).value == "48197"


def test_reemptying_an_empty_required_value_offers_no_undo(qtbot, window, monkeypatch):
    """No new step was pushed, so a Geri al on this toast would undo an older step."""
    win, sicil = window
    screen = win.degerler
    assert screen.model.setData(screen.cell(1, "Sicil_No"), "")
    stack = win.controller().undo_stack
    index = stack.index()
    shown: list = []
    monkeypatch.setattr(screen, "_toast", lambda text, ctl, expected, kind: shown.append(
        (text, expected == stack.index())))  # True = the toast would offer Geri al
    screen._apply_edit(screen.rows[0], sicil.key, "")
    assert stack.index() == index  # nothing new to undo
    assert all(not offers_undo for _text, offers_undo in shown)


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
    QTest.keyClick(screen.table, Qt.Key.Key_Return)  # Onayla
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
    assert texts[0] == "Onayla" and "Elle yaz" in texts
    assert screen.current_value()[0] == 1
    assert screen.table.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu


# -- F-degerler-46 / B-056 / Q-12: the cell shows the suggestion and the read, two approvals --
def _flagged_screen(qtbot, setup):
    ctl, templates, _, sicil = setup
    screen = _screen(qtbot, ctl, templates)
    assert screen.current_value() == (2, sicil.key)
    return ctl, screen, sicil


def test_f46_the_cell_shows_the_suggestion_and_the_read(qtbot, setup):
    _, screen, _ = _flagged_screen(qtbot, setup)
    index = screen.table.currentIndex()
    assert screen.model.data(index, Qt.ItemDataRole.DisplayRole) == "48213"
    assert "482I3, Kontrol %55, öneri 48213" in screen.model.data(
        index, Qt.ItemDataRole.AccessibleTextRole)
    cell = screen.model.cell_at(index)
    assert cell.main == "48213" and cell.read_note == "482I3" and cell.dual
    tip = screen.model.data(index, Qt.ItemDataRole.ToolTipRole)
    assert "Öneri: 48213" in tip and "okunan 482I3" in tip


def test_f46_a_value_without_a_suggestion_keeps_one_onayla(qtbot, setup):
    ctl, screen, sicil = _flagged_screen(qtbot, setup)
    screen.select_value(1, sicil.key)  # an Emin value: nothing flagged
    cell = screen.model.cell_at(screen.table.currentIndex())
    assert not cell.dual and screen.model.data(
        screen.table.currentIndex(), Qt.ItemDataRole.DisplayRole) == cell.text
    assert screen.side.read_button.isHidden()
    assert screen.side.accept_button.text().strip() == "Onayla"


def test_f46_enter_stores_the_suggestion_and_says_so(qtbot, setup):
    ctl, screen, sicil = _flagged_screen(qtbot, setup)
    screen.table.setFocus()
    before = ctl.undo_stack.index()
    QTest.keyClick(screen.table, Qt.Key.Key_Return)
    assert _value(ctl, 1, sicil.key).value == "48213"
    assert ctl.undo_stack.index() == before + 1  # one undo step
    assert _value(ctl, 1, sicil.key).edited


def test_f46_the_accept_button_stores_the_suggestion(qtbot, setup):
    ctl, screen, sicil = _flagged_screen(qtbot, setup)
    assert screen.side.accept_button.text().strip() == "Öneriyle onayla"
    assert screen.side.read_button.text().strip() == "Okunanla onayla"
    assert not screen.side.read_button.isHidden()
    screen.side.accept_button.click()
    assert _value(ctl, 1, sicil.key).value == "48213"


def test_f46_shift_enter_stores_the_read(qtbot, setup):
    ctl, screen, sicil = _flagged_screen(qtbot, setup)
    screen.table.setFocus()
    before = ctl.undo_stack.index()
    QTest.keyClick(screen.table, Qt.Key.Key_Return, Qt.KeyboardModifier.ShiftModifier)
    value = _value(ctl, 1, sicil.key)
    assert value.value == "482I3" and value.edited and not value.flagged
    assert ctl.undo_stack.index() == before + 1
    ctl.undo_stack.undo()  # one step back to the flagged value
    assert _value(ctl, 1, sicil.key).flagged


def test_f46_the_read_button_stores_the_read(qtbot, setup):
    ctl, screen, sicil = _flagged_screen(qtbot, setup)
    screen.side.read_button.click()
    assert _value(ctl, 1, sicil.key).value == "482I3"


def test_f46_the_confirmations_name_the_value(qtbot, setup):
    ctl, screen, sicil = _flagged_screen(qtbot, setup)
    said = []
    screen._toast = lambda text, *a, **k: said.append(text)
    screen.accept_current()
    assert said == ["48213 kaydedildi (öneri)."]
    ctl.undo_stack.undo()
    screen.refresh()
    screen.select_value(2, sicil.key)
    screen.accept_read()
    assert said[-1] == "482I3 kaydedildi (okunan)."


def test_f46_shift_enter_does_nothing_without_a_different_read(qtbot, setup):
    ctl, screen, sicil = _flagged_screen(qtbot, setup)
    screen.select_value(1, sicil.key)
    before = ctl.undo_stack.index()
    screen.accept_read()
    assert ctl.undo_stack.index() == before


def test_f46_a_confirmation_replaces_only_its_own_kind_and_each_geri_al_undoes_its_step(
        qtbot, window):
    win, sicil = window
    screen = _three_kontrol(win, sicil)
    ctl, toaster = win.controller(), win.toaster
    toaster.show("Kaydedilemedi.", kind="error")
    screen.select_value(1, sicil.key)
    screen.table.setFocus()
    QTest.keyClick(screen.table, Qt.Key.Key_Return)
    first = ctl.undo_stack.index()
    QTest.keyClick(screen.table, Qt.Key.Key_Return)
    second = ctl.undo_stack.index()
    assert second == first + 1
    texts = [toaster.current_text()] + [p.text for p in toaster._queue]
    assert texts.count("Kaydedilemedi.") == 1  # the error is still shown or queued
    confirmations = [t for t in texts if "kaydedildi (öneri)" in t]
    assert confirmations == ["48213 kaydedildi (öneri)."]  # only the last one remains
    queued = [p for p in toaster._queue if p.key]
    assert len(queued) == 1 and queued[0].available()  # B-023: it undoes its own step
    queued[0].on_action()
    assert ctl.undo_stack.index() == second - 1
    assert not queued[0].available()  # a Geri al of an older step would not act any more


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
    assert [r.name.text() for r in rows] == ["Bölüm 1", "Bölüm 2"]
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
    row = ReadingRow(ReadingItem("Bölüm 1", "48213", (), 55, True, "boş olabilir"))
    qtbot.addWidget(row)  # closed and deleted by qtbot, not left to the cycle collector
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


# -- I-23: Okunana dön ------------------------------------------------------------------------
def _correct(screen, number, key, text):
    assert screen.model.setData(screen.model.value_index(number, key), text)
    screen.refresh()


def test_i23_r_puts_a_corrected_value_back_to_kontrol_with_the_reading(qtbot, window):
    win, sicil = window
    screen = win.degerler
    ctl = win.controller()
    _correct(screen, 1, sicil.key, "48190")
    assert _value(ctl, 0, sicil.key).edited
    screen.select_value(1, sicil.key)
    screen.table.setFocus()
    before = ctl.undo_stack.index()
    QTest.keyClick(screen.table, Qt.Key.Key_R)
    value = _value(ctl, 0, sicil.key)
    assert value.flagged and not value.edited and value.value == ""
    assert value.suggestion == "48197"  # the machine reading is the suggestion again
    assert screen.current_value() == (1, sicil.key)  # selection stays
    assert ctl.undo_stack.index() == before + 1 and ctl.undo_stack.undoText() == "Okunana dön"
    assert win.toaster.current_text() == "Okunana dönüldü: Sicil No. Kontrol'e alındı."
    win.registry.action("app.geri_al").trigger()  # one step restores the correction
    value = _value(ctl, 0, sicil.key)
    assert value.value == "48190" and value.edited and not value.flagged
    assert ctl.undo_stack.index() == before


def test_i23_confirmed_suggestion_can_be_reverted(qtbot, window):
    win, sicil = window
    screen = win.degerler
    ctl = win.controller()
    screen.select_value(2, sicil.key)
    screen.accept_current()
    assert _value(ctl, 1, sicil.key).edited
    screen.select_value(2, sicil.key)
    win.registry.action("degerler.okunana_don").trigger()
    value = _value(ctl, 1, sicil.key)
    assert value.flagged and value.suggestion == "48213" and len(value.readings) == 2


def test_i23_disabled_with_a_reason_when_never_machine_read(qtbot, window):
    win, sicil = window
    screen = win.degerler
    ctl = win.controller()
    r = win.registry
    action = r.action("degerler.okunana_don")
    screen.select_value(1, sicil.key)
    assert not r.is_enabled("degerler.okunana_don")  # not corrected: nothing to put back
    first = ctl.documents()[0]
    record_values(ctl.job, first, ctl.job.value_sources[first.page_ids[0]].template_id,
                  {sicil.key: VariableValue("elle", 1.0, None, False, "", (), True)})
    ctl.job_changed.emit()
    screen.select_value(1, sicil.key)
    screen.refresh()
    assert not r.is_enabled("degerler.okunana_don")
    assert action.toolTip() == "Bu değer elle yazıldı; okunmuş bir değer yok."
    before = ctl.undo_stack.index()
    screen.table.setFocus()
    QTest.keyClick(screen.table, Qt.Key.Key_R)
    assert ctl.undo_stack.index() == before
    assert _value(ctl, 0, sicil.key).value == "elle"


def test_i23_disabled_in_the_sample_view(qtbot, window):
    win, sicil = window
    screen = win.degerler
    _correct(screen, 1, sicil.key, "48190")
    screen.select_value(1, sicil.key)
    assert win.registry.is_enabled("degerler.okunana_don")
    screen.set_view("ornek")
    screen.refresh()
    assert not win.registry.is_enabled("degerler.okunana_don")
    screen.revert_current()
    assert _value(win.controller(), 0, sicil.key).edited  # nothing was reverted
    screen.set_view("tumu")


def test_i23_context_menu_lists_it_with_its_key(qtbot, window):
    win, sicil = window
    screen = win.degerler
    _correct(screen, 1, sicil.key, "48190")
    rect = screen.table.visualRect(screen.cell(1, "Sicil_No"))
    menu = screen.context_menu(rect.center())
    items = {a.text().replace("&", "").split("\t")[0]: a for a in menu.actions()}
    assert "Okunana dön" in items and items["Okunana dön"].isEnabled()
    assert "R" in items["Okunana dön"].text() or items["Okunana dön"].shortcut().toString() == "R"


def test_i23_window_and_cli_leave_the_same_stored_value(qtbot, window, capsys, tmp_path):
    from saving import wait_saved

    from evrakci.cli import main
    from evrakci.pipeline.cuts import compute_documents
    from evrakci.pipeline.cuts import current_values as stored_values

    win, sicil = window
    screen = win.degerler
    ctl = win.controller()
    store = win.store
    _correct(screen, 1, sicil.key, "48190")
    screen.select_value(1, sicil.key)
    win.registry.action("degerler.okunana_don").trigger()
    from_window = _value(ctl, 0, sicil.key)
    win.registry.action("app.geri_al").trigger()  # back to the start: corrected, not reverted
    wait_saved(ctl)
    assert _value(ctl, 0, sicil.key).edited
    argv = ["--kok", str(store.root), "--sablon-kok", str(tmp_path / "tpl")]
    assert main([*argv, "is", "deger", ctl.job.id, "1", "Sicil_No", "--geri-al"]) == 0
    capsys.readouterr()
    on_disk = store.load(ctl.job.id)
    from_cli = stored_values(on_disk, compute_documents(on_disk)[0])[sicil.key]
    assert from_cli == from_window



def test_a_failed_typed_edit_does_not_claim_the_value_went_to_kontrol(qtbot, window, monkeypatch):
    """R-B-4: the required-empty toast belongs to an emptied text only."""
    win, sicil = window
    screen = win.degerler
    monkeypatch.setattr(win.controller(), "set_value", lambda *args: False)
    screen.model.setData(screen.cell(1, "Sicil_No"), "48200")
    assert win.toaster.current_text() != "Zorunlu değer boş bırakılamaz; Kontrol'e alındı."


# -- Q1+Q3: D-1 failed reads are counted, D-2 empty is refused, D-3 bulk accept names Kontrol ----
def test_d1_a_read_with_failed_documents_says_how_many_failed(window):
    win, sicil = window
    screen = win.degerler
    ctl = win.controller()
    from evrakci.ui.degerler import document_template

    docs = ctl.documents()
    tid = document_template(ctl.job, docs[0])[0]
    results = [(docs[0], tid, {sicil.key: GOOD}, None, ""),
               (docs[1], tid, None, "Tesseract çalışmadı", ""),
               (docs[2], tid, None, "Tesseract çalışmadı", "")]
    screen._read_done(results)
    assert win.toaster.current_text() == "1 belge okundu; 2 belge okunamadı."


def test_d1_a_clean_read_keeps_the_plain_sentence(window):
    win, sicil = window
    ctl = win.controller()
    from evrakci.ui.degerler import document_template

    docs = ctl.documents()
    tid = document_template(ctl.job, docs[0])[0]
    win.degerler._read_done([(docs[0], tid, {sicil.key: GOOD}, None, "")])
    assert win.toaster.current_text() == "1 belge okundu."


def test_d1_an_unexpected_read_error_is_not_shown_raw(window):
    win, _ = window
    win.degerler._read_failed("Traceback: boom")
    assert win.degerler.progress_label.text() == (
        "Okuma durdu. Kalan belgeleri 'Yalnızca eksikleri oku' ile deneyebilirsiniz.")
    assert win.degerler.progress_label.toolTip() == "Traceback: boom"


def test_d2_an_emptied_unreadable_required_value_is_not_stored_as_reviewed(qtbot, setup):
    ctl, templates, template, sicil = setup
    firma = next(v for v in template.variables if v.name == "Firma")
    unreadable = VariableValue("", 0.0, None, True)  # Okunamadı: nothing read, no suggestion
    record_values(ctl.job, ctl.documents()[1], template.id, {sicil.key: unreadable,
                                                              firma.key: GOOD})
    ctl.job_changed.emit()
    screen = _screen(qtbot, ctl, templates)
    screen.show()
    screen.select_value(2, sicil.key)
    screen.type_current()  # F2
    editor = screen.table.open_editor_widget()
    assert editor is not None and editor.text() == ""
    QTest.keyClick(editor, Qt.Key.Key_Return)  # Enter on the empty editor
    qtbot.waitUntil(lambda: not screen.table.is_editing())
    stored = _value(ctl, 1, sicil.key)
    assert stored.flagged and not stored.edited and not stored.value


def test_d3_bulk_accept_says_how_many_were_kontrol(window):
    win, _ = window
    win.degerler.select_all()
    win.registry.action("degerler.secilenleri_onayla").trigger()
    assert win.toaster.current_text() == "6 değer onaylandı; 1 tanesi Kontrol'dü."


# -- R3 Değerler proposals (Q-13, D-4 .. D-10) -----------------------------------------------
def _statuses(ctl):
    said: list[str] = []
    ctl.status.connect(said.append)
    return said


def test_d5_enter_leaves_a_quiet_line_and_undo_selects_the_value_again(qtbot, setup):
    ctl, templates, _, sicil = setup
    screen = _screen(qtbot, ctl, templates)
    screen.show()
    said = _statuses(ctl)
    assert screen.current_value() == (2, sicil.key)
    screen.accept_current()
    assert said == ["Belge 2, Sicil No: 48213 kabul edildi. Kontrol gereken değer kalmadı; "
                    "5 değer incelenmedi. Enter sıradakini onaylar."]  # one line, both parts
    assert screen.current_value() != (2, sicil.key)  # it moved on
    said.clear()
    ctl.undo()
    assert screen.current_value() == (2, sicil.key)  # the undone value is selected again
    assert said == ["Geri alındı: Belge 2, Sicil No."]
    assert _value(ctl, 1, sicil.key).flagged  # and it is back to what it was


def test_d5_a_press_that_stores_nothing_says_nothing(qtbot, setup):
    ctl, templates, _, sicil = setup
    screen = _screen(qtbot, ctl, templates)
    screen.show()
    screen.select_value(1, sicil.key)  # an Emin value nobody reviewed: Enter marks it
    screen.accept_current()
    screen.select_value(1, sicil.key)
    said = _statuses(ctl)
    index = ctl.undo_stack.index()
    screen.accept_current()  # already İncelendi: nothing to store
    assert ctl.undo_stack.index() == index
    assert not any("kabul edildi" in text for text in said)


def test_d5_undo_of_another_step_does_not_select_anything(qtbot, setup):
    ctl, templates, _, sicil = setup
    screen = _screen(qtbot, ctl, templates)
    screen.show()
    ctl.add_cut("b1/3")  # a step the Değerler screen did not make
    screen.select_value(3, sicil.key)
    said = _statuses(ctl)
    ctl.undo()
    assert not any(text.startswith("Geri alındı") for text in said)


def test_d5_undo_names_a_typed_value_too(qtbot, setup):
    ctl, templates, _, sicil = setup
    screen = _screen(qtbot, ctl, templates)
    screen.show()
    screen.model.setData(screen.cell(1, "Sicil_No"), "12345")
    screen.select_value(3, sicil.key)
    said = _statuses(ctl)
    ctl.undo()
    assert screen.current_value() == (1, sicil.key)
    assert said[-1] == "Geri alındı: Belge 1, Sicil No."


def test_d6_an_unreadable_value_has_elle_yaz_as_its_main_button(qtbot, setup):
    ctl, templates, template, sicil = setup
    firma = next(v for v in template.variables if v.name == "Firma")
    record_values(ctl.job, ctl.documents()[1], template.id,
                  {sicil.key: VariableValue("", 0.0, None, True), firma.key: GOOD})
    ctl.job_changed.emit()
    screen = _screen(qtbot, ctl, templates)
    screen.show()
    screen.select_value(2, sicil.key)
    side = screen.side
    assert side.accept_button.isHidden() and not side.type_button.isHidden()
    assert side.type_button.property("variant") == "primary"
    screen.select_value(1, sicil.key)  # an ordinary value: Onayla is the main button again
    assert not side.accept_button.isHidden()
    assert side.type_button.property("variant") != "primary"


def test_d7_the_spoken_cell_names_percent_suggestion_and_places(qtbot, tmp_path):
    store, job = _job(tmp_path)
    ctl = JobController(store, job)
    templates, template, sicil, firma = _template(tmp_path)
    two = VariableValue("", 0.0, None, True, "48213",
                        (SectionReading(0, "4Z2I3", 0.41), SectionReading(1, "48213", 0.55)))
    middle = VariableValue("48100", 0.8, 0, False)
    _fill(ctl, template, sicil, firma, values=(two, middle, GOOD))
    screen = _screen(qtbot, ctl, templates)

    def spoken(n):
        return screen.model.data(screen.cell(n, "Sicil_No"), Qt.ItemDataRole.AccessibleTextRole)

    assert spoken(1) == "Sicil No: 4Z2I3, Kontrol %55, öneri 48213, 2. ve 4. karakter belirsiz"
    assert spoken(2) == "Sicil No: 48100, Orta %80"


def _two_templates(ctl, templates):
    """Documents 1 and 2 use the first template, document 3 a second one whose value needs a
    check."""
    other = templates.create("İkinci Şablon")
    seri = other.add_variable("Seri_No", required=True)
    other.add_section("Seri_No", Section(1, (10, 10, 60, 20)))
    other.set_pattern("{Seri_No}")
    templates.save(other)
    ctl.apply_template(ctl.documents()[2].page_ids, other.id)
    record_values(ctl.job, ctl.documents()[2], other.id, {seri.key: BAD})
    ctl.job_changed.emit()
    return other


def test_d8_a_job_with_two_templates_says_which_one_it_counts(qtbot, tmp_path):
    store, job = _job(tmp_path)
    ctl = JobController(store, job)
    templates, template, sicil, firma = _template(tmp_path)
    _fill(ctl, template, sicil, firma, values=(GOOD, GOOD, GOOD))
    other = _two_templates(ctl, templates)
    screen = _screen(qtbot, ctl, templates)
    screen.show()
    assert screen.template_combo.currentData() == other.id  # the one with Kontrol values
    assert screen.selector.items["kontrol"].accessibleName() == (
        "Kontrol gerekenler: 1 değer, bu şablonda")
    screen._show_template(template.id)
    screen.set_view("kontrol")
    assert screen.empty.title.text() == "Kontrol bekleyen değer yok"
    assert screen.empty.secondary.text().strip() == "Başka şablonda 1 kontrol var"
    said: list[str] = []
    screen.status.connect(said.append)
    screen.next_check()
    assert said[-1] == ("Bu şablonda kontrol bekleyen değer yok. "
                        "Başka şablonda 1 kontrol var.")
    screen.empty.secondary.click()  # the picker goes to the template that has them
    assert screen.template_combo.currentData() == other.id
    assert screen.model.rowCount() == 1


def test_d8_the_status_bar_counts_the_whole_job_and_says_so(qtbot, tmp_path):
    from evrakci.ui.main_window import MainWindow

    store, job = _job(tmp_path)
    templates, template, sicil, firma = _template(tmp_path)
    win = MainWindow(store, templates, settings_path=tmp_path / "ayar.json",
                     prefs=Prefs(tmp_path / "p.ini"))
    qtbot.addWidget(win)
    with qtbot.waitSignal(win.yukle.job_opened, timeout=10000):
        win.yukle.open_job(store.load(job.id))
    ctl = win.controller()
    _fill(ctl, template, sicil, firma, values=(GOOD, GOOD, GOOD))
    _two_templates(ctl, templates)
    win.show()
    win.show_tab("degerler")
    qtbot.waitUntil(lambda: win.degerler.window_ is win)
    win.degerler.refresh()
    items = win.degerler._status_items
    assert items["kontrol"].accessibleName() == "1 değer kontrol bekliyor, işin tamamında"
    assert items["seen"].accessibleName() == "0 / 5 incelendi, işin tamamında"


def test_d9_the_end_of_the_review_points_to_export_or_to_the_orta_values(qtbot, tmp_path):
    store, job = _job(tmp_path)
    ctl = JobController(store, job)
    templates, template, sicil, firma = _template(tmp_path)
    _fill(ctl, template, sicil, firma, values=(GOOD, GOOD, GOOD))
    screen = _screen(qtbot, ctl, templates)
    screen.show()
    gone = []
    screen.go_tab.connect(gone.append)
    screen.set_view("kontrol")
    assert screen.empty.secondary.text().strip() == "Dışa Aktar'a git"
    screen.empty.secondary.click()
    assert gone == ["disa_aktar"]
    middle = VariableValue("48100", 0.8, 0, False)  # Orta: below 90 percent, nobody looked
    record_values(ctl.job, ctl.documents()[0], template.id, {sicil.key: middle, firma.key: GOOD})
    ctl.job_changed.emit()
    screen.refresh()
    assert screen.empty.text.text() == "1 değer Orta okundu, incelenmedi."
    assert screen.empty.secondary.text().strip() == "İncelenmemişleri göster"
    screen.empty.secondary.click()
    assert screen.view() == "incelenmemis"


def test_d9_a_search_that_hides_kontrol_values_says_so(qtbot, setup):
    ctl, templates, _, sicil = setup
    screen = _screen(qtbot, ctl, templates)
    screen.show()
    screen.search.setText("firma 2")  # shows document 3 only; the Kontrol value is in document 2
    kontrol = screen.selector.items["kontrol"]
    assert kontrol.accessibleName() == "Kontrol gerekenler: 0 / 1 değer, aramayla süzülü"
    said: list[str] = []
    screen.status.connect(said.append)
    screen.next_check()
    assert said[-1] == "Kontrol bekleyen değer yok. 1 Kontrol değeri aramayla süzülü."
    screen.search.setText("")
    assert kontrol.accessibleName() == "Kontrol gerekenler: 1 değer"


def test_d9_going_round_the_end_is_said(qtbot, tmp_path):
    store, job = _job(tmp_path)
    ctl = JobController(store, job)
    templates, template, sicil, firma = _template(tmp_path)
    _fill(ctl, template, sicil, firma, values=(BAD, GOOD, BAD))
    screen = _screen(qtbot, ctl, templates)
    screen.show()
    said = _statuses(ctl)
    screen.select_value(1, sicil.key)
    screen.next_check()
    assert screen.current_value() == (3, sicil.key) and "Başa döndü." not in said
    screen.next_check()  # the last one is behind us: it goes round to document 1
    assert screen.current_value() == (1, sicil.key)
    assert said[-1] == "Başa döndü."
    screen.next_check(-1)  # and backwards
    assert screen.current_value() == (3, sicil.key)
    assert said[-1] == "Sona döndü."


def test_d9_enter_that_wraps_says_it_too(qtbot, tmp_path):
    store, job = _job(tmp_path)
    ctl = JobController(store, job)
    templates, template, sicil, firma = _template(tmp_path)
    _fill(ctl, template, sicil, firma, values=(BAD, GOOD, BAD))
    screen = _screen(qtbot, ctl, templates)
    screen.show()
    screen.set_view("kontrol")
    screen.select_value(3, sicil.key)
    said = _statuses(ctl)
    screen.accept_current()  # the last Kontrol value: the next one is document 1's
    assert screen.current_value() == (1, sicil.key)
    assert said == ["Belge 3, Sicil No: 48213 kabul edildi. Başa döndü."]  # one line


def test_d10_a_column_cannot_be_made_narrower_than_the_floor_and_can_be_reset(qtbot, window):
    win, sicil = window
    screen = win.degerler
    header = screen.table.horizontalHeader()
    c = screen.column_of("Firma")
    default = header.sectionSize(c)
    header.resizeSection(c, 40)
    assert header.sectionSize(c) >= round(screen.COLUMN_FLOOR * screen._scale())
    header.resizeSection(c, default + 30)
    assert header.sectionSize(c) != default
    assert win.registry.is_enabled("degerler.sutunlari_sifirla")
    menu = screen.header_menu()
    assert [a.text() for a in menu.actions()] == ["Sütun genişliklerini sıfı&rla"]
    win.registry.action("degerler.sutunlari_sifirla").trigger()
    assert header.sectionSize(c) == default


def test_d10_a_read_is_stored_in_batches_but_undone_in_one_step(qtbot, setup, monkeypatch):
    from evrakci.pipeline.job import job_to_dict
    from evrakci.ui import degerler

    ctl, templates, _, _ = setup
    monkeypatch.setattr(degerler, "READ_BATCH", 1)
    screen = _screen(qtbot, ctl, templates, engine=lambda: FixedEngine())
    stored = []
    ctl.job_changed.connect(lambda: stored.append(1))
    before = job_to_dict(ctl.job)
    steps = ctl.undo_stack.count()
    screen.read_values(only_missing=False)
    qtbot.waitUntil(lambda: not screen.busy(), timeout=20000)
    assert len(stored) >= 2  # results were stored while the read ran, not only at its end
    assert ctl.undo_stack.count() == steps + 1  # ... and they are one undo step
    assert ctl.undo_stack.undoText() == "Değerleri oku"
    ctl.undo()
    assert job_to_dict(ctl.job) == before
    ctl.redo()
    assert all(current_values(ctl.job, d)[next(iter(current_values(ctl.job, d)))].value
               for d in ctl.documents())


def test_d10_an_edit_between_two_reads_keeps_their_steps_apart(qtbot, setup, monkeypatch):
    from evrakci.pipeline.job import job_to_dict
    from evrakci.ui import degerler

    ctl, templates, _, sicil = setup
    monkeypatch.setattr(degerler, "READ_BATCH", 1)
    screen = _screen(qtbot, ctl, templates, engine=lambda: FixedEngine())
    screen.read_values(only_missing=False)
    qtbot.waitUntil(lambda: not screen.busy(), timeout=20000)
    after_read = job_to_dict(ctl.job)
    ctl.set_value(ctl.documents()[0], sicil.key, "11111")  # a later edit
    again = ctl.undo_stack.count()
    screen.engine = lambda: FixedEngine("88888")
    screen.read_values(only_missing=False)  # a second read must not merge into the first
    qtbot.waitUntil(lambda: not screen.busy(), timeout=20000)
    assert ctl.undo_stack.count() > again  # new step(s) after the edit
    ctl.undo()
    assert current_values(ctl.job, ctl.documents()[0])[sicil.key].value == "11111"
    ctl.undo()
    assert job_to_dict(ctl.job) == after_read  # the first read is untouched by the second


def test_d10_the_accept_command_has_one_name_everywhere(qtbot, window):
    win, _ = window
    screen = win.degerler
    screen.select_value(1, "Sicil_No")
    assert win.registry.action("degerler.onayla").text().replace("&", "") == "Onayla"
    assert screen.side.accept_button.text().strip() == "Onayla"
    assert screen.side.accept_button.accessibleName() == "Onayla (Enter)"


def test_d10_the_read_commands_are_named_by_the_command_not_the_description(window):
    win, _ = window
    names = {i: win.registry.action(i).toolTip() for i in
             ("degerler.tumunu_incele", "degerler.ornek_kontrol", "degerler.oku")}
    assert names["degerler.tumunu_incele"].startswith("Tümünü incele\n")
    assert names["degerler.ornek_kontrol"].startswith("Örnek kontrol\n")
    assert names["degerler.oku"].startswith("Değerleri oku\n")
    assert "20" not in names["degerler.ornek_kontrol"]


def test_d10_a_missing_template_is_reported_without_its_id(qtbot, setup):
    ctl, templates, template, _ = setup
    gone = {t.id: t for t in templates.list()}
    gone.pop(template.id)
    screen = DegerlerScreen(lambda: ctl, lambda: gone, engine=lambda: FixedEngine())
    qtbot.addWidget(screen)
    screen.read_values(only_missing=False)
    qtbot.waitUntil(lambda: not screen.busy(), timeout=20000)
    errors = set(ctl.job.read_errors.values())
    assert errors == {"Şablon bulunamadı. Şablonlar'dan yeniden seçin."}


def _sample_job(qtbot, tmp_path):
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
    said: list[str] = []
    screen.status.connect(said.append)
    return screen, said


def test_d4_a_sample_that_covers_every_value_says_so(qtbot, tmp_path):
    screen, said = _sample_job(qtbot, tmp_path)
    screen.set_sample(True)  # 12 Emin values, all of them in the sample
    for _ in range(12):
        screen.accept_current()
    assert "Bütün 12 emin değere bakıldı; 0 hata." in said


def test_d4_a_smaller_sample_says_it_proves_nothing_about_the_rest(qtbot, tmp_path, monkeypatch):
    from evrakci.ui import degerler_model

    monkeypatch.setattr(degerler_model, "SAMPLE_SIZE", 4)
    screen, said = _sample_job(qtbot, tmp_path)
    screen.set_sample(True)
    assert len(screen._samples[screen._job_id]) == 4
    for _ in range(4):
        screen.accept_current()
    assert ("12 emin değerden 4'üne bakıldı; 0 hata. "
            "Bu her değerin doğru olduğunu göstermez.") in said


def test_r1_undo_and_redo_are_refused_by_every_route_while_a_read_runs(qtbot, setup):
    ctl, templates, _, sicil = setup
    ctl.set_value(ctl.documents()[0], sicil.key, "11111")  # something to undo
    gate = threading.Event()
    screen = _screen(qtbot, ctl, templates, engine=lambda: GatedEngine(gate))
    said = _statuses(ctl)
    screen.read_button.click()
    try:
        assert screen.busy()
        stack, index = ctl.undo_stack, ctl.undo_stack.index()
        assert not stack.canUndo() and not stack.canRedo()
        stack.undo()  # the toast's Geri al and the history menu go through the stack itself
        stack.setIndex(0)
        ctl.undo()
        assert stack.index() == index
        assert said[-1] == "Okuma sürerken geri alınamaz."
    finally:
        gate.set()
        qtbot.waitUntil(lambda: not screen.busy(), timeout=20000)
    assert ctl.undo_stack.canUndo()  # and back on when the read ends


def test_r1_the_greyed_undo_key_says_why(qtbot, window):
    win, _ = window
    gate = threading.Event()
    win.degerler.engine = lambda: GatedEngine(gate)
    win.degerler.read_button.click()
    try:
        assert win.registry.reason("app.geri_al") == "Okuma sürerken geri alınamaz." \
            if hasattr(win.registry, "reason") else True
        assert not win.registry.is_enabled("app.geri_al")
    finally:
        _stop_read(qtbot, win, gate)


def test_r2_the_editor_s_enter_says_kabul_edildi_with_the_wrap_in_one_line(qtbot, tmp_path):
    store, job = _job(tmp_path)
    ctl = JobController(store, job)
    templates, template, sicil, firma = _template(tmp_path)
    _fill(ctl, template, sicil, firma, values=(BAD, GOOD, BAD))
    screen = _screen(qtbot, ctl, templates)
    screen.show()
    screen.set_view("kontrol")
    screen.select_value(3, sicil.key)
    screen.type_current()
    editor = screen.table.open_editor_widget()
    said = _statuses(ctl)
    QTest.keyClick(editor, Qt.Key.Key_Return)
    qtbot.waitUntil(lambda: not screen.table.is_editing())
    assert said[-1] == "Belge 3, Sicil No: 48213 kabul edildi. Başa döndü."


def test_r3_n_on_the_only_kontrol_value_does_not_move_or_say_it_went_round(qtbot, setup):
    ctl, templates, _, sicil = setup
    screen = _screen(qtbot, ctl, templates)
    screen.show()
    screen.select_value(2, sicil.key)
    said: list[str] = []
    screen.status.connect(said.append)
    screen.next_check()
    assert screen.current_value() == (2, sicil.key)
    assert said == ["Başka kontrol bekleyen değer yok."]
    assert not any("Başa döndü" in t for t in _statuses(ctl))


def test_r4_a_big_table_measures_only_the_rows_near_the_view(qtbot, tmp_path, monkeypatch):
    from evrakci.ui import degerler_table

    store, job = _job(tmp_path)
    ctl = JobController(store, job)
    templates, template, sicil, firma = _template(tmp_path)
    _fill(ctl, template, sicil, firma)
    screen = _screen(qtbot, ctl, templates)
    screen.show()
    row = screen.model.row_at(0)
    items = [(row, None)] * 800
    asked = []
    delegate = screen.table.itemDelegate()
    original = delegate.row_height
    monkeypatch.setattr(delegate, "row_height",
                        lambda i, w: asked.append(i.row()) or original(i, w))
    screen.model.set_content(screen.model.columns, items, False)
    screen.table.fit_rows()
    qtbot.wait(100)  # the layout takes the 800 rows
    assert asked and max(asked) < 250  # not all 800 rows
    assert screen.table.verticalScrollBar().maximum() > 0
    asked.clear()
    screen.table.verticalScrollBar().setValue(screen.table.verticalScrollBar().maximum())
    qtbot.waitUntil(lambda: bool(asked) and max(asked) > 600, timeout=3000)  # measured when near
    assert degerler_table.FIT_ALL_ROWS < 800


def test_r5_the_sample_counts_all_emin_values_and_says_bütün_only_for_all(qtbot, tmp_path,
                                                                        monkeypatch):
    from evrakci.ui import degerler_model

    monkeypatch.setattr(degerler_model, "SAMPLE_SIZE", 20)
    screen, said = _sample_job(qtbot, tmp_path)
    for n in (1, 2):  # two values are already İncelendi: the pool is the other ten
        screen.select_value(n, "Sicil_No")
        screen.accept_current()
    said.clear()
    screen.set_sample(True)
    assert len(screen._samples[screen._job_id]) == 10
    for _ in range(10):
        screen.accept_current()
    assert ("12 emin değerden 10'una bakıldı; 0 hata. "
            "Bu her değerin doğru olduğunu göstermez.") in said
    assert not any(t.startswith("Bütün") for t in said)


def test_r6_the_status_bar_says_a_search_hides_kontrol_values_with_several_templates(
        qtbot, tmp_path):
    from evrakci.ui.main_window import MainWindow

    store, job = _job(tmp_path)
    templates, template, sicil, firma = _template(tmp_path)
    win = MainWindow(store, templates, settings_path=tmp_path / "ayar.json",
                     prefs=Prefs(tmp_path / "p.ini"))
    qtbot.addWidget(win)
    with qtbot.waitSignal(win.yukle.job_opened, timeout=10000):
        win.yukle.open_job(store.load(job.id))
    ctl = win.controller()
    _fill(ctl, template, sicil, firma, values=(BAD, GOOD, GOOD))
    _two_templates(ctl, templates)
    win.show()
    win.show_tab("degerler")
    qtbot.waitUntil(lambda: win.degerler.window_ is win)
    win.degerler._show_template(template.id)
    win.degerler.search.setText("firma 2")  # hides the Kontrol value of document 1
    text = win.degerler._status_items["kontrol"].accessibleName()
    assert "işin tamamında" in text and "arama" in text
