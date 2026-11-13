"""The Değerler table: a model over `degerler_model.Row`s, one delegate that paints every cell
(no widget per row, smooth at 1,000 documents), A's header and the in-place editor.

Main views: one row per document, one column per variable, a review mark and Güven.
Örnek kontrol: one row per sampled value (Belge, Sayfa, Değişken, Okunan değer, Güven).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import (
    QAbstractTableModel,
    QEvent,
    QModelIndex,
    QPointF,
    QRect,
    QRectF,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QKeyEvent, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemDelegate,
    QAbstractItemView,
    QFrame,
    QHeaderView,
    QLabel,
    QLineEdit,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableView,
    QWidget,
)

from evrakci.ui import icons, theme
from evrakci.ui.degerler_model import LEVELS, RANK, Cell, Row, column_kind, display_name

ROW_ROLE = Qt.ItemDataRole.UserRole + 1
CELL_ROLE = Qt.ItemDataRole.UserRole + 2
KIND_ROLE = Qt.ItemDataRole.UserRole + 3
VALUE_KINDS = ("var", "value")

# A's colgroup at 100 % text (degerler.html); variable columns by what they hold.
WIDTHS = {"review": 44, "doc": 76, "pages": 80, "guven": 132, "name": 150,
          "number": 96, "date": 116, "code": 150, "text": 150}


@dataclass(frozen=True)
class Column:
    kind: str  # review, doc, pages, var, name, value, guven
    title: str
    key: str = ""  # the variable key of a "var" column
    style: str = "text"  # var / value: number, date, code, text

    @property
    def right(self) -> bool:
        return self.kind == "doc" or (self.kind == "var" and self.style == "number")


def main_columns(rows: list[Row], variables: list[tuple[str, str]]) -> list[Column]:
    """✓, Belge, Sayfa, the template's variables, Güven."""
    columns = [Column("review", ""), Column("doc", "Belge"), Column("pages", "Sayfa")]
    for key, name in variables:
        texts = [c.suggestion if c.needs_check else c.text  # what it should read
                 for r in rows for c in r.cells if c.key == key]
        columns.append(Column("var", display_name(name), key, column_kind(texts)))
    columns.append(Column("guven", "Güven"))
    return columns


SAMPLE_COLUMNS = [Column("review", ""), Column("doc", "Belge"), Column("pages", "Sayfa"),
                  Column("name", "Değişken"), Column("value", "Okunan değer"),
                  Column("guven", "Güven")]


def _guven_sort(row: Row, cell: Cell | None) -> tuple:
    level = cell.level if cell is not None else row.level
    percent = cell.percent if cell is not None else row.percent
    return (-RANK[level], percent if percent is not None else -1)


class ValuesModel(QAbstractTableModel):
    """Rows of the current view. `edited(row, key, text)` asks the screen to store a value."""

    edited = Signal(object, str, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.columns: list[Column] = []
        self.items: list[tuple[Row, Cell | None]] = []  # (row, the sampled cell or None)
        self.sample = False
        self._sort: tuple[int, Qt.SortOrder] = (1, Qt.SortOrder.AscendingOrder)

    # Content
    def set_content(self, columns: list[Column], items: list[tuple[Row, Cell | None]],
                    sample: bool) -> None:
        self.beginResetModel()
        same = [c.kind for c in columns] == [c.kind for c in self.columns]
        self.columns, self.items, self.sample = columns, list(items), sample
        if not same and self._sort[0] >= len(columns):
            self._sort = (1, Qt.SortOrder.AscendingOrder)
        self._apply_sort()
        self.endResetModel()

    def row_at(self, row: int) -> Row | None:
        return self.items[row][0] if 0 <= row < len(self.items) else None

    def cell_at(self, index: QModelIndex) -> Cell | None:
        if not index.isValid():
            return None
        row, sampled = self.items[index.row()]
        column = self.columns[index.column()]
        if column.kind == "value":
            return sampled
        if column.kind == "var":
            return row.cell(column.key)
        return None

    def value_index(self, number: int, key: str) -> QModelIndex:
        """The index of document `number`'s value `key` (invalid when not shown)."""
        for r, (row, sampled) in enumerate(self.items):
            if row.number != number:
                continue
            if self.sample:
                if sampled is not None and sampled.key == key:
                    return self.index(r, self._kind_column("value"))
            else:
                for c, column in enumerate(self.columns):
                    if column.kind == "var" and column.key == key:
                        return self.index(r, c)
        return QModelIndex()

    def row_of(self, number: int) -> int:
        return next((r for r, (row, _) in enumerate(self.items) if row.number == number), -1)

    def _kind_column(self, kind: str) -> int:
        return next(c for c, column in enumerate(self.columns) if column.kind == kind)

    def value_columns(self) -> list[int]:
        return [c for c, column in enumerate(self.columns) if column.kind in VALUE_KINDS]

    # Qt model
    def rowCount(self, parent=None) -> int:  # noqa: N802
        return 0 if parent is not None and parent.isValid() else len(self.items)

    def columnCount(self, parent=None) -> int:  # noqa: N802
        return 0 if parent is not None and parent.isValid() else len(self.columns)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if orientation != Qt.Orientation.Horizontal or not 0 <= section < len(self.columns):
            return None
        column = self.columns[section]
        if role == Qt.ItemDataRole.DisplayRole:
            return column.title
        if role in (Qt.ItemDataRole.ToolTipRole, Qt.ItemDataRole.AccessibleTextRole):
            return "İnceleme" if column.kind == "review" else column.title
        if role == KIND_ROLE:
            return column
        return None

    def _text(self, row: Row, sampled: Cell | None, column: Column) -> str:
        kind = column.kind
        if kind == "review":
            reviewed = sampled.reviewed if sampled is not None else row.reviewed
            return "İncelendi" if reviewed else ""
        if kind == "doc":
            return str(row.number)
        if kind == "pages":
            return row.pages
        if kind == "name":
            return sampled.title if sampled is not None else ""
        cell = sampled if kind == "value" else row.cell(column.key) if kind == "var" else None
        if kind in VALUE_KINDS:
            if cell is None or cell.value is None:
                return ""
            return cell.text or ("boş" if cell.level == "okunamadi" else "")
        level = cell.level if cell is not None else row.level
        percent = sampled.percent if sampled is not None else row.percent
        word = LEVELS[level][2]
        return f"{word} %{percent}" if percent is not None and level != "okunamadi" else word

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row, sampled = self.items[index.row()]
        column = self.columns[index.column()]
        if role == Qt.ItemDataRole.DisplayRole:
            return self._text(row, sampled, column)
        if role == Qt.ItemDataRole.EditRole:
            cell = self.cell_at(index)
            return cell.edit_text() if cell is not None else ""
        if role == ROW_ROLE:
            return row
        if role == CELL_ROLE:
            return self.cell_at(index)
        if role == KIND_ROLE:
            return column
        if role == Qt.ItemDataRole.AccessibleTextRole:
            return self._spoken(row, sampled, column, index)
        if role == Qt.ItemDataRole.ToolTipRole and column.kind in VALUE_KINDS:
            cell = self.cell_at(index)
            if cell is not None and cell.needs_check and cell.suggestion:
                return f"Öneri: {cell.suggestion}"
        return None

    def _spoken(self, row: Row, sampled: Cell | None, column: Column, index) -> str:
        text = self._text(row, sampled, column)
        if column.kind in VALUE_KINDS:
            cell = self.cell_at(index)
            name = cell.title if cell is not None else column.title
            if cell is None or cell.value is None:
                return f"{name}: okunmadı"
            parts = [f"{name}: {text or 'boş'}", LEVELS[cell.level][2]]
            if cell.uncertain:
                parts.append(f"{len(cell.uncertain)} karakter belirsiz")
            if cell.reviewed:
                parts.append("İncelendi")
            return ", ".join(parts)
        if column.kind == "review":
            return "İncelendi" if text else "İncelenmedi"
        return f"{column.title or 'İnceleme'}: {text}" if text else column.title

    def flags(self, index):
        base = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if index.isValid() and self.columns[index.column()].kind in VALUE_KINDS:
            row = self.items[index.row()][0]
            if row.read and self.cell_at(index) is not None:
                base |= Qt.ItemFlag.ItemIsEditable
        return base

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole) -> bool:  # noqa: N802
        if role != Qt.ItemDataRole.EditRole or not self.flags(index) & Qt.ItemFlag.ItemIsEditable:
            return False
        cell = self.cell_at(index)
        row = self.items[index.row()][0]
        text = str(value)
        unchanged = cell.value is not None and cell.reviewed and text == cell.value.value
        if not unchanged:
            self.edited.emit(row, cell.key, text)
        return True

    # Sorting (the header's click; the view keeps the indicator)
    def sort(self, column: int, order=Qt.SortOrder.AscendingOrder) -> None:
        if not 0 <= column < len(self.columns):
            return
        self.layoutAboutToBeChanged.emit()
        self._sort = (column, order)
        self._apply_sort()
        self.layoutChanged.emit()

    def sort_state(self) -> tuple[int, Qt.SortOrder]:
        return self._sort

    def _apply_sort(self) -> None:
        column_no, order = self._sort
        if not self.columns or column_no >= len(self.columns):
            return
        column = self.columns[column_no]

        def key(item: tuple[Row, Cell | None]):
            row, sampled = item
            if column.kind == "pages":
                return (row.first, row.number)
            if column.kind == "guven":
                return (*_guven_sort(row, sampled), row.number)
            if column.kind in ("var", "value", "name"):
                cell = sampled if column.kind != "var" else row.cell(column.key)
                text = (cell.title if column.kind == "name" else cell.text) if cell else ""
                number = _as_number(text) if column.style == "number" else None
                return (number is None, number or 0, text.casefold(), row.number)
            if column.kind == "review":
                reviewed = sampled.reviewed if sampled is not None else row.reviewed
                return (reviewed, row.number)
            return (row.number, sampled.key if sampled is not None else "")

        self.items.sort(key=key, reverse=order == Qt.SortOrder.DescendingOrder)


def _as_number(text: str) -> float | None:
    try:
        return float(text.replace(".", "").replace(",", ".").replace(" ", ""))
    except ValueError:
        return None


# Painting
class Fonts:
    """The type roles the table paints with, rebuilt after a theme or text-size change."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        m = theme.manager()
        self.body = m.font("body")
        self.strong = m.font("body-strong")
        self.num = m.font("num")
        self.value = m.font("value")
        self.caption = m.font("caption-strong")


def paint_marked(painter: QPainter, rect: QRectF, text: str, font: QFont, colour: QColor,
                 marks: tuple[int, ...] = (), style: str = "uncertain",
                 right: bool = False) -> None:
    """One line of text with marked characters: "uncertain" = check wash + a 2 px rider-edge
    underline (what the reader was unsure of); "changed" = accent text + a 2 px accent
    underline (what the suggestion changes). Elides on the right when it does not fit."""
    m = theme.manager()
    metrics = QFontMetricsF(font)
    full = metrics.horizontalAdvance(text)
    if full > rect.width():
        text = metrics.elidedText(text, Qt.TextElideMode.ElideRight, rect.width())
        full = metrics.horizontalAdvance(text)
    x0 = rect.right() - full if right else rect.left()
    baseline = rect.center().y() + (metrics.ascent() - metrics.descent()) / 2
    top = baseline - metrics.ascent()
    height = metrics.ascent() + metrics.descent()
    spans = []
    for i in marks:
        if i >= len(text) or text[i] == "…":
            continue
        left = x0 + metrics.horizontalAdvance(text[:i])
        spans.append(QRectF(left, top, metrics.horizontalAdvance(text[: i + 1]) - left + x0,
                            height))
    painter.setFont(font)
    if style == "uncertain":
        painter.setPen(Qt.PenStyle.NoPen)
        for span in spans:
            painter.setBrush(m.color("check-wash"))
            painter.drawRoundedRect(span.adjusted(-1, 0, 1, 0), 2, 2)
            painter.fillRect(QRectF(span.left() - 1, span.bottom() - 2, span.width() + 2, 2),
                             m.color("rider-edge"))
    painter.setPen(colour)
    painter.drawText(QPointF(x0, baseline), text)
    if style == "changed":
        accent = m.color("text-accent")
        for span in spans:
            painter.save()
            painter.setClipRect(span)
            painter.setPen(accent)
            painter.drawText(QPointF(x0, baseline), text)
            painter.restore()
            painter.fillRect(QRectF(span.left(), span.bottom() - 2, span.width(), 2),
                             m.color("accent"))


def paint_level(painter: QPainter, rect: QRectF, level: str, percent: int | None,
                fonts: Fonts, icon_size: int = 16, ink: str | None = None) -> None:
    """Güven: icon + word + "%55" (A .st): the word carries the meaning, colour confirms.
    `ink` paints all of it in one role (high contrast on a Highlight row)."""
    m = theme.manager()
    name, role, word, strong = LEVELS[level]
    role = ink or role
    x = rect.left()
    icons.paint(painter, name, QRectF(x, rect.center().y() - icon_size / 2, icon_size,
                                      icon_size), m.hex(role))
    x += icon_size + 6  # A .st gap
    font = fonts.strong if strong else fonts.body
    painter.setFont(font)
    painter.setPen(m.color(role))
    width = QFontMetricsF(font).horizontalAdvance(word)
    painter.drawText(QRectF(x, rect.top(), rect.right() - x, rect.height()),
                     Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, word)
    if percent is not None and level not in ("okunamadi", "okunmadi"):
        painter.setFont(fonts.num)
        painter.setPen(m.color(ink or "text-2"))
        gap = QFontMetricsF(font).horizontalAdvance(" ")
        painter.drawText(QRectF(x + width + gap, rect.top(), rect.right() - x - width - gap,
                                rect.height()),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                         f"%{percent}")


def level_width(level: str, percent: int | None, fonts: Fonts) -> int:
    word = LEVELS[level][2]
    font = fonts.strong if LEVELS[level][3] else fonts.body
    width = 16 + 6 + QFontMetricsF(font).horizontalAdvance(word)
    if percent is not None:
        width += QFontMetricsF(font).horizontalAdvance(" ")
        width += QFontMetricsF(fonts.num).horizontalAdvance(f"%{percent}")
    return int(width) + 1


class ValuesDelegate(QStyledItemDelegate):
    """Paints A's table: row hairlines, the selected row fill with its 3 px accent bar, the
    review mark, values in their font with uncertain characters tinted, and Güven."""

    def __init__(self, view: ValuesTable) -> None:
        super().__init__(view)
        self.view = view
        self.fonts = Fonts()
        theme.follow(self, self.fonts.reset, "degerler-fonts")

    def sizeHint(self, option, index) -> QSize:  # noqa: N802
        return QSize(WIDTHS.get(index.data(KIND_ROLE).kind, 120), theme.manager().size("row-h"))

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        m = theme.manager()
        column: Column = index.data(KIND_ROLE)
        row: Row = index.data(ROW_ROLE)
        rect = QRectF(option.rect)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        selection = self.view.selectionModel()
        current = self.view.currentIndex()
        selected = selection is not None and selection.isRowSelected(index.row(), QModelIndex())
        hc = m.theme() == "hc"  # a selected row is a Highlight fill with HighlightText
        ink = "text-on-accent" if hc and selected else None
        if selected:
            painter.fillRect(rect, m.color("accent" if hc else "selected"))
        if index.row() < index.model().rowCount() - 1:
            painter.fillRect(QRectF(rect.left(), rect.bottom(), rect.width(), 1),
                             m.color("stroke-soft"))
        if index.column() == 0 and current.isValid() and current.row() == index.row():
            painter.fillRect(QRectF(rect.left(), rect.top(), 3, rect.height()),
                             m.color(ink or "accent"))
        s3, s4 = m.size("s3"), m.size("s4")
        inner = rect.adjusted(s4 if column.kind == "review" else s3, 0,
                              0 if column.kind == "review" else -s3, -1)
        kind = column.kind
        sampled = index.model().items[index.row()][1]
        if kind == "review":
            reviewed = sampled.reviewed if sampled is not None else row.reviewed
            icon = "circle-check" if reviewed else ("circle-dashed" if sampled else "")
            if icon:
                icons.paint(painter, icon, QRectF(inner.left(), inner.center().y() - 9, 16, 16),
                            m.hex(ink or ("ok" if reviewed else "text-2")))
        elif kind == "doc":
            self._text(painter, inner, str(row.number), self.fonts.num, m.color(ink or "text"),
                       True)
        elif kind == "pages":
            self._text(painter, inner, row.pages, self.fonts.num, m.color(ink or "text-2"))
        elif kind == "name":
            self._text(painter, inner, sampled.title if sampled else "", self.fonts.body,
                       m.color(ink or "text"))
        elif kind in VALUE_KINDS:
            self._value(painter, inner, index.model().cell_at(index), column, ink)
        elif kind == "guven":
            level = sampled.level if sampled is not None else row.level
            percent = sampled.percent if sampled is not None else row.percent
            paint_level(painter, inner.adjusted(0, 0, s3 - 4, 0), level, percent, self.fonts,
                        ink=ink)
        if (kind in VALUE_KINDS and current == index and self.view.hasFocus()
                and self.view.state() != QAbstractItemView.State.EditingState):
            self._focus_ring(painter, rect)
        painter.restore()

    @staticmethod
    def _text(painter: QPainter, rect: QRectF, text: str, font: QFont, colour: QColor,
              right: bool = False) -> None:
        painter.setFont(font)
        painter.setPen(colour)
        shown = QFontMetricsF(font).elidedText(text, Qt.TextElideMode.ElideRight, rect.width())
        align = Qt.AlignmentFlag.AlignRight if right else Qt.AlignmentFlag.AlignLeft
        painter.drawText(rect, Qt.AlignmentFlag.AlignVCenter | align, shown)

    def _value(self, painter: QPainter, rect: QRectF, cell: Cell | None, column: Column,
               ink: str | None = None) -> None:
        m = theme.manager()
        if cell is None or cell.value is None:
            return
        if cell.level == "okunamadi" or not cell.text:
            self._text(painter, rect, "boş", self.fonts.body, m.color(ink or "text-2"),
                       column.right)
            return
        style = column.style if column.kind == "var" else column_kind([cell.text])
        font = {"number": self.fonts.num, "date": self.fonts.num,
                "code": self.fonts.value}.get(style, self.fonts.body)
        paint_marked(painter, rect, cell.text, font, m.color(ink or "text"), cell.uncertain,
                     right=column.right)

    @staticmethod
    def _focus_ring(painter: QPainter, rect: QRectF) -> None:
        """D11 on the current value: 2 px outer + 1 px inner ring, inside the cell."""
        m = theme.manager()
        ring = rect.adjusted(3, 3, -3, -4)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(m.color("focus-outer"), 2))
        painter.drawRoundedRect(ring, 4, 4)
        painter.setPen(QPen(m.color("focus-inner"), 1))
        painter.drawRoundedRect(ring.adjusted(1.5, 1.5, -1.5, -1.5), 3, 3)

    # The in-place editor: the same box, inset 4 px (zero layout shift)
    def createEditor(self, parent, option, index) -> QWidget:  # noqa: N802
        editor = QLineEdit(parent)
        editor.setFont(self.fonts.value)
        editor.setAccessibleName(f"{index.data(KIND_ROLE).title or 'Değer'} düzenle")
        editor.setProperty("focusRadius", 4)
        return editor

    def setEditorData(self, editor, index) -> None:  # noqa: N802
        editor.setText(index.data(Qt.ItemDataRole.EditRole) or "")
        editor.end(False)

    def setModelData(self, editor, model, index) -> None:  # noqa: N802
        """Store only what was typed, or what Enter confirmed: Tab or a click elsewhere on an
        untouched editor must not accept a suggestion."""
        if editor.isModified() or editor.property("submit"):
            model.setData(index, editor.text(), Qt.ItemDataRole.EditRole)

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        if isinstance(obj, QLineEdit) and event.type() == QEvent.Type.KeyPress and \
                event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            obj.setProperty("submit", True)
        return super().eventFilter(obj, event)

    def updateEditorGeometry(self, editor, option, index) -> None:  # noqa: N802
        editor.setGeometry(option.rect.adjusted(4, 4, -4, -4))


class ValuesHeader(QHeaderView):
    """A's header: 36 px, caption semibold in text-2, a hairline below, the sorted column in
    text with its chevron; the first column is the review mark."""

    def __init__(self, parent=None) -> None:
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.fonts = Fonts()
        theme.follow(self, self.fonts.reset, "degerler-header-fonts")
        self.setSectionsClickable(True)
        self.setHighlightSections(False)
        self.setSortIndicatorShown(True)
        self.setMinimumSectionSize(40)
        self.setStretchLastSection(False)

    def sizeHint(self) -> QSize:  # noqa: N802
        hint = super().sizeHint()
        return QSize(hint.width(), theme.manager().size("header-h"))

    def paintSection(self, painter: QPainter, rect: QRect, logical: int) -> None:  # noqa: N802
        m = theme.manager()
        column: Column | None = self.model().headerData(logical, Qt.Orientation.Horizontal,
                                                        KIND_ROLE) if self.model() else None
        painter.save()
        painter.fillRect(rect, m.color("card"))
        painter.fillRect(QRect(rect.left(), rect.bottom(), rect.width(), 1), m.color("stroke"))
        if column is None:
            painter.restore()
            return
        sorted_here = self.isSortIndicatorShown() and self.sortIndicatorSection() == logical
        colour = m.color("text" if sorted_here else "text-2")
        s3, s4 = m.size("s3"), m.size("s4")
        inner = QRectF(rect).adjusted(s4 if column.kind == "review" else s3, 0,
                                      0 if column.kind == "review" else -s3, -1)
        if column.kind == "review":
            icons.paint(painter, "circle-check",
                        QRectF(inner.left() + 1, inner.center().y() - 7, 14, 14), m.hex("text-2"))
            painter.restore()
            return
        font = self.fonts.caption
        metrics = QFontMetricsF(font)
        chevron = 16 if sorted_here else 0
        if column.right:  # a narrow number column may use its left padding (A: "Belge ^")
            inner.setLeft(rect.left() + 4)
        text = metrics.elidedText(column.title, Qt.TextElideMode.ElideRight,
                                  inner.width() - chevron)
        width = metrics.horizontalAdvance(text) + chevron
        left = inner.right() - width if column.right else inner.left()
        painter.setFont(font)
        painter.setPen(colour)
        painter.drawText(QRectF(left, inner.top(), width, inner.height()),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)
        if sorted_here:
            up = self.sortIndicatorOrder() == Qt.SortOrder.AscendingOrder
            icons.paint(painter, "chevron-up" if up else "chevron-down",
                        QRectF(left + width - 14, inner.center().y() - 7, 14, 14),
                        m.hex("text"))
        painter.restore()


class KeyHint(QLabel):
    """A's quiet key hint under the cell being edited: keys as text, no keycaps."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.hide()
        theme.bind_style(self, lambda: (
            f"QLabel {{ background: {theme.manager().hex('popover')}; "
            f"color: {theme.manager().hex('text-2')}; "
            f"border: 1px solid {theme.manager().hex('stroke')}; border-radius: 4px; "
            f"padding: 0 {theme.manager().size('s3')}px; "
            f"font-size: {theme.manager().size('fs-caption')}px; }}"))

    def set_keys(self, pairs: list[tuple[str, str]]) -> None:
        text = theme.manager().hex("text")
        gap = "&nbsp;" * 5
        self.setText(gap.join(
            f"<span style='color:{text}; font-weight:600'>{key}</span>&nbsp;&nbsp;{word}"
            for key, word in pairs))
        self.setAccessibleName(", ".join(f"{k} {w}" for k, w in pairs))
        self.setFixedHeight(36)
        self.adjustSize()


class ValuesTable(QTableView):
    """The view: Tab and Shift+Tab walk the values, the editor's Enter commits and moves on,
    and A's key hint follows the open editor."""

    submitted = Signal(int)  # the editor closed: 1 = Enter, 0 = Esc
    return_pressed = Signal()
    hint_keys: Callable[[], list[tuple[str, str]]] | None = None

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        m = theme.manager()
        self.setHorizontalHeader(ValuesHeader(self))
        self.verticalHeader().hide()
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.verticalHeader().setDefaultSectionSize(m.size("row-h"))
        self.verticalHeader().setMinimumSectionSize(m.size("row-h"))
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked
                             | QAbstractItemView.EditTrigger.EditKeyPressed)
        self.setTabKeyNavigation(False)
        self.setSortingEnabled(True)
        self.setItemDelegate(ValuesDelegate(self))
        self.setAccessibleName("Değerler tablosu")
        self.hint = KeyHint(self.viewport())
        theme.follow(self, self._rescale, "degerler-rows")

    def _rescale(self) -> None:
        row = theme.manager().size("row-h")
        self.verticalHeader().setDefaultSectionSize(row)
        self.verticalHeader().setMinimumSectionSize(row)

    def model(self) -> ValuesModel:  # typed
        return super().model()

    # Value-to-value movement
    def step_value(self, index: QModelIndex, step: int) -> QModelIndex:
        """The next (step 1) or previous (-1) value cell after `index`, row by row."""
        model = self.model()
        columns = model.value_columns()
        if not columns or model.rowCount() == 0:
            return QModelIndex()
        cells = [(r, c) for r in range(model.rowCount()) for c in columns]
        here = (index.row(), index.column()) if index.isValid() else None
        if here in cells:
            position = cells.index(here) + step
        elif here is None:
            position = 0 if step > 0 else len(cells) - 1
        else:  # on a non-value column: the next value to the right / left in the row
            after = [i for i, rc in enumerate(cells) if rc > here]
            position = (after[0] if after else len(cells)) if step > 0 else \
                (after[0] - 1 if after else len(cells) - 1)
        if not 0 <= position < len(cells):
            return QModelIndex()
        return model.index(*cells[position])

    def moveCursor(self, action, modifiers) -> QModelIndex:  # noqa: N802
        if action in (QAbstractItemView.CursorAction.MoveNext,
                      QAbstractItemView.CursorAction.MovePrevious):
            step = 1 if action == QAbstractItemView.CursorAction.MoveNext else -1
            target = self.step_value(self.currentIndex(), step)
            return target if target.isValid() else self.currentIndex()
        return super().moveCursor(action, modifiers)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        key = event.key()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and \
                self.state() != QAbstractItemView.State.EditingState:
            self.return_pressed.emit()  # only reached when no window action took the key
            event.accept()
            return
        super().keyPressEvent(event)

    def focusNextPrevChild(self, forward: bool) -> bool:  # noqa: N802
        """Tab / Shift+Tab (QWidget routes them here first): the next or previous value; from
        the last one, focus leaves the table (F6 also moves between regions)."""
        if self.state() == QAbstractItemView.State.EditingState:
            return super().focusNextPrevChild(forward)
        target = self.step_value(self.currentIndex(), 1 if forward else -1)
        if target.isValid():
            self.setCurrentIndex(target)
            self.scrollTo(target)
            return True
        return QWidget.focusNextPrevChild(self, forward)

    # The editor and its key hint
    def edit(self, index, trigger=QAbstractItemView.EditTrigger.AllEditTriggers,
             event=None) -> bool:
        opened = super().edit(index, trigger, event)
        if opened:
            self._show_hint(index)
        return opened

    def open_editor(self, index: QModelIndex) -> bool:
        if not index.isValid() or not self.model().flags(index) & Qt.ItemFlag.ItemIsEditable:
            return False
        self.setCurrentIndex(index)
        self.scrollTo(index)
        opened = self.edit(index, QAbstractItemView.EditTrigger.AllEditTriggers, None)
        return opened

    def _show_hint(self, index: QModelIndex) -> None:
        editor = self.open_editor_widget()
        if editor is not None:  # A: the caret at the end, nothing selected
            editor.deselect()
            editor.end(False)
        if self.hint_keys is None:
            return
        self.hint.set_keys(self.hint_keys())
        rect = self.visualRect(index)
        x = max(0, min(rect.left() + 8, self.viewport().width() - self.hint.width()))
        y = rect.bottom() + 2
        if y + self.hint.height() > self.viewport().height():
            y = rect.top() - self.hint.height() - 2
        self.hint.move(x, y)
        self.hint.show()
        self.hint.raise_()

    def closeEditor(self, editor, hint) -> None:  # noqa: N802
        self.hint.hide()
        super().closeEditor(editor, hint)
        if hint == QAbstractItemDelegate.EndEditHint.SubmitModelCache:
            self.submitted.emit(1)
        elif hint == QAbstractItemDelegate.EndEditHint.RevertModelCache:
            self.submitted.emit(0)

    def is_editing(self) -> bool:
        return self.state() == QAbstractItemView.State.EditingState

    def open_editor_widget(self) -> QLineEdit | None:
        index = self.currentIndex()
        widget = self.indexWidget(index) if index.isValid() else None
        if isinstance(widget, QLineEdit):
            return widget
        editors = [e for e in self.viewport().findChildren(QLineEdit) if e.isVisible()]
        return editors[0] if editors else None
