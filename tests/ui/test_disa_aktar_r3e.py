"""Dışa Aktar proposals E-3..E-10 (Q-15, first half)."""
from __future__ import annotations

import shutil

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QCheckBox
from test_disa_aktar import _screen, _window

from evrakci.ui import disa_aktar as module
from evrakci.ui.disa_aktar_model import folder_state
from evrakci.ui.disa_aktar_table import FilesModel


def _double_click(viewport, point):
    """QTest.mouseDClick sends no double-click event offscreen; send the four real ones."""
    from PySide6.QtCore import QEvent, QPointF
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtWidgets import QApplication

    pos = QPointF(point)
    for kind in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease,
                 QEvent.Type.MouseButtonDblClick, QEvent.Type.MouseButtonRelease):
        QApplication.sendEvent(viewport, QMouseEvent(
            kind, pos, viewport.mapToGlobal(pos), Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier))


def _export(qtbot, screen, tmp_path, layer=False):
    screen.folder.setText(str(tmp_path / "out"))
    screen.layer.setChecked(layer)
    with qtbot.waitSignal(screen.finished, timeout=60000):
        screen.export_button.click()


def test_e3_a_failed_write_shows_turkish_text_only(qtbot, tmp_path, monkeypatch):
    import errno

    from evrakci.pipeline import exporting

    def broken(*_a, **_k):
        raise PermissionError(errno.EACCES, "Permission denied")

    monkeypatch.setattr(exporting, "write_documents", broken)
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    _export(qtbot, screen, tmp_path)
    assert "Klasöre yazma izni yok." in screen.message.text()
    assert "Permission" not in screen.message.text()


def test_e3_the_folder_hint_for_an_unreadable_folder_is_turkish(tmp_path, monkeypatch):
    import errno
    from pathlib import Path

    def broken(self):
        raise PermissionError(errno.EACCES, "Permission denied")

    monkeypatch.setattr(Path, "iterdir", broken)
    (tmp_path / "k").mkdir()
    state = folder_state(str(tmp_path / "k"))
    assert state.kind == "error"
    assert "Klasöre yazma izni yok." in state.text and "Permission" not in state.text


def test_e4_a_deleted_folder_hides_its_buttons_and_says_so(qtbot, tmp_path):
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    screen.show()
    _export(qtbot, screen, tmp_path)
    assert screen.outcome.index_button.isVisibleTo(screen)
    (tmp_path / "out" / "index.xlsx").unlink()
    screen.open_index()
    assert not screen.outcome.index_button.isVisibleTo(screen)
    assert screen.outcome.folder_button.isVisibleTo(screen)
    shutil.rmtree(tmp_path / "out")
    screen._open_out(screen.out_dir)
    assert not screen.outcome.folder_button.isVisibleTo(screen)
    assert not screen.outcome.reveal_button.isVisibleTo(screen)


def test_e4_the_status_line_names_what_is_missing(qtbot, tmp_path):
    window, screen = _window(qtbot, tmp_path)
    _export(qtbot, screen, tmp_path)
    (tmp_path / "out" / "index.xlsx").unlink()
    screen.open_index()
    assert window.message.text() == "index.xlsx bulunamadı."
    shutil.rmtree(tmp_path / "out")
    screen._open_out(screen.out_dir)
    assert window.message.text() == "Klasör bulunamadı."


def test_e5_a_stopped_export_says_the_text_layer_is_unfinished(qtbot, tmp_path, monkeypatch):
    real = module.export_job

    def stopping(*args, progress=None, **kwargs):
        def report(stage, done, total):
            progress(stage, done, total)
            if done >= 1:
                screen.cancel()

        return real(*args, progress=report, **kwargs)

    monkeypatch.setattr(module, "export_job", stopping)
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    _export(qtbot, screen, tmp_path, layer=True)
    assert "Metin katmanı tamamlanmadı." in screen.message.text()
    assert "index.xlsx yazılmadı" in screen.message.text()


def test_e5_the_progress_card_has_a_durdur_button(qtbot, tmp_path, monkeypatch):
    real = module.export_job
    seen = {}

    def holding(*args, progress=None, **kwargs):
        def report(stage, done, total):
            progress(stage, done, total)
            if done >= 1 and "stop" not in seen:
                seen["stop"] = True
                screen.run_banner.stop_button.click()

        return real(*args, progress=report, **kwargs)

    monkeypatch.setattr(module, "export_job", holding)
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    assert screen.run_banner.stop_button.text() == "Durdur"
    assert screen.run_banner.stop_button.property("action_id") == "disa_aktar.durdur"
    _export(qtbot, screen, tmp_path)
    assert screen.outcome.title.text() == "Dışa aktarma durduruldu"


def test_e6_both_stages_are_one_bar(qtbot, tmp_path):
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    screen._with_layer = True
    screen._stage = "write"
    screen._progress(2, 4)
    bar = screen.run_banner.bar
    assert (bar.minimum(), bar.maximum(), bar.value()) == (0, 8, 2)
    assert screen.run_banner.stage.text().startswith("Adım 1 / 2")
    screen._stage = "layer"
    screen._progress(1, 4)
    assert (bar.maximum(), bar.value()) == (8, 5)  # it never goes back to the start
    assert screen.run_banner.stage.text().startswith("Adım 2 / 2")
    assert "%62" in screen.run_banner.sub.text()
    screen._with_layer = False
    screen._stage = "write"
    screen._progress(1, 4)
    assert (bar.maximum(), bar.value()) == (4, 1)
    assert "Adım" not in screen.run_banner.stage.text()


def test_e6_other_tabs_show_that_an_export_runs(qtbot, tmp_path):
    window, screen = _window(qtbot, tmp_path)
    assert not window.export_status.isVisibleTo(window)
    window.set_export_running(True)
    assert not window.export_status.isVisibleTo(window)  # this tab has its own line
    window.show_tab("kontrol")
    assert window.export_status.isVisibleTo(window)
    assert window.export_status.text() == "Dışa aktarılıyor"
    window.set_export_running(False)
    assert not window.export_status.isVisibleTo(window)
    screen._sync()


def test_e7_unticking_the_characters_box_says_why(qtbot, tmp_path):
    window, screen = _window(qtbot, tmp_path)
    box = screen.side.chars_box
    box.setChecked(False)
    assert box.isChecked()
    assert window.message.text().startswith("Windows'un kabul etmediği karakterler")


def test_e7_a_pattern_edited_after_a_run_says_when_it_applies(qtbot, tmp_path):
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    _export(qtbot, screen, tmp_path)
    assert screen.state() == "done"
    screen.pattern.setText("{Firma}")
    screen._pattern_committed("{Firma}")
    assert screen.side.pattern_hint.text.text() == "Desen sonraki dışa aktarmada geçerli."
    screen.again()
    assert screen.side.pattern_hint.text.text() != "Desen sonraki dışa aktarmada geçerli."


def test_e7_unknown_variable_is_worded_one_way(qtbot, tmp_path):
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    screen.pattern.setText("{Yok} {Yok2} {Yok3}")
    screen._pattern_committed("{Yok} {Yok2} {Yok3}")
    assert screen.side.pattern_hint.text.text() == "Bilinmeyen değişken: “Yok”. Menüden seçin."
    first = screen._findings[0]
    assert first.title == "Kalıpta bilinmeyen değişken: “Yok” ve 2 değişken daha."


def test_e8_enter_and_double_click_open_the_document_in_kontrol(qtbot, tmp_path):
    window, screen = _window(qtbot, tmp_path)
    row = screen.model.row_of(lambda r: r.number == 3)
    screen.results.setCurrentIndex(screen.model.index(row, FilesModel.NAME))
    screen.results.setFocus()
    QTest.keyClick(screen.results, Qt.Key.Key_Return)
    qtbot.waitUntil(lambda: window.current_tab() == "kontrol", timeout=5000)
    qtbot.waitUntil(lambda: window.kontrol.current_document() == 3, timeout=5000)
    window.show_tab("disa_aktar")
    index = screen.model.index(screen.model.row_of(lambda r: r.number == 1), FilesModel.NAME)
    screen.results.setCurrentIndex(index)
    rect = screen.results.visualRect(index)
    _double_click(screen.results.viewport(), rect.center())
    qtbot.waitUntil(lambda: window.current_tab() == "kontrol", timeout=5000)
    qtbot.waitUntil(lambda: window.kontrol.current_document() == 1, timeout=5000)


def test_e8_pages_come_before_the_name(qtbot, tmp_path):
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    header = screen.results.horizontalHeader()
    assert header.visualIndex(FilesModel.PAGES) < header.visualIndex(FilesModel.NAME)


def test_e8_ordinary_rows_are_a_quiet_check_with_no_word(qtbot, tmp_path):
    from evrakci.ui.disa_aktar_table import QUIET

    assert "Tamam" in QUIET and "Yazıldı" in QUIET
    assert "Kontrol" not in QUIET and "Bilgi" not in QUIET
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    ordinary = screen.model.row_of(lambda r: r.state == "tamam")
    assert "Tamam" in screen.model.index(ordinary, 0).data()  # the word stays as text for readers


def test_e9_there_is_no_disabled_index_box(qtbot, tmp_path):
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    assert not hasattr(screen.side, "index_box")
    texts = [b.text() for b in screen.side.findChildren(QCheckBox)]
    assert not any("her zaman yazılır" in t for t in texts)


def test_e9_the_done_card_says_the_index_was_written(qtbot, tmp_path):
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    _export(qtbot, screen, tmp_path)
    assert "index.xlsx yazıldı." in screen.message.text()


def test_e10_a_full_folder_names_what_is_in_it(tmp_path):
    (tmp_path / "b").mkdir()
    (tmp_path / "b" / "ornek.pdf").write_bytes(b"x")
    (tmp_path / "b" / "zeta.pdf").write_bytes(b"x")
    (tmp_path / "b" / "diger.pdf").write_bytes(b"x")
    state = folder_state(str(tmp_path / "b"))
    assert state.text == ("Klasörde 3 PDF var (diger.pdf, …). Dosyaların üzerine yazılmaz; "
                          "yeni bir alt klasör oluşturun.")
    (tmp_path / "c").mkdir()
    (tmp_path / "c" / "index.xlsx").write_bytes(b"x")
    assert folder_state(str(tmp_path / "c")).text.startswith("Klasörde index.xlsx var.")
    (tmp_path / "d").mkdir()
    (tmp_path / "d" / "tek.pdf").write_bytes(b"x")
    assert folder_state(str(tmp_path / "d")).text.startswith("Klasörde 1 PDF var (tek.pdf).")


def test_e10_the_preflight_engel_carries_the_same_sentence(qtbot, tmp_path):
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "eski.pdf").write_bytes(b"x")
    screen.folder.setText(str(tmp_path / "out"))
    row = screen.preflight.rows[0].finding
    assert row.title == "Hedef klasör boş değil."
    assert row.detail.startswith("Klasörde 1 PDF var (eski.pdf).")


# -- review round 1 ------------------------------------------------------------------------
def test_durdur_disables_itself_and_the_stopping_text_stays(qtbot, tmp_path):
    screen, _ctl, _t = _screen(qtbot, tmp_path)

    class FakeTask:
        cancelled = 0

        def cancel(self):
            self.cancelled += 1

    screen.task = task = FakeTask()
    screen._with_layer, screen._stage = True, "write"
    screen.run_banner.stop_button.click()
    assert not screen.run_banner.stop_button.isEnabled()
    stopping = screen.run_banner.sub.text()
    assert stopping.startswith("Durduruluyor; geçerli dosya bitince durur")
    screen._progress(2, 3)  # a report queued behind the click
    assert screen.run_banner.sub.text() == stopping
    screen.cancel()
    assert task.cancelled == 1  # a second press does nothing
    screen.task = None


def test_a_stop_in_the_layer_stage_names_the_files_with_a_layer(qtbot, tmp_path, monkeypatch):
    real = module.export_job

    def stopping(*args, progress=None, **kwargs):
        def report(stage, done, total):
            progress(stage, done, total)
            if stage == "layer" and done >= 1:
                screen.cancel()

        return real(*args, progress=report, **kwargs)

    monkeypatch.setattr(module, "export_job", stopping)
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    _export(qtbot, screen, tmp_path, layer=True)
    first = screen._items[0].relative
    assert f"Metin katmanı eklenenler: {first}." in screen.message.text()


def test_the_disk_is_checked_once_when_the_card_appears(qtbot, tmp_path, monkeypatch):
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    _export(qtbot, screen, tmp_path)
    calls = []
    real = screen._drop_gone_buttons
    monkeypatch.setattr(screen, "_drop_gone_buttons", lambda: calls.append(1) or real())
    for _ in range(5):
        screen._shown_findings = None
        screen._sync()
    assert calls == []  # a refresh never touches the disk for the buttons


def test_a_missing_document_number_is_said_not_silent(qtbot, tmp_path):
    window, screen = _window(qtbot, tmp_path)
    screen.open_in_kontrol(99)
    assert window.message.text() == "Belge 99 artık yok."
    assert window.current_tab() == "disa_aktar"


def test_a_full_folder_with_an_index_says_so(tmp_path):
    (tmp_path / "b").mkdir()
    (tmp_path / "b" / "a.pdf").write_bytes(b"x")
    (tmp_path / "b" / "index.xlsx").write_bytes(b"x")
    assert folder_state(str(tmp_path / "b")).text.startswith(
        "Klasörde 1 PDF ve index.xlsx var (a.pdf).")
