"""I-38: the printed file list, its page painter and the "Baskı önizleme" dialog.

`index_html` is plain text built from plain tuples, so `run_background` can make it in a worker
(thread rule 1, see `workers`). The `QTextDocument` and the dialog are made on the window thread.
`paint_document` is the one painter for the preview and the printer: every page is drawn from the
document with a footer line "<iş> · <tarih> · Sayfa n / m". `<thead>` makes Qt repeat the header
row on every page.
"""

from __future__ import annotations

from datetime import datetime
from html import escape

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QFont, QKeySequence, QPainter, QShortcut, QTextDocument
from PySide6.QtPrintSupport import QPrinter, QPrintPreviewWidget
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from evrakci.pipeline.index import format_time
from evrakci.ui import actions, theme
from evrakci.ui.chrome import make_icon

COLUMNS = ("Durum", "No", "Dosya adı", "Sayfalar", "Şablon", "Not")
PLAN_SUBTITLE = "Dışa aktarma planı, henüz yazılmadı"
TITLE = "Baskı önizleme"
FOOTER_MM = 10  # height reserved for the footer line


def subtitle(last_export, current_state: str | None = None) -> str:
    """"Dışa aktarıldı: 20.11.2026 14:32" after a written export, else the plan line. The plan
    line also shows when the job changed after that export (`current_state` is the job's
    `job_state()`; an export from before the state was kept always counts as unchanged)."""
    changed = bool(last_export is not None and last_export.state and current_state is not None
                   and current_state != last_export.state)
    if last_export is not None and not changed:
        try:
            return f"Dışa aktarıldı: {format_time(datetime.fromisoformat(last_export.at))}"
        except ValueError:
            pass
    return PLAN_SUBTITLE


def index_html(name: str, rows, documents: int, pages: int, sub: str) -> str:
    """The list as a printable table. `rows`: (durum, no, dosya adı, sayfalar, şablon, not)."""
    head = "".join(f"<th align='left'>{escape(t)}</th>" for t in COLUMNS)
    body = "".join(
        f"<tr><td>{escape(state)}</td><td align='right'>{number}</td><td>{escape(file)}</td>"
        f"<td align='right'>{escape(count)}</td><td>{escape(template)}</td>"
        f"<td>{escape(why)}</td></tr>" for state, number, file, count, template, why in rows)
    return (f"<table width='100%'><tr><td><h2>{escape(name)}</h2></td>"
            f"<td align='right'>{escape(sub)}</td></tr></table>"
            f"<p>{documents} belge, {pages} sayfa</p>"
            f"<table border='1' cellspacing='0' cellpadding='4' width='100%'>"
            f"<thead><tr>{head}</tr></thead>{body}</table>")


def page_text(n: int, m: int) -> str:
    return f"Sayfa {n} / {m}"


def paint_document(printer, document: QTextDocument, job_name: str, stamp: str) -> int:
    """Draw every page of `document` on `printer` with the footer; returns the page count.
    Called from `paintRequested` (preview) and for the real printer."""
    layout = document.documentLayout()
    layout.setPaintDevice(printer)
    page = printer.pageRect(QPrinter.Unit.DevicePixel)
    footer = printer.logicalDpiY() * FOOTER_MM / 25.4
    body = QRectF(0, 0, page.width(), page.height() - footer)
    document.setPageSize(body.size())
    count = max(1, document.pageCount())
    painter = QPainter(printer)
    try:
        font = QFont(document.defaultFont())
        font.setPointSizeF(8)
        for index in range(count):
            if index:
                printer.newPage()
            painter.save()
            painter.translate(0, -index * body.height())
            painter.setClipRect(QRectF(0, index * body.height(), body.width(), body.height()))
            document.drawContents(painter, QRectF(0, index * body.height(), body.width(),
                                                  body.height()))
            painter.restore()
            painter.setFont(font)
            painter.drawText(QRectF(0, body.height(), page.width(), footer),
                             int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                             f"{job_name} · {stamp} · {page_text(index + 1, count)}")
    finally:
        painter.end()
    return count


def make_document(html: str) -> QTextDocument:
    document = QTextDocument()
    document.setHtml(html)
    return document


def now_stamp() -> str:
    return format_time(datetime.now())


class PrintPreviewDialog(QDialog):
    """"Baskı önizleme": our own Turkish buttons around a QPrintPreviewWidget (QPrintPreviewDialog
    has English strings). Enter prints, Esc closes, PgDn / PgUp turn pages, Ctrl++ / Ctrl+- /
    Ctrl+0 zoom."""

    def __init__(self, html: str, job_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._name, self._stamp = job_name, now_stamp()
        self._document = make_document(html)
        self.printer_ = QPrinter(QPrinter.PrinterMode.HighResolution)
        self.setObjectName("printPreview")
        self.setWindowTitle(TITLE)
        self.setAccessibleName(TITLE)
        self.setModal(True)
        self.resize(1000, 700)
        m = theme.manager()
        root = QVBoxLayout(self)
        root.setContentsMargins(*(m.size("s4"),) * 4)
        root.setSpacing(m.size("s3"))
        bar = QHBoxLayout()
        bar.setSpacing(m.size("s2"))
        self.previous = self._tool("chevron-left", "Önceki sayfa", actions.key_text("PgUp"))
        self.page_label = QLabel(page_text(1, 1))
        self.page_label.setAccessibleName("Sayfa")
        self.next = self._tool("chevron-right", "Sonraki sayfa", actions.key_text("PgDown"))
        zoom_out, zoom_in = actions.spec("app.uzaklastir"), actions.spec("app.yakinlastir")
        self.zoom_out = self._tool("zoom-out", actions.plain_text(zoom_out.text),
                              actions.key_text(zoom_out.shortcuts[0]))
        self.zoom_label = QLabel("100 %")
        self.zoom_label.setAccessibleName("Yakınlık")
        self.zoom_in = self._tool("zoom-in", actions.plain_text(zoom_in.text),
                             actions.key_text(zoom_in.shortcuts[0]))
        self.fit = QPushButton("Sığdır")
        self.fit.setToolTip(f"Sayfaya sığdır ({actions.key_text('Ctrl+0')})")
        self.print_button = QPushButton("Yazdır…")
        self.print_button.setObjectName("primary")
        self.close_button = QPushButton("Kapat")
        for button in (self.fit, self.print_button, self.close_button):
            button.setAutoDefault(False)
        self.print_button.setDefault(True)
        for widget in (self.previous, self.page_label, self.next):
            bar.addWidget(widget)
        bar.addSpacing(m.size("s4"))
        for widget in (self.zoom_out, self.zoom_label, self.zoom_in, self.fit):
            bar.addWidget(widget)
        bar.addStretch(1)
        bar.addWidget(self.print_button)
        bar.addWidget(self.close_button)
        root.addLayout(bar)
        self.preview = QPrintPreviewWidget(self.printer_)
        self.preview.setAccessibleName(TITLE)
        root.addWidget(self.preview, 1)

        self.preview.paintRequested.connect(self.paint)
        self.preview.previewChanged.connect(self._sync)
        self.previous.clicked.connect(self.go_previous)
        self.next.clicked.connect(self.go_next)
        self.zoom_in.clicked.connect(self.zoom_bigger)
        self.zoom_out.clicked.connect(self.zoom_smaller)
        self.fit.clicked.connect(self.fit_page)
        self.print_button.clicked.connect(self.print_now)
        self.close_button.clicked.connect(self.reject)
        self._keys()
        self.preview.updatePreview()
        self.fit_page()
        self.print_button.setFocus()

    def _tool(self, icon: str, name: str, keys: str = "") -> QPushButton:
        button = QPushButton()
        button.setIcon(make_icon(icon, "icon"))
        button.setToolTip(f"{name} ({keys})" if keys else name)
        button.setAccessibleName(name)
        button.setAutoDefault(False)
        side = theme.manager().size("icon-btn")
        button.setFixedSize(side, side)
        return button

    def _keys(self) -> None:
        def bind(keys, slot) -> None:
            for key in keys:
                shortcut = QShortcut(QKeySequence(key), self)
                shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
                shortcut.activated.connect(slot)
        bind(("PgDown",), self.go_next)
        bind(("PgUp",), self.go_previous)
        bind(actions.spec("app.yakinlastir").shortcuts, self.zoom_bigger)
        bind(actions.spec("app.uzaklastir").shortcuts, self.zoom_smaller)
        bind(("Ctrl+0",), self.fit_page)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not event.isAutoRepeat():
            event.accept()
            focus = self.focusWidget()  # Enter presses the focused button, else it prints
            button = focus if isinstance(focus, QPushButton) else self.print_button
            button.click()
            return
        super().keyPressEvent(event)

    # -- pages and zoom -------------------------------------------------------------------
    def paint(self, printer) -> None:
        paint_document(printer, self._document, self._name, self._stamp)

    def page_count(self) -> int:
        return self.preview.pageCount()

    def current_page(self) -> int:
        return self.preview.currentPage()

    def go_next(self) -> None:
        self.preview.setCurrentPage(min(self.current_page() + 1, self.page_count()))
        self._sync()

    def go_previous(self) -> None:
        self.preview.setCurrentPage(max(self.current_page() - 1, 1))
        self._sync()

    def zoom_bigger(self) -> None:
        self.preview.zoomIn()
        self._sync()

    def zoom_smaller(self) -> None:
        self.preview.zoomOut()
        self._sync()

    def fit_page(self) -> None:
        self.preview.fitInView()
        self._sync()

    def _sync(self) -> None:
        count, page = max(1, self.page_count()), max(1, self.current_page())
        self.page_label.setText(page_text(page, count))
        self.zoom_label.setText(f"{round(self.preview.zoomFactor() * 100)} %")
        self.previous.setEnabled(page > 1)
        self.next.setEnabled(page < count)

    # -- print ------------------------------------------------------------------------------
    def print_now(self) -> bool:
        """Yazdır…: the system print dialog, then the pages. True when something was printed."""
        import PySide6.QtPrintSupport as qt_print  # looked up late: a test swaps QPrintDialog

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = qt_print.QPrintDialog(printer, self)
        dialog.setWindowTitle("Dizini yazdır")
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return False
        paint_document(printer, self._document, self._name, self._stamp)
        return True
