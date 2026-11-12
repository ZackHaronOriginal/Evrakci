import os
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from evrakci.pipeline.settings import SettingsError, load_settings
from evrakci.pipeline.store import JobStore, default_root
from evrakci.pipeline.templates.store import TemplateStore, default_template_root
from evrakci.ui import fonts, icons, theme
from evrakci.ui.main_window import MainWindow


def build_window(
    job_root: Path | None = None,
    template_root: Path | None = None,
    settings_path: Path | None = None,
) -> MainWindow:
    """The main window, after jobs past the day limit (if one is set) are deleted."""
    store = JobStore(job_root or default_root())
    notes = []
    try:
        days = load_settings(settings_path).retention_days
    except SettingsError as error:
        days = None
        notes.append(f"{error}. Varsayılan kullanılıyor: sakla.")
    if days:
        failed = []
        deleted = store.delete_older_than(days, on_error=failed.append)
        if deleted:
            notes.append(f"Saklama süresi dolan {len(deleted)} iş silindi.")
        if failed:
            notes.append(f"Silinemedi: {'; '.join(failed)}")
    window = MainWindow(store, TemplateStore(template_root or default_template_root()),
                        settings_path=settings_path)
    if notes:
        window.message.setText(" ".join(notes))
    return window


def configure_application(app: QApplication) -> None:
    app.setApplicationName("Evrakçı")
    # Matches the Linux menu entry (evrakci-arayuz.desktop), so the dock shows its icon.
    app.setDesktopFileName("evrakci-arayuz")
    app.setStyle("Fusion")  # the same base look on Windows and Linux; the stylesheet does the rest
    fonts.register_fonts()
    theme.apply_font(app)
    app.setPalette(theme.palette())
    app.setWindowIcon(icons.app_icon())


def hide_console_for_children(windows=None, frozen=None, kernel32=None, user32=None) -> bool:
    """Give the window app one hidden console, so the programs OCRmyPDF starts (Tesseract)
    use it instead of flashing a console window each time. Windows build only."""
    windows = os.name == "nt" if windows is None else windows
    frozen = getattr(sys, "frozen", False) if frozen is None else frozen
    if not (windows and frozen):
        return False
    if kernel32 is None or user32 is None:
        import ctypes

        kernel32, user32 = ctypes.windll.kernel32, ctypes.windll.user32
    if kernel32.GetConsoleWindow():
        return False  # started from a console: keep it
    if not kernel32.AllocConsole():
        return False
    window = kernel32.GetConsoleWindow()
    if window:
        user32.ShowWindow(window, 0)  # SW_HIDE
    return True


def main() -> int:
    from multiprocessing import freeze_support

    freeze_support()  # OCRmyPDF's worker processes in the frozen Windows app
    hide_console_for_children()
    app = QApplication(sys.argv)
    configure_application(app)
    window = build_window()
    window.show()
    close_after = os.environ.get("EVRAKCI_KAPAT_MS")  # smoke tests: start, then close itself
    if close_after:
        QTimer.singleShot(int(close_after), app.quit)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
