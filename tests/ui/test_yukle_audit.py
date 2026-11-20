"""Yükle audit fixes (Phase 4, Görev B): F-yukle-42 undo of a batch removal, and the rest."""
from __future__ import annotations

import os

import pytest
from fakes import empty_page, make_pdf, qr_page, text_page
from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFileDialog, QLabel

from evrakci.pipeline.job import job_to_dict
from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.pipeline.templates.values import VariableValue
from evrakci.ui.main_window import MainWindow
from evrakci.ui.prefs import Prefs
from evrakci.ui.yukle import YukleScreen
from evrakci.ui.yukle_parts import DropOverlay, EmptyPage, JobEntry
from evrakci.ui.yukle_table import FILE, GRIP, PAGES, STATUS


@pytest.fixture
def look():
    from evrakci.ui import theme

    m = theme.manager()
    mode, scale = m.mode(), m.text_scale()
    yield m
    m.set_text_scale(scale)
    m.set_mode(mode)


@pytest.fixture
def pdfs(tmp_path):
    (tmp_path / "in").mkdir()
    a = make_pdf(tmp_path / "in" / "tarama-1.pdf", [text_page("A"), qr_page(), text_page("B")])
    b = make_pdf(tmp_path / "in" / "tarama-2.pdf", [text_page("C"), text_page("D"), empty_page()])
    return [a, b]


def _screen(qtbot, tmp_path, pdfs) -> YukleScreen:
    screen = YukleScreen(JobStore(tmp_path / "s"))
    qtbot.addWidget(screen)
    screen.open_job(screen.store.load(screen.store.create_job("İş", pdfs).id))
    return screen


def test_undo_of_removing_an_edited_batch_restores_job_data_and_the_batch_file(
    qtbot, tmp_path, pdfs
):
    """F-yukle-42: cuts, deletes, templates, filters, rotations and read values come back."""
    screen = _screen(qtbot, tmp_path, pdfs)
    controller = screen.controller
    second = controller.job.batches[1].id
    p0, p1, p2 = (f"{second}/{i}" for i in range(3))
    assert controller.add_cut(p1)
    assert controller.delete_page(p2)
    assert controller.rotate(p0, 90)
    assert controller.apply_filter([p0, p1], 2)
    assert controller.apply_template([p0, p1], "t1")
    assert controller.run("Değer", lambda j: j.values.__setitem__(
        p0, {"Ad": VariableValue("Ali", 0.9, None, False, edited=True)}))
    before = job_to_dict(controller.job)
    batch_file = screen.store.batch_file(controller.job, controller.job.get_batch(second))
    assert batch_file.exists()

    screen.table.select_batch(second)
    screen.remove_batch()
    assert second not in [b.id for b in controller.job.batches]
    controller.undo()

    assert job_to_dict(controller.job) == before
    assert batch_file.exists()
    # and what is on disk (the automatic save) is the restored job too
    assert job_to_dict(screen.store.load(controller.job.id)) == before


@pytest.mark.parametrize("scale", [100, 150])
def test_inspector_without_scan_image_fits_its_viewport(qtbot, tmp_path, pdfs, look, scale):
    """F-yukle-01: "Dosyalarda tarama görüntüsü bulunamadı" elides instead of widening the body."""
    look.set_text_scale(scale)
    screen = _screen(qtbot, tmp_path, pdfs)
    screen.resize(1366, 700)
    screen.show()
    inspector = screen.side
    inspector.profile.set_profile(None)
    qtbot.wait(50)
    body = inspector.scroll.widget()
    assert body.width() <= inspector.scroll.viewport().width()
    detail = inspector.profile.detail
    assert detail.full_text() == "Dosyalarda tarama görüntüsü bulunamadı"
    assert detail.toolTip() == detail.full_text()
    right = detail.mapTo(inspector.scroll.viewport(), detail.rect().topRight()).x()
    assert right <= inspector.scroll.viewport().width()


@pytest.fixture
def qt_translation(qtbot):
    """The app's Qt translation, removed again so other tests see the untranslated shared app."""
    from PySide6.QtCore import QLibraryInfo
    from PySide6.QtWidgets import QApplication

    from evrakci.app import install_qt_translation

    directory = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if not os.path.isfile(os.path.join(directory, "qtbase_tr.qm")):
        pytest.skip(f"qtbase_tr.qm is not shipped in this environment ({directory})")
    app = QApplication.instance()
    install_qt_translation(app)
    yield app
    app.removeTranslator(app._evrakci_qt_translator)
    del app._evrakci_qt_translator


def test_standard_dialog_buttons_read_turkish(qt_translation):
    """F-yukle-39: Qt's own qtbase_tr button texts are loaded at startup (no text of ours)."""
    from PySide6.QtWidgets import QDialogButtonBox, QMessageBox

    standard = QDialogButtonBox.StandardButton
    box = QDialogButtonBox(standard.Ok | standard.Cancel)
    texts = {b.text().replace("&", "") for b in box.buttons()}
    assert texts == {"Tamam", "İptal"}, texts
    yes_no = QMessageBox(QMessageBox.Icon.Question, "x", "y",
                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    assert {b.text().replace("&", "") for b in yes_no.buttons()} == {"Evet", "Hayır"}


def test_qt_translation_leaves_registry_key_texts_alone(qtbot):
    """key_text / tooltip_for of every registry action are identical with and without it."""
    from PySide6.QtCore import QLibraryInfo
    from PySide6.QtWidgets import QApplication

    from evrakci.app import install_qt_translation
    from evrakci.ui import actions

    def snapshot():
        return [(spec.id, actions.tooltip_for(spec),
                 [actions.key_text(k) for k in spec.shortcuts]) for spec in actions.SPECS]

    directory = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if not os.path.isfile(os.path.join(directory, "qtbase_tr.qm")):
        pytest.skip("qtbase_tr.qm is not shipped in this environment")
    before = snapshot()
    assert any(keys for _, _, keys in before)
    app = QApplication.instance()
    install_qt_translation(app)
    try:
        assert snapshot() == before
    finally:
        app.removeTranslator(app._evrakci_qt_translator)
        del app._evrakci_qt_translator


def test_qt_translation_leaves_key_names_alone(qt_translation):
    """The translation must not reach QKeySequence texts (Ctrl, Tab, Space, PgDown ...)."""
    from PySide6.QtGui import QKeySequence

    for text in ("Ctrl+Shift+Del", "Tab", "Space", "PgDown", "Ctrl+K", "Alt+Left", "Esc"):
        assert QKeySequence(text).toString(QKeySequence.SequenceFormat.NativeText) == (
            QKeySequence(text).toString(QKeySequence.SequenceFormat.PortableText)), text
    shown = QKeySequence("Ctrl+Shift+Del").toString(QKeySequence.SequenceFormat.NativeText)
    assert shown == "Ctrl+Shift+Del"
    assert QKeySequence("Tab").toString(QKeySequence.SequenceFormat.NativeText) == "Tab"
    assert QKeySequence("Space").toString(QKeySequence.SequenceFormat.NativeText) == "Space"
    assert QKeySequence("PgDown").toString(QKeySequence.SequenceFormat.NativeText) == "PgDown"


# -- the window-based findings --------------------------------------------------------------

def _window(qtbot, tmp_path) -> MainWindow:
    window = MainWindow(JobStore(tmp_path / "jobs"), TemplateStore(tmp_path / "tpl"),
                        settings_path=tmp_path / "ayar.json", prefs=Prefs(tmp_path / "p.ini"))
    qtbot.addWidget(window)
    window.show()
    qtbot.waitUntil(lambda: window.yukle.window_ is window, timeout=3000)
    return window


def _open(window, pdfs, name="Kasım"):
    job = window.store.create_job(name, pdfs)
    window.yukle.open_job(window.store.load(job.id))
    return window.yukle


def _three(qtbot, tmp_path, pdfs):
    screen = YukleScreen(JobStore(tmp_path / "s"))
    qtbot.addWidget(screen)
    screen.open_job(screen.store.load(screen.store.create_job("İş", pdfs + pdfs[:1]).id))
    screen.resize(900, 500)
    screen.show()
    screen.table.setFocus()
    return screen


def test_keys_never_land_on_toplam_and_home_end_jump_to_the_batches(qtbot, tmp_path, pdfs):
    """F-yukle-02, F-yukle-03."""
    screen = _three(qtbot, tmp_path, pdfs)
    table = screen.table
    ids = [b.id for b in screen.controller.job.batches]
    assert len(ids) == 3
    table.select_batch(ids[0])
    for key in (Qt.Key.Key_End, Qt.Key.Key_Down, Qt.Key.Key_PageDown):
        QTest.keyClick(table, key)
        assert table.selected_batch() == ids[-1], key
    QTest.keyClick(table, Qt.Key.Key_Home)
    assert table.selected_batch() == ids[0]
    QTest.keyClick(table, Qt.Key.Key_End, Qt.KeyboardModifier.ControlModifier)
    assert table.selected_batch() == ids[-1]
    total = screen.model.index(len(screen.model.items) - 1, FILE)
    QTest.mouseClick(table.viewport(), Qt.MouseButton.LeftButton,
                     pos=table.visualRect(total).center())
    assert table.selected_batch() == ids[-1]  # a click on Toplam does not take the selection


def test_file_name_and_status_have_tooltips(qtbot, tmp_path, pdfs):
    """F-yukle-04, F-yukle-05: what the cell may cut is in the tooltip."""
    screen = _three(qtbot, tmp_path, pdfs)
    first = screen.model.index(0, FILE)
    assert screen.model.data(first, Qt.ItemDataRole.ToolTipRole) == "tarama-1.pdf"
    status = screen.model.index(0, STATUS)
    assert screen.model.data(status, Qt.ItemDataRole.ToolTipRole) in ("Hazır", "Kontrol")


def test_columns_cannot_be_dragged_below_their_title_and_the_grip_is_fixed(qtbot, tmp_path, pdfs):
    """F-yukle-13."""
    screen = _three(qtbot, tmp_path, pdfs)
    header = screen.table.horizontalHeader()
    header.resizeSection(PAGES, 40)
    assert header.sectionSize(PAGES) >= header.readable_width(PAGES) > 40
    assert header.sectionResizeMode(GRIP) == header.ResizeMode.Fixed


def test_a_double_click_on_a_command_button_acts_once_and_enter_presses_it(qtbot, tmp_path, pdfs):
    """F-yukle-14, F-yukle-15."""
    window = _window(qtbot, tmp_path)
    screen = _open(window, pdfs + pdfs[:1])
    bar = window.command_bar("yukle")
    screen.table.select_batch(screen.controller.job.batches[0].id)
    button = bar.button_for("yukle.cikar")
    assert button.isEnabled()
    centre = button.rect().center()
    QTest.mouseClick(button, Qt.MouseButton.LeftButton, pos=centre)  # the first click
    double = QMouseEvent(QEvent.Type.MouseButtonDblClick, QPointF(centre), button.mapToGlobal(
        QPointF(centre)), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(button, double)  # the second press, as the system sends it
    QTest.mouseRelease(button, Qt.MouseButton.LeftButton, pos=centre)
    assert len(screen.controller.job.batches) == 2  # one removal, not two
    # Enter on the focused button, and on the inspector buttons
    go = bar.button_for("app.sekme.kontrol")
    seen = []
    go.clicked.connect(lambda *_: seen.append("bar"))
    screen.side.go.connect(lambda: seen.append("side"))
    for widget in (go, screen.side.go_button):
        QTest.keyClick(widget, Qt.Key.Key_Return)
    assert sorted(seen) == ["bar", "side"]
    closed = []
    screen.side.close_job.connect(lambda: closed.append(1))
    QTest.keyClick(screen.side.close_button, Qt.Key.Key_Enter)
    assert closed == [1]


def test_enter_presses_a_job_row(qtbot):
    page = EmptyPage()
    qtbot.addWidget(page)
    page.show()
    page.set_jobs([JobEntry("a", "Kasım", 10, "dün")])
    with qtbot.waitSignal(page.open_job, timeout=1000):
        QTest.keyClick(page._rows()[0], Qt.Key.Key_Return)


def test_dialog_files_are_queued_while_a_read_runs(qtbot, tmp_path, pdfs, monkeypatch):
    """F-yukle-17: Dosya ekle… during a read goes through add_paths (which queues)."""
    window = _window(qtbot, tmp_path)
    screen = _open(window, pdfs[:1])
    monkeypatch.setattr(QFileDialog, "getOpenFileNames",
                        staticmethod(lambda *a, **k: ([str(pdfs[1])], "")))
    monkeypatch.setattr(screen, "busy", lambda: True)
    monkeypatch.setattr(screen, "_begin", lambda *a, **k: pytest.fail("started a second read"))
    try:
        screen.choose_batch()
        assert screen._queued == [pdfs[1]]
        assert "sıraya alındı" in screen.last_message
    finally:
        monkeypatch.undo()  # closing the window waits for a running read


def test_the_drop_overlay_wraps_a_long_unbroken_job_name(qtbot, tmp_path, pdfs, look):
    """F-yukle-06."""
    look.set_text_scale(150)
    parent = _screen(qtbot, tmp_path, pdfs)
    parent.resize(1200, 700)
    parent.show()
    overlay = DropOverlay(parent)
    overlay.show_drop(pdfs[:1], "Kasim" * 20)
    overlay.summary.setFixedWidth(500)
    assert overlay.summary.minimumSizeHint().width() <= 500
    assert "\u200b" not in overlay.accessibleDescription()  # break marks are not spoken
    assert "Kasim" * 20 in overlay.accessibleDescription()
    assert "Kasim" * 20 == overlay.summary.text().replace("​", "").split("<b>")[1].split("</b>")[0]


def test_a_long_file_name_does_not_cut_the_toast_sentence(qtbot, tmp_path, look):
    """F-yukle-08: the verb stays visible, the toast fits inside the window and starts at or
    right of its left edge, and a screen reader still hears the full name."""
    name = "tarama-2026-11-04-0912-Organizasyon-Raporu-son-hali-v7-kopya-final.pdf"
    pdf = make_pdf(tmp_path / name, [text_page("A")])
    other = make_pdf(tmp_path / "diger.pdf", [text_page("B")])
    window = _window(qtbot, tmp_path)
    look.set_text_scale(150)  # after the window: its prefs set the scale while it is built
    look.apply(QApplication.instance())  # the application font follows the scale
    window.resize(1366, 768)
    screen = _open(window, [pdf, other])
    screen.table.select_batch(screen.controller.job.batches[0].id)
    screen.remove_batch()
    qtbot.wait(300)
    toast = window.toaster._current
    assert toast is not None
    label = next(w for w in toast.findChildren(QLabel) if w.text().endswith("işten çıkarıldı."))
    assert "…" in label.text() and name not in label.text()
    assert label.heightForWidth(label.width()) <= label.height()  # every line is shown
    frame = toast.frame.geometry().translated(toast.pos())  # the shell adds shadow room
    assert frame.left() >= 0 and frame.right() <= window.width()
    assert toast.accessibleName() == f"{name} işten çıkarıldı."
    assert screen.last_message.endswith("işten çıkarıldı.")
    from evrakci.ui.yukle import _short_name

    assert _short_name("tarama-1.pdf") == "tarama-1.pdf"


def test_the_durum_word_is_elided_when_the_column_is_too_narrow(qtbot, tmp_path, pdfs, look):
    """F-yukle-05: "Okunuyor" at 150 % in the 148 px column is cut by the delegate, not the cell."""
    from evrakci.ui import theme
    from evrakci.ui.yukle_table import BatchDelegate

    look.set_text_scale(150)
    screen = _three(qtbot, tmp_path, pdfs)
    screen.model.set_pending([("a.pdf", 5, "okunuyor")])
    row = next(r for r, i in enumerate(screen.model.items) if i.kind == "pending")
    rect = screen.table.visualRect(screen.model.index(row, STATUS))
    m = theme.manager()
    room = rect.width() - 2 * m.size("s3") - m.inline_icon(16) - 6
    font = m.font("body")
    shown = BatchDelegate.status_word("Okunuyor", font, room)
    assert shown != "Okunuyor" and shown.endswith("…")  # too wide at 150 %: elided
    assert BatchDelegate.status_word("Okunuyor", font, 4000) == "Okunuyor"
    assert screen.model.data(screen.model.index(row, STATUS),
                             Qt.ItemDataRole.ToolTipRole) == "Okunuyor"  # the whole word


@pytest.mark.parametrize("scale", [100, 150])
def test_the_inspector_cannot_be_dragged_narrower_than_its_content(
    qtbot, tmp_path, pdfs, look, scale
):
    """F-yukle-12: below its natural width the cards were cut at the right with no scroll bar."""
    look.set_text_scale(scale)
    screen = _screen(qtbot, tmp_path, pdfs)
    screen.resize(1366, 700)
    screen.show()
    qtbot.wait(50)
    screen.splitter.setSizes([1366 - 100, 100])
    qtbot.wait(80)
    side = screen.side
    assert side.scroll.widget().width() <= side.scroll.viewport().width()


def test_the_inspector_minimum_follows_content_that_grows_without_a_resize(
    qtbot, tmp_path, pdfs, look
):
    """Windows (wider fonts, wide scroll bar): the content got wider than the viewport after the
    minimum was taken (316 > 307 at 150 %), and nothing resized the panel to take it again. A
    widget that makes the content wider stands in for the font difference."""
    from PySide6.QtWidgets import QLabel

    look.set_text_scale(150)
    screen = _screen(qtbot, tmp_path, pdfs)
    screen.resize(1366, 700)
    screen.show()
    qtbot.wait(50)
    side = screen.side
    screen.splitter.setSizes([1366 - 100, 100])
    qtbot.wait(80)
    wide = QLabel("x")
    wide.setMinimumWidth(side.width() + 60)
    side.scroll.widget().layout().addWidget(wide)
    qtbot.wait(150)
    assert side.minimumWidth() >= wide.minimumWidth()
    assert side.scroll.widget().width() <= side.scroll.viewport().width()


def test_no_action_slot_of_yukle_takes_the_checked_flag():
    """QAction.triggered passes `checked`: a slot with a default parameter would receive it
    (B-047, F-degerler-01 pattern). Every slot Yükle connects to a registry action has none."""
    import inspect

    from evrakci.ui.main_window import MainWindow as Window

    for method in (YukleScreen.remove_batch, YukleScreen.choose_folder, YukleScreen.rename_job,
                   YukleScreen.show_in_explorer, YukleScreen.cancel, YukleScreen.choose_batch,
                   YukleScreen.choose_new_job, Window._new_job, Window._add_files):
        extra = [p for p in inspect.signature(method).parameters.values()
                 if p.name != "self"]
        assert not extra, (method.__qualname__, extra)
