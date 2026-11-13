"""The Kontrol timeline (direction A): documents filed as stacks of pages under manila guide tabs.

Each document is a group: a guide tab in the logo's trapezoid (QR on the left, filter in the
centre, manual on the right, so the cut is clear in greyscale), the manila lip whose top line is
solid / dashed / dotted, and its pages. Documents flow left to right and wrap to the next row;
a document is split over rows only when it is wider than a row. Separator pages are narrow
tiles between documents; pages that will be deleted stay in their document, dimmed.

Smooth at 1,000 pages: the view is one QListView with its own flow layout (plain rectangles,
computed in one pass), it paints only the rows in view, every page through the delegate, and
asks the thumbnail service only for the pages it paints.
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass, field
from enum import IntEnum

from PySide6.QtCore import (
    QAbstractListModel,
    QItemSelection,
    QItemSelectionModel,
    QModelIndex,
    QPersistentModelIndex,
    QPoint,
    QPointF,
    QRect,
    QRectF,
    QSize,
    Qt,
)
from PySide6.QtGui import QColor, QFontMetrics, QImage, QPainter, QPen, QRegion
from PySide6.QtWidgets import (
    QAbstractItemView,
    QListView,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
)

from evrakci.ui import kontrol_paint as kp
from evrakci.ui import style, theme
from evrakci.ui.controller import JobController
from evrakci.ui.thumbnails import ThumbnailService

SEP_W = 48  # A .sepage
DOC_GAP = 28  # A .row gap between documents
ZOOM_MIN, ZOOM_MAX, ZOOM_STEP = 50, 200, 10


class Roles(IntEnum):
    PID = Qt.ItemDataRole.UserRole + 1
    DOC = Qt.ItemDataRole.UserRole + 2  # document number (1-based) or 0
    CUT = Qt.ItemDataRole.UserRole + 3  # "qr" | "filter" | "manual" | "start" on a first page
    STATE = Qt.ItemDataRole.UserRole + 4  # "page" | "separator" | "deleted" | "dropped"
    TEMPLATE = Qt.ItemDataRole.UserRole + 5
    CHECK = Qt.ItemDataRole.UserRole + 6  # the document needs a check
    PAGE_NO = Qt.ItemDataRole.UserRole + 7
    REVIEWED = Qt.ItemDataRole.UserRole + 8  # the document was approved (İncelendi)


@dataclass(slots=True)
class Group:
    """Consecutive rows drawn as one unit: a document, a separator, or loose pages."""

    kind: str  # "doc" | "sep" | "loose"
    first: int
    last: int
    doc: int = 0
    cut: str | None = None


class TimelineModel(QAbstractListModel):
    """Every page of the job in order; documents, cuts and states from the core."""

    def __init__(self, controller: JobController, templates=dict) -> None:
        super().__init__()
        self.controller = controller
        self.templates = templates  # callable returning {template id: Template}
        self.checks: dict[int, list[str]] = {}
        self.reviewed: set[int] = set()
        self._rebuild()
        controller.job_changed.connect(self.refresh)

    def refresh(self) -> None:
        self.beginResetModel()
        self._rebuild()
        self.endResetModel()

    def set_checks(self, checks: dict[int, list[str]]) -> None:
        self.checks = checks
        self._changed_all()

    def set_reviewed(self, numbers: set[int]) -> None:
        self.reviewed = set(numbers)
        self._changed_all()

    def _changed_all(self) -> None:
        if self._pids:
            self.dataChanged.emit(self.index(0), self.index(len(self._pids) - 1))

    def _rebuild(self) -> None:
        job = self.controller.job
        self._pids = job.ordered_page_ids()
        self._row: dict[str, int] = {pid: row for row, pid in enumerate(self._pids)}
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
        self._states = [self._state(pid) for pid in self._pids]
        self._groups = self._make_groups()

    def _state(self, pid: str) -> str:
        job = self.controller.job
        if job.pages[pid].is_separator:
            return "separator"
        if pid in job.deleted:
            return "deleted"
        if self._doc_of.get(pid, 0) == 0:
            return "dropped"
        return "page"

    def _make_groups(self) -> list[Group]:
        groups: list[Group] = []
        for row, pid in enumerate(self._pids):
            state, doc = self._states[row], self._doc_of.get(pid, 0)
            last = groups[-1] if groups else None
            if state == "separator":
                groups.append(Group("sep", row, row))
            elif doc:
                if last is not None and last.kind == "doc" and last.doc == doc:
                    last.last = row
                else:
                    groups.append(Group("doc", row, row, doc, self._kinds.get(pid)))
            elif last is not None and last.kind in ("doc", "loose"):
                last.last = row  # a page to delete stays where it was filed
            else:
                groups.append(Group("loose", row, row))
        return groups

    # Reading
    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(self._pids)

    def groups(self) -> list[Group]:
        return self._groups

    def page_id(self, row: int) -> str:
        return self._pids[row]

    def row_of(self, pid: str) -> int:
        try:
            return self._row[pid]
        except KeyError:
            raise ValueError(pid) from None

    def state(self, row: int) -> str:
        return self._states[row]

    def doc_of_row(self, row: int) -> int:
        return self._doc_of.get(self._pids[row], 0)

    def document_rows(self, number: int) -> range:
        """Rows of the pages of document `number` (first to last page, deleted ones too)."""
        for group in self._groups:
            if group.kind == "doc" and group.doc == number:
                return range(group.first, group.last + 1)
        return range(0)

    def first_row(self, number: int) -> int:
        rows = self.document_rows(number)
        return rows.start if rows else -1

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        pid = self._pids[row]
        doc = self._doc_of.get(pid, 0)
        if role == Roles.PID:
            return pid
        if role == Roles.PAGE_NO:
            return row + 1
        if role == Roles.DOC:
            return doc
        if role == Roles.CUT:
            return self._kinds.get(pid)
        if role == Roles.STATE:
            return self._states[row]
        if role == Roles.TEMPLATE:
            return self._template_of.get(pid)
        if role == Roles.CHECK:
            return bool(self.checks.get(doc))
        if role == Roles.REVIEWED:
            return doc in self.reviewed
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole,
                    Qt.ItemDataRole.AccessibleTextRole):
            return self.describe(row)
        return None

    def describe(self, row: int) -> str:
        """"Sayfa 73, Belge 16, kontrol gerekiyor" (tooltip and screen reader text)."""
        state = self._states[row]
        if state == "separator":
            return f"Sayfa {row + 1}, QR ayıraç"
        doc = self._doc_of.get(self._pids[row], 0)
        parts = [f"Sayfa {row + 1}"]
        if doc:
            parts.append(f"Belge {doc}")
            if self.checks.get(doc):
                parts.append("kontrol gerekiyor")
            parts.append("incelendi" if doc in self.reviewed else "incelenmedi")
        if state == "deleted":
            parts.append("silinecek")
        elif state == "dropped":
            parts.append("boş sayfa, dışa aktarılmaz")
        return ", ".join(parts)


# -- geometry -----------------------------------------------------------------------------------
@dataclass(frozen=True)
class Metrics:
    """A's timeline sizes at a zoom percentage (pages scale, chrome follows the text size)."""

    page_w: int
    page_h: int
    sep_w: int
    gap: int  # between the pages of one document (A .pages gap s3)
    doc_gap: int
    pad_top: int
    pad_x: int
    row_gap: int
    tab_h: int
    lip_h: int
    lip_gap: int  # lip to pages (A .pages padding-top s3)
    caption_h: int

    @property
    def header(self) -> int:
        return self.tab_h + self.lip_h + self.lip_gap

    @property
    def row_h(self) -> int:
        return self.header + self.page_h + self.caption_h

    @staticmethod
    def at(zoom: int) -> Metrics:
        m = theme.manager()
        scale = zoom / 100
        return Metrics(
            page_w=round(m.size("thumb-w") * scale), page_h=round(m.size("thumb-h") * scale),
            sep_w=max(32, round(SEP_W * scale)), gap=m.size("s3"), doc_gap=DOC_GAP,
            pad_top=m.size("s4"), pad_x=m.size("s6"), row_gap=m.size("s6"),
            tab_h=kp.tab_height(), lip_h=kp.LIP_H, lip_gap=m.size("s3"),
            caption_h=m.size("lh-caption") + 10)  # A figcaption: 28 px (6 + 18 + 4)


@dataclass(slots=True)
class Segment:
    """The part of a group on one layout row."""

    group: int
    first: int
    last: int
    x0: int
    x1: int
    start: bool  # the group starts here (its guide tab is drawn on this segment)


@dataclass(slots=True)
class LayoutRow:
    y: int
    first: int
    last: int
    segments: list[Segment] = field(default_factory=list)


def flow(groups: list[Group], states: list[str], metrics: Metrics,
         width: int) -> tuple[list[QRect], list[LayoutRow], int]:
    """Place every page: (page rects in content coordinates, layout rows, content height)."""
    mt = metrics
    right = max(mt.pad_x + mt.page_w, width - mt.pad_x)
    rects: list[QRect] = [QRect()] * len(states)
    rows: list[LayoutRow] = []
    x = mt.pad_x
    y = mt.pad_top

    def new_row(first: int) -> LayoutRow:
        nonlocal x, y
        if rows:
            y += mt.row_h + mt.row_gap
        x = mt.pad_x
        row = LayoutRow(y, first, first)
        rows.append(row)
        return row

    for number, group in enumerate(groups):
        widths = [mt.sep_w if states[r] == "separator" else mt.page_w
                  for r in range(group.first, group.last + 1)]
        total = sum(widths) + mt.gap * (len(widths) - 1)
        row = rows[-1] if rows else new_row(group.first)
        if row.segments and x + total > right:
            row = new_row(group.first)
        start, seg = True, None
        for offset, w in enumerate(widths):
            r = group.first + offset
            if seg is not None and x + w > right:  # a document wider than a row goes on
                row = new_row(r)
                seg = None
            if seg is None:
                if row.segments:
                    x += mt.doc_gap
                seg = Segment(number, r, r, x, x, start)
                row.segments.append(seg)
                start = False
            else:
                x += mt.gap
            top = y + mt.header
            rects[r] = QRect(x, top, w, mt.page_h)
            x += w
            seg.last, seg.x1 = r, x
            row.last = r
    height = (y + mt.row_h + mt.pad_top) if rows else 0
    return rects, rows, height


# -- delegate -----------------------------------------------------------------------------------
class TimelineDelegate(QStyledItemDelegate):
    """Paints one page slot: paper (scan or placeholder), selection ring and check badge,
    focus ring, the page number under it; a separator tile; a page that will be deleted."""

    def __init__(self, thumbnails: ThumbnailService | None = None, parent=None) -> None:
        super().__init__(parent)
        self.thumbnails = thumbnails

    def sizeHint(self, option, index) -> QSize:
        view = self.parent()
        mt = view.metrics if isinstance(view, TimelineView) else Metrics.at(100)
        return QSize(mt.page_w, mt.page_h + mt.caption_h)

    def paint(self, painter: QPainter, option, index) -> None:
        m = theme.manager()
        view = self.parent()
        mt = view.metrics if isinstance(view, TimelineView) else Metrics.at(100)
        rect = QRectF(option.rect)
        state = index.data(Roles.STATE)
        page = QRectF(rect.x(), rect.y(), rect.width(), mt.page_h)
        row = index.row()
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        focused = bool(option.state & QStyle.StateFlag.State_HasFocus)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if state == "separator":
            kp.paint_separator(painter, page, row + 1)
        elif state in ("deleted", "dropped"):
            if kp.hc():
                kp.paint_hatch(painter, page)
            else:
                kp.paint_paper(painter, page, 0.38)
                self._scan(painter, index, page, row, 0.38)
            if state == "deleted":
                kp.paint_bin(painter, QPointF(page.center().x(), page.y() + 84 * mt.page_h / 209
                                              + 20))
        else:
            kp.paint_paper(painter, page)
            self._scan(painter, index, page, row, 1.0)
        radius = m.size("r-paper")
        if selected:  # A .slot.sel: 2 px accent ring with a 3 px layer gap + check badge
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(m.color("accent"), 2))
            painter.drawRoundedRect(page.adjusted(-4, -4, 4, 4), radius + 4, radius + 4)
            kp.paint_check_badge(painter, QPointF(page.x() + 3, page.y() + 3))
        if focused:  # A .slot.foc: D11 ring outside the selection ring
            style.paint_ring(painter, page.adjusted(-10, -10, 10, 10), radius + 8)
        if state != "separator":
            self._caption(painter, QRectF(page.x() - 8, page.bottom(), page.width() + 16,
                                          mt.caption_h), row, state, selected)
        painter.restore()

    def _scan(self, painter: QPainter, index, page: QRectF, row: int, dim: float) -> None:
        pid = index.data(Roles.PID)
        service = self.thumbnails
        image: QImage | None = service.cache.get(pid) if service is not None else None
        if service is not None and not service.is_current(pid):
            service.request(pid)
        if image is None or image.isNull():
            kp.paint_placeholder(painter, page, row, dim)
            return
        size = QSize(image.width(), image.height()).scaled(
            page.size().toSize(), Qt.AspectRatioMode.KeepAspectRatio)
        target = QRectF(page.center().x() - size.width() / 2, page.center().y()
                        - size.height() / 2, size.width(), size.height())
        painter.save()
        painter.setOpacity(dim)
        painter.drawImage(target, image)
        kp.tint_scan(painter, target)
        painter.restore()

    def _caption(self, painter: QPainter, rect: QRectF, row: int, state: str,
                 selected: bool) -> None:
        m = theme.manager()
        text = str(row + 1)
        if state == "deleted":
            text, font, colour = f"{text} Silinecek", m.font("caption-strong"), "danger"
        elif state == "dropped":
            text, font, colour = f"{text} Boş", m.font("caption-num"), "text-2"
        elif selected:
            font, colour = m.font("caption-strong"), "text-accent"
        else:
            font, colour = m.font("caption-num"), "text-2"
        painter.setFont(font)
        painter.setPen(m.color(colour))
        line = QFontMetrics(font).height()
        painter.drawText(QRectF(rect.x(), rect.y() + 6, rect.width(), line),
                         Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, text)


# -- view ---------------------------------------------------------------------------------------
class TimelineView(QListView):
    """The working timeline: A's flow layout, page selection (click, Shift/Ctrl, rubber band),
    arrow keys, Home/End and PgUp/PgDn; Ctrl+wheel zooms through the screen's ZoomController."""

    def __init__(self, thumbnails: ThumbnailService | None = None, parent=None) -> None:
        self.zoom = 100
        self.metrics = Metrics.at(100)
        self._rects: list[QRect] = []
        self._rows: list[LayoutRow] = []
        self._row_tops: list[int] = []
        self._height = 0
        self._laid_width = -1
        self._band: QRect | None = None
        self._press: QPoint | None = None
        super().__init__(parent)
        self.thumbnails = thumbnails
        self.setObjectName("timeline")
        self.setAccessibleName("Sayfalar")
        self.setAccessibleDescription(
            "Belgeler sırayla. Oklar sayfa değiştirir, Shift ile seçim genişler, "
            "Boşluk önizler, Enter belgeyi onaylar.")
        self.setViewMode(QListView.ViewMode.ListMode)
        self.setLayoutMode(QListView.LayoutMode.SinglePass)
        self.setUniformItemSizes(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSelectionRectVisible(False)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setFrameShape(QListView.Shape.NoFrame)
        self.setItemDelegate(TimelineDelegate(thumbnails, self))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        if thumbnails is not None:
            thumbnails.ready.connect(self._thumbnail_ready)
            self.verticalScrollBar().valueChanged.connect(self._forget_hidden)
        theme.follow(self, self.relayout)

    # -- layout -------------------------------------------------------------------------------
    def set_zoom(self, percent: int) -> None:
        """Page size in percent of A's 148 x 209 (the status-bar slider)."""
        percent = max(ZOOM_MIN, min(ZOOM_MAX, int(percent)))
        if percent != self.zoom:
            self.zoom = percent
            self.relayout()

    def thumbnail_height(self) -> int:
        """Pixel height the scans are rendered at for the current zoom and screen."""
        return max(16, round(self.metrics.page_h * self.devicePixelRatioF()))

    def relayout(self) -> None:
        current = self.currentIndex()
        anchor = None
        if current.isValid() and current.row() < len(self._rects):
            anchor = self.visualRect(current).top()
        self.metrics = Metrics.at(self.zoom)
        self._laid_width = -1
        self.doItemsLayout()
        if anchor is not None and current.isValid():  # keep the current page where it was
            top = self._rects[current.row()].top() - self.metrics.header
            self.verticalScrollBar().setValue(top - max(0, anchor - self.metrics.header))
        self.viewport().update()

    def doItemsLayout(self) -> None:  # noqa: N802
        model = self.model()
        if isinstance(model, TimelineModel) and model.rowCount():
            self._rects, self._rows, self._height = flow(
                model.groups(), model._states, self.metrics, self.viewport().width())
        else:
            self._rects, self._rows, self._height = [], [], 0
        self._row_tops = [row.y for row in self._rows]
        self._laid_width = self.viewport().width()
        QAbstractItemView.doItemsLayout(self)

    def reset(self) -> None:
        super().reset()
        self.doItemsLayout()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self.viewport().width() != self._laid_width:
            self.doItemsLayout()

    def updateGeometries(self) -> None:  # noqa: N802
        bar = self.verticalScrollBar()
        bar.setRange(0, max(0, self._height - self.viewport().height()))
        bar.setPageStep(self.viewport().height())
        bar.setSingleStep(max(20, self.metrics.row_h // 6))
        self.horizontalScrollBar().setRange(0, 0)
        QAbstractItemView.updateGeometries(self)

    def viewportSizeHint(self) -> QSize:  # noqa: N802
        return QSize(self.viewport().width(), self._height)

    def content_height(self) -> int:
        return self._height

    def layout_rows(self) -> list[LayoutRow]:
        return self._rows

    def page_rect(self, row: int) -> QRect:
        """The page sheet of `row` in viewport coordinates (no caption)."""
        if not 0 <= row < len(self._rects):
            return QRect()
        return self._rects[row].translated(0, -self.verticalOffset())

    # -- geometry API of QAbstractItemView ----------------------------------------------------
    def horizontalOffset(self) -> int:  # noqa: N802
        return 0

    def verticalOffset(self) -> int:  # noqa: N802
        return self.verticalScrollBar().value()

    def isIndexHidden(self, index) -> bool:  # noqa: N802
        return False

    def _slot(self, row: int) -> QRect:
        rect = self._rects[row]
        return QRect(rect.x(), rect.y(), rect.width(), rect.height() + self.metrics.caption_h)

    def visualRect(self, index) -> QRect:  # noqa: N802
        if not index.isValid() or index.row() >= len(self._rects):
            return QRect()
        # room for the selection ring, check badge and focus ring around the sheet
        return self._slot(index.row()).adjusted(-11, -11, 11, 0).translated(
            0, -self.verticalOffset())

    def _rows_between(self, top: int, bottom: int) -> list[LayoutRow]:
        if not self._rows:
            return []
        start = max(0, bisect_right(self._row_tops, top - self.metrics.row_h) - 1)
        found = []
        for row in self._rows[start:]:
            if row.y > bottom:
                break
            if row.y + self.metrics.row_h >= top:
                found.append(row)
        return found

    def indexAt(self, point: QPoint) -> QModelIndex:  # noqa: N802
        model = self.model()
        if model is None:
            return QModelIndex()
        y = point.y() + self.verticalOffset()
        for row in self._rows_between(y, y):
            for r in range(row.first, row.last + 1):
                if self._slot(r).contains(QPoint(point.x(), y)):
                    return model.index(r, 0)
        return QModelIndex()

    def scrollTo(self, index, hint=QAbstractItemView.ScrollHint.EnsureVisible) -> None:  # noqa: N802
        if not index.isValid() or index.row() >= len(self._rects):
            return
        rect = self._rects[index.row()]
        top = rect.top() - self.metrics.header - self.metrics.pad_top // 2
        bottom = rect.bottom() + self.metrics.caption_h
        bar, height = self.verticalScrollBar(), self.viewport().height()
        hints = QAbstractItemView.ScrollHint
        if hint == hints.PositionAtTop:
            bar.setValue(top)
        elif hint == hints.PositionAtBottom:
            bar.setValue(bottom - height)
        elif hint == hints.PositionAtCenter:
            bar.setValue((top + bottom) // 2 - height // 2)
        elif top < bar.value():
            bar.setValue(top)
        elif bottom > bar.value() + height:
            bar.setValue(min(top, bottom - height))
        self.viewport().update()

    def moveCursor(self, action, modifiers) -> QModelIndex:  # noqa: N802
        model = self.model()
        if model is None or model.rowCount() == 0:
            return QModelIndex()
        count = model.rowCount()
        current = self.currentIndex()
        row = current.row() if current.isValid() else 0
        a = QAbstractItemView.CursorAction
        if action in (a.MoveLeft, a.MovePrevious):
            row = max(0, row - 1)
        elif action in (a.MoveRight, a.MoveNext):
            row = min(count - 1, row + 1)
        elif action == a.MoveHome:
            row = 0
        elif action == a.MoveEnd:
            row = count - 1
        elif action in (a.MoveUp, a.MoveDown, a.MovePageUp, a.MovePageDown):
            row = self._vertical_neighbour(row, action)
        return model.index(row, 0)

    def _vertical_neighbour(self, row: int, action) -> int:
        a = QAbstractItemView.CursorAction
        if not self._rects:
            return row
        rect = self._rects[row]
        step = self.metrics.row_h + self.metrics.row_gap
        if action in (a.MovePageUp, a.MovePageDown):
            step = max(step, self.viewport().height() - self.metrics.row_h // 2)
        y = rect.top() + (-step if action in (a.MoveUp, a.MovePageUp) else step)
        here = next((i for i, r in enumerate(self._rows) if r.first <= row <= r.last), 0)
        target = min(range(len(self._rows)), key=lambda i: abs(self._rows[i].y
                                                                + self.metrics.header - y))
        if target == here:
            target = max(0, here - 1) if action in (a.MoveUp, a.MovePageUp) else \
                min(len(self._rows) - 1, here + 1)
        line = self._rows[target]
        centre = rect.center().x()
        return min(range(line.first, line.last + 1),
                   key=lambda r: abs(self._rects[r].center().x() - centre))

    def setSelection(self, rect: QRect, command) -> None:  # noqa: N802
        model = self.model()
        if model is None:
            return
        area = rect.normalized().translated(0, self.verticalOffset())
        selection = QItemSelection()
        start = None
        rows = sorted(r for line in self._rows_between(area.top(), area.bottom())
                      for r in range(line.first, line.last + 1)
                      if self._slot(r).intersects(area))
        for i, r in enumerate(rows):
            if start is None:
                start = r
            if i + 1 == len(rows) or rows[i + 1] != r + 1:
                selection.select(model.index(start, 0), model.index(r, 0))
                start = None
        self.selectionModel().select(selection, command)

    def visualRegionForSelection(self, selection) -> QRegion:  # noqa: N802
        region = QRegion()
        top = self.verticalOffset()
        bottom = top + self.viewport().height()
        for item in selection:
            for r in range(item.top(), item.bottom() + 1):
                if r < len(self._rects) and top - 300 < self._rects[r].y() < bottom + 300:
                    region += self.visualRect(self.model().index(r, 0))
        return region

    def visible_rows(self) -> range:
        """Rows of the pages at least partly in view."""
        top = self.verticalOffset()
        lines = self._rows_between(top, top + self.viewport().height())
        if not lines:
            return range(0)
        return range(lines[0].first, lines[-1].last + 1)

    # -- painting -----------------------------------------------------------------------------
    def paintEvent(self, event) -> None:  # noqa: N802
        m = theme.manager()
        painter = QPainter(self.viewport())
        painter.fillRect(event.rect(), m.color("layer"))
        model = self.model()
        if not isinstance(model, TimelineModel) or not self._rows:
            return
        dy = self.verticalOffset()
        clip = event.rect().translated(0, dy)
        groups = model.groups()
        selection = self.selectionModel()
        current = self.currentIndex()
        has_focus = self.hasFocus()
        option = QStyleOptionViewItem()
        self.initViewItemOption(option)
        delegate = self.itemDelegate()
        painter.translate(0, -dy)
        for line in self._rows_between(clip.top() - 12, clip.bottom() + 12):
            for segment in line.segments:
                self._paint_group(painter, model, groups[segment.group], segment, line.y)
            for r in range(line.first, line.last + 1):
                index = model.index(r, 0)
                option.rect = self._slot(r)
                option.state = QStyle.StateFlag.State_Enabled
                if selection is not None and selection.isSelected(index):
                    option.state |= QStyle.StateFlag.State_Selected
                if has_focus and index == current:
                    option.state |= QStyle.StateFlag.State_HasFocus
                delegate.paint(painter, option, index)
        painter.translate(0, dy)
        if self._band is not None:
            band = QRectF(self._band.translated(0, -dy))
            fill = QColor(m.color("accent"))
            fill.setAlphaF(0.12)
            painter.fillRect(band, fill)
            painter.setPen(QPen(m.color("accent"), 1))
            painter.drawRect(band.adjusted(0.5, 0.5, -0.5, -0.5))

    def _paint_group(self, painter: QPainter, model: TimelineModel, group: Group,
                     segment: Segment, y: int) -> None:
        if group.kind != "doc":
            return
        mt = self.metrics
        kind = group.cut if group.cut in kp.CUT_ICONS else "start"
        lip = QRectF(segment.x0, y + mt.tab_h, segment.x1 - segment.x0, mt.lip_h)
        kp.paint_lip(painter, lip, kind)
        if not segment.start:
            return
        reviewed = group.doc in model.reviewed
        check = bool(model.checks.get(group.doc))
        tab = kp.guide_tab_size(group.doc, group.cut, reviewed)
        rider = kp.rider_size() if check else QSize(0, 0)
        pad = theme.manager().size("s3")
        block = tab.width() + (theme.manager().size("s1") + rider.width() if check else 0)
        if group.cut == "filter":
            x = (segment.x0 + segment.x1 - block) / 2
        elif group.cut == "manual":
            x = segment.x1 - pad - block
        else:
            x = segment.x0 + pad
        x = max(segment.x0, x)
        kp.paint_guide_tab(painter, QRectF(x, y, tab.width(), mt.tab_h + 1), group.cut,
                           group.doc, reviewed)
        if check:
            rx = x + tab.width() + theme.manager().size("s1")
            kp.paint_rider(painter, QRectF(rx, y + mt.tab_h - 2 - rider.height(), rider.width(),
                                           rider.height()))

    # -- rubber band --------------------------------------------------------------------------
    def mousePressEvent(self, event) -> None:  # noqa: N802
        self._press = event.position().toPoint() + QPoint(0, self.verticalOffset())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        super().mouseMoveEvent(event)
        if (self.state() == QAbstractItemView.State.DragSelectingState
                and self._press is not None and event.buttons() & Qt.MouseButton.LeftButton):
            here = event.position().toPoint() + QPoint(0, self.verticalOffset())
            band = QRect(self._press, here).normalized()
            if band.width() > 3 or band.height() > 3:
                self._band = band
                self.viewport().update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        super().mouseReleaseEvent(event)
        self._press = None
        if self._band is not None:
            self._band = None
            self.viewport().update()

    def select_rows(self, first: int, last: int, current: int | None = None) -> None:
        """Select a range of rows (and make `current` the current page)."""
        model = self.model()
        selection = QItemSelection(model.index(first, 0), model.index(last, 0))
        flags = QItemSelectionModel.SelectionFlag
        self.selectionModel().select(selection, flags.ClearAndSelect)
        if current is not None:
            self.selectionModel().setCurrentIndex(model.index(current, 0), flags.NoUpdate)

    # -- thumbnails ---------------------------------------------------------------------------
    def _forget_hidden(self) -> None:
        model = self.model()
        if model is None or self.thumbnails is None:
            return
        rows = self.visible_rows()
        self.thumbnails.keep_only({model.page_id(r) for r in rows})

    def _thumbnail_ready(self, pid: str, _image) -> None:
        model = self.model()
        if model is None:
            return
        try:
            row = model.row_of(pid)
        except ValueError:
            return
        self.viewport().update(self.visualRect(model.index(row, 0)))
