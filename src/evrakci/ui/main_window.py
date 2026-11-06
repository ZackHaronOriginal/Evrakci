from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QTabWidget, QVBoxLayout, QWidget

from evrakci import __version__

# Screen names are Turkish-first; see CONTRIBUTING.md.
TABS = [
    ("Yükle", "Taranmış PDF dosyalarını buraya sürükleyin."),
    ("Kontrol", "Belge ayrımlarını ve türlerini burada onaylayın."),
    ("Dışa Aktar", "PDF'leri ve Excel listesini dışa aktarın."),
    ("Rehber", "Tarama rehberi burada görünecek."),
]


def _placeholder(text: str) -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    label = QLabel(text)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(label)
    return page


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"Evrakçı {__version__}")
        self.resize(1100, 720)
        self.tabs = QTabWidget()
        for name, text in TABS:
            self.tabs.addTab(_placeholder(text), name)
        self.setCentralWidget(self.tabs)
