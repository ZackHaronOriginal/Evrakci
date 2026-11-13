"""Pieces of the Rehber screen (final-a/rehber.html): the search field, the contents list, the
empty search state and the status bar text. All colours and sizes come from `theme.manager()`."""

from __future__ import annotations

from PySide6.QtCore import QModelIndex, QSize, Qt, Signal
from PySide6.QtGui import QAction, QKeyEvent, QPainter
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QVBoxLayout,
    QWidget,
)

from evrakci.ui import disa_aktar_icons, theme
from evrakci.ui.chrome import make_icon
from evrakci.ui.disa_aktar_parts import PartsButton

assert disa_aktar_icons  # registers the extra Lucide icons the shared parts use
COUNT_ROLE = Qt.ItemDataRole.UserRole + 1


class SearchField(QLineEdit):
    """A's search field: a leading magnifier, the placeholder "Rehberde ara" with "Ctrl+F" at the
    end while empty, and an x button (Esc) while it holds text. Enter and Shift+Enter ask for
    the next and the previous result; Esc asks to clear."""

    next_requested = Signal()
    previous_requested = Signal()
    clear_requested = Signal()

    def __init__(self, key_hint: str = "Ctrl+F", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._hint = key_hint
        self.setPlaceholderText("Rehberde ara")
        self.setAccessibleName("Rehberde ara")
        self.setToolTip(f"Rehberde ara ({key_hint})")
        self.lead = QAction("Ara", self)
        self.addAction(self.lead, QLineEdit.ActionPosition.LeadingPosition)
        self.clear_action = QAction("Aramayı temizle", self)
        self.clear_action.setToolTip("Aramayı temizle (Esc)")
        self.clear_action.triggered.connect(self.clear_requested)
        self.addAction(self.clear_action, QLineEdit.ActionPosition.TrailingPosition)
        self.clear_action.setVisible(False)
        self.textChanged.connect(self._sync)
        theme.follow(self, self._restyle, "search-field")

    def _restyle(self) -> None:
        self.lead.setIcon(make_icon("search"))
        self.clear_action.setIcon(make_icon("x"))
        self._sync()

    def _sync(self, *_args) -> None:
        self.clear_action.setVisible(bool(self.text()))
        m = theme.manager()
        reserve = 0
        if not self.text():
            reserve = self.fontMetrics().horizontalAdvance(self._hint) + m.size("s3")
        self.setTextMargins(0, 0, reserve, 0)

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        if self.text():
            return
        m = theme.manager()
        painter = QPainter(self)
        painter.setFont(m.font("caption"))
        painter.setPen(m.color("text-2"))
        painter.drawText(self.rect().adjusted(0, 0, -m.size("s3"), 0),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                         self._hint)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        key = event.key()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.previous_requested.emit()
            else:
                self.next_requested.emit()
            return
        if key == Qt.Key.Key_Escape and self.text():
            self.clear_requested.emit()
            return
        super().keyPressEvent(event)


class _TocDelegate(QStyledItemDelegate):
    """The row as the style draws it (selected fill, accent bar, focus ring) plus the hit count
    at the right end in caption numerals."""

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:  # noqa: N802
        return QSize(option.rect.width(), theme.manager().size("row-h"))

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        super().paint(painter, option, index)
        count = index.data(COUNT_ROLE)
        if not count:
            return
        m = theme.manager()
        painter.save()
        painter.setFont(m.font("caption-num"))
        painter.setPen(m.color("text-2"))
        painter.drawText(option.rect.adjusted(0, 0, -m.size("s3"), 0),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, str(count))
        painter.restore()


class TocList(QListWidget):
    """"İçindekiler": one row per section, the current one marked, hit counts while searching."""

    section_chosen = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("kind", "nav-list")
        self.setAccessibleName("İçindekiler")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setItemDelegate(_TocDelegate(self))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.viewport().setAutoFillBackground(False)
        self._syncing = False
        self.currentRowChanged.connect(self._row_changed)
        self.clicked.connect(lambda index: self.section_chosen.emit(index.row()))
        theme.follow(self, self._restyle, "toc")

    def _restyle(self) -> None:
        self.setFixedHeight(self.count() * theme.manager().size("row-h")
                            + 2 * theme.manager().size("s1"))
        self.setSpacing(0)

    def set_sections(self, titles: list[str]) -> None:
        self._syncing = True
        self.clear()
        for number, title in enumerate(titles, 1):
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.AccessibleTextRole, f"{number}. {title}")
            self.addItem(item)
        self._syncing = False
        self._restyle()

    def set_counts(self, counts: list[int]) -> None:
        """Hit counts per section (0 or an empty list shows none)."""
        for row in range(self.count()):
            n = counts[row] if row < len(counts) else 0
            item = self.item(row)
            item.setData(COUNT_ROLE, n or None)
            title = item.text()
            item.setData(Qt.ItemDataRole.AccessibleTextRole,
                         f"{row + 1}. {title}" + (f", {n} sonuç" if n else ""))
        self.viewport().update()

    def mark(self, row: int | None) -> None:
        """Select `row` (the section being read) without announcing a choice."""
        self._syncing = True
        try:
            if row is None:
                self.setCurrentRow(-1)
                self.clearSelection()
            else:
                self.setCurrentRow(row)
        finally:
            self._syncing = False

    def _row_changed(self, row: int) -> None:
        if not self._syncing and row >= 0:
            self.section_chosen.emit(row)


class EmptyResults(QWidget):
    """A's empty search state: a 48 px mark, "“x” için sonuç yok", one sentence, two buttons
    and the common topics."""

    clear_clicked = Signal()
    keys_clicked = Signal()

    def __init__(self, topics: tuple[str, ...], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        m = theme.manager()
        self.setAccessibleName("Sonuç yok")
        col = QVBoxLayout(self)
        col.setContentsMargins(m.size("s6"), 0, m.size("s6"), m.size("s8"))
        col.setSpacing(0)
        col.addStretch(1)
        self.mark = QLabel()
        self.mark.setFixedSize(48, 48)
        self.mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mark.setProperty("kind", "card")
        col.addWidget(self.mark, 0, Qt.AlignmentFlag.AlignHCenter)
        col.addSpacing(m.size("s4"))
        self.title = QLabel()
        self.title.setProperty("textRole", "panel")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setWordWrap(True)
        self.text = QLabel("Daha kısa bir sözcük deneyin; Türkçe harf fark etmez.")
        self.text.setProperty("textRole", "secondary")
        self.text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text.setWordWrap(True)
        col.addWidget(self.title)
        col.addSpacing(m.size("s1"))
        col.addWidget(self.text)
        col.addSpacing(m.size("s6"))
        row = QHBoxLayout()
        row.setSpacing(m.size("s2"))
        row.addStretch(1)
        self.clear = PartsButton("Aramayı temizle", "x", primary=True, large=True)
        self.keys = PartsButton("Kısayolları göster", "keyboard", large=True)
        self.clear.clicked.connect(self.clear_clicked)
        self.keys.clicked.connect(self.keys_clicked)
        row.addWidget(self.clear)
        row.addWidget(self.keys)
        row.addStretch(1)
        col.addLayout(row)
        col.addSpacing(m.size("s3"))
        self.topics = QLabel("Sık aranan konular: " + ", ".join(topics))
        self.topics.setProperty("textRole", "caption")
        self.topics.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.topics.setWordWrap(True)
        col.addWidget(self.topics)
        col.addStretch(1)
        theme.follow(self, lambda: self.mark.setPixmap(
            make_icon("search", size=24).pixmap(24, 24)), "mark")

    def set_query(self, query: str) -> None:
        self.title.setText(f"“{query}” için sonuç yok")
        self.setAccessibleName(f"“{query}” için sonuç yok")


class StatusText(QLabel):
    """One status bar item: "Bölüm <b>2</b> / 7", the numbers in the text colour."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setTextFormat(Qt.TextFormat.RichText)
        self._parts: tuple[str, ...] = ()

    def set_parts(self, *parts: str) -> None:
        """Alternating plain and strong parts, like `StatusItem.set`."""
        self._parts = parts
        strong = theme.manager().hex("text")
        self.setText("".join(
            f"<span style='color:{strong}; font-weight:600'>{p}</span>" if i % 2 else p
            for i, p in enumerate(parts)))
        self.setAccessibleName("".join(parts))

    def parts(self) -> tuple[str, ...]:
        return self._parts

