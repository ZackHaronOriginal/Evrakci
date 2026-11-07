"""The Kontrol timeline: every page in order, each document starting under a manila guide tab.

The cut type is shown by the tab's position and pictogram first, then by colour:
QR on the left (solid line), filter in the centre (dashed), manual on the right (scissors).
"""

from __future__ import annotations

from enum import IntEnum

from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QPersistentModelIndex,
    QPointF,
    QRect,
    QRectF,
    QSize,
    Qt,
)
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import QAbstractItemView, QListView, QStyle, QStyledItemDelegate

from evrakci.ui import theme
from evrakci.ui.controller import JobController
from evrakci.ui.thumbnails import ThumbnailService

PAGE_W = 84
SHEET_H = 116
TAB_H = 44
GAP = 8  # between pages of one document
CUT_W = 30  # the gap before a document that a cut starts
ITEM_H = TAB_H + 12 + SHEET_H + 28


class Roles(IntEnum):
    PID = Qt.ItemDataRole.UserRole + 1
    DOC = Qt.ItemDataRole.UserRole + 2  # document number (1-based) or 0
    CUT = Qt.ItemDataRole.UserRole + 3  # "qr" | "filter" | "manual" | "start" on a first page
    STATE = Qt.ItemDataRole.UserRole + 4  # "page" | "separator" | "deleted" | "dropped"
    TEMPLATE = Qt.ItemDataRole.UserRole + 5
    CHECK = Qt.ItemDataRole.UserRole + 6  # the document needs a check
    PAGE_NO = Qt.ItemDataRole.UserRole + 7


class TimelineModel(QAbstractListModel):
    def __init__(self, controller: JobController, templates=dict) -> None:
        super().__init__()
        self.controller = controller
        self.templates = templates  # callable returning {template id: Template}
        self.checks: dict[int, list[str]] = {}
        self._rebuild()
        controller.job_changed.connect(self.refresh)

    def refresh(self) -> None:
        self.beginResetModel()
        self._rebuild()
        self.endResetModel()

    def set_checks(self, checks: dict[int, list[str]]) -> None:
        self.checks = checks
        if self._pids:
            self.dataChanged.emit(self.index(0), self.index(len(self._pids) - 1))

    def _rebuild(self) -> None:
        job = self.controller.job
        self._pids = job.ordered_page_ids()
        self._doc_of: dict[str, int] = {}
        for number, document in enumerate(self.controller.documents(), start=1):
            for pid in document.page_ids:
                self._doc_of[pid] = number
        self._kinds = self.controller.cut_kinds()
        templates = self.templates()
        self._template_of: dict[str, str] = {}
        for application in job.templates:
            template = templates.get(application.template_id)
            name = template.name if template is not None else application.template_id
            for pid in application.page_ids:
                self._template_of[pid] = name

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(self._pids)

    def page_id(self, row: int) -> str:
        return self._pids[row]

    def row_of(self, pid: str) -> int:
        return self._pids.index(pid)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        pid = self._pids[index.row()]
        job = self.controller.job
        doc = self._doc_of.get(pid, 0)
        if role == Roles.PID:
            return pid
        if role == Roles.PAGE_NO:
            return index.row() + 1
        if role == Roles.DOC:
            return doc
        if role == Roles.CUT:
            return self._kinds.get(pid)
        if role == Roles.STATE:
            if job.pages[pid].is_separator:
                return "separator"
            if pid in job.deleted:
                return "deleted"
            if doc == 0:
                return "dropped"
            return "page"
        if role == Roles.TEMPLATE:
            return self._template_of.get(pid)
        if role == Roles.CHECK:
            return bool(self.checks.get(doc))
        if role == Qt.ItemDataRole.ToolTipRole:
            return f"Sayfa {index.row() + 1}" + (f" · Belge {doc}" if doc else "")
        return None


def _qr_icon(painter: QPainter, x: float, y: float, colour: QColor) -> None:
    painter.setPen(QPen(colour, 1.6))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    for dx, dy in ((0, 0), (8, 0), (0, 8)):
        painter.drawRect(QRectF(x + dx, y + dy, 5, 5))
    painter.fillRect(QRectF(x + 9, y + 9, 4, 4), colour)


def _funnel_icon(painter: QPainter, x: float, y: float, colour: QColor) -> None:
    painter.setPen(QPen(colour, 1.6))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawPolygon(
        QPolygonF([QPointF(x, y), QPointF(x + 13, y), QPointF(x + 8, y + 6),
                   QPointF(x + 8, y + 12), QPointF(x + 5, y + 13), QPointF(x + 5, y + 6)])
    )


def _scissors_icon(painter: QPainter, x: float, y: float, colour: QColor) -> None:
    painter.setPen(QPen(colour, 1.6))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(QPointF(x + 3, y + 3), 2.5, 2.5)
    painter.drawEllipse(QPointF(x + 3, y + 11), 2.5, 2.5)
    painter.drawLine(QPointF(x + 5, y + 5), QPointF(x + 13, y + 13))
    painter.drawLine(QPointF(x + 5, y + 9), QPointF(x + 13, y + 1))


ICONS = {"qr": _qr_icon, "filter": _funnel_icon, "manual": _scissors_icon}


class TimelineDelegate(QStyledItemDelegate):
    def __init__(self, thumbnails: ThumbnailService | None = None, parent=None) -> None:
        super().__init__(parent)
        self.thumbnails = thumbnails

    @staticmethod
    def cut_before(index) -> str | None:
        kind = index.data(Roles.CUT)
        return kind if kind in ("qr", "filter", "manual") else None

    def sizeHint(self, option, index) -> QSize:
        extra = CUT_W if self.cut_before(index) else 0
        return QSize(PAGE_W + GAP + extra, ITEM_H)

    def paint(self, painter: QPainter, option, index) -> None:
        t = theme.TOKENS
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect: QRect = option.rect
        kind = self.cut_before(index)
        x0 = rect.x() + (CUT_W if kind else 0)
        state = index.data(Roles.STATE)
        doc = index.data(Roles.DOC)
        top = rect.y() + TAB_H + 12
        page = QRectF(x0, top, PAGE_W, SHEET_H)

        if kind:  # the cut line and its pictogram badge, in the gap before the page
            colour = QColor(t[kind])
            pen = QPen(colour, 2)
            if kind == "filter":
                pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            cx = rect.x() + CUT_W / 2
            painter.drawLine(QPointF(cx, top + 26), QPointF(cx, top + SHEET_H))
            badge = QRectF(cx - 11, top, 22, 22)
            painter.setBrush(QColor(t["ground"]))
            painter.setPen(QPen(colour, 1.5))
            if kind == "manual":
                painter.drawRoundedRect(badge, 3, 3)
            else:
                painter.drawEllipse(badge)
            ICONS[kind](painter, badge.x() + 4, badge.y() + 4, colour)

        if doc:  # manila page-edge strip under every page of a document
            edge = QRectF(rect.x() + (CUT_W if kind else 0), top - 9, PAGE_W + GAP, 6)
            painter.fillRect(edge, QColor(t["manila"]))
            if index.data(Roles.CUT):  # first page: the guide tab
                self._tab(painter, index, QRectF(x0, rect.y() + 4, PAGE_W + GAP, TAB_H - 4))

        self._sheet(painter, index, page, state, option)
        painter.restore()

    def _tab(self, painter: QPainter, index, area: QRectF) -> None:
        t = theme.TOKENS
        kind = index.data(Roles.CUT)
        width = min(area.width() * 0.9, 120)
        if kind == "filter":
            x = area.x() + (area.width() - width) / 2
        elif kind == "manual":
            x = area.right() - width
        else:
            x = area.x()
        tab = QRectF(x, area.y() + 8, width, area.height() - 8)
        path = QPainterPath()
        path.addRoundedRect(tab.adjusted(0, 0, 0, 8), 7, 7)
        painter.save()
        painter.setClipRect(tab)
        painter.fillPath(path, QColor(t["manila"]))
        pen = QPen(QColor(t["filter"] if kind == "filter" else t["manila_edge"]), 1.2)
        if kind == "filter":
            pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawPath(path)
        painter.restore()
        if kind in ICONS:
            ICONS[kind](painter, tab.x() + 6, tab.y() + 6, QColor(t[kind]))
        font = QFont(theme.FONT_FAMILY)
        font.setPixelSize(theme.SMALL)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(t["manila_ink"]))
        painter.drawText(QRectF(tab.x() + 24, tab.y() + 3, tab.width() - 26, 18),
                         Qt.AlignmentFlag.AlignVCenter, f"Belge {index.data(Roles.DOC)}")
        if index.data(Roles.CHECK):  # the orange signal rider, always with text
            rider = QRectF(tab.x() + 6, area.y() - 4, 64, 17)
            painter.setBrush(QColor(t["rider"]))
            painter.setPen(QPen(QColor(t["rider_edge"]), 1))
            painter.drawRoundedRect(rider, 3, 3)
            painter.setPen(QColor(t["rider_ink"]))
            painter.drawText(rider, Qt.AlignmentFlag.AlignCenter, "Kontrol")

    def _sheet(self, painter: QPainter, index, page: QRectF, state: str, option) -> None:
        t = theme.TOKENS
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        focused = bool(option.state & QStyle.StateFlag.State_HasFocus)
        pid = index.data(Roles.PID)
        painter.setBrush(QColor(t["paper"]))
        border = QPen(QColor(t["shell"] if selected else "#b8c1bb"), 2 if selected else 1)
        if state in ("deleted", "dropped"):
            border.setStyle(Qt.PenStyle.DashLine)
            painter.setBrush(QColor("#f3f4f1"))
        painter.setPen(border)
        painter.drawRect(page)
        image = self.thumbnails.cache.get(pid) if self.thumbnails else None
        if state == "separator":
            painter.setPen(QColor(t["qr"]))
            _qr_icon(painter, page.center().x() - 7, page.y() + 36, QColor(t["ink"]))
            font = QFont(theme.FONT_FAMILY)
            font.setPixelSize(theme.SMALL)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor(t["qr"]))
            painter.drawText(page.adjusted(0, 40, 0, 0), Qt.AlignmentFlag.AlignCenter, "AYIRAÇ")
        elif state in ("deleted", "dropped"):
            font = QFont(theme.FONT_FAMILY)
            font.setPixelSize(theme.SMALL)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor(t["ink_2"]))
            label = "silindi" if state == "deleted" else "boş"
            painter.drawText(page, Qt.AlignmentFlag.AlignCenter, label)
        elif image is not None and not image.isNull():
            target = page.adjusted(2, 2, -2, -2)
            painter.drawImage(target, image)
        else:  # placeholder lines until the thumbnail arrives
            painter.fillRect(QRectF(page.x() + 10, page.y() + 10, 38, 6), QColor("#cfd5d1"))
            for line in range(7):
                painter.fillRect(QRectF(page.x() + 10, page.y() + 26 + line * 11, 58, 3),
                                 QColor("#dde2de"))
        if self.thumbnails is not None and state == "page" and image is None:
            self.thumbnails.request(pid)
        if focused:
            painter.setPen(QPen(QColor(t["focus"]), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(page.adjusted(-4, -4, 4, 4))
        number = QRectF(page.x(), page.bottom() + 5, PAGE_W, 20)
        font = QFont(theme.FONT_FAMILY)
        font.setPixelSize(14)
        font.setBold(True)
        painter.setFont(font)
        if selected:
            painter.fillRect(number, QColor(t["shell"]))
            painter.setPen(QColor(t["on_shell"]))
        else:
            painter.setPen(QColor(t["ink"]))
        painter.drawText(number, Qt.AlignmentFlag.AlignCenter, str(index.data(Roles.PAGE_NO)))


class TimelineView(QListView):
    """A horizontal strip of pages, with range selection (Shift / Ctrl), like a video editor."""

    def __init__(self, thumbnails: ThumbnailService | None = None, parent=None) -> None:
        super().__init__(parent)
        self.thumbnails = thumbnails
        self.setFlow(QListView.Flow.LeftToRight)
        self.setWrapping(False)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setItemDelegate(TimelineDelegate(thumbnails, self))
        self.setMinimumHeight(ITEM_H + 24)
        self.setSpacing(0)
        self.setUniformItemSizes(False)
        self.setObjectName("timeline")
        if thumbnails is not None:
            thumbnails.ready.connect(self._thumbnail_ready)
            self.horizontalScrollBar().valueChanged.connect(self._forget_hidden)

    def visible_rows(self) -> range:
        model = self.model()
        if model is None or model.rowCount() == 0:
            return range(0)
        first = self.indexAt(self.viewport().rect().topLeft() + QPointF(1, ITEM_H / 2).toPoint())
        last = self.indexAt(self.viewport().rect().topRight() + QPointF(-1, ITEM_H / 2).toPoint())
        start = first.row() if first.isValid() else 0
        end = last.row() if last.isValid() else model.rowCount() - 1
        return range(start, end + 1)

    def _forget_hidden(self) -> None:
        model = self.model()
        rows = self.visible_rows()
        self.thumbnails.keep_only({model.data(model.index(r), Roles.PID) for r in rows})

    def _thumbnail_ready(self, pid: str, image) -> None:
        model = self.model()
        if model is None:
            return
        try:
            row = model.row_of(pid)
        except ValueError:
            return
        self.update(model.index(row))
