"""The batch table of Yükle (final-a/yukle.html .tablecard): one model, one delegate that paints
every cell (no widget per row), A's header, drag handles and the Toplam row.

Rows are the job's batches in their order, then the batches being read ("Okunuyor", or
"Sırada" while waiting), then a Toplam row. Reordering is by drag (the grip column) or by
Alt+Up / Alt+Down; the model only reports the wish (`move_requested`), the screen asks the
job controller so every move is one undoable edit.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import (
    QAbstractTableModel,
    QByteArray,
    QMimeData,
    QModelIndex,
    QRect,
    QRectF,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import QFontMetricsF, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHeaderView,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableView,
)

from evrakci.ui import icons, theme
from evrakci.ui.yukle_info import BatchSummary

MIME = "application/x-evrakci-batch"
GRIP, NO, FILE, PAGES, QR, STATUS = range(6)
TITLES = {GRIP: "", NO: "No", FILE: "Dosya", PAGES: "Sayfa", QR: "QR ayıraç", STATUS: "Durum"}
RIGHT = (NO, PAGES, QR)
# A's colgroup (yukle.html) at 100 % text; Dosya takes the rest
WIDTHS = {GRIP: 44, NO: 56, PAGES: 96, QR: 116, STATUS: 148}
ITEM_ROLE = Qt.ItemDataRole.UserRole + 1
# status -> (icon, colour role, strong, word)
STATUSES = {
    "hazir": ("circle-check", "ok", False, "Hazır"),
    "kontrol": ("triangle-alert", "check-text", True, "Kontrol"),
    "okunuyor": ("loader-circle", "text-2", False, "Okunuyor"),
    "sirada": ("clock", "text-2", False, "Sırada"),
}


@dataclass(frozen=True)
class Item:
    kind: str  # "batch" | "pending" | "total"
    number: int = 0
    batch_id: str = ""
    name: str = ""
    pages: int = 0
    qr: int | None = 0  # None while the batch is being read
    status: str = "hazir"
    parties: int = 0  # total row


class BatchModel(QAbstractTableModel):
    """The rows above; `move_requested(batch_id, target_index)` when a drag is dropped."""

    move_requested = Signal(str, int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.items: list[Item] = []
        self._batches: list[BatchSummary] = []
        self._pending: list[Item] = []

    # content
    def set_content(self, batches: tuple[BatchSummary, ...] | list[BatchSummary],
                    pending: list[tuple[str, int, str]] = ()) -> None:
        """The job's batches and the files being read: (file name, pages, "okunuyor" |
        "sirada"). One reset, so a table that is read while it changes keeps its place."""
        self._batches = list(batches)
        self._pending = [Item("pending", len(self._batches) + i + 1, "", name, pages, None,
                              status) for i, (name, pages, status) in enumerate(pending)]
        self._rebuild()

    def set_batches(self, batches: tuple[BatchSummary, ...] | list[BatchSummary]) -> None:
        self.set_content(batches, [(i.name, i.pages, i.status) for i in self._pending])

    def set_pending(self, rows: list[tuple[str, int, str]]) -> None:
        self.set_content(self._batches, rows)

    def _rebuild(self) -> None:
        rows = [Item("batch", n, b.id, b.name, b.pages, b.qr, b.status)
                for n, b in enumerate(self._batches, start=1)]
        rows += self._pending
        if rows:
            reading = any(r.qr is None for r in rows)
            rows.append(Item("total", 0, "", "Toplam", sum(r.pages for r in rows),
                             None if reading else sum(r.qr or 0 for r in rows),
                             parties=len(rows)))
        self.beginResetModel()
        self.items = rows
        self.endResetModel()

    def batch_ids(self) -> list[str]:
        return [b.id for b in self._batches]

    def row_of(self, batch_id: str) -> int:
        return next((r for r, i in enumerate(self.items)
                     if i.kind == "batch" and i.batch_id == batch_id), -1)

    # Qt model
    def rowCount(self, parent=None) -> int:  # noqa: N802
        return 0 if parent is not None and parent.isValid() else len(self.items)

    def columnCount(self, parent=None) -> int:  # noqa: N802
        return 0 if parent is not None and parent.isValid() else 6

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if orientation != Qt.Orientation.Horizontal or section not in TITLES:
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return TITLES[section]
        if role in (Qt.ItemDataRole.ToolTipRole, Qt.ItemDataRole.AccessibleTextRole):
            return "Sürükle" if section == GRIP else TITLES[section]
        return None

    @staticmethod
    def text(item: Item, column: int) -> str:
        if column == NO:
            return str(item.number) if item.kind != "total" else ""
        if column == FILE:
            return item.name
        if column == PAGES:
            return str(item.pages)
        if column == QR:
            return "…" if item.qr is None else str(item.qr)
        if column == STATUS:
            if item.kind == "total":
                return f"{item.parties} parti"
            return STATUSES[item.status][3]
        return ""

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        item = self.items[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return self.text(item, index.column())
        if role == ITEM_ROLE:
            return item
        if role == Qt.ItemDataRole.AccessibleTextRole:
            return self._spoken(item, index.column())
        return None

    def _spoken(self, item: Item, column: int) -> str:
        if item.kind == "total":
            qr = "okunuyor" if item.qr is None else f"{item.qr} QR ayıraç"
            return f"Toplam: {item.parties} parti, {item.pages} sayfa, {qr}"
        qr = "QR ayıraçlar okunuyor" if item.qr is None else f"{item.qr} QR ayıraç"
        return (f"Parti {item.number}: {item.name}, {item.pages} sayfa, {qr}, "
                f"{STATUSES[item.status][3]}")

    def flags(self, index):
        base = Qt.ItemFlag.ItemIsEnabled
        if not index.isValid():
            return Qt.ItemFlag.ItemIsDropEnabled  # the empty area below the rows: "to the end"
        item = self.items[index.row()]
        if item.kind == "batch":
            base |= (Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsDragEnabled
                     | Qt.ItemFlag.ItemIsDropEnabled)
        return base

    # drag and drop (a batch onto a row or between rows)
    def supportedDropActions(self):  # noqa: N802
        return Qt.DropAction.CopyAction

    def supportedDragActions(self):  # noqa: N802
        return Qt.DropAction.CopyAction

    def mimeTypes(self):  # noqa: N802
        return [MIME]

    def mimeData(self, indexes):  # noqa: N802
        data = QMimeData()
        rows = sorted({i.row() for i in indexes})
        if rows and self.items[rows[0]].kind == "batch":
            data.setData(MIME, QByteArray(self.items[rows[0]].batch_id.encode()))
        return data

    def canDropMimeData(self, data, action, row, column, parent):  # noqa: N802
        return data.hasFormat(MIME)

    def drop_target(self, current: int, row: int, parent: QModelIndex) -> int:
        """Where the batch at index `current` ends up for a drop at (row, parent): onto a
        batch = that batch's place, between rows = before `row`, below the rows = the end."""
        count = len(self._batches)
        if parent.isValid():
            return min(parent.row(), count - 1)
        if row < 0 or row >= count:
            return count - 1
        return row if row <= current else row - 1  # the gap counts the dragged row too

    def dropMimeData(self, data, action, row, column, parent):  # noqa: N802
        if not data.hasFormat(MIME) or not self._batches:
            return False
        batch_id = bytes(data.data(MIME)).decode()
        if batch_id not in self.batch_ids():
            return False
        current = self.batch_ids().index(batch_id)
        target = self.drop_target(current, row, parent)
        if target != current:
            self.move_requested.emit(batch_id, target)
        return True


class BatchHeader(QHeaderView):
    """A's header: 36 px, caption semibold in text-2, a hairline below; numbers right-aligned."""

    def __init__(self, parent=None) -> None:
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setSectionsClickable(False)
        self.setHighlightSections(False)
        self.setStretchLastSection(False)
        self.setMinimumSectionSize(40)
        self.setSectionsMovable(False)

    def sizeHint(self) -> QSize:  # noqa: N802
        hint = super().sizeHint()
        return QSize(hint.width(), theme.manager().size("header-h"))

    def paintSection(self, painter: QPainter, rect: QRect, logical: int) -> None:  # noqa: N802
        m = theme.manager()
        painter.save()
        painter.fillRect(rect, m.color("card"))
        painter.fillRect(QRect(rect.left(), rect.bottom(), rect.width(), 1), m.color("stroke"))
        title = TITLES.get(logical, "")
        if title:
            font = m.font("caption-strong")
            s3, s4 = m.size("s3"), m.size("s4")
            inner = QRectF(rect).adjusted(s4 if logical == 0 else s3, 0, -s3, -1)
            if logical in RIGHT:
                inner.setLeft(rect.left() + 4)
            text = QFontMetricsF(font).elidedText(title, Qt.TextElideMode.ElideRight,
                                                  inner.width())
            painter.setFont(font)
            painter.setPen(m.color("text-2"))
            align = Qt.AlignmentFlag.AlignRight if logical in RIGHT else Qt.AlignmentFlag.AlignLeft
            painter.drawText(inner, Qt.AlignmentFlag.AlignVCenter | align, text)
        painter.restore()


class BatchDelegate(QStyledItemDelegate):
    """Paints A's rows: hairlines, the selected fill with its 3 px accent bar, the grip,
    numbers in tabular figures, Durum as icon + word, and the Toplam row."""

    def __init__(self, view: BatchTable) -> None:
        super().__init__(view)
        self.view = view

    def sizeHint(self, option, index) -> QSize:  # noqa: N802
        return QSize(WIDTHS.get(index.column(), 120), theme.manager().size("row-h"))

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        m = theme.manager()
        item: Item = index.data(ITEM_ROLE)
        column = index.column()
        rect = QRectF(option.rect)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        selected = (item.kind == "batch" and self.view.selectionModel() is not None
                    and self.view.selectionModel().isRowSelected(index.row(), QModelIndex()))
        hc = m.theme() == "hc"  # a selected row is a Highlight fill with HighlightText
        ink = "text-on-accent" if hc and selected else None
        if selected:
            painter.fillRect(rect, m.color("accent" if hc else "selected"))
            if column == 0:
                painter.fillRect(QRectF(rect.left(), rect.top(), 3, rect.height()),
                                 m.color(ink or "accent"))
        if index.row() < index.model().rowCount() - 1:
            painter.fillRect(QRectF(rect.left(), rect.bottom(), rect.width(), 1),
                             m.color("stroke-soft"))
        s3, s4 = m.size("s3"), m.size("s4")
        inner = rect.adjusted(s4 if column == 0 else s3, 0, -s3, -1)
        total = item.kind == "total"
        if column == GRIP:
            if item.kind == "batch":
                icons.paint(painter, "grip-vertical",
                            QRectF(rect.center().x() - 8, rect.center().y() - 8, 16, 16),
                            m.hex(ink or "text-2"))
        elif column == STATUS and not total:
            self._status(painter, inner, item, ink)
        else:
            self._cell(painter, inner, item, column, ink)
        painter.restore()

    def _cell(self, painter, rect: QRectF, item: Item, column: int, ink) -> None:
        m = theme.manager()
        text = BatchModel.text(item, column)
        total = item.kind == "total"
        strong = total and column in (PAGES, QR)
        font = m.font("body-strong") if strong else (
            m.font("num") if column in (NO, PAGES, QR) else m.font("body"))
        quiet = (total and not strong) or (item.kind == "pending" and column == FILE)
        colour = m.color(ink or ("text-2" if quiet else "text"))
        shown = QFontMetricsF(font).elidedText(text, Qt.TextElideMode.ElideRight, rect.width())
        painter.setFont(font)
        painter.setPen(colour)
        align = Qt.AlignmentFlag.AlignRight if column in RIGHT else Qt.AlignmentFlag.AlignLeft
        painter.drawText(rect, Qt.AlignmentFlag.AlignVCenter | align, shown)

    def _status(self, painter, rect: QRectF, item: Item, ink) -> None:
        m = theme.manager()
        name, role, strong, word = STATUSES[item.status]
        role = ink or role
        icons.paint(painter, name, QRectF(rect.left(), rect.center().y() - 8, 16, 16),
                    m.hex(role))
        font = m.font("body-strong" if strong else "body")
        painter.setFont(font)
        painter.setPen(m.color(role))
        x = rect.left() + 16 + 6  # A .st gap
        painter.drawText(QRectF(x, rect.top(), rect.right() - x, rect.height()),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, word)


class BatchTable(QTableView):
    """The view. One row selected at a time; the grip (or any part of the row) drags."""

    files_dragged = Signal(object)  # QDragEnterEvent / QDragMoveEvent with URLs
    files_left = Signal()
    files_dropped = Signal(object)  # QDropEvent with URLs

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        m = theme.manager()
        self.setHorizontalHeader(BatchHeader(self))
        self.verticalHeader().hide()
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.verticalHeader().setDefaultSectionSize(m.size("row-h"))
        self.verticalHeader().setMinimumSectionSize(m.size("row-h"))
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)
        self.setItemDelegate(BatchDelegate(self))
        self.setAccessibleName("Partiler")
        self.setAccessibleDescription(
            "Taranmış dosyaların sırası. Alt+Yukarı ve Alt+Aşağı ile taşıyın, Del ile çıkarın.")
        self.setMouseTracking(True)
        theme.bind_style(self, lambda: (
            f"QTableView {{ background: {theme.manager().hex('card')}; }}"
            f"QHeaderView::section {{ background: {theme.manager().hex('card')}; }}"))
        theme.follow(self, self._rescale, "yukle-rows")

    def _rescale(self) -> None:
        row = theme.manager().size("row-h")
        self.verticalHeader().setDefaultSectionSize(row)
        self.verticalHeader().setMinimumSectionSize(row)

    def model(self) -> BatchModel:  # typed
        return super().model()

    def clear(self) -> None:
        self.model().set_content([], [])

    def selected_batch(self) -> str | None:
        row = self.currentIndex().row()
        if not self.currentIndex().isValid() or row >= len(self.model().items):
            return None
        item = self.model().items[row]
        return item.batch_id if item.kind == "batch" else None

    def select_batch(self, batch_id: str) -> None:
        row = self.model().row_of(batch_id)
        if row >= 0:
            self.selectRow(row)
            self.setCurrentIndex(self.model().index(row, FILE))

    # files dragged in from outside belong to the window-wide drop, not to reordering
    @staticmethod
    def _foreign(event) -> bool:
        return event.mimeData().hasUrls() and not event.mimeData().hasFormat(MIME)

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if self._foreign(event):
            self.files_dragged.emit(event)
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event) -> None:  # noqa: N802
        if self._foreign(event):
            self.files_dragged.emit(event)
            return
        super().dragMoveEvent(event)

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        self.files_left.emit()
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:  # noqa: N802
        if self._foreign(event):
            self.files_dropped.emit(event)
            return
        super().dropEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        index = self.indexAt(event.position().toPoint())
        over_grip = (index.isValid() and index.column() == GRIP
                     and self.model().items[index.row()].kind == "batch")
        self.viewport().setCursor(Qt.CursorShape.SizeAllCursor if over_grip
                                  else Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        index = self.currentIndex()
        if not (self.hasFocus() and index.isValid() and index.row() < len(self.model().items)
                and self.model().items[index.row()].kind == "batch"):
            return
        m = theme.manager()  # D11 on the current row: 2 px outer + 1 px inner, inside the row
        row = QRectF(0, self.rowViewportPosition(index.row()), self.viewport().width(),
                     self.rowHeight(index.row())).adjusted(3, 3, -3, -4)
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(m.color("focus-outer"), 2))
        painter.drawRoundedRect(row, 4, 4)
        painter.setPen(QPen(m.color("focus-inner"), 1))
        painter.drawRoundedRect(row.adjusted(1.5, 1.5, -1.5, -1.5), 3, 3)
