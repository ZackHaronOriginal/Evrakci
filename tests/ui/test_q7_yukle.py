"""Q7: the same file twice warns, a broken file keeps the good ones of a multi-add, and a close
after a failed save asks Yes/No and never hangs. Synthetic PDFs only."""
from __future__ import annotations

import pytest
from fakes import make_pdf, qr_page, text_page
from PySide6.QtWidgets import QMessageBox

from evrakci.cli.main import main
from evrakci.pipeline.job import repeated_files
from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.ui.main_window import MainWindow
from evrakci.ui.prefs import Prefs


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
    bad = tmp_path / "bozuk.pdf"
    bad.write_bytes(b"bu bir pdf degil")
    bad2 = tmp_path / "bozuk-2.pdf"
    bad2.write_bytes(b"yine degil")
    return a, b, bad, bad2


def _open(qtbot, window, paths):
    job = window.store.create_job("Kasım", paths)
    with qtbot.waitSignal(window.yukle.job_opened, timeout=10000):
        window.yukle.open_job(window.store.load(job.id))
    return window.yukle


def _batches(screen):
    return [b.file_name for b in screen.controller.job.batches]


def test_repeated_files_names_each_repeat_once():
    assert repeated_files(["a.pdf"], ["A.PDF", "b.pdf", "b.pdf", "c.pdf"]) == ["A.PDF", "b.pdf"]
    assert repeated_files([], ["a.pdf", "b.pdf"]) == []


def test_the_same_file_twice_warns_with_undo_and_keeps_the_add(qtbot, tmp_path, files):
    a, b, _bad, _bad2 = files
    window = _window(qtbot, tmp_path)
    screen = _open(qtbot, window, [a])
    screen.add_batches([a])
    qtbot.waitUntil(lambda: not screen.busy(), timeout=10000)
    assert _batches(screen) == ["tarama-1.pdf", "tarama-1.pdf"]
    assert screen.last_message == "tarama-1.pdf zaten ekli."
    screen.controller.undo_stack.undo()  # Geri al takes the add back
    assert _batches(screen) == ["tarama-1.pdf"]
    screen.add_batches([b])
    qtbot.waitUntil(lambda: not screen.busy(), timeout=10000)
    assert screen.last_message == "tarama-2.pdf eklendi."  # a new file: no warning


def test_a_repeat_inside_one_multi_add_warns_too(qtbot, tmp_path, files):
    a, b, _bad, _bad2 = files
    window = _window(qtbot, tmp_path)
    screen = _open(qtbot, window, [a])
    screen.add_batches([b, b, b])
    qtbot.waitUntil(lambda: not screen.busy(), timeout=10000)
    assert screen.last_message == "3 parti eklendi. tarama-2.pdf zaten ekli."  # the count stays
    assert len(_batches(screen)) == 4


def test_several_repeats_are_listed_by_name(qtbot, tmp_path, files):
    a, b, _bad, _bad2 = files
    window = _window(qtbot, tmp_path)
    screen = _open(qtbot, window, [a, b])
    screen.add_batches([a, b])
    qtbot.waitUntil(lambda: not screen.busy(), timeout=10000)
    assert screen.last_message == "2 parti eklendi. 2 dosya zaten ekli: tarama-1.pdf, tarama-2.pdf"


def test_a_broken_file_keeps_the_good_files_and_every_failure_is_listed(qtbot, tmp_path, files):
    a, b, bad, bad2 = files
    window = _window(qtbot, tmp_path)
    screen = _open(qtbot, window, [a])
    screen.add_batches([b, bad, bad2])
    qtbot.waitUntil(lambda: not screen.busy(), timeout=10000)
    assert _batches(screen) == ["tarama-1.pdf", "tarama-2.pdf"]
    text = screen.last_message
    assert "PDF açılamadı: bozuk.pdf" in text and "PDF açılamadı: bozuk-2.pdf" in text
    assert "Parola korumalı olabilir." in text
    assert text.startswith("1 parti eklendi.")  # not only "Okunamadı": the good file was added
    assert screen._error is not None
    assert not hasattr(screen, "_readable") and not hasattr(screen, "_failed_files")  # thread rule


def test_only_broken_files_change_nothing_and_name_each(qtbot, tmp_path, files):
    a, _b, bad, bad2 = files
    window = _window(qtbot, tmp_path)
    screen = _open(qtbot, window, [a])
    screen.add_batches([bad, bad2])
    qtbot.waitUntil(lambda: not screen.busy(), timeout=10000)
    assert _batches(screen) == ["tarama-1.pdf"]
    assert "bozuk.pdf" in screen.last_message and "bozuk-2.pdf" in screen.last_message
    assert not screen.controller.undo_stack.canUndo()


def test_a_file_that_breaks_while_reading_keeps_the_others(qtbot, tmp_path, files, monkeypatch):
    from evrakci.pipeline.analyze import BatchError

    a, b, _bad, _bad2 = files
    window = _window(qtbot, tmp_path)
    screen = _open(qtbot, window, [a])
    real = window.store.prepare_batch

    def prepare(job, path, progress=None):
        if path.name == "tarama-2.pdf":
            raise BatchError("PDF açılamadı: tarama-2.pdf")
        return real(job, path, progress)

    monkeypatch.setattr(window.store, "prepare_batch", prepare)
    c = make_pdf(tmp_path / "tarama-3.pdf", [text_page("E")])
    screen.add_batches([b, c])
    qtbot.waitUntil(lambda: not screen.busy(), timeout=10000)
    assert _batches(screen) == ["tarama-1.pdf", "tarama-3.pdf"]
    assert "PDF açılamadı: tarama-2.pdf" in screen.last_message


def test_a_new_job_from_a_repeated_file_warns_like_the_cli(qtbot, tmp_path, files):
    """R-O-7: creating a job from several files warns about a repeat, as `is olustur` does."""
    a, b, _bad, _bad2 = files
    window = _window(qtbot, tmp_path)
    with qtbot.waitSignal(window.yukle.job_opened, timeout=20000):
        window.yukle.create_job([a, b, a], "Kasım")
    assert window.yukle.last_message == "tarama-1.pdf zaten ekli."


def test_cli_warns_about_a_repeated_file_and_still_adds(tmp_path, capsys, files):
    a, _b, _bad, _bad2 = files
    root = tmp_path / "kok"
    assert main(["--kok", str(root), "is", "olustur", "Liste", str(a)]) == 0
    job_id = capsys.readouterr().out.split()[0]
    assert main(["--kok", str(root), "is", "ekle", job_id, str(a)]) == 0
    captured = capsys.readouterr()
    assert "tarama-1.pdf zaten ekli." in captured.err
    assert "b2 eklendi" in captured.out


def _failing_window(qtbot, tmp_path, monkeypatch):
    window = _window(qtbot, tmp_path)
    pdf = make_pdf(tmp_path / "t.pdf", [text_page(), qr_page(), text_page()])
    with qtbot.waitSignal(window.yukle.job_opened, timeout=20000):
        window.yukle.create_job([pdf], "Kasım")
    controller = window.controller()

    def save_dict(job_id, data):
        raise OSError("salt okunur")

    monkeypatch.setattr(controller.store, "save_dict", save_dict)
    controller._changed()
    qtbot.waitUntil(lambda: window.job_switch.save_state.state() == "failed", timeout=3000)
    return window


def _question(window):
    return window._close_question


def test_close_after_a_failed_save_asks_and_no_keeps_the_job(qtbot, tmp_path, monkeypatch):
    window = _failing_window(qtbot, tmp_path, monkeypatch)
    assert window.close() is False
    qtbot.waitUntil(lambda: getattr(window, "_close_question", None) is not None
                    and _question(window).isVisible(), timeout=3000)
    box = _question(window)
    assert box.text() == "Değişiklikler kaydedilemedi. Yine de kapatılsın mı? " \
                         "Son değişiklikler kaybolur."
    assert box.button(QMessageBox.StandardButton.Yes) is not None
    box.button(QMessageBox.StandardButton.No).click()
    qtbot.waitUntil(lambda: not box.isVisible(), timeout=3000)
    assert window.controller() is not None and not window._closed


def test_close_after_a_failed_save_asks_and_yes_closes(qtbot, tmp_path, monkeypatch):
    window = _failing_window(qtbot, tmp_path, monkeypatch)
    assert window.close() is False
    qtbot.waitUntil(lambda: getattr(window, "_close_question", None) is not None
                    and _question(window).isVisible(), timeout=3000)
    _question(window).button(QMessageBox.StandardButton.Yes).click()
    qtbot.waitUntil(lambda: window._closed, timeout=3000)  # never stuck on a failing disk


def test_a_hung_write_does_not_hold_the_close_for_ever(qtbot, tmp_path, monkeypatch):
    import threading

    from evrakci.ui import saver as saver_module

    monkeypatch.setattr(saver_module, "STALL_MS", 300)
    window = _window(qtbot, tmp_path)
    pdf = make_pdf(tmp_path / "t.pdf", [text_page(), qr_page()])
    with qtbot.waitSignal(window.yukle.job_opened, timeout=20000):
        window.yukle.create_job([pdf], "Kasım")
    controller = window.controller()
    gate = threading.Event()
    monkeypatch.setattr(controller.store, "save_dict", lambda *_a: gate.wait(20))
    controller._changed()
    assert window.close() is False
    qtbot.waitUntil(lambda: getattr(window, "_close_question", None) is not None
                    and _question(window).isVisible(), timeout=5000)
    _question(window).button(QMessageBox.StandardButton.Yes).click()
    qtbot.waitUntil(lambda: window._closed, timeout=3000)
    gate.set()


def test_no_then_another_close_never_closes_silently(qtbot, tmp_path, monkeypatch):
    window = _failing_window(qtbot, tmp_path, monkeypatch)
    assert window.close() is False
    qtbot.waitUntil(lambda: getattr(window, "_close_question", None) is not None
                    and _question(window).isVisible(), timeout=3000)
    # a second close while the question is up must not close the window
    assert window.close() is False and not window._closed
    _question(window).button(QMessageBox.StandardButton.No).click()
    qtbot.waitUntil(lambda: not _question(window).isVisible(), timeout=3000)
    window.registry.action("app.cikis").trigger()  # Ctrl+Q after No: retried, asked again
    qtbot.waitUntil(lambda: _question(window).isVisible(), timeout=3000)
    assert not window._closed and window.controller() is not None
    window.close_job()  # Ctrl+W: retried, refused with the status, the job stays
    qtbot.waitUntil(lambda: window.message.text() == "Kaydedilemedi: salt okunur", timeout=3000)
    assert window.controller() is not None
