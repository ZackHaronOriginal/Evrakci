"""Kontrol's inspector (A .inspector): Settings-style cards about the current document.

Head: the rider when the document needs a check, "Belge 16" (the one page-size title), its
template and pages, and one sentence on why it needs a look (or why it starts here). Then
"Neden burada başlıyor" (Kesim, Önceki, Durum), the selection's actions as rows with their
value and a chevron, "Son değişiklikler", and at the bottom one primary "Belgeyi onayla" and
"Değerlerde aç". The cards scroll above the pinned buttons when the text is large.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPalette
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStyle,
    QStyleOptionButton,
    QStylePainter,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from evrakci.ui import icons, theme
from evrakci.ui.card_scroll import CardScroll
from evrakci.ui.chrome import make_icon
from evrakci.ui.kontrol_paint import RiderLabel

KEY_W = 76  # A .kv .r .k width


@dataclass
class DocumentInfo:
    number: int
    template: str  # "Ekspertiz Raporu" or "Şablon yok"
    first: int  # page positions (1-based)
    last: int
    pages: int
    reason: str  # one sentence
    cut_icon: str | None  # Lucide name of the cut pictogram
    cut_role: str  # its colour role
    cut_text: str  # "Filtre, her 2 sayfada"
    previous: str  # "Belge 15, 1 sayfa" / "Yok"
    check: bool
    reviewed: bool


@dataclass
class SelectionInfo:
    count: int
    first: int
    last: int
    template: str  # the template "Şablon uygula" will apply ("" when none exists)
    every_n: int


@dataclass
class Change:
    icon: str
    text: str
    time: str


@dataclass
class _IconSpec:
    label: QLabel
    name: str
    role: str
    size: int = 16
    extra: dict = field(default_factory=dict)


def _group_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setProperty("kind", "group-label")
    return label


def _card() -> QFrame:
    card = QFrame()
    card.setProperty("kind", "card")
    return card


class _KvRow(QWidget):
    """A .kv .r: a 76 px caption key and a value with an optional icon; 40 px high."""

    def __init__(self, key: str) -> None:
        super().__init__()
        m = theme.manager()
        self.setMinimumHeight(m.size("row-h"))
        row = QHBoxLayout(self)
        row.setContentsMargins(m.size("s4"), 0, m.size("s4"), 0)
        row.setSpacing(m.size("s3"))
        self.key = QLabel(key)
        self.key.setProperty("kind", "inspector-key")
        self.key.setFixedWidth(KEY_W)
        self.icon = QLabel()
        self.icon.setFixedSize(16, 16)
        self.value = QLabel()
        self.value.setProperty("kind", "inspector-value")
        self.value.setWordWrap(True)
        self.value.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        value = QHBoxLayout()
        value.setSpacing(m.size("s2"))
        value.addWidget(self.icon, 0, Qt.AlignmentFlag.AlignVCenter)
        value.addWidget(self.value, 1)
        row.addWidget(self.key, 0, Qt.AlignmentFlag.AlignVCenter)
        row.addLayout(value, 1)
        self._icon: tuple[str, str] | None = None

    def set(self, text: str, icon: str | None = None, role: str = "icon",
            state: str | None = None) -> None:
        self.value.setText(text)
        self.value.setProperty("textRole", "secondary" if state == "orta" else None)
        self.value.setProperty("state", state if state == "ok" else None)
        self.value.style().unpolish(self.value)
        self.value.style().polish(self.value)
        self._icon = (icon, role) if icon else None
        self.icon.setVisible(bool(icon))
        self.refresh()
        self.setAccessibleName(f"{self.key.text()}: {text}")

    def refresh(self) -> None:
        if self._icon is not None:
            name, role = self._icon
            self.icon.setPixmap(icons.pixmap(name, theme.manager().hex(role), 16))


class ActionRow(QPushButton):
    """A .act .r: a Settings-style action row, label left, value + chevron right."""

    def __init__(self, text: str) -> None:
        super().__init__()
        m = theme.manager()
        self.setProperty("kind", "inspector-row")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumHeight(m.size("row-h"))
        row = QHBoxLayout(self)
        row.setContentsMargins(m.size("s3"), 0, m.size("s3"), 0)
        row.setSpacing(m.size("s3"))
        self.label = QLabel(text)
        self.value = QLabel()
        self.value.setProperty("textRole", "secondary")
        self.value.setProperty("kind", "row-value")
        self.chevron = QLabel()
        self.chevron.setFixedSize(16, 16)
        for widget in (self.label, self.value, self.chevron):
            widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        row.addWidget(self.label)
        row.addStretch(1)
        value = QHBoxLayout()
        value.setSpacing(m.size("s1"))
        value.addWidget(self.value)
        value.addWidget(self.chevron)
        row.addLayout(value)
        self.refresh()

    def set_value(self, text: str) -> None:
        self.value.setText(text)
        self.setAccessibleName(f"{self.label.text()}: {text}" if text else self.label.text())
        self.setToolTip(self.accessibleName())

    def refresh(self) -> None:
        m = theme.manager()
        self.value.setStyleSheet(f"font-size: {m.size('fs-caption')}px;")
        self.chevron.setPixmap(icons.pixmap("chevron-right", m.hex("text-2"), 16))

    def sizeHint(self) -> QSize:  # noqa: N802
        hint = self.layout().sizeHint()
        return QSize(hint.width(), max(hint.height(), theme.manager().size("row-h")))


class _HistRow(QWidget):
    """A .hist .r: icon, what changed, when; 36 px, caption type."""

    def __init__(self) -> None:
        super().__init__()
        m = theme.manager()
        self.setMinimumHeight(36)
        row = QHBoxLayout(self)
        row.setContentsMargins(m.size("s4"), 0, m.size("s4"), 0)
        row.setSpacing(m.size("s3"))
        self.icon = QLabel()
        self.icon.setFixedSize(16, 16)
        self.text = QLabel()
        self.time = QLabel()
        self.time.setProperty("textRole", "secondary")
        for label in (self.text, self.time):
            label.setProperty("textRole", "caption" if label is self.text else "secondary")
        row.addWidget(self.icon)
        row.addWidget(self.text, 1)
        row.addWidget(self.time)
        self._name = "clock"

    def set(self, change: Change) -> None:
        self._name = change.icon
        self.text.setText(change.text)
        self.time.setText(change.time)
        self.setAccessibleName(f"{change.text}, {change.time}")
        self.refresh()

    def refresh(self) -> None:
        m = theme.manager()
        self.icon.setPixmap(icons.pixmap(self._name, m.hex("icon"), 16))
        self.time.setStyleSheet(f"font-size: {m.size('fs-caption')}px;")


class GapButton(QPushButton):
    """A .btn: icon and label centred with A's s2 (8 px) gap, which QPushButton cannot give;
    the style still draws the box (fill, hover, focus) from the stylesheet."""

    def sizeHint(self) -> QSize:  # noqa: N802
        hint = super().sizeHint()
        return QSize(hint.width() + theme.manager().size("s1"), hint.height())

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QStylePainter(self)
        option = QStyleOptionButton()
        self.initStyleOption(option)
        text, icon = self.text(), self.icon()
        option.text, option.icon = "", QIcon()
        painter.drawControl(QStyle.ControlElement.CE_PushButton, option)
        gap = theme.manager().size("s2")
        size = self.iconSize()
        width = size.width() + gap + self.fontMetrics().horizontalAdvance(text)
        x = (self.width() - width) // 2
        mode = QIcon.Mode.Normal if self.isEnabled() else QIcon.Mode.Disabled
        icon.paint(painter, QRect(x, (self.height() - size.height()) // 2, size.width(),
                                  size.height()), Qt.AlignmentFlag.AlignCenter, mode)
        group = QPalette.ColorGroup.Active if self.isEnabled() else QPalette.ColorGroup.Disabled
        painter.setPen(self.palette().color(group, QPalette.ColorRole.ButtonText))
        painter.drawText(QRect(x + size.width() + gap, 0, self.width(), self.height()),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)


class Inspector(QWidget):
    """The side panel (F9 hides it). Buttons emit signals; the screen does the work."""

    approve = Signal()
    open_values = Signal()
    template_row = Signal()
    filter_row = Signal()
    HISTORY = 3

    def __init__(self, fill_more: Callable[[QMenu], None] | None = None,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("kontrolInspector")
        self.setAccessibleName("Belge ayrıntısı")
        m = theme.manager()
        self.document = 0
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, m.size("s3"), m.size("s4"), m.size("s3"))
        outer.setSpacing(m.size("s3"))

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        body = QWidget()
        column = QVBoxLayout(body)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(m.size("s3"))
        self.scroll.setWidget(body)

        # head
        head = QWidget()
        head_col = QVBoxLayout(head)
        head_col.setContentsMargins(m.size("s1"), m.size("s1"), m.size("s1"), 0)
        head_col.setSpacing(0)
        top = QHBoxLayout()
        top.setSpacing(m.size("s2"))
        self.rider = RiderLabel()
        top.addWidget(self.rider)
        top.addStretch(1)
        self.more = QToolButton()
        self.more.setProperty("kind", "icon")
        self.more.setProperty("sizeVariant", "sm")
        self.more.setAutoRaise(True)
        self.more.setToolTip("Diğer")
        self.more.setAccessibleName("Diğer belge komutları")
        self.more.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.more.setStyleSheet("QToolButton::menu-indicator { image: none; width: 0; }")
        menu = QMenu(self.more)
        if fill_more is not None:
            menu.aboutToShow.connect(lambda: (menu.clear(), fill_more(menu)))
        self.more.setMenu(menu)
        top.addWidget(self.more)
        head_col.addLayout(top)
        self.title = QLabel("Belge seçilmedi")
        self.title.setProperty("textRole", "page")
        self.title.setContentsMargins(0, m.size("s1"), 0, 0)
        self.sub = QLabel("")
        self.sub.setProperty("textRole", "secondary")
        self.sub.setContentsMargins(0, 2, 0, 0)
        self.reason = QLabel("")
        self.reason.setWordWrap(True)
        self.reason.setContentsMargins(0, m.size("s3"), 0, 0)
        for widget in (self.title, self.sub, self.reason):
            head_col.addWidget(widget)
        column.addWidget(head)

        # Neden burada başlıyor
        self.why_group = QWidget()
        why_col = QVBoxLayout(self.why_group)
        why_col.setContentsMargins(0, 0, 0, 0)
        why_col.setSpacing(0)
        why_col.addWidget(_group_label("Neden burada başlıyor"))
        card = _card()
        card_col = QVBoxLayout(card)
        card_col.setContentsMargins(0, m.size("s1"), 0, m.size("s1"))
        card_col.setSpacing(0)
        self.cut_row, self.previous_row, self.state_row = (
            _KvRow("Kesim"), _KvRow("Önceki"), _KvRow("Durum"))
        for row in (self.cut_row, self.previous_row, self.state_row):
            card_col.addWidget(row)
        why_col.addWidget(card)
        column.addWidget(self.why_group)

        # Seçim
        self.selection_group = QWidget()
        sel_col = QVBoxLayout(self.selection_group)
        sel_col.setContentsMargins(0, 0, 0, 0)
        sel_col.setSpacing(0)
        self.selection_label = _group_label("Seçim")
        sel_col.addWidget(self.selection_label)
        card = _card()
        card_col = QVBoxLayout(card)
        pad = m.size("s1")
        card_col.setContentsMargins(pad, pad, pad, pad)
        card_col.setSpacing(0)
        self.template_button = ActionRow("Şablon uygula")
        self.filter_button = ActionRow("Filtre uygula")
        self.template_button.clicked.connect(self.template_row)
        self.filter_button.clicked.connect(self.filter_row)
        card_col.addWidget(self.template_button)
        card_col.addWidget(self.filter_button)
        sel_col.addWidget(card)
        column.addWidget(self.selection_group)

        # Son değişiklikler
        self.history_group = QWidget()
        hist_col = QVBoxLayout(self.history_group)
        hist_col.setContentsMargins(0, 0, 0, 0)
        hist_col.setSpacing(0)
        hist_col.addWidget(_group_label("Son değişiklikler"))
        card = _card()
        card_col = QVBoxLayout(card)
        card_col.setContentsMargins(0, m.size("s1"), 0, m.size("s1"))
        card_col.setSpacing(0)
        self.history_rows = [_HistRow() for _ in range(self.HISTORY)]
        for row in self.history_rows:
            card_col.addWidget(row)
        hist_col.addWidget(card)
        column.addWidget(self.history_group)
        column.addStretch(1)
        outer.addWidget(self.scroll, 1)

        # pinned actions
        foot = QVBoxLayout()
        foot.setSpacing(m.size("s1"))
        self.approve_button = GapButton("Belgeyi onayla")
        self.approve_button.setProperty("variant", "primary")
        self.approve_button.setProperty("sizeVariant", "lg")
        self.approve_button.clicked.connect(self.approve)
        self.values_button = GapButton("Değerlerde aç")
        self.values_button.setProperty("variant", "subtle")
        self.values_button.clicked.connect(self.open_values)
        foot.addWidget(self.approve_button)
        foot.addWidget(self.values_button)
        outer.addLayout(foot)
        self.card_scroll = CardScroll(self.scroll, self.approve_button)
        self.set_history([])
        self.show_nothing()
        theme.follow(self, self.refresh)
        self.refresh()

    # -- content ------------------------------------------------------------------------------
    def show_nothing(self) -> None:
        self.document = 0
        self.rider.hide()
        self.title.setText("Belge seçilmedi")
        self.sub.setText("Bir sayfaya tıklayın ya da oklarla gezinin.")
        self.reason.setText("")
        self.reason.hide()
        self.why_group.hide()
        self.approve_button.setEnabled(False)
        self.values_button.setEnabled(False)
        self.approve_button.setAccessibleName("Belgeyi onayla (Enter)")

    def show_document(self, info: DocumentInfo) -> None:
        self.document = info.number
        self.rider.setVisible(info.check)
        self.title.setText(f"Belge {info.number}")
        pages = (f"sayfa {info.first}" if info.first == info.last
                 else f"sayfa {info.first}–{info.last}")
        self.sub.setText(f"{info.template}, {pages}")
        self.reason.setText(info.reason)
        self.reason.setVisible(bool(info.reason))
        self.why_group.show()
        self.cut_row.set(info.cut_text, info.cut_icon, info.cut_role)
        self.previous_row.set(info.previous)
        if info.reviewed:
            self.state_row.set("İncelendi", "circle-check", "ok", "ok")
        else:
            self.state_row.set("İncelenmedi", "circle-dashed", "text-2", "orta")
        self.approve_button.setEnabled(True)
        self.values_button.setEnabled(True)
        self.approve_button.setAccessibleName(f"Belge {info.number} onayla (Enter)")
        self.values_button.setAccessibleName(f"Belge {info.number} Değerlerde aç")
        self.setAccessibleDescription(
            f"Belge {info.number}, {self.sub.text()}. "
            + ("Kontrol gerekiyor. " if info.check else "")
            + ("İncelendi." if info.reviewed else "İncelenmedi."))

    def show_selection(self, info: SelectionInfo | None) -> None:
        if info is None or info.count == 0:
            self.selection_group.hide()
            return
        span = (f"sayfa {info.first}" if info.first == info.last
                else f"{info.first}–{info.last}")
        self.selection_label.setText(f"Seçim: {info.count} sayfa ({span})")
        self.template_button.set_value(info.template or "Şablon yok")
        self.filter_button.set_value(f"Her {info.every_n} sayfa")
        self.selection_group.show()

    def set_history(self, changes: list[Change]) -> None:
        shown = changes[: self.HISTORY]
        for row, change in zip(self.history_rows, shown, strict=False):
            row.set(change)
            row.show()
        for row in self.history_rows[len(shown):]:
            row.hide()
        self.history_group.setVisible(bool(shown))

    def refresh(self) -> None:
        m = theme.manager()
        self.more.setIcon(make_icon("ellipsis"))
        self.approve_button.setIcon(make_icon("check", "text-on-accent"))
        self.values_button.setIcon(make_icon("table", "icon"))
        for row in (self.cut_row, self.previous_row, self.state_row):
            row.refresh()
        for row in self.history_rows:
            row.refresh()
        for button in (self.template_button, self.filter_button):
            button.refresh()
        self.setMinimumWidth(m.size("inspector-w") // 2)
