"""R3 (Q-11): the Yükle texts and behaviours the owner approved on the plain list (Y-3 to Y-14).
Synthetic PDFs only."""
from __future__ import annotations

from pathlib import Path

import pytest
from fakes import make_pdf, qr_page, text_page
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QInputDialog

from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.ui import motion
from evrakci.ui.main_window import MainWindow
from evrakci.ui.prefs import Prefs
from evrakci.ui.yukle import _Reading, added_text
from evrakci.ui.yukle_info import batch_edits, possessive, reason
from evrakci.ui.yukle_parts import EmptyPage, JobEntry
from evrakci.ui.yukle_table import STATUSES


def _window(qtbot, tmp_path):
    window = MainWindow(JobStore(tmp_path / "jobs"), TemplateStore(tmp_path / "tpl"),
                        settings_path=tmp_path / "ayar.json", prefs=Prefs(tmp_path / "p.ini"))
    qtbot.addWidget(window)
    window.show()
    qtbot.waitUntil(lambda: window.yukle.window_ is window, timeout=3000)
    return window


@pytest.fixture
def files(tmp_path):
    a = make_pdf(tmp_path / "tarama-1.pdf", [text_page("A"), qr_page(), text_page("B")])
    b = make_pdf(tmp_path / "tarama-2.pdf", [text_page("C"), text_page("D")])
    return a, b


def _open(qtbot, window, paths, name="Kasım"):
    job = window.store.create_job(name, paths)
    with qtbot.waitSignal(window.yukle.job_opened, timeout=10000):
        window.yukle.open_job(window.store.load(job.id))
    return window.yukle


# -- Y-3 ---------------------------------------------------------------------------------
def test_removing_a_batch_with_edits_says_the_edits_go_too(qtbot, tmp_path, files):
    a, b = files
    window = _window(qtbot, tmp_path)
    screen = _open(qtbot, window, [a, b])
    first, second = screen.controller.job.batches
    screen.controller.job.deleted.add(f"{first.id}/0")
    screen.controller.job.manual_cuts.add(f"{first.id}/2")
    assert batch_edits(screen.controller.job, first.id) == 2
    assert batch_edits(screen.controller.job, second.id) == 0
    screen.table.select_batch(first.id)
    screen.remove_batch()
    assert screen.last_message == ("tarama-1.pdf işten çıkarıldı; "
                                   "bu partinin sayfalarındaki düzenlemeler de gitti.")
    screen.controller.undo_stack.undo()  # Geri al brings the edits back with the batch
    assert batch_edits(screen.controller.job, first.id) == 2


def test_removing_a_batch_without_edits_keeps_the_short_toast(qtbot, tmp_path, files):
    a, b = files
    window = _window(qtbot, tmp_path)
    screen = _open(qtbot, window, [a, b])
    screen.table.select_batch(screen.controller.job.batches[1].id)
    screen.remove_batch()
    assert screen.last_message == "tarama-2.pdf işten çıkarıldı."


# -- Y-4 ---------------------------------------------------------------------------------
def test_an_empty_job_name_asks_again_and_says_why(qtbot, tmp_path, files, monkeypatch):
    a, _b = files
    window = _window(qtbot, tmp_path)
    screen = _open(qtbot, window, [a])
    asked: list[tuple[str, str]] = []
    answers = iter([("   ", True), ("Yeni ad", True)])

    def get_text(_parent, title, label, *_a, **kw):
        asked.append((label, kw.get("text", "")))
        return next(answers)

    monkeypatch.setattr(QInputDialog, "getText", staticmethod(get_text))
    screen.rename_job()
    assert screen.controller.job.name == "Yeni ad"
    assert asked[0][0] == "İşin adı:" and asked[1][0] == "İşin adı:\nİş adı boş olamaz."
    assert asked[1][1] == "Kasım"
    assert screen.last_message == "İş adı boş olamaz."


def test_cancelling_the_name_dialog_changes_nothing(qtbot, tmp_path, files, monkeypatch):
    a, _b = files
    window = _window(qtbot, tmp_path)
    screen = _open(qtbot, window, [a])
    monkeypatch.setattr(QInputDialog, "getText", staticmethod(lambda *a, **k: ("", False)))
    screen.rename_job()
    assert screen.controller.job.name == "Kasım"


# -- Y-5 ---------------------------------------------------------------------------------
def test_a_damaged_job_is_named_with_a_next_step(qtbot, tmp_path, files):
    a, _b = files
    window = _window(qtbot, tmp_path)
    job = window.store.create_job("Bozuk iş", [a])
    window.store._job_file(job.id).write_text("{ bu json degil", encoding="utf-8")
    window.yukle.open_job_id(job.id, "Bozuk iş")
    qtbot.waitUntil(lambda: window.yukle.last_message != "", timeout=5000)
    assert window.yukle.last_message == "Bozuk iş açılamadı. İş klasörünü kontrol edin."
    assert job.id not in window.yukle.last_message


# -- Y-6, Y-9 (inspector) -----------------------------------------------------------------
def test_the_inspector_leads_with_what_needs_action(qtbot, tmp_path, files):
    a, _b = files
    window = _window(qtbot, tmp_path)
    screen = _open(qtbot, window, [a])
    info = screen._summary()
    assert info.checks == 0 and screen.side.title.text() == "3 sayfa"
    assert screen.side.state_row.value.text() == "Hazır"
    from dataclasses import replace

    flagged = replace(info, checks=2)
    screen.side.show_job(flagged, None)
    assert screen.side.title.text() == "2 belge kontrol bekliyor"
    assert screen.side.sub.text() == f"3 sayfa, 1 parti, {info.documents} belge bulundu"
    assert screen.side.state_row.value.text() == "2 belge kontrol bekliyor"


def test_an_empty_job_says_there_is_no_batch_yet(qtbot, tmp_path, files):
    a, _b = files
    window = _window(qtbot, tmp_path)
    screen = _open(qtbot, window, [a])
    screen.table.select_batch(screen.controller.job.batches[0].id)
    screen.remove_batch()
    assert screen.side.state_row.value.text() == "Henüz parti yok"


# -- Y-7 ---------------------------------------------------------------------------------
def test_the_qr_sentence_names_at_most_three_batches():
    assert reason([5, 0, 0]).startswith("1 parti QR ayıraçlı; 2. ve 3. partilerde ayıraç yok")
    many = reason([9] + [0] * 40)
    assert "2., 3., 4. ve 37 partide ayıraç yok" in many and len(many) < 120
    assert reason([9, 0, 0, 0, 0]).startswith("1 parti QR ayıraçlı; 2., 3., 4. ve 1 partide")


# -- Y-8 ---------------------------------------------------------------------------------
def test_the_progress_card_has_its_own_cancel_and_the_read_is_announced(qtbot, tmp_path, files):
    a, b = files
    window = _window(qtbot, tmp_path)
    screen = _open(qtbot, window, [a])
    stop = screen.progress.stop_button
    assert stop is not None and stop.text() == "İptal et"
    assert stop.property("action_id") == "yukle.iptal" and "Ctrl+." in stop.toolTip()
    reading = _Reading([a, b], [3, 2])
    spoken: list[str] = []
    screen._reading = reading
    import evrakci.ui.yukle as module

    original = module.announce
    module.announce = lambda _w, text: spoken.append(text)
    try:
        for done in (1, 2, 3, 4, 5):
            reading.done = done
            screen._announce_progress(reading)
        screen._reading = None
    finally:
        module.announce = original
    assert spoken == ["Okuma başladı: 5 sayfa", "Okuma: %25 bitti", "Okuma: %50 bitti",
                      "Okuma: %75 bitti"]


def test_the_card_cancel_stops_the_read_and_a_finished_read_is_announced(qtbot, tmp_path, files):
    a, b = files
    window = _window(qtbot, tmp_path)
    screen = _open(qtbot, window, [a])
    screen.add_batches([b])
    screen.progress.stop_button.click()
    qtbot.waitUntil(lambda: not screen.busy(), timeout=10000)
    assert len(screen.controller.job.batches) in (1, 2)  # cancelled in time, or already done
    screen.add_batches([b])
    qtbot.waitUntil(lambda: not screen.busy(), timeout=10000)
    assert screen._live.accessibleName() == "Okuma bitti."


# -- Y-10 --------------------------------------------------------------------------------
def test_finished_files_say_okundu():
    assert STATUSES["okundu"][3] == "Okundu"
    reading = _Reading([Path(n) for n in ("a", "b", "c")], [10, 20, 5])
    reading.done = 12  # inside the second file
    assert [row[2] for row in reading.rows()] == ["okundu", "okunuyor", "sirada"]


def test_the_waiting_bar_stands_still_under_reduced_motion(qtbot):
    from evrakci.ui.loading import ProgressCard

    card = ProgressCard()
    qtbot.addWidget(card)
    motion.set_reduced_motion_override(True)
    try:
        card.show_waiting("Dosyalar sayılıyor: 2", "a.pdf")
        assert (card.bar.minimum(), card.bar.maximum()) == (0, 1) and card.bar.value() == 0
    finally:
        motion.set_reduced_motion_override(None)
    # motion on (forced: a Windows CI runner may have system animations off)
    motion.set_reduced_motion_override(False)
    try:
        card.show_waiting("Dosyalar sayılıyor: 2", "a.pdf")
        assert (card.bar.minimum(), card.bar.maximum()) == (0, 0)
    finally:
        motion.set_reduced_motion_override(None)


def test_the_add_toast_reports_documents_and_checks(qtbot, tmp_path, files):
    a, b = files
    window = _window(qtbot, tmp_path)
    screen = _open(qtbot, window, [a])
    screen.add_batches([b])
    qtbot.waitUntil(lambda: not screen.busy(), timeout=10000)
    # tarama-2 has no QR page: its pages go on the last document of tarama-1 (one document)
    assert screen.last_message == "tarama-2.pdf eklendi; 1 belge bulundu."
    from evrakci.ui.yukle_info import JobSummary

    info = JobSummary("x", 5, 1, 2, 1, (), "", ((frozenset({"a"}), False),
                                               (frozenset({"a", "b"}), True),
                                               (frozenset({"c"}), True)))
    assert info.found_in({"b"}) == (1, 1) and info.found_in({"a", "b"}) == (2, 1)
    assert info.found_in({"d"}) == (0, 0)
    assert added_text(3, "x", 6, 2) == "3 parti eklendi; 6 belge bulundu, 2'si kontrol bekliyor."
    assert added_text(3, "x", 6, 0) == "3 parti eklendi; 6 belge bulundu."
    assert added_text(1, "x.pdf", 0, 0) == "x.pdf eklendi."


def test_possessive_suffixes():
    assert [possessive(n) for n in (1, 2, 3, 4, 5, 6, 7, 8, 9)] == [
        "1'i", "2'si", "3'ü", "4'ü", "5'i", "6'sı", "7'si", "8'i", "9'u"]
    assert [possessive(n) for n in (10, 12, 20, 30, 40, 50, 60, 70, 80, 90, 100, 1000)] == [
        "10'u", "12'si", "20'si", "30'u", "40'ı", "50'si", "60'ı", "70'i", "80'i", "90'ı",
        "100'ü", "1000'i"]


# -- Y-9 empty page ----------------------------------------------------------------------
def test_the_empty_page_says_no_open_job_when_jobs_exist(qtbot):
    page = EmptyPage()
    qtbot.addWidget(page)
    page.set_mode("empty")
    assert page.title.text() == "Henüz iş yok"  # the very first start
    page.set_jobs([JobEntry("j1", "Kasım", 12, "dün")])
    assert page.title.text() == "Açık iş yok"
    assert page.text.text() == "Son işlerinizden birini açın ya da yeni bir iş oluşturun."
    page.set_jobs([])
    assert page.title.text() == "Henüz iş yok"


# -- Y-9 bar -----------------------------------------------------------------------------
def test_the_new_job_button_has_its_word(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    button = window.command_bar("yukle").button_for("app.yeni_is")
    assert button.text() == "Yeni iş" and button.labelled()


def test_a_read_error_bar_sits_under_the_table_and_rows_keep_their_place(qtbot, tmp_path, files):
    a, _b = files
    window = _window(qtbot, tmp_path)
    screen = _open(qtbot, window, [a])
    QApplication.processEvents()
    top = screen.table.mapTo(screen, screen.table.rect().topLeft()).y()
    screen._fail("PDF açılamadı: x.pdf")
    QApplication.processEvents()
    assert screen.table.mapTo(screen, screen.table.rect().topLeft()).y() == top
    assert screen._error is not None and screen._error.y() > screen.card.y()


# -- Y-11 --------------------------------------------------------------------------------
def test_enter_and_double_click_open_kontrol_at_the_batch(qtbot, tmp_path, files):
    a, b = files
    window = _window(qtbot, tmp_path)
    screen = _open(qtbot, window, [a, b])
    second = screen.controller.job.batches[1]
    screen.table.select_batch(second.id)
    screen.table.setFocus()
    QTest.keyClick(screen.table, Qt.Key.Key_Return)
    assert window.current_tab() == "kontrol"
    kontrol = window.kontrol
    assert kontrol.model.page_id(kontrol.timeline.currentIndex().row()) == f"{second.id}/0"
    window.show_tab("yukle")
    screen.table.select_batch(screen.controller.job.batches[0].id)
    row = screen.table.model().row_of(second.id)
    index = screen.table.model().index(row, 2)
    rect = screen.table.visualRect(index)
    QTest.mouseDClick(screen.table.viewport(), Qt.MouseButton.LeftButton, pos=rect.center())
    assert window.current_tab() == "kontrol"
    assert kontrol.model.page_id(kontrol.timeline.currentIndex().row()) == f"{second.id}/0"


def test_open_in_kontrol_is_in_the_menu_and_the_row_menu(qtbot, tmp_path, files):
    a, _b = files
    window = _window(qtbot, tmp_path)
    _open(qtbot, window, [a])
    action = window.registry.action("yukle.kontrolde_ac")
    assert action.isEnabled()
    window.registry.action("yukle.kontrolde_ac").trigger()
    assert window.current_tab() == "kontrol"


# -- Y-13 --------------------------------------------------------------------------------
def test_the_counting_phase_is_called_counting(qtbot):
    from evrakci.ui.loading import ProgressCard

    card = ProgressCard()
    qtbot.addWidget(card)
    import inspect

    import evrakci.ui.yukle as module

    assert "Dosyalar sayılıyor" in inspect.getsource(module.YukleScreen._begin)
    assert "inceleniyor" not in inspect.getsource(module)


# -- second round ------------------------------------------------------------------------
def test_removing_a_batch_counts_every_edit_remove_batch_drops(qtbot, tmp_path, files):
    from evrakci.pipeline.job import FilterApplication

    a, b = files
    window = _window(qtbot, tmp_path)
    screen = _open(qtbot, window, [a, b])
    job = screen.controller.job
    first = job.batches[0]
    job.rotations[f"{first.id}/1"] = 90
    job.filters.append(FilterApplication(frozenset({f"{first.id}/0"}), 2))
    assert batch_edits(job, first.id) == 2
    screen.table.select_batch(first.id)
    screen.remove_batch()
    assert screen.last_message == ("tarama-1.pdf işten çıkarıldı; "
                                   "bu partinin sayfalarındaki düzenlemeler de gitti.")


def test_a_failed_or_cancelled_read_is_announced(qtbot, tmp_path, files):
    a, _b = files
    window = _window(qtbot, tmp_path)
    _open(qtbot, window, [a])
    screen = window.yukle
    spoken: list[str] = []
    import evrakci.ui.yukle as module

    original = module.announce
    module.announce = lambda _w, text: spoken.append(text)
    try:
        screen._finish(None, None, cancelled=True)
        assert spoken[-1] == module.CANCELLED_TEXT
        screen._finish(None, None, error="PDF açılamadı: x.pdf")
        assert spoken[-1] == screen.last_message and "PDF açılamadı: x.pdf" in spoken[-1]
    finally:
        module.announce = original


def test_rows_count_a_zero_page_file_and_the_last_file_as_done():
    reading = _Reading([Path(n) for n in ("a", "b", "c")], [5, 0, 5])
    reading.done = 7
    assert [r[2] for r in reading.rows()] == ["okundu", "okundu", "okunuyor"]
    reading.done = 10  # the read is over: the last file says okundu too
    assert [r[2] for r in reading.rows()] == ["okundu", "okundu", "okundu"]


def test_empty_name_dialog_comes_back_with_the_previous_name(qtbot, tmp_path, files, monkeypatch):
    a, _b = files
    window = _window(qtbot, tmp_path)
    screen = _open(qtbot, window, [a])
    seen: list[str] = []
    answers = iter([("  ", True), ("Ad", True)])

    def get_text(_p, _t, _l, *_a, **kw):
        seen.append(kw.get("text"))
        return next(answers)

    monkeypatch.setattr(QInputDialog, "getText", staticmethod(get_text))
    screen.rename_job()
    assert seen == ["Kasım", "Kasım"]  # the previous name is back in the field


def test_cancel_in_the_card_moves_focus_to_the_table(qtbot, tmp_path, files):
    a, b = files
    window = _window(qtbot, tmp_path)
    screen = _open(qtbot, window, [a])
    screen.add_batches([b])
    screen.progress.stop_button.setFocus()
    screen._stop_clicked()
    assert QApplication.focusWidget() is screen.table
    qtbot.waitUntil(lambda: not screen.busy(), timeout=10000)
