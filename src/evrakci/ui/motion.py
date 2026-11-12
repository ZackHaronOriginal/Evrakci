"""Motion tokens, easing curves and helpers (decision D7).

Durations are 0/80/120/180/240 ms and nothing larger. Reduced motion (the
user's override, else Qt's motion preference, else the OS hint) turns every
duration into 0, so animations apply their end value at once.
Repeated actions (arrow keys, accept-next) must not animate: pass
``animate=False`` to the helpers.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from contextlib import contextmanager
from enum import IntEnum

from PySide6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QObject,
    QPointF,
    QPropertyAnimation,
    Qt,
    QTimer,
)
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import QApplication, QGraphicsOpacityEffect, QWidget


class Duration(IntEnum):
    """Duration tokens in milliseconds."""

    NONE = 0
    FAST = 80
    NORMAL = 120
    SLOW = 180
    SLOWER = 240


MAX_DURATION = int(Duration.SLOWER)
BUSY_DELAY_MS = 100

_override: bool | None = None  # None = follow the system


def _bezier(x1: float, y1: float, x2: float, y2: float) -> QEasingCurve:
    curve = QEasingCurve(QEasingCurve.Type.BezierSpline)
    curve.addCubicBezierSegment(QPointF(x1, y1), QPointF(x2, y2), QPointF(1, 1))
    return curve


def standard() -> QEasingCurve:
    """Default curve for things that move or resize on screen."""
    return _bezier(0.2, 0.0, 0.0, 1.0)


def enter() -> QEasingCurve:
    """Things appearing."""
    return _bezier(0.0, 0.0, 0.0, 1.0)


def exit_() -> QEasingCurve:
    """Things leaving."""
    return _bezier(0.3, 0.0, 1.0, 1.0)


def linear() -> QEasingCurve:
    return QEasingCurve(QEasingCurve.Type.Linear)


def set_reduced_motion_override(value: bool | None) -> None:
    """User setting: None follows the system, True/False forces it."""
    global _override
    _override = value


def system_reduced_motion() -> bool:
    """Qt 6.12 motion preference if present, else the OS animation hint."""
    app = QGuiApplication.instance()
    hints = app.styleHints() if app is not None else None
    for name in ("motionPreference", "prefersReducedMotion"):
        if hints is not None and hasattr(hints, name):
            value = getattr(hints, name)()
            if isinstance(value, bool):
                return value
            text = str(getattr(value, "name", value)).lower()
            return "reduce" in text or "less" in text or "no" in text
    if sys.platform == "win32":
        import ctypes

        enabled = ctypes.c_int(1)
        # SPI_GETCLIENTAREAANIMATION = 0x1042
        if ctypes.windll.user32.SystemParametersInfoW(0x1042, 0, ctypes.byref(enabled), 0):
            return not enabled.value
    return False


def reduced_motion() -> bool:
    """True when animations must be skipped."""
    return _override if _override is not None else system_reduced_motion()


def duration(token: Duration | int) -> int:
    """Milliseconds for a token; 0 under reduced motion."""
    ms = int(token)
    if ms not in {int(d) for d in Duration}:
        raise ValueError(f"Bilinmeyen süre: {ms}")
    return 0 if reduced_motion() else ms


def animate(
    target: QObject,
    prop: bytes,
    start: object,
    end: object,
    token: Duration | int = Duration.NORMAL,
    curve: QEasingCurve | None = None,
    parent: QObject | None = None,
    animate: bool = True,
) -> QPropertyAnimation | None:
    """Animate ``prop`` from start to end; set the end value at once if reduced.

    Returns None when nothing runs (reduced motion, zero duration or
    ``animate=False`` for repeated actions). The animation deletes itself.
    """
    ms = duration(token) if animate else 0
    if ms == 0:
        target.setProperty(prop.decode(), end)
        return None
    anim = QPropertyAnimation(target, prop, parent or target)
    anim.setDuration(ms)
    anim.setStartValue(start)
    anim.setEndValue(end)
    anim.setEasingCurve(curve if curve is not None else standard())
    anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
    return anim


def _effect(widget: QWidget) -> QGraphicsOpacityEffect:
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
    return effect


def fade_in(
    widget: QWidget, token: Duration | int = Duration.NORMAL, animate_: bool = True
) -> QPropertyAnimation | None:
    """Show the widget and fade it in (instant when reduced)."""
    effect = _effect(widget)
    effect.setOpacity(0.0)
    widget.show()
    anim = animate(effect, b"opacity", 0.0, 1.0, token, enter(), widget, animate_)
    if anim is None:
        effect.setOpacity(1.0)
    return anim


def fade_out(
    widget: QWidget, token: Duration | int = Duration.FAST, animate_: bool = True
) -> QPropertyAnimation | None:
    """Fade the widget out, then hide it (instant when reduced)."""
    effect = _effect(widget)
    effect.setOpacity(1.0)
    anim = animate(effect, b"opacity", 1.0, 0.0, token, exit_(), widget, animate_)
    if anim is None:
        widget.hide()
        return None
    anim.finished.connect(widget.hide)
    return anim


@contextmanager
def busy_cursor(delay_ms: int = BUSY_DELAY_MS) -> Iterator[None]:
    """Wait cursor only if the block lasts longer than ``delay_ms``.

    The timer needs the event loop, so use it around work that keeps the
    loop running (workers, processEvents); a fully blocking block never shows it.
    """
    shown = False

    def show() -> None:
        nonlocal shown
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
        shown = True

    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(show)
    timer.start(delay_ms)
    try:
        yield
    finally:
        timer.stop()
        if shown:
            QApplication.restoreOverrideCursor()


__all__ = [
    "BUSY_DELAY_MS", "MAX_DURATION", "Duration", "animate", "busy_cursor",
    "duration", "enter", "exit_", "fade_in", "fade_out", "linear", "reduced_motion",
    "set_reduced_motion_override", "standard", "system_reduced_motion",
]
