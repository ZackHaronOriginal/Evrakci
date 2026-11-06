import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from evrakci.ui.main_window import TABS, MainWindow  # noqa: E402


def test_main_window_has_all_tabs() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    names = [window.tabs.tabText(i) for i in range(window.tabs.count())]
    assert names == [name for name, _ in TABS]
    window.close()
    assert app is not None
