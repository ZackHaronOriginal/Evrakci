"""I-06: "Kontrol gerekenler" in Ölçüte göre seç…: reasons with icon, word and count, the pages
radios, the live count, the status line, and counts that equal the Değerler table.

Job of the tests: 4 documents of 3 pages and a short group of 2 pages (a filter of 3):
document 1 Kontrol, 2 Okunamadı, 3 Orta, 4 Emin, 5 not read and short ("Eksik sayfa").
"""

import pytest
from test_kontrol_a import _window

from evrakci.pipeline.cuts import compute_documents, record_values
from evrakci.pipeline.templates.model import Section, Template, Variable
from evrakci.pipeline.templates.values import SectionReading, VariableValue
from evrakci.ui.degerler_model import build_rows, count
from evrakci.ui.kontrol_dialogs import NBSP, SelectDialog

SICIL = Variable("Sicil_No", [Section(1, (10, 10, 60, 20))], True, key="k1")
TARIH = Variable("Tarih", [Section(-1, (10, 10, 60, 20))], False, key="k2")
TEMPLATE = Template("t1", "Rapor", [SICIL, TARIH])
EMIN = VariableValue("48190", 0.97, 0, False)
ORTA = VariableValue("48190", 0.80, 0, False)
KONTROL = VariableValue("", 0.0, None, True, "48213", (SectionReading(0, "482I3", 0.4),))
OKUNAMADI = VariableValue("", 0.0, None, True, "", (SectionReading(0, "", 0.0),))
SPEC = {"a": "pppq" * 4 + "pp"}


def _prepare(window, read=True):
    ctl = window.controller()
    job = ctl.job
    job.apply_template(job.ordered_page_ids(), TEMPLATE.id)
    job.apply_filter(job.ordered_page_ids()[-2:], 3)
    docs = compute_documents(job)
    if read:
        for document, sicil in zip(docs[:4], (KONTROL, OKUNAMADI, ORTA, EMIN), strict=True):
            record_values(job, document, TEMPLATE.id, {"k1": sicil, "k2": EMIN})
    window.kontrol.templates = lambda: {TEMPLATE.id: TEMPLATE}
    return job, docs


def _dialog(window, qtbot, kind="guven"):
    dialog = SelectDialog(window.controller().job, 1, [], kind, window,
                          window.kontrol.templates())
    qtbot.addWidget(dialog)
    return dialog


def _rows(window):
    return sorted(i.row() for i in window.kontrol.timeline.selectionModel().selectedIndexes())


def test_reasons_have_icon_word_count_and_orta_is_off(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, spec=SPEC)
    _prepare(window)
    dialog = _dialog(window, qtbot)
    boxes = dialog._reason_boxes
    assert [b.text() for b in boxes.values()][:5] == [
        "Kontrol", "Okunamadı", "Orta", "Okunmadı", "Eksik sayfa"]
    assert [b.isChecked() for b in boxes.values()][:5] == [True, True, False, True, True]
    assert not boxes["kontrol"].icon().isNull() and boxes["eksik sayfa"].icon().isNull()
    assert boxes["kontrol"].accessibleName() == "Kontrol, 1 değer"
    assert boxes["okunmadi"].accessibleName() == "Okunmadı, 1 belge"
    assert boxes["eksik sayfa"].accessibleName() == "Eksik sayfa, 1 belge"
    assert dialog._reason_counts["orta"].text() == f"1{NBSP}değer"
    assert boxes["karışık şablon"].isHidden()  # only shown when a document has it
    assert dialog.pages_value.isChecked() and dialog.pages_label.text() == "Sayfalar"
    assert dialog.guven_count.text() == f"3{NBSP}belge, 4{NBSP}sayfa"


def test_live_count_follows_the_boxes_and_the_pages_radios(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, spec=SPEC)
    _prepare(window)
    dialog = _dialog(window, qtbot)
    dialog._reason_boxes["orta"].setChecked(True)
    assert dialog.guven_count.text() == f"4{NBSP}belge, 5{NBSP}sayfa"
    dialog.pages_document.setChecked(True)
    assert dialog.guven_count.text() == f"4{NBSP}belge, 11{NBSP}sayfa"  # 3 + 3 + 3 + 2
    assert dialog._counts["guven"].text() == "11"
    for box in dialog._reason_boxes.values():
        box.setChecked(False)
    assert dialog.guven_count.text() == f"0{NBSP}belge, 0{NBSP}sayfa"
    assert dialog._counts["guven"].text() == "Hiç yok"


def test_counts_equal_the_selection_and_the_degerler_table(qtbot, tmp_path, monkeypatch):
    window = _window(qtbot, tmp_path, spec=SPEC)
    job, docs = _prepare(window)
    rows = build_rows(job, docs, {TEMPLATE.id: TEMPLATE})
    table = count(rows)
    dialog = _dialog(window, qtbot)
    totals = dialog._reason_totals
    assert totals["kontrol"] + totals["okunamadi"] == table.kontrol == 2
    assert totals["okunmadi"] == table.unread_documents == 1
    status, seen = [], {}
    window.controller().status.connect(status.append)

    def answer(chosen):
        seen["text"] = chosen.guven_count.text()
        seen["criterion"] = chosen.criterion()
        return True

    monkeypatch.setattr(SelectDialog, "exec", answer)
    window.kontrol.select_by("guven")
    rows_selected = _rows(window)
    assert seen["text"] == f"3{NBSP}belge, {len(rows_selected)}{NBSP}sayfa"
    assert status[-1] == "3 belge seçildi: Kontrol 1, Okunamadı 1, Okunmadı 1, Eksik sayfa 1"


def test_row_is_off_with_the_reason_when_no_values_are_read(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, spec=SPEC)
    _prepare(window, read=False)
    dialog = _dialog(window, qtbot)
    assert dialog.kind() == "belge"  # it opens on the first row instead
    assert not dialog._radios["guven"].isEnabled()
    assert dialog._counts["guven"].text() == "Değerler henüz okunmadı"
    assert dialog._radios["guven"].accessibleName() == "Kontrol gerekenler, Değerler henüz okunmadı"


@pytest.mark.parametrize("scale", [100, 150])
def test_dialog_builds_once_and_opens_fast(qtbot, tmp_path, scale):
    import time

    window = _window(qtbot, tmp_path, spec={"a": "pppq" * 200})
    job = window.controller().job
    job.apply_template(job.ordered_page_ids(), TEMPLATE.id)
    for i, document in enumerate(compute_documents(job)):
        record_values(job, document, TEMPLATE.id,
                      {"k1": (KONTROL, EMIN, ORTA, OKUNAMADI)[i % 4], "k2": EMIN})
    window.kontrol.templates = lambda: {TEMPLATE.id: TEMPLATE}
    start = time.perf_counter()
    dialog = _dialog(window, qtbot)
    elapsed_ms = (time.perf_counter() - start) * 1000
    print(f"dialog open (800 pages, 200 documents): {elapsed_ms:.0f} ms")
    assert elapsed_ms < 1500
    assert dialog._reason_totals["kontrol"] == 50
