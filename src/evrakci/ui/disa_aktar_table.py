"""The file list of Dışa Aktar (A's table): a model over `FileRow`s and one delegate that paints
every cell, so 1,000 documents scroll without a widget per row.

Columns: Durum (icon + word + why), the file name, Sayfalar, Şablon. Before writing the word is
Tamam / Bilgi / Kontrol; while writing Bekliyor / Yazılıyor / Yazıldı; afterwards Yazıldı (the why
stays, so the flagged files are still found).
"""

from __future__ import annotations

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QRectF,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import QFontMetricsF, QKeyEvent, QKeySequence, QPainter
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHeaderView,
    QStyledItemDelegate,
    QTableView,
)

from evrakci.ui import disa_aktar_icons, icons, theme
from evrakci.ui.disa_aktar_model import FileRow

assert disa_aktar_icons  # registers loader-circle
ROW_ROLE = Qt.ItemDataRole.UserRole + 1
STATUS_ROLE = Qt.ItemDataRole.UserRole + 2
WIDTHS = (252, 0, 104, 148)  # A's colgroup at 100 % text; the name column takes the rest
WIDTHS_150 = (330, 0, 156, 222)  # A's 150 % render (the Şablon column scrolls into view)
NAME_MIN = 200  # the narrowest the name column gets at 100 % text
NO_TEMPLATE = "Şablon yok"
# (icon, colour role, strong) per Durum word
LOOK = {
    "Kontrol": ("triangle-alert", "check-text", True),
    "Bilgi": ("info", "text-2", False),
    "Tamam": ("circle-check", "ok", False),
    "Yazıldı": ("circle-check", "ok", False),
    "Yazılıyor": ("loader-circle", "text-2", False),
    "Bekliyor": ("circle-dashed", "text-2", False),
}
PREVIEW_WORDS = {"kontrol": "Kontrol", "bilgi": "Bilgi", "tamam": "Tamam"}


class FilesModel(QAbstractTableModel):
    """mode "preview" (what will be written), "run" (writing: `done` files of the last stage
    are written) or "written" (the files on disk)."""

    HEADERS = ("Durum", "Yazılacak dosya adı", "Sayfalar", "Şablon")
    WRITTEN_HEADERS = ("Durum", "Yazılan dosya", "Sayfalar", "Şablon")

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._all: list[FileRow] = []
        self._rows: list[FileRow] = []
        self.mode = "preview"
        self.done = 0  # run: files finished by the last stage
        self.final = False  # run: the stage in progress is the last one
        self.only_kontrol = False

    # -- data -----------------------------------------------------------------------------
    def set_rows(self, rows: list[FileRow], mode: str = "preview") -> None:
        self.beginResetModel()
        self._all = list(rows)
        self.mode = mode
        self.done, self.final = 0, False
        self._rows = self._visible()
        self.endResetModel()

    def _visible(self) -> list[FileRow]:
        return [r for r in self._all if r.state == "kontrol"] if self.only_kontrol \
            else list(self._all)

    def set_filter(self, only_kontrol: bool) -> None:
        if only_kontrol == self.only_kontrol:
            return
        self.beginResetModel()
        self.only_kontrol = only_kontrol
        self._rows = self._visible()
        self.endResetModel()

    def set_progress(self, done: int, final: bool) -> None:
        self.done, self.final = done, final
        if self._rows:
            self.dataChanged.emit(self.index(0, 0), self.index(len(self._rows) - 1, 0))

    def kontrol_count(self) -> int:
        return sum(1 for r in self._all if r.state == "kontrol")

    def row_at(self, row: int) -> FileRow | None:
        return self._rows[row] if 0 <= row < len(self._rows) else None

    def row_of(self, predicate) -> int:
        return next((i for i, r in enumerate(self._rows) if predicate(r)), -1)

    def word(self, row: FileRow) -> str:
        """The Durum word of a row in the current mode."""
        if self.mode == "written":
            return "Yazıldı"
        if self.mode == "run":
            index = row.number - 1
            if index < self.done:
                return "Yazıldı" if self.final else "Yazılıyor"
            return "Yazılıyor" if index == self.done and self.final else "Bekliyor"
        return PREVIEW_WORDS[row.state]

    # -- the model ------------------------------------------------------------------------
    def rowCount(self, parent=None) -> int:  # noqa: N802
        return 0 if parent is not None and parent.isValid() else len(self._rows)

    def columnCount(self, parent=None) -> int:  # noqa: N802
        return 0 if parent is not None and parent.isValid() else 4

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return (self.HEADERS if self.mode == "preview" else self.WRITTEN_HEADERS)[section]
        if role == Qt.ItemDataRole.TextAlignmentRole and section == 2:
            return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._rows):
            return None
        row = self._rows[index.row()]
        column = index.column()
        if role == ROW_ROLE:
            return row
        if role == STATUS_ROLE:
            return self.word(row)
        if role == Qt.ItemDataRole.DisplayRole:
            if column == 0:
                return f"{self.word(row)} {row.why}".strip()
            return (row.name, row.pages, row.template or NO_TEMPLATE)[column - 1]
        if role == Qt.ItemDataRole.ToolTipRole and column == 1:
            return row.name
        if role == Qt.ItemDataRole.TextAlignmentRole and column == 2:
            return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return None

    def flags(self, index):
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable if index.isValid() \
            else Qt.ItemFlag.NoItemFlags


class FilesDelegate(QStyledItemDelegate):
    """A's rows: hairline between rows, the selected fill with the 3 px accent bar on the
    current row, Durum as icon + word + why, the name in body type, pages tabular."""

    def __init__(self, view: FilesTable) -> None:
        super().__init__(view)
        self.view = view
        self.fonts: dict[str, object] = {}
        theme.follow(self, self.fonts.clear, "disa-aktar-fonts")

    def _font(self, role: str):
        if role not in self.fonts:
            self.fonts[role] = theme.manager().font(role)
        return self.fonts[role]

    def sizeHint(self, option, index) -> QSize:  # noqa: N802
        return QSize(WIDTHS[index.column()] or 200, theme.manager().size("row-h"))

    def paint(self, painter: QPainter, option, index) -> None:
        m = theme.manager()
        model: FilesModel = index.model()
        row: FileRow = index.data(ROW_ROLE)
        rect = QRectF(option.rect)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        selection = self.view.selectionModel()
        selected = selection is not None and selection.isRowSelected(index.row(), QModelIndex())
        hc = m.theme() == "hc"
        ink = "text-on-accent" if hc and selected else None
        if selected:
            painter.fillRect(rect, m.color("accent" if hc else "selected"))
        if index.row() < model.rowCount() - 1:
            painter.fillRect(QRectF(rect.left(), rect.bottom(), rect.width(), 1),
                             m.color("stroke-soft"))
        current = self.view.currentIndex()
        if index.column() == 0 and current.isValid() and current.row() == index.row():
            painter.fillRect(QRectF(rect.left(), rect.top(), 3, rect.height()),
                             m.color(ink or "accent"))
        s2, s3, s4 = m.size("s2"), m.size("s3"), m.size("s4")
        column = index.column()
        if column == 0:
            self._status(painter, rect.adjusted(s4, 0, -s2, -1), model.word(row), row.why, ink)
        elif column == 1:
            self._name(painter, rect.adjusted(s3, 0, -s3, -1), row, ink)
        elif column == 2:
            painter.setFont(self._font("num"))
            painter.setPen(m.color(ink or "text-2"))
            painter.drawText(rect.adjusted(s3, 0, -s3, -1),
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                             row.pages)
        else:
            painter.setFont(self._font("caption"))
            painter.setPen(m.color(ink or "text-2"))
            area = rect.adjusted(s3, 0, -s3, -1)
            text = row.template or NO_TEMPLATE
            painter.drawText(area, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                             QFontMetricsF(painter.font()).elidedText(
                                 text, Qt.TextElideMode.ElideRight, area.width()))
        painter.restore()

    def _status(self, painter, rect: QRectF, word: str, why: str, ink: str | None) -> None:
        m = theme.manager()
        name, role, strong = LOOK[word]
        role = ink or role
        x = rect.left()
        icons.paint(painter, name, QRectF(x, rect.center().y() - 8, 16, 16), m.hex(role))
        x += 16 + 6  # A .st gap
        font = self._font("body-strong" if strong else "body")
        painter.setFont(font)
        painter.setPen(m.color(role))
        advance = QFontMetricsF(font).horizontalAdvance(word)
        painter.drawText(QRectF(x, rect.top(), rect.right() - x, rect.height()),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, word)
        if why:
            x += advance + m.size("s2")
            caption = self._font("caption")
            painter.setFont(caption)
            painter.setPen(m.color(ink or "text-2"))
            painter.drawText(QRectF(x, rect.top(), max(0.0, rect.right() - x), rect.height()),
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                             QFontMetricsF(caption).elidedText(
                                 why, Qt.TextElideMode.ElideRight, max(0.0, rect.right() - x)))

    def _name(self, painter, rect: QRectF, row: FileRow, ink: str | None) -> None:
        m = theme.manager()
        font = self._font("body")
        metrics = QFontMetricsF(font)
        painter.setFont(font)
        flags = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        if not row.tail or metrics.horizontalAdvance(row.name) > rect.width():
            painter.setPen(m.color(ink or "text"))
            painter.drawText(rect, flags, metrics.elidedText(
                row.name, Qt.TextElideMode.ElideMiddle, rect.width()))
            return
        x = rect.left()
        for text, role, strong in ((row.pre, "text", False), (row.tail, "text-accent", True),
                                   (row.post, "text", False)):
            part_font = self._font("body-strong" if strong else "body")
            painter.setFont(part_font)
            painter.setPen(m.color(ink or role))
            width = QFontMetricsF(part_font).horizontalAdvance(text)
            painter.drawText(QRectF(x, rect.top(), width + 2, rect.height()), flags, text)
            x += width


class FilesTable(QTableView):
    """A's table view: rows select as a whole, arrows move, Home / End jump."""

    copy_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        m = theme.manager()
        self.verticalHeader().hide()
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.verticalHeader().setDefaultSectionSize(m.size("row-h"))
        self.verticalHeader().setMinimumSectionSize(m.size("row-h"))
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setTabKeyNavigation(False)
        self.setItemDelegate(FilesDelegate(self))
        self.setAccessibleName("Dosya adları")
        theme.follow(self, self._rescale, "disa-aktar-rows")

    def _rescale(self) -> None:
        row = theme.manager().size("row-h")
        self.verticalHeader().setDefaultSectionSize(row)
        self.verticalHeader().setMinimumSectionSize(row)

    def sizeHint(self) -> QSize:  # noqa: N802
        """Small: the card around it takes the room there is (QTableView asks for 192 px,
        which kept a scrolling column from giving the list less)."""
        m = theme.manager()
        return QSize(400, m.size("header-h") + 2 * m.size("row-h"))

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.matches(QKeySequence.StandardKey.Copy):
            self.copy_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)
