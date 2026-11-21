"""The questions Kontrol asks: "Filtre uygula…" (every how many pages), "Ölçüte göre seç…"
(which pages to select) and Ctrl+G "Belgeye veya sayfaya git…". Small dialogs with visible
labels, the range as helper text, the safe button first and one primary verb; Enter confirms,
Esc closes, focus starts in the first field and goes back to the timeline afterwards.
"""

from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QBoxLayout,
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

from evrakci.pipeline.job import Job
from evrakci.pipeline.select import Criterion, combine, evaluate
from evrakci.ui import fonts, theme


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


class SelectDialog(QDialog):
    """Ölçüte göre seç…: a list of criteria with the live count of each, the parameters of the
    chosen one on the right and how the result joins the selection. It only chooses pages: the
    caller turns `criterion()` and `mode()` into a selection, nothing in the job changes.
    At 150 % text the two columns stack."""

    ROWS = (
        ("belge", "Bu belge", ""),
        ("tek", "Tek sayfalar", "Her belgenin 1., 3., 5. ... sayfaları"),
        ("cift", "Çift sayfalar", "Her belgenin 2., 4., 6. ... sayfaları"),
    )
    MODES = (("replace", "Seçimi değiştir"), ("add", "Seçime ekle"),
             ("within", "Seçimle kesiştir"))

    def __init__(self, job: Job, document: int, selection: Iterable[str] = (),
                 kind: str = "belge", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        m = theme.manager()
        self._job, self._document = job, document
        self._selection = tuple(selection)
        self.setWindowTitle("Sayfaları seç")
        self.setAccessibleName("Sayfaları seç")
        stacked = m.text_scale() >= 150
        col = QVBoxLayout(self)
        col.setContentsMargins(*(m.size("s6"),) * 4)
        col.setSpacing(m.size("s2"))
        columns = QBoxLayout(QBoxLayout.Direction.TopToBottom if stacked
                             else QBoxLayout.Direction.LeftToRight)
        columns.setSpacing(m.size("s8") if not stacked else m.size("s4"))

        left = QVBoxLayout()
        left.setSpacing(m.size("s1"))
        heading = QLabel("Ölçüt")
        heading.setProperty("kind", "group-label")
        left.addWidget(heading)
        self.kinds = QButtonGroup(self)
        self._radios: dict[str, QRadioButton] = {}
        self._counts: dict[str, QLabel] = {}
        for name, text, _hint in self.ROWS:
            row = QHBoxLayout()
            radio = QRadioButton(text)
            self.kinds.addButton(radio)
            self._radios[name] = radio
            count = QLabel()
            count.setFont(fonts.tabular(count.font()))
            count.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._counts[name] = count
            row.addWidget(radio, 1)
            row.addSpacing(m.size("s4"))
            row.addWidget(count)
            left.addLayout(row)
            radio.toggled.connect(self._row_changed)
        left.addStretch(1)

        right = QVBoxLayout()
        right.setSpacing(m.size("s2"))
        self.title = QLabel()
        self.title.setProperty("kind", "group-label")
        self.hint = QLabel()
        self.hint.setProperty("textRole", "secondary")
        self.hint.setWordWrap(True)
        right.addWidget(self.title)
        right.addWidget(self.hint)
        right.addSpacing(m.size("s2"))
        self.modes = QButtonGroup(self)
        self._mode_radios: dict[str, QRadioButton] = {}
        for name, text in self.MODES:
            radio = QRadioButton(text)
            self.modes.addButton(radio)
            self._mode_radios[name] = radio
            right.addWidget(radio)
            radio.toggled.connect(self._mode_changed)
        right.addStretch(1)

        columns.addLayout(left, 1)
        columns.addLayout(right, 1)
        col.addLayout(columns)
        col.addSpacing(m.size("s4"))
        row, self.ok = _buttons(self, "Seç")
        col.addLayout(row)

        self._mode_radios["replace"].setChecked(True)
        self._radios[kind if kind in self._radios else "belge"].setChecked(True)
        self._refresh_counts()
        self._row_changed()
        self.kinds.checkedButton().setFocus(Qt.FocusReason.OtherFocusReason)

    def kind(self) -> str:
        return next(name for name, radio in self._radios.items() if radio.isChecked())

    def mode(self) -> str:
        return next(name for name, radio in self._mode_radios.items() if radio.isChecked())

    def criterion(self, kind: str | None = None) -> Criterion:
        kind = kind or self.kind()
        if kind == "belge":
            return Criterion("belge", {"number": self._document})
        return Criterion(kind, {"within": self.mode() == "within"})

    def count(self, kind: str) -> int:
        """How many pages Seç would select for this row in the chosen mode."""
        match = evaluate(self._job, self.criterion(kind), selection=self._selection)
        mode = self.mode()
        return len(combine(self._selection, match, "within" if mode == "within" else "replace"))

    def _refresh_counts(self) -> None:
        for name, text, _hint in self.ROWS:
            n = self.count(name)
            label = self._counts[name]
            label.setText(str(n) if n else "Hiç yok")
            label.setProperty("textRole", None if n else "secondary")
            label.style().unpolish(label)
            label.style().polish(label)
            self._radios[name].setAccessibleName(f"{text}, {label.text()}")

    def _row_changed(self, *_args) -> None:
        if not hasattr(self, "title"):
            return
        name = self.kind()
        _kind, text, hint = next(row for row in self.ROWS if row[0] == name)
        self.title.setText(text)
        self.hint.setText(hint)
        self.hint.setVisible(bool(hint))
        self.title.setAccessibleName(text)
        for radio in self._mode_radios.values():
            radio.setAccessibleDescription(hint)

    def _mode_changed(self, *_args) -> None:
        if hasattr(self, "_counts") and self.modes.checkedButton() is not None:
            self._refresh_counts()
