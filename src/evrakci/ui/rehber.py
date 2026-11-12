"""The Rehber screen: the scanning guide, and separator sheets to print."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from evrakci.pipeline.ocr.models import app_dir, data_dir
from evrakci.pipeline.separator import make_separator_pdf
from evrakci.ui.widgets import index_rule, key_button


def guide_text() -> str:
    """The scanning guide shipped with the app (docs/tarama-rehberi.md)."""
    here = Path(__file__).resolve()
    bundle = app_dir()  # the installed app ships docs/ next to evrakci-arayuz.exe
    folders = [bundle / "docs"] if bundle is not None else []
    folders += [here.parents[3] / "docs"]  # a source checkout
    for folder in folders:
        path = folder / "tarama-rehberi.md"
        if path.is_file():
            return path.read_text(encoding="utf-8")
    return "# Tarama rehberi\n\nRehber dosyası bulunamadı."


class RehberScreen(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("page")
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        reading = QVBoxLayout()
        reading.setContentsMargins(32, 16, 32, 16)
        self.text = QTextBrowser()
        self.text.setOpenExternalLinks(True)
        self.text.setMarkdown(guide_text())
        self.text.setStyleSheet("font-size: 16px; background: transparent; border: 0;")
        reading.addWidget(self.text)
        root.addLayout(reading, 1)

        side = QFrame()
        side.setObjectName("card")
        side.setFixedWidth(300)
        layout = QVBoxLayout(side)
        layout.setContentsMargins(20, 16, 20, 16)
        title = QLabel("Ayıraç sayfası yazdır")
        title.setStyleSheet("font-size: 20px; font-weight: 700;")
        layout.addWidget(title)
        layout.addWidget(index_rule())
        row = QHBoxLayout()
        row.addWidget(QLabel("Kaç adet"))
        self.count = QSpinBox()
        self.count.setRange(1, 200)
        self.count.setValue(20)
        row.addWidget(self.count)
        row.addWidget(QLabel("sayfa"))
        layout.addLayout(row)
        self.print_button = key_button("PDF olarak aç", "", primary=True)
        self.print_button.clicked.connect(self.open_separators)
        layout.addWidget(self.print_button)
        note = QLabel("Ayıraç sayfaları dışa aktarılmaz. PDF görüntüleyicide açılır; "
                      "oradan yazdırın.")
        note.setWordWrap(True)
        note.setProperty("role", "muted")
        layout.addWidget(note)
        layout.addStretch(1)
        root.addWidget(side)

    def write_separators(self, path: Path, sheets: int) -> Path:
        return make_separator_pdf(Path(path), sheets=sheets)

    def open_separators(self) -> None:
        path = self.write_separators(data_dir() / "ayirac-sayfalari.pdf", self.count.value())
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
