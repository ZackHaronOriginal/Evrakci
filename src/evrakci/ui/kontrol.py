"""The Kontrol screen: check and fix how the pile was split, with the keyboard."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from PySide6.QtCore import QItemSelectionModel, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QKeySequence, QPainter, QPen, QShortcut
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from evrakci.pipeline.export import plan_export
from evrakci.pipeline.templates.model import Template
from evrakci.ui import theme
from evrakci.ui.controller import JobController
from evrakci.ui.thumbnails import ThumbnailService
from evrakci.ui.timeline import Roles, TimelineModel, TimelineView
from evrakci.ui.widgets import index_rule, key_button

KIND_TEXT = {
    "qr": "QR ayıraç",
    "filter": "Filtre",
    "manual": "Elle kesim",
    "start": "İşin başı",
}


class WholeJobStrip(QWidget):
    """The whole job at true density: one hairline per page, a rider per document to check."""

    jump = Signal(int)  # row

    def __init__(self, model: TimelineModel, parent=None) -> None:
        super().__init__(parent)
        self.model = model
        self.visible = range(0)
        self.check_rows: list[tuple[int, int]] = []  # (row, document number)
        self.setFixedHeight(64)
        self.setToolTip("Tüm iş: her çizgi bir sayfa. Tıklayınca oraya gider.")

    def _x(self, row: float) -> float:
        total = max(1, self.model.rowCount())
        return 16 + (self.width() - 32) * row / total

    def paintEvent(self, event) -> None:
        t = theme.TOKENS
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(t["card"]))
        total = self.model.rowCount()
        base = 54
        painter.setPen(QPen(QColor("#7f8c84"), 1))
        step = max(1, total // max(1, self.width() - 32))
        for row in range(0, total, step):
            x = self._x(row)
            painter.drawLine(QPointF(x, base - 20), QPointF(x, base))
        painter.drawLine(QPointF(16, base), QPointF(self.width() - 16, base))
        for row, number in self.check_rows:
            x = self._x(row)
            painter.setPen(QPen(QColor(t["rider"]), 2))
            painter.drawLine(QPointF(x, base - 28), QPointF(x, base))
            painter.fillRect(QRectF(x - 4, base - 32, 9, 7), QColor(t["rider"]))
            painter.setPen(QColor(t["check_ink"]))
            painter.drawText(QRectF(x - 20, base - 52, 40, 18), Qt.AlignmentFlag.AlignCenter,
                             str(number))
        if self.visible:
            a, b = self._x(self.visible.start), self._x(self.visible.stop)
            painter.setPen(QPen(QColor(t["ink"]), 2))
            painter.setBrush(QColor(63, 90, 76, 46))
            painter.drawRect(QRectF(a, base - 24, max(4, b - a), 28))

    def mousePressEvent(self, event) -> None:
        total = self.model.rowCount()
        if total:
            fraction = (event.position().x() - 16) / max(1, self.width() - 32)
            self.jump.emit(int(min(max(fraction, 0), 0.9999) * total))


class SidePanel(QFrame):
    open_values = Signal(int)  # document number

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedWidth(340)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        self.title = QLabel("Belge seçilmedi")
        self.title.setStyleSheet("font-size: 20px; font-weight: 700;")
        self.meta = QLabel("")
        self.meta.setProperty("role", "muted")
        layout.addWidget(self.title)
        layout.addWidget(self.meta)
        layout.addWidget(index_rule())
        self.notice = QLabel("")
        self.notice.setWordWrap(True)
        self.notice.setStyleSheet(f"color: {theme.colour('check_ink')}; font-weight: 700;")
        self.values_button = key_button("Değerlerde aç", "Ctrl+4", primary=True)
        self.values_button.clicked.connect(lambda: self.open_values.emit(self.document))
        layout.addWidget(self.notice)
        layout.addWidget(self.values_button)
        why = QLabel("Neden burada başlıyor?")
        why.setStyleSheet("font-weight: 700; margin-top: 12px;")
        layout.addWidget(why)
        self.why = QLabel("")
        self.why.setWordWrap(True)
        layout.addWidget(self.why)
        self.merge_button = key_button("Öncekiyle birleştir", "M")
        layout.addWidget(self.merge_button)
        layout.addStretch(1)
        self.document = 0
        self.notice.hide()
        self.values_button.hide()

    def show_document(self, number: int, info: dict) -> None:
        self.document = number
        self.title.setText(f"Belge {number} · {info['template'] or 'Şablon yok'}")
        self.meta.setText(info["meta"])
        checks = info["checks"]
        self.notice.setText("Kontrol: " + "; ".join(checks) if checks else "")
        self.notice.setVisible(bool(checks))
        self.values_button.setVisible(bool(checks))
        self.why.setText(info["why"])


class KontrolScreen(QWidget):
    open_values = Signal(int)

    def __init__(
        self,
        controller: JobController,
        thumbnails: ThumbnailService | None,
        templates: Callable[[], Mapping[str, Template]] = dict,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("page")
        self.controller = controller
        self.templates = templates
        self.model = TimelineModel(controller, templates)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._toolbar())
        self.strip = WholeJobStrip(self.model)
        self.strip.jump.connect(self.go_to_row)
        root.addWidget(self.strip)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        work = QVBoxLayout()
        work.setContentsMargins(24, 12, 24, 0)
        heading = QHBoxLayout()
        self.guide_words = QLabel("")
        self.guide_words.setProperty("role", "heading")
        heading.addWidget(self.guide_words)
        heading.addStretch(1)
        self.prev_check = key_button("Önceki kontrol", "Shift+N")
        self.next_check = key_button("Sonraki kontrol", "N")
        self.prev_check.clicked.connect(lambda: self.jump_to_check(-1))
        self.next_check.clicked.connect(lambda: self.jump_to_check(1))
        heading.addWidget(self.prev_check)
        heading.addWidget(self.next_check)
        work.addLayout(heading)
        work.addWidget(index_rule())
        self.timeline = TimelineView(thumbnails)
        self.timeline.setModel(self.model)
        work.addWidget(self.timeline, 1)
        body.addLayout(work, 1)
        self.side = SidePanel()
        self.side.merge_button.clicked.connect(self.merge_current)
        self.side.open_values.connect(self.open_values)
        body.addWidget(self.side)
        root.addLayout(body, 1)

        self.model.modelAboutToBeReset.connect(self._remember_selection)
        self.model.modelReset.connect(self._restore_selection)
        self._kept: tuple[list[str], str | None] = ([], None)
        self._rotations = dict(controller.job.rotations)
        self.thumbnails = thumbnails
        self.timeline.selectionModel().selectionChanged.connect(self._selection_changed)
        self.timeline.selectionModel().currentChanged.connect(self._current_changed)
        self.timeline.horizontalScrollBar().valueChanged.connect(self._scrolled)
        controller.job_changed.connect(self._job_changed)
        self._shortcuts()
        if self.model.rowCount():  # focus the first page without selecting it
            self.timeline.selectionModel().setCurrentIndex(
                self.model.index(0), QItemSelectionModel.SelectionFlag.NoUpdate)
        self._job_changed()

    # Building
    def _toolbar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("card")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 8, 16, 8)
        self.undo_button = key_button("Geri al", "Ctrl+Z")
        self.redo_button = key_button("Yinele", "Ctrl+Y")
        self.undo_button.clicked.connect(self.controller.undo)
        self.redo_button.clicked.connect(self.controller.redo)
        self.selection_label = QLabel("Seçim yok")
        self.selection_label.setStyleSheet("font-weight: 700;")
        self.every_n = QSpinBox()
        self.every_n.setRange(1, 999)
        self.every_n.setValue(2)
        self.every_n.setToolTip("Seçili sayfalarda her kaç sayfa bir belge olsun")
        self.filter_button = key_button("Filtreyi uygula", "F", primary=True)
        self.filter_button.clicked.connect(self.apply_filter)
        self.cut_button = key_button("Kesim", "K")
        self.cut_button.clicked.connect(self.toggle_cut)
        self.template_box = QComboBox()
        self.template_box.setToolTip("Uygulanacak şablon")
        self.template_button = key_button("Şablon uygula", "T")
        self.template_button.clicked.connect(self.apply_template)
        self.rotate_button = key_button("Döndür", "R")
        self.rotate_button.clicked.connect(self.rotate_selected)
        self.delete_button = key_button("Sil", "Del")
        self.delete_button.clicked.connect(self.toggle_delete)
        for widget in (self.undo_button, self.redo_button, self.selection_label):
            layout.addWidget(widget)
        layout.addSpacing(8)
        layout.addWidget(QLabel("Her"))
        layout.addWidget(self.every_n)
        layout.addWidget(QLabel("sayfada bir belge"))
        for widget in (self.filter_button, self.cut_button, self.template_box,
                       self.template_button, self.rotate_button, self.delete_button):
            layout.addWidget(widget)
        layout.addStretch(1)
        return bar

    def _shortcuts(self) -> None:
        # Ctrl+Z/Y, F, K, T, R, Del, M, N, Shift+N are registry actions (main window).
        bindings: dict = {}
        for key, slot in bindings.items():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(slot)

    # Reading the state
    def selected_ids(self) -> list[str]:
        rows = sorted(i.row() for i in self.timeline.selectionModel().selectedIndexes())
        if not rows and self.timeline.currentIndex().isValid():
            rows = [self.timeline.currentIndex().row()]
        return [self.model.page_id(r) for r in rows]

    def current_document(self) -> int:
        index = self.timeline.currentIndex()
        return index.data(Roles.DOC) if index.isValid() else 0

    # Actions
    def apply_filter(self) -> None:
        ids = [pid for pid in self.selected_ids()
               if not self.controller.job.pages[pid].is_separator]
        if not ids:
            self.controller.status.emit("Önce sayfaları seçin.")
            return
        self.controller.apply_filter(ids, self.every_n.value())

    def apply_template(self) -> None:
        template_id = self.template_box.currentData()
        ids = self.selected_ids()
        if not template_id or not ids:
            self.controller.status.emit("Önce sayfaları ve bir şablonu seçin.")
            return
        self.controller.apply_template(ids, template_id)

    def toggle_cut(self) -> None:
        index = self.timeline.currentIndex()
        if not index.isValid():
            return
        pid = index.data(Roles.PID)
        if pid in self.controller.job.manual_cuts:
            self.controller.remove_cut(pid)
        else:
            self.controller.add_cut(pid)

    def rotate_selected(self) -> None:
        ids = self.selected_ids()
        if ids:  # one undo step for the whole selection
            self.controller.run("Döndür", lambda job: [job.rotate(pid, 90) for pid in ids])

    def toggle_delete(self) -> None:
        ids = self.selected_ids()
        if not ids:
            return

        def toggle(job) -> None:
            for pid in ids:
                if pid in job.deleted:
                    job.undelete_page(pid)
                else:
                    job.delete_page(pid)

        self.controller.run("Sil / geri al", toggle)

    def merge_current(self) -> None:
        number = self.current_document()
        if not number:
            return
        document = self.controller.documents()[number - 1]
        first = document.page_ids[0]
        kind = self.controller.cut_kinds().get(first)
        if kind == "manual":
            self.controller.remove_cut(first)
        elif kind == "qr":
            ordered = self.controller.job.ordered_page_ids()
            before = ordered[: ordered.index(first)]
            separator = next(pid for pid in reversed(before)
                             if self.controller.job.pages[pid].is_separator)
            self.controller.remove_cut(separator)
        elif kind == "filter":
            self.controller.status.emit("Bu kesimi filtre yaptı; filtreyi değiştirin.")
        else:
            self.controller.status.emit("İlk belgenin öncesi yok.")

    def go_to_row(self, row: int) -> None:
        index = self.model.index(row)
        self.timeline.setCurrentIndex(index)
        self.timeline.scrollTo(index, TimelineView.ScrollHint.PositionAtCenter)

    def jump_to_check(self, direction: int) -> None:
        rows = [row for row, _ in self.strip.check_rows]
        if not rows:
            self.controller.status.emit("Kontrol bekleyen belge yok.")
            return
        here = self.timeline.currentIndex().row() if self.timeline.currentIndex().isValid() else -1
        if direction > 0:
            target = next((r for r in rows if r > here), rows[0])
        else:
            target = next((r for r in reversed(rows) if r < here), rows[-1])
        self.go_to_row(target)

    # Refreshing
    def _remember_selection(self) -> None:
        rows = sorted(i.row() for i in self.timeline.selectionModel().selectedIndexes())
        current = self.timeline.currentIndex()
        self._kept = ([self.model.page_id(r) for r in rows],
                      self.model.page_id(current.row()) if current.isValid() else None)

    def _restore_selection(self) -> None:
        selected, current = self._kept
        selection = self.timeline.selectionModel()
        flags = QItemSelectionModel.SelectionFlag.Select
        for pid in selected:
            try:
                selection.select(self.model.index(self.model.row_of(pid)), flags)
            except ValueError:
                continue  # the page is gone (its batch was removed)
        if current is not None:
            try:
                selection.setCurrentIndex(self.model.index(self.model.row_of(current)),
                                          QItemSelectionModel.SelectionFlag.NoUpdate)
            except ValueError:
                pass

    def _refresh_thumbnails(self) -> None:
        rotations = self.controller.job.rotations
        changed = {pid for pid in set(rotations) | set(self._rotations)
                   if rotations.get(pid) != self._rotations.get(pid)}
        self._rotations = dict(rotations)
        if self.thumbnails is not None:
            for pid in changed:
                self.thumbnails.invalidate(pid)

    def _job_changed(self) -> None:
        self._refresh_thumbnails()
        items = plan_export(self.controller.job, self.templates())
        checks = {item.number: item.checks for item in items}
        self.model.set_checks(checks)
        self.strip.check_rows = [
            (self.model.row_of(item.document.page_ids[0]), item.number)
            for item in items if item.checks
        ]
        current = self.template_box.currentData()
        self.template_box.clear()
        for template_id, template in sorted(self.templates().items(), key=lambda kv: kv[1].name):
            self.template_box.addItem(template.name, template_id)
        if current:
            self.template_box.setCurrentIndex(max(0, self.template_box.findData(current)))
        self.undo_button.setEnabled(self.controller.undo_stack.canUndo())
        self.redo_button.setEnabled(self.controller.undo_stack.canRedo())
        self._scrolled()
        self._current_changed(self.timeline.currentIndex())

    def _scrolled(self) -> None:
        rows = self.timeline.visible_rows()
        self.strip.visible = rows
        self.strip.update()
        numbers = sorted({self.model.data(self.model.index(r), Roles.DOC) for r in rows} - {0})
        if numbers:
            self.guide_words.setText(f"Belge {numbers[0]} — Belge {numbers[-1]}")
        else:
            self.guide_words.setText("")

    def _selection_changed(self) -> None:
        ids = self.selected_ids()
        if not ids:
            self.selection_label.setText("Seçim yok")
            return
        first = self.controller.job.position_of(ids[0])
        last = self.controller.job.position_of(ids[-1])
        span = f"Sayfa {first}" if first == last else f"Sayfa {first}–{last}"
        self.selection_label.setText(f"{span} seçili · {len(ids)} sayfa")

    def _current_changed(self, index) -> None:
        number = index.data(Roles.DOC) if index.isValid() else 0
        if not number:
            return
        documents = self.controller.documents()
        if number > len(documents):
            return
        document = documents[number - 1]
        kinds = self.controller.cut_kinds()
        job = self.controller.job
        first, last = job.position_of(document.page_ids[0]), job.position_of(document.page_ids[-1])
        dropped = sum(
            1 for pid in job.ordered_page_ids()[first - 1:last]
            if pid not in document.page_ids and not job.pages[pid].is_separator
        )
        why = f"Önceki kesim: {KIND_TEXT[kinds.get(document.page_ids[0], 'start')]}"
        if dropped:
            why += f"\nAtlanan sayfa: {dropped}"
        self.side.show_document(number, {
            "template": self.model.data(self.model.index(self.model.row_of(document.page_ids[0])),
                                        Roles.TEMPLATE),
            "meta": f"Sayfa {first}–{last} · {len(document.page_ids)} sayfa",
            "checks": self.model.checks.get(number, []),
            "why": why,
        })
