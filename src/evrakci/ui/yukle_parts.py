"""Pieces of the Yükle tab that are not the table or the inspector: the reading progress card,
the window-wide drop overlay, the empty page (no job open: "Henüz iş yok", job search and the
recent jobs) and one status-bar count. Final-a/yukle.html states `running`, `drop`, `empty`.
"""

from __future__ import annotations

import html
import os
import re
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QPoint, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QKeyEvent, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from evrakci.ui import actions, icons, theme
from evrakci.ui.chrome import ElidedLabel, make_icon

PDF_LIMIT = 5000  # a dropped folder tree is read this far; more is almost certainly a mistake
SHOWN_FILES = 5  # file rows in the drop overlay


# -- plain helpers ----------------------------------------------------------------------
def ago(seconds: float) -> str:
    """Turkish relative time: "az önce", "dün", "3 gün önce", "2 hafta önce"."""
    minutes = int(seconds // 60)
    for size, word in ((525600, "yıl"), (43200, "ay"), (10080, "hafta"), (1440, "gün"),
                       (60, "saat"), (1, "dakika")):
        if minutes >= size:
            count = minutes // size
            return "dün" if word == "gün" and count == 1 else f"{count} {word} önce"
    return "az önce"


def human_size(size: int) -> str:
    """"18,4 MB" (Turkish decimal comma); below 1 MB in KB."""
    if size >= 1_000_000:
        return f"{size / 1_000_000:.1f} MB".replace(".", ",")
    return f"{max(1, round(size / 1000))} KB"


def rate_text(pages_per_second: float) -> str:
    return f"{pages_per_second:.1f}".replace(".", ",") + " sayfa/sn"


def eta_text(seconds: float | None) -> str:
    if seconds is None:
        return "Süre hesaplanıyor…"
    if seconds < 90:
        return f"Yaklaşık {max(1, round(seconds))} sn kaldı"
    return f"Yaklaşık {round(seconds / 60)} dk kaldı"


def _natural(path: Path) -> list:
    return [int(p) if p.isdigit() else p.casefold() for p in re.split(r"(\d+)", str(path))]


def collect_pdfs(paths: list[Path], limit: int = PDF_LIMIT) -> list[Path]:
    """The PDFs among dropped or chosen paths: files as they are, folders searched through
    (every other file is skipped). In natural order, so tarama-2 comes before tarama-10."""
    found: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        if path.is_dir():
            candidates = sorted((p for p in path.rglob("*") if p.suffix.lower() == ".pdf"
                                 and p.is_file()), key=_natural)
        elif path.suffix.lower() == ".pdf" and path.is_file():
            candidates = [path]
        else:
            continue
        for candidate in candidates:
            if candidate not in seen:
                seen.add(candidate)
                found.append(candidate)
            if len(found) >= limit:
                return found
    return found


# -- status bar -------------------------------------------------------------------------
class StatusPart(QWidget):
    """One status-bar count: an optional icon and rich text, numbers in text colour (A)."""

    def __init__(self, icon: str | None = None, role: str = "icon",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        self.icon_name, self.role = icon, role
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self.icon = QLabel()
        self.icon.setFixedSize(14, 14)
        self.label = QLabel()
        self.label.setTextFormat(Qt.TextFormat.RichText)
        if icon:
            row.addWidget(self.icon)
        else:
            self.icon.hide()
        row.addWidget(self.label)
        self.parts: tuple[str, ...] = ()

    def set(self, *parts: str) -> None:
        """Alternating plain and strong parts: set("Okunuyor: ", "77", " / 124")."""
        self.parts = parts
        m = theme.manager()
        if self.icon_name:
            self.icon.setPixmap(icons.pixmap(self.icon_name, m.hex(self.role), 14))
        text = "".join(
            f"<span style='color:{m.hex('text')}; font-weight:600'>{html.escape(p)}</span>"
            if i % 2 else html.escape(p) for i, p in enumerate(parts))
        self.label.setText(text)
        plain = "".join(parts)
        self.setAccessibleName(plain)
        self.label.setAccessibleName(plain)


# -- reading progress -------------------------------------------------------------------
class ProgressCard(QFrame):
    """A .progress card: what is read, the bar, and "%62, Yaklaşık 40 sn kaldı, 3,2 sayfa/sn,
    İptal ederseniz hiçbir şey değişmez." A live region for screen readers."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("kind", "card")
        self.setAccessibleName("Okuma ilerlemesi")
        m = theme.manager()
        column = QVBoxLayout(self)
        column.setContentsMargins(m.size("s4"), m.size("s4"), m.size("s4"), m.size("s4"))
        column.setSpacing(m.size("s2"))
        top = QHBoxLayout()
        top.setSpacing(m.size("s3"))
        self.icon = QLabel()
        self.icon.setFixedSize(m.size("icon-md"), m.size("icon-md"))
        self.title = QLabel("")
        self.title.setFont(m.font("body-strong"))
        self.name = ElidedLabel("", min_chars=12)
        self.name.setProperty("textRole", "secondary")
        top.addWidget(self.icon)
        top.addWidget(self.title)
        top.addWidget(self.name, 1)
        column.addLayout(top)
        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        self.bar.setAccessibleName("Okuma ilerlemesi")
        column.addWidget(self.bar)
        sub = QHBoxLayout()
        sub.setSpacing(m.size("s4"))
        self.percent, self.eta, self.rate, self.note = (QLabel() for _ in range(4))
        for label in (self.percent, self.eta, self.rate, self.note):
            label.setProperty("textRole", "secondary")
            sub.addWidget(label)
        sub.addStretch(1)
        self.note.setText("İptal ederseniz hiçbir şey değişmez.")
        column.addLayout(sub)
        theme.bind_style(self, lambda: (
            f"QProgressBar {{ min-height: 6px; max-height: 6px; "
            f"background: {theme.manager().hex('track')}; }}"))
        theme.follow(self, self._restyle, "yukle-progress")

    def _restyle(self) -> None:
        m = theme.manager()
        self.icon.setPixmap(icons.pixmap("scan-text", m.hex("icon"), m.size("icon-md")))
        size = f"font-size: {m.size('fs-caption')}px;"
        for label in (self.percent, self.eta, self.rate, self.note, self.name):
            label.setStyleSheet(size)
        self.percent.setFont(m.font("caption-num"))

    def show_progress(self, done: int, total: int, name: str, eta: float | None,
                      rate: float | None) -> None:
        total = max(total, 1)
        self.bar.setRange(0, total)
        self.bar.setValue(min(done, total))
        self.title.setText(f"Sayfalar okunuyor: {done} / {total}")
        self.name.setText(name)
        percent = round(100 * done / total)
        self.percent.setText(f"%{percent}")
        self.eta.setText(eta_text(eta))
        self.rate.setText(rate_text(rate) if rate else "")
        self.rate.setVisible(bool(rate))
        self.setAccessibleDescription(f"%{percent}, {self.eta.text()}")

    def show_waiting(self, text: str, name: str) -> None:
        """Before the first page is read: an indeterminate bar."""
        self.bar.setRange(0, 0)
        self.title.setText(text)
        self.name.setText(name)
        self.percent.setText("")
        self.eta.setText("")
        self.rate.hide()


# -- the window-wide drop ---------------------------------------------------------------
class DropOverlay(QWidget):
    """The `drop` state: the layer below the command bar, a dashed accent edge and a card that
    says what the drop does. Mouse-transparent: the drop itself is handled by the window."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAccessibleName("PDF'leri bırakın")
        m = theme.manager()
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card = QFrame()
        self.card.setProperty("kind", "card")
        self.card.setFixedWidth(560)
        column = QVBoxLayout(self.card)
        column.setContentsMargins(m.size("s6"), m.size("s6"), m.size("s6"), m.size("s6"))
        column.setSpacing(m.size("s3"))
        head = QHBoxLayout()
        head.setSpacing(m.size("s3"))
        self.mark = QLabel()
        self.mark.setFixedSize(28, 28)
        self.heading = QLabel("PDF'leri bırakın")
        self.heading.setProperty("textRole", "panel")
        head.addWidget(self.mark)
        head.addWidget(self.heading, 1)
        column.addLayout(head)
        self.summary = QLabel()
        self.summary.setTextFormat(Qt.TextFormat.RichText)
        self.summary.setWordWrap(True)
        column.addWidget(self.summary)
        self.files = QVBoxLayout()
        self.files.setSpacing(0)
        column.addLayout(self.files)
        note = QHBoxLayout()
        note.setSpacing(m.size("s2"))
        self.note_icon = QLabel()
        self.note_icon.setFixedSize(16, 16)
        self.note = QLabel("Klasörlerdeki PDF'ler de eklenir, diğer dosyalar atlanır. "
                           "Vazgeçmek için Esc.")
        self.note.setProperty("textRole", "secondary")
        self.note.setWordWrap(True)
        note.addWidget(self.note_icon, 0, Qt.AlignmentFlag.AlignTop)
        note.addWidget(self.note, 1)
        column.addLayout(note)
        outer.addWidget(self.card)
        self.hide()
        theme.follow(self, self._restyle, "yukle-drop")

    def _restyle(self) -> None:
        m = theme.manager()
        self.mark.setPixmap(icons.pixmap("upload", m.hex("accent"), 28))
        self.note_icon.setPixmap(icons.pixmap("info", m.hex("icon"), 16))
        self.note.setStyleSheet(f"font-size: {m.size('fs-caption')}px;")
        self.update()

    def place(self) -> None:
        """Cover the layer under its command bar (A .dropzone: inset commandbar-h s1 s1 s1)."""
        parent = self.parentWidget()
        if parent is None:
            return
        m = theme.manager()
        top = m.size("commandbar-h")
        s1 = m.size("s1")
        self.setGeometry(s1, top, max(0, parent.width() - 2 * s1),
                         max(0, parent.height() - top - s1))
        self.raise_()

    def show_drop(self, paths: list[Path], job_name: str | None) -> list[Path]:
        """Describe what dropping `paths` would do; returns the PDFs found."""
        pdfs = collect_pdfs(paths, limit=200)
        count = len(pdfs)
        if not count:
            self.summary.setText("Burada PDF yok. Yalnızca PDF dosyaları ve klasörleri eklenir.")
        elif job_name:
            self.summary.setText(f"{count} parti, <b>{html.escape(job_name)}</b> işinin "
                                 "sonuna eklenir.")
        else:
            self.summary.setText(f"{count} partiyle yeni bir iş oluşturulur.")
        while self.files.count():
            item = self.files.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        for path in pdfs[:SHOWN_FILES]:
            try:
                size = human_size(path.stat().st_size)
            except OSError:
                size = ""
            self.files.addWidget(_FileRow(path.name, size))
        if count > SHOWN_FILES:
            more = QLabel(f"ve {count - SHOWN_FILES} dosya daha")
            more.setProperty("textRole", "secondary")
            self.files.addWidget(more)
        self.setAccessibleDescription(self.summary.text())
        self.place()
        self.show()
        self.raise_()
        return pdfs

    def paintEvent(self, _event) -> None:  # noqa: N802
        m = theme.manager()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        fill = QColor(m.color("layer"))
        fill.setAlphaF(1.0 if m.theme() == "hc" else 0.82)
        painter.setBrush(fill)
        pen = QPen(m.color("accent"), 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        radius = m.size("r-layer")
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), radius, radius)


class _FileRow(QWidget):
    """A .dropcard .file: file icon, name, size at the right (32 px)."""

    def __init__(self, name: str, size: str) -> None:
        super().__init__()
        m = theme.manager()
        self.setMinimumHeight(32)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(m.size("s2"))
        icon = QLabel()
        icon.setFixedSize(16, 16)
        icon.setPixmap(icons.pixmap("file-text", m.hex("icon"), 16))
        label = ElidedLabel(name, min_chars=16)
        weight = QLabel(size)
        weight.setProperty("textRole", "secondary")
        weight.setStyleSheet(f"font-size: {m.size('fs-caption')}px;")
        row.addWidget(icon)
        row.addWidget(label, 1)
        row.addWidget(weight)
        self.setAccessibleName(f"{name}, {size}" if size else name)


# -- the empty page ---------------------------------------------------------------------
@dataclass(frozen=True)
class JobEntry:
    id: str
    name: str
    pages: int
    age: str  # "dün", "3 gün önce"

    @property
    def detail(self) -> str:
        return f"{self.pages} sayfa, {self.age}"


class _JobRow(QPushButton):
    """A .recent .act .r: folder icon, job name, "640 sayfa, dün" at the right."""

    def __init__(self, entry: JobEntry) -> None:
        super().__init__()
        m = theme.manager()
        self.entry = entry
        self.setProperty("kind", "inspector-row")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumHeight(m.size("row-h"))
        self.setAccessibleName(f"{entry.name} işini aç, {entry.detail}")
        self.setToolTip(f"{entry.name} işini aç")
        row = QHBoxLayout(self)
        row.setContentsMargins(m.size("s3"), 0, m.size("s3"), 0)
        row.setSpacing(m.size("s3"))
        self.icon = QLabel()
        self.icon.setFixedSize(16, 16)
        self.name = ElidedLabel(entry.name, min_chars=12)
        self.detail = QLabel(entry.detail)
        self.detail.setProperty("textRole", "secondary")
        for widget in (self.icon, self.name, self.detail):
            widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        row.addWidget(self.icon)
        row.addWidget(self.name, 1)
        row.addWidget(self.detail)
        self.refresh()

    def refresh(self) -> None:
        m = theme.manager()
        self.icon.setPixmap(icons.pixmap("folder", m.hex("icon"), 16))
        self.detail.setStyleSheet(f"font-size: {m.size('fs-caption')}px;")

    def sizeHint(self) -> QSize:  # noqa: N802
        hint = self.layout().sizeHint()
        return QSize(hint.width(), max(hint.height(), theme.manager().size("row-h")))

    def contextMenuEvent(self, event) -> None:  # noqa: N802
        """Right-click (or the menu key) on a job: İşi aç, Klasörünü göster."""
        page = self.parent()
        while page is not None and not isinstance(page, EmptyPage):
            page = page.parent()
        if page is not None:
            page.job_menu(self.entry, event.globalPos())
            event.accept()


class _Search(QLineEdit):
    """"İş adı ara": Esc clears, Down moves to the first job, Enter opens the first match."""

    down = Signal()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape and self.text():
            self.clear()
            event.accept()
        elif event.key() == Qt.Key.Key_Down:
            self.down.emit()
            event.accept()
        else:
            super().keyPressEvent(event)


class EmptyPage(QWidget):
    """The page when no job is open (and, with `set_mode("all")`, the list of every job):
    mark, "Henüz iş yok", one sentence, "Yeni iş oluştur" (Ctrl+N) and "Dosya ekle…", then the
    job search and "Son işler". Searching with no match says so and offers to clear."""

    new_job = Signal()
    add_files = Signal()
    open_job = Signal(str)
    show_job_folder = Signal(str)
    BASE_WIDTH = 440  # A .recent width
    RECENT = 3
    ALL = 8

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("page")
        self.setAccessibleName("Henüz iş yok")
        self.entries: list[JobEntry] = []
        self._mode = "empty"
        m = theme.manager()
        outer = QVBoxLayout(self)
        outer.addStretch(1)
        column = QVBoxLayout()
        column.setSpacing(0)
        column.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.mark = QLabel()
        self.mark.setFixedSize(48, 48)
        self.mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mark.setProperty("kind", "card")
        self.title = QLabel("Henüz iş yok")
        self.title.setProperty("textRole", "panel")
        self.text = QLabel("Taradığınız PDF'leri bırakın ya da yeni bir iş oluşturun.")
        self.text.setProperty("textRole", "secondary")
        self.text.setContentsMargins(0, m.size("s1"), 0, 0)
        column.addWidget(self.mark, 0, Qt.AlignmentFlag.AlignHCenter)
        column.addSpacing(m.size("s4"))
        column.addWidget(self.title, 0, Qt.AlignmentFlag.AlignHCenter)
        column.addWidget(self.text, 0, Qt.AlignmentFlag.AlignHCenter)
        column.addSpacing(m.size("s6"))
        buttons = QHBoxLayout()
        buttons.setSpacing(m.size("s2"))
        buttons.addStretch(1)
        key = actions.key_text("Ctrl+N")
        self.new_button = QPushButton()
        self.new_button.setProperty("variant", "primary")
        self.new_button.setProperty("sizeVariant", "lg")
        inside = QHBoxLayout(self.new_button)  # A: icon, "Yeni iş oluştur", the key in caption
        inside.setContentsMargins(m.size("s4"), 0, m.size("s4"), 0)
        inside.setSpacing(m.size("s2"))
        self.new_icon, self.new_key = QLabel(), QLabel(key)
        self.new_text = QLabel("Yeni iş oluştur")
        for label in (self.new_icon, self.new_text, self.new_key):
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            inside.addWidget(label)
        self.new_icon.setFixedSize(16, 16)
        self.new_button.setAccessibleName(f"Yeni iş oluştur ({key})")
        self.new_button.setToolTip(f"Yeni iş oluştur ({key})")
        self.new_button.clicked.connect(self.new_job)
        self.add_button = QPushButton(" Dosya ekle…")
        self.add_button.setProperty("sizeVariant", "lg")
        self.add_button.setAccessibleName("Dosya ekle")
        self.add_button.setToolTip(f"Dosya ekle ({actions.key_text('Ctrl+O')})")
        self.add_button.clicked.connect(self.add_files)
        buttons.addWidget(self.new_button)
        buttons.addWidget(self.add_button)
        buttons.addStretch(1)
        column.addLayout(buttons)
        self.recent_box = QWidget()
        self.recent_box.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        recent = QVBoxLayout(self.recent_box)
        recent.setContentsMargins(0, m.size("s8"), 0, 0)
        recent.setSpacing(0)
        self.search = _Search()
        self.search.setPlaceholderText("İş adı ara")
        self.search.setAccessibleName("İş adı ara")
        self.search.setClearButtonEnabled(True)
        self.search.addAction(make_icon("search"), QLineEdit.ActionPosition.LeadingPosition)
        self.search.textChanged.connect(self.rebuild)
        self.search.returnPressed.connect(self._open_first)
        self.search.down.connect(self._focus_first)
        recent.addWidget(self.search)
        recent.addSpacing(m.size("s4"))
        self.group = QLabel("Son işler")
        self.group.setProperty("kind", "group-label")
        recent.addWidget(self.group)
        self.card = QFrame()
        self.card.setProperty("kind", "card")
        self.rows = QVBoxLayout(self.card)
        pad = m.size("s1")
        self.rows.setContentsMargins(pad, pad, pad, pad)
        self.rows.setSpacing(0)
        recent.addWidget(self.card)
        self.none = QWidget()  # filtered-zero: what happened and the way out
        none_col = QVBoxLayout(self.none)
        none_col.setContentsMargins(0, m.size("s3"), 0, 0)
        self.none_text = QLabel()
        self.none_text.setProperty("textRole", "secondary")
        self.none_text.setWordWrap(True)
        self.clear_button = QPushButton("Aramayı temizle")
        self.clear_button.setProperty("variant", "link")
        self.clear_button.clicked.connect(self.search.clear)
        none_col.addWidget(self.none_text)
        none_col.addWidget(self.clear_button, 0, Qt.AlignmentFlag.AlignLeft)
        recent.addWidget(self.none)
        self.more = QLabel()
        self.more.setProperty("textRole", "secondary")
        self.more.setContentsMargins(m.size("s1"), m.size("s2"), 0, 0)
        recent.addWidget(self.more)
        column.addWidget(self.recent_box, 0, Qt.AlignmentFlag.AlignHCenter)
        outer.addLayout(column)
        outer.addStretch(1)
        theme.follow(self, self.refresh, "yukle-empty")

    # -- content -------------------------------------------------------------------------
    def set_mode(self, mode: str) -> None:
        """"empty" (no job open) or "all" (every job, for "Tüm işler…")."""
        self._mode = mode
        everything = mode == "all"
        self.title.setText("Tüm işler" if everything else "Henüz iş yok")
        self.text.setText("Açmak için bir iş seçin ya da adını yazın." if everything
                          else "Taradığınız PDF'leri bırakın ya da yeni bir iş oluşturun.")
        self.group.setText("İşler" if everything else "Son işler")
        self.setAccessibleName(self.title.text())
        self.rebuild()

    def job_menu(self, entry: JobEntry, where: QPoint) -> QMenu:
        """A job row's context menu: open it, or show its folder in the file manager."""
        menu = QMenu(self)
        menu.setAccessibleName(entry.name)
        menu.addAction(make_icon("folder-open"), "İşi &aç",
                       lambda: self.open_job.emit(entry.id))
        menu.addAction(make_icon("external-link"), "Klasörünü Dosya &Gezgini'nde göster",
                       lambda: self.show_job_folder.emit(entry.id))
        menu.popup(where)
        self.menu = menu
        return menu

    def set_jobs(self, entries: list[JobEntry]) -> None:
        self.entries = list(entries)
        self.rebuild()

    def rebuild(self, *_args) -> None:
        query = self.search.text().strip().casefold()
        limit = self.ALL if self._mode == "all" else self.RECENT
        matches = [e for e in self.entries if query in e.name.casefold()]
        shown = matches if query else matches[:limit]
        if query:
            shown = matches[:self.ALL]
        while self.rows.count():
            item = self.rows.takeAt(0)
            if item.widget() is not None:
                item.widget().hide()
                item.widget().deleteLater()
        for entry in shown:
            row = _JobRow(entry)
            row.clicked.connect(lambda _c=False, job=entry.id: self.open_job.emit(job))
            self.rows.addWidget(row)
        has_any = bool(self.entries)
        self.recent_box.setVisible(has_any)
        self.card.setVisible(bool(shown))
        self.group.setVisible(bool(shown))
        self.none.setVisible(has_any and not shown)
        if has_any and not shown:
            self.none_text.setText(f"“{self.search.text().strip()}” ile eşleşen iş yok.")
        left = len(matches) - len(shown)
        self.more.setVisible(left > 0)
        self.more.setText(f"{left} iş daha var; aramak için adını yazın." if not query
                          else f"{left} iş daha var; aramayı daraltın.")
        self.search.setVisible(has_any)

    def _rows(self) -> list[_JobRow]:
        return [self.rows.itemAt(i).widget() for i in range(self.rows.count())
                if isinstance(self.rows.itemAt(i).widget(), _JobRow)]

    def _open_first(self) -> None:
        rows = self._rows()
        if rows:
            rows[0].click()

    def _focus_first(self) -> None:
        rows = self._rows()
        if rows:
            rows[0].setFocus(Qt.FocusReason.TabFocusReason)

    def refresh(self) -> None:
        m = theme.manager()
        self.mark.setPixmap(icons.pixmap("upload", m.hex("icon"), 24))
        on = m.hex("text-on-accent")
        self.new_icon.setPixmap(icons.pixmap("file-plus", on, 16))
        self.new_text.setStyleSheet(f"color: {on}; font-weight: 600;")
        self.new_key.setStyleSheet(f"color: {on}; font-size: {m.size('fs-caption')}px;")
        self.new_button.setMinimumWidth(self.new_button.layout().sizeHint().width())
        self.add_button.setIcon(make_icon("file-up"))
        self.recent_box.setFixedWidth(round(self.BASE_WIDTH * m.text_scale() / 100))
        for row in self._rows():
            row.refresh()

    def showEvent(self, event) -> None:  # noqa: N802
        self.refresh()
        super().showEvent(event)


def default_folder(prefs) -> str:
    """Where a file dialog starts: the last folder a PDF was added from, else the documents."""
    if prefs is not None:
        recent = prefs.recent_folders()
        if recent and os.path.isdir(recent[0]):
            return recent[0]
    return str(Path.home())

