"""The box inspector of Şablonlar (final-a .inspector): Settings-style cards about the selected
box: its name, whether it is required, its page and its position in millimetres, then what the
box reads right now with how sure it is, and one primary "Şablonu kaydet" pinned below.

The panel never edits the template: it shows an `InspectorState` and reports edits through
signals. F9 hides and shows it (`setVisible` is remembered, so an empty screen can keep it away
without forgetting what the user chose).
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QLocale, QSize, Qt, Signal
from PySide6.QtGui import QValidator
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from evrakci.ui import icons, theme
from evrakci.ui.chrome import ElidedLabel, make_icon
from evrakci.ui.sablon_canvas import MIN_BOX_MM, NUDGE_MM, fmt_mm
from evrakci.ui.sablon_parts import small_button_style
from evrakci.ui.sablon_read import LEVELS, Shown

KEY_W = 76  # A .kv .r .k
FIELD_W = 64  # A .fld.small
STATE_ROLE = {"ok": "ok", "orta": "text-2", "kontrol": "check-text", "bad": "danger"}


@dataclass
class InspectorState:
    """What the panel shows. mode: "box" (a section), "variable" (no box chosen), "none"."""

    mode: str = "none"
    top: str = ""  # "Kutu 1 / 2"
    title: str = ""
    sub: str = ""
    name: str = ""
    required: bool = False
    page: int = 1
    box: tuple[float, float, float, float] = (0, 0, 0, 0)  # x0, y0, x1, y1 in mm
    sheet: tuple[float, float] = (210.0, 297.0)
    read_title: str = "Okunan"
    shown: Shown | None = None
    busy: bool = False
    hint: str = ""  # shown instead of the cards' geometry when there is no box


class MmSpin(QDoubleSpinBox):
    """A millimetre field: Turkish decimal comma, 70,0 / 70,25, no buttons, right aligned."""

    def __init__(self, label: str) -> None:
        super().__init__()
        self.setLocale(QLocale(QLocale.Language.Turkish, QLocale.Country.Turkey))
        self.setDecimals(2)
        self.setSingleStep(NUDGE_MM)
        self.setRange(0.0, 1000.0)
        self.setKeyboardTracking(False)
        self.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.setAccessibleName(label)
        self.setToolTip(label)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        return QSize(40, super().minimumSizeHint().height())  # four fit in a 312 px card

    def textFromValue(self, value: float) -> str:  # noqa: N802
        return fmt_mm(value)

    def valueFromText(self, text: str) -> float:  # noqa: N802
        try:
            return float(text.strip().replace(",", "."))
        except ValueError:
            return self.value()

    def validate(self, text: str, pos: int):
        clean = text.strip().replace(",", ".")
        if clean in ("", "."):
            return QValidator.State.Intermediate, text, pos
        try:
            float(clean)
        except ValueError:
            return QValidator.State.Invalid, text, pos
        return QValidator.State.Acceptable, text, pos


class PageSpin(QSpinBox):
    """The box's page: 1, 2, …, or "son" (-1, the last page); never 0."""

    def __init__(self) -> None:
        super().__init__()
        self.setRange(-1, 999)
        self.setValue(1)
        self.setKeyboardTracking(False)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAccessibleName("Kutunun sayfası")
        self.setToolTip("Kutunun sayfası (son: son sayfa)")

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        return QSize(40, super().minimumSizeHint().height())

    def textFromValue(self, value: int) -> str:  # noqa: N802
        return "son" if value == -1 else str(value)

    def valueFromText(self, text: str) -> int:  # noqa: N802
        text = text.strip().lower()
        if text in ("son", "-1", "-"):
            return -1
        try:
            return max(1, int(text))
        except ValueError:
            return self.value()

    def validate(self, text: str, pos: int):
        clean = text.strip().lower()
        if clean in ("", "-", "s", "so", "son") or clean.isdigit():
            ok = clean in ("son", "-1") or clean.isdigit() and int(clean) > 0
            return (QValidator.State.Acceptable if ok else QValidator.State.Intermediate), text, pos
        return QValidator.State.Invalid, text, pos

    def stepBy(self, steps: int) -> None:  # noqa: N802
        value = self.value() + steps
        if value == 0:
            value = 1 if steps > 0 else -1
        self.setValue(value)


class KvRow(QWidget):
    """A .kv .r: a 76 px caption key and a value; 40 px high, no hairlines."""

    def __init__(self, key: str, value: QWidget) -> None:
        super().__init__()
        m = theme.manager()
        self.setMinimumHeight(m.size("row-h"))
        row = QHBoxLayout(self)
        row.setContentsMargins(m.size("s4"), 0, m.size("s4"), 0)
        row.setSpacing(m.size("s3"))
        self.key = QLabel(key)
        self.key.setProperty("kind", "inspector-key")
        self.key.setFixedWidth(KEY_W)
        self.value = value
        row.addWidget(self.key, 0, Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(value, 1, Qt.AlignmentFlag.AlignVCenter)


class LevelWidget(QWidget):
    """Güven: icon + word + percent, the app's status line (never colour alone)."""

    def __init__(self) -> None:
        super().__init__()
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)  # A .st
        self.icon = QLabel()
        self.icon.setFixedSize(16, 16)
        self.word = QLabel()
        self.percent = QLabel()
        self.percent.setProperty("textRole", "secondary")
        for widget in (self.icon, self.word, self.percent):
            row.addWidget(widget)
        row.addStretch(1)
        self._level = "okunmadi"
        theme.follow(self, self._restyle, f"sablon-level-{id(self)}")

    def set(self, level: str, percent: int | None) -> None:
        self._level = level
        icon, state, word = LEVELS[level]
        self.word.setText(word)
        self.word.setProperty("state", state)
        self.word.style().unpolish(self.word)
        self.word.style().polish(self.word)
        self.percent.setText(f"%{percent}" if percent is not None else "")
        self.setAccessibleName(f"Güven: {word}" + (f" %{percent}" if percent is not None else ""))
        self._restyle()

    def _restyle(self) -> None:
        m = theme.manager()
        icon, state, _word = LEVELS[self._level]
        self.icon.setPixmap(icons.pixmap(icon, m.hex(STATE_ROLE[state]), 16))
        self.percent.setFont(m.font("num"))


def _label(text: str, kind: str = "inspector-key") -> QLabel:
    label = QLabel(text)
    label.setProperty("kind", kind)
    return label


def _card() -> QFrame:
    card = QFrame()
    card.setProperty("kind", "card")
    return card


class InspectorPanel(QWidget):
    name_edited = Signal(str)
    required_toggled = Signal(bool)
    page_edited = Signal(int)
    box_edited = Signal(tuple)  # x0, y0, x1, y1 in mm
    save_clicked = Signal()
    pattern_edited = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("sablonInspector")
        self.setAccessibleName("Kutu ayrıntısı")
        self._wanted = True  # what F9 chose; the screen may keep the panel away besides
        self._allowed = True
        self._state = InspectorState()
        m = theme.manager()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, m.size("s3"), m.size("s4"), m.size("s3"))
        outer.setSpacing(m.size("s3"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        col = QVBoxLayout(body)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(m.size("s3"))
        col.addLayout(self._head())
        col.addLayout(self._box_group())
        col.addLayout(self._read_group())
        col.addLayout(self._pattern_group())
        col.addStretch(1)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)
        self.save = QPushButton(" Şablonu kaydet")
        self.save.setProperty("variant", "primary")
        self.save.setProperty("sizeVariant", "lg")
        self.save.setAccessibleName("Şablonu kaydet")
        self.save.setToolTip("Şablonu kaydet (Ctrl+S)")
        self.save.clicked.connect(self.save_clicked)
        outer.addWidget(self.save)
        self.name.editingFinished.connect(self._name_done)
        self.required.toggled.connect(self.required_toggled)
        self.page.valueChanged.connect(self.page_edited)
        for spin in self.spins:
            spin.valueChanged.connect(self._geometry_edited)
        self.setTabOrder(self.more, self.name)
        self.setTabOrder(self.name, self.required)
        self.setTabOrder(self.required, self.page)
        previous: QWidget = self.page
        for spin in self.spins:
            self.setTabOrder(previous, spin)
            previous = spin
        self.setTabOrder(previous, self.save)
        theme.follow(self, self._restyle, "sablon-inspector")

    # -- building ---------------------------------------------------------------------------
    def _head(self) -> QVBoxLayout:
        m = theme.manager()
        col = QVBoxLayout()
        col.setSpacing(0)
        col.setContentsMargins(m.size("s1"), m.size("s1"), m.size("s1"), 0)
        top = QHBoxLayout()
        self.top = QLabel()
        self.top.setProperty("textRole", "secondary")
        self.more = QToolButton()
        self.more.setProperty("kind", "icon")
        self.more.setProperty("sizeVariant", "sm")
        self.more.setAutoRaise(True)
        self.more.setToolTip("Diğer")
        self.more.setAccessibleName("Kutu için diğer komutlar")
        self.more.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        top.addWidget(self.top, 1)
        top.addWidget(self.more)
        col.addLayout(top)
        self.title = ElidedLabel("", 8)
        self.title.setProperty("textRole", "page")
        self.sub = QLabel()
        self.sub.setProperty("textRole", "secondary")
        col.addSpacing(m.size("s1"))
        col.addWidget(self.title)
        col.addSpacing(2)
        col.addWidget(self.sub)
        return col

    def _box_group(self) -> QVBoxLayout:
        m = theme.manager()
        group = QVBoxLayout()
        group.setSpacing(0)
        self.box_label = _label("Kutu", "group-label")
        group.addWidget(self.box_label)
        self.box_card = _card()
        card = QVBoxLayout(self.box_card)
        card.setContentsMargins(*(m.size("s4"),) * 4)
        card.setSpacing(m.size("s3"))
        name = QVBoxLayout()
        name.setSpacing(m.size("s1"))
        name_label = _label("Ad")
        self.name = QLineEdit()
        self.name.setAccessibleName("Değişken adı")
        name_label.setBuddy(self.name)
        name.addWidget(name_label)
        name.addWidget(self.name)
        card.addLayout(name)
        self.line_row = QWidget()
        line = QHBoxLayout(self.line_row)
        line.setContentsMargins(0, 0, 0, 0)
        line.setSpacing(m.size("s2"))
        self.required = QCheckBox("Zorunlu")
        self.required.setAccessibleName("Zorunlu")
        self.page_key = _label("Kutunun sayfası")
        self.page = PageSpin()
        self.page.setFixedWidth(FIELD_W)
        self.page_key.setBuddy(self.page)
        line.addWidget(self.required)
        line.addStretch(1)
        line.addWidget(self.page_key)
        line.addWidget(self.page)
        card.addWidget(self.line_row)
        self.geometry = QWidget()
        geometry = QVBoxLayout(self.geometry)
        geometry.setContentsMargins(0, 0, 0, 0)
        geometry.setSpacing(m.size("s1"))
        self.geometry_label = _label("X, Y, genişlik, yükseklik (mm)")
        grid = QGridLayout()
        grid.setSpacing(m.size("s2"))
        self.spins = [MmSpin(label) for label in ("Kutu X (mm)", "Kutu Y (mm)",
                                                  "Kutu genişliği (mm)", "Kutu yüksekliği (mm)")]
        for column, spin in enumerate(self.spins):
            grid.addWidget(spin, 0, column)
            grid.setColumnStretch(column, 1)
        self.geometry_label.setBuddy(self.spins[0])
        geometry.addWidget(self.geometry_label)
        geometry.addLayout(grid)
        card.addWidget(self.geometry)
        self.hint = _label("")
        self.hint.setWordWrap(True)
        card.addWidget(self.hint)
        group.addWidget(self.box_card)
        return group

    def _read_group(self) -> QVBoxLayout:
        m = theme.manager()
        group = QVBoxLayout()
        group.setSpacing(0)
        self.read_label = _label("Okunan", "group-label")
        group.addWidget(self.read_label)
        self.read_card = _card()
        card = QVBoxLayout(self.read_card)
        card.setContentsMargins(0, m.size("s1"), 0, m.size("s1"))
        card.setSpacing(0)
        self.read_value = QLabel()
        self.read_value.setProperty("kind", "inspector-value")
        self.read_value.setWordWrap(True)
        self.read_value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.read_value.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.level = LevelWidget()
        self.read_note = QLabel()
        self.read_note.setProperty("kind", "inspector-key")
        self.read_note.setWordWrap(True)
        self.value_row = KvRow("Değer", self.read_value)
        self.level_row = KvRow("Güven", self.level)
        self.note_row = KvRow("Not", self.read_note)
        for row in (self.value_row, self.level_row, self.note_row):
            card.addWidget(row)
        group.addWidget(self.read_card)
        return group

    def _pattern_group(self) -> QVBoxLayout:
        """The template's file-name pattern: A shows it in Dışa Aktar per job, the template's own
        default still has to be set somewhere (a card under the read, in the free space)."""
        m = theme.manager()
        group = QVBoxLayout()
        group.setSpacing(0)
        self.pattern_label = _label("Dosya adı", "group-label")
        group.addWidget(self.pattern_label)
        self.pattern_card = _card()
        card = QVBoxLayout(self.pattern_card)
        card.setContentsMargins(*(m.size("s4"),) * 4)
        card.setSpacing(m.size("s1"))
        row = QHBoxLayout()
        row.setSpacing(m.size("s2"))
        self.pattern = QLineEdit()
        self.pattern.setPlaceholderText("{Değişken}_{Değişken}")
        self.pattern.setAccessibleName("Dosya adı kalıbı")
        self.pattern.setToolTip("Dışa aktarılan her belgenin adı. Değişkenleri {Ad} ile yazın.")
        self.pattern_label.setBuddy(self.pattern)
        suffix = QLabel(".pdf")
        suffix.setProperty("textRole", "secondary")
        row.addWidget(self.pattern, 1)
        row.addWidget(suffix)
        card.addLayout(row)
        self.pattern_error = QLabel()
        self.pattern_error.setWordWrap(True)
        self.pattern_error.setProperty("state", "bad")
        self.pattern_error.setAccessibleName("Dosya adı kalıbı hatası")
        self.pattern_error.hide()
        card.addWidget(self.pattern_error)
        group.addWidget(self.pattern_card)
        self.pattern.editingFinished.connect(self.pattern_edited)
        self.pattern.textEdited.connect(lambda _t: self.set_pattern_error(""))
        return group

    def set_pattern_error(self, text: str) -> None:
        """The message at the field (what is wrong and how to mend it); gone at the next key."""
        self.pattern_error.setText(text)
        self.pattern_error.setVisible(bool(text))
        self.pattern.setProperty("invalid", bool(text))

    def _restyle(self) -> None:
        m = theme.manager()
        self.title.setFont(m.font("page"))
        self.read_value.setFont(m.font("value"))
        self.more.setIcon(make_icon("ellipsis", "icon", m.size("icon-sm")))
        self.more.setStyleSheet("QToolButton::menu-indicator { image: none; width: 0; } "
                                + small_button_style(m.title_band().control_height))
        self.save.setIcon(make_icon("save", "text-on-accent", m.size("icon-sm")))
        self.save.setMinimumHeight(m.size("lg-h"))
        pad = m.size("s2")
        for spin in (*self.spins, self.page):
            spin.setFont(m.font("num"))
            # A's field has no spin buttons: their sub-controls get no room, the text its own
            # margins (Qt's NoButtons leaves the line edit one pixel wide under the stylesheet)
            kind = type(spin).__mro__[1].__name__
            spin.setStyleSheet(f"{kind}::up-button, {kind}::down-button "
                               "{ width: 0; border: 0; } "
                               f"{kind}::up-arrow, {kind}::down-arrow "
                               "{ image: none; width: 0; height: 0; }")
            spin.lineEdit().setTextMargins(pad, 0, pad, 0)

    # -- visibility (F9) --------------------------------------------------------------------
    def setVisible(self, visible: bool) -> None:  # noqa: N802
        self._wanted = visible
        super().setVisible(visible and self._allowed)

    def isHidden(self) -> bool:  # noqa: N802
        return not self._wanted

    def allow(self, allowed: bool) -> None:
        """Keep the panel away (no template) without losing what F9 chose."""
        self._allowed = allowed
        super().setVisible(self._wanted and allowed)

    # -- showing a state --------------------------------------------------------------------
    def show_state(self, state: InspectorState) -> None:
        self._state = state
        box_mode, has = state.mode == "box", state.mode != "none"
        self.top.setText(state.top)
        self.title.setText(state.title)
        self.sub.setText(state.sub)
        self.sub.setVisible(bool(state.sub))
        fields = (self.name, self.required, self.page, *self.spins)
        for widget in fields:
            widget.blockSignals(True)
        self.name.setText(state.name)
        self.required.setChecked(state.required)
        self.page.setValue(state.page)
        self._set_geometry(state)
        for widget in fields:
            widget.blockSignals(False)
        for widget in (self.page_key, self.page, self.geometry):
            widget.setVisible(box_mode)
        self.hint.setText(state.hint)
        self.hint.setVisible(bool(state.hint))
        for widget in (self.box_label, self.box_card, self.read_label, self.read_card):
            widget.setVisible(has)
        self.read_label.setText(state.read_title)
        self._show_read(state)
        self.more.setEnabled(has)

    def _show_read(self, state: InspectorState) -> None:
        shown = state.shown
        if state.busy:
            self.read_value.setText("Okunuyor…")
            self.level.set("okunmadi", None)
            self.note_row.setVisible(False)
            return
        if shown is None:
            self.read_value.setText("—")
            self.level.set("okunmadi", None)
            self.note_row.setVisible(False)
            return
        self.read_value.setText(shown.text or "—")
        self.level.set(shown.level, shown.percent)
        self.read_note.setText(shown.note)
        self.note_row.setVisible(bool(shown.note))
        self.value_row.setAccessibleName(f"Değer: {shown.text or 'okunmadı'}")

    def _set_geometry(self, state: InspectorState) -> None:
        x0, y0, x1, y1 = state.box
        sheet_w, sheet_h = state.sheet
        x, y, w, h = self.spins
        x.setRange(0.0, max(0.0, sheet_w - MIN_BOX_MM))
        y.setRange(0.0, max(0.0, sheet_h - MIN_BOX_MM))
        w.setRange(MIN_BOX_MM, sheet_w)
        h.setRange(MIN_BOX_MM, sheet_h)
        for spin, value in zip(self.spins, (x0, y0, x1 - x0, y1 - y0), strict=True):
            spin.setValue(round(value, 2))

    def set_box(self, box: tuple[float, float, float, float]) -> None:
        """The box moved on the canvas: refresh the four fields without reporting an edit."""
        self._state.box = box
        for spin in self.spins:
            spin.blockSignals(True)
        self._set_geometry(self._state)
        for spin in self.spins:
            spin.blockSignals(False)

    # -- edits ------------------------------------------------------------------------------
    def _name_done(self) -> None:
        text = self.name.text().strip()
        if text != self._state.name:
            self.name_edited.emit(text)

    def _geometry_edited(self, _value: float) -> None:
        x, y, w, h = (spin.value() for spin in self.spins)
        self.box_edited.emit((round(x, 2), round(y, 2), round(x + w, 2), round(y + h, 2)))
