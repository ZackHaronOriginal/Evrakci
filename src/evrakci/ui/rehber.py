"""The Rehber tab (final-a/rehber.html): the scanning guide in a reading card, and at the right
the search, the contents list and the printable QR separator sheet.

Ctrl+F searches (Turkish-folded, hits painted), F3 / Shift+F3 step through the hits, Esc clears,
Ctrl+wheel and Ctrl+plus/minus zoom the text, Ctrl+P prints the separator sheets. The shortcut
list at the end of the guide is generated from the action registry.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent, QSize, Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QKeyEvent
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStackedLayout,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from evrakci.pipeline.ocr.models import data_dir
from evrakci.pipeline.separator import make_separator_pdf
from evrakci.ui import actions, theme
from evrakci.ui import rehber_print as printing
from evrakci.ui.chrome import make_icon
from evrakci.ui.disa_aktar_parts import PartsButton
from evrakci.ui.feedback import announce
from evrakci.ui.rehber_content import (
    COMMON_TOPICS,
    Guide,
    Look,
    guide_text,
    parse_guide,
    with_shortcuts,
)
from evrakci.ui.rehber_parts import EmptyResults, SearchField, StatusText, TocList
from evrakci.ui.rehber_reader import Reader
from evrakci.ui.zoomview import ZoomController

__all__ = ["RehberScreen", "guide_text"]

SPLITTER_NAME = "rehber"
ZOOM_KEY = "rehber"
ZOOM_RANGE = (50, 300)
SIDE_W = 368  # A: the aside column at 100 % text (440 at 150 %)
TEXT_WIDTH = 680  # A: .article .doc max-width
NOTE_KEY = "rehber-ipucu"  # prefs flag that remembers "Bir daha gösterme"
ANNOUNCE_MS = 500


def side_width() -> int:
    return SIDE_W if theme.manager().size("fs-body") / 15 < 1.4 else 440


def mono_stack() -> str:
    """A's code font (Cascadia Mono, Consolas) and then the system's own fixed-width font, so
    a code span is monospace on every machine (a generic "monospace" is not resolved by Qt's
    rich text)."""
    from PySide6.QtGui import QFontDatabase

    fixed = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont).family()
    return f"Cascadia Mono, Consolas, '{fixed}', monospace"


class RehberScreen(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("page")
        self.window_ = None
        self.guide: Guide = with_shortcuts(parse_guide(guide_text()))
        self._hits: list[tuple[int, int]] = []
        self._query = ""
        self._section = 0
        self._pin: int | None = None  # a section chosen by the contents list or a hit
        self._internal = False  # a scroll the screen made itself
        self._show_note = True
        self._scale = 0.0
        self._print_dialog = QPrintDialog  # a test swaps it for a dialog that answers at once
        m = theme.manager()

        root = QVBoxLayout(self)
        root.setContentsMargins(m.size("s3"), 0, m.size("s3"), m.size("s3"))
        root.setSpacing(0)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setObjectName(SPLITTER_NAME)
        self.splitter.setChildrenCollapsible(False)
        root.addWidget(self.splitter, 1)

        # Left: the reading card (the guide, or the empty search state)
        self.article = QFrame()
        self.article.setProperty("kind", "card")
        self.article.setAccessibleName("Tarama rehberi")
        stack_host = QVBoxLayout(self.article)
        stack_host.setContentsMargins(1, 1, 1, 1)
        stack_host.setSpacing(0)
        self.text = Reader()
        self.empty = EmptyResults(COMMON_TOPICS)
        self.stack = QStackedLayout()
        self.stack.setContentsMargins(0, 0, 0, 0)
        self.stack.addWidget(self.text)
        self.stack.addWidget(self.empty)
        stack_host.addLayout(self.stack)
        self.splitter.addWidget(self.article)

        # Right: search, contents, separator sheet (F9 toggles it)
        self.side = QWidget()
        self.side.setAccessibleName("Rehber paneli")
        self.side.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        outer = QVBoxLayout(self.side)
        outer.setContentsMargins(0, 0, 0, 0)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.viewport().setAutoFillBackground(False)
        body = QWidget()
        body.setAutoFillBackground(False)
        col = QVBoxLayout(body)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(m.size("s3"))
        self.scroll.setWidget(body)
        outer.addWidget(self.scroll)
        col.addLayout(self._build_find())
        col.addLayout(self._group("İçindekiler", self._build_toc()))
        col.addLayout(self._group("Ayıraç sayfası", self._build_print()))
        col.addStretch(1)
        self.splitter.addWidget(self.side)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)

        self.zoom: ZoomController | None = None
        self._make_zoom(None)
        self._wire()
        self.toc.set_sections(self.guide.titles())
        self._status_section = StatusText()
        self._status_hits = StatusText()
        self._status_hits.hide()
        self.setTabOrder(self.text, self.search)
        self.setTabOrder(self.search, self.previous_button)
        self.setTabOrder(self.previous_button, self.next_button)
        self.setTabOrder(self.next_button, self.toc)
        self.setTabOrder(self.toc, self.count)
        self.setTabOrder(self.count, self.print_button)
        theme.follow(self, self._restyle, "screen")
        QTimer.singleShot(0, self._try_attach)

    # -- building ----------------------------------------------------------------------------
    def _group(self, title: str, card: QFrame) -> QVBoxLayout:
        box = QVBoxLayout()
        box.setSpacing(0)
        label = QLabel(title)
        label.setProperty("kind", "group-label")
        box.addWidget(label)
        box.addWidget(card)
        return box

    def _card(self) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setProperty("kind", "card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(0, 0, 0, 0)
        return card, lay

    def _small_button(self, icon: str, name: str) -> QToolButton:
        button = QToolButton()
        button.setProperty("kind", "icon")
        button.setProperty("sizeVariant", "sm")
        button.setAutoRaise(True)
        button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        button.setAccessibleName(name)
        button.setToolTip(name)
        button.setProperty("lucide", icon)
        return button

    def _build_find(self) -> QVBoxLayout:
        m = theme.manager()
        box = QVBoxLayout()
        box.setSpacing(m.size("s2"))
        key = actions.key_text(actions.spec("app.bul").shortcuts[0])
        self.search = SearchField(key)
        box.addWidget(self.search)
        row = QHBoxLayout()
        row.setContentsMargins(m.size("s1"), 0, 0, 0)
        row.setSpacing(m.size("s1"))
        self.result = QLabel()
        self.result.setTextFormat(Qt.TextFormat.RichText)
        self.result.setProperty("textRole", "caption")
        row.addWidget(self.result)
        row.addStretch(1)
        self.previous_button = self._small_button(
            "chevron-up", f"Önceki sonuç ({actions.key_text('Shift+F3')})")
        self.next_button = self._small_button(
            "chevron-down", f"Sonraki sonuç ({actions.key_text('F3')})")
        row.addWidget(self.previous_button)
        row.addWidget(self.next_button)
        box.addLayout(row)
        return box

    def _build_toc(self) -> QFrame:
        card, lay = self._card()
        s1 = theme.manager().size("s1")
        lay.setContentsMargins(s1, s1, s1, s1)
        self.toc = TocList()
        lay.addWidget(self.toc)
        return card

    def _build_print(self) -> QFrame:
        m = theme.manager()
        card, lay = self._card()
        lay.setContentsMargins(m.size("s4"), m.size("s3"), m.size("s4"), m.size("s4"))
        lay.setSpacing(m.size("s3"))
        line = QHBoxLayout()
        line.setSpacing(m.size("s3"))
        self.count_label = QLabel("Kaç adet")
        self.count_label.setProperty("textRole", "caption")
        self.count = QSpinBox()
        self.count.setRange(*printing.SHEETS)
        self.count.setValue(20)
        self.count.setAlignment(Qt.AlignmentFlag.AlignRight)
        # A's field is a clean box: no spin buttons and no arrow images (the arrows were the
        # stray tick at the right edge); Up/Down and PgUp/PgDn still step. Only the 3:1 bottom
        # edge every input has.
        self.count.setStyleSheet(
            f"QSpinBox {{ padding: 0 {m.size('s3')}px; }}"
            "QSpinBox::up-button, QSpinBox::down-button { width: 0; height: 0; border: 0;"
            " image: none; }"
            "QSpinBox::up-arrow, QSpinBox::down-arrow { image: none; width: 0; height: 0; }")
        self.count.setAccessibleName("Kaç adet ayıraç sayfası")
        self.count.setToolTip("Yazdırılacak ayıraç sayfası sayısı (1 ile 200 arası)")
        self.count_label.setBuddy(self.count)
        line.addWidget(self.count_label)
        line.addWidget(self.count)
        line.addWidget(QLabel("sayfa"))
        line.addStretch(1)
        lay.addLayout(line)
        paper = QHBoxLayout()
        paper.setSpacing(m.size("s3"))
        paper_key = QLabel("Kâğıt")
        paper_key.setProperty("textRole", "caption")
        self.paper = QLabel("A4, iki yüze aynı QR")
        paper.addWidget(paper_key)
        paper.addWidget(self.paper, 1)
        lay.addLayout(paper)
        self.paper_key = paper_key
        key = actions.key_text(actions.spec("rehber.yazdir").shortcuts[0])
        self.print_button = PartsButton("Yazdır", "printer", key, primary=True, large=True,
                                        accessible=f"Ayıraç sayfasını yazdır ({key})")
        self.print_button.setToolTip(f"Ayıraç sayfasını yazdır ({key})")
        lay.addWidget(self.print_button)
        self._key_column = (self.count_label, paper_key)
        return card

    def _wire(self) -> None:
        self.search.textChanged.connect(self._search_changed)
        self.search.next_requested.connect(lambda: self.step(1))
        self.search.previous_requested.connect(lambda: self.step(-1))
        self.search.clear_requested.connect(self.clear_search)
        self.next_button.clicked.connect(lambda: self.step(1))
        self.previous_button.clicked.connect(lambda: self.step(-1))
        self.empty.clear_clicked.connect(self.clear_search)
        self.empty.keys_clicked.connect(self.show_keys)
        self.toc.section_chosen.connect(self.go_to_section)
        self.print_button.clicked.connect(self.print_separators)
        self.text.anchorClicked.connect(self._link)
        self.text.verticalScrollBar().valueChanged.connect(self._scrolled)
        self.text.installEventFilter(self)
        self.toc.installEventFilter(self)
        self._announce = QTimer(self)
        self._announce.setSingleShot(True)
        self._announce.setInterval(ANNOUNCE_MS)
        self._announce.timeout.connect(lambda: announce(self.result, self._result_text()))

    # -- the window --------------------------------------------------------------------------
    def _try_attach(self) -> None:
        window = self.window()
        if self.window_ is None and window is not self and hasattr(window, "registry"):
            self.attach(window)

    def attach(self, window) -> None:
        """Hook this tab into its MainWindow: the registry actions it does not wire itself, the
        extra command-bar button, the status bar items, the saved zoom and the toasts."""
        if self.window_ is window:
            return
        self.window_ = window
        r = window.registry
        r.connect_tab("app.bul", "rehber", self.focus_search)
        r.connect_tab("app.sonraki_sonuc", "rehber", lambda: self.step(1))
        r.connect_tab("app.onceki_sonuc", "rehber", lambda: self.step(-1))
        r.connect("rehber.yazdir", self.print_separators)
        r.connect("rehber.pdf_ac", self.open_separators)
        r.connect("rehber.aramayi_temizle", self.clear_search)
        layout = window.status_slot("rehber").layout()
        layout.addWidget(self._status_section)
        layout.addWidget(self._status_hits)
        layout.addStretch(1)
        prefs = getattr(window, "prefs", None)
        self._make_zoom(prefs)
        window.register_zoom("rehber", self.zoom, "Rehber yazısı")
        if prefs is not None and (prefs.flag(NOTE_KEY)
                                  or prefs.splitter_sizes(NOTE_KEY) == [1]):  # older builds
            self._show_note = False
        self._render()
        self._sync_status()
        self._sync_hit_actions()

    def _active(self) -> bool:
        """The app-wide search keys (Ctrl+F, F3) reach every tab's slot; act only on Rehber."""
        window = self.window_
        return window is None or window.current_tab() == "rehber"

    def _toaster(self):
        return getattr(self.window_, "toaster", None)

    def _prefs(self):
        return getattr(self.window_, "prefs", None)

    # -- look and zoom -----------------------------------------------------------------------
    def _make_zoom(self, prefs) -> None:
        if self.zoom is not None:
            self.zoom.zoom_changed.disconnect(self._zoomed)
            self.text.removeEventFilter(self.zoom)
            self.text.viewport().removeEventFilter(self.zoom)
            self.zoom.deleteLater()
        self.zoom = ZoomController(self.text, prefs, ZOOM_KEY, *ZOOM_RANGE, step=10)
        self.zoom.zoom_changed.connect(self._zoomed)

    def _zoomed(self, _percent: int) -> None:
        self._render()

    def _look(self) -> Look:
        m = theme.manager()
        k = (self.zoom.zoom() if self.zoom is not None else 100) / 100

        def px(name: str) -> int:
            return round(m.size(name) * k)

        return Look(text=m.hex("text"), text_2=m.hex("text-2"), stroke=m.hex("stroke"),
                    stroke_soft=m.hex("stroke-soft"), well=m.hex("well"),
                    accent=m.hex("text-accent"), body=px("fs-body"), caption=px("fs-caption"),
                    section=px("fs-section"), page=px("fs-page"),
                    gap=(px("s1"), px("s2"), px("s3"), px("s4"), px("s6")), row=px("row-h"),
                    mono=mono_stack())

    def _render(self) -> None:
        """Show the guide at the zoom and text size in use; hits and the section are kept."""
        m = theme.manager()
        k = (self.zoom.zoom() if self.zoom is not None else 100) / 100
        look = self._look()
        font = m.font("body")
        font.setPixelSize(look.body)
        widest = round(TEXT_WIDTH * k * m.size("fs-body") / 15)
        keep = self.text.current()
        self.text.show_guide(self.guide, look, (look.gap[4], round(m.size("s8") * k), widest),
                             font, self._show_note)
        if self._query:
            self._hits = self.text.search(self._query)
            self.text.set_hits(self._hits, keep if keep >= 0 else 0 if self._hits else -1)
        self._counts()
        self._sync_status()

    def _restyle(self) -> None:
        m = theme.manager()
        scale = m.size("fs-body") / 15
        self.side.setMinimumWidth(min(side_width(), 320))
        if scale != self._scale:
            first = self._scale == 0.0
            self._scale = scale
            width = side_width()
            self.splitter.setHandleWidth(m.size("s3"))
            if first or self._prefs() is None:
                self.splitter.setSizes([max(400, self.width() - width), width])
        self.toc._restyle()
        for button in (self.previous_button, self.next_button):
            button.setIcon(make_icon(button.property("lucide")))
        self.count.setFixedWidth(round(72 * scale) if scale < 1.4 else 96)
        key_w = round(76 * scale) if scale < 1.4 else 120
        for label in self._key_column:
            label.setFixedWidth(key_w)
        self.text.apply_margins()
        self._render()

    # -- search ------------------------------------------------------------------------------
    def _search_changed(self, text: str) -> None:
        self._query = text.strip()
        if not self._query:
            self._hits = []
            self.text.set_hits([])
            self.stack.setCurrentWidget(self.text)
            self._counts()
            self._pin = None
            self._sync_status()
            self._announce.start()
            return
        self._hits = self.text.search(self._query)
        if self._hits:
            self.stack.setCurrentWidget(self.text)
            self._goto(self._first_in_view())
        else:
            self.empty.set_query(self._query)
            self.stack.setCurrentWidget(self.empty)
            self.text.set_hits([])
        self._counts()
        self._sync_status()
        self._announce.start()

    def _first_in_view(self) -> int:
        """The first hit at or below the top of the view, else the first (wrapping)."""
        top = self.text.cursorForPosition(self.text.viewport().rect().topLeft()).position()
        return next((i for i, (start, _n) in enumerate(self._hits) if start >= top), 0)

    def _goto(self, index: int) -> None:
        self._internal = True
        try:
            self.text.set_current(index)
        finally:
            self._internal = False
        if self._hits:
            self._pin = self.text.section_of(self._hits[self.text.current()][0])

    def step(self, direction: int) -> None:
        """F3 / Shift+F3 / Enter: the next or previous hit, wrapping round."""
        if not self._hits:
            self._announce_text("Sonuç yok")
            return
        at = self.text.current()
        self._goto((at + direction) % len(self._hits) if at >= 0 else 0)
        self._counts()
        self._sync_status()
        self._announce.start()

    def clear_search(self) -> None:
        """Esc / the x button / "Aramayı temizle": empty the field and give the guide back."""
        if self.search.text():
            self.search.clear()
        self.search.setFocus()

    def focus_search(self) -> None:
        """Ctrl+F: show the side panel if F9 hid it, then select the field's text."""
        if self.side.isHidden() and self.window_ is not None:
            self.window_.toggle_inspector()
        self.search.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self.search.selectAll()

    def show_keys(self) -> None:
        """"Kısayolları göster": back to the guide and down to the shortcut list."""
        self.clear_search()
        self.go_to_section(len(self.guide.sections) - 1)

    def _counts(self) -> None:
        per = [0] * len(self.guide.sections)
        for start, _n in self._hits:
            per[self.text.section_of(start)] += 1
        self.toc.set_counts(per if self._query else [])
        total = len(self._hits)
        if self._query:
            at = self.text.current() + 1
            self.previous_button.setEnabled(total > 0)
            self.next_button.setEnabled(total > 0)
            self.result.setText(
                f"<b style='color:{theme.manager().hex('text')}'>{total}</b> sonuç"
                + (f", {at} / {total}" if total else ""))
        else:
            sections = len(self.guide.sections)
            self.previous_button.setEnabled(False)
            self.next_button.setEnabled(False)
            self.result.setText(f"{sections} bölüm, {self.guide.minutes()} dakikalık okuma")
        self.result.setAccessibleName(self._result_text())
        self._sync_hit_actions()

    def _sync_hit_actions(self) -> None:
        """F3 / Shift+F3 (and the bar's arrows) only while there are hits to step through."""
        window = self.window_
        if window is None:
            return
        on = bool(self._query and self._hits)
        for action_id in ("app.sonraki_sonuc", "app.onceki_sonuc"):
            window.registry.set_enabled_for(action_id, "rehber", on)

    def _result_text(self) -> str:
        total = len(self._hits)
        if not self._query:
            return f"{len(self.guide.sections)} bölüm, {self.guide.minutes()} dakikalık okuma"
        if not total:
            return f"{self._query} için sonuç yok"
        return f"{total} sonuç, {self.text.current() + 1} / {total}"

    def _announce_text(self, text: str) -> None:
        announce(self.result, text)

    # -- sections ----------------------------------------------------------------------------
    def go_to_section(self, row: int) -> None:
        """Scroll so section `row` starts at the top; the list and the status bar follow."""
        if not 0 <= row < len(self.guide.sections):
            return
        self._pin = row
        self._internal = True
        try:
            self.text.scroll_to_section(row, theme.manager().size("s4"))
        finally:
            self._internal = False
        self._sync_status()

    def _scrolled(self, _value: int) -> None:
        if not self._internal:
            self._pin = None
            self._sync_status()

    def _sync_status(self) -> None:
        """The contents list marks the section being read; the status bar says which and how
        many hits there are."""
        total = len(self.guide.sections)
        empty = self._query != "" and not self._hits
        if not empty:
            row = self._pin if self._pin is not None else self.text.section_at_scroll(
                theme.manager().size("s4"))
            self._section = min(row, total - 1)
        self.toc.mark(None if empty else self._section)
        self._status_section.set_parts("Bölüm ", str(self._section + 1), f" / {total}")
        if self._query:
            self._status_hits.set_parts(str(len(self._hits)), f" sonuç: {self._query}")
            self._status_hits.show()
        else:
            self._status_hits.hide()

    def section(self) -> int:
        return self._section

    # -- events ------------------------------------------------------------------------------
    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        if (event.type() == QEvent.Type.KeyPress and isinstance(event, QKeyEvent)
                and event.key() == Qt.Key.Key_Escape and self._query
                and obj in (self.text, self.toc)):
            self.clear_search()
            return True
        return False

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._try_attach()
        self._sync_status()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        QTimer.singleShot(0, self._sync_status)

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(900, 600)

    def _link(self, url: QUrl) -> None:
        if url.scheme() == "rehber":
            if url.path() == "gizle":
                self.dismiss_note()
            return
        QDesktopServices.openUrl(url)

    def dismiss_note(self) -> None:
        """"Bir daha gösterme": the tip leaves the page now and on later starts."""
        self._show_note = False
        prefs = self._prefs()
        if prefs is not None:
            prefs.set_flag(NOTE_KEY, True)
        self._render()

    # -- the separator sheets ----------------------------------------------------------------
    def write_separators(self, path: Path, sheets: int) -> Path:
        return make_separator_pdf(Path(path), sheets=sheets)

    def open_separators(self) -> Path | None:
        """"PDF olarak aç": the sheets as a PDF in the viewer, for printing from there. When
        the usual file is held open (a PDF viewer still shows it, common on Windows), the
        sheets go to a new numbered file; when nothing can be written, a toast says why."""
        folder = data_dir()
        sheets = self.count.value()
        names = ["ayirac-sayfalari.pdf"] + [f"ayirac-sayfalari-{n}.pdf" for n in range(2, 21)]
        error: Exception | None = None
        for name in names:
            try:
                path = self.write_separators(folder / name, sheets)
            except (OSError, ValueError) as failure:
                error = failure
                if isinstance(failure, ValueError):
                    break
                continue
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
            return path
        reason = getattr(error, "strerror", None) or str(error)
        self._tell(f"Ayıraç sayfaları PDF olarak yazılamadı: {reason}. Açık bir PDF "
                   "görüntüleyiciyi kapatıp yeniden deneyin.", "Yeniden dene",
                   self.open_separators, kind="error")
        return None

    def print_separators(self, printer: QPrinter | None = None) -> int | None:
        """Ctrl+P: ask for a printer, then print the sheets. Returns the pages sent, or None
        when the person cancelled or printing failed (then the toast offers the PDF)."""
        if not self._active():
            return None
        if not isinstance(printer, QPrinter):
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            dialog = self._print_dialog(printer, self)
            dialog.setWindowTitle("Ayıraç sayfasını yazdır")
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return None
        sheets = self.count.value()
        printer.setDocName("Ayıraç sayfaları")
        try:
            pages = printing.print_separators(printer, sheets)
        except (RuntimeError, ValueError, OSError) as error:
            self._tell(f"Ayıraç sayfaları yazdırılamadı: {error}. PDF olarak açıp oradan "
                       "yazdırabilirsiniz.", "PDF olarak aç", self.open_separators)
            return None
        self._tell(f"{sheets} ayıraç sayfası ({pages} sayfa) yazıcıya gönderildi.", kind="success")
        return pages

    def _tell(self, text: str, action: str | None = None, slot=None, kind: str = "info") -> None:
        toaster = self._toaster()
        if toaster is not None:
            toaster.show(text, action, slot, kind)

