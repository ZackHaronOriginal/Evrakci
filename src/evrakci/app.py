import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from evrakci.pipeline.settings import SettingsError, load_settings
from evrakci.pipeline.store import JobStore, default_root
from evrakci.pipeline.templates.store import TemplateStore, default_template_root
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


def main() -> int:
    from multiprocessing import freeze_support

    freeze_support()  # OCRmyPDF's worker processes in the frozen Windows app
    app = QApplication(sys.argv)
    app.setApplicationName("Evrakçı")
    window = build_window()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
