import sys

from PySide6.QtWidgets import QApplication

from evrakci.ui.main_window import MainWindow


def main() -> int:
    from multiprocessing import freeze_support

    freeze_support()  # OCRmyPDF's worker processes in the frozen Windows app
    app = QApplication(sys.argv)
    app.setApplicationName("Evrakçı")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
