"""Painted pieces of the Kontrol tab (direction A, final-a/kontrol.html): the manila guide tab
in the logo's trapezoid, the document lip, the orange rider, paper sheets, the separator tile.

Every colour and size comes from `theme.manager()`; nothing here holds a colour literal.
The timeline delegate, the timeline view, the overview strip and the inspector all draw with
these helpers, so a guide tab or a rider looks the same wherever it appears.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from evrakci.ui import icons, theme

# Cut kind -> (Lucide icon, colour role). "start" (the job's first document) has no cut.
CUT_ICONS = {"qr": ("qr-code", "cut-qr"), "filter": ("funnel", "cut-filter"),
             "manual": ("scissors", "cut-manual")}
CUT_WORDS = {"qr": "QR ayıraç", "filter": "Filtre", "manual": "Elle kesim", "start": "İşin başı"}
TAB_SLANT = 8  # A .gtab clip-path: 8 px slants
TAB_RADIUS = 3  # A .gtab::before border-radius 3px 3px 0 0
TAB_PAD_L, TAB_PAD_R, TAB_GAP = 14, 16, 6  # A .gtab padding 0 16 0 14, gap 6
TAB_ICON = 14
RIDER_ICON = 14
RIDER_PAD_L = 6  # A .rider padding 0 s2 0 6px
LIP_H = 6  # A .lip
BIN = 40  # A .slot.del .bin
BADGE = 22  # A .slot.sel .chk


def hc() -> bool:
    return theme.manager().theme() == "hc"


def _pix(name: str, role: str, size: int, stroke: float = 1.75):
    return icons.pixmap(name, theme.manager().hex(role), size, 2.0, stroke)


# -- rider ------------------------------------------------------------------------------------
def rider_size() -> QSize:
    """A .rider: 22 px high, padding 0 s2 0 6, warn icon 14, gap s1, "Kontrol" caption 600."""
    m = theme.manager()
    text = QFontMetrics(m.font("caption-strong")).horizontalAdvance("Kontrol")
    return QSize(RIDER_PAD_L + RIDER_ICON + m.size("s1") + text + m.size("s2"),
                 m.size("rider-h"))


def paint_rider(painter: QPainter, rect: QRectF) -> None:
    """The orange kontrol rider: never without its icon and the word (D1)."""
    m = theme.manager()
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    edge = 2 if hc() else 1
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(m.color("rider-edge"))
    painter.drawRoundedRect(rect, 3, 3)
    painter.setBrush(m.color("rider"))
    painter.drawRoundedRect(rect.adjusted(edge, edge, -edge, -edge), 3 - edge / 2, 3 - edge / 2)
    icon = QRectF(rect.x() + RIDER_PAD_L, rect.center().y() - RIDER_ICON / 2, RIDER_ICON,
                  RIDER_ICON)
    painter.drawPixmap(icon, _pix("triangle-alert", "rider-ink", RIDER_ICON, 2.2),
                       QRectF(0, 0, 2 * RIDER_ICON, 2 * RIDER_ICON))
    painter.setFont(m.font("caption-strong"))
    painter.setPen(m.color("rider-ink"))
    left = icon.right() + m.size("s1")
    painter.drawText(QRectF(left, rect.y(), rect.right() - left, rect.height()),
                     Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "Kontrol")
    painter.restore()


class RiderLabel(QWidget):
    """The rider as a widget (inspector head, loupe); accessible as "Kontrol gerekiyor"."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setAccessibleName("Kontrol gerekiyor")
        self.setToolTip("Bu belge kontrol bekliyor")

    def sizeHint(self) -> QSize:  # noqa: N802
        return rider_size()

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        return rider_size()

    def paintEvent(self, _event) -> None:  # noqa: N802
        size = rider_size()
        rect = QRectF(0, (self.height() - size.height()) / 2, size.width(), size.height())
        paint_rider(QPainter(self), rect)


# -- guide tab and lip ------------------------------------------------------------------------
def guide_tab_size(number: int, kind: str | None, reviewed: bool) -> QSize:
    m = theme.manager()
    text = QFontMetrics(m.font("caption-strong")).horizontalAdvance(str(number))
    width = TAB_PAD_L + text + TAB_PAD_R
    if kind in CUT_ICONS:
        width += TAB_ICON + TAB_GAP
    if reviewed:
        width += TAB_GAP + TAB_ICON
    return QSize(width, tab_height())


def tab_height() -> int:
    """A .gtab is 26 px at 100 %: the caption line + 8."""
    return max(26, theme.manager().size("lh-caption") + 8)


def _trapezoid(rect: QRectF, inset: float = 0.0) -> QPainterPath:
    """The logo's tab: 8 px slants, 3 px top corners, open bottom edge."""
    left, right = rect.left() + inset, rect.right() - inset
    top, bottom = rect.top() + inset, rect.bottom()
    slant = TAB_SLANT - inset * 0.4
    r = max(0.0, TAB_RADIUS - inset)
    path = QPainterPath()
    path.moveTo(left, bottom)
    path.lineTo(left + slant - r * 0.3, top + r)
    path.quadTo(left + slant, top, left + slant + r, top)
    path.lineTo(right - slant - r, top)
    path.quadTo(right - slant, top, right - slant + r * 0.3, top + r)
    path.lineTo(right, bottom)
    path.closeSubpath()
    return path


def paint_guide_tab(painter: QPainter, rect: QRectF, kind: str | None, number: int,
                    reviewed: bool) -> None:
    """A .gtab: manila-edge outline, manila fill, cut pictogram + number + reviewed check."""
    m = theme.manager()
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.fillPath(_trapezoid(rect), m.color("manila-edge"))
    painter.fillPath(_trapezoid(rect.adjusted(0, 0, 0, 1), 1.0), m.color("manila"))
    x = rect.x() + TAB_PAD_L
    mid = rect.center().y()
    if kind in CUT_ICONS:
        name, role = CUT_ICONS[kind]
        painter.drawPixmap(QRectF(x, mid - TAB_ICON / 2, TAB_ICON, TAB_ICON),
                           _pix(name, role, TAB_ICON, 2.2),
                           QRectF(0, 0, 2 * TAB_ICON, 2 * TAB_ICON))
        x += TAB_ICON + TAB_GAP
    font = m.font("caption-strong")
    painter.setFont(font)
    painter.setPen(m.color("manila-ink"))
    text = str(number)
    width = QFontMetrics(font).horizontalAdvance(text)
    painter.drawText(QRectF(x, rect.y(), width + 2, rect.height()),
                     Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)
    if reviewed:
        x += width + TAB_GAP
        painter.drawPixmap(QRectF(x, mid - TAB_ICON / 2, TAB_ICON, TAB_ICON),
                           _pix("circle-check", "on-manila-ok", TAB_ICON, 2.2),
                           QRectF(0, 0, 2 * TAB_ICON, 2 * TAB_ICON))
    painter.restore()


def paint_lip(painter: QPainter, rect: QRectF, kind: str | None) -> None:
    """A .lip: a 6 px manila band; its top line tells the cut (solid 2 px QR, dashed filter,
    dotted 2 px manual, 1 px for the job's first document)."""
    m = theme.manager()
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(rect.adjusted(0, 0, 0, 2), 2, 2)
    painter.setClipRect(rect)
    painter.fillPath(path, m.color("manila"))
    painter.setClipping(False)
    width = 2 if kind in ("qr", "manual") else 1
    pen = QPen(m.color("manila-edge"), width)
    pen.setCapStyle(Qt.PenCapStyle.FlatCap)
    if kind == "filter":
        pen.setStyle(Qt.PenStyle.DashLine)
    elif kind == "manual":
        pen.setStyle(Qt.PenStyle.DotLine)
    painter.setPen(pen)
    y = rect.top() + width / 2
    painter.drawLine(QPointF(rect.left() + 1, y), QPointF(rect.right() - 1, y))
    painter.restore()


# -- paper ------------------------------------------------------------------------------------
def paint_paper(painter: QPainter, rect: QRectF, dim: float = 1.0) -> None:
    """A .pg: paper, 1 px page edge and the paper shadow (hc: a 1 px stroke, no shadow)."""
    m = theme.manager()
    radius = m.size("r-paper")
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    if not hc():
        for layer in m.shadow("shadow-paper"):
            if layer.inset:
                continue
            colour = QColor(layer.color)
            colour.setAlphaF(colour.alphaF() * dim)
            painter.setBrush(colour)
            grow = layer.spread + layer.blur / 4
            painter.drawRoundedRect(rect.translated(layer.x, layer.y).adjusted(
                -grow, -grow, grow, grow), radius + grow, radius + grow)
    edge = m.color("stroke" if hc() else "page-edge")
    painter.setBrush(edge)
    painter.drawRoundedRect(rect.adjusted(-1, -1, 1, 1), radius + 1, radius + 1)
    paper = m.color("paper")
    if dim < 1.0:  # A .slot.del .pg: opacity .38 over the layer
        layer_colour = m.color("layer")
        paper = QColor.fromRgbF(*(dim * a + (1 - dim) * b for a, b in zip(
            paper.getRgbF()[:3], layer_colour.getRgbF()[:3], strict=True)))
    painter.setBrush(paper)
    painter.drawRoundedRect(rect, radius, radius)
    painter.restore()


def paint_placeholder(painter: QPainter, rect: QRectF, row: int, dim: float = 1.0) -> None:
    """A's paper drawing (.h, .h2, .lines) until the scan's thumbnail arrives; the pattern
    varies with the page so a row of placeholders does not look like one repeated page."""
    m = theme.manager()
    painter.save()
    painter.setOpacity(dim)
    s = rect.width() / 148.0
    x, y = rect.x() + 14 * s, rect.y() + 16 * s
    w = rect.width() - 28 * s
    head, line = m.color("paper-head"), m.color("paper-line")
    if row % 3 != 2:
        painter.fillRect(QRectF(x, y, w * 0.58, max(2.0, 6 * s)), head)
        y += 15 * s
    painter.fillRect(QRectF(x, y, w * 0.34, max(1.0, 4 * s)), line)
    y += 13 * s
    if row % 4 == 1:  # a table
        table = QRectF(x, y, w, 78 * s)
        painter.setPen(QPen(line, 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(table)
        for k in range(1, 6):
            painter.drawLine(QPointF(x, y + 13 * s * k), QPointF(x + w, y + 13 * s * k))
        for k in range(1, 4):
            painter.drawLine(QPointF(x + w * k / 4, y), QPointF(x + w * k / 4, y + 78 * s))
        y += 87 * s
    bottom = rect.bottom() - 16 * s
    while y + 2 * s < bottom:
        painter.fillRect(QRectF(x, y, w * 0.92, max(1.0, 2 * s)), line)
        y += 8 * s
    painter.restore()


def paint_separator(painter: QPainter, rect: QRectF, position: int) -> None:
    """A .sepage: a narrow well tile with the QR pictogram and "Ayraç 76" written upwards."""
    m = theme.manager()
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(m.color("stroke"), 1) if hc() else Qt.PenStyle.NoPen)
    painter.setBrush(m.color("well"))
    painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), m.size("r-paper"),
                            m.size("r-paper"))
    size = m.size("icon-md")
    font = m.font("caption-num")
    text = f"Ayraç {position}"
    text_w = QFontMetrics(font).horizontalAdvance(text)
    gap = m.size("s3")
    total = size + gap + text_w
    top = rect.center().y() - total / 2
    painter.drawPixmap(QRectF(rect.center().x() - size / 2, top, size, size),
                       _pix("qr-code", "text-2", size), QRectF(0, 0, 2 * size, 2 * size))
    painter.setFont(font)
    painter.setPen(m.color("text-2"))
    painter.translate(rect.center().x(), top + size + gap + text_w)
    painter.rotate(-90)
    line = QFontMetrics(font).height()
    painter.drawText(QRectF(0, -line / 2, text_w + 2, line),
                     Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)
    painter.restore()


def paint_bin(painter: QPainter, centre: QPointF) -> None:
    """A .slot.del .bin: a card disc with the danger bin, over a page that will be deleted."""
    m = theme.manager()
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    rect = QRectF(centre.x() - BIN / 2, centre.y() - BIN / 2, BIN, BIN)
    if hc():
        painter.setPen(QPen(m.color("stroke"), 1))
    else:
        painter.setPen(Qt.PenStyle.NoPen)
        for layer in m.shadow("shadow-paper"):
            if not layer.inset:
                painter.setBrush(layer.color)
                painter.drawEllipse(rect.translated(layer.x, layer.y).adjusted(-1, -1, 1, 1))
    painter.setBrush(m.color("card"))
    painter.drawEllipse(rect)
    size = m.size("icon-md")
    painter.drawPixmap(QRectF(centre.x() - size / 2, centre.y() - size / 2, size, size),
                       _pix("trash-2", "danger", size), QRectF(0, 0, 2 * size, 2 * size))
    painter.restore()


def paint_hatch(painter: QPainter, rect: QRectF) -> None:
    """High contrast deleted page: Window with a GrayText edge and a GrayText hatch."""
    m = theme.manager()
    grey = m.color("text-disabled")
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.fillRect(rect, m.color("layer"))
    painter.setClipRect(rect)
    painter.setPen(QPen(grey, 1))
    step = 10.0
    x = rect.left() - rect.height()
    while x < rect.right():
        painter.drawLine(QPointF(x, rect.bottom()), QPointF(x + rect.height(), rect.top()))
        x += step
    painter.setClipping(False)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRect(rect.adjusted(0.5, 0.5, -0.5, -0.5))
    painter.restore()


def paint_check_badge(painter: QPainter, centre: QPointF) -> None:
    """A .slot.sel .chk: a 22 px accent disc with a 2 px layer ring and a white check."""
    m = theme.manager()
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(m.color("layer"))
    painter.drawEllipse(centre, BADGE / 2 + 2, BADGE / 2 + 2)
    painter.setBrush(m.color("accent"))
    painter.drawEllipse(centre, BADGE / 2, BADGE / 2)
    size = 14
    painter.drawPixmap(QRectF(centre.x() - size / 2, centre.y() - size / 2, size, size),
                       _pix("check", "text-on-accent", size, 3.0), QRectF(0, 0, 2 * size, 2 * size))
    painter.restore()
