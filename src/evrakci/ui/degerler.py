"""The Değerler screen: every read value in one table; unsure ones are marked and fixed here."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QStyle,
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
from evrakci.pipeline.review import store_reading
from evrakci.pipeline.templates.model import Template
from evrakci.pipeline.templates.read import read_document
from evrakci.ui import theme
from evrakci.ui.controller import JobController
from evrakci.ui.kontrol import index_rule, key_button
from evrakci.ui.workers import Task, start

DOC_ROLE = Qt.ItemDataRole.UserRole + 1
KEY_ROLE = Qt.ItemDataRole.UserRole + 2


class ValueSide(QFrame):
    """The selected value: what was read, the suggestion, and what to do."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedWidth(380)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        self.title = QLabel("Bir değer seçin")
        self.title.setStyleSheet("font-size: 20px; font-weight: 700;")
        self.meta = QLabel("")
        self.meta.setProperty("role", "muted")
        self.meta.setWordWrap(True)
        layout.addWidget(self.title)
        layout.addWidget(self.meta)
        layout.addWidget(index_rule())
        self.read = QLabel("")
        self.read.setWordWrap(True)
        self.suggestion = QLabel("")
        self.suggestion.setStyleSheet("font-size: 26px; font-weight: 700;")
        layout.addWidget(self.read)
        layout.addWidget(self.suggestion)
        self.accept_button = key_button("Öneriyi kabul et", "Enter", primary=True)
        self.type_button = key_button("Elle yaz", "F2")
        self.variant_button = key_button("Yeni varyant çiz", "V")
        for button in (self.accept_button, self.type_button, self.variant_button):
            layout.addWidget(button)
        layout.addStretch(1)


class DegerlerScreen(QWidget):
    draw_variant = Signal(int, str)  # document number, variable name
    status = Signal(str)

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

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        bar = QFrame()
        bar.setObjectName("card")
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(16, 8, 16, 8)
        self.only_checks = QCheckBox("Yalnızca kontrol gerekenler")
        self.only_checks.setChecked(True)
        self.only_checks.toggled.connect(self.refresh)
        self.template_filter = QComboBox()
        self.template_filter.currentIndexChanged.connect(self.refresh)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Ara: firma, sicil no…")
        self.search.textChanged.connect(self.refresh)
        self.missing_button = key_button("Yalnızca eksikleri oku", "")
        self.missing_button.clicked.connect(lambda: self.read_values(only_missing=True))
        self.read_button = key_button("Değerleri oku", "")
        self.read_button.clicked.connect(lambda: self.read_values(only_missing=False))
        for widget in (self.only_checks, self.template_filter, self.search):
            bar_layout.addWidget(widget)
        bar_layout.addStretch(1)
        bar_layout.addWidget(self.missing_button)
        bar_layout.addWidget(self.read_button)
        root.addWidget(bar)

        progress_row = QHBoxLayout()
        progress_row.setContentsMargins(16, 6, 16, 6)
        self.progress_label = QLabel("")
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.cancel_button = key_button("İptal", "Esc")
        self.cancel_button.clicked.connect(self.cancel)
        progress_row.addWidget(self.progress_label)
        progress_row.addWidget(self.progress, 1)
        progress_row.addWidget(self.cancel_button)
        root.addLayout(progress_row)

        body = QHBoxLayout()
        work = QVBoxLayout()
        work.setContentsMargins(24, 8, 24, 8)
        self.heading = QLabel("")
        self.heading.setProperty("role", "heading")
        work.addWidget(self.heading)
        work.addWidget(index_rule())
        self.table = QTableWidget()
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked
                                   | QAbstractItemView.EditTrigger.EditKeyPressed)
        self.table.setSortingEnabled(False)
        self.table.itemChanged.connect(self._item_changed)
        self.table.currentCellChanged.connect(self._cell_selected)
        work.addWidget(self.table, 1)
        self.note = QLabel("")
        self.note.setProperty("role", "muted")
        work.addWidget(self.note)
        body.addLayout(work, 1)
        self.side = ValueSide()
        self.side.accept_button.clicked.connect(self.accept_current)
        self.side.type_button.clicked.connect(self.type_current)
        self.side.variant_button.clicked.connect(self._draw_variant)
        body.addWidget(self.side)
        root.addLayout(body, 1)

        keys = {"Return": self.accept_current, "F2": self.type_current,
                "V": self._draw_variant, "N": self.next_check, "Esc": self.cancel}
        for key, slot in keys.items():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(slot)
        self._set_busy(False)

    # Table
    def column_of(self, variable_name: str) -> int:
        return 3 + self._columns.index(variable_name)

    def refresh(self) -> None:
        controller = self.controller()
        self._filling = True
        self.table.clear()
        self.table.setRowCount(0)
        if controller is None:
            self._filling = False
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
        warn = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning)
        for row, (item, template) in enumerate(shown):
            self._fill_row(row, item, template, warn)
        hidden = len(rows) - len(shown)
        self.note.setText(f"Filtre açık: {hidden} belge gizli." if hidden else "")
        numbers = [item.number for item, _ in shown]
        self.heading.setText(
            f"Belge {numbers[0]} — Belge {numbers[-1]} · {checks} kontrol" if numbers else
            "Gösterilecek belge yok"
        )
        self.table.resizeColumnsToContents()
        self._filling = False

    def _fill_row(self, row: int, item, template: Template | None, warn) -> None:
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
                cell.setBackground(QColor(theme.colour("check_wash")))
                cell.setIcon(warn)
                cell.setToolTip("Emin değil" + (f"; öneri: {value.suggestion}"
                                                if value.suggestion else ""))
                if not text:
                    cell.setText("")
            if value is not None and value.edited:
                cell.setToolTip("Elle düzeltildi")
            self.table.setItem(row, column, cell)
        status = QTableWidgetItem("Kontrol" if item.checks else "Tamam")
        status.setFlags(status.flags() & ~Qt.ItemFlag.ItemIsEditable)
        status.setData(DOC_ROLE, item.number)
        if item.checks:
            status.setIcon(warn)
            status.setToolTip("; ".join(item.checks))
        self.table.setItem(row, len(self._columns) + 3, status)

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

    def _cell_selected(self, row: int, column: int, *_args) -> None:
        cell = self.table.item(row, column)
        current = self._current()
        if cell is None or current is None:
            return
        document, key = current
        value = (current_values(self.controller().job, document) or {}).get(key)
        name = self.table.horizontalHeaderItem(column).text()
        self.side.title.setText(f"Belge {cell.data(DOC_ROLE)} · {name}")
        if value is None:
            return
        percent = round(value.confidence * 100)
        self.side.read.setText(f"Okunan: {value.value or '(boş)'} · güven %{percent}")
        self.side.suggestion.setText(value.suggestion if value.flagged else "")
        self.side.accept_button.setEnabled(bool(value.flagged and value.suggestion))
        error = current_read_error(self.controller().job, document)
        self.side.meta.setText(error or "")

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
                self.table.setCurrentCell(row, 3)
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
        job = controller.job
        templates = self.templates()
        files = controller.store.batch_files(job)
        rotations = dict(job.rotations)
        work = []
        for document in controller.documents():
            template_id, _ = document_template(job, document)
            if template_id is None:
                continue
            if only_missing and current_values(job, document) is not None:
                continue
            work.append((document, template_id, templates.get(template_id)))

        def run(progress):
            engine = self._engine()
            reason = engine.available()
            results = []
            for done, (document, template_id, template) in enumerate(work, start=1):
                progress(done - 1, len(work))
                if reason:
                    results.append((document, template_id, None, reason))
                    continue
                if template is None:
                    results.append((document, template_id, None,
                                    f"Şablon bulunamadı: {template_id}"))
                    continue

                def page_image(index, document=document):
                    pid = document.page_ids[index]
                    batch_id, page = parse_page_id(pid)
                    return render_page(files[batch_id], page, rotations.get(pid, 0))

                try:
                    values = read_document(template, len(document.page_ids), page_image, engine)
                    results.append((document, template_id, values, None))
                except (EngineUnavailable, OSError) as error:
                    results.append((document, template_id, None, str(error)))
            progress(len(work), len(work))
            return results

        self.task = Task(run)
        self.task.signals.progress.connect(self._progress)
        self.task.signals.done.connect(self._read_done)
        self.task.signals.failed.connect(self._read_failed)
        self.task.signals.cancelled.connect(self._read_cancelled)
        self.progress_label.setText(f"Okunuyor: 0 / {len(work)} belge · elle yazdıklarınız korunur")
        self._set_busy(True)
        start(self.task)

    def _progress(self, done: int, total: int) -> None:
        self.progress.setRange(0, max(1, total))
        self.progress.setValue(done)
        self.progress_label.setText(
            f"Okunuyor: {done} / {total} belge · elle yazdıklarınız korunur")

    def _read_done(self, results) -> None:
        controller = self.controller()
        current = {tuple(d.page_ids) for d in controller.documents()}

        def store(job) -> None:
            for document, template_id, values, error in results:
                if tuple(document.page_ids) not in current:
                    continue  # the cuts changed while reading; this reading is stale
                if values is None:
                    record_read_error(job, document, template_id, error)
                else:
                    store_reading(job, document, template_id, values)

        controller.run("Değerleri oku", store)
        self._finish(f"{len(results)} belge okundu.")

    def _read_failed(self, message: str) -> None:
        self._finish(f"Okunamadı: {message}")

    def _read_cancelled(self) -> None:
        self._finish("Okuma iptal edildi; okunanlar kaydedilmedi.")

    def _finish(self, message: str) -> None:
        self.task = None
        self._set_busy(False)
        self.progress_label.setText(message)
        self.refresh()

    def cancel(self) -> None:
        if self.task is not None:
            self.task.cancel()

    def busy(self) -> bool:
        return self.task is not None

    def _set_busy(self, busy: bool) -> None:
        self.progress.setVisible(busy)
        self.cancel_button.setVisible(busy)
        self.read_button.setEnabled(not busy)
        self.missing_button.setEnabled(not busy)
