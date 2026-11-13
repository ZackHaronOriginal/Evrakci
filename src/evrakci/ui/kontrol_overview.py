"""The whole job above the timeline (A .overview): one segment per document, reviewed in the
accent, kontrol in the rider orange (with its edge), the rest on the track; a 2 px ring marks
the documents in view, and "Belge 14–18 / 96" names them. A click jumps to a document; dragging
moves the view along the job. Painted in one widget, so 1,000 documents cost one paint.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QFontMetrics, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QToolTip, QWidget

from evrakci.ui import theme

TRACK_H = 8  # A .track height
SEG_GAP = 2  # A .track gap
VP_OUT_V = 6  # A .vp top/bottom -6px
VP_OUT_H = 4  # A: viewport ring 4 px wider than its segments on both sides
SEG_MAX = 8  # A: a document is a small square (about 8 px) on the track, never a long bar


class OverviewStrip(QWidget):
    """`documents` is the count; `kontrol` and `reviewed` hold 1-based document numbers;
    `visible` is the (first, last) document in view. `check_rows` keeps (row, number) of the
    documents that need a check (the window counts them for its status bar)."""

    jump = Signal(int)  # document number

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.documents = 0
        self.kontrol: set[int] = set()
        self.reviewed: set[int] = set()
        self.visible: tuple[int, int] | None = None
        self.check_rows: list[tuple[int, int]] = []
        self._dragging = False
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # keys: N, U, Ctrl+G, Ctrl+arrows
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.refresh_size()
        theme.follow(self, self.refresh_size)

    def refresh_size(self) -> None:
        self.setFixedHeight(theme.manager().size("overview-h"))
        self.update()

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(400, theme.manager().size("overview-h"))

    # -- state --------------------------------------------------------------------------------
    def set_state(self, documents: int, kontrol: set[int], reviewed: set[int]) -> None:
        self.documents = documents
        self.kontrol = set(kontrol)
        self.reviewed = set(reviewed)
        self._describe()
        self.update()

    def set_visible(self, first: int, last: int) -> None:
        value = (first, last) if first and last else None
        if value != self.visible:
            self.visible = value
            self._describe()
            self.update()

    def where_text(self) -> str:
        """"Belge 14–18 / 96" (the bold part first, then the total)."""
        if not self.documents:
            return ""
        if self.visible is None:
            return f"/ {self.documents}"
        first, last = self.visible
        span = f"Belge {first}" if first == last else f"Belge {first}–{last}"
        return f"{span} / {self.documents}"

    def _describe(self) -> None:
        self.setAccessibleName(f"Tüm iş: {self.documents} belge")
        parts = [self.where_text().replace("/", "görünüyor, toplam").strip()]
        if self.kontrol:
            parts.append(f"{len(self.kontrol)} belge kontrol bekliyor")
        parts.append(f"{len(self.reviewed)} belge incelendi")
        self.setAccessibleDescription(", ".join(p for p in parts if p))

    # -- geometry -----------------------------------------------------------------------------
    def _where_width(self) -> int:
        m = theme.manager()
        text = self.where_text()
        if not text:
            return 0
        bold, _, rest = text.partition(" / ")
        return (QFontMetrics(m.font("caption-strong")).horizontalAdvance(bold + " ")
                + QFontMetrics(m.font("caption-num")).horizontalAdvance("/ " + rest)) + 2

    def track_rect(self) -> QRectF:
        m = theme.manager()
        left, right = m.size("s6"), m.size("s4")
        where = self._where_width()
        width = self.width() - left - right - (where + m.size("s4") if where else 0)
        return QRectF(left, (self.height() - TRACK_H) / 2, max(0, width), TRACK_H)

    def _pitch(self, track: QRectF) -> tuple[float, float]:
        """(segment width, gap): A's 8 px squares with 2 px gaps, left-aligned; only when the
        job has more documents than fit do they share the track (narrower, then no gaps)."""
        n = max(1, self.documents)
        if n * (SEG_MAX + SEG_GAP) - SEG_GAP <= track.width():
            return float(SEG_MAX), float(SEG_GAP)
        gap = SEG_GAP if track.width() / n >= 4 else 0
        return (track.width() - gap * (n - 1)) / n, float(gap)

    def run_rect(self) -> QRectF:
        """The part of the track the documents take (left-aligned)."""
        track = self.track_rect()
        width, gap = self._pitch(track)
        n = max(1, self.documents)
        return QRectF(track.x(), track.y(), min(track.width(), n * (width + gap) - gap),
                      track.height())

    def _segment(self, number: int, track: QRectF) -> QRectF:
        """The rect of document `number` (1-based) on the track."""
        width, gap = self._pitch(track)
        x = track.x() + (number - 1) * (width + gap)
        return QRectF(x, track.y(), max(width, 1.0), track.height())

    def number_at(self, x: float) -> int:
        run = self.run_rect()
        if not self.documents or run.width() <= 0:
            return 0
        fraction = (x - run.x()) / run.width()
        return int(min(max(fraction, 0.0), 0.9999) * self.documents) + 1

    # -- painting -----------------------------------------------------------------------------
    def paintEvent(self, _event) -> None:  # noqa: N802
        m = theme.manager()
        hc = m.theme() == "hc"
        painter = QPainter(self)
        painter.fillRect(self.rect(), m.color("layer"))
        if not self.documents:
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        track = self.track_rect()
        n = self.documents
        thin = self._pitch(track)[1] == 0
        if thin:  # too many documents for gaps: one track, states drawn on it
            painter.setPen(QPen(m.color("stroke"), 1) if hc else Qt.PenStyle.NoPen)
            painter.setBrush(m.color("track"))
            painter.drawRoundedRect(track, 2, 2)
        for number in range(1, n + 1):
            state = ("k" if number in self.kontrol else "done" if number in self.reviewed
                     else "")
            if thin and not state:
                continue
            rect = self._segment(number, track)
            if thin and state == "k":
                rect = QRectF(rect.center().x() - 1.5, rect.y(), 3, rect.height())
            colour = {"k": "rider", "done": "accent"}.get(state, "track")
            painter.setPen(Qt.PenStyle.NoPen)
            if state == "k" and hc:  # high contrast: a filled mark, not one more outline
                painter.setBrush(m.color("text"))
                painter.drawRoundedRect(rect, 2, 2)
                continue
            if state == "k":  # A .track i.k: inset 1 px rider edge
                painter.setBrush(m.color("rider-edge"))
                painter.drawRoundedRect(rect, 2, 2)
                painter.setBrush(m.color("rider"))
                painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 1, 1)
                continue
            if hc:
                painter.setPen(QPen(m.color("stroke"), 1))
            painter.setBrush(m.color(colour))
            painter.drawRoundedRect(rect.adjusted(0.5 if hc else 0, 0.5 if hc else 0,
                                                  -0.5 if hc else 0, -0.5 if hc else 0), 2, 2)
        if self.visible is not None:
            first = self._segment(self.visible[0], track)
            last = self._segment(self.visible[1], track)
            ring = QRectF(first.x() - VP_OUT_H, track.y() - VP_OUT_V,
                          last.right() - first.x() + 2 * VP_OUT_H, track.height() + 2 * VP_OUT_V)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(m.color("text"), 2))
            painter.drawRoundedRect(ring.adjusted(1, 1, -1, -1), 4, 4)
        text = self.where_text()
        bold, _, rest = text.partition(" / ")
        x = track.right() + m.size("s4")  # A: "Belge 14–18 / 96" at the track's end
        strong, num = m.font("caption-strong"), m.font("caption-num")
        painter.setFont(strong)
        painter.setPen(m.color("text"))
        rect = QRectF(x, 0, self.width() - x, self.height())
        align = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        painter.drawText(rect, align, bold)
        x += QFontMetrics(strong).horizontalAdvance(bold + " ")
        painter.setFont(num)
        painter.setPen(m.color("text-2"))
        painter.drawText(QRectF(x, 0, self.width() - x, self.height()), align, f"/ {rest}")

    # -- mouse --------------------------------------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._jump(event.position())

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._dragging:
            self._jump(event.position())
            return
        number = self.number_at(event.position().x())
        if number and self.track_rect().adjusted(0, -VP_OUT_V, 0, VP_OUT_V).contains(
                event.position()):
            state = ("Kontrol bekliyor" if number in self.kontrol else "İncelendi"
                     if number in self.reviewed else "İncelenmedi")
            QToolTip.showText(event.globalPosition().toPoint(), f"Belge {number}: {state}", self)
        else:
            QToolTip.hideText()

    def mouseReleaseEvent(self, _event: QMouseEvent) -> None:  # noqa: N802
        self._dragging = False

    def _jump(self, position: QPointF) -> None:
        number = self.number_at(position.x())
        if number:
            self.jump.emit(number)
