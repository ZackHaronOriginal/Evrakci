"""The page canvas of Şablonlar (final-a/sablonlar.html): an example page on a well, with the
template's boxes drawn over it.

Zoom is a percentage of the printed size at 96 dpi (%100 = life size); Ctrl+wheel, Ctrl+plus,
minus and 0 are the foundation's `ZoomController` (wired by the screen). The page pans with the
wheel, Shift+wheel, a middle-button drag and Space + drag. A box is selected by a click, moved by
dragging its body, resized by its corner handles, and nudged by the arrow keys (0,25 mm, Shift
1 mm; D11 ring while the canvas has keyboard focus). With "Kutu çiz" on, a drag draws a box. With
"Izgaraya oturt" on, drawing, moving and resizing snap to whole millimetres; nudging never snaps.

Everything is drawn in the item `paint`s: boxes, handles and number badges are painted in device
pixels (constant size at every zoom) from the theme tokens, so a theme switch needs no rebuild.
"""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image
from PySide6.QtCore import QEvent, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QKeyEvent, QPainter, QPen, QTransform
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsItem,
    QGraphicsScene,
    QGraphicsView,
    QToolTip,
)

from evrakci.ui import icons, theme
from evrakci.ui.style import KEYBOARD_REASONS, focus_ring, paint_ring
from evrakci.ui.thumbnails import to_qimage

CANVAS_DPI = 200  # scene units are pixels of the page rendered at this resolution
MM = 25.4
SCREEN_DPI = 96  # %100 is life size at this resolution
NUDGE_MM = 0.25
NUDGE_BIG_MM = 1.0
DEFAULT_BOX_MM = (40.0, 10.0)  # B then Enter: a box drawn from the keyboard
SNAP_MM = 1.0
MIN_BOX_MM = 2.0
MARGIN_MM = 2.5  # scene room around the sheet (A: 8 px between the ruler and the sheet)
FIT_MARGIN = 16  # screen px left and right of the sheet when it is fitted
ZOOM_MIN, ZOOM_MAX, ZOOM_STEP = 25, 400, 10
HANDLE = 7  # A .fbox.sel i
HANDLE_HIT = 8
BADGE = 20  # A .fbox .no
BADGE_GAP = 6
SCROLLBAR_ROOM = theme.SCROLLBAR_W
ARROWS = {Qt.Key.Key_Left: (-1, 0), Qt.Key.Key_Right: (1, 0), Qt.Key.Key_Up: (0, -1),
          Qt.Key.Key_Down: (0, 1)}
Box = tuple[float, float, float, float]


def pixels_to_mm(rect: QRectF, dpi: int) -> Box:
    """A box drawn on the page as displayed, in millimetres from its top-left corner."""
    r = rect.normalized()
    return tuple(round(v / dpi * MM, 2) for v in (r.left(), r.top(), r.right(), r.bottom()))


def fmt_mm(value: float) -> str:
    """Millimetres as the Turkish UI writes them: 70,0  70,25  104,5."""
    whole, fraction = f"{value:.2f}".split(".")
    return f"{whole},{fraction.rstrip('0') or '0'}"


@dataclass
class BoxSpec:
    """One box on the displayed page: which variable and section it reads, where."""

    name: str  # the variable
    index: int  # its section
    number: int  # the variable's number in the list (the badge)
    box: Box  # millimetres from the sheet's top-left
    dashed: bool = False  # a variant, or drawn on another example
    reading: str = ""  # the live read, for "Okumaları sayfada göster"
    level: str = ""  # emin / orta / kontrol / okunamadi


class PageItem(QGraphicsItem):
    """The sheet: the scan, a hairline and A's two-step paper shadow (painted, not QSS)."""

    def __init__(self, image, width: int, height: int) -> None:
        super().__init__()
        self._image = image
        self._rect = QRectF(0, 0, width, height)
        self._scale = 1.0
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.setZValue(0)

    def set_scale(self, scale: float) -> None:
        self.prepareGeometryChange()
        self._scale = max(scale, 1e-3)

    def boundingRect(self) -> QRectF:  # noqa: N802
        pad = 16 / self._scale
        return self._rect.adjusted(-pad, -pad, pad, pad)

    def paint(self, painter, option, widget=None) -> None:  # noqa: N802
        m = theme.manager()
        dev = painter.worldTransform().mapRect(self._rect)
        painter.save()
        painter.resetTransform()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for layer in m.shadow("shadow-paper"):
            if layer.color.alpha() == 0:
                continue
            for i in range(layer.blur + 1):
                colour = QColor(layer.color)
                colour.setAlphaF(layer.color.alphaF() * (1 - i / (layer.blur + 1)) ** 2)
                painter.setPen(QPen(colour, 1))
                painter.drawRoundedRect(dev.translated(layer.x, layer.y).adjusted(-i, -i, i, i),
                                        2 + i, 2 + i)
        painter.restore()
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawImage(self._rect, self._image)
        painter.save()
        painter.resetTransform()
        painter.setPen(QPen(m.color("stroke"), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(dev.adjusted(-0.5, -0.5, 0.5, 0.5))
        painter.restore()


class BoxItem(QGraphicsItem):
    """A template box: a 2 px outline in `paper-box`, a number badge to its left, and, when it is
    selected, a paper halo, four corner handles and (keyboard focus) the D11 ring."""

    def __init__(self, spec: BoxSpec, per_mm: float) -> None:
        super().__init__()
        self.spec = spec
        self._per_mm = per_mm  # scene px per mm
        self._scale = 1.0
        self.selected = False
        self.focused = False
        self.show_reading = False
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.setZValue(1)

    def rect(self) -> QRectF:
        x0, y0, x1, y1 = (v * self._per_mm for v in self.spec.box)
        return QRectF(x0, y0, x1 - x0, y1 - y0)

    def set_scale(self, scale: float) -> None:
        self.prepareGeometryChange()
        self._scale = max(scale, 1e-3)

    def set_box(self, box: Box) -> None:
        self.prepareGeometryChange()
        self.spec.box = box

    def set_selected(self, selected: bool, focused: bool) -> None:
        self.selected, self.focused = selected, focused
        self.setZValue(2 if selected else 1)
        self.update()

    def boundingRect(self) -> QRectF:  # noqa: N802
        left, other = 64 / self._scale, 16 / self._scale
        reading = 300 / self._scale if self.show_reading else 0
        return self.rect().adjusted(-left, -other, max(other, reading), 44 / self._scale
                                    if self.show_reading else other)

    def paint(self, painter, option, widget=None) -> None:  # noqa: N802
        m = theme.manager()
        dev = painter.worldTransform().mapRect(self.rect())
        ink, paper = m.color("paper-box"), m.color("paper")
        painter.save()
        painter.resetTransform()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        outline = dev.adjusted(-1, -1, 1, 1)  # a 2 px ring just outside the box (A box-shadow)
        if self.selected:
            painter.setPen(QPen(paper, 2))
            painter.drawRoundedRect(outline.adjusted(-2, -2, 2, 2), 3, 3)
        pen = QPen(ink, 2)
        if self.spec.dashed:
            pen.setDashPattern([3, 2])
        painter.setPen(pen)
        painter.drawRoundedRect(outline, 2, 2)
        if self.selected:
            painter.setPen(QPen(ink, 1.5))
            painter.setBrush(paper)
            for corner in (dev.topLeft(), dev.topRight(), dev.bottomLeft(), dev.bottomRight()):
                painter.drawRect(QRectF(corner.x() - HANDLE / 2, corner.y() - HANDLE / 2,
                                        HANDLE, HANDLE))
            painter.setBrush(Qt.BrushStyle.NoBrush)
        self._badge(painter, dev, ink, paper)
        if self.focused and self.selected:
            paint_ring(painter, dev.adjusted(-8, -8, 8, 8), 4)
        if self.show_reading:
            self._reading(painter, dev)
        painter.restore()

    def _badge(self, painter, dev: QRectF, ink: QColor, paper: QColor) -> None:
        font = theme.manager().font("caption-strong")
        painter.setFont(font)
        text = str(self.spec.number)
        width = max(BADGE, painter.fontMetrics().horizontalAdvance(text) + 10)
        rect = QRectF(dev.left() - BADGE_GAP - width, dev.center().y() - BADGE / 2, width, BADGE)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(ink)
        painter.drawRoundedRect(rect, 2, 2)
        painter.setPen(paper)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
        painter.setBrush(Qt.BrushStyle.NoBrush)

    def label_text(self) -> str:
        return self.spec.reading or "—"

    def _reading(self, painter, dev: QRectF) -> None:
        """The live read under the box: a small card; a kontrol read also carries its icon."""
        m = theme.manager()
        painter.setFont(m.font("caption"))
        metrics = painter.fontMetrics()
        flagged = self.spec.level in ("kontrol", "okunamadi")
        icon = 14 + 4 if flagged else 0
        width = metrics.horizontalAdvance(self.label_text()) + 12 + icon
        rect = QRectF(dev.left(), dev.bottom() + 8, width, 22)
        painter.setPen(QPen(m.color("stroke"), 1))
        painter.setBrush(m.color("card"))
        painter.drawRoundedRect(rect, 4, 4)
        role = "check-text" if flagged else "text"
        if flagged:
            icons.paint(painter, "triangle-alert",
                        QRectF(rect.left() + 6, rect.center().y() - 7, 14, 14), role, 2.0)
        painter.setPen(m.color(role))
        painter.drawText(rect.adjusted(6 + icon, 0, -6, 0), Qt.AlignmentFlag.AlignVCenter
                         | Qt.AlignmentFlag.AlignLeft, self.label_text())


class PageCanvas(QGraphicsView):
    """An example page with the template's boxes; zoom, pan, snap, handles and nudge."""

    box_drawn = Signal(tuple)  # millimetres, from "Kutu çiz"
    box_selected = Signal(str, int)  # a click on a box ("", -1: on the bare page)
    box_changed = Signal(str, int, tuple)  # moved, resized or nudged
    drawing_cancelled = Signal()  # Esc while "Kutu çiz" is on
    view_changed = Signal()  # scrolled, zoomed, resized, new page (the rulers repaint)
    cursor_moved = Signal(object)  # (x_mm, y_mm) over the sheet, or None
    auto_zoomed = Signal(int)  # the percentage after a fit
    focus_changed = Signal(bool)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setBackgroundBrush(QBrush(Qt.BrushStyle.NoBrush))  # the well behind it is the colour
        self.viewport().setAutoFillBackground(False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.setAccessibleName("Örnek sayfa")
        self.dpi = CANVAS_DPI
        self.drawing = False
        self.snap = False
        self.show_reads = False
        self._image = None
        self._size = (0, 0)
        self._page: PageItem | None = None
        self._items: list[BoxItem] = []
        self._selected: tuple[str, int] | None = None
        self._pct = 100
        self._auto = True  # fitted: follows the window until the user zooms
        self._space = False
        self._keyboard = False  # focus came from the keyboard: the D11 ring shows
        self._last_mm: tuple[float, float] | None = None  # pointer over the sheet, for B Enter
        self._pan: tuple[QPointF, int, int] | None = None
        self._drag: tuple | None = None  # ("move"|"size", item, scene start, start box, corner)
        self._start: QPointF | None = None  # "Kutu çiz"
        self._rubber = None
        self.escape_hook = None  # the screen may use Esc first (stopping a long read)
        self._tip = "Kutu çizmek için Kutu çiz (B) açıkken sayfada sürükleyin."
        theme.follow(self, self._restyle, "canvas")

    # -- the page and its boxes -------------------------------------------------------------
    def set_page(self, image: Image.Image | None, dpi: int = CANVAS_DPI) -> None:
        self.dpi = dpi
        self._image = image
        self._size = image.size if image is not None else (0, 0)
        self.scene().clear()
        self._items, self._page, self._rubber, self._drag, self._start = [], None, None, None, None
        if not self._size[0]:
            self.scene().setSceneRect(QRectF())
            self.view_changed.emit()
            return
        width, height = self._size
        self._page = PageItem(to_qimage(image), width, height)
        self.scene().addItem(self._page)
        room = self._px(MARGIN_MM)
        self.scene().setSceneRect(QRectF(-room, -room, width + 2 * room, height + 2 * room))
        if self._auto:
            self.refit()
        else:
            self._apply_zoom(self._pct)
            self.scroll_to_top()
        self.view_changed.emit()

    def has_page(self) -> bool:
        return self._page is not None

    def page_mm(self) -> tuple[float, float]:
        return (self._size[0] / self.dpi * MM, self._size[1] / self.dpi * MM)

    def set_boxes(self, specs: list[BoxSpec]) -> None:
        """The boxes of the displayed page; the selection stays when its box is still there."""
        for item in self._items:
            self.scene().removeItem(item)
        self._items = []
        if self._page is None:
            return
        for spec in specs:
            item = BoxItem(spec, self._px(1))
            item.show_reading = self.show_reads
            item.set_scale(self._scale())
            self.scene().addItem(item)
            self._items.append(item)
        if self._selected is not None and self._find(*self._selected) is None:
            self._selected = None
        self._mark_selection()
        self._update_a11y()
        self.view_changed.emit()

    def boxes(self) -> list[BoxSpec]:
        return [item.spec for item in self._items]

    def update_box(self, name: str, index: int, box: Box) -> None:
        item = self._find(name, index)
        if item is not None:
            item.set_box(box)
            self._update_a11y()
            self.view_changed.emit()

    def set_show_reads(self, on: bool) -> None:
        self.show_reads = on
        for item in self._items:
            item.prepareGeometryChange()
            item.show_reading = on
            item.update()

    def set_readings(self, readings: dict[tuple[str, int], tuple[str, str]]) -> None:
        """(text, level) of each box's live read, shown under it when "Okumaları göster" is on."""
        for item in self._items:
            item.spec.reading, item.spec.level = readings.get(
                (item.spec.name, item.spec.index), ("", ""))
            item.update()

    def _find(self, name: str, index: int) -> BoxItem | None:
        return next((i for i in self._items if (i.spec.name, i.spec.index) == (name, index)),
                    None)

    # -- selection --------------------------------------------------------------------------
    def selected(self) -> tuple[str, int] | None:
        return self._selected

    def selected_item(self) -> BoxItem | None:
        return self._find(*self._selected) if self._selected else None

    def select(self, name: str | None, index: int = -1, reveal: bool = False) -> None:
        self._selected = (name, index) if name and self._find(name, index) else None
        self._mark_selection()
        item = self.selected_item()
        if reveal and item is not None:
            self.ensureVisible(item.rect(), 48, 48)
        self._update_a11y()
        self.view_changed.emit()

    def _mark_selection(self) -> None:
        for item in self._items:
            item.set_selected((item.spec.name, item.spec.index) == self._selected,
                              self.hasFocus() and self._keyboard)
        self._sync_ring()

    def _sync_ring(self) -> None:
        """The D11 ring goes around the selected box; without one, around the canvas itself."""
        ring = focus_ring()
        if ring is not None and self.hasFocus() and self._keyboard:
            ring.show_for(None if self.selected_item() is not None else self)

    def _update_a11y(self) -> None:
        item = self.selected_item()
        if item is None:
            self.setAccessibleDescription(
                f"{len(self._items)} kutu. Seçili kutu yok. Kutu çiz (B) ve Enter, sayfaya "
                "40 x 10 mm bir kutu koyar.")
            return
        x0, y0, x1, y1 = item.spec.box
        self.setAccessibleDescription(
            f"Kutu {item.spec.number}: {item.spec.name}, bölüm {item.spec.index + 1}. "
            f"x {fmt_mm(x0)} y {fmt_mm(y0)} milimetre, genişlik {fmt_mm(x1 - x0)}, "
            f"yükseklik {fmt_mm(y1 - y0)}. Ok tuşları 0,25 mm, Shift ile 1 mm kaydırır; "
            "Ctrl ile oklar boyutu değiştirir.")

    # -- zoom -------------------------------------------------------------------------------
    def _scale(self) -> float:
        return self._pct / 100 * SCREEN_DPI / self.dpi

    def zoom(self) -> int:
        return self._pct

    def is_fitted(self) -> bool:
        return self._auto

    def fit_zoom(self) -> int:
        """The percentage at which the sheet's width fills the view (Ctrl+0)."""
        if not self._size[0]:
            return 100
        full = self._size[0] / self.dpi * SCREEN_DPI  # width in px at %100
        room = self.width() - SCROLLBAR_ROOM - 2 * FIT_MARGIN
        if room <= 0:
            return 100
        return max(ZOOM_MIN, min(ZOOM_MAX, int(room / full * 100)))

    def refit(self) -> None:
        self._auto = True
        pct = self.fit_zoom()
        self._apply_zoom(pct)
        self.scroll_to_top()
        self.auto_zoomed.emit(pct)

    def scroll_to_top(self) -> None:
        for bar in (self.horizontalScrollBar(), self.verticalScrollBar()):
            bar.setValue(bar.minimum())

    def set_zoom(self, pct: int) -> None:
        """A zoom the user chose: the view stops following the window."""
        self._auto = False
        self._apply_zoom(pct)

    def _apply_zoom(self, pct: int) -> None:
        self._pct = pct
        scale = self._scale()
        self.setTransform(QTransform.fromScale(scale, scale))
        if self._page is not None:
            self._page.set_scale(scale)
        for item in self._items:
            item.set_scale(scale)
        self.view_changed.emit()

    def px_per_mm(self) -> float:
        return self.transform().m11() * self.dpi / MM

    def origin(self) -> QPointF:
        """Where the sheet's top-left corner is in viewport pixels."""
        return QPointF(self.mapFromScene(QPointF(0, 0)))

    def view_to_mm(self, pos) -> tuple[float, float]:
        point = self.mapToScene(pos)
        return (point.x() / self.dpi * MM, point.y() / self.dpi * MM)

    def _px(self, mm: float) -> float:
        return mm / MM * self.dpi

    def _mm(self, px: float) -> float:
        return px / self.dpi * MM

    # -- geometry helpers -------------------------------------------------------------------
    def _snapped(self, mm: float) -> float:
        return round(mm / SNAP_MM) * SNAP_MM if self.snap else mm

    def _clamp(self, box: Box) -> Box:
        """Keep the box on the sheet at least MIN_BOX_MM in size (rounded to 0,01 mm)."""
        width, height = self.page_mm()
        x0, y0, x1, y1 = box
        x1, y1 = min(max(x1, MIN_BOX_MM), width), min(max(y1, MIN_BOX_MM), height)
        x0, y0 = max(0.0, min(x0, x1 - MIN_BOX_MM)), max(0.0, min(y0, y1 - MIN_BOX_MM))
        return (round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2))

    def _moved(self, box: Box, dx: float, dy: float) -> Box:
        """The box shifted without changing its size, kept on the sheet."""
        width, height = self.page_mm()
        x0, y0, x1, y1 = box
        dx = min(max(dx, -x0), width - x1)
        dy = min(max(dy, -y0), height - y1)
        return (round(x0 + dx, 2), round(y0 + dy, 2), round(x1 + dx, 2), round(y1 + dy, 2))

    def box_at(self, scene_pos: QPointF) -> BoxItem | None:
        """The box under the point: the selected one first, else the smallest."""
        tol = 4 / max(self._scale(), 1e-3)
        found = [i for i in self._items if i.rect().adjusted(-tol, -tol, tol, tol)
                 .contains(scene_pos)]
        for item in found:
            if (item.spec.name, item.spec.index) == self._selected:
                return item
        return min(found, key=lambda i: i.rect().width() * i.rect().height(), default=None)

    def handle_at(self, pos) -> int | None:
        """The selected box's corner handle under a viewport point: 0 tl, 1 tr, 2 bl, 3 br."""
        item = self.selected_item()
        if item is None:
            return None
        rect = item.rect()
        for number, corner in enumerate((rect.topLeft(), rect.topRight(), rect.bottomLeft(),
                                         rect.bottomRight())):
            spot = self.mapFromScene(corner)
            if abs(spot.x() - pos.x()) <= HANDLE_HIT and abs(spot.y() - pos.y()) <= HANDLE_HIT:
                return number
        return None

    # -- mouse ------------------------------------------------------------------------------
    def mousePressEvent(self, event) -> None:  # noqa: N802
        self._keyboard = False
        self.setFocus(Qt.FocusReason.MouseFocusReason)
        self._mark_selection()
        pos = event.position().toPoint()
        button = event.button()
        if button == Qt.MouseButton.MiddleButton or (
                button == Qt.MouseButton.LeftButton and self._space):
            self._pan = (event.position(), self.horizontalScrollBar().value(),
                         self.verticalScrollBar().value())
            self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
            return
        if button != Qt.MouseButton.LeftButton or self._page is None:
            super().mousePressEvent(event)
            return
        scene_pos = self.mapToScene(pos)
        if self.drawing:
            start = self._snap_point(scene_pos)
            self._start = start
            self._rubber = self.scene().addRect(QRectF(start, start), self._rubber_pen())
            self._rubber.setZValue(3)
            return
        corner = self.handle_at(pos)
        item = self.selected_item() if corner is not None else self.box_at(scene_pos)
        if item is None:
            self._select_from_click("", -1)
            return
        if (item.spec.name, item.spec.index) != self._selected:
            self._select_from_click(item.spec.name, item.spec.index)
        self._drag = ("size" if corner is not None else "move", item, scene_pos, item.spec.box,
                      corner)

    def _snap_point(self, point: QPointF) -> QPointF:
        step = self._px(SNAP_MM)
        if not self.snap:
            return QPointF(point)
        return QPointF(round(point.x() / step) * step, round(point.y() / step) * step)

    def _rubber_pen(self) -> QPen:
        pen = QPen(theme.manager().color("paper-box"), 2, Qt.PenStyle.DashLine)
        pen.setCosmetic(True)
        return pen

    def _select_from_click(self, name: str, index: int) -> None:
        self.select(name, index)
        self.box_selected.emit(name, index)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        pos = event.position().toPoint()
        if self._pan is not None:
            start, hbar, vbar = self._pan
            delta = event.position() - start
            self.horizontalScrollBar().setValue(hbar - round(delta.x()))
            self.verticalScrollBar().setValue(vbar - round(delta.y()))
            return
        self._report_cursor(pos)
        scene_pos = self.mapToScene(pos)
        if self._start is not None and self._rubber is not None:
            self._rubber.setRect(QRectF(self._start, self._snap_point(scene_pos)).normalized())
            return
        if self._drag is not None:
            self._drag_to(scene_pos)
            return
        self._hover_cursor(pos)
        super().mouseMoveEvent(event)

    def _drag_to(self, scene_pos: QPointF) -> None:
        kind, item, start, box, corner = self._drag
        dx, dy = self._mm(scene_pos.x() - start.x()), self._mm(scene_pos.y() - start.y())
        x0, y0, x1, y1 = box
        if kind == "move":
            if self.snap:
                dx, dy = self._snapped(x0 + dx) - x0, self._snapped(y0 + dy) - y0
            new = self._moved(box, dx, dy)
        else:
            nx0, ny0, nx1, ny1 = x0, y0, x1, y1
            if corner in (0, 2):
                nx0 = self._snapped(x0 + dx)
            else:
                nx1 = self._snapped(x1 + dx)
            if corner in (0, 1):
                ny0 = self._snapped(y0 + dy)
            else:
                ny1 = self._snapped(y1 + dy)
            new = self._clamp((nx0, ny0, nx1, ny1))
        item.set_box(new)
        self.view_changed.emit()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if self._pan is not None:
            self._pan = None
            self._hover_cursor(event.position().toPoint())
            return
        if self._start is not None:
            end = self._snap_point(self.mapToScene(event.position().toPoint()))
            rect = QRectF(self._start, end).normalized()
            self._start = None
            width, height = self._size
            rect = rect.intersected(QRectF(0, 0, width, height))
            if self._rubber is not None:
                self.scene().removeItem(self._rubber)
                self._rubber = None
            if rect.width() >= self._px(MIN_BOX_MM) and rect.height() >= self._px(MIN_BOX_MM):
                self.box_drawn.emit(pixels_to_mm(rect, self.dpi))
            return
        if self._drag is not None:
            _kind, item, _start, before, _corner = self._drag
            self._drag = None
            if item.spec.box != before:
                self._update_a11y()
                self.box_changed.emit(item.spec.name, item.spec.index, item.spec.box)
            return
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self.cursor_moved.emit(None)
        super().leaveEvent(event)

    def _report_cursor(self, pos) -> None:
        if self._page is None:
            return
        x, y = self.view_to_mm(pos)
        width, height = self.page_mm()
        inside = 0 <= x <= width and 0 <= y <= height
        if inside:
            self._last_mm = (x, y)
        self.cursor_moved.emit((round(x, 2), round(y, 2)) if inside else None)

    def _hover_cursor(self, pos) -> None:
        shape = Qt.CursorShape.ArrowCursor
        if self._space:
            shape = Qt.CursorShape.OpenHandCursor
        elif self.drawing:
            shape = Qt.CursorShape.CrossCursor
        elif (corner := self.handle_at(pos)) is not None:
            shape = (Qt.CursorShape.SizeFDiagCursor if corner in (0, 3)
                     else Qt.CursorShape.SizeBDiagCursor)
        elif self.box_at(self.mapToScene(pos)) is not None:
            shape = Qt.CursorShape.SizeAllCursor
        self.viewport().setCursor(shape)

    def set_drawing(self, on: bool) -> None:
        self.drawing = on
        self.viewport().setCursor(Qt.CursorShape.CrossCursor if on
                                  else Qt.CursorShape.ArrowCursor)

    def wheelEvent(self, event) -> None:  # noqa: N802
        if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
            bar = self.horizontalScrollBar()
            delta = event.angleDelta().y() or event.angleDelta().x()
            bar.setValue(bar.value() - delta)
            event.accept()
            return
        super().wheelEvent(event)

    def viewportEvent(self, event) -> bool:  # noqa: N802
        if event.type() == QEvent.Type.ToolTip:
            item = self.box_at(self.mapToScene(event.pos()))
            if item is not None:
                spec = item.spec
                QToolTip.showText(event.globalPos(), f"{spec.number}. {spec.name}, "
                                  f"bölüm {spec.index + 1}", self.viewport())
            else:
                QToolTip.showText(event.globalPos(), self._tip, self.viewport())
            return True
        return super().viewportEvent(event)

    # -- keyboard ---------------------------------------------------------------------------
    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        key, mods = event.key(), event.modifiers()
        if not self._keyboard:
            self._keyboard = True
            self._mark_selection()
        plain = not mods & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier)
        if key == Qt.Key.Key_Space and plain and not mods & Qt.KeyboardModifier.ShiftModifier:
            if not event.isAutoRepeat():
                self._space = True
                self.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept()
            return
        if key in ARROWS and plain and self.selected_item() is not None:
            big = bool(mods & Qt.KeyboardModifier.ShiftModifier)
            self.nudge(*ARROWS[key], NUDGE_BIG_MM if big else NUDGE_MM)
            event.accept()
            return
        ctrl_only = (mods & Qt.KeyboardModifier.ControlModifier
                     and not mods & Qt.KeyboardModifier.AltModifier)
        if key in ARROWS and ctrl_only and self.selected_item() is not None:
            # WCAG 2.1.1 / 2.5.7: resize without dragging a handle. Ctrl+Right/Down grow
            # the box, Ctrl+Left/Up shrink it (0,25 mm; with Shift 1 mm).
            big = bool(mods & Qt.KeyboardModifier.ShiftModifier)
            self.resize_selected(*ARROWS[key], NUDGE_BIG_MM if big else NUDGE_MM)
            event.accept()
            return
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and plain and self.drawing:
            # "Kutu çiz" (B) then Enter: a 40 x 10 mm box where the pointer last was over the
            # sheet, or in the middle of what is in view; then arrows, Ctrl+arrows adjust it.
            self.place_default_box()
            event.accept()
            return
        if key == Qt.Key.Key_Escape and plain:
            if self.escape_hook is not None and self.escape_hook():
                event.accept()
                return
            if self.drawing:
                self.drawing_cancelled.emit()
            elif self._selected is not None:
                self._select_from_click("", -1)
            else:
                event.ignore()
                return
            event.accept()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self._space = False
            self.viewport().setCursor(Qt.CursorShape.CrossCursor if self.drawing
                                      else Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        super().keyReleaseEvent(event)

    def nudge(self, dx: int, dy: int, step: float) -> bool:
        """Move the selected box `step` mm in a direction (-1, 0 or 1 on each axis)."""
        item = self.selected_item()
        if item is None:
            return False
        new = self._moved(item.spec.box, dx * step, dy * step)
        if new == item.spec.box:
            return False
        item.set_box(new)
        self._update_a11y()
        self.view_changed.emit()
        self.box_changed.emit(item.spec.name, item.spec.index, new)
        return True

    def resize_selected(self, dx: int, dy: int, step: float) -> bool:
        """Grow (Right, Down) or shrink (Left, Up) the selected box by `step` mm at its right
        or bottom edge, kept on the sheet and at least MIN_BOX_MM."""
        item = self.selected_item()
        if item is None:
            return False
        x0, y0, x1, y1 = item.spec.box
        new = self._clamp((x0, y0, max(x0 + MIN_BOX_MM, x1 + dx * step),
                           max(y0 + MIN_BOX_MM, y1 + dy * step)))
        if new == item.spec.box:
            return False
        item.set_box(new)
        self._update_a11y()
        self.view_changed.emit()
        self.box_changed.emit(item.spec.name, item.spec.index, new)
        return True

    def place_default_box(self) -> Box | None:
        """The keyboard's "draw": a DEFAULT_BOX_MM box centred on the last pointer position
        over the sheet, else on the middle of the view. Emits box_drawn like a drag does."""
        if not self.has_page():
            return None
        width, height = DEFAULT_BOX_MM
        centre = self._last_mm
        if centre is None:
            middle = self.mapToScene(self.viewport().rect().center())
            centre = (self._mm(middle.x()), self._mm(middle.y()))
        cx, cy = centre
        box = self._clamp(self._moved((cx - width / 2, cy - height / 2, cx + width / 2,
                                       cy + height / 2), 0, 0))
        page_w, page_h = self.page_mm()
        x0, y0, x1, y1 = box
        if x1 - x0 < width:  # the edge cut it: slide it back on the sheet
            x0, x1 = max(0.0, page_w - width), min(page_w, max(0.0, page_w - width) + width)
        if y1 - y0 < height:
            y0, y1 = max(0.0, page_h - height), min(page_h, max(0.0, page_h - height) + height)
        box = (round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2))
        self.box_drawn.emit(box)
        return box

    def focusInEvent(self, event) -> None:  # noqa: N802
        super().focusInEvent(event)
        self._keyboard = event.reason() in KEYBOARD_REASONS
        self._mark_selection()
        self.focus_changed.emit(True)

    def focusOutEvent(self, event) -> None:  # noqa: N802
        super().focusOutEvent(event)
        self._space = False
        self._mark_selection()
        self.focus_changed.emit(False)

    # -- view -------------------------------------------------------------------------------
    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self._page is not None and self._auto:
            self.refit()  # not once the user has zoomed
        self.view_changed.emit()

    def scrollContentsBy(self, dx: int, dy: int) -> None:  # noqa: N802
        super().scrollContentsBy(dx, dy)
        self.view_changed.emit()

    def _restyle(self) -> None:
        self.scene().update()
        self.viewport().update()
        self.view_changed.emit()
