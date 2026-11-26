"""The Kontrol timeline (direction A): documents filed as stacks of pages under manila guide tabs.

Each document is a group: a guide tab in the logo's trapezoid (QR on the left, filter in the
centre, manual on the right, so the cut is clear in greyscale), the manila lip whose top line is
solid / dashed / dotted, and its pages. Documents flow left to right and wrap to the next row;
a document is split over rows only when it is wider than a row. Separator pages are narrow
tiles between documents; pages that will be deleted stay in their document, dimmed.

Smooth at 1,000 pages: the view is one QListView with its own flow layout (plain rectangles,
computed in one pass), it paints only the rows in view, every page through the delegate, and
asks the thumbnail service for the pages in view plus a margin ahead of the scroll (driven by
the scroll position, not by painting or the mouse), nearest first.
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
    QTimer,
    Signal,
)
from PySide6.QtGui import QColor, QFontMetrics, QImage, QPainter, QPen, QRegion
from PySide6.QtWidgets import (
    QAbstractItemView,
    QListView,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
)

from evrakci.pipeline.select import different_pages
from evrakci.ui import kontrol_paint as kp
from evrakci.ui import style, theme
from evrakci.ui.controller import JobController
from evrakci.ui.thumbnails import ThumbnailService

SEP_W = 48  # A .sepage
DOC_GAP = 28  # A .row gap between documents
ZOOM_MIN, ZOOM_MAX, ZOOM_STEP = 50, 200, 10
PREFETCH_AHEAD = 1.0  # viewports of pages requested beyond the edge the scroll moves towards
PREFETCH_BEHIND = 0.5  # and beyond the other edge


class Roles(IntEnum):
    PID = Qt.ItemDataRole.UserRole + 1
    DOC = Qt.ItemDataRole.UserRole + 2  # document number (1-based) or 0
    CUT = Qt.ItemDataRole.UserRole + 3  # "qr" | "filter" | "manual" | "start" on a first page
    STATE = Qt.ItemDataRole.UserRole + 4  # "page" | "separator" | "deleted" | "dropped"
    TEMPLATE = Qt.ItemDataRole.UserRole + 5
    CHECK = Qt.ItemDataRole.UserRole + 6  # the document needs a check
    PAGE_NO = Qt.ItemDataRole.UserRole + 7
    REVIEWED = Qt.ItemDataRole.UserRole + 8  # the document was approved (İncelendi)
    ODD = Qt.ItemDataRole.UserRole + 9  # "boyut" | "yatay" | "dikey" on a page that looks different


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

    marks_changed = Signal()  # the marks were switched on or off: the view lays out again

    def __init__(self, controller: JobController, templates=dict) -> None:
        super().__init__()
        self.controller = controller
        self.templates = templates  # callable returning {template id: Template}
        self.checks: dict[int, list[str]] = {}
        self.reviewed: set[int] = set()
        self.marks_on = True  # "Farklı görünenleri işaretle" (the jumps work with it off, too)
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

    def set_marks(self, on: bool) -> None:
        """Show or hide the "looks different" marks (the pages are found either way)."""
        on = bool(on)
        if on != self.marks_on:
            self.marks_on = on
            self._changed_all()
            self.marks_changed.emit()

    def odd_rows(self) -> list[int]:
        """Rows of the pages that look different (size or orientation), in order."""
        return self._odd_rows

    def odd_kind(self, row: int) -> str | None:
        """What is different about the page of `row` ("boyut", "yatay", "dikey") while the marks
        are shown, else None."""
        return self._odd.get(self._pids[row]) if self.marks_on else None

    def marked_kinds(self) -> set[str]:
        """The kinds of mark that are drawn now."""
        return set(self._odd.values()) if self.marks_on else set()

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
        # once per rebuild, O(n): the pages whose size or orientation (after the job's own
        # rotations) differs from the job's majority
        self._odd = different_pages(job, documents=self.controller.documents())
        self._odd_rows = [self._row[pid] for pid in self._odd]

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
        if role == Roles.ODD:
            return self.odd_kind(row)
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole,
                    Qt.ItemDataRole.AccessibleTextRole):
            return self.describe(row)
        return None

    def describe(self, row: int) -> str:
        """"Sayfa 73, Belge 16, kontrol bekliyor" (tooltip and screen reader text)."""
        state = self._states[row]
        if state == "separator":
            return f"Sayfa {row + 1}, QR ayraç"
        doc = self._doc_of.get(self._pids[row], 0)
        parts = [f"Sayfa {row + 1}"]
        if doc:
            parts.append(f"Belge {doc}")
            if self.checks.get(doc):
                parts.append("kontrol bekliyor")
            parts.append("incelendi" if doc in self.reviewed else "incelenmedi")
        odd = self.odd_kind(row)
        if odd is not None:
            parts.append(kp.ODD_MARKS[odd][1].lower())  # "farklı boyut", "yatay", "dikey"
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
    lines: int = 1  # caption lines reserved: 2 when a "looks different" mark wraps (150 % text)

    @property
    def header(self) -> int:
        return self.tab_h + self.lip_h + self.lip_gap

    @property
    def row_h(self) -> int:
        return self.header + self.page_h + self.caption_h

    @staticmethod
    def at(zoom: int, lines: int = 1) -> Metrics:
        m = theme.manager()
        scale = zoom / 100
        return Metrics(
            page_w=round(m.size("thumb-w") * scale), page_h=round(m.size("thumb-h") * scale),
            sep_w=max(32, round(SEP_W * scale)), gap=m.size("s3"), doc_gap=DOC_GAP,
            pad_top=m.size("s4"), pad_x=m.size("s6"), row_gap=m.size("s6"),
            tab_h=kp.tab_height(), lip_h=kp.LIP_H, lip_gap=m.size("s3"),
            # A figcaption: 28 px (6 + 18 + 4); a second line under a wrapped mark
            caption_h=m.size("lh-caption") * lines + 10, lines=lines)


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
    """Paints one page slot: paper (scan or placeholder), selection ring and corner dot,
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
        if (option.state & QStyle.StateFlag.State_MouseOver) and not selected \
                and state != "separator":  # S-3: hover tint behind the tile and its number
            tile = QRectF(page.x() - 8, page.y() - 6, page.width() + 16,
                          page.height() + mt.caption_h + 6)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(m.color("hover"))
            painter.drawRoundedRect(tile, m.size("r-control"), m.size("r-control"))
            painter.setBrush(Qt.BrushStyle.NoBrush)
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
        if selected:  # 2 px accent ring with a 3 px layer gap + a corner dot (K-2)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(m.color("accent"), 2))
            painter.drawRoundedRect(page.adjusted(-4, -4, 4, 4), radius + 4, radius + 4)
            kp.paint_select_dot(painter, QPointF(page.x() + 3, page.y() + 3))
        if focused:  # A .slot.foc: D11 ring outside the selection ring
            style.paint_ring(painter, page.adjusted(-10, -10, 10, 10), radius + 8)
        if state != "separator":
            self._caption(painter, QRectF(page.x() - 8, page.bottom(), page.width() + 16,
                                          mt.caption_h), row, state, selected,
                          index.data(Roles.ODD))
        else:  # "Ayraç 4" under the tile; it may be wider than the narrow tile (K-8)
            text = f"Ayraç {row + 1}"
            font = m.font("caption-strong" if selected else "caption-num")
            width = max(page.width() + 16, QFontMetrics(font).horizontalAdvance(text) + 8)
            painter.setFont(font)
            painter.setPen(m.color("text-accent" if selected else "text-2"))
            painter.drawText(QRectF(page.center().x() - width / 2, page.bottom() + 6, width,
                                    QFontMetrics(font).height()),
                             Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, text)
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
                 selected: bool, odd: str | None = None) -> None:
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
        metrics = QFontMetrics(font)
        line = metrics.height()
        top = rect.y() + 6
        if odd is None or state != "page":
            painter.drawText(QRectF(rect.x(), top, rect.width(), line),
                             Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, text)
            return
        # "looks different": the number, then a 14 px icon and the word (caption weight 600,
        # text colour). Side by side when they fit, else two short lines (150 % text).
        if kp.odd_caption_lines(text, odd, rect.width()) == 1:
            number = metrics.horizontalAdvance(text)
            gap = m.size("s3")
            total = number + gap + kp.odd_mark_width(odd)
            left = rect.center().x() - total / 2
            painter.drawText(QRectF(left, top, number + 2, line),
                             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, text)
            kp.paint_odd_mark(painter, QRectF(left + number + gap, top, total - number - gap,
                                              line), odd, align_left=True)
        else:
            painter.drawText(QRectF(rect.x(), top, rect.width(), line),
                             Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, text)
            kp.paint_odd_mark(painter, QRectF(rect.x(), top + m.size("lh-caption"), rect.width(),
                                              line), odd)


# -- view ---------------------------------------------------------------------------------------
class TimelineView(QListView):
    """The working timeline: A's flow layout, page selection (click, Shift/Ctrl, rubber band),
    arrow keys, Home/End and PgUp/PgDn; Ctrl+wheel zooms through the screen's ZoomController.
    Ctrl+Space asks to toggle the current page (`toggle_requested`) and Alt+Left / Alt+Right to
    move the focus ring one page without touching the selection (`focus_requested(-1 / +1)`)."""

    toggle_requested = Signal()
    focus_requested = Signal(int)

    def __init__(self, thumbnails: ThumbnailService | None = None, parent=None) -> None:
        self.zoom = 100
        self.metrics = Metrics.at(100)
        self._rects: list[QRect] = []
        self._rows: list[LayoutRow] = []
        self._row_tops: list[int] = []
        self._height = 0
        self._laid_width = -1
        self._last_offset = 0
        self._band: QRect | None = None
        self._press: QPoint | None = None
        self._hover = -1  # S-3: the page under the mouse
        super().__init__(parent)
        self.thumbnails = thumbnails
        self.setMouseTracking(True)
        self.setObjectName("timeline")
        self.setAccessibleName("Sayfalar")
        self.setAccessibleDescription(
            "Belgeler sırayla. Oklar sayfa değiştirir, Shift ile seçim genişler, "
            "Boşluk önizler, Enter belgeyi onaylar. K keser, M birleştirir, Del siler, "
            "R döndürür.")
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
            self.verticalScrollBar().valueChanged.connect(self.load_thumbnails)
            thumbnails.distance = self._distance
        theme.follow(self, self.relayout)

    # -- layout -------------------------------------------------------------------------------
    def setModel(self, model) -> None:  # noqa: N802
        old = self.model()
        if isinstance(old, TimelineModel):
            try:
                old.marks_changed.disconnect(self.relayout)
            except (RuntimeError, TypeError):
                pass
        super().setModel(model)
        if isinstance(model, TimelineModel):
            model.marks_changed.connect(self.relayout)

    def _caption_lines(self) -> int:
        """2 when a mark that is drawn does not fit beside the page number (150 % text)."""
        model = self.model()
        if not isinstance(model, TimelineModel):
            return 1
        kinds = model.marked_kinds()
        if not kinds:
            return 1
        number, width = str(model.rowCount()), self.metrics.page_w + 16
        return max(kp.odd_caption_lines(number, kind, width) for kind in kinds)

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
        self.metrics = Metrics.at(self.zoom, self._caption_lines())
        self._laid_width = -1
        self.doItemsLayout()
        if anchor is not None and current.isValid():  # keep the current page where it was
            top = self._rects[current.row()].top() - self.metrics.header
            self.verticalScrollBar().setValue(top - max(0, anchor - self.metrics.header))
        self.viewport().update()

    def doItemsLayout(self) -> None:  # noqa: N802
        model = self.model()
        lines = self._caption_lines()
        if lines != self.metrics.lines:  # a mark appeared or went: the caption height follows
            self.metrics = Metrics.at(self.zoom, lines)
        if isinstance(model, TimelineModel) and model.rowCount():
            self._rects, self._rows, self._height = flow(
                model.groups(), model._states, self.metrics, self.viewport().width())
        else:
            self._rects, self._rows, self._height = [], [], 0
        self._row_tops = [row.y for row in self._rows]
        self._laid_width = self.viewport().width()
        QAbstractItemView.doItemsLayout(self)
        if self.thumbnails is not None and self._rows:
            QTimer.singleShot(0, self, self.load_thumbnails)  # after the layout settles

    def reset(self) -> None:
        super().reset()
        self.doItemsLayout()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self.viewport().width() != self._laid_width:
            self.doItemsLayout()

    def scrollContentsBy(self, dx: int, dy: int) -> None:  # noqa: N802
        """Move the painted pixels and repaint the strip that came into view. The inherited
        QListView version does nothing here (doItemsLayout skips the list-mode layout), which
        left old pixels on screen after a scroll (B-032)."""
        self.viewport().scroll(dx, dy)

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
        # room for the selection ring, corner dot and focus ring around the sheet
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

    def keyPressEvent(self, event) -> None:  # noqa: N802
        key, mods = event.key(), event.modifiers()
        if key == Qt.Key.Key_Space and mods == Qt.KeyboardModifier.ControlModifier:
            event.accept()
            self.toggle_requested.emit()
            return
        if mods == Qt.KeyboardModifier.AltModifier and key in (Qt.Key.Key_Left, Qt.Key.Key_Right):
            event.accept()
            self.focus_requested.emit(-1 if key == Qt.Key.Key_Left else 1)
            return
        super().keyPressEvent(event)

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

    def _row_at(self, point: QPoint) -> int | None:
        for line in self._rows_between(point.y(), point.y()):
            for r in range(line.first, line.last + 1):
                if self._slot(r).contains(point):
                    return r
        return None

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
        here = self.currentIndex()
        dragging = self.state() == QAbstractItemView.State.DragSelectingState
        if (command & QItemSelectionModel.SelectionFlag.Current and not dragging
                and here.isValid()):
            # Shift+click / Shift+arrow: Qt hands over the rectangle from the anchor page to the
            # current one. The pages between them in reading order are the range, not the slots
            # the rectangle touches (F-kontrol-01, F-kontrol-02).
            offset = QPoint(0, self.verticalOffset())
            ends = {self._row_at(rect.topLeft() + offset),
                    self._row_at(rect.bottomRight() + offset)}
            ends.discard(None)
            ends.discard(here.row())
            if len(ends) == 1:
                low, high = sorted((ends.pop(), here.row()))
                selection = QItemSelection(model.index(low, 0), model.index(high, 0))
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
                if r == self._hover:
                    option.state |= QStyle.StateFlag.State_MouseOver
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

    def _set_hover(self, row: int) -> None:
        if row == self._hover:
            return
        old, self._hover = self._hover, row
        for r in (old, row):
            if 0 <= r < len(self._rects):
                self.viewport().update(self.visualRect(self.model().index(r, 0)))

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._set_hover(-1)
        super().leaveEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        index = self.indexAt(event.position().toPoint())
        self._set_hover(index.row() if index.isValid() else -1)
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

    def select_row_set(self, rows) -> None:
        """Select exactly these rows (one selection of merged ranges, one repaint); the current
        page stays where it is."""
        model = self.model()
        selection = QItemSelection()
        first = last = None
        for row in sorted(set(rows)):
            if first is not None and row == last + 1:
                last = row
                continue
            if first is not None:
                selection.select(model.index(first, 0), model.index(last, 0))
            first = last = row
        if first is not None:
            selection.select(model.index(first, 0), model.index(last, 0))
        self.selectionModel().select(selection, QItemSelectionModel.SelectionFlag.ClearAndSelect)

    # -- thumbnails ---------------------------------------------------------------------------
    def prefetch_rows(self) -> tuple[list[int], list[int]]:
        """(rows in view, rows in the margin), each nearest to the viewport first. The margin is
        PREFETCH_AHEAD viewports beyond the edge the scroll moves towards (down by default) and
        PREFETCH_BEHIND beyond the other."""
        if not self._rows:
            return [], []
        top = self.verticalOffset()
        height = self.viewport().height()
        down = top >= self._last_offset
        ahead, behind = round(height * PREFETCH_AHEAD), round(height * PREFETCH_BEHIND)
        before, after = (behind, ahead) if down else (ahead, behind)
        view_top, view_bottom = top, top + height
        seen = set()
        near: list[tuple[int, int]] = []
        far: list[tuple[int, int]] = []
        for line in self._rows_between(view_top - before, view_bottom + after):
            bottom = line.y + self.metrics.row_h
            gap = max(view_top - bottom, line.y - view_bottom, 0)
            for r in range(line.first, line.last + 1):
                if r not in seen:
                    seen.add(r)
                    (near if gap == 0 else far).append((gap, r))
        return [r for _g, r in sorted(near)], [r for _g, r in sorted(far)]

    def load_thumbnails(self) -> None:
        """Ask for the pages in view and the margin (nearest first), forget the rest. Runs on
        every scroll and after a layout, so loading never waits for a paint or the mouse."""
        model = self.model()
        service = self.thumbnails
        if model is None or service is None or not isinstance(model, TimelineModel):
            return
        visible, margin = self.prefetch_rows()
        self._last_offset = self.verticalOffset()
        # separator tiles are drawn without a scan, so they are never rendered
        pids = [model.page_id(r) for r in visible + margin if model.state(r) != "separator"]
        service.keep_only(set(pids))
        # never evict a page that is wanted right now: the cap covers the whole request
        service.capacity = max(service.min_capacity, int(1.5 * len(pids)))
        for pid in pids:
            if not service.is_current(pid):
                service.request(pid)

    def detach_thumbnails(self) -> None:
        """Stop using the thumbnail service (it was retired): no more requests reach it."""
        service, self.thumbnails = self.thumbnails, None
        self.itemDelegate().thumbnails = None
        if service is not None:
            for signal, slot in ((service.ready, self._thumbnail_ready),
                                 (self.verticalScrollBar().valueChanged, self.load_thumbnails)):
                try:
                    signal.disconnect(slot)
                except (RuntimeError, TypeError):
                    pass

    def _distance(self, pid: str) -> float:
        """Pixels between page `pid` and the viewport (0 inside it), for cache eviction."""
        try:
            row = self.model().row_of(pid)
        except (ValueError, AttributeError, RuntimeError):
            return float("inf")
        if row >= len(self._rects):
            return float("inf")
        rect = self._rects[row]
        top = self.verticalOffset()
        return max(top - rect.bottom(), rect.top() - (top + self.viewport().height()), 0)

    def _thumbnail_ready(self, pid: str, _image) -> None:
        model = self.model()
        if model is None:
            return
        try:
            row = model.row_of(pid)
        except ValueError:
            return
        self.viewport().update(self.visualRect(model.index(row, 0)))
