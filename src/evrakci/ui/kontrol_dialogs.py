"""The questions Kontrol asks: "Filtre uygula…" (every how many pages), "Ölçüte göre seç…"
(which pages to select) and Ctrl+G "Belgeye veya sayfaya git…". Small dialogs with visible
labels, the range as helper text, the safe button first and one primary verb; Enter confirms,
Esc closes, focus starts in the first field and goes back to the timeline afterwards.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from PySide6.QtCore import QLocale, Qt, QTimer
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (
    QBoxLayout,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from evrakci.pipeline.analyze import EMPTY_INK_RATIO
from evrakci.pipeline.job import Job
from evrakci.pipeline.select import (
    FARKLI_BY,
    GUVEN_CHECKS,
    GUVEN_DEFAULT,
    GUVEN_LEVELS,
    GUVEN_REASONS,
    GUVEN_WORDS,
    Criterion,
    combine,
    evaluate,
    guven_findings,
    guven_match,
    ink_range,
    reason_count_text,
    unknown_sizes,
    values_read,
)
from evrakci.ui import fonts, icons, theme
from evrakci.ui.degerler_model import LEVELS

NBSP = " "  # a number and its unit never part when a line wraps at 150 %


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
    The modes sit under the criteria list so the dialog stays short at 150 % text."""

    ROWS = (
        ("belge", "Bu belge", ""),
        ("tek", "Tek sayfalar", "Her belgenin 1., 3., 5. ... sayfaları"),
        ("cift", "Çift sayfalar", "Her belgenin 2., 4., 6. ... sayfaları"),
        ("bos", "Boş sayfalar", ""),
        ("guven", "Kontrol gerekenler", ""),
        ("farkli", "Farklı boyut veya yön", ""),
    )
    NOT_READ = "Değerler henüz okunmadı"
    INK_RANGE = (0.1, 5.0)  # percent
    INK_DEBOUNCE_MS = 80
    FARKLI_BOXES = (("boyut", "Boyut"), ("yon", "Yön"))
    FARKLI_REFERENCES = (("is", "Bütün iş"), ("belge", "Her belge"))
    MODES = (("replace", "Seçimi değiştir"), ("add", "Seçime ekle"),
             ("within", "Seçimle kesiştir"))

    def __init__(self, job: Job, document: int, selection: Iterable[str] = (),
                 kind: str = "belge", parent: QWidget | None = None,
                 templates: Mapping | None = None) -> None:
        super().__init__(parent)
        m = theme.manager()
        self._job, self._document = job, document
        self._templates = templates or {}
        # Built once on open (the dialog is modal, the job cannot change under it): the rows of
        # Kontrol gerekenler and the counts of every reason.
        self._findings = guven_findings(job, self._templates)
        self._has_values = values_read(job)
        self._selection = tuple(selection)
        self.setWindowTitle("Sayfaları seç")
        self.setAccessibleName("Sayfaları seç")
        col = QVBoxLayout(self)
        col.setContentsMargins(*(m.size("s6"),) * 4)
        col.setSpacing(m.size("s2"))
        columns = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        columns.setSpacing(m.size("s8"))

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
        left.addSpacing(m.size("s4"))
        self.modes = QButtonGroup(self)
        self._mode_radios: dict[str, QRadioButton] = {}
        for name, text in self.MODES:  # how the result joins the selection: under the list
            radio = QRadioButton(text)
            self.modes.addButton(radio)
            self._mode_radios[name] = radio
            left.addWidget(radio)
            radio.toggled.connect(self._mode_changed)
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
        self._blank_parameters(right)
        self._guven_parameters(right)
        self._farkli_parameters(right)
        right.addStretch(1)

        columns.addLayout(left, 1)
        columns.addLayout(right, 1)
        col.addLayout(columns)
        col.addSpacing(m.size("s4"))
        row, self.ok = _buttons(self, "Seç")
        col.addLayout(row)
        self._tab_order()

        self._mode_radios["replace"].setChecked(True)
        if kind == "guven" and not self._has_values:
            kind = "belge"  # the row is off; the dialog opens on the first one
        self._radios[kind if kind in self._radios else "belge"].setChecked(True)
        self._refresh_counts()
        self._blank_count_text()
        self._row_changed()
        self.kinds.checkedButton().setFocus(Qt.FocusReason.OtherFocusReason)

    def _tab_order(self) -> None:
        """Criterion -> its parameters -> the modes -> Seç -> Vazgeç. Parameters of other
        criteria are hidden and Tab skips them, so one fixed chain serves every criterion."""
        cancel = self.ok.parentWidget().findChildren(QPushButton)
        cancel = next(b for b in cancel if b is not self.ok)
        chain = [*self._radios.values(), self.ink,
                 *(box for box in self._reason_boxes.values()),
                 self.pages_value, self.pages_document,
                 *self.farkli_boxes.values(), self.farkli_reference,
                 *self._mode_radios.values(), self.ok, cancel]
        for first, second in zip(chain, chain[1:], strict=False):
            QWidget.setTabOrder(first, second)

    def _blank_parameters(self, col: QVBoxLayout) -> None:
        """The parameter pane of "Boş sayfalar" (ink limit, hint, live count) goes straight into
        `col`: wrapped labels in a nested widget lose their height at 150 % text."""
        label = QLabel("En çok mürekkep oranı")
        self.ink = QDoubleSpinBox()
        self.ink.setLocale(QLocale(QLocale.Language.Turkish, QLocale.Country.Turkey))
        self.ink.setDecimals(1)
        self.ink.setSingleStep(0.1)
        self.ink.setRange(*self.INK_RANGE)
        self.ink.setValue(EMPTY_INK_RATIO * 100)
        self.ink.setSuffix(" %")
        self.ink.setAccessibleName("En çok mürekkep oranı")
        label.setBuddy(self.ink)
        self.ink_hint = QLabel("Bu orandan az mürekkepli sayfalar boş sayılır.")
        self.ink_hint.setProperty("textRole", "secondary")
        self.ink_hint.setWordWrap(True)
        self.ink.setAccessibleDescription(self.ink_hint.text())
        self.ink_count = QLabel()
        self.ink_count.setWordWrap(True)
        self.ink_count.setFont(fonts.tabular(self.ink_count.font()))
        self.ink_widgets = (label, self.ink, self.ink_hint, self.ink_count)
        for widget in self.ink_widgets:
            col.addWidget(widget)
        # Every key press changes the count; the evaluation waits until the typing pauses.
        self._ink_timer = QTimer(self)
        self._ink_timer.setSingleShot(True)
        self._ink_timer.setInterval(self.INK_DEBOUNCE_MS)
        self._ink_timer.timeout.connect(self._ink_settled)
        self.ink.valueChanged.connect(lambda *_: self._ink_timer.start())

    def ink_ratio(self) -> float:
        """The spin box as a fraction (0,3 % is 0.003)."""
        return round(self.ink.value() / 100, 6)

    @staticmethod
    def _percent(ratio: float) -> str:
        text = f"{round(ratio * 100, 2):.2f}".rstrip("0")
        text = text + "0" if text.endswith(".") else text
        return text.replace(".", ",")

    def _ink_settled(self) -> None:
        self._refresh_counts()
        self._blank_count_text()

    def _blank_count_text(self) -> None:
        match = evaluate(self._job, self.criterion("bos"))
        text = f"{match.count()} sayfa boş"
        spread = ink_range(self._job, match)
        details = []
        if spread:
            low, high = spread
            # U+00A0: a number and its unit never part when the line wraps at 150 %
            details.append(
                f"en boş {self._percent(low)}\u00a0%, en dolu {self._percent(high)}\u00a0%")
        deleted = match.reasons.get("silinmis", 0)
        if deleted:
            details.append(f"{deleted}\u00a0silinmiş")
        if details:
            text += "   (" + ", ".join(details) + ")"
        self.ink_count.setText(text)

    def _guven_parameters(self, col: QVBoxLayout) -> None:
        """The parameter pane of "Kontrol gerekenler": a check box per reason with its icon,
        word and count, the pages and the live count."""
        m = theme.manager()
        every = guven_match(self._job, self._findings, Criterion("guven", {
            "levels": GUVEN_LEVELS, "checks": GUVEN_CHECKS, "pages": "belge"}))
        self._reason_totals = dict(every.reasons)
        self._reason_boxes: dict[str, QCheckBox] = {}
        self._reason_counts: dict[str, QLabel] = {}
        widgets: list[QWidget] = []
        for reason in GUVEN_REASONS:
            n = self._reason_totals.get(reason, 0)
            box = QCheckBox(GUVEN_WORDS[reason])
            box.setChecked(reason in GUVEN_DEFAULT)
            if reason in LEVELS:
                icon, role, _word, _strong = LEVELS[reason]
                box.setIcon(icons.icon(icon, m.hex(role)))
                if reason == "kontrol":  # the one orange-family word, as in Değerler
                    palette = box.palette()
                    palette.setColor(QPalette.ColorRole.WindowText, m.color(role))
                    box.setPalette(palette)
                    box.setStyleSheet(f"QCheckBox {{ color: {m.hex(role)}; }}")
            count = QLabel(reason_count_text(reason, n).replace(" ", NBSP))
            count.setFont(fonts.tabular(count.font()))
            count.setProperty("textRole", "secondary")
            box.setAccessibleName(f"{GUVEN_WORDS[reason]}, {reason_count_text(reason, n)}")
            row = QHBoxLayout()
            row.setSpacing(m.size("s4"))
            row.addWidget(box, 1)
            row.addWidget(count)
            col.addLayout(row)
            self._reason_boxes[reason] = box
            self._reason_counts[reason] = count
            widgets += [box, count]
            box.toggled.connect(self._guven_changed)
        if not self._reason_totals.get("karışık şablon"):  # rare: only shown when there is one
            for widget in widgets[-2:]:
                widget.setVisible(False)
            self._hidden_reason = widgets[-2:]
        else:
            self._hidden_reason = []
        self.pages_label = QLabel("Sayfalar")
        self.pages_value = QRadioButton("Değerin sayfası")
        self.pages_document = QRadioButton("Belgenin bütün sayfaları")
        self.pages_value.setChecked(True)
        pages = QButtonGroup(self)
        pages.addButton(self.pages_value)
        pages.addButton(self.pages_document)
        self.pages_value.setAccessibleName("Sayfalar: Değerin sayfası")
        self.pages_document.setAccessibleName("Sayfalar: Belgenin bütün sayfaları")
        self.pages_value.toggled.connect(self._guven_changed)
        self.guven_count = QLabel()
        self.guven_count.setFont(fonts.tabular(self.guven_count.font()))
        self.guven_count.setWordWrap(True)
        self.guven_widgets = [self.pages_label, self.pages_value, self.pages_document,
                              self.guven_count]
        for widget in self.guven_widgets:
            col.addWidget(widget)
        self._guven_rows = widgets
        self._guven_texts()

    def _farkli_parameters(self, col: QVBoxLayout) -> None:
        """The parameter pane of "Farklı boyut veya yön": Boyut and Yön check boxes (both on),
        what to compare with, and the live count; the pages of unknown size are named."""
        self.farkli_boxes: dict[str, QCheckBox] = {}
        widgets: list[QWidget] = []
        for name, text in self.FARKLI_BOXES:
            box = QCheckBox(text)
            box.setChecked(True)
            box.toggled.connect(self._farkli_changed)
            self.farkli_boxes[name] = box
            widgets.append(box)
        self.farkli_label = QLabel("Karşılaştır")
        self.farkli_reference = QComboBox()
        for value, text in self.FARKLI_REFERENCES:
            self.farkli_reference.addItem(text, value)
        self.farkli_reference.setAccessibleName("Karşılaştır")
        self.farkli_label.setBuddy(self.farkli_reference)
        self.farkli_reference.currentIndexChanged.connect(self._farkli_changed)
        self.farkli_count = QLabel()
        self.farkli_count.setFont(fonts.tabular(self.farkli_count.font()))
        self.farkli_count.setWordWrap(True)
        self.farkli_note = QLabel()
        self.farkli_note.setProperty("textRole", "secondary")
        self.farkli_note.setWordWrap(True)
        self._unknown = unknown_sizes(self._job)
        if self._unknown:
            self.farkli_note.setText(f"Boyutu bilinmiyor ({self._unknown})")
        self.farkli_widgets = [*widgets, self.farkli_label, self.farkli_reference,
                               self.farkli_count, self.farkli_note]
        for widget in self.farkli_widgets:
            col.addWidget(widget)
        self._farkli_texts()

    def _farkli_texts(self) -> None:
        match = evaluate(self._job, self.criterion("farkli"))
        self.farkli_count.setText(f"{match.count()}{NBSP}sayfa farklı görünüyor")

    def _farkli_changed(self, *_args) -> None:
        if hasattr(self, "farkli_count"):
            self._farkli_texts()
            self._refresh_counts()

    def _guven_texts(self) -> None:
        match = self._guven_match()
        self.guven_count.setText(
            f"{match.documents}{NBSP}belge, {match.count()}{NBSP}sayfa")

    def _guven_match(self):
        return guven_match(self._job, self._findings, self.criterion("guven"))

    def _guven_changed(self, *_args) -> None:
        if hasattr(self, "guven_count"):
            self._guven_texts()
            self._refresh_counts()

    def kind(self) -> str:
        return next(name for name, radio in self._radios.items() if radio.isChecked())

    def mode(self) -> str:
        return next(name for name, radio in self._mode_radios.items() if radio.isChecked())

    def criterion(self, kind: str | None = None) -> Criterion:
        kind = kind or self.kind()
        if kind == "belge":
            return Criterion("belge", {"number": self._document})
        if kind == "bos":
            return Criterion("bos", {"ink": self.ink_ratio()})
        if kind == "guven":
            reasons = [r for r, box in self._reason_boxes.items() if box.isChecked()]
            return Criterion("guven", {
                "levels": [r for r in reasons if r in GUVEN_LEVELS],
                "checks": [r for r in reasons if r in GUVEN_CHECKS],
                "pages": "deger" if self.pages_value.isChecked() else "belge"})
        if kind == "farkli":
            return Criterion("farkli", {
                "by": [name for name in FARKLI_BY if self.farkli_boxes[name].isChecked()],
                "reference": self.farkli_reference.currentData()})
        return Criterion(kind, {"within": self.mode() == "within"})

    def count(self, kind: str) -> int:
        """How many pages Seç would select for this row in the chosen mode."""
        if kind == "guven":
            match = self._guven_match()
        else:
            match = evaluate(self._job, self.criterion(kind), selection=self._selection)
        mode = self.mode()
        return len(combine(self._selection, match, "within" if mode == "within" else "replace"))

    def _refresh_counts(self) -> None:
        for name, text, _hint in self.ROWS:
            label = self._counts[name]
            if name == "guven" and not self._has_values:
                label.setText(self.NOT_READ)
                label.setProperty("textRole", "secondary")
                label.setWordWrap(True)
                label.style().unpolish(label)
                label.style().polish(label)
                self._radios[name].setEnabled(False)
                self._radios[name].setAccessibleName(f"{text}, {self.NOT_READ}")
                continue
            n = self.count(name)
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
        for widget in self.ink_widgets:
            widget.setVisible(name == "bos")
        if hasattr(self, "farkli_widgets"):
            for widget in self.farkli_widgets:
                widget.setVisible(name == "farkli")
            self.farkli_note.setVisible(bool(self._unknown) and name == "farkli")
        if hasattr(self, "guven_widgets"):
            on = name == "guven"
            for widget in (*self.guven_widgets, *self._guven_rows):
                widget.setVisible(on and widget not in self._hidden_reason)
        self.title.setAccessibleName(text)
        for radio in self._mode_radios.values():
            radio.setAccessibleDescription(hint)

    def _mode_changed(self, *_args) -> None:
        if hasattr(self, "_counts") and self.modes.checkedButton() is not None:
            self._refresh_counts()
