"""Shared Kartotek widgets: key-hint buttons, headings on the index rule, riders, state text.

Everything here takes its colours from `theme.TOKENS` (see DESIGN.md, Components).
"""

from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QIcon, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStyle,
    QStyleOptionButton,
    QStylePainter,
    QVBoxLayout,
    QWidget,
)

from evrakci.ui import icons, theme

ICON = 18
PAD = 9
GAP = 7
KEY_GAP = 12


def _font(size: int, weight: QFont.Weight) -> QFont:
    font = QFont(theme.FONT_FAMILY)
    font.setPixelSize(size)
    font.setWeight(weight)
    return font


class KeyHintButton(QPushButton):
    """A button that paints its icon, label and key-cap hint itself (DESIGN.md: Buttons).

    `text()` stays the plain label, so screen readers and tests see the words only.
    """

    def __init__(self, text: str, key: str = "", icon: str | None = None,
                 primary: bool = False, icon_only: bool = False, parent=None) -> None:
        super().__init__(text, parent)
        self.key = key
        self.icon_name = icon
        self.icon_only = icon_only and icon is not None
        if primary:
            self.setProperty("primary", True)
        if self.icon_only:
            self.setToolTip(f"{text} ({key})" if key else text)
        elif key:
            self.setToolTip(f"{text} ({key})")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    # Size
    def _label_font(self) -> QFont:
        return _font(theme.FONT_SIZE, QFont.Weight.DemiBold)

    def _key_font(self) -> QFont:
        return _font(theme.SMALL, QFont.Weight.DemiBold)

    def _key_size(self) -> QSize:
        if not self.key:
            return QSize(0, 0)
        metrics = QFontMetrics(self._key_font())
        return QSize(metrics.horizontalAdvance(self.key) + 10, 21)

    def sizeHint(self) -> QSize:
        height = 34
        if self.icon_only:
            key = self._key_size()
            width = 34 if not self.key else PAD + ICON + 8 + key.width() + 7
            return QSize(width, height)
        width = PAD * 2 + QFontMetrics(self._label_font()).horizontalAdvance(self.text())
        if self.icon_name:
            width += ICON + GAP
        if self.key:
            width += KEY_GAP + self._key_size().width()
        return QSize(width + 2, height)

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    # Paint
    def _colours(self) -> tuple[str, str, str, str]:
        """(text, key fill, key edge, key text) for the current state."""
        t = theme.TOKENS
        primary = bool(self.property("primary"))
        if not self.isEnabled():
            if primary:
                return t["on_shell"], t["shell_3"], t["key_edge_on_shell"], t["on_shell"]
            return t["disabled_ink"], t["layer"], t["rule"], t["disabled_ink"]
        if primary:
            return t["on_shell"], t["shell_3"], t["key_edge_on_shell"], t["on_shell"]
        return t["ink"], t["key_cap"], t["key_edge"], t["ink_2"]

    def paintEvent(self, event) -> None:
        painter = QStylePainter(self)
        option = QStyleOptionButton()
        self.initStyleOption(option)
        option.text = ""
        option.icon = QIcon()
        painter.drawControl(QStyle.ControlElement.CE_PushButton, option)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        text_colour, cap_fill, cap_edge, cap_text = self._colours()
        rect = self.rect()
        mid = rect.height() / 2
        x = PAD
        if self.icon_only and not self.key:
            x = (rect.width() - ICON) / 2
        if self.icon_name:
            icons.paint(painter, self.icon_name, QRectF(x, mid - ICON / 2, ICON, ICON),
                        text_colour)
            x += ICON + (8 if self.icon_only else GAP)
        key = self._key_size()
        right = rect.width() - PAD + (2 if self.key else 0)
        if not self.icon_only:
            painter.setFont(self._label_font())
            painter.setPen(QColor(text_colour))
            label = self._label_rect()
            painter.drawText(label, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                             self.displayed_text())
        if self.key:
            cap = QRectF(right - key.width(), mid - key.height() / 2, key.width(), key.height())
            self._paint_key(painter, cap, cap_fill, cap_edge, cap_text)

    def _label_rect(self) -> QRectF:
        rect = self.rect()
        x = PAD + (ICON + GAP if self.icon_name else 0)
        right = rect.width() - PAD + (2 if self.key else 0)
        label_right = right - (self._key_size().width() + KEY_GAP if self.key else 0)
        return QRectF(x, 0, max(0.0, label_right - x), rect.height())

    def displayed_text(self) -> str:
        """The label as painted (elided with "…" when the button is too narrow)."""
        if self.icon_only:
            return ""
        return QFontMetrics(self._label_font()).elidedText(
            self.text(), Qt.TextElideMode.ElideRight, int(self._label_rect().width()))

    def is_elided(self) -> bool:
        return not self.icon_only and self.displayed_text() != self.text()

    def _paint_key(self, painter: QPainter, cap: QRectF, fill: str, edge: str,
                   text: str) -> None:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(edge))
        painter.drawRoundedRect(cap, 4, 4)  # the 2px lower lip shows under the face
        painter.setBrush(QColor(fill))
        painter.drawRoundedRect(cap.adjusted(1, 1, -1, -2), 3, 3)
        painter.setFont(self._key_font())
        painter.setPen(QColor(text))
        painter.drawText(cap.adjusted(0, 0, 0, -1), Qt.AlignmentFlag.AlignCenter, self.key)


def key_button(text: str, key: str = "", primary: bool = False, icon: str | None = None,
               icon_only: bool = False) -> KeyHintButton:
    return KeyHintButton(text, key, icon=icon, primary=primary, icon_only=icon_only)


def index_rule() -> QFrame:
    """The 1px index-red rule under a heading."""
    rule = QFrame()
    rule.setProperty("role", "index-rule")
    rule.setFixedHeight(1)
    return rule


def rule(vertical: bool = False) -> QFrame:
    """A grey 1px rule between groups (vertical: the 28px toolbar separator)."""
    line = QFrame()
    line.setProperty("role", "vrule" if vertical else "hrule")
    if vertical:
        line.setFixedSize(1, 28)
    else:
        line.setFixedHeight(1)
    return line


def label(text: str = "", role: str | None = None, wrap: bool = False) -> QLabel:
    widget = QLabel(text)
    if role:
        widget.setProperty("role", role)
    widget.setWordWrap(wrap)
    return widget


class Heading(QWidget):
    """A heading with an optional muted subtitle on the same line, widgets at the right,
    and the 1px index-red rule under it (DESIGN.md: Headings with the index rule).

    level: "page" (24px), "panel" (20px) or "section" (17px).
    """

    def __init__(self, title: str, subtitle: str = "", level: str = "page",
                 widgets: tuple = (), parent=None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6 if level == "section" else 8)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(14)
        self.title = label(title, f"{level}-title")
        self.subtitle = label(subtitle, "muted")
        self.subtitle.setVisible(bool(subtitle))
        row.addWidget(self.title, 0, Qt.AlignmentFlag.AlignBaseline)
        row.addWidget(self.subtitle, 0, Qt.AlignmentFlag.AlignBaseline)
        row.addStretch(1)
        for widget in widgets:
            row.addWidget(widget, 0, Qt.AlignmentFlag.AlignVCenter)
        outer.addLayout(row)
        outer.addWidget(index_rule())

    def setText(self, title: str, subtitle: str | None = None) -> None:
        self.title.setText(title)
        if subtitle is not None:
            self.subtitle.setText(subtitle)
            self.subtitle.setVisible(bool(subtitle))

    def text(self) -> str:
        return self.title.text()


class PanelHeading(QWidget):
    """A side-panel title (20px), then its meta line on the index rule."""

    def __init__(self, title: str = "", meta: str = "", parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.title = label(title, "panel-title", wrap=True)
        self.meta = label(meta, "meta", wrap=True)
        layout.addWidget(self.title)
        layout.addWidget(self.meta)
        layout.addSpacing(6)
        layout.addWidget(index_rule())

    def set(self, title: str, meta: str = "") -> None:
        self.title.setText(title)
        self.meta.setText(meta)


class Rider(QWidget):
    """The orange signal rider: warn pictogram + "Kontrol" (only ever for needs-a-check)."""

    def __init__(self, text: str = "Kontrol", parent=None) -> None:
        super().__init__(parent)
        self._text = text
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def setText(self, text: str) -> None:
        self._text = text
        self.updateGeometry()
        self.update()

    def text(self) -> str:
        return self._text

    def sizeHint(self) -> QSize:
        width = QFontMetrics(_font(theme.SMALL, QFont.Weight.Bold)).horizontalAdvance(self._text)
        return QSize(5 + 14 + 4 + width + 8, 21)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        paint_rider(painter, QRectF(self.rect()), self._text)


def paint_rider(painter: QPainter, rect: QRectF, text: str) -> None:
    """Paint a rider into `rect` (also used by the timeline and table delegates)."""
    t = theme.TOKENS
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    body = rect.adjusted(0.5, 0.5, -0.5, -0.5)
    path = QPainterPath()
    path.addRoundedRect(body, 3, 3)
    painter.fillPath(path, QColor(t["rider"]))
    lip = QColor(0, 0, 0, 36)
    painter.save()
    painter.setClipPath(path)
    painter.fillRect(QRectF(body.left(), body.bottom() - 3, body.width(), 3), lip)
    painter.restore()
    painter.setPen(QPen(QColor(t["rider_edge"]), 1))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawPath(path)
    icons.paint(painter, "warn", QRectF(rect.left() + 5, rect.center().y() - 7.5, 14, 14),
                "rider_ink", 2)
    painter.setFont(_font(theme.SMALL, QFont.Weight.Bold))
    painter.setPen(QColor(t["rider_ink"]))
    painter.drawText(rect.adjusted(23, 0, -4, -1),
                     Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)
    painter.restore()


STATES = {
    # state: (icon, token, word)
    "ok": ("ok", "ok", "Tamam"),
    "check": ("warn", "check_ink", "Kontrol"),
    "none": ("no", "ink_2", "Okunmadı"),
}


class StateLabel(QWidget):
    """Icon + word state text: Tamam (ok), Kontrol (check), Okunmadı (none)."""

    def __init__(self, state: str = "none", text: str | None = None, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.icon = QLabel()
        self.word = QLabel()
        layout.addWidget(self.icon)
        layout.addWidget(self.word)
        layout.addStretch(1)
        self.set(state, text)

    def set(self, state: str, text: str | None = None) -> None:
        name, token, word = STATES[state]
        self.word.setText(text or word)

        def paint() -> None:  # again after a theme switch
            self.icon.setPixmap(icons.pixmap(name, token, 18))
            self.word.setStyleSheet(
                f"color: {theme.TOKENS[token]}; font-weight: 600; font-size: 14px;")

        theme.follow(self, paint, "state")


def icon_label(name: str, colour: str = "ink", size: int = 18) -> QLabel:
    widget = QLabel()
    widget.setPixmap(icons.pixmap(name, colour, size))
    widget.setFixedSize(size, size)
    return widget


class Toolbar(QFrame):
    """The 52px card band under the window tabs (rule along its bottom edge)."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setProperty("role", "toolbar")
        self.setFixedHeight(52)
        self.row = QHBoxLayout(self)
        self.row.setContentsMargins(16, 0, 16, 0)
        self.row.setSpacing(6)

    def add(self, *widgets) -> None:
        for widget in widgets:
            if widget is None:
                self.row.addWidget(rule(vertical=True))
            elif widget == "stretch":
                self.row.addStretch(1)
            else:
                self.row.addWidget(widget)


class KeyValue(QWidget):
    """A two-column list of muted terms and 600-weight values (dl.kv in the mockups)."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        from PySide6.QtWidgets import QGridLayout

        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 4, 0, 4)
        self.grid.setHorizontalSpacing(14)
        self.grid.setVerticalSpacing(4)
        self.grid.setColumnStretch(2, 1)
        self._rows: list[tuple[QLabel, QLabel, QLabel]] = []

    def set_rows(self, rows: list[tuple]) -> None:
        """rows: (term, value) or (icon, icon_colour, term, value)."""
        for widgets in self._rows:
            for widget in widgets:
                widget.deleteLater()
        self._rows = []
        for number, row in enumerate(rows):
            if len(row) == 4:
                name, colour, term, value = row
                pic = icon_label(name, colour)
            else:
                term, value = row
                pic = QLabel()
            term_label = label(term, "muted")
            value_label = label(value, "value", wrap=True)
            self.grid.addWidget(pic, number, 0)
            self.grid.addWidget(term_label, number, 1)
            self.grid.addWidget(value_label, number, 2)
            self._rows.append((pic, term_label, value_label))
