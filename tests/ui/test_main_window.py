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
    assert second.yukle.controller is not None
    assert second.yukle.controller.job.id == job_id


def test_app_applies_the_day_limit_at_start(qtbot, tmp_path):
    import os
    import time

    from evrakci.app import build_window
    from evrakci.pipeline.settings import Settings, save_settings

    pdf = make_pdf(tmp_path / "t.pdf", [text_page()])
    store = JobStore(tmp_path / "jobs")
    old = store.create_job("Eski", [pdf])
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
