import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # window tests run without a screen

import pytest

from evrakci.pipeline.ocr.tesseract import TesseractEngine


@pytest.fixture(autouse=True)
def _private_ui_settings(tmp_path, monkeypatch):
    """Every test gets its own window-settings file (prefs.default_settings_file), so no test
    reads or writes the real ~/.config/Evrakçı/Evrakçı.ini and one run cannot leak column
    widths, geometry or the last tab into the next."""
    monkeypatch.setenv("EVRAKCI_UI_AYARLAR", str(tmp_path / "ui-ayarlar.ini"))


def _look():
    from PySide6.QtWidgets import QApplication

    from evrakci.ui import theme

    app = QApplication.instance() or QApplication([])
    return theme.manager(), app


def _snapshot(manager, app):
    return (manager._app, app.font(), app.palette(), app.styleSheet(), app.applicationName(),
            app.desktopFileName())


def _restore(manager, app, saved) -> None:
    if _snapshot(manager, app) == saved:
        return  # nothing changed the application's look
    app.processEvents()  # the last test's windows finish closing before the look changes
    manager._app, font, palette, sheet, name, desktop = saved
    app.setFont(font)
    app.setPalette(palette)
    app.setStyleSheet(sheet)
    app.setApplicationName(name)
    app.setDesktopFileName(desktop)
    app.processEvents()


@pytest.fixture(autouse=True, scope="module")
def _app_look_stays_in_its_module():
    """A test that calls evrakci.app.configure_application (or builds the real window, as the
    shortcut audit does) binds the theme manager to the QApplication and installs Inter, the
    palette and the style sheet on it. Without this, every later module measures the panels in
    that look and every text-size change re-applies it (the Değerler side-panel scroll test
    failed in full runs only). The look is put back when the module ends."""
    manager, app = _look()
    saved = _snapshot(manager, app)
    yield
    _restore(manager, app, saved)


@pytest.fixture
def real_look():
    """The application as the real start-up sets it up (evrakci.app.configure_application:
    Inter, palette, style sheet), for one test; the plain test look comes back afterwards."""
    from evrakci import app as start_up

    manager, app = _look()
    saved = _snapshot(manager, app)
    start_up.configure_application(app)
    yield app
    _restore(manager, app, saved)


MODAL_ANSWERED = "evrakci_test_modal_answered"  # QApplication property: a helper answers dialogs


def _modal_text(args) -> str:
    texts = [a for a in args[1:] if isinstance(a, str)]  # (parent, title, text, ...)
    return " | ".join(texts) or "(no text)"


@pytest.fixture(autouse=True)
def _no_stray_modal_dialogs(monkeypatch):
    """A modal dialog nobody answers blocks the run for ever (it hung Windows CI in
    MainWindow.closeEvent). QMessageBox's static helpers and QDialog.exec/QMessageBox.exec raise
    instead, unless the test patches them itself (its own monkeypatch wins) or answers dialogs
    through tests/ui/contract_helpers (on_modal / watchdog set MODAL_ANSWERED on the app)."""
    from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

    def answered() -> bool:
        app = QApplication.instance()
        return bool(app is not None and app.property(MODAL_ANSWERED))

    def guard_static(name):
        original = getattr(QMessageBox, name)

        def guarded(*args, **kwargs):
            if answered():
                return original(*args, **kwargs)
            raise AssertionError(f"unexpected modal dialog in a test: {_modal_text(args)}")

        return staticmethod(guarded)

    for name in ("question", "warning", "information", "critical"):
        monkeypatch.setattr(QMessageBox, name, guard_static(name))
    for cls in (QDialog, QMessageBox):
        original_exec = cls.exec

        def guarded_exec(self, *args, _original=original_exec, **kwargs):
            if answered():
                return _original(self, *args, **kwargs)
            text = getattr(self, "text", lambda: "")() or self.windowTitle()
            what = text or type(self).__name__
            raise AssertionError(f"unexpected modal dialog in a test: {what}")

        monkeypatch.setattr(cls, "exec", guarded_exec)


def _tesseract_missing() -> str | None:
    return TesseractEngine().available()


needs_tesseract = pytest.mark.skipif(
    _tesseract_missing() is not None, reason="Tesseract (tur) kurulu değil"
)


def _rapidocr_missing() -> str | None:
    try:
        from evrakci.pipeline.ocr.rapid import RapidOcrEngine
    except ImportError:
        return "rapidocr yok"
    return RapidOcrEngine(download=False).available()


needs_rapidocr = pytest.mark.skipif(
    _rapidocr_missing() is not None, reason="RapidOCR veya modelleri yok"
)
