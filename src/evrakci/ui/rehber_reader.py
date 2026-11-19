"""The reading area of Rehber: a QTextBrowser that shows the guide, marks search hits and knows
where each section starts. Hits are painted as extra selections, so a search never edits the
document and 1,000 hits cost nothing more than the first."""

from __future__ import annotations

from bisect import bisect_right

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import (
    QColor,
    QFont,
    QTextBlockFormat,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextFrameFormat,
)
from PySide6.QtWidgets import QTextBrowser, QTextEdit, QWidget

from evrakci.ui import theme
from evrakci.ui.chrome import make_icon
from evrakci.ui.rehber_content import Guide, Look, find_in_text, guide_html

HEADING_LEVEL = 2  # <h2>: one per section


class Reader(QTextBrowser):
    """The article. `show_guide` renders; `search` finds; `set_current` marks and reveals."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAccessibleName("Tarama rehberi")
        self.setOpenLinks(False)
        self.setTabChangesFocus(True)  # Tab leaves the text (it is read-only)
        self.setFrameShape(QTextBrowser.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.viewport().setAutoFillBackground(False)
        self.document().setDocumentMargin(0)
        self._tops: list[int] = []
        self._starts: list[int] = []
        self._hits: list[tuple[int, int]] = []
        self._current = -1
        self._margins = (0, 0, 0)  # top, side, max text width in px
        self._look: Look | None = None

    def focusNextPrevChild(self, next: bool) -> bool:  # noqa: N802, A002
        """Tab goes on to the next control (QTextBrowser would walk its links and keep
        focus); the guide's links are reached with the table of contents."""
        return QWidget.focusNextPrevChild(self, next)

    # -- the document ---------------------------------------------------------------------
    def show_guide(self, guide: Guide, look: Look, margins: tuple[int, int, int],
                   font: QFont, note: bool = True) -> None:
        """Render `guide` (the scroll position is the caller's business) and find where each
        section starts."""
        self._look = look
        self._margins = margins
        doc = self.document()
        doc.setDefaultFont(font)
        doc.setIndentWidth(round(look.gap[4] * 1.2))  # A: list text 28 px from the margin
        doc.addResource(QTextDocument.ResourceType.ImageResource, QUrl("rehber:info"),
                        make_icon("info", size=look.body).pixmap(look.body, look.body))
        self.setHtml(guide_html(guide, look, note))
        self._mark_headings(guide)
        self.apply_margins()
        self._locate_sections()
        self._paint()

    def _mark_headings(self, guide: Guide) -> None:
        """Give the title and the section heads their heading level (1 and 2): they are
        written as paragraphs at A's sizes, since Qt's <h1>/<h2> override the CSS size."""
        titles = [(1, guide.title)] + [(HEADING_LEVEL, s.title) for s in guide.sections]
        block = self.document().begin()
        while block.isValid() and titles:
            level, title = titles[0]
            if block.text().strip() == title:
                fmt = QTextBlockFormat()
                fmt.setHeadingLevel(level)
                QTextCursor(block).mergeBlockFormat(fmt)
                titles.pop(0)
            block = block.next()

    def apply_margins(self) -> None:
        """A's reading column: s6 above, s8 at the sides, the text at most 680 px wide."""
        top, side, widest = self._margins
        frame = self.document().rootFrame()
        fmt = frame.frameFormat()
        room = self.viewport().width() - 2 * side
        fmt.setLeftMargin(side)
        fmt.setRightMargin(side + max(0, room - widest))
        fmt.setTopMargin(top)
        fmt.setBottomMargin(side)
        fmt.setBorder(0)
        fmt.setBorderStyle(QTextFrameFormat.BorderStyle.BorderStyle_None)
        frame.setFrameFormat(fmt)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self._look is not None:
            self.apply_margins()
            self._locate_sections()

    def _locate_sections(self) -> None:
        """y of every section heading, and its first document position."""
        self._tops, self._starts = [], []
        layout = self.document().documentLayout()
        block = self.document().begin()
        while block.isValid():
            if block.blockFormat().headingLevel() == HEADING_LEVEL:
                self._tops.append(round(layout.blockBoundingRect(block).top()))
                self._starts.append(block.position())
            block = block.next()

    def section_tops(self) -> list[int]:
        return list(self._tops)

    def scroll_to_section(self, row: int, lead: int = 0) -> None:
        if 0 <= row < len(self._tops):
            self.verticalScrollBar().setValue(max(0, self._tops[row] - lead))

    def section_at_scroll(self, tolerance: int) -> int:
        """The section being read: the last heading at or above the top edge (+ `tolerance`);
        the last one once the scroll bar is at the bottom."""
        bar = self.verticalScrollBar()
        if not self._tops:
            return 0
        if bar.maximum() > 0 and bar.value() >= bar.maximum() - 1:
            return len(self._tops) - 1
        return max(0, bisect_right(self._tops, bar.value() + tolerance) - 1)

    def section_of(self, position: int) -> int:
        return max(0, bisect_right(self._starts, position) - 1)

    # -- search -----------------------------------------------------------------------------
    def search(self, query: str) -> list[tuple[int, int]]:
        """Find `query` (Turkish-folded) in the text; the hits are painted until `set_hits`."""
        hits: list[tuple[int, int]] = []
        block = self.document().begin()
        while block.isValid():
            text = block.text()
            if text:
                hits += [(block.position() + start, length)
                         for start, length in find_in_text(text, query)]
            block = block.next()
        self.set_hits(hits)
        return hits

    def set_hits(self, hits: list[tuple[int, int]], current: int = -1) -> None:
        self._hits = hits
        self._current = current if 0 <= current < len(hits) else -1
        self._paint()

    def hits(self) -> list[tuple[int, int]]:
        return list(self._hits)

    def current(self) -> int:
        return self._current

    def set_current(self, index: int, reveal: bool = True) -> None:
        """Mark hit `index` as the current one; scroll only when it is not already in view."""
        if not self._hits:
            return
        self._current = index % len(self._hits)
        self._paint()
        if reveal:
            self.reveal(self._hits[self._current][0])

    def reveal(self, position: int) -> None:
        """Bring `position` into the upper half of the view unless it is already comfortably
        visible (no jump when the next hit is on screen)."""
        cursor = QTextCursor(self.document())
        cursor.setPosition(position)
        rect = self.cursorRect(cursor)
        height = self.viewport().height()
        if rect.top() >= height * 0.08 and rect.bottom() <= height * 0.92:
            return
        bar = self.verticalScrollBar()
        bar.setValue(bar.value() + rect.top() - height // 3)

    def _paint(self) -> None:
        m = theme.manager()
        marks: list[QTextEdit.ExtraSelection] = []
        for index, (start, length) in enumerate(self._hits):
            cursor = QTextCursor(self.document())
            cursor.setPosition(start)
            cursor.setPosition(start + length, QTextCursor.MoveMode.KeepAnchor)
            fmt = QTextCharFormat()
            if index == self._current:
                fmt.setBackground(QColor(m.hex("accent")))
                fmt.setForeground(QColor(m.hex("text-on-accent")))
            else:
                fmt.setBackground(QColor(m.hex("selected")))
                fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)
                fmt.setUnderlineColor(QColor(m.hex("accent")))
            mark = QTextEdit.ExtraSelection()
            mark.cursor = cursor
            mark.format = fmt
            marks.append(mark)
        self.setExtraSelections(marks)
