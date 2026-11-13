"""Pieces of the Dışa Aktar screen (final-a/disa-aktar.html): the button that paints its key
hint, the card head, one row of "Ön kontrol", the hint line under a field, the empty state."""

from __future__ import annotations

import html
from collections.abc import Callable

from PySide6.QtCore import QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFontMetrics, QIcon, QPainter
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

from evrakci.ui import disa_aktar_icons, icons, theme
from evrakci.ui.chrome import make_icon
from evrakci.ui.disa_aktar_model import Finding

assert disa_aktar_icons
# word, icon, colour role, strong (A .st)
LEVEL_LOOK = {
    "engel": ("Engel", "ban", "danger", True),
    "kontrol": ("Kontrol", "triangle-alert", "check-text", True),
    "eksik": ("Eksik", "circle-dashed", "text-2", False),
    "bilgi": ("Bilgi", "info", "text-2", False),
    "tamam": ("Tamam", "circle-check", "ok", False),
}


def scale() -> float:
    """The type scale against A's 15 px body (1.0 at 100 % text)."""
    return theme.manager().size("fs-body") / 15


def tint(label: QLabel, role: str) -> None:
    """Colour a label from a token role, and again after every theme switch."""
    theme.follow(label, lambda: label.setStyleSheet(f"color: {theme.manager().hex(role)};"),
                 "tint")


class PartsButton(QPushButton):
    """A button that paints its own contents: icon, label and a quiet trailing text (A's key
    hint "Ctrl+E" on a primary, the count on "Yalnızca kontrol gerekenler  7"). The style draws
    the box, so hover, pressed, disabled and the focus ring are A's. `text()` is the label."""

    def __init__(self, label: str, icon: str | None = None, trail: str = "",
                 primary: bool = False, large: bool = False, accessible: str = "",
                 chevron: bool = False, parent=None) -> None:
        super().__init__(label, parent)
        self._chevron = chevron
        self._icon = icon
        self._trail = trail
        self._primary = primary
        self._accessible = accessible
        if primary:
            self.setProperty("variant", "primary")
        if large:
            self.setProperty("sizeVariant", "lg")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._height = "lg-h" if large else "control-h"
        self._sync_name()
        theme.follow(self, self._restyle, "parts")

    def _sync_name(self) -> None:
        self.setAccessibleName(self._accessible or (
            f"{self.text()} ({self._trail})" if self._trail else self.text()))

    def set_parts(self, label: str | None = None, trail: str | None = None) -> None:
        if label is not None:
            self.setText(label)
        if trail is not None:
            self._trail = trail
        self._sync_name()
        self.updateGeometry()
        self.update()

    def trail(self) -> str:
        return self._trail

    def _restyle(self) -> None:
        self.setMinimumHeight(theme.manager().size(self._height))
        self.updateGeometry()
        self.update()

    def _fonts(self):
        m = theme.manager()
        return (m.font("body-strong" if self._primary else "body-medium"),
                m.font("caption-num" if not self._primary else "caption"))

    def sizeHint(self) -> QSize:  # noqa: N802
        m = theme.manager()
        label, trail = self._fonts()
        width = 2 * m.size("s3") + QFontMetrics(label).horizontalAdvance(self.text())
        if self._icon:
            width += 16 + m.size("s2")
        if self._chevron:
            width += 16 + m.size("s2")
        if self._trail:
            width += m.size("s1") + QFontMetrics(trail).horizontalAdvance(self._trail)
        return QSize(width, m.size(self._height))

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        return self.sizeHint()

    def paintEvent(self, _event) -> None:  # noqa: N802
        m = theme.manager()
        painter = QStylePainter(self)
        option = QStyleOptionButton()
        self.initStyleOption(option)
        option.text = ""
        option.icon = QIcon()
        painter.drawControl(QStyle.ControlElement.CE_PushButton, option)
        enabled = self.isEnabled()
        if self._primary:
            ink = m.color("text-on-accent" if enabled else "on-accent-disabled")
            icon_hex = ink.name()
            quiet = QColor(ink)
            quiet.setAlphaF(0.8)
        else:
            ink = m.color("text" if enabled else "text-disabled")
            icon_hex = m.hex("icon" if enabled else "icon-disabled")
            quiet = m.color("text-2" if enabled else "text-disabled")
        label, trail = self._fonts()
        gap = m.size("s2")
        total = self.sizeHint().width() - 2 * m.size("s3")
        x = (self.width() - total) / 2
        box = self.rect()
        if self._icon:
            icons.paint(painter, self._icon, QRectF(x, box.center().y() - 8 + 0.5, 16, 16),
                        ink.name() if self._primary else icon_hex)
            x += 16 + gap
        painter.setFont(label)
        painter.setPen(ink)
        advance = QFontMetrics(label).horizontalAdvance(self.text())
        painter.drawText(QRectF(x, 0, advance + 2, self.height()),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())
        if self._chevron:
            icons.paint(painter, "chevron-down",
                        QRectF(x + advance + gap, box.center().y() - 8 + 0.5, 16, 16), icon_hex)
        if self._trail:
            painter.setFont(trail)
            painter.setPen(quiet)
            painter.drawText(QRectF(x + advance + m.size("s1"), 0,
                                    self.width(), self.height()),
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                             self._trail)


class HeadBar(QWidget):
    """A card head (.thead-bar): "<b>Title</b> caption" on the left, widgets on the right."""

    def __init__(self, title: str, caption: str = "", parent=None) -> None:
        super().__init__(parent)
        self._title, self._caption = title, caption
        self.row = QHBoxLayout(self)
        self.label = QLabel()
        self.label.setTextFormat(Qt.TextFormat.RichText)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.row.addWidget(self.label)
        self.row.addStretch(1)
        self.tail = QWidget()
        self.tail_row = QHBoxLayout(self.tail)
        self.tail_row.setContentsMargins(0, 0, 0, 0)
        self.row.addWidget(self.tail)
        theme.follow(self, self._restyle, "headbar")

    def set_text(self, title: str, caption: str = "") -> None:
        self._title, self._caption = title, caption
        self._restyle()

    def add_widget(self, widget: QWidget) -> None:
        self.tail_row.addWidget(widget)

    def _restyle(self) -> None:
        m = theme.manager()
        self.row.setContentsMargins(m.size("s4"), 0, m.size("s3"), 0)
        self.row.setSpacing(m.size("s2"))
        self.setFixedHeight(52 if m.text_scale() < 130 else 64)
        small = f"font-size:{m.size('fs-caption')}px; color:{m.hex('text-2')};"
        self.label.setText(
            f"<span style='font-weight:600'>{html.escape(self._title)}</span>"
            + (f"&nbsp;&nbsp;<span style='{small}'>{html.escape(self._caption)}</span>"
               if self._caption else ""))
        self.setAccessibleName(f"{self._title} {self._caption}".strip())


class HintLine(QWidget):
    """The line under a field: a 14 px icon and a caption (A .hintl), tone info / ok / err."""

    ICONS = {"info": "info", "ok": "circle-check", "err": "ban"}
    ROLES = {"info": "text-2", "ok": "ok", "err": "danger"}

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        self.icon = QLabel()
        self.icon.setFixedSize(14, 14)
        self.text = QLabel()
        self.text.setWordWrap(True)
        self.text.setProperty("textRole", "caption")
        row.addWidget(self.icon, 0, Qt.AlignmentFlag.AlignTop)
        row.addWidget(self.text, 1)
        self._tone = "info"
        self._icon_name: str | None = None
        theme.follow(self, self._restyle, "hint")

    def set(self, text: str, tone: str = "info", icon: str | None = None) -> None:
        self.text.setText(text)
        self._tone, self._icon_name = tone, icon
        self.setAccessibleName(text)
        self._restyle()

    def tone(self) -> str:
        return self._tone

    def _restyle(self) -> None:
        m = theme.manager()
        role = self.ROLES[self._tone]
        icon_role = "icon" if self._tone == "info" else role
        self.icon.setPixmap(icons.pixmap(self._icon_name or self.ICONS[self._tone],
                                         m.hex(icon_role), 14))
        self.text.setStyleSheet(f"color: {m.hex(role)};")
        self.text.setMinimumHeight(m.size("lh-caption"))


class CheckRow(QWidget):
    """One row of "Ön kontrol": status (icon + word), the sentence, a count, one link."""

    clicked = Signal(str)

    def __init__(self, finding: Finding, first: bool, parent=None) -> None:
        super().__init__(parent)
        self.finding = finding
        word, icon, role, strong = LEVEL_LOOK[finding.level]
        self.word, self.icon_name, self.role, self.strong = word, icon, role, strong
        self.grid = QHBoxLayout(self)
        self.status = QWidget()
        status = QHBoxLayout(self.status)
        status.setContentsMargins(0, 0, 0, 0)
        status.setSpacing(6)
        self.icon = QLabel()
        self.icon.setFixedSize(16, 16)
        self.word_label = QLabel(word)
        status.addWidget(self.icon)
        status.addWidget(self.word_label, 1)
        self.text = QLabel()
        self.text.setTextFormat(Qt.TextFormat.RichText)
        self.text.setWordWrap(True)
        self.text.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.count = QLabel(finding.count_text or ("" if finding.count is None
                                                   else str(finding.count)))
        self.count.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.link = QPushButton(finding.link, self)
        self.link.setProperty("variant", "link")
        self.link.setCursor(Qt.CursorShape.PointingHandCursor)
        self.link.setVisible(bool(finding.link))
        self.link.setAccessibleName(f"{finding.link}: {finding.title}" if finding.link else "")
        self.link.setToolTip(finding.link)
        self.link.clicked.connect(lambda: self.clicked.emit(finding.action))
        self.grid.addWidget(self.status)
        self.grid.addWidget(self.text, 1)
        self.grid.addWidget(self.count)
        self.grid.addWidget(self.link)
        self.setAccessibleName(f"{word}: {finding.title} {finding.detail}".strip()
                               + (f", {finding.count}" if finding.count is not None else ""))
        theme.follow(self, self._restyle, "row")

    def _restyle(self) -> None:
        m = theme.manager()
        k = scale()
        self.grid.setContentsMargins(m.size("s4"), m.size("s2") if k > 1.2 else 0,
                                     m.size("s2"), m.size("s2") if k > 1.2 else 0)
        self.grid.setSpacing(m.size("s3"))
        self.setMinimumHeight(m.size("row-h"))
        self.status.setFixedWidth(round(96 * k) if k < 1.4 else 136)
        self.count.setFixedWidth(round(32 * k))
        self.icon.setPixmap(icons.pixmap(self.icon_name, m.hex(self.role), 16))
        font = m.font("body-strong" if self.strong else "body")
        self.word_label.setFont(font)
        self.word_label.setStyleSheet(f"color: {m.hex(self.role)};")
        self.count.setFont(m.font("num-strong"))
        self.link.setMinimumHeight(m.size("control-h"))
        f = self.finding
        detail = (f" <span style='color:{m.hex('text-2')}'>{html.escape(f.detail)}</span>"
                  if f.detail else "")
        title = f"<span style='font-weight:600'>{html.escape(f.title)}</span>" if f.title else ""
        lh = m.size("lh-body")
        self.text.setText(f"<p style='margin:0; line-height:{lh}px'>{title}{detail}</p>")
        self.text.setMinimumHeight(lh)

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(400, max(theme.manager().size("row-h"), self.layout().sizeHint().height()))

    def paintEvent(self, _event) -> None:  # noqa: N802
        m = theme.manager()
        painter = QPainter(self)
        painter.fillRect(0, 0, self.width(), 1, m.color("stroke-soft"))
        if self.finding.level == "engel":
            painter.fillRect(0, 0, 3, self.height(), m.color("danger"))


class PreflightCard(QFrame):
    """"Ön kontrol": the head and one row per finding. `action(name)` says which link was used."""

    action = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setProperty("kind", "table-card")
        self.setAccessibleName("Ön kontrol")
        self.col = QVBoxLayout(self)
        self.col.setContentsMargins(1, 1, 1, 1)
        self.col.setSpacing(0)
        self.head = HeadBar("Ön kontrol")
        self.col.addWidget(self.head)
        self.rows: list[CheckRow] = []
        self._fitting = False

    def fit(self) -> None:
        """Rows that wrap (large text) need their full height: the card never gives it up to
        the list below, which scrolls instead."""
        width = self.width() - 2
        if width <= 0 or self._fitting:
            return
        self._fitting = True
        try:
            row_h = theme.manager().size("row-h")
            need = 2 + self.head.height() + sum(max(row_h, r.heightForWidth(width))
                                                for r in self.rows)
            if need != self.minimumHeight():
                self.setMinimumHeight(need)
        finally:
            self._fitting = False

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.fit()

    def set_findings(self, findings: list[Finding], caption: str) -> None:
        self.head.set_text("Ön kontrol", caption)
        for row in self.rows:
            self.col.removeWidget(row)
            row.hide()  # deleteLater alone leaves it painted until the next event loop turn
            row.setParent(None)
            row.deleteLater()
        self.rows = []
        for number, finding in enumerate(findings):
            row = CheckRow(finding, number == 0)
            row.clicked.connect(self.action)
            self.col.addWidget(row)
            self.rows.append(row)
        QTimer.singleShot(0, self.fit)

    def levels(self) -> list[str]:
        return [r.finding.level for r in self.rows]

    def first_link(self, level: str) -> QPushButton | None:
        return next((r.link for r in self.rows if r.finding.level == level), None)


class EmptyPane(QWidget):
    """A's empty state: a 48 px mark, one heading, one sentence and the primary action."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        m = theme.manager()
        col = QVBoxLayout(self)
        col.setContentsMargins(m.size("s6"), 0, m.size("s6"), m.size("s8"))
        col.setSpacing(0)
        col.addStretch(1)
        self.mark = QLabel()
        self.mark.setFixedSize(48, 48)
        self.mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mark.setProperty("kind", "card")
        col.addWidget(self.mark, 0, Qt.AlignmentFlag.AlignHCenter)
        col.addSpacing(m.size("s4"))
        self.title = QLabel("Dışa aktarılacak belge yok")
        self.title.setProperty("textRole", "panel")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text = QLabel("Önce Yükle'den bir iş açın; belgeler burada listelenir.")
        self.text.setProperty("textRole", "secondary")
        self.text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text.setWordWrap(True)
        col.addWidget(self.title)
        col.addSpacing(m.size("s1"))
        col.addWidget(self.text)
        col.addSpacing(m.size("s6"))
        self.go = PartsButton("Yükle'ye git", "upload", "Ctrl+1", primary=True, large=True)
        col.addWidget(self.go, 0, Qt.AlignmentFlag.AlignHCenter)
        col.addStretch(1)
        self.setAccessibleName("Dışa aktarılacak belge yok")
        theme.follow(self, lambda: self.mark.setPixmap(
            make_icon("file-output", size=24).pixmap(24, 24)), "mark")


def connect_once(signal, slot: Callable) -> None:
    """Connect a signal without doubling an earlier connection."""
    try:
        signal.disconnect(slot)
    except (RuntimeError, TypeError):
        pass
    signal.connect(slot)
