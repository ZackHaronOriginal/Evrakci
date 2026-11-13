"""The two questions Kontrol asks: "Filtre uygula…" (every how many pages) and Ctrl+G
"Belgeye veya sayfaya git…". Small dialogs with visible labels, the range as helper text,
the safe button first and one primary verb; Enter confirms, Esc closes, focus starts in the
number field and goes back to the timeline afterwards.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from evrakci.ui import theme


def _buttons(dialog: QDialog, verb: str) -> tuple[QHBoxLayout, QPushButton]:
    row = QHBoxLayout()
    row.addStretch(1)
    cancel = QPushButton("Vazgeç")
    cancel.clicked.connect(dialog.reject)
    ok = QPushButton(verb)
    ok.setProperty("variant", "primary")
    ok.setDefault(True)
    ok.clicked.connect(dialog.accept)
    row.addWidget(cancel)
    row.addWidget(ok)
    return row, ok


class FilterDialog(QDialog):
    """Filtre uygula…: the selected pages become documents of N pages each."""

    def __init__(self, pages: int, every_n: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        m = theme.manager()
        self.setWindowTitle("Filtre uygula")
        self.setAccessibleName("Filtre uygula")
        col = QVBoxLayout(self)
        col.setContentsMargins(*(m.size("s6"),) * 4)
        col.setSpacing(m.size("s2"))
        intro = QLabel(f"Seçili {pages} sayfa, her biri aynı sayıda sayfadan oluşan "
                       "belgelere ayrılır.")
        intro.setWordWrap(True)
        col.addWidget(intro)
        col.addSpacing(m.size("s2"))
        label = QLabel("Her belgedeki sayfa sayısı")
        self.every_n = QSpinBox()
        self.every_n.setRange(1, 999)
        self.every_n.setValue(max(1, every_n))
        self.every_n.setAccessibleName("Her belgedeki sayfa sayısı")
        label.setBuddy(self.every_n)
        hint = QLabel("Örnek: önlü arkalı tek yapraklı belgeler için 2.")
        hint.setProperty("textRole", "secondary")
        hint.setWordWrap(True)
        self.every_n.setAccessibleDescription(hint.text())
        for widget in (label, self.every_n, hint):
            col.addWidget(widget)
        col.addSpacing(m.size("s4"))
        row, self.ok = _buttons(self, "Filtreyi uygula")
        col.addLayout(row)
        self.every_n.setFocus(Qt.FocusReason.OtherFocusReason)
        self.every_n.selectAll()

    def value(self) -> int:
        return self.every_n.value()


class GoToDialog(QDialog):
    """Ctrl+G: a document or a page number, its range shown under the field."""

    def __init__(self, documents: int, pages: int, kind: str = "belge", number: int = 1,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        m = theme.manager()
        self._limits = {"belge": max(1, documents), "sayfa": max(1, pages)}
        self.setWindowTitle("Belgeye veya sayfaya git")
        self.setAccessibleName("Belgeye veya sayfaya git")
        col = QVBoxLayout(self)
        col.setContentsMargins(*(m.size("s6"),) * 4)
        col.setSpacing(m.size("s2"))
        choose = QHBoxLayout()
        choose.setSpacing(m.size("s4"))
        self.document = QRadioButton("Belge")
        self.page = QRadioButton("Sayfa")
        group = QButtonGroup(self)
        for button in (self.document, self.page):
            group.addButton(button)
            choose.addWidget(button)
        choose.addStretch(1)
        col.addLayout(choose)
        col.addSpacing(m.size("s2"))
        self.label = QLabel("Numara")
        self.number = QSpinBox()
        self.label.setBuddy(self.number)
        self.hint = QLabel("")
        self.hint.setProperty("textRole", "secondary")
        for widget in (self.label, self.number, self.hint):
            col.addWidget(widget)
        col.addSpacing(m.size("s4"))
        row, self.ok = _buttons(self, "Git")
        col.addLayout(row)
        self.document.toggled.connect(self._kind_changed)
        (self.page if kind == "sayfa" else self.document).setChecked(True)
        self._kind_changed()
        self.number.setValue(number)
        self.number.setFocus(Qt.FocusReason.OtherFocusReason)
        self.number.selectAll()

    def kind(self) -> str:
        return "sayfa" if self.page.isChecked() else "belge"

    def _kind_changed(self, *_args) -> None:
        kind = self.kind()
        limit = self._limits[kind]
        self.number.setRange(1, limit)
        name = "Belge numarası" if kind == "belge" else "Sayfa numarası"
        self.label.setText(name)
        self.number.setAccessibleName(name)
        self.hint.setText(f"1 ile {limit} arası")
        self.number.setAccessibleDescription(self.hint.text())

    def value(self) -> int:
        return self.number.value()
