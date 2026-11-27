from fakes import make_pdf, qr_page, text_page
from PySide6.QtWidgets import QMessageBox

from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.ui.main_window import TAB_NAMES, MainWindow


def _window(qtbot, tmp_path):
    window = MainWindow(JobStore(tmp_path / "jobs"), TemplateStore(tmp_path / "tpl"),
                        settings_path=tmp_path / "ayar.json")
    qtbot.addWidget(window)
    return window


def test_tabs_match_the_approved_mockups(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    assert TAB_NAMES == ["Yükle", "Kontrol", "Şablonlar", "Değerler", "Dışa Aktar", "Rehber"]
    assert [window.tabs.tabText(i) for i in range(window.tabs.count())] == TAB_NAMES


def test_opening_a_job_fills_the_other_tabs_and_status_bar(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    pdf = make_pdf(tmp_path / "t.pdf", [text_page(), qr_page(), text_page()])
    with qtbot.waitSignal(window.yukle.job_opened, timeout=20000):
        window.yukle.create_job([pdf], "Kasım")
    assert window.kontrol is not None and window.kontrol.model.rowCount() == 3
    assert "2 belge" in window.counts.text()
    assert "Kasım" in window.windowTitle()


def test_closing_during_export_asks_first(qtbot, tmp_path, monkeypatch):
    window = _window(qtbot, tmp_path)
    window.disa_aktar.task = object()  # an export is running
    asked = []
    monkeypatch.setattr(QMessageBox, "question",
                        lambda *a, **k: asked.append(a) or QMessageBox.StandardButton.No)
    assert window.close() is False
    assert asked
    window.disa_aktar.task = None


def test_reopening_shows_the_last_job(qtbot, tmp_path):
    first = _window(qtbot, tmp_path)
    pdf = make_pdf(tmp_path / "t.pdf", [text_page(), text_page()])
    with qtbot.waitSignal(first.yukle.job_opened, timeout=20000):
        first.yukle.create_job([pdf], "Son iş")
    job_id = first.yukle.controller.job.id
    first.close()
    second = _window(qtbot, tmp_path)
    qtbot.waitUntil(lambda: second.yukle.controller is not None, timeout=10000)
    assert second.yukle.controller.job.id == job_id


def test_app_applies_the_day_limit_at_start(qtbot, tmp_path):
    import os
    import time

    from evrakci.app import build_window
    from evrakci.pipeline.job import LastExport
    from evrakci.pipeline.settings import Settings, save_settings

    pdf = make_pdf(tmp_path / "t.pdf", [text_page()])
    store = JobStore(tmp_path / "jobs")
    old = store.create_job("Eski", [pdf])
    old.last_export = LastExport("2026-01-01T10:00:00", "/tmp/o", 1, 0)
    store.save(old)
    stamp = time.time() - 40 * 86400
    os.utime(tmp_path / "jobs" / old.id / "job.json", (stamp, stamp))
    save_settings(Settings("30"), tmp_path / "ayar.json")
    window = build_window(tmp_path / "jobs", tmp_path / "tpl", tmp_path / "ayar.json")
    qtbot.addWidget(window)
    assert JobStore(tmp_path / "jobs").list_jobs() == []
    assert "silindi" in window.message.text()


def test_undo_follows_the_current_tab(qtbot, tmp_path):
    from PySide6.QtGui import QUndoCommand

    window = _window(qtbot, tmp_path)
    window.show_tab("sablonlar")
    stack = window.sablon.undo_stack
    assert not window.registry.is_enabled("app.geri_al")
    stack.push(QUndoCommand("Kutu taşı"))
    assert window.registry.is_enabled("app.geri_al")
    assert "Kutu taşı" in window.registry.action("app.geri_al").toolTip()
    window.registry.action("app.geri_al").trigger()
    assert stack.index() == 0
    window.show_tab("yukle")  # no job open: nothing to undo here
    assert not window.registry.is_enabled("app.geri_al")


def test_kontrol_without_a_job_offers_the_way_to_yukle(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    window.show_tab("kontrol")
    assert window.kontrol is None
    assert not window.registry.is_enabled("kontrol.kes")
    assert window.tabs.currentWidget() is window._kontrol_placeholder


def _failed_save_window(qtbot, tmp_path, monkeypatch):
    """A window whose job folder became read-only: the automatic save fails (B-035). The write
    is the saver's (behind the edit), so the failure arrives from the event loop."""
    window = _window(qtbot, tmp_path)
    pdf = make_pdf(tmp_path / "t.pdf", [text_page(), qr_page(), text_page()])
    with qtbot.waitSignal(window.yukle.job_opened, timeout=20000):
        window.yukle.create_job([pdf], "Kasım")
    controller = window.controller()
    real = controller.store.save_dict
    state = {"fail": True}

    def save_dict(job_id, data):
        if state["fail"]:
            raise OSError("salt okunur")
        return real(job_id, data)

    monkeypatch.setattr(controller.store, "save_dict", save_dict)
    controller._changed()
    qtbot.waitUntil(lambda: window.job_switch.save_state.state() == "failed", timeout=3000)
    return window, state


def test_close_after_failed_save_is_blocked_with_the_status(qtbot, tmp_path, monkeypatch):
    window, _state = _failed_save_window(qtbot, tmp_path, monkeypatch)
    assert window.close() is False  # first attempt: retried, still failing, blocked
    qtbot.waitUntil(lambda: window._close_warned, timeout=3000)
    assert window.message.text() == "Kaydedilemedi: salt okunur"
    assert window.controller() is not None
    assert window.close() is False  # Q7: every attempt retries and asks again, never silent
    assert window.controller() is not None and not window._closed


def test_close_retries_the_save_and_closes_when_it_works(qtbot, tmp_path, monkeypatch):
    window, state = _failed_save_window(qtbot, tmp_path, monkeypatch)
    state["fail"] = False
    assert window.close() is False  # the retry runs first ...
    qtbot.waitUntil(lambda: window._closed, timeout=3000)  # ... then it closes
    assert window.job_switch.save_state.state() == "saved"


def test_quit_shortcut_keeps_asking_while_the_save_fails(qtbot, tmp_path, monkeypatch):
    window, state = _failed_save_window(qtbot, tmp_path, monkeypatch)
    window.registry.action("app.cikis").trigger()
    qtbot.waitUntil(lambda: window._close_warned, timeout=3000)
    assert window.isVisible() or window.controller() is not None
    assert window.message.text().startswith("Kaydedilemedi")
    window.registry.action("app.cikis").trigger()  # still blocked: the edits are not on disk
    assert window.message.text().startswith("Kaydedilemedi")
    assert window._unsaved_pending() and not window._closed


def _answer(qtbot, window, button):
    qtbot.waitUntil(window._question_open, timeout=3000)
    box = window._close_question
    box.button(button).click()
    qtbot.waitUntil(lambda: not box.isVisible(), timeout=3000)


def test_closing_the_job_after_failed_save_asks_and_no_stays(qtbot, tmp_path, monkeypatch):
    window, state = _failed_save_window(qtbot, tmp_path, monkeypatch)
    window.close_job()
    qtbot.waitUntil(lambda: window._close_warned, timeout=3000)
    assert window.message.text() == "Kaydedilemedi: salt okunur"
    assert window._close_question.text().startswith("Değişiklikler kaydedilemedi.")
    _answer(qtbot, window, QMessageBox.StandardButton.No)
    assert window.controller() is not None and window._unsaved_pending()
    window.close_job()  # asked again, never silent
    _answer(qtbot, window, QMessageBox.StandardButton.No)
    state["fail"] = False  # the disk works again: the retry saves and the job closes
    window.close_job()
    qtbot.waitUntil(lambda: window.controller() is None, timeout=3000)


def test_closing_the_job_after_failed_save_yes_discards_and_leaves(qtbot, tmp_path, monkeypatch):
    window, _state = _failed_save_window(qtbot, tmp_path, monkeypatch)
    window.close_job()
    _answer(qtbot, window, QMessageBox.StandardButton.Yes)
    qtbot.waitUntil(lambda: window.controller() is None, timeout=3000)  # never stuck


def test_switching_the_job_after_failed_save_asks_yes_switches_no_stays(
        qtbot, tmp_path, monkeypatch):
    window, _state = _failed_save_window(qtbot, tmp_path, monkeypatch)
    old = window.controller()
    other = JobStore(tmp_path / "jobs").create_job("Diğer", [tmp_path / "t.pdf"])  # unpatched
    window.yukle.open_job_id(other.id)
    _answer(qtbot, window, QMessageBox.StandardButton.No)
    assert window.controller() is old
    window.yukle.open_job_id(other.id)
    _answer(qtbot, window, QMessageBox.StandardButton.Yes)
    qtbot.waitUntil(lambda: window.controller() is not old, timeout=5000)
    assert window.controller().job.id == other.id


def test_a_success_or_new_failed_edit_resets_the_warning(qtbot, tmp_path, monkeypatch):
    window, state = _failed_save_window(qtbot, tmp_path, monkeypatch)
    assert window._unsaved_pending()  # the last write failed
    window.close_job()
    qtbot.waitUntil(lambda: window._close_warned, timeout=3000)
    assert window._unsaved_pending()  # still pending: only a save or a Yes lets the edits go
    window.controller()._changed()  # a new edit that fails again
    qtbot.waitUntil(lambda: not window._close_warned, timeout=3000)
    assert window._unsaved_pending()
    state["fail"] = False
    window.save_job()
    qtbot.waitUntil(lambda: window.job_switch.save_state.state() == "saved", timeout=3000)
    assert not window._close_warned and not window._unsaved_pending()
