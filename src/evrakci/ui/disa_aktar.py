"""The Dışa Aktar screen: write the named PDFs and index.xlsx, never silently."""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from pathlib import Path

from PySide6.QtCore import QRectF, QSize, Qt, QUrl, Signal
from PySide6.QtGui import (
    QColor,
    QDesktopServices,
    QFont,
    QFontMetrics,
    QKeySequence,
    QPainter,
    QShortcut,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QProgressBar,
    QStyledItemDelegate,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from evrakci.pipeline.export import plan_export
from evrakci.pipeline.exporting import ExportError, export_job, may_delete_after_export
from evrakci.pipeline.job import job_from_dict, job_to_dict
from evrakci.pipeline.ocr.engine import EngineUnavailable
from evrakci.pipeline.settings import (
    DELETE_AFTER_EXPORT,
    KEEP,
    Settings,
    SettingsError,
    load_settings,
    save_settings,
)
from evrakci.pipeline.templates.model import Template
from evrakci.ui import icons, theme
from evrakci.ui.controller import JobController
from evrakci.ui.widgets import Heading, Rider, icon_label, key_button, label, paint_rider, rule
from evrakci.ui.workers import Task, start

RETENTION = [
    (KEEP, "Süresiz"),
    (DELETE_AFTER_EXPORT, "Tam dışa aktarınca sil"),
    ("30", "30 gün"),
    ("90", "90 gün"),
]

MONO = 'Consolas, "DejaVu Sans Mono", monospace'
STATE_ROLE = Qt.ItemDataRole.UserRole + 1  # Durum: "check", "ok", "info" or "none"
FLAG_ROLE = Qt.ItemDataRole.UserRole + 2  # the whole row needs a check (wash)
NOTE_ROLE = Qt.ItemDataRole.UserRole + 3  # a second line under the file name
FILE_ROLE = Qt.ItemDataRole.UserRole + 4  # a file name: mono
DIM_ROLE = Qt.ItemDataRole.UserRole + 5  # muted text ("Şablon yok")

STATE_LOOK = {  # state: (icon, token)
    "ok": ("ok", "ok"),
    "info": ("info", "qr"),
    "none": ("no", "ink_2"),
}
STAGES = {"write": "dosyalar yazılıyor", "layer": "metin katmanı ekleniyor"}


def _font(base: QFont, size: int, weight: QFont.Weight, mono: bool = False) -> QFont:
    font = QFont(base)
    if mono:
        font.setFamilies(["Consolas", "DejaVu Sans Mono", "monospace"])
        font.setStyleHint(QFont.StyleHint.Monospace)
    font.setPixelSize(size)
    font.setWeight(weight)
    return font


def _pages(job, document) -> str:
    positions = [job.position_of(pid) for pid in document.page_ids]
    return f"{positions[0]}–{positions[-1]}" if len(positions) > 1 else str(positions[0])


class _FileDelegate(QStyledItemDelegate):
    """Rows like the mockup: rules not grid, file names in mono, flagged rows on the check
    wash, and the Durum column as a rider (Kontrol) or icon + word."""

    def __init__(self, view: QTableWidget) -> None:
        super().__init__(view)
        self.view = view

    def sizeHint(self, option, index) -> QSize:
        height = 56 if index.siblingAtColumn(0).data(NOTE_ROLE) else 36
        text = index.data(Qt.ItemDataRole.DisplayRole) or ""
        mono = bool(index.data(FILE_ROLE))
        flagged = bool(index.data(FLAG_ROLE))
        size = 14 if mono else (theme.SMALL if index.data(STATE_ROLE) == "check" else 15)
        weight = QFont.Weight.Bold if (mono and flagged) or index.data(STATE_ROLE) else \
            QFont.Weight.Normal
        width = QFontMetrics(_font(option.font, size, weight, mono)).horizontalAdvance(text)
        if index.data(STATE_ROLE):
            width += 28
        return QSize(width + 20, height)

    def paint(self, painter: QPainter, option, index) -> None:
        t = theme.TOKENS
        rect = option.rect
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        flagged = bool(index.data(FLAG_ROLE))
        if flagged:
            painter.fillRect(rect, QColor(t["check_wash"]))
        elif self.view.currentIndex().row() == index.row():
            painter.fillRect(rect, QColor(t["row_cur"]))
        painter.fillRect(rect.left(), rect.bottom(), rect.width(), 1, QColor(t["rule"]))
        inner = QRectF(rect.adjusted(10, 0, -8, -1))
        text = index.data(Qt.ItemDataRole.DisplayRole) or ""
        state = index.data(STATE_ROLE)
        note = index.data(NOTE_ROLE)
        if state == "check":
            font = _font(option.font, theme.SMALL, QFont.Weight.Bold)
            room = int(inner.width()) - 31
            shown = QFontMetrics(font).elidedText(text, Qt.TextElideMode.ElideRight, room)
            width = min(inner.width(), 5 + 14 + 4 + QFontMetrics(font).horizontalAdvance(shown)
                        + 8)
            paint_rider(painter, QRectF(inner.left(), inner.center().y() - 11, width, 22), shown)
        elif state:
            name, token = STATE_LOOK[state]
            icons.paint(painter, name, QRectF(inner.left(), inner.center().y() - 9, 18, 18),
                        token)
            font = _font(option.font, 14, QFont.Weight.DemiBold)
            painter.setFont(font)
            painter.setPen(QColor(t["ok"] if state == "ok" else t["ink"]))
            area = inner.adjusted(24, 0, 0, 0)
            painter.drawText(area, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                             QFontMetrics(font).elidedText(text, Qt.TextElideMode.ElideRight,
                                                           int(area.width())))
        else:
            mono = bool(index.data(FILE_ROLE))
            bold = mono and flagged
            font = _font(option.font, 14 if mono else theme.FONT_SIZE,
                         QFont.Weight.Bold if bold else QFont.Weight.Normal, mono)
            colour = t["check_ink"] if bold else (t["ink_2"] if index.data(DIM_ROLE)
                                                   else t["ink"])
            area = QRectF(inner)
            if note:
                area = QRectF(inner.left(), inner.top() + 6, inner.width(), 22)
            painter.setFont(font)
            painter.setPen(QColor(colour))
            painter.drawText(area, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                             QFontMetrics(font).elidedText(text, Qt.TextElideMode.ElideMiddle,
                                                           int(area.width())))
            if note:
                line = QRectF(inner.left(), area.bottom(), inner.width(), 22)
                icons.paint(painter, "info", QRectF(line.left(), line.center().y() - 8, 16, 16),
                            "qr")
                small = _font(option.font, 14, QFont.Weight.Normal)
                painter.setFont(small)
                painter.setPen(QColor(t["ink_2"]))
                rest = line.adjusted(22, 0, 0, 0)
                painter.drawText(rest, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                                 QFontMetrics(small).elidedText(note, Qt.TextElideMode.ElideRight,
                                                                int(rest.width())))
        painter.restore()


def _icon_row(icon_widget: QWidget, text: QLabel, figure: QLabel | None = None) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(8)
    row.addWidget(icon_widget)
    row.addWidget(text, 1)
    if figure is not None:
        figure.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(figure)
    return row


class DisaAktarScreen(QWidget):
    finished = Signal()
    job_deleted = Signal()

    def __init__(
        self,
        controller: Callable[[], JobController | None],
        templates: Callable[[], Mapping[str, Template]],
        settings_path: Path | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("page")
        self.controller = controller
        self.templates = templates
        self.settings_path = settings_path
        self.task: Task | None = None
        self.out_dir: Path | None = None
        self._written = False  # the table shows what was written, not the preview
        self._written_for: JobController | None = None
        self._stage = "write"
        self._stage_started = 0.0

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        left = QFrame()
        left.setObjectName("card")
        left.setProperty("edge", "right")
        left.setFixedWidth(420)
        form = QVBoxLayout(left)
        form.setContentsMargins(24, 16, 24, 16)
        form.setSpacing(0)
        self.heading = Heading("Dışa aktar")
        form.addWidget(self.heading)

        # Target folder
        form.addSpacing(12)
        form.addWidget(self._strong("Hedef klasör"))
        form.addSpacing(6)
        row = QHBoxLayout()
        row.setSpacing(8)
        self.folder = QLineEdit()
        self.folder.setPlaceholderText("Boş bir klasör seçin")
        self.folder.textChanged.connect(self._check_folder)
        self.choose_button = key_button("Seç…", "", icon="folder")
        self.choose_button.clicked.connect(self.choose_folder)
        row.addWidget(self.folder, 1)
        row.addWidget(self.choose_button)
        form.addLayout(row)
        form.addSpacing(6)
        self.folder_icon = icon_label("info", "qr")
        self.folder_state = label("", "hint", wrap=True)
        form.addLayout(_icon_row(self.folder_icon, self.folder_state))
        form.addSpacing(12)
        form.addWidget(rule())

        # What is written
        form.addSpacing(12)
        self.layer = QCheckBox("Aranabilir metin katmanı ekle")
        self.layer.setChecked(True)
        form.addWidget(self.layer)
        form.addWidget(self._indented("OCR, PDF/A"))
        form.addSpacing(8)
        index_row = QHBoxLayout()
        index_row.setSpacing(8)
        index_row.addSpacing(1)
        index_row.addWidget(icon_label("sheet", "ink_2"))
        index_row.addWidget(label("index.xlsx her zaman yazılır", "value"), 1)
        form.addLayout(index_row)
        form.addWidget(self._indented("Her dosya bir satır: adı, sayfaları, değerleri"))
        form.addSpacing(12)
        form.addWidget(rule())

        # Retention
        form.addSpacing(10)
        row = QHBoxLayout()
        row.setSpacing(12)
        row.addWidget(self._strong("İşi sakla"))
        self.retention = QComboBox()
        self.retention.setMinimumWidth(200)
        self.retention.setToolTip("Dışa aktarılan iş bu bilgisayarda ne kadar saklansın")
        for value, text in RETENTION:
            self.retention.addItem(text, value)
        row.addWidget(self.retention)
        row.addStretch(1)
        form.addLayout(row)
        form.addSpacing(10)
        form.addWidget(rule())

        # Before export: the summary
        form.addSpacing(10)
        form.addWidget(self._strong("Yazılmadan önce"))
        form.addSpacing(4)
        summary = QGridLayout()
        summary.setContentsMargins(0, 0, 0, 0)
        summary.setHorizontalSpacing(8)
        summary.setVerticalSpacing(0)
        summary.setColumnStretch(1, 1)
        self.count_all = label("", "figure")
        self.count_ok = label("", "figure")
        self.count_check = label("", "figure")
        self.count_none = label("", "figure")
        check_cell = QHBoxLayout()
        check_cell.setSpacing(8)
        check_cell.addWidget(Rider())
        check_cell.addWidget(QLabel("işaretli"), 1)
        lines = [
            (icon_label("file", "ink"), QLabel("Yazılacak belge"), self.count_all),
            (icon_label("ok", "ok"), QLabel("Tamam"), self.count_ok),
            (None, check_cell, self.count_check),
            (icon_label("no", "ink_2"), QLabel("Şablon yok"), self.count_none),
        ]
        for number, (pic, text, figure) in enumerate(lines):
            summary.setRowMinimumHeight(number, 30)
            if pic is None:
                summary.addLayout(text, number, 0, 1, 2)
            else:
                summary.addWidget(pic, number, 0)
                summary.addWidget(text, number, 1)
            figure.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            summary.addWidget(figure, number, 2)
        form.addLayout(summary)
        form.addSpacing(4)
        self.preflight = label("", "hint", wrap=True)
        form.addWidget(self.preflight)

        # Go
        form.addSpacing(14)
        row = QHBoxLayout()
        row.setSpacing(10)
        self.export_button = key_button("Dışa aktar", "Ctrl+E", primary=True, icon="drop")
        self.export_button.clicked.connect(self.export)
        row.addWidget(self.export_button)
        self.lock_hint = label("Yazma sürerken kilitli", "hint")
        row.addWidget(self.lock_hint)
        row.addStretch(1)
        form.addLayout(row)
        form.addStretch(1)
        root.addWidget(left)

        # Right: the file names (preview, then what was written)
        right = QVBoxLayout()
        right.setContentsMargins(24, 16, 24, 12)
        right.setSpacing(0)
        self.results_heading = Heading("Dosya adları")
        right.addWidget(self.results_heading)
        self.progress_block = QWidget()
        block = QVBoxLayout(self.progress_block)
        block.setContentsMargins(0, 12, 0, 12)
        block.setSpacing(10)
        top = QHBoxLayout()
        top.setSpacing(12)
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("font-weight: 700;")
        self.stage_label = QLabel("")
        self.eta_label = label("", "hint")
        self.cancel_button = key_button("İptal", "Esc", icon="no")
        self.cancel_button.clicked.connect(self.cancel)
        top.addWidget(self.progress_label)
        top.addWidget(self.stage_label)
        top.addStretch(1)
        top.addWidget(self.eta_label)
        top.addWidget(self.cancel_button)
        block.addLayout(top)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        block.addWidget(self.progress)
        block.addWidget(rule())
        right.addWidget(self.progress_block)
        right.addSpacing(14)
        self.results = QTableWidget(0, 4)
        self.results.setHorizontalHeaderLabels(["Dosya", "Sayfalar", "Şablon", "Durum"])
        self.results.verticalHeader().setVisible(False)
        self.results.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.results.setShowGrid(False)
        self.results.setWordWrap(False)
        self.results.setFrameShape(QFrame.Shape.NoFrame)
        self.results.setItemDelegate(_FileDelegate(self.results))
        self.results.currentCellChanged.connect(lambda *_: self.results.viewport().update())
        header = self.results.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header.setHighlightSections(False)
        header.setMinimumSectionSize(80)
        theme.bind_style(self.results, lambda: (
            f"QTableWidget {{ background: {theme.TOKENS['ground']}; }}"
            f"QHeaderView::section {{ background: {theme.TOKENS['ground']}; "
            "padding: 0 10px 6px 10px; }"))
        right.addWidget(self.results, 1)
        right.addSpacing(8)
        self.count_line = label("", "hint", wrap=True)
        right.addWidget(self.count_line)
        right.addSpacing(10)
        self.message_icon = icon_label("ok", "ok")
        self.message_icon.hide()
        self.message = label("", wrap=True)
        self.message.setStyleSheet("font-weight: 600;")
        self.message.hide()
        message_row = _icon_row(self.message_icon, self.message)
        message_row.setAlignment(self.message_icon, Qt.AlignmentFlag.AlignTop)
        right.addLayout(message_row)
        right.addSpacing(14)
        right.addWidget(rule())
        right.addSpacing(14)
        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        self.open_index = key_button("index.xlsx'i aç", "", icon="sheet")
        self.open_folder = key_button("Klasörü aç", "", icon="folder")
        self.open_index.clicked.connect(lambda: self._open(self.out_dir / "index.xlsx"))
        self.open_folder.clicked.connect(lambda: self._open(self.out_dir))
        self.after_hint = QWidget()
        hint_row = QHBoxLayout(self.after_hint)
        hint_row.setContentsMargins(0, 0, 0, 0)
        hint_row.setSpacing(6)
        hint_row.addWidget(icon_label("clock", "ink_2"))
        hint_row.addWidget(label("Yazma bitince açılır", "hint"))
        buttons.addWidget(self.open_index)
        buttons.addWidget(self.open_folder)
        buttons.addWidget(self.after_hint)
        buttons.addStretch(1)
        right.addLayout(buttons)
        right.addStretch(1)
        root.addLayout(right, 1)

        # Ctrl+E is the registry action app.disa_aktar (main window).
        for key, slot in {"Esc": self.cancel}.items():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(slot)

        self._load_settings()
        self.retention.currentIndexChanged.connect(self._save_settings)
        self._set_busy(False)
        self._set_opened(False)
        self._check_folder()
        self.refresh()

    @staticmethod
    def _strong(text: str) -> QLabel:
        widget = QLabel(text)
        widget.setStyleSheet("font-weight: 700;")
        return widget

    @staticmethod
    def _indented(text: str) -> QLabel:
        widget = label(text, "hint", wrap=True)
        widget.setContentsMargins(26, 0, 0, 0)
        return widget

    # Settings
    def _load_settings(self) -> None:
        try:
            value = load_settings(self.settings_path).retention
        except SettingsError as error:
            self._say(str(error), "warn", "check_ink")
            value = KEEP
        index = self.retention.findData(value)
        if index < 0:
            self.retention.addItem(f"{value} gün", value)
            index = self.retention.count() - 1
        self.retention.setCurrentIndex(index)

    def _save_settings(self) -> None:
        save_settings(Settings(self.retention.currentData()), self.settings_path)

    # Messages
    def _say(self, text: str, icon: str = "ok", colour: str = "ok") -> None:
        self.message.setText(text)
        self.message_icon.setPixmap(icons.pixmap(icon, colour, 18))
        self.message_icon.setVisible(bool(text))
        self.message.setVisible(bool(text))

    # Before export
    def _check_folder(self) -> None:
        """Say under the field whether the folder can take the export."""
        text = self.folder.text().strip()
        icon, colour = "info", "qr"
        if not text:
            message = "Boş bir klasör seçin ya da yazın; yoksa oluşturulur."
        else:
            path = Path(text)
            try:
                if not path.exists():
                    message = "Klasör yok; dışa aktarınca oluşturulur."
                elif not path.is_dir():
                    icon, colour = "no", "ink"
                    message = "Bu bir dosya, klasör değil."
                else:
                    old = [p for p in path.iterdir()
                           if p.suffix.lower() == ".pdf" or p.name.lower() == "index.xlsx"]
                    if old:
                        icon, colour = "no", "ink"
                        message = ("Klasörde önceki bir dışa aktarım var; "
                                   "boş bir klasör seçin.")
                    else:
                        icon, colour = "ok", "ok"
                        message = "Klasör boş"
            except OSError as error:
                icon, colour = "no", "ink"
                message = f"Klasöre bakılamadı: {error.strerror or error}"
        self.folder_icon.setPixmap(icons.pixmap(icon, colour, 18))
        self.folder_state.setText(message)
        self.folder_state.setProperty("role", "ok" if icon == "ok" else "hint")
        self.folder_state.style().unpolish(self.folder_state)
        self.folder_state.style().polish(self.folder_state)

    def refresh(self) -> None:
        controller = self.controller()
        if self._written and controller is not self._written_for and self.task is None:
            self._written = False  # another job is open: show its names again
            self._set_opened(False)
        if controller is None:
            self.heading.setText("Dışa aktar", "")
            for figure in (self.count_all, self.count_ok, self.count_check, self.count_none):
                figure.setText("–")
            self.preflight.setText("Önce Yükle sekmesinden bir iş açın.")
            self.export_button.setEnabled(False)
            if not self._written:
                self._fill([])
                self.results_heading.setText("Dosya adları", "")
                self.count_line.setText("")
            return
        self.export_button.setEnabled(self.task is None)
        job = controller.job
        items = plan_export(job, self.templates())
        checks = sum(1 for item in items if item.checks)
        no_template = sum(1 for item in items if item.template_name is None and not item.checks)
        pages = sum(len(item.document.page_ids) for item in items)
        self.heading.setText("Dışa aktar", f"{len(items)} belge · {pages} sayfa")
        self.count_all.setText(str(len(items)))
        self.count_ok.setText(str(len(items) - checks - no_template))
        self.count_check.setText(str(checks))
        self.count_none.setText(str(no_template))
        self.preflight.setText(
            "Kontrol gerekenler de yazılır; index.xlsx'te işaretlenir ve nedeni yazılır. "
            "Hiçbiri sessizce geçmez."
        )
        if not self._written:
            self._show_preview(job, items)

    def _show_preview(self, job, items) -> None:
        ordered = sorted(items, key=lambda item: not item.checks)  # flagged first
        rows = []
        for item in ordered:
            if item.checks:
                state, text = "check", "Kontrol · " + item.checks[0]
            elif item.template_name is None:
                state, text = "none", "Şablon yok · numaralı ad"
            else:
                state, text = "ok", "Tamam"
            rows.append((f"{item.name}.pdf", _pages(job, item.document), item.template_name,
                         state, text, "; ".join(item.checks), None))
        self._fill(rows)
        self.results_heading.setText("Dosya adları", f"önizleme · {len(items)} dosya")
        self.count_line.setText(
            "Adlar şablondaki kalıptan gelir; klasör yolu uzunsa yazarken kısaltılabilir. "
            "İşaretliler üstte." if items else "Yazılacak belge yok.")

    def _fill(self, rows) -> None:
        """rows: (file name, pages, template name, state, status text, tooltip, note)."""
        self.results.setRowCount(len(rows))
        for row, (name, pages, template, state, text, tip, note) in enumerate(rows):
            flagged = state == "check"
            cells = [QTableWidgetItem(name), QTableWidgetItem(pages),
                     QTableWidgetItem(template or "Şablon yok"), QTableWidgetItem(text)]
            cells[0].setData(FILE_ROLE, True)
            cells[0].setToolTip(name)
            if note:
                cells[0].setData(NOTE_ROLE, note)
            if not template:
                cells[2].setData(DIM_ROLE, True)
            cells[3].setData(STATE_ROLE, state)
            if tip:
                cells[3].setToolTip(tip)
            for column, cell in enumerate(cells):
                if flagged:
                    cell.setData(FLAG_ROLE, True)
                self.results.setItem(row, column, cell)
            self.results.setRowHeight(row, 56 if note else 36)
        header = self.results.horizontalHeader()
        self.results.resizeColumnsToContents()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in (1, 2):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Interactive)
        self.results.setColumnWidth(3, min(max(self.results.columnWidth(3), 160), 360))
        # Only as tall as its rows, so the notes and buttons sit right under them.
        rows = sum(self.results.rowHeight(r) for r in range(self.results.rowCount())) or 36
        self.results.setMaximumHeight(header.sizeHint().height() + rows + 2
                                      + self.results.horizontalScrollBar().sizeHint().height())

    def _path_heading(self, folder: Path) -> None:
        """"Yazılan dosyalar" with the folder beside it, shortened in the middle to fit."""
        metrics = QFontMetrics(self.results_heading.subtitle.font())
        text = metrics.elidedText(str(folder), Qt.TextElideMode.ElideMiddle, 520)
        self.results_heading.setText("Yazılan dosyalar", text)
        self.results_heading.subtitle.setToolTip(str(folder))

    def choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Boş bir klasör seçin")
        if folder:
            self.folder.setText(folder)

    # Export
    def export(self) -> None:
        controller = self.controller()
        if controller is None or self.task is not None:
            return
        if not self.folder.text().strip():
            self._say("Önce boş bir hedef klasör seçin.", "warn", "check_ink")
            return
        out_dir = Path(self.folder.text().strip())
        controller.store.save(controller.job)  # marks the job as in use for the day limit
        # The worker gets its own copy: the live job can still be edited meanwhile.
        job = job_from_dict(job_to_dict(controller.job))
        files = controller.store.batch_files(job)
        self._exporting = (controller, job)
        templates = dict(self.templates())
        with_layer = self.layer.isChecked()

        def report(progress, stage, done, total):
            self._stage = stage  # read by the window thread with the next progress signal
            progress(done, total)

        def work(progress):
            try:
                return export_job(job, files, templates, out_dir, with_layer=with_layer,
                                  progress=lambda stage, done, total: report(progress, stage,
                                                                             done, total))
            except EngineUnavailable as error:
                raise ExportError(f"{error}. Metin katmanı olmadan yazmak için "
                                  "“Aranabilir metin katmanı ekle” kutusunu kapatın.") from None

        self.out_dir = out_dir
        self._say("")
        self._written = False
        self._set_opened(False)
        self._stage = "write"
        self._stage_seen = None
        self.task = Task(work)
        self.task.signals.progress.connect(self._progress)
        self.task.signals.done.connect(self._done)
        self.task.signals.failed.connect(self._failed)
        self.task.signals.cancelled.connect(self._cancelled)
        self.progress_label.setText("Yazılıyor…")
        self.stage_label.setText("")
        self.eta_label.setText("")
        self.progress.setRange(0, 0)
        self._path_heading(out_dir)
        self._set_busy(True)
        start(self.task)

    def _progress(self, done: int, total: int) -> None:
        stage = self._stage
        if stage != getattr(self, "_stage_seen", None):
            self._stage_seen = stage
            self._stage_started = time.monotonic()
        self.progress.setRange(0, max(1, total))
        self.progress.setValue(done)
        self.progress_label.setText(f"Yazılıyor: {done} / {total}")
        self.stage_label.setText(f"· {STAGES.get(stage, '')}")
        percent = round(done * 100 / total) if total else 0
        eta = f"%{percent}"
        if 0 < done < total:
            left = (time.monotonic() - self._stage_started) / done * (total - done)
            eta += (f" · yaklaşık {max(1, round(left / 60))} dk kaldı" if left >= 60
                    else " · bir dakikadan az kaldı")
        self.eta_label.setText(eta)

    def _done(self, result) -> None:
        controller, job = self._exporting  # the job that was exported, not the open one
        ordered = sorted(zip(result.paths, result.items, strict=True),
                         key=lambda pair: not pair[1].checks)  # flagged files first
        rows = []
        for path, item in ordered:
            pdfa_notes = [c for c in item.checks if c.startswith("PDF/A değil")]
            others = [c for c in item.checks if c not in pdfa_notes]
            note = None
            if others:
                state, text = "check", "Kontrol · " + others[0]
            elif pdfa_notes:
                state, text = "info", "Yazıldı · PDF/A değil"
                note = pdfa_notes[0]
            elif item.template_name is None:
                state, text = "none", "Yazıldı · şablon yok"
            else:
                state, text = "ok", "Yazıldı"
            rows.append((path.name, _pages(job, item.document), item.template_name, state, text,
                         "; ".join(item.checks), note))
        self._fill(rows)
        self._written = True
        self._written_for = controller
        self._path_heading(self.out_dir)
        self.count_line.setText(f"{len(result.paths)} dosya yazıldı · işaretliler üstte"
                                + (" · liste kaydırılır" if len(rows) > 12 else ""))
        message = (f"{len(result.paths)} belge yazıldı, {result.needing_check} belge kontrol "
                   "gerektiriyor. Liste: index.xlsx")
        if self.retention.currentData() == DELETE_AFTER_EXPORT and may_delete_after_export(result):
            controller.store.delete(job.id)
            message += " İş silindi (saklama ayarı)."
            self.job_deleted.emit()
        elif (self.retention.currentData() == DELETE_AFTER_EXPORT and result.paths
              and not result.with_layer):
            message += " İş saklandı: metin katmanı eklenmedi."
        self._set_opened(True, index=bool(result.paths))
        self._finish(message, *(("warn", "check_ink") if result.needing_check else ("ok", "ok")))

    def _failed(self, message: str) -> None:
        self._finish(message, "warn", "check_ink")

    def _cancelled(self) -> None:
        written = sorted(p.name for p in self.out_dir.glob("*.pdf")) if self.out_dir else []
        if written:
            self._set_opened(True, index=False)
        self._finish(
            f"Dışa aktarma durduruldu: {len(written)} dosya yazıldı, index.xlsx yazılmadı. "
            "Yeniden dışa aktarmak için boş bir klasör seçin.", "info", "qr"
        )

    def _finish(self, message: str, icon: str = "ok", colour: str = "ok") -> None:
        self.task = None
        self._exporting = None
        self._set_busy(False)
        self.progress_label.setText("")
        self._say(message, icon, colour)
        self._check_folder()
        self.refresh()
        self.finished.emit()

    def cancel(self) -> None:
        if self.task is not None:
            self.task.cancel()

    def busy(self) -> bool:
        return self.task is not None

    def _set_busy(self, busy: bool) -> None:
        self.progress_block.setVisible(busy)
        self.cancel_button.setVisible(busy)
        self.progress.setVisible(busy)
        self.export_button.setEnabled(not busy and self.controller() is not None)
        self.lock_hint.setVisible(busy)
        for widget in (self.folder, self.choose_button, self.layer, self.retention):
            widget.setEnabled(not busy)

    def _set_opened(self, folder: bool, index: bool | None = None) -> None:
        self.open_folder.setEnabled(folder)
        self.open_index.setEnabled(folder if index is None else index)
        self.after_hint.setVisible(not folder)

    def _open(self, path: Path) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
