"""Phase 4 fixes: Dışa Aktar (B-055, B-008, F-disa-aktar-02/04/36), Rehber (F-rehber-*)."""
from __future__ import annotations

import dataclasses

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from test_disa_aktar import _screen, _window
from test_rehber import _window as _rehber_window

from evrakci.ui import disa_aktar as module


def _pages(screen) -> int:
    return screen._summary.pages


def test_b055_dis_aktar_plans_again_when_the_job_changes_by_undo_and_redo(qtbot, tmp_path):
    window, screen = _window(qtbot, tmp_path)
    ctl = window.controller()
    before = _pages(screen)
    assert ctl.delete_page(ctl.job.ordered_page_ids()[0])
    assert _pages(screen) == before - 1
    window.undo()
    assert _pages(screen) == before
    window.redo()
    assert _pages(screen) == before - 1


def test_b055_ctrl_z_on_rehber_does_not_undo_the_job_unseen(qtbot, tmp_path):
    window, _screen_ = _window(qtbot, tmp_path)
    ctl = window.controller()
    assert ctl.delete_page(ctl.job.ordered_page_ids()[0])
    window.show_tab("rehber")
    window.undo()
    window.redo()
    assert ctl.undo_stack.canUndo() and not ctl.undo_stack.canRedo()
    assert not window.registry.action("app.geri_al").isEnabled()
    window.show_tab("disa_aktar")
    assert window.registry.action("app.geri_al").isEnabled()


def test_unmatched_brace_in_the_pattern_is_an_engel_not_an_exception(qtbot, tmp_path):
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    screen.folder.setText(str(tmp_path / "out"))
    screen.pattern.setText("{Sicil_No")
    screen.side.pattern_committed.emit("{Sicil_No")
    assert screen.state() == "blocked"
    assert "süslü parantez" in screen.preflight.rows[0].finding.title.lower()
    assert screen.side.pattern_hint.tone() == "err"
    screen.export()  # no exception; nothing is written
    assert not (tmp_path / "out").exists()
    screen.refresh()


def test_b008_a_deleted_job_is_closed_and_not_written_back(qtbot, tmp_path):
    window, _screen_ = _window(qtbot, tmp_path)
    job_id = window.controller().job.id
    window.store.delete(job_id)
    window.disa_aktar.job_deleted.emit()
    assert window.controller() is None
    assert not window.store._job_file(job_id).exists()


def test_long_target_path_is_elided_to_the_column_and_keeps_a_tooltip(qtbot, tmp_path):
    window, screen = _window(qtbot, tmp_path)
    window.resize(1366, 768)
    from evrakci.ui import theme
    theme.manager().set_text_scale(150)
    try:
        QApplication.processEvents()
        long = str(tmp_path / ("klasor-" * 20))
        screen.out_dir = type(tmp_path)(long)
        screen._written = True
        screen._sync()
        room = screen._path_room()
        assert room <= screen.left_scroll.viewport().width() - 100
        shown = screen.files_head.label.text()
        assert "…" in shown
        assert screen.files_head.label.toolTip() == long
        assert screen.files_head.width() <= screen.left_scroll.viewport().width()
        assert QFontMetrics(theme.manager().font("caption")).horizontalAdvance(
            screen._short_path(long)) <= room
    finally:
        theme.manager().set_text_scale(100)


def test_the_folder_field_has_the_full_path_as_tooltip(qtbot, tmp_path):
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    screen.folder.setText(str(tmp_path / "a" / "b"))
    assert screen.folder.toolTip() == str(tmp_path / "a" / "b")


def test_enter_presses_the_round_buttons_of_the_tab(qtbot):
    from evrakci.ui.disa_aktar_parts import PartsButton
    button = PartsButton("Yazdır", "printer")
    qtbot.addWidget(button)
    button.show()
    hits = []
    button.clicked.connect(lambda *_: hits.append(1))
    QTest.keyClick(button, Qt.Key.Key_Return)
    assert hits == [1]


def test_f_rehber_09_the_reading_place_survives_a_text_size_change(qtbot, tmp_path):
    window = _rehber_window(qtbot, tmp_path)
    screen = window.rehber
    bar = screen.text.verticalScrollBar()
    bar.setValue(bar.maximum() // 2)
    place = bar.value() / bar.maximum()
    from evrakci.ui import theme
    theme.manager().set_text_scale(130)
    try:
        QApplication.processEvents()
        bar = screen.text.verticalScrollBar()
        assert bar.maximum() > 0
        assert abs(bar.value() / bar.maximum() - place) < 0.05
    finally:
        theme.manager().set_text_scale(100)


def test_f_rehber_18_19_search_empty_state(qtbot, tmp_path):
    window = _rehber_window(qtbot, tmp_path)
    screen = window.rehber
    screen.search.setText("zzzzqqqq")
    assert screen.stack.currentWidget() is screen.empty
    button = screen._empty_buttons[0]
    button.setFocus()
    QTest.keyClick(button, Qt.Key.Key_Escape)
    assert screen.stack.currentWidget() is screen.text
    assert screen.search.text() == ""
    # the tip is the only match: dismissing it leaves nothing to show
    screen.search.setText("gösterme")
    assert screen._hits
    screen.dismiss_note()
    assert screen.stack.currentWidget() is screen.empty


def test_b008_the_outcome_card_stays_after_the_deleted_job_closes(qtbot, tmp_path, monkeypatch):
    from fakes import make_pdf, text_page
    from test_ledger_b import _window as ledger_window

    from evrakci.pipeline.settings import DELETE_AFTER_EXPORT, Settings, save_settings
    window = ledger_window(qtbot, tmp_path)
    pdf = make_pdf(tmp_path / "t.pdf", [text_page("A"), text_page("B")])
    job = window.store.create_job("İş", [pdf])
    save_settings(Settings(DELETE_AFTER_EXPORT), tmp_path / "ayar.json")
    window.yukle.open_job(window.store.load(job.id))
    window.show_tab("disa_aktar")
    screen = window.disa_aktar
    real = module.export_job
    monkeypatch.setattr(module, "export_job", lambda *a, **k: dataclasses.replace(
        real(*a, **k), with_layer=True))
    screen.folder.setText(str(tmp_path / "out"))
    screen.layer.setChecked(False)
    with qtbot.waitSignal(screen.finished, timeout=30000):
        screen.export_button.click()
    assert window.controller() is None
    assert screen._outcome is not None and "yazıldı" in screen._outcome["title"]
    assert screen.outcome.isVisible()
    assert "İş silindi" in screen._outcome["message"]
