"""Yükle as drawn in final-a/yukle.html: the batch table, the inspector, reading progress,
the window-wide drop, the empty page and the registry actions of the tab."""
from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest
from fakes import empty_page, make_pdf, qr_page, text_page
from PySide6.QtCore import QMimeData, QModelIndex, Qt, QUrl
from PySide6.QtGui import QAccessible
from PySide6.QtWidgets import QApplication, QInputDialog

from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.ui import theme
from evrakci.ui.main_window import MainWindow
from evrakci.ui.prefs import Prefs
from evrakci.ui.yukle import YukleScreen, _Reading
from evrakci.ui.yukle_info import paper_name, reason, scan_profile, summarize
from evrakci.ui.yukle_parts import (
    EmptyPage,
    JobEntry,
    collect_pdfs,
    eta_text,
    human_size,
    rate_text,
)
from evrakci.ui.yukle_table import (
    FILE,
    GRIP,
    MIME,
    PAGES,
    QR,
    STATUS,
    STATUSES,
    BatchModel,
)


@pytest.fixture
def pdfs(tmp_path):
    (tmp_path / "in").mkdir()
    a = make_pdf(tmp_path / "in" / "tarama-1.pdf", [text_page("A"), qr_page(), text_page("B")])
    b = make_pdf(tmp_path / "in" / "tarama-2.pdf", [text_page("C"), empty_page()])
    c = make_pdf(tmp_path / "in" / "tarama-10.pdf", [text_page("D"), text_page("E")])
    return [a, b, c]


@pytest.fixture
def look():
    m = theme.manager()
    mode, scale = m.mode(), m.text_scale()
    yield m
    m.set_text_scale(scale)
    m.set_mode(mode)


def _window(qtbot, tmp_path, show=True) -> MainWindow:
    window = MainWindow(JobStore(tmp_path / "jobs"), TemplateStore(tmp_path / "tpl"),
                        settings_path=tmp_path / "ayar.json", prefs=Prefs(tmp_path / "p.ini"))
    qtbot.addWidget(window)
    if show:
        window.show()
    qtbot.waitUntil(lambda: window.yukle.window_ is window, timeout=3000)
    return window


def _open(window, pdfs, name="Kasım"):
    job = window.store.create_job(name, pdfs)
    window.yukle.open_job(window.store.load(job.id))
    return window.yukle


def _names(screen) -> list[str]:
    return [i.name for i in screen.model.items if i.kind == "batch"]


class _Drag:
    """The part of a QDropEvent the screen reads."""

    def __init__(self, paths):
        self.data = QMimeData()
        self.data.setUrls([QUrl.fromLocalFile(str(p)) for p in paths])
        self.accepted = False

    def mimeData(self):  # noqa: N802
        return self.data

    def acceptProposedAction(self):  # noqa: N802
        self.accepted = True


# -- pure counts ------------------------------------------------------------------------
def test_reason_names_the_batches_without_separators():
    assert reason([27, 26, 24, 0]).startswith("3 parti QR ayıraçlı; 4. partide ayıraç yok")
    assert reason([3, 2]) == "2 partinin hepsi QR ayıraçlı."
    assert "Partide QR ayıraç yok" in reason([0])
    assert reason([0, 4, 0]).startswith("1 parti QR ayıraçlı; 1. ve 3. partilerde")
    assert reason([]).startswith("Henüz parti yok")


def test_summary_counts_pages_separators_documents_and_flags_batches(tmp_path, pdfs):
    store = JobStore(tmp_path / "s")
    job = store.create_job("İş", pdfs)
    from evrakci.pipeline.cuts import compute_documents

    documents = compute_documents(job)
    info = summarize(job, documents, [])
    assert (info.pages, info.qr, info.parties) == (7, 1, 3)
    assert [b.status for b in info.batches] == ["hazir", "kontrol", "kontrol"]  # no QR = Kontrol
    assert info.checks == 0 and info.documents == len(documents)
    assert [b.qr for b in info.batches] == [1, 0, 0]
    flagged = summarize(job, documents, [documents[0]])  # a document of batch 1 needs a look
    assert flagged.checks == 1 and flagged.batches[0].status == "kontrol"


def test_scan_profile_reads_resolution_colour_and_paper_from_the_file(tmp_path, pdfs):
    profile = scan_profile(pdfs[0])
    assert profile is not None
    assert profile.title == "100 dpi, gri tonlamalı"
    assert profile.detail == "A4, dosyalardan okundu"
    assert scan_profile(tmp_path / "yok.pdf") is None
    assert paper_name(595, 842) == "A4" and paper_name(300, 400) == "106 × 141 mm"


def test_text_helpers_use_turkish_numbers():
    assert human_size(18_400_000) == "18,4 MB" and human_size(500) == "1 KB"
    assert rate_text(3.2) == "3,2 sayfa/sn"
    assert eta_text(40) == "Yaklaşık 40 sn kaldı" and eta_text(180) == "Yaklaşık 3 dk kaldı"
    assert eta_text(None) == "Süre hesaplanıyor…"


def test_collect_pdfs_reads_folders_in_natural_order_and_skips_other_files(tmp_path, pdfs):
    folder = pdfs[0].parent
    (folder / "not.txt").write_text("x", encoding="utf-8")
    (folder / "alt").mkdir()
    sub = make_pdf(folder / "alt" / "tarama-3.pdf", [text_page()])
    found = collect_pdfs([folder, pdfs[0]])
    assert found.count(pdfs[0]) == 1 and sub in found
    assert all(p.suffix == ".pdf" for p in found)
    names = [p.name for p in found if p.parent == folder]
    assert names == ["tarama-1.pdf", "tarama-2.pdf", "tarama-10.pdf"]


# -- the table ---------------------------------------------------------------------------
def test_table_rows_total_and_status_words(qtbot, tmp_path, pdfs):
    screen = YukleScreen(JobStore(tmp_path / "s"))
    qtbot.addWidget(screen)
    screen.open_job(screen.store.load(screen.store.create_job("İş", pdfs).id))
    items = screen.model.items
    assert [i.kind for i in items] == ["batch", "batch", "batch", "total"]
    total = items[-1]
    assert (total.pages, total.qr, total.parties) == (7, 1, 3)
    text = screen.model.text
    assert [text(items[0], c) for c in (1, FILE, PAGES, QR, STATUS)] == [
        "1", "tarama-1.pdf", "3", "1", "Hazır"]
    assert text(items[1], STATUS) == "Kontrol" and text(total, STATUS) == "3 parti"
    # status is an icon and a word, never colour alone
    assert all(icon and word for icon, _role, _strong, word in STATUSES.values())
    index = screen.model.index(1, FILE)
    assert "Parti 2: tarama-2.pdf, 2 sayfa, 0 QR ayıraç, Kontrol" == index.data(
        Qt.ItemDataRole.AccessibleTextRole)
    assert screen.table.selected_batch() == screen.controller.job.batches[0].id


def test_the_total_row_and_the_reading_rows_cannot_be_selected_or_dragged(qtbot, tmp_path, pdfs):
    screen = YukleScreen(JobStore(tmp_path / "s"))
    qtbot.addWidget(screen)
    screen.open_job(screen.store.load(screen.store.create_job("İş", pdfs).id))
    screen.model.set_pending([("yeni.pdf", 12, "okunuyor"), ("sonra.pdf", 4, "sirada")])
    kinds = [i.kind for i in screen.model.items]
    assert kinds == ["batch"] * 3 + ["pending", "pending", "total"]
    for row in (3, 4, 5):
        flags = screen.model.flags(screen.model.index(row, 0))
        assert not flags & Qt.ItemFlag.ItemIsSelectable
        assert not flags & Qt.ItemFlag.ItemIsDragEnabled
    assert screen.model.items[-1].qr is None  # "…" until they are read
    assert screen.model.text(screen.model.items[-1], QR) == "…"
    assert [screen.model.text(i, STATUS) for i in screen.model.items[3:5]] == [
        "Okunuyor", "Sırada"]


def test_dropping_a_row_reorders_by_the_gap_it_lands_in(qtbot, tmp_path, pdfs):
    screen = YukleScreen(JobStore(tmp_path / "s"))
    qtbot.addWidget(screen)
    screen.open_job(screen.store.load(screen.store.create_job("İş", pdfs).id))
    model, wanted = screen.model, []
    model.move_requested.disconnect(screen.move_batch_to)  # only listen: do not move
    model.move_requested.connect(lambda batch, target: wanted.append((batch, target)))
    first, _second, third = (b.id for b in screen.controller.job.batches)

    def drop(batch, row, parent=None):
        parent = parent or QModelIndex()
        data = QMimeData()
        data.setData(MIME, batch.encode())
        return model.dropMimeData(data, Qt.DropAction.CopyAction, row, 0, parent)

    assert drop(first, 3)  # into the gap after the last batch
    assert drop(third, 0)  # before the first
    assert drop(first, -1, model.index(2, 0))  # onto the third = its place
    assert drop(third, -1)  # below the rows = the end (it is already there: nothing to do)
    assert wanted == [(first, 2), (third, 0), (first, 2)]
    assert not drop("b99", 0)
    assert model.mimeTypes() == [MIME]
    assert model.flags(QModelIndex()) & Qt.ItemFlag.ItemIsDropEnabled


def test_moving_by_key_and_dragging_are_one_undoable_edit(qtbot, tmp_path, pdfs):
    screen = YukleScreen(JobStore(tmp_path / "s"))
    qtbot.addWidget(screen)
    screen.open_job(screen.store.load(screen.store.create_job("İş", pdfs).id))
    ids = [b.id for b in screen.controller.job.batches]
    screen.table.select_batch(ids[0])
    screen.move_batch(1)
    assert _names(screen) == ["tarama-2.pdf", "tarama-1.pdf", "tarama-10.pdf"]
    assert screen.table.selected_batch() == ids[0]  # the selection follows the batch
    screen.move_batch_to(ids[2], 0)  # what a drop asks for
    assert _names(screen)[0] == "tarama-10.pdf"
    screen.controller.undo()
    screen.controller.undo()
    assert _names(screen) == ["tarama-1.pdf", "tarama-2.pdf", "tarama-10.pdf"]
    screen.table.select_batch(ids[0])
    screen.move_batch(-1)  # already first: nothing happens
    assert not screen.controller.undo_stack.canUndo()


def test_removing_a_batch_is_undoable_without_a_question(qtbot, tmp_path, pdfs):
    screen = YukleScreen(JobStore(tmp_path / "s"))
    qtbot.addWidget(screen)
    screen.open_job(screen.store.load(screen.store.create_job("İş", pdfs).id))
    ids = [b.id for b in screen.controller.job.batches]
    screen.table.select_batch(ids[1])
    screen.remove_batch()
    assert _names(screen) == ["tarama-1.pdf", "tarama-10.pdf"]
    assert screen.table.selected_batch() == ids[2]  # focus stays on the neighbour
    assert screen.last_message == "tarama-2.pdf işten çıkarıldı."
    screen.controller.undo()
    assert _names(screen) == ["tarama-1.pdf", "tarama-2.pdf", "tarama-10.pdf"]
    assert screen.controller.job.pages  # the pages came back with it
    assert f"{ids[1]}/0" in screen.controller.job.pages


# -- the window: keys, actions, command bar, status bar --------------------------------------
def test_yukle_actions_are_connected_and_follow_the_selection(qtbot, tmp_path, pdfs):
    window = _window(qtbot, tmp_path)
    registry = window.registry
    window.show_tab("yukle")
    for action_id in ("yukle.yukari", "yukle.asagi", "yukle.cikar", "yukle.yeniden_adlandir",
                      "yukle.gezginde_goster", "yukle.iptal"):
        assert not registry.is_enabled(action_id), action_id  # no job: nothing to do
    screen = _open(window, pdfs)
    first = screen.controller.job.batches[0].id
    assert registry.is_enabled("yukle.asagi") and not registry.is_enabled("yukle.yukari")
    assert registry.is_enabled("yukle.cikar") and registry.is_enabled("yukle.yeniden_adlandir")
    assert registry.is_enabled("yukle.gezginde_goster")
    assert not registry.is_enabled("yukle.iptal")
    screen.table.select_batch(screen.controller.job.batches[2].id)
    assert registry.is_enabled("yukle.yukari") and not registry.is_enabled("yukle.asagi")
    registry.action("yukle.yukari").trigger()
    assert _names(screen)[1] == "tarama-10.pdf"
    registry.action("yukle.cikar").trigger()
    assert "tarama-10.pdf" not in _names(screen)
    window.undo()
    assert "tarama-10.pdf" in _names(screen)
    assert first in [b.id for b in screen.controller.job.batches]


def test_alt_arrows_and_del_work_from_the_table(qtbot, tmp_path, pdfs):
    from PySide6.QtTest import QTest

    window = _window(qtbot, tmp_path)
    window.activateWindow()
    assert QTest.qWaitForWindowActive(window)  # window shortcuts need the active window
    screen = _open(window, pdfs)
    screen.table.setFocus()
    screen.table.select_batch(screen.controller.job.batches[0].id)
    QTest.keyClick(screen.table, Qt.Key.Key_Down, Qt.KeyboardModifier.AltModifier)
    assert _names(screen) == ["tarama-2.pdf", "tarama-1.pdf", "tarama-10.pdf"]
    QTest.keyClick(screen.table, Qt.Key.Key_Delete)
    assert _names(screen) == ["tarama-2.pdf", "tarama-10.pdf"]


def test_f2_renames_the_job_and_the_title_band_follows(qtbot, tmp_path, pdfs, monkeypatch):
    window = _window(qtbot, tmp_path)
    screen = _open(window, pdfs)
    monkeypatch.setattr(QInputDialog, "getText", staticmethod(lambda *a, **k: ("Yeni ad", True)))
    window.registry.action("yukle.yeniden_adlandir").trigger()
    assert screen.controller.job.name == "Yeni ad"
    assert window.job_switch.name.full_text() == "Yeni ad"
    window.undo()
    assert window.job_switch.name.full_text() == "Kasım"


def test_command_bar_follows_the_mockup_and_cancel_shows_only_while_reading(qtbot, tmp_path,
                                                                           pdfs):
    window = _window(qtbot, tmp_path)
    window.show_tab("yukle")
    bar = window.command_bar("yukle")
    labelled = [b.text() for b in bar.findChildren(type(bar.buttons()[0])) if b.labelled()]
    assert "Dosya ekle…" in labelled and "Kontrol'e geç" in labelled
    names = [b.accessibleName() for b in bar.findChildren(type(bar.buttons()[0]))]
    assert any(n.startswith("Klasör ekle") for n in names)
    screen = window.yukle
    cancel = screen._own["cancel"]
    assert cancel.isHidden() or not cancel.isVisibleTo(bar)
    go = bar.button_for("app.sekme.kontrol")
    assert not go.isEnabled()  # no job
    _open(window, pdfs)
    assert go.isEnabled()
    screen._reading = _Reading(pdfs[:1], [3])
    screen._sync_actions()
    assert cancel.isVisibleTo(bar) and cancel.text() == "İptal et"
    assert not go.isEnabled()  # A: disabled while a batch is read
    window.registry.action("app.sekme.kontrol").changed.emit()  # an action change or
    bar.refresh()  # a restyle does not switch it back on
    assert not go.isEnabled()
    assert window.registry.is_enabled("app.sekme.kontrol")  # Ctrl+2 still switches tabs
    assert window.registry.is_enabled("yukle.iptal")
    screen._reading = None
    screen._sync_actions()
    assert go.isEnabled() and not cancel.isVisibleTo(bar)


def test_status_bar_line_is_parti_sayfa_belge_in_that_order(qtbot, tmp_path, pdfs):
    window = _window(qtbot, tmp_path)
    window.show_tab("yukle")
    parts = window.yukle.status_parts
    assert parts["text"].isVisibleTo(window) and "Ctrl+N" in parts["text"].accessibleName()
    screen = _open(window, pdfs)
    qtbot.waitUntil(lambda: not window.counts.isVisible(), timeout=2000)  # this tab's line wins
    assert parts["parti"].accessibleName() == "3 parti"
    assert parts["sayfa"].accessibleName() == "7 sayfa"
    assert parts["belge"].isVisibleTo(window) and not parts["text"].isVisibleTo(window)
    screen._reading = _Reading(pdfs[:1], [3])
    screen._reading.done = 2
    screen._show_state()
    assert parts["busy"].accessibleName() == "Okunuyor: 2 / 3"
    assert not parts["belge"].isVisibleTo(window)
    screen._reading = None
    screen._show_state()
    window.show_tab("disa_aktar")  # the window's own counts show only where A draws them
    qtbot.waitUntil(lambda: window.counts.isVisibleTo(window), timeout=2000)
    window.show_tab("yukle")
    qtbot.waitUntil(lambda: not window.counts.isVisibleTo(window), timeout=2000)


# -- inspector --------------------------------------------------------------------------
def test_inspector_shows_the_preflight_counts_and_the_profile(qtbot, tmp_path, pdfs):
    screen = YukleScreen(JobStore(tmp_path / "s"))
    qtbot.addWidget(screen)
    screen.open_job(screen.store.load(screen.store.create_job("İş", pdfs).id))
    side = screen.side
    assert side.title.text() == "7 sayfa" and side.sub.text() == "3 parti, 2 belge bulundu"
    assert side.reason.text().startswith("1 parti QR ayıraçlı; 2. ve 3. partilerde ayıraç yok")
    assert side.qr_row.value.text() == "1" and side.docs_row.value.text() == "2"
    assert side.state_row.value.text() == "Hazır"
    assert side.profile.title.text() == "100 dpi, gri tonlamalı"
    assert side.go_button.isEnabled() and side.close_button.isEnabled()
    assert screen.summary is side.title and screen.batches is screen.table


def test_inspector_while_reading_disables_the_primary_and_says_when_it_opens(qtbot, tmp_path,
                                                                            pdfs):
    screen = YukleScreen(JobStore(tmp_path / "s"))
    qtbot.addWidget(screen)
    screen.show()
    screen.open_job(screen.store.load(screen.store.create_job("İş", pdfs[:2]).id))
    screen._reading = _Reading(pdfs[2:], [2])
    screen._show_batches()
    side = screen.side
    assert side.sub.text() == "3 parti, okuma sürüyor"
    assert side.reason.text() == "3. parti bitince belge sayısı ve uyarılar burada görünür."
    assert side.docs_row.value.text() == "…" and side.state_row.value.text() == "Okunuyor"
    assert side.qr_row.extra.text() == "şimdilik"
    assert not side.go_button.isEnabled() and side.close_button.isHidden()
    assert not side.note_box.isHidden()
    screen._reading = None
    screen._show_batches()
    assert side.go_button.isEnabled() and not side.close_button.isHidden()


def test_inspector_marks_documents_that_need_a_check_with_the_word_kontrol(qtbot, tmp_path,
                                                                          pdfs):
    screen = YukleScreen(JobStore(tmp_path / "s"))
    qtbot.addWidget(screen)
    job = screen.store.create_job("İş", pdfs[:1])
    screen.open_job(job)
    info = screen._summary()
    from evrakci.ui.yukle_info import JobSummary

    flagged = JobSummary(info.name, info.pages, info.qr, info.documents, 7, info.batches,
                         info.reason)
    screen.side.show_job(flagged, None)
    assert screen.side.state_row.value.text() == "7 belge"
    assert screen.side.state_row.accessibleName() == "Durum: 7 belge"
    assert screen.side.profile.title.text() == "Tarama bilgisi yok"  # never invented


# -- reading progress ------------------------------------------------------------------------
def test_progress_card_reports_percent_time_left_and_speed(qtbot, tmp_path):
    from evrakci.ui.yukle_parts import ProgressCard

    card = ProgressCard()
    qtbot.addWidget(card)
    card.show_progress(77, 124, "tarama-4.pdf", 40, 3.2)
    assert card.title.text() == "Sayfalar okunuyor: 77 / 124"
    assert (card.percent.text(), card.eta.text(), card.rate.text()) == (
        "%62", "Yaklaşık 40 sn kaldı", "3,2 sayfa/sn")
    assert card.note.text() == "İptal ederseniz hiçbir şey değişmez."
    assert (card.bar.value(), card.bar.maximum()) == (77, 124)
    card.show_waiting("Dosyalar inceleniyor: 2", "a.pdf")
    assert card.bar.maximum() == 0  # indeterminate before the first page
    assert card.accessibleName() == "Okuma ilerlemesi"


def test_reading_tracks_the_current_file_and_the_time_left():
    reading = _Reading([Path("a"), Path("b"), Path("c")], [10, 20, 5])
    assert reading.total == 35 and reading.current() == 0
    reading.done = 12
    assert reading.current() == 1
    assert reading.rows() == [("a", 10, "okunuyor"), ("b", 20, "okunuyor"), ("c", 5, "sirada")]
    reading.started = time.monotonic() - 10
    assert reading.rate() == pytest.approx(1.2, rel=0.1)
    assert reading.eta() == pytest.approx(23 / 1.2, rel=0.1)
    reading.done = 0
    assert reading.rate() is None and reading.eta() is None


def test_reading_a_batch_shows_progress_then_attaches_it_as_one_edit(qtbot, tmp_path, pdfs):
    window = _window(qtbot, tmp_path)
    screen = _open(window, pdfs[:1])
    shown = []
    screen.progress.setVisible = lambda v, f=screen.progress.setVisible: (shown.append(v), f(v))[1]
    with qtbot.waitSignal(screen.task_finished, timeout=20000):
        screen.add_batches(pdfs[1:])
    assert True in shown and not screen.progress.isVisible()
    assert _names(screen) == ["tarama-1.pdf", "tarama-2.pdf", "tarama-10.pdf"]
    assert window.toaster.current_text() == "2 parti eklendi."
    assert screen.controller.undo_stack.undoText() == "2 parti ekle"
    screen.controller.undo()
    assert _names(screen) == ["tarama-1.pdf"]  # one Geri al takes both away
    assert window.taskbar.state == "none"


def test_cancelling_a_batch_read_changes_nothing_and_keeps_no_copies(qtbot, tmp_path, pdfs,
                                                                    monkeypatch):
    window = _window(qtbot, tmp_path)
    screen = _open(window, pdfs[:1])
    gate = threading.Event()
    real = window.store.prepare_batch

    def held(job, path, progress=None):
        result = real(job, path, progress)
        gate.wait(5)
        return result

    monkeypatch.setattr(window.store, "prepare_batch", held)
    job = screen.controller.job
    with qtbot.waitSignal(screen.task_finished, timeout=20000):
        screen.add_batches(pdfs[1:2])
        qtbot.waitUntil(lambda: screen.busy(), timeout=2000)
        assert screen.model.items[-2].kind == "pending"  # the file shows as being read
        screen.cancel()
        assert screen.progress.title.text() == "İptal ediliyor…"
        gate.set()
    assert [b.id for b in job.batches] == ["b1"]
    assert not window.store.batch_file(job, type("B", (), {"id": "b2"})()).exists()
    assert not screen.controller.undo_stack.canUndo()
    assert screen.last_message == "İptal edildi; hiçbir şey değişmedi."
    assert _names(screen) == ["tarama-1.pdf"]


def test_a_failed_read_leaves_an_info_bar_with_the_way_forward(qtbot, tmp_path, pdfs):
    window = _window(qtbot, tmp_path)
    screen = _open(window, pdfs[:1])
    broken = tmp_path / "bozuk.pdf"
    broken.write_bytes(b"bu bir pdf degil")
    screen.add_batches([broken])  # pages are counted in the worker, never on the GUI thread
    qtbot.waitUntil(lambda: not screen.busy())
    bar = screen._error
    assert bar is not None and bar.property("severity") == "error"
    assert "Dosyayı kontrol edip yeniden ekleyin." in screen.last_message
    assert bar.action_button.text() == "Dosya ekle…"
    assert _names(screen) == ["tarama-1.pdf"]


def test_files_dropped_while_reading_wait_their_turn(qtbot, tmp_path, pdfs, monkeypatch):
    window = _window(qtbot, tmp_path)
    screen = _open(window, pdfs[:1])
    gate = threading.Event()
    real = window.store.prepare_batch

    def held(job, path, progress=None):
        gate.wait(5)
        return real(job, path, progress)

    monkeypatch.setattr(window.store, "prepare_batch", held)
    with qtbot.waitSignal(screen.task_finished, timeout=20000):
        screen.add_paths([pdfs[1]])
        screen.add_paths([pdfs[2]])  # while the first is read
        assert "sıraya alındı" in screen.last_message
        gate.set()
    qtbot.waitUntil(lambda: _names(screen) == ["tarama-1.pdf", "tarama-2.pdf", "tarama-10.pdf"],
                    timeout=20000)


# -- the window-wide drop ----------------------------------------------------------------
def test_dragging_pdfs_over_the_window_shows_what_a_drop_does(qtbot, tmp_path, pdfs):
    window = _window(qtbot, tmp_path)
    screen = _open(window, pdfs[:1], "Kasım 2026 kapasite raporları")
    overlay = screen.overlay
    assert overlay.parentWidget() is window.layer and not overlay.isVisible()
    drag = _Drag(pdfs[1:])
    assert screen.drag_over(drag) and drag.accepted
    assert overlay.isVisible()
    assert overlay.summary.text() == (
        "2 parti, <b>Kasım 2026 kapasite raporları</b> işinin sonuna eklenir.")
    assert overlay.note.text().endswith("Vazgeçmek için Esc.")
    assert overlay.geometry().top() >= window.command_bars.height()  # below the command bar
    screen.drag_left()
    assert not overlay.isVisible()
    assert not screen.drag_over(type("E", (), {"mimeData": lambda s: QMimeData()})())


def test_the_drop_overlay_without_a_job_says_it_will_make_one(qtbot, tmp_path, pdfs):
    screen = YukleScreen(JobStore(tmp_path / "s"))
    qtbot.addWidget(screen)
    screen.resize(900, 600)
    screen.drag_over(_Drag(pdfs))
    assert screen.overlay.summary.text() == "3 partiyle yeni bir iş oluşturulur."
    screen.drag_over(_Drag([pdfs[0].parent / "yok.txt"]))
    assert screen.overlay.summary.text().startswith("Burada PDF yok")


def test_dropping_on_any_tab_makes_a_job_in_yukle(qtbot, tmp_path, pdfs):
    window = _window(qtbot, tmp_path)
    window.show_tab("degerler")  # not on Yükle
    screen = window.yukle
    drop = _Drag([pdfs[0].parent])  # a folder: its PDFs are found
    with qtbot.waitSignal(screen.job_opened, timeout=20000):
        assert screen.dropped(drop)
    assert window.current_tab() == "yukle"
    assert _names(screen) == ["tarama-1.pdf", "tarama-2.pdf", "tarama-10.pdf"]
    assert screen.controller.job.name == "in"  # the folder's name
    assert window.acceptDrops()


def test_dropping_files_with_no_pdf_says_so(qtbot, tmp_path, pdfs):
    window = _window(qtbot, tmp_path)
    (tmp_path / "x.txt").write_text("x", encoding="utf-8")
    window.yukle.add_paths([tmp_path / "x.txt"])
    assert "PDF bulunamadı" in window.toaster.current_text()
    assert window.yukle.controller is None


# -- the empty page -----------------------------------------------------------------------
def test_empty_state_names_what_belongs_here_and_how_to_start(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    page = window.yukle.empty
    assert window.yukle.stack.currentWidget() is page
    assert page.title.text() == "Henüz iş yok"
    assert page.text.text() == "Taradığınız PDF'leri bırakın ya da yeni bir iş oluşturun."
    assert page.new_button.accessibleName().startswith("Yeni iş oluştur (")
    assert page.add_button.accessibleName() == "Dosya ekle"
    assert page.search.accessibleName() == "İş adı ara"
    assert page.search.placeholderText() == "İş adı ara"
    assert not page.recent_box.isVisibleTo(page)  # no jobs yet: no empty list


def test_empty_state_lists_recent_jobs_newest_first_and_opens_one(qtbot, tmp_path, pdfs):
    store = JobStore(tmp_path / "s")
    older = store.create_job("Eski iş", pdfs[:1])
    time.sleep(0.02)
    newer = store.create_job("Yeni iş", pdfs[1:2])
    screen = YukleScreen(store)
    qtbot.addWidget(screen)
    screen.show()
    assert [e.name for e in screen.empty.entries] == ["Yeni iş", "Eski iş"]
    assert screen.empty.entries[0].detail == "2 sayfa, az önce"
    rows = screen.empty._rows()
    assert rows[0].accessibleName() == "Yeni iş işini aç, 2 sayfa, az önce"
    with qtbot.waitSignal(screen.job_opened, timeout=5000):
        rows[1].click()
    assert screen.controller.job.id == older.id and newer.id != older.id
    assert screen.stack.currentWidget() is screen.splitter


def test_job_search_filters_and_a_miss_offers_to_clear(qtbot):
    page = EmptyPage()
    qtbot.addWidget(page)
    page.show()
    page.set_jobs([JobEntry(str(i), name, 10, "dün") for i, name in enumerate(
        ["Kasım kapasite", "Ekim faaliyet", "Eylül kapasite", "Ağustos", "Temmuz"])])
    assert len(page._rows()) == 3  # Son işler: the three newest
    page.search.setText("kapasite")
    assert [r.entry.name for r in page._rows()] == ["Kasım kapasite", "Eylül kapasite"]
    page.search.setText("yok böyle")
    assert page._rows() == [] and page.none.isVisibleTo(page)
    assert "“yok böyle” ile eşleşen iş yok" in page.none_text.text()
    page.clear_button.click()
    assert page.search.text() == "" and len(page._rows()) == 3
    page.set_mode("all")
    assert page.title.text() == "Tüm işler" and len(page._rows()) == 5


def test_job_list_over_an_open_job_and_back_with_escape(qtbot, tmp_path, pdfs):
    from PySide6.QtTest import QTest

    window = _window(qtbot, tmp_path)
    screen = _open(window, pdfs)
    screen.show_job_list()
    assert screen.stack.currentWidget() is screen.empty and screen.empty.title.text() == "Tüm işler"
    QTest.keyClick(screen, Qt.Key.Key_Escape)
    assert screen.stack.currentWidget() is screen.splitter


def test_closing_the_job_returns_to_the_empty_page(qtbot, tmp_path, pdfs):
    window = _window(qtbot, tmp_path)
    screen = _open(window, pdfs)
    window.close_job()
    assert screen.controller is None and screen.stack.currentWidget() is screen.empty
    assert screen.model.rowCount() == 0
    assert [e.name for e in screen.empty.entries] == ["Kasım"]
    assert not window.registry.is_enabled("yukle.cikar")
    assert not window.command_bar("yukle").button_for("app.sekme.kontrol").isEnabled()


# -- persistence ---------------------------------------------------------------------------
def test_columns_and_the_inspector_split_are_remembered(qtbot, tmp_path, pdfs):
    window = _window(qtbot, tmp_path)
    window.resize(1366, 768)
    screen = _open(window, pdfs)  # the splitter shows with the first job
    qtbot.wait(100)
    assert screen.splitter.objectName() == "yukle"
    assert screen.splitter.sizes()[1] == theme.manager().size("inspector-w")
    header = screen.table.horizontalHeader()
    header.resizeSection(QR, 150)
    qtbot.wait(450)  # the columns are saved 300 ms after the last change
    sizes = screen.splitter.sizes()
    screen.splitter.setSizes([sizes[0] - 40, sizes[1] + 40])
    screen.splitter.splitterMoved.emit(0, 0)
    window.prefs.sync() if hasattr(window.prefs, "sync") else None
    second = MainWindow(window.store, window.template_store, settings_path=tmp_path / "ayar.json",
                        prefs=Prefs(tmp_path / "p.ini"))
    qtbot.addWidget(second)
    second.resize(1366, 768)
    second.show()
    qtbot.waitUntil(lambda: second.yukle.window_ is second, timeout=3000)
    qtbot.wait(100)
    assert second.yukle.table.columnWidth(QR) == 150
    assert second.yukle.splitter.sizes()[1] == pytest.approx(sizes[1] + 40, abs=6)


def test_file_dialogs_start_where_the_last_pdfs_came_from(qtbot, tmp_path, pdfs, monkeypatch):
    from PySide6.QtWidgets import QFileDialog

    window = _window(qtbot, tmp_path)
    screen = _open(window, pdfs[:1])
    seen = []

    def chosen(parent, title, start, filt):
        seen.append(start)
        return [str(pdfs[1])], ""

    monkeypatch.setattr(QFileDialog, "getOpenFileNames", staticmethod(chosen))
    with qtbot.waitSignal(screen.task_finished, timeout=20000):
        screen.choose_batch()
    with qtbot.waitSignal(screen.task_finished, timeout=20000):
        screen.choose_batch()
    assert seen[1] == str(pdfs[1].parent) and seen[0] != str(pdfs[1].parent)
    assert window.prefs.recent_folders()[0] == str(pdfs[1].parent)


# -- accessible names and keys -------------------------------------------------------------
def test_every_control_has_an_accessible_name(qtbot, tmp_path, pdfs):
    window = _window(qtbot, tmp_path)
    screen = _open(window, pdfs)
    named = [screen.table, screen.card, screen.side, screen.side.more, screen.side.go_button,
             screen.side.close_button, screen.side.profile.link, screen.progress, screen.overlay,
             screen.dropline, screen.empty, screen.empty.search, screen.empty.new_button,
             screen.empty.add_button]
    for widget in named:
        assert widget.accessibleName(), type(widget).__name__
    assert screen.table.accessibleName() == "Partiler"
    assert screen.side.accessibleName() == "İş ayrıntısı"
    assert "Kontrol'e geç" in screen.side.go_button.text()
    for part in (screen.status_parts["parti"], screen.status_parts["sayfa"]):
        assert part.accessibleName()
    assert QAccessible.isActive() or True


def test_tab_order_reaches_the_table_then_the_inspector(qtbot, tmp_path, pdfs):
    window = _window(qtbot, tmp_path)
    screen = _open(window, pdfs)
    for widget in (screen.table, screen.side.more, screen.side.profile.link,
                   screen.side.go_button, screen.side.close_button):
        assert widget.focusPolicy() & Qt.FocusPolicy.TabFocus, type(widget).__name__


def test_no_per_screen_shortcuts_remain(qtbot, tmp_path):
    from PySide6.QtGui import QShortcut

    screen = YukleScreen(JobStore(tmp_path / "s"))
    qtbot.addWidget(screen)
    # Ctrl+N/O, Alt+arrows, Del and Ctrl+. are registry actions of the window
    assert screen.findChildren(QShortcut) == []


def test_escape_does_not_cancel_a_read(qtbot, tmp_path, pdfs):
    from PySide6.QtTest import QTest

    screen = YukleScreen(JobStore(tmp_path / "s"))
    qtbot.addWidget(screen)
    screen.show()
    screen._reading = _Reading(pdfs[:1], [3])
    screen.task = object()
    QTest.keyClick(screen, Qt.Key.Key_Escape)
    assert not screen._reading.cancelling  # Ctrl+. cancels; a stray Esc loses nothing
    screen.task = None


def test_screen_is_usable_at_large_text_without_clipping_the_file_column(qtbot, tmp_path, pdfs,
                                                                         look):
    look.set_text_scale(150)
    window = _window(qtbot, tmp_path)
    window.resize(1366, 768)
    screen = _open(window, pdfs)
    QApplication.processEvents()
    header = screen.table.horizontalHeader()
    assert header.sectionSize(FILE) > 200  # A's colgroup stays in px, Dosya takes the rest
    assert header.sectionSize(GRIP) == 44
    assert screen.side.qr_row.key.width() >= screen.side.qr_row.key.fontMetrics().horizontalAdvance(
        "QR ayıraç")


def test_thousand_pages_open_quickly(qtbot, tmp_path):
    """The table paints in a delegate: a job of 1,000 pages is a handful of rows, not widgets."""
    from evrakci.pipeline.analyze import PageInfo
    from evrakci.pipeline.job import Batch, Job

    job = Job(id="big", name="Büyük")
    for n in range(1, 6):
        job.batches.append(Batch(f"b{n}", f"tarama-{n}.pdf", 200))
        for i in range(200):
            job.pages[f"b{n}/{i}"] = PageInfo(0.1, i % 20 == 0)
    store = JobStore(tmp_path / "s")
    store.save(job)
    screen = YukleScreen(store)
    qtbot.addWidget(screen)
    started = time.monotonic()
    screen.open_job(job)
    assert time.monotonic() - started < 2.0
    assert screen.model.rowCount() == 6 and screen.side.title.text() == "1000 sayfa"
    assert len(screen.table.findChildren(type(screen.side.go_button))) == 0
    assert BatchModel.text(screen.model.items[0], QR) == "10"


def test_real_drag_events_on_the_window_reach_the_overlay_and_make_a_job(qtbot, tmp_path, pdfs):
    from PySide6.QtCore import QPoint
    from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent

    window = _window(qtbot, tmp_path)
    window.show_tab("sablonlar")  # not Yükle: the drop works on every tab
    screen = window.yukle
    data = QMimeData()
    data.setUrls([QUrl.fromLocalFile(str(p)) for p in pdfs[:2]])
    point, copy = QPoint(200, 200), Qt.DropAction.CopyAction
    enter = QDragEnterEvent(point, copy, data, Qt.MouseButton.LeftButton,
                            Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(window, enter)
    assert enter.isAccepted() and screen.overlay.isVisible()
    assert screen.overlay.summary.text() == "2 partiyle yeni bir iş oluşturulur."
    QApplication.sendEvent(window, QDragLeaveEvent())
    assert not screen.overlay.isVisible()
    drop = QDropEvent(point, copy, data, Qt.MouseButton.LeftButton,
                      Qt.KeyboardModifier.NoModifier)
    from evrakci.ui.yukle import _WindowDrops

    filt = screen.findChildren(_WindowDrops)[0]  # Qt only delivers a Drop during a real drag
    with qtbot.waitSignal(screen.job_opened, timeout=20000):
        assert filt.eventFilter(window, drop)
    assert drop.isAccepted() and window.current_tab() == "yukle"
    assert _names(screen) == ["tarama-1.pdf", "tarama-2.pdf"]


def test_files_queued_behind_a_cancelled_read_are_reported_not_dropped(qtbot, tmp_path, pdfs,
                                                                      monkeypatch):
    window = _window(qtbot, tmp_path)
    screen = _open(window, pdfs[:1])
    gate = threading.Event()
    real = window.store.prepare_batch

    def held(job, path, progress=None):
        gate.wait(5)
        return real(job, path, progress)

    monkeypatch.setattr(window.store, "prepare_batch", held)
    with qtbot.waitSignal(screen.task_finished, timeout=20000):
        screen.add_paths([pdfs[1]])
        screen.add_paths([pdfs[2]])  # queued behind the first
        screen.cancel()
        gate.set()
    assert screen.last_message.startswith("Sıradaki 1 dosya eklenmedi")
    assert window.toaster.current_text() or window.toaster.pending()
    monkeypatch.setattr(window.store, "prepare_batch", real)
    with qtbot.waitSignal(screen.task_finished, timeout=20000):
        screen.add_paths([pdfs[2]])  # what "Yine de ekle" does
    assert _names(screen) == ["tarama-1.pdf", "tarama-10.pdf"]


def test_a_folder_over_the_limit_says_how_many_were_left_out(qtbot, tmp_path, pdfs, monkeypatch):
    from evrakci.ui import yukle

    window = _window(qtbot, tmp_path)
    screen = _open(window, pdfs[:1])
    from evrakci.ui.yukle_parts import find_pdfs

    told = []
    real_tell = screen._tell
    monkeypatch.setattr(screen, "_tell", lambda text, *a, **k: (told.append(text),
                                                                  real_tell(text, *a, **k)))
    monkeypatch.setattr(yukle, "find_pdfs", lambda paths: (list(pdfs[1:2]), 6200))
    with qtbot.waitSignal(screen.task_finished, timeout=20000):
        screen.add_paths([tmp_path])
    assert any("1 dosya alındı, 6.199 dosya alınmadı" in t for t in told)
    found, total = find_pdfs([pdfs[0].parent], limit=1)
    assert len(found) == 1 and total >= 2
