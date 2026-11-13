"""The Değerler screen: every read value in one table; unsure ones are marked and fixed here."""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping

import pypdfium2 as pdfium
from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QKeySequence, QPainter, QPen, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemDelegate,
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFrame,
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

from evrakci.pipeline.cuts import (
    Document,
    current_read_error,
    current_values,
    document_template,
    record_read_error,
)
from evrakci.pipeline.export import plan_export
from evrakci.pipeline.job import parse_page_id
from evrakci.pipeline.ocr.engine import EngineUnavailable
from evrakci.pipeline.render import render_page
from evrakci.pipeline.review import needs_reading, store_reading
from evrakci.pipeline.templates.model import Template, template_revision
from evrakci.pipeline.templates.read import read_document
from evrakci.ui import icons, theme
from evrakci.ui.controller import JobController
from evrakci.ui.widgets import (
    STATES,
    Heading,
    PanelHeading,
    StateLabel,
    Toolbar,
    icon_label,
    key_button,
    label,
    paint_rider,
)
from evrakci.ui.workers import Task, start

DOC_ROLE = Qt.ItemDataRole.UserRole + 1
KEY_ROLE = Qt.ItemDataRole.UserRole + 2
FLAG_ROLE = Qt.ItemDataRole.UserRole + 3  # the value needs a check: wash, warn icon, bold
EMPTY_ROLE = Qt.ItemDataRole.UserRole + 4  # what an unsure empty value says ("boş · zorunlu")
EDITED_ROLE = Qt.ItemDataRole.UserRole + 5  # typed by hand: the small "elle" tag
STATE_ROLE = Qt.ItemDataRole.UserRole + 6  # Durum column: "check", "ok" or "none"

ROW_HEIGHT = 40  # DESIGN.md: rows are 40px in Değerler
UNREAD = "değerler okunmadı"
MONO = 'Consolas, "DejaVu Sans Mono", monospace'


def _font(base: QFont, size: int, weight: QFont.Weight) -> QFont:
    font = QFont(base)
    font.setPixelSize(size)
    font.setWeight(weight)
    return font


def _section_name(section: int | None) -> str:
    """Section 0 is the template's own box; later ones are its variants (as in Şablonlar)."""
    return "Bölüm 1" if not section else f"Varyant {section + 1}"


def _rider_width(font: QFont) -> int:
    return 5 + 14 + 4 + QFontMetrics(font).horizontalAdvance("Kontrol") + 8


class _CellDelegate(QStyledItemDelegate):
    """Paints the value table like the mockup: rules not grid, flagged cells on the check
    wash with the warn icon, the "elle" tag on edited values, and riders in the Durum column.

    Item texts stay plain, so editing and tests see only the value itself.
    """

    TAG = "elle"

    def __init__(self, view: QTableWidget) -> None:
        super().__init__(view)
        self.view = view

    # Size
    def _tag_width(self, font: QFont) -> int:
        return 5 + 13 + 3 + QFontMetrics(_font(font, theme.SMALL, QFont.Weight.DemiBold)
                                         ).horizontalAdvance(self.TAG) + 5

    def sizeHint(self, option, index) -> QSize:
        font = option.font
        state = index.data(STATE_ROLE)
        if state == "check":
            return QSize(16 + _rider_width(_font(font, theme.SMALL, QFont.Weight.Bold)),
                         ROW_HEIGHT)
        if state:
            word = STATES[state][2]
            width = QFontMetrics(_font(font, 14, QFont.Weight.DemiBold)).horizontalAdvance(word)
            return QSize(16 + 18 + 6 + width, ROW_HEIGHT)
        flagged = bool(index.data(FLAG_ROLE))
        text = index.data(Qt.ItemDataRole.DisplayRole) or index.data(EMPTY_ROLE) or "—"
        weight = QFont.Weight.Bold if flagged else QFont.Weight.Normal
        width = 16 + QFontMetrics(_font(font, theme.FONT_SIZE, weight)).horizontalAdvance(text)
        if flagged:
            width += 16 + 5
        if index.data(EDITED_ROLE):
            width += 8 + self._tag_width(font)
        return QSize(width + 4, ROW_HEIGHT)

    # Paint
    def paint(self, painter: QPainter, option, index) -> None:
        t = theme.TOKENS
        rect = option.rect
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        current = self.view.currentIndex()
        flagged = bool(index.data(FLAG_ROLE))
        if flagged:
            painter.fillRect(rect, QColor(t["check_wash"]))
        elif current.isValid() and current.row() == index.row():
            painter.fillRect(rect, QColor(t["row_cur"]))
        painter.fillRect(rect.left(), rect.bottom(), rect.width(), 1, QColor(t["rule"]))
        inner = QRectF(rect.adjusted(8, 0, -8, -1))
        state = index.data(STATE_ROLE)
        if state == "check":
            font = _font(option.font, theme.SMALL, QFont.Weight.Bold)
            width = _rider_width(font)
            paint_rider(painter, QRectF(inner.left(), inner.center().y() - 10.5, width, 21),
                        "Kontrol")
        elif state:
            name, token, word = STATES[state]
            icons.paint(painter, name, QRectF(inner.left(), inner.center().y() - 9, 18, 18),
                        token)
            painter.setFont(_font(option.font, 14, QFont.Weight.DemiBold))
            painter.setPen(QColor(t[token]))
            painter.drawText(inner.adjusted(24, 0, 0, 0),
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, word)
        else:
            self._paint_value(painter, option, index, inner, flagged, current)
        if current.isValid() and current == index:  # the focused cell: firm pencil frame
            painter.setPen(QPen(QColor(t["focus"]), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRectF(rect).adjusted(1, 1, -1, -2))
        painter.restore()

    def _paint_value(self, painter, option, index, inner: QRectF, flagged: bool,
                     current) -> None:
        t = theme.TOKENS
        text = index.data(Qt.ItemDataRole.DisplayRole) or ""
        x = inner.left()
        if flagged:
            icons.paint(painter, "warn", QRectF(x, inner.center().y() - 8, 16, 16), "check_ink")
            x += 21
        colour = t["check_ink"] if flagged else t["ink"]
        bold = flagged or (index.column() == 0 and current.isValid()
                           and current.row() == index.row())
        weight = QFont.Weight.Bold if bold else QFont.Weight.Normal
        if not text:
            text = index.data(EMPTY_ROLE) or ""
            if text:
                weight = QFont.Weight.DemiBold
            else:
                text, colour = "—", t["ink_2"]
        font = _font(option.font, theme.FONT_SIZE, weight)
        tag = self._tag_width(option.font) + 8 if index.data(EDITED_ROLE) else 0
        metrics = QFontMetrics(font)
        room = max(0, int(inner.right() - x - tag))
        shown = metrics.elidedText(text, Qt.TextElideMode.ElideRight, room)
        painter.setFont(font)
        painter.setPen(QColor(colour))
        area = QRectF(x, inner.top(), room, inner.height())
        painter.drawText(area, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, shown)
        if tag:
            left = x + metrics.horizontalAdvance(shown) + 8
            self._paint_tag(painter, option.font, QRectF(left, inner.center().y() - 10,
                                                         tag - 8, 20))

    def _paint_tag(self, painter: QPainter, base: QFont, box: QRectF) -> None:
        t = theme.TOKENS
        painter.setPen(QPen(QColor(t["rule_strong"]), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(box.adjusted(0.5, 0.5, -0.5, -0.5), 3, 3)
        icons.paint(painter, "pen", QRectF(box.left() + 5, box.center().y() - 6.5, 13, 13),
                    "ink_2")
        painter.setFont(_font(base, theme.SMALL, QFont.Weight.DemiBold))
        painter.setPen(QColor(t["ink_2"]))
        painter.drawText(box.adjusted(21, 0, 0, -1),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.TAG)


def _note_line(icon: str) -> tuple[QWidget, QLabel]:
    """A muted footer line with a leading icon (filter and not-yet-read notes)."""
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    text = label("", "hint")
    text.setTextFormat(Qt.TextFormat.RichText)
    layout.addWidget(icon_label(icon, "ink_2"))
    layout.addWidget(text, 1)
    return row, text


class ValueSide(QFrame):
    """The selected value: what was read, the suggestion, and what to do."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setProperty("edge", "left")
        self.setFixedWidth(380)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 16)
        layout.setSpacing(0)
        self.heading = PanelHeading("Bir değer seçin")
        self.title = self.heading.title
        self.meta = self.heading.meta
        layout.addWidget(self.heading)

        # Nothing selected
        self.empty = QWidget()
        empty = QHBoxLayout(self.empty)
        empty.setContentsMargins(0, 14, 0, 0)
        empty.setSpacing(8)
        empty.addWidget(icon_label("info", "qr"), 0, Qt.AlignmentFlag.AlignTop)
        self.empty_text = label("Tablodan bir değer hücresi seçin. N sonraki kontrole gider; "
                                "işaretli hücrede öneriyi Enter ile kabul edersiniz.",
                                "hint", wrap=True)
        empty.addWidget(self.empty_text, 1)
        layout.addWidget(self.empty)

        # The value that was read, and the suggestion
        self.details = QWidget()
        details = QVBoxLayout(self.details)
        details.setContentsMargins(0, 12, 0, 0)
        details.setSpacing(4)
        read_row = QHBoxLayout()
        read_row.setSpacing(8)
        self.read_caption = label("Okunan:", "hint")
        self.read = label("", "bad")
        self.read_note = label("", "hint")
        read_row.addWidget(self.read_caption)
        read_row.addWidget(self.read)
        read_row.addWidget(self.read_note)
        read_row.addStretch(1)
        details.addLayout(read_row)
        self.state = StateLabel("ok")
        details.addWidget(self.state)
        self.suggestion_caption = label("", "hint")
        self.suggestion = QLabel("")
        self.suggestion.setStyleSheet(
            f"font-family: {MONO}; font-size: 28px; font-weight: 700; letter-spacing: 1px;")
        self.suggestion.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        details.addSpacing(2)
        details.addWidget(self.suggestion_caption)
        details.addWidget(self.suggestion)
        layout.addWidget(self.details)

        layout.addSpacing(12)
        self.accept_button = key_button("Öneriyi kabul et", "Enter", primary=True, icon="check")
        self.type_button = key_button("Elle yaz", "F2", icon="pen")
        self.variant_button = key_button("Yeni varyant çiz", "V", icon="box")
        for button in (self.accept_button, self.type_button, self.variant_button):
            button.setFixedHeight(38)
            layout.addWidget(button)
            layout.addSpacing(8)
        layout.addStretch(1)
        self.show_empty()

    def show_nothing(self) -> None:
        """Clear the value part (the heading stays): used before a cell is described."""
        for widget in (self.read, self.read_note, self.suggestion, self.suggestion_caption):
            widget.setText("")
        self.read.setVisible(False)
        self.read_caption.setVisible(False)
        self.state.setVisible(False)
        self.accept_button.setEnabled(False)

    def show_empty(self) -> None:
        """No value cell is selected."""
        self.show_nothing()
        self.heading.set("Bir değer seçin", "Değeri olan bir hücre seçilince burada görünür.")
        self.empty.setVisible(True)
        self.details.setVisible(False)
        self.type_button.setEnabled(False)
        self.variant_button.setEnabled(False)

    def show_value(self) -> None:
        self.empty.setVisible(False)
        self.details.setVisible(True)
        self.type_button.setEnabled(True)
        self.variant_button.setEnabled(True)


class DegerlerScreen(QWidget):
    draw_variant = Signal(int, str)  # document number, variable name
    status = Signal(str)
    finished = Signal()

    def __init__(
        self,
        controller: Callable[[], JobController | None],
        templates: Callable[[], Mapping[str, Template]],
        engine: Callable[[], object] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("page")
        self.controller = controller
        self.templates = templates
        self.engine = engine
        self.task: Task | None = None
        self._columns: list[str] = []
        self._filling = False
        self._started = 0.0

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Toolbar band
        bar = Toolbar()
        self.only_checks = QCheckBox("Yalnızca kontrol gerekenler")
        self.only_checks.setChecked(True)
        self.only_checks.toggled.connect(self.refresh)
        self.template_filter = QComboBox()
        self.template_filter.setMinimumWidth(150)
        self.template_filter.currentIndexChanged.connect(self.refresh)
        self.search = QLineEdit()
        self.search.setProperty("role", "search")
        self.search.setPlaceholderText("Ara: firma, sicil no…")
        self.search.addAction(icons.icon("search", "ink_2"),
                              QLineEdit.ActionPosition.LeadingPosition)
        self.search.setClearButtonEnabled(True)
        self.search.setFixedWidth(236)
        self.search.textChanged.connect(self.refresh)
        self.missing_button = key_button("Yalnızca eksikleri oku", "", icon="play")
        self.missing_button.setToolTip("Değeri hiç okunmamış ya da şablonu değişmiş belgeleri "
                                       "okur; elle yazdıklarınız korunur.")
        self.missing_button.clicked.connect(lambda: self.read_values(only_missing=True))
        self.read_button = key_button("Değerleri oku", "", icon="play")
        self.read_button.setToolTip("Şablonu olan bütün belgeleri yeniden okur; "
                                    "elle yazdıklarınız korunur.")
        self.read_button.clicked.connect(lambda: self.read_values(only_missing=False))
        bar.row.setSpacing(8)
        bar.add(self.only_checks, None, self.template_filter, self.search, "stretch",
                self.missing_button, self.read_button)
        root.addWidget(bar)

        # Progress band: while reading, and for the message after it
        self.progress_band = QFrame()
        self.progress_band.setProperty("role", "toolbar")
        self.progress_band.setFixedHeight(46)
        band = QHBoxLayout(self.progress_band)
        band.setContentsMargins(16, 0, 16, 0)
        band.setSpacing(14)
        self.progress_icon = icon_label("info", "qr")
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("font-weight: 700;")
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedWidth(320)
        self.progress_hint = label("", "hint")
        self.cancel_button = key_button("İptal", "Esc", icon="no")
        self.cancel_button.clicked.connect(self.cancel)
        self.dismiss_button = key_button("Kapat", icon="x", icon_only=True)
        self.dismiss_button.clicked.connect(self._dismiss)
        band.addWidget(self.progress_icon)
        band.addWidget(self.progress_label)
        band.addWidget(self.progress)
        band.addWidget(self.progress_hint, 1)
        band.addWidget(self.cancel_button)
        band.addWidget(self.dismiss_button)
        root.addWidget(self.progress_band)

        # Table column
        body = QHBoxLayout()
        body.setSpacing(0)
        work = QVBoxLayout()
        work.setContentsMargins(24, 14, 24, 12)
        work.setSpacing(0)
        self.heading = Heading("")
        work.addWidget(self.heading)
        work.addSpacing(14)
        self.table = QTableWidget()
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.table.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
        self.table.setShowGrid(False)
        self.table.setWordWrap(False)
        self.table.setFrameShape(QFrame.Shape.NoFrame)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        header = self.table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header.setHighlightSections(False)
        header.setMinimumSectionSize(54)
        ground = theme.TOKENS["ground"]
        self.table.setStyleSheet(
            f"QTableWidget {{ background: {ground}; }}"
            f"QHeaderView::section {{ background: {ground}; padding: 0 8px 6px 8px; }}")
        self.table.setItemDelegate(_CellDelegate(self.table))
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked
                                   | QAbstractItemView.EditTrigger.EditKeyPressed)
        self.table.setSortingEnabled(False)
        self.table.itemChanged.connect(self._item_changed)
        self.table.currentCellChanged.connect(self._cell_selected)
        work.addWidget(self.table, 1)
        work.addSpacing(10)
        self.unread_line, self.unread_note = _note_line("clock")
        self.filter_line, self.note = _note_line("funnel")
        work.addWidget(self.unread_line)
        work.addSpacing(4)
        work.addWidget(self.filter_line)
        work.addStretch(1)
        body.addLayout(work, 1)
        self.side = ValueSide()
        self.side.accept_button.clicked.connect(self.accept_current)
        self.side.type_button.clicked.connect(self.type_current)
        self.side.variant_button.clicked.connect(self._draw_variant)
        body.addWidget(self.side)
        root.addLayout(body, 1)

        # Return, F2, V and N are registry actions (main window).
        keys = {"Esc": self.cancel}
        for key, slot in keys.items():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(slot)
        self._set_busy(False)
        self.refresh()

    # Table
    def column_of(self, variable_name: str) -> int:
        return 3 + self._columns.index(variable_name)

    def _commit_open_editor(self) -> None:
        """Store text still being typed, so a refresh never throws it away."""
        if self.table.state() != QAbstractItemView.State.EditingState:
            return
        editor = self.table.findChild(QLineEdit)
        if editor is not None:
            self.table.commitData(editor)
            self.table.closeEditor(editor, QAbstractItemDelegate.EndEditHint.NoHint)

    def _empty_view(self, title: str) -> None:
        self.heading.setText(title, "")
        self.unread_line.setVisible(False)
        self.filter_line.setVisible(False)
        self.side.show_empty()

    def refresh(self) -> None:
        if self._filling:
            return
        self._commit_open_editor()
        controller = self.controller()
        self._filling = True
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        if controller is None:
            self._filling = False
            self._empty_view("Henüz açık iş yok")
            return
        templates = self.templates()
        self._refresh_template_filter(templates)
        job = controller.job
        items = plan_export(job, templates)
        wanted_template = self.template_filter.currentData()
        rows = []
        names: list[str] = []
        for item in items:
            template_id, _ = document_template(job, item.document)
            if template_id is None:
                continue
            template = templates.get(template_id)
            if template is not None:
                for variable in template.variables:
                    if variable.name not in names:
                        names.append(variable.name)
            rows.append((item, template_id, template))
        self._columns = names
        checks = sum(1 for item, _, _ in rows if item.checks)
        self.only_checks.setText(f"Yalnızca kontrol gerekenler ({checks})")
        query = self.search.text().strip().casefold()
        shown = []
        for item, template_id, template in rows:
            if self.only_checks.isChecked() and not item.checks:
                continue
            if wanted_template and template_id != wanted_template:
                continue
            if query and query not in " ".join(item.values.values()).casefold():
                continue
            shown.append((item, template))
        headers = ["Belge", "Sayfalar", "Şablon", *names, "Durum"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(shown))
        for row, (item, template) in enumerate(shown):
            self._fill_row(row, item, template)
        unread = sum(1 for item, _, _ in rows if self._state(item) == "none")
        pending = sum(1 for item, _, _ in rows if self._state(item) == "check")
        hidden = len(rows) - len(shown)
        if hidden:
            reason = ("kontrol gerekmeyen " if self.only_checks.isChecked()
                      and not query and not wanted_template else "")
            self.note.setText(f"<b>Filtre açık:</b> {reason}{hidden} belge gizli")
        else:
            self.note.setText("")
        self.filter_line.setVisible(bool(hidden))
        self.unread_note.setText(
            f"{unread} belge henüz okunmadı; <b>Değerleri oku</b> ile okunur" if unread else "")
        self.unread_line.setVisible(bool(unread))
        subtitle = f"{pending} kontrol" + (f" · {unread} okunmadı" if unread else "")
        numbers = [item.number for item, _ in shown]
        if not rows:
            self.heading.setText("Şablonlu belge yok",
                                 "Değerler, şablon uygulanmış belgelerden okunur")
        elif not numbers:
            self.heading.setText("Gösterilecek belge yok", subtitle)
        elif numbers[0] == numbers[-1]:
            self.heading.setText(f"Belge {numbers[0]}", subtitle)
        else:
            self.heading.setText(f"Belge {numbers[0]} — Belge {numbers[-1]}", subtitle)
        self._size_columns()
        self._fit_height()
        self._filling = False
        if not self.table.currentIndex().isValid():
            self._select_first_flag()
        self._describe_current()

    def _select_first_flag(self) -> None:
        """Start on the first value that needs a check, so the panel has something to say."""
        for row in range(self.table.rowCount()):
            for column in range(3, 3 + len(self._columns)):
                cell = self.table.item(row, column)
                if cell is not None and cell.data(FLAG_ROLE):
                    self.table.setCurrentCell(row, column)
                    return

    def _size_columns(self) -> None:
        header = self.table.horizontalHeader()
        for column in range(self.table.columnCount()):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Interactive)
        self.table.resizeColumnsToContents()
        if not self._columns:
            return
        widest = max(range(3, 3 + len(self._columns)), key=self.table.columnWidth)
        header.setSectionResizeMode(widest, QHeaderView.ResizeMode.Stretch)

    def _fit_height(self) -> None:
        """The table is only as tall as its rows, so the notes sit right under them."""
        header = self.table.horizontalHeader().sizeHint().height()
        rows = max(1, self.table.rowCount())
        self.table.setMaximumHeight(header + rows * ROW_HEIGHT + 2
                                    + self.table.horizontalScrollBar().sizeHint().height())

    @staticmethod
    def _state(item) -> str:
        if not item.checks:
            return "ok"
        if all(check == UNREAD for check in item.checks):
            return "none"
        return "check"

    def _fill_row(self, row: int, item, template: Template | None) -> str:
        controller = self.controller()
        job = controller.job
        document = item.document
        first, last = job.position_of(document.page_ids[0]), job.position_of(document.page_ids[-1])
        fixed = [str(item.number), f"{first}–{last}" if first != last else str(first),
                 template.name if template else "şablon bulunamadı"]
        for column, text in enumerate(fixed):
            cell = QTableWidgetItem(text)
            cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable)
            cell.setData(DOC_ROLE, item.number)
            self.table.setItem(row, column, cell)
        values = current_values(job, document) or {}
        by_name = {v.name: v for v in template.variables} if template else {}
        for name in self._columns:
            column = self.column_of(name)
            variable = by_name.get(name)
            value = values.get(variable.key) if variable else None
            text = value.value if value else ""
            cell = QTableWidgetItem(text)
            cell.setData(DOC_ROLE, item.number)
            if variable is None:
                cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable)
            else:
                cell.setData(KEY_ROLE, variable.key)
                if value is None:
                    cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable)
            unsure = value is not None and (value.flagged or (variable.required and not text))
            if unsure:
                cell.setData(FLAG_ROLE, True)
                cell.setData(EMPTY_ROLE, "boş · zorunlu" if variable.required else "boş")
                cell.setToolTip("Emin değil" + (f"; öneri: {value.suggestion}"
                                                if value.suggestion else ""))
            if value is not None and value.edited:
                cell.setData(EDITED_ROLE, True)
                cell.setToolTip("Elle düzeltildi")
            self.table.setItem(row, column, cell)
        state = self._state(item)
        status = QTableWidgetItem(STATES[state][2])
        status.setFlags(status.flags() & ~Qt.ItemFlag.ItemIsEditable)
        status.setData(DOC_ROLE, item.number)
        status.setData(STATE_ROLE, state)
        if item.checks:
            status.setToolTip("; ".join(item.checks))
        self.table.setItem(row, len(self._columns) + 3, status)
        return state

    def _refresh_template_filter(self, templates) -> None:
        current = self.template_filter.currentData()
        self.template_filter.blockSignals(True)
        self.template_filter.clear()
        self.template_filter.addItem("Şablon: hepsi", None)
        for template_id, template in sorted(templates.items(), key=lambda kv: kv[1].name):
            self.template_filter.addItem(template.name, template_id)
        self.template_filter.setCurrentIndex(max(0, self.template_filter.findData(current)))
        self.template_filter.blockSignals(False)

    # Selection and fixing
    def _current(self) -> tuple[Document, str] | None:
        cell = self.table.currentItem()
        if cell is None or cell.data(KEY_ROLE) is None:
            return None
        document = self.controller().documents()[cell.data(DOC_ROLE) - 1]
        return document, cell.data(KEY_ROLE)

    def _describe_current(self) -> None:
        current = self.table.currentIndex()
        if current.isValid():
            self._cell_selected(current.row(), current.column())
        else:
            self.side.show_empty()

    def _cell_selected(self, row: int, column: int, *_args) -> None:
        self.table.viewport().update()  # the current-row wash follows the cell
        if self._filling:
            return
        cell = self.table.item(row, column)
        current = self._current()
        if cell is None or current is None:
            self.side.show_empty()
            return
        document, key = current
        job = self.controller().job
        value = (current_values(job, document) or {}).get(key)
        name = self.table.horizontalHeaderItem(column).text()
        template = self.table.item(row, 2).text()
        pages = self.table.item(row, 1).text()
        pages = f"Sayfa {pages}"
        self.side.show_value()
        self.side.show_nothing()
        meta = [template, pages]
        error = current_read_error(job, document)
        if value is not None and value.flagged:
            meta.append(f"{name} emin değil")
        if error:
            meta.append(error)
        self.side.heading.set(f"Belge {cell.data(DOC_ROLE)} · {name}", " · ".join(meta))
        if value is None:
            self.side.state.set("none", "Bu değer henüz okunmadı")
            self.side.state.setVisible(True)
            return
        percent = round(value.confidence * 100)
        where = (f"{_section_name(value.section)}, %{percent}" if value.section is not None
                 else f"%{percent}")
        self.side.read_caption.setVisible(True)
        self.side.read.setVisible(True)
        self.side.read.setText(value.value or "(boş)")
        self.side.read.setProperty("role", "bad" if cell.data(FLAG_ROLE) else "mono")
        self.side.read.style().unpolish(self.side.read)
        self.side.read.style().polish(self.side.read)
        self.side.read_note.setText(f"({where})")
        if value.edited:
            self.side.read_caption.setText("Yazılan:")
            self.side.read_note.setText("")
            self.side.state.set("ok", "Elle düzeltildi")
            self.side.state.setVisible(True)
        else:
            self.side.read_caption.setText("Okunan:")
        if value.flagged and value.suggestion:
            source = next((r for r in value.readings if r.text == value.suggestion), None)
            if source is not None:
                self.side.suggestion_caption.setText(
                    f"Öneri, {_section_name(source.section)}'den "
                    f"(%{round(source.confidence * 100)}):")
            else:
                self.side.suggestion_caption.setText("Öneri:")
            self.side.suggestion.setText(value.suggestion)
        elif cell.data(FLAG_ROLE):
            self.side.suggestion_caption.setText(
                "Öneri yok: değeri elle yazın (F2) ya da yeni bir varyant çizin (V).")
        elif not value.edited:
            self.side.state.set("ok", "Emin okundu")
            self.side.state.setVisible(True)
        self.side.suggestion_caption.setWordWrap(True)
        self.side.accept_button.setEnabled(bool(value.flagged and value.suggestion))

    def _item_changed(self, cell: QTableWidgetItem) -> None:
        if self._filling or cell.data(KEY_ROLE) is None:
            return
        controller = self.controller()
        document = controller.documents()[cell.data(DOC_ROLE) - 1]
        controller.set_value(document, cell.data(KEY_ROLE), cell.text())
        self._keep_cell(cell.row(), cell.column())

    def _keep_cell(self, row: int, column: int) -> None:
        self.refresh()
        if row < self.table.rowCount():
            self.table.setCurrentCell(row, column)

    def accept_current(self) -> None:
        current = self._current()
        if current is None:
            return
        row, column = self.table.currentRow(), self.table.currentColumn()
        self.controller().accept_suggestion(*current)
        self._keep_cell(row, column)

    def type_current(self) -> None:
        cell = self.table.currentItem()
        if cell is not None and cell.flags() & Qt.ItemFlag.ItemIsEditable:
            self.table.editItem(cell)

    def _draw_variant(self) -> None:
        cell = self.table.currentItem()
        if cell is None or cell.data(KEY_ROLE) is None:
            return
        name = self.table.horizontalHeaderItem(cell.column()).text()
        self.draw_variant.emit(cell.data(DOC_ROLE), name)

    def next_check(self) -> None:
        for row in range(self.table.currentRow() + 1, self.table.rowCount()):
            if self.table.item(row, self.table.columnCount() - 1).text() == "Kontrol":
                flagged = [c for c in range(3, 3 + len(self._columns))
                           if self.table.item(row, c) is not None
                           and self.table.item(row, c).data(FLAG_ROLE)]
                self.table.setCurrentCell(row, flagged[0] if flagged else 3)
                return

    # Reading values in the background
    def _engine(self):
        if self.engine is not None:
            return self.engine()
        from evrakci.pipeline.ocr.tesseract import default_engine

        return default_engine()

    def read_values(self, only_missing: bool) -> None:
        controller = self.controller()
        if controller is None or self.task is not None:
            return
        engine = self._engine()
        reason = engine.available()
        if reason:  # refuse like the command line does; nothing is touched
            self._show_message(f"Okunamadı: {reason}", "warn", "check_ink")
            return
        job = controller.job
        templates = self.templates()
        files = controller.store.batch_files(job)
        rotations = dict(job.rotations)
        work = []
        for document in controller.documents():
            template_id, _ = document_template(job, document)
            if template_id is None:
                continue
            template = templates.get(template_id)
            if only_missing and template is not None and not needs_reading(job, document,
                                                                           template):
                continue
            work.append((document, template_id, templates.get(template_id)))
        results: list = []  # filled by the worker; kept even when the read is cancelled
        self._results = results

        def run(progress):
            for done, (document, template_id, template) in enumerate(work, start=1):
                progress(done - 1, len(work))
                if template is None:
                    results.append((document, template_id, None,
                                    f"Şablon bulunamadı: {template_id}", ""))
                    continue

                def page_image(index, document=document):
                    pid = document.page_ids[index]
                    batch_id, page = parse_page_id(pid)
                    return render_page(files[batch_id], page, rotations.get(pid, 0))

                try:
                    values = read_document(template, len(document.page_ids), page_image, engine)
                    results.append((document, template_id, values, None,
                                    template_revision(template)))
                except (EngineUnavailable, OSError, pdfium.PdfiumError) as error:
                    results.append((document, template_id, None, str(error), ""))
            progress(len(work), len(work))
            return results

        self.task = Task(run)
        self.task.signals.progress.connect(self._progress)
        self.task.signals.done.connect(self._read_done)
        self.task.signals.failed.connect(self._read_failed)
        self.task.signals.cancelled.connect(self._read_cancelled)
        self._started = time.monotonic()
        self._set_busy(True)
        self._progress(0, len(work))
        start(self.task)

    def read_count(self) -> int:
        return len(getattr(self, "_results", []))

    def _progress(self, done: int, total: int) -> None:
        self.progress.setRange(0, max(1, total))
        self.progress.setValue(done)
        self.progress_label.setText(f"Okunuyor: {done} / {total} belge")
        hint = "elle yazdıklarınız korunur"
        if 0 < done < total:
            left = (time.monotonic() - self._started) / done * (total - done)
            hint = (f"yaklaşık {max(1, round(left / 60))} dk kaldı · {hint}" if left >= 60
                    else f"bir dakikadan az kaldı · {hint}")
        self.progress_hint.setText(hint)

    def _store(self, results) -> int:
        """Store readings on the window thread, as one undoable edit. Returns how many."""
        controller = self.controller()
        job = controller.job
        current = {tuple(d.page_ids): document_template(job, d)[0]
                   for d in controller.documents()}
        stored = []

        def store(job) -> None:
            for document, template_id, values, error, revision in list(results):
                if current.get(tuple(document.page_ids), object()) != template_id:
                    continue  # the cuts or the template changed while reading: stale
                if values is not None:
                    store_reading(job, document, template_id, values, revision)
                else:  # keeps earlier values and the user's corrections
                    record_read_error(job, document, template_id, error)
                stored.append(document)

        controller.run("Değerleri oku", store)
        return len(stored)

    def _read_done(self, results) -> None:
        count = self._store(results)
        self._finish(f"{count} belge okundu.", "ok", "ok")

    def _read_failed(self, message: str) -> None:
        self._finish(f"Okunamadı: {message}", "warn", "check_ink")

    def _read_cancelled(self) -> None:
        count = self._store(self._results)
        self._finish(f"Okuma durduruldu: {count} belge okundu ve kaydedildi, kalanlar okunmadı.",
                     "info", "qr")

    def _finish(self, message: str, icon: str, colour: str) -> None:
        self.task = None
        self._set_busy(False)
        self._show_message(message, icon, colour)
        self.refresh()
        self.finished.emit()

    def _show_message(self, message: str, icon: str, colour: str) -> None:
        """After a read (or a refusal) the band stays with one line until it is closed."""
        self.progress_icon.setPixmap(icons.pixmap(icon, colour, 18))
        self.progress_label.setText(message)
        self.progress_hint.setText("")
        self.progress_band.setVisible(True)

    def _dismiss(self) -> None:
        self.progress_label.setText("")
        self.progress_band.setVisible(False)

    def cancel(self) -> None:
        if self.task is not None:
            self.task.cancel()

    def busy(self) -> bool:
        return self.task is not None

    def _set_busy(self, busy: bool) -> None:
        self.progress.setVisible(busy)
        self.progress_hint.setVisible(True)
        self.cancel_button.setVisible(busy)
        self.dismiss_button.setVisible(not busy)
        self.progress_icon.setVisible(not busy)
        self.progress_band.setVisible(busy or bool(self.progress_label.text()))
        self.read_button.setEnabled(not busy)
        self.missing_button.setEnabled(not busy)
