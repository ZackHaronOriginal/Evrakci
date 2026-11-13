"""Zoom for views: Ctrl+wheel, Ctrl+plus/minus/0, one saved level per view key.

``ZoomController`` only keeps the percentage and emits ``zoom_changed``; the view's owner
applies it (scale a transform, re-render a page). Scroll areas keep the point under the
cursor fixed while zooming. ``ZoomSlider`` is the status bar control bound to a controller.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QEvent, QObject, QPoint, Qt, Signal
from PySide6.QtGui import QKeyEvent, QWheelEvent
from PySide6.QtWidgets import (
    QAbstractScrollArea,
    QHBoxLayout,
    QLabel,
    QSlider,
    QToolButton,
    QWidget,
)

from evrakci.ui import icons, theme
from evrakci.ui.prefs import ZOOM_RANGE, Prefs

SLIDER_WIDTH = 112
_PLUS = (Qt.Key.Key_Plus, Qt.Key.Key_Equal)
_MINUS = (Qt.Key.Key_Minus, Qt.Key.Key_Underscore)


class ZoomController(QObject):
    """Percentage state for one view, persisted under ``prefs.zoom(key)``."""

    zoom_changed = Signal(int)

    def __init__(self, view: QWidget, prefs: Prefs | None, key: str, minimum: int = 25,
                 maximum: int = 400, step: int = 10,
                 fit_callback: Callable[[], int | None] | None = None) -> None:
        super().__init__(view)
        self._view = view
        self._prefs = prefs
        self._key = key
        self._min = max(minimum, ZOOM_RANGE[0])
        self._max = min(maximum, ZOOM_RANGE[1])
        self._step = step
        self._fit = fit_callback
        self._pct = self._clamp(prefs.zoom(key) if prefs is not None else 100)
        self._wheel = 0
        view.installEventFilter(self)
        if isinstance(view, QAbstractScrollArea):
            view.viewport().installEventFilter(self)

    # -- state --------------------------------------------------------------
    def zoom(self) -> int:
        return self._pct

    def minimum(self) -> int:
        return self._min

    def maximum(self) -> int:
        return self._max

    def key(self) -> str:
        return self._key

    def _clamp(self, pct: int) -> int:
        return max(self._min, min(self._max, int(round(pct))))

    def set_fit_callback(self, callback: Callable[[], int | None] | None) -> None:
        self._fit = callback

    def set_zoom(self, pct: int, anchor: QPoint | None = None, save: bool = True) -> None:
        """Clamp, store, emit; ``anchor`` (viewport point) stays put in scroll areas."""
        new = self._clamp(pct)
        if new == self._pct:
            return
        old, self._pct = self._pct, new
        scroll = self._view if isinstance(self._view, QAbstractScrollArea) else None
        point = anchor
        if scroll is not None and point is None:
            point = scroll.viewport().rect().center()
        before = None
        if scroll is not None and point is not None:
            before = (scroll.horizontalScrollBar().value() + point.x(),
                      scroll.verticalScrollBar().value() + point.y())
        if save and self._prefs is not None:
            self._prefs.set_zoom(self._key, new)
        self.zoom_changed.emit(new)
        if scroll is not None and before is not None and point is not None:
            ratio = new / old
            scroll.horizontalScrollBar().setValue(round(before[0] * ratio) - point.x())
            scroll.verticalScrollBar().setValue(round(before[1] * ratio) - point.y())

    def zoom_in(self, anchor: QPoint | None = None) -> None:
        self.set_zoom(self._pct + self._step, anchor)

    def zoom_out(self, anchor: QPoint | None = None) -> None:
        self.set_zoom(self._pct - self._step, anchor)

    def fit(self) -> None:
        """Ctrl+0: ask the owner for the fitting percentage (else 100)."""
        value = self._fit() if self._fit is not None else None
        self.set_zoom(value if isinstance(value, int) else 100)

    # -- input --------------------------------------------------------------
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802
        kind = event.type()
        if kind == QEvent.Type.Wheel and isinstance(event, QWheelEvent):
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                self._on_wheel(obj, event)
                event.accept()
                return True
        elif kind == QEvent.Type.KeyPress and isinstance(event, QKeyEvent):
            if obj is self._view and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                return self._on_key(event.key())
        return False

    def _on_wheel(self, obj: QObject, event: QWheelEvent) -> None:
        self._wheel += event.angleDelta().y() or event.angleDelta().x()
        steps = int(self._wheel / 120)
        if steps == 0:
            return
        self._wheel -= steps * 120
        pos = event.position().toPoint()
        if isinstance(self._view, QAbstractScrollArea) and obj is not self._view.viewport():
            pos = self._view.viewport().mapFromGlobal(event.globalPosition().toPoint())
        self.set_zoom(self._pct + steps * self._step, pos)

    def _on_key(self, key: int) -> bool:
        if key in _PLUS:
            self.zoom_in()
        elif key in _MINUS:
            self.zoom_out()
        elif key == Qt.Key.Key_0:
            self.fit()
        else:
            return False
        return True


class ZoomSlider(QWidget):
    """Status bar control: zoom out, slider, zoom in, "%112"; rebindable per tab."""

    def __init__(self, controller: ZoomController | None = None, target: str = "Görünüm",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        m = theme.manager()
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(m.size("s2"))
        self._out = self._button("zoom-out")
        self._in = self._button("zoom-in")
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setFixedWidth(SLIDER_WIDTH)
        self.slider.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.label = QLabel("%100")
        self.label.setProperty("textRole", "secondary")
        self.label.setFont(m.font("caption-num"))
        self.label.setMinimumWidth(m.size("s12"))
        self.label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        for widget in (self._out, self.slider, self._in, self.label):
            row.addWidget(widget)
        self._controller: ZoomController | None = None
        self._target = target
        self._busy = False
        self.slider.valueChanged.connect(self._on_slider)
        self._out.clicked.connect(lambda: self._controller and self._controller.zoom_out())
        self._in.clicked.connect(lambda: self._controller and self._controller.zoom_in())
        self.bind(controller, target)

    def _button(self, icon: str) -> QToolButton:
        button = QToolButton()
        button.setProperty("kind", "icon")
        button.setProperty("size", "sm")
        button.setAutoRaise(True)
        button.setIcon(icons.icon(icon, theme.manager().hex("icon")))
        button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        return button

    def controller(self) -> ZoomController | None:
        return self._controller

    def bind(self, controller: ZoomController | None, target: str | None = None) -> None:
        """Follow another controller (e.g. when the tab changes); None disables."""
        if self._controller is not None:
            try:
                self._controller.zoom_changed.disconnect(self._show)
            except (RuntimeError, TypeError):
                pass
        self._controller = controller
        if target is not None:
            self._target = target
        name = self._target
        for widget, text in ((self._out, f"{name} uzaklaştır"), (self._in, f"{name} yakınlaştır"),
                             (self.slider, f"{name} yakınlaştırma düzeyi")):
            widget.setToolTip(text)
            widget.setAccessibleName(text)
        self.setToolTip(f"{name}: yakınlaştırma (Ctrl+tekerlek, Ctrl+0 sığdır)")
        self.setEnabled(controller is not None)
        if controller is not None:
            self._busy = True
            self.slider.setRange(controller.minimum(), controller.maximum())
            self._busy = False
            controller.zoom_changed.connect(self._show)
            self._show(controller.zoom())
        else:
            self.label.setText("")

    def _show(self, pct: int) -> None:
        self._busy = True
        self.slider.setValue(pct)
        self._busy = False
        self.label.setText(f"%{pct}")

    def _on_slider(self, value: int) -> None:
        if not self._busy and self._controller is not None:
            self._controller.set_zoom(value)
