"""The well of Şablonlar: the page canvas with the two millimetre rulers (final-a .canvas-well).

The rulers are two small widgets painted with QPainter beside the QGraphicsView (caption text,
a `stroke` hairline on the inner edge, `text-2` ticks every 5 mm with taller ones every 10 mm
and numbers every 20 mm at the A scale; the selected box's extent is a 2 px `accent` bar on each
ruler). The origin is the sheet's top-left corner; they follow zoom and scroll.
"""

from __future__ import annotations

from PySide6.QtCore import QLineF, QRectF, QSize, Qt
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QFrame, QGridLayout, QSizePolicy, QWidget

from evrakci.ui import theme
from evrakci.ui.sablon_canvas import PageCanvas

RULER = 24  # A .ruler thickness at 100 % text (36 at 150 %)
LABEL_STEPS = (10, 20, 50, 100, 200, 500)  # mm between numbers
LABEL_ROOM = 44  # px a number needs between neighbours


def ruler_size() -> int:
    return round(RULER * theme.manager().text_scale() / 100)


class Ruler(QWidget):
    """One ruler (top: horizontal; left: vertical, numbers reading bottom-up as in Word)."""

    def __init__(self, canvas: PageCanvas, horizontal: bool, parent=None) -> None:
        super().__init__(parent)
        self.canvas = canvas
        self.horizontal = horizontal
        self.extent: tuple[float, float] | None = None
        name = "Cetvel, yatay (mm)" if horizontal else "Cetvel, dikey (mm)"
        self.setAccessibleName(name)
        self.setToolTip(name)
        self.setSizePolicy(QSizePolicy.Policy.Expanding if horizontal else QSizePolicy.Policy.Fixed,
                           QSizePolicy.Policy.Fixed if horizontal else QSizePolicy.Policy.Expanding)
        canvas.view_changed.connect(self.update)
        theme.follow(self, self._restyle, f"ruler-{horizontal}")

    def _restyle(self) -> None:
        size = ruler_size()
        if self.horizontal:
            self.setFixedHeight(size)
        else:
            self.setFixedWidth(size)
        self.update()

    def sizeHint(self) -> QSize:  # noqa: N802
        size = ruler_size()
        return QSize(size, size)

    def set_extent(self, start: float | None, end: float | None = None) -> None:
        """The selected box's extent in mm along this ruler (None clears it)."""
        self.extent = None if start is None or end is None else (start, end)
        self.update()

    def _steps(self, per_mm: float) -> tuple[float, float, float]:
        """(minor, major, label) spacing in mm for the zoom: label = 4 minors = 2 majors."""
        label = next((s for s in LABEL_STEPS if s * per_mm >= LABEL_ROOM), LABEL_STEPS[-1])
        return label / 4, label / 2, label

    def paintEvent(self, _event) -> None:  # noqa: N802
        m = theme.manager()
        canvas = self.canvas
        painter = QPainter(self)
        thick = self.height() if self.horizontal else self.width()
        length = self.width() if self.horizontal else self.height()
        painter.setPen(QPen(m.color("stroke"), 1))
        if self.horizontal:
            painter.drawLine(QLineF(0, thick - 0.5, length, thick - 0.5))
        else:
            painter.drawLine(QLineF(thick - 0.5, 0, thick - 0.5, length))
        if not canvas.has_page():
            return
        per_mm = canvas.px_per_mm()
        origin = canvas.origin()
        start = origin.x() if self.horizontal else origin.y()
        minor, major, label = self._steps(per_mm)
        font = m.font("caption-num")
        painter.setFont(font)
        metrics = painter.fontMetrics()
        ink = m.color("text-2")
        first = 0
        last = int((length - start) / per_mm / minor) + 1
        for k in range(first, max(last, 0) + 1):
            mm = k * minor
            at = round(start + mm * per_mm) + 0.5
            if at < 0 or at > length:
                continue
            is_major = abs(mm % major) < 1e-6
            tick = 7 if is_major else 4
            painter.setPen(QPen(ink, 1))
            if self.horizontal:
                painter.drawLine(QLineF(at, thick - 1 - tick, at, thick - 1))
            else:
                painter.drawLine(QLineF(thick - 1 - tick, at, thick - 1, at))
            if abs(mm % label) < 1e-6:
                text = f"{round(mm):d}"
                width = metrics.horizontalAdvance(text)
                if self.horizontal and at + 3 + width <= length:
                    painter.drawText(QRectF(at + 3, 0, width + 2, thick - 8),
                                     Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, text)
                elif not self.horizontal and at - 3 - width >= 0:
                    painter.save()
                    painter.translate(0, at)
                    painter.rotate(-90)  # the number reads bottom-up, starting above its tick
                    painter.drawText(QRectF(3, 0, width + 2, thick - 8),
                                     Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, text)
                    painter.restore()
        if self.extent is not None:
            a = start + self.extent[0] * per_mm
            b = start + self.extent[1] * per_mm
            bar = QRectF(a, thick - 2, max(b - a, 1.0), 2) if self.horizontal else QRectF(
                thick - 2, a, 2, max(b - a, 1.0))
            painter.fillRect(bar, m.color("accent"))


class RulerCorner(QWidget):
    """The square where the rulers meet: the two inner hairlines only."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        theme.follow(self, self._restyle, "ruler-corner")

    def _restyle(self) -> None:
        size = ruler_size()
        self.setFixedSize(size, size)
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setPen(QPen(theme.manager().color("stroke"), 1))
        painter.drawLine(QLineF(self.width() - 0.5, 0, self.width() - 0.5, self.height()))
        painter.drawLine(QLineF(0, self.height() - 0.5, self.width(), self.height() - 0.5))


class CanvasWell(QFrame):
    """A recessed well (`well`, radius 8) holding the canvas and its two rulers."""

    def __init__(self, canvas: PageCanvas, parent=None) -> None:
        super().__init__(parent)
        self.setProperty("kind", "well")
        self.canvas = canvas
        self.top = Ruler(canvas, True)
        self.left = Ruler(canvas, False)
        self.corner = RulerCorner()
        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)
        grid.addWidget(self.corner, 0, 0)
        grid.addWidget(self.top, 0, 1)
        grid.addWidget(self.left, 1, 0)
        grid.addWidget(canvas, 1, 1)

    def set_extent(self, box: tuple[float, float, float, float] | None) -> None:
        """Mark the selected box on both rulers (x0, y0, x1, y1 in mm; None clears)."""
        if box is None:
            self.top.set_extent(None)
            self.left.set_extent(None)
        else:
            self.top.set_extent(box[0], box[2])
            self.left.set_extent(box[1], box[3])
