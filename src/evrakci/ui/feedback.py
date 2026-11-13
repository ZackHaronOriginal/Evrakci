"""Passive feedback: toast, persistent info bar and the title band's save state.

The toast follows the one in the approved direction A (Değerler): ``popover`` surface,
1 px stroke, one soft shadow, a check icon, text, a flat accent action and a close
button. It never takes focus, shows one at a time (the rest queue), fades with
``motion`` (instantly under reduced motion) and is announced to screen readers.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from PySide6.QtCore import QEvent, QObject, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QAccessible, QAccessibleEvent, QColor, QKeyEvent, QPainter
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QToolButton,
    QWidget,
)

from evrakci.ui import icons, motion, theme

TOAST_MARGIN = 12
SHADOW_ROOM = 16
KIND_ICON = {"info": "info", "success": "circle-check", "kontrol": "triangle-alert"}
KIND_COLOUR = {"info": "icon", "success": "ok", "kontrol": "check-text"}


def announce(widget: QWidget, text: str) -> None:
    """Name the widget and raise an alert event; never moves focus."""
    widget.setAccessibleName(text)
    if QAccessible.isActive():
        QAccessible.updateAccessibility(QAccessibleEvent(widget, QAccessible.Event.Alert))


def _icon_label(name: str, role: str, size: int) -> QLabel:
    label = QLabel()
    label.setFixedSize(size, size)
    label.setPixmap(icons.pixmap(name, theme.manager().hex(role), size))
    label.setAccessibleName("")
    return label


def _close_button(callback: Callable[[], None], tip: str) -> QToolButton:
    m = theme.manager()
    button = QToolButton()
    button.setProperty("kind", "icon")
    button.setProperty("size", "sm")
    button.setIcon(icons.icon("x", m.hex("icon")))
    button.setToolTip(tip)
    button.setAccessibleName(tip)
    button.setAutoRaise(True)
    button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
    button.clicked.connect(callback)
    return button


def _link_button(text: str, callback: Callable[[], None]) -> QPushButton:
    button = QPushButton(text)
    button.setProperty("variant", "link")
    button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
    button.clicked.connect(callback)
    return button


class _Toast(QWidget):
    """Transparent shell (room for the shadow) around the styled toast frame."""

    closed = Signal()

    def __init__(self, parent: QWidget, text: str, action_text: str | None,
                 on_action: Callable[[], None] | None, kind: str) -> None:
        super().__init__(parent)
        m = theme.manager()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(SHADOW_ROOM, SHADOW_ROOM, SHADOW_ROOM, SHADOW_ROOM)
        self.frame = QFrame()
        self.frame.setProperty("kind", "toast")
        outer.addWidget(self.frame)
        row = QHBoxLayout(self.frame)
        row.setContentsMargins(m.size("s4"), 0, m.size("s2"), 0)
        row.setSpacing(m.size("s3"))
        name = KIND_ICON.get(kind, "info")
        row.addWidget(_icon_label(name, KIND_COLOUR.get(kind, "icon"), m.size("icon-md")))
        label = QLabel(text)
        label.setWordWrap(False)
        row.addWidget(label, 1)
        if action_text:
            def act() -> None:
                if on_action is not None:
                    on_action()
                self.closed.emit()

            row.addWidget(_link_button(action_text, act))
        row.addWidget(_close_button(self.closed.emit, "Kapat"))
        self.setMaximumWidth(560 + 2 * SHADOW_ROOM)
        announce(self, text)

    def paintEvent(self, event: QEvent) -> None:  # noqa: N802
        """Soft shadow of the popover level under the frame."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        base = QRectF(self.frame.geometry())
        radius = theme.manager().size("r-layer")
        for layer in theme.manager().shadow("shadow-float"):
            if layer.inset:
                continue
            steps = max(2, layer.blur // 4)
            for i in range(steps):
                grow = layer.blur / 2 * (1 - i / steps)
                colour = QColor(layer.color)
                colour.setAlphaF(layer.color.alphaF() / steps * 1.6)
                painter.setBrush(colour)
                rect = base.translated(layer.x, layer.y).adjusted(-grow, -grow, grow, grow)
                painter.drawRoundedRect(rect, radius + grow, radius + grow)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.closed.emit()
            event.accept()
        else:
            super().keyPressEvent(event)


@dataclass
class _Pending:
    text: str
    action_text: str | None
    on_action: Callable[[], None] | None
    kind: str
    timeout_ms: int


class Toaster(QObject):
    """Shows one toast at a time at the window's bottom-right; later ones wait."""

    def __init__(self, window: QWidget) -> None:
        super().__init__(window)
        self._window = window
        self._queue: deque[_Pending] = deque()
        self._current: _Toast | None = None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.dismiss)
        window.installEventFilter(self)

    def show(self, text: str, action_text: str | None = None,
             on_action: Callable[[], None] | None = None, kind: str = "info",
             timeout_ms: int = 6000) -> None:
        """Queue a toast; it appears at once when none is visible."""
        self._queue.append(_Pending(text, action_text, on_action, kind, timeout_ms))
        if self._current is None:
            self._next()

    def current_text(self) -> str:
        return self._current.accessibleName() if self._current is not None else ""

    def pending(self) -> int:
        return len(self._queue)

    def dismiss(self) -> None:
        """Close the visible toast and show the next one."""
        toast, self._current = self._current, None
        self._timer.stop()
        if toast is not None:
            toast.hide()
            toast.deleteLater()
        if self._queue:
            self._next()

    def _next(self) -> None:
        item = self._queue.popleft()
        toast = _Toast(self._window, item.text, item.action_text, item.on_action, item.kind)
        toast.closed.connect(self.dismiss)
        self._current = toast
        toast.adjustSize()
        self._place()
        toast.raise_()
        motion.fade_in(toast, motion.Duration.SLOWER)
        if item.timeout_ms > 0:
            self._timer.start(item.timeout_ms)

    def _place(self) -> None:
        toast = self._current
        if toast is None:
            return
        win = self._window
        bottom = win.height() - TOAST_MARGIN
        if isinstance(win, QMainWindow) and win.statusBar() is not None:
            bottom -= win.statusBar().height()
        size = toast.sizeHint()
        width = min(size.width(), win.width() - 2 * TOAST_MARGIN + 2 * SHADOW_ROOM)
        toast.setGeometry(win.width() - TOAST_MARGIN + SHADOW_ROOM - width,
                          bottom - size.height() + SHADOW_ROOM, width, size.height())

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802
        if obj is getattr(self, "_window", None) and event.type() == QEvent.Type.Resize:
            self._place()
        return False


class InfoBar(QFrame):
    """A persistent problem or note: icon, bold title, text, one action, dismiss."""

    dismissed = Signal()
    action_clicked = Signal()

    def __init__(self, kind: str, title: str, text: str, action_text: str | None = None,
                 on_action: Callable[[], None] | None = None, dismissible: bool = True,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        m = theme.manager()
        self.setProperty("kind", "infobar")
        if kind in ("error", "kontrol"):
            self.setProperty("severity", kind)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        row = QHBoxLayout(self)
        row.setContentsMargins(m.size("s4"), m.size("s3"), m.size("s2"), m.size("s3"))
        row.setSpacing(m.size("s3"))
        icon = {"error": "circle-x", "kontrol": "triangle-alert"}.get(kind, "info")
        role = {"error": "danger", "kontrol": "check-text"}.get(kind, "icon")
        row.addWidget(_icon_label(icon, role, m.size("icon-md")), 0, Qt.AlignmentFlag.AlignTop)
        self.title_label = QLabel(title)
        self.title_label.setFont(m.font("body-strong"))
        self.text_label = QLabel(text)
        self.text_label.setWordWrap(True)
        body = QWidget()
        column = QHBoxLayout(body)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(m.size("s2"))
        column.addWidget(self.title_label)
        column.addWidget(self.text_label, 1)
        row.addWidget(body, 1)
        self.action_button: QPushButton | None = None
        if action_text:
            def act() -> None:
                if on_action is not None:
                    on_action()
                self.action_clicked.emit()

            self.action_button = _link_button(action_text, act)
            row.addWidget(self.action_button)
        self.close_button: QToolButton | None = None
        if dismissible:
            self.close_button = _close_button(self._dismiss, "Kapat")
            row.addWidget(self.close_button)
        self.setAccessibleName(f"{title}. {text}")
        self.setAccessibleDescription("Uyarı")

    def _dismiss(self) -> None:
        self.hide()
        self.dismissed.emit()


MONTHS = ("Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara")


def saved_text(when: datetime, now: datetime | None = None) -> str:
    """"14:32" today, "12 Kas 14:32" on another day this year, "12 Kas 2025 14:32" before."""
    now = now or datetime.now()
    if when.date() == now.date():
        return f"{when:%H:%M}"
    year = "" if when.year == now.year else f" {when.year}"
    return f"{when.day} {MONTHS[when.month - 1]}{year} {when:%H:%M}"


class SaveState(QWidget):
    """Title band status next to the job name: Kaydediliyor / Kaydedildi 14:32 / Kaydedilemedi."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        m = theme.manager()
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(m.size("s1"))
        self._icon = QLabel()
        self._icon.setFixedSize(m.size("icon-sm"), m.size("icon-sm"))
        self._label = QLabel()
        self._label.setProperty("textRole", "secondary")
        self._retry = _link_button("Yeniden dene", self._on_retry)
        self._retry.hide()
        row.addWidget(self._icon)
        row.addWidget(self._label)
        row.addWidget(self._retry)
        self._retry_call: Callable[[], None] | None = None
        self._state = "saved"
        self._text = ""
        self._glyph = ""
        self._role = "icon"
        theme.manager().changed.connect(self._refresh_icon)
        self.hide()

    def state(self) -> str:
        return self._state

    def text(self) -> str:
        return self._text

    def set_saving(self) -> None:
        self._show("saving", "Kaydediliyor…", "refresh-cw", "icon")

    def set_saved(self, when: datetime) -> None:
        self._show("saved", f"Kaydedildi {saved_text(when)}", "check", "icon")

    def set_failed(self, message: str, retry: Callable[[], None] | None = None) -> None:
        """Show "Kaydedilemedi" (the message is the tooltip) with a retry action."""
        self._retry_call = retry
        self._show("failed", "Kaydedilemedi", "circle-x", "danger")
        self.setToolTip(message)
        self._retry.setVisible(retry is not None)

    def _show(self, state: str, text: str, glyph: str, role: str) -> None:
        self._state, self._text, self._glyph, self._role = state, text, glyph, role
        self._label.setText(text)
        self._retry.hide()
        self.setToolTip("")
        self._refresh_icon()
        self.setAccessibleName(text)
        self.show()

    def _refresh_icon(self) -> None:
        if not self._glyph:
            return
        size = theme.manager().size("icon-sm")
        self._icon.setPixmap(icons.pixmap(self._glyph, theme.manager().hex(self._role), size))

    def _on_retry(self) -> None:
        if self._retry_call is not None:
            self._retry_call()

