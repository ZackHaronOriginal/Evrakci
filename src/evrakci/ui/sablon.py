"""The Şablonlar screen: name variables, draw where they are, add variants from other examples."""

from __future__ import annotations

from collections.abc import Callable

from PIL import Image
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QKeySequence,
    QPen,
    QPixmap,
    QShortcut,
    QUndoCommand,
    QUndoStack,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from evrakci.pipeline.job import parse_page_id
from evrakci.pipeline.ocr.engine import EngineUnavailable
from evrakci.pipeline.render import render_page
from evrakci.pipeline.templates.model import (
    Section,
    Template,
    TemplateError,
    template_from_dict,
    template_to_dict,
)
from evrakci.pipeline.templates.read import read_document
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.ui import theme
from evrakci.ui.controller import JobController
from evrakci.ui.thumbnails import to_qimage
from evrakci.ui.widgets import index_rule, key_button
from evrakci.ui.workers import Task, start

CANVAS_DPI = 100
READ_DPI = 300
MM = 25.4


def pixels_to_mm(rect: QRectF, dpi: int) -> tuple[float, float, float, float]:
    """A box drawn on the page as displayed, in millimetres from its top-left corner."""
    r = rect.normalized()
    return tuple(round(v / dpi * MM, 2) for v in (r.left(), r.top(), r.right(), r.bottom()))


class PageCanvas(QGraphicsView):
    """An example page with the template's boxes; drag to draw a new box."""

    box_drawn = Signal(tuple)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.setBackgroundBrush(QColor("#dfe5e1"))
        self.setRenderHint(self.renderHints().Antialiasing)
        self.dpi = CANVAS_DPI
        self.drawing = False
        self.show_grid = True
        self._start: QPointF | None = None
        self._rubber = None
        self._size = (0, 0)
        self._boxes: list[tuple[tuple[float, float, float, float], str, str, bool]] = []
        self.setToolTip("Kutu çizmek için sürükleyin (B). Izgara 1 mm adımla oturur (G).")

    def set_page(self, image: Image.Image | None, dpi: int = CANVAS_DPI) -> None:
        self.dpi = dpi
        self._size = image.size if image is not None else (0, 0)
        self._image = image
        self._redraw()
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def set_boxes(self, boxes) -> None:
        """(box_mm, label, colour, dashed) for each section to show."""
        self._boxes = list(boxes)
        self._redraw()

    def _px(self, mm: float) -> float:
        return mm / MM * self.dpi

    def _redraw(self) -> None:
        scene = self.scene()
        scene.clear()
        self._rubber = None
        width, height = self._size
        if not width:
            return
        scene.setSceneRect(QRectF(-20, -20, width + 40, height + 40))
        scene.addPixmap(QPixmap.fromImage(to_qimage(self._image)))
        if self.show_grid:  # 5 mm lines, stronger every 10 mm
            for step in range(0, int(max(width, height) / self._px(5)) + 1):
                strong = step % 2 == 0
                pen = QPen(QColor(31, 95, 191, 46 if strong else 22), 0)
                v = self._px(5 * step)
                if v <= width:
                    scene.addLine(v, 0, v, height, pen)
                if v <= height:
                    scene.addLine(0, v, width, v, pen)
        scene.addRect(QRectF(0, 0, width, height), QPen(QColor("#74817a"), 1))
        for box, label, colour, dashed in self._boxes:
            x0, y0, x1, y1 = (self._px(v) for v in box)
            pen = QPen(QColor(colour), 2.5)
            if dashed:
                pen.setStyle(Qt.PenStyle.DashLine)
            scene.addRect(QRectF(x0, y0, x1 - x0, y1 - y0), pen)
            font = QFont(theme.FONT_FAMILY)
            font.setPixelSize(20)  # scene pixels; about 13 px on screen at the usual zoom
            font.setBold(True)
            text = scene.addText(label, font)
            text.setDefaultTextColor(QColor(colour))
            text.setPos(x0, max(0, y0 - 30))

    def _snap(self, point: QPointF) -> QPointF:
        step = self._px(1)  # 1 mm
        return QPointF(round(point.x() / step) * step, round(point.y() / step) * step)

    def mousePressEvent(self, event) -> None:
        if self.drawing and event.button() == Qt.MouseButton.LeftButton and self._size[0]:
            self._start = self.mapToScene(event.position().toPoint())
            self._rubber = self.scene().addRect(
                QRectF(self._start, self._start), QPen(QColor(theme.colour("focus")), 2,
                                                       Qt.PenStyle.DashLine))
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._start is not None and self._rubber is not None:
            self._rubber.setRect(QRectF(self._start, self.mapToScene(event.position().toPoint())))
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._start is not None:
            end = self.mapToScene(event.position().toPoint())
            rect = QRectF(self._start, end).normalized()
            self._start = None
            width, height = self._size
            rect = rect.intersected(QRectF(0, 0, width, height))
            if rect.width() >= self._px(2) and rect.height() >= self._px(2):
                self.box_drawn.emit(pixels_to_mm(rect, self.dpi))
            if self._rubber is not None:
                self.scene().removeItem(self._rubber)
                self._rubber = None
            return
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._size[0]:
            self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)


class _TemplateEdit(QUndoCommand):
    def __init__(self, screen: SablonScreen, text: str, before: dict, after: dict) -> None:
        super().__init__(text)
        self.screen, self.before, self.after, self.first = screen, before, after, True

    def redo(self) -> None:
        if self.first:
            self.first = False
            return
        self.screen._restore(self.after)

    def undo(self) -> None:
        self.screen._restore(self.before)


class SablonScreen(QWidget):
    def __init__(
        self,
        store: TemplateStore,
        controller: Callable[[], JobController | None],
        engine: Callable[[], object] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("page")
        self.store = store
        self.controller = controller
        self.engine = engine
        self.template: Template | None = None
        self.variable_name: str | None = None
        self.example = 0  # document number in the open job
        self.undo_stack = QUndoStack(self)
        self._read_task: Task | None = None
        self._reread = False

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._left())
        root.addLayout(self._centre(), 1)
        root.addWidget(self._right())
        self.message = QLabel("")
        self.message.setStyleSheet(f"color: {theme.colour('check_ink')}; font-weight: 600;")
        self._centre_layout.addWidget(self.message)
        for key, slot in {"B": self.toggle_draw, "G": self.toggle_grid, "Ctrl+S": self.save,
                          "Ctrl+Z": self.undo_stack.undo, "Ctrl+Y": self.undo_stack.redo,
                          "Ctrl+T": self.read_all_examples}.items():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(slot)
        self.refresh_templates()

    # Layout
    def _left(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("card")
        panel.setFixedWidth(300)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 14, 16, 14)
        head = QHBoxLayout()
        title = QLabel("Şablonlar")
        title.setStyleSheet("font-size: 20px; font-weight: 700;")
        head.addWidget(title)
        head.addStretch(1)
        new = key_button("Yeni", "")
        new.clicked.connect(self.new_template)
        head.addWidget(new)
        layout.addLayout(head)
        layout.addWidget(index_rule())
        self.templates = QListWidget()
        self.templates.setMaximumHeight(130)
        self.templates.currentItemChanged.connect(
            lambda item, _old: item and self.open_template(item.data(Qt.ItemDataRole.UserRole)))
        layout.addWidget(self.templates)
        head = QHBoxLayout()
        title = QLabel("Değişkenler")
        title.setStyleSheet("font-size: 17px; font-weight: 700;")
        head.addWidget(title)
        head.addStretch(1)
        add = key_button("Ekle", "")
        add.clicked.connect(self.ask_variable)
        head.addWidget(add)
        layout.addLayout(head)
        self.variables = QTreeWidget()
        self.variables.setHeaderHidden(True)
        self.variables.currentItemChanged.connect(self._tree_selected)
        layout.addWidget(self.variables, 1)
        self.required = QCheckBox("Zorunlu")
        self.required.toggled.connect(self._required_toggled)
        layout.addWidget(self.required)
        moves = QHBoxLayout()
        self.section_up_button = key_button("Yukarı", "Alt+↑")
        self.section_up_button.clicked.connect(lambda: self.move_selected_section(-1))
        self.section_down_button = key_button("Aşağı", "Alt+↓")
        self.section_down_button.clicked.connect(lambda: self.move_selected_section(1))
        moves.addWidget(self.section_up_button)
        moves.addWidget(self.section_down_button)
        layout.addLayout(moves)
        hint = QLabel("Bölümler yukarıdan aşağı denenir; ilk emin okuma kazanır.")
        hint.setWordWrap(True)
        hint.setProperty("role", "muted")
        layout.addWidget(hint)
        return panel

    def _centre(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 10, 16, 10)
        bar = QHBoxLayout()
        self.draw_button = key_button("Kutu çiz", "B", primary=True)
        self.draw_button.setCheckable(True)
        self.draw_button.toggled.connect(self._set_drawing)
        self.examples = QComboBox()
        self.examples.setToolTip("Kutuların çizildiği örnek belge")
        self.examples.currentIndexChanged.connect(
            lambda i: self.set_example(self.examples.itemData(i) or 0))
        self.grid = QCheckBox("Mm ızgarası   G")
        self.grid.setChecked(True)
        self.grid.toggled.connect(self._grid_toggled)
        bar.addWidget(self.draw_button)
        bar.addWidget(QLabel("Örnek:"))
        bar.addWidget(self.examples, 1)
        bar.addWidget(self.grid)
        layout.addLayout(bar)
        self.canvas = PageCanvas()
        self.canvas.box_drawn.connect(self.add_box)
        layout.addWidget(self.canvas, 1)
        pattern_row = QHBoxLayout()
        pattern_row.addWidget(QLabel("Dosya adı:"))
        self.pattern = QLineEdit()
        self.pattern.setPlaceholderText("{Değişken}_{Değişken}")
        self.pattern.editingFinished.connect(self._pattern_changed)
        pattern_row.addWidget(self.pattern, 1)
        pattern_row.addWidget(QLabel(".pdf"))
        layout.addLayout(pattern_row)
        self._centre_layout = layout
        return layout

    def _right(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("card")
        panel.setFixedWidth(340)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 14, 20, 14)
        title = QLabel("Bu kutular ne okuyor?")
        title.setStyleSheet("font-size: 20px; font-weight: 700;")
        layout.addWidget(title)
        sub = QLabel("Seçili örnek üzerinde, kaydetmeden önce.")
        sub.setProperty("role", "muted")
        layout.addWidget(sub)
        layout.addWidget(index_rule())
        self.reads = QListWidget()
        layout.addWidget(self.reads, 1)
        try_all = key_button("Bütün örneklerde dene", "Ctrl+T")
        try_all.clicked.connect(self.read_all_examples)
        save = key_button("Şablonu kaydet", "Ctrl+S", primary=True)
        save.clicked.connect(self.save)
        layout.addWidget(try_all)
        layout.addWidget(save)
        return panel

    # Templates and variables
    def refresh_templates(self) -> None:
        self.templates.blockSignals(True)
        self.templates.clear()
        for template in sorted(self.store.list(), key=lambda t: t.name):
            item = QListWidgetItem(f"{template.name}   ·   {len(template.variables)} değişken")
            item.setData(Qt.ItemDataRole.UserRole, template.id)
            self.templates.addItem(item)
            if self.template is not None and template.id == self.template.id:
                self.templates.setCurrentItem(item)
        self.templates.blockSignals(False)
        self._refresh_examples()
        if self.template is None and self.templates.count():
            self.templates.setCurrentRow(0)

    def new_template(self) -> None:
        name, ok = QInputDialog.getText(self, "Yeni şablon", "Şablonun adı:")
        if ok and name.strip():
            template = self.store.create(name.strip())
            self.refresh_templates()
            self.open_template(template.id)

    def open_template(self, template_id: str) -> None:
        self.template = self.store.load(template_id)
        self.undo_stack.clear()
        self.variable_name = None
        self.pattern.setText(self.template.filename_pattern)
        self._show_variables()
        self._show_boxes()
        self.read_example()

    def ask_variable(self) -> None:
        name, ok = QInputDialog.getText(self, "Değişken ekle",
                                        "Değişkenin adı (örn. Firma_Adi):")
        if ok and name.strip():
            self._edit("Değişken ekle", lambda t: t.add_variable(name.strip()))
            self.select_variable(name.strip())

    def select_variable(self, name: str) -> None:
        for i in range(self.variables.topLevelItemCount()):
            item = self.variables.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == name:
                self.variables.setCurrentItem(item)
                return

    def select_section(self, name: str, index: int) -> None:
        for i in range(self.variables.topLevelItemCount()):
            item = self.variables.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == name and index < item.childCount():
                self.variables.setCurrentItem(item.child(index))
                return

    def _tree_selected(self, item, _old=None) -> None:
        if item is None:
            return
        parent = item.parent() or item
        self.variable_name = parent.data(0, Qt.ItemDataRole.UserRole)
        self.required.blockSignals(True)
        self.required.setChecked(self.template.variable(self.variable_name).required)
        self.required.blockSignals(False)

    def _show_variables(self) -> None:
        current = self.variable_name
        self.variables.clear()
        for number, variable in enumerate(self.template.variables):
            colour = theme.variable_colour(number)
            label = variable.name + ("   · zorunlu" if variable.required else "")
            item = QTreeWidgetItem([label])
            item.setData(0, Qt.ItemDataRole.UserRole, variable.name)
            item.setForeground(0, QColor(colour))
            for index, section in enumerate(variable.sections):
                kind = "Bölüm 1" if index == 0 else f"Varyant {index + 1}"
                child = QTreeWidgetItem([f"{kind} · {section.example or 'örnek'}"])
                child.setData(0, Qt.ItemDataRole.UserRole, index)
                item.addChild(child)
            self.variables.addTopLevelItem(item)
            item.setExpanded(True)
        if current:
            self.select_variable(current)

    def _required_toggled(self, value: bool) -> None:
        if self.variable_name:
            name = self.variable_name
            self._edit("Zorunlu", lambda t: t.set_required(name, value))

    def move_selected_section(self, step: int) -> None:
        item = self.variables.currentItem()
        if item is None or item.parent() is None:
            self.message.setText("Önce bir bölüm seçin.")
            return
        name = item.parent().data(0, Qt.ItemDataRole.UserRole)
        index = item.data(0, Qt.ItemDataRole.UserRole)
        if self._edit("Sırayı değiştir", lambda t: t.move_section(name, index, index + step)):
            self.select_section(name, index + step)

    def _pattern_changed(self) -> None:
        if self.template is None:
            return
        text = self.pattern.text()
        if text != self.template.filename_pattern:
            if not self._edit("Dosya adı", lambda t: t.set_pattern(text)):
                self.pattern.setText(self.template.filename_pattern)

    # Examples and boxes
    def _refresh_examples(self) -> None:
        controller = self.controller()
        self.examples.blockSignals(True)
        self.examples.clear()
        if controller is not None:
            job = controller.job
            for number, document in enumerate(controller.documents(), start=1):
                page = job.position_of(document.page_ids[0])
                self.examples.addItem(f"Belge {number} · sayfa {page}", number)
        self.examples.blockSignals(False)
        if self.examples.count() and not self.example:
            self.set_example(1)

    def set_example(self, number: int) -> None:
        controller = self.controller()
        if controller is None or not number:
            self.canvas.set_page(None)
            return
        self.example = number
        index = self.examples.findData(number)
        if index >= 0 and self.examples.currentIndex() != index:
            self.examples.blockSignals(True)
            self.examples.setCurrentIndex(index)
            self.examples.blockSignals(False)
        self.canvas.set_page(self._render(1, CANVAS_DPI), CANVAS_DPI)
        self._show_boxes()
        self.read_example()

    def _example_name(self) -> str:
        controller = self.controller()
        document = controller.documents()[self.example - 1]
        page = controller.job.position_of(document.page_ids[0])
        return f"{controller.job.name} · Belge {self.example} · s.{page}"

    def _document(self):
        return self.controller().documents()[self.example - 1]

    def _render(self, page: int, dpi: int) -> Image.Image:
        controller = self.controller()
        pid = self._document().page_ids[page - 1]
        batch_id, index = parse_page_id(pid)
        path = controller.store.batch_files(controller.job)[batch_id]
        return render_page(path, index, controller.job.rotations.get(pid, 0), dpi=dpi)

    def add_box(self, box_mm) -> None:
        if self.template is None or not self.variable_name:
            self.message.setText("Önce bir değişken seçin.")
            return
        if not self.example:
            self.message.setText("Önce bir örnek belge açın.")
            return
        name = self.variable_name
        section = Section(1, tuple(float(v) for v in box_mm), self._example_name())
        self._edit("Kutu ekle", lambda t: t.add_section(name, section))
        self.read_example()

    def _show_boxes(self) -> None:
        if self.template is None:
            self.canvas.set_boxes([])
            return
        current = self._example_name() if self.example and self.controller() else None
        boxes = []
        for number, variable in enumerate(self.template.variables):
            for index, section in enumerate(variable.sections):
                kind = "" if index == 0 else f" · Varyant {index + 1}"
                faint = section.example != current
                boxes.append((section.box_mm, variable.name + kind,
                              theme.variable_colour(number), index > 0 or faint))
        self.canvas.set_boxes(boxes)

    def toggle_draw(self) -> None:
        self.draw_button.toggle()

    def _set_drawing(self, value: bool) -> None:
        self.canvas.drawing = value
        self.canvas.setCursor(Qt.CursorShape.CrossCursor if value else Qt.CursorShape.ArrowCursor)

    def toggle_grid(self) -> None:
        self.grid.toggle()

    def _grid_toggled(self, value: bool) -> None:
        self.canvas.show_grid = value
        self.canvas._redraw()

    # Live reading
    def _engine(self):
        if self.engine is not None:
            return self.engine()
        from evrakci.pipeline.ocr.tesseract import default_engine

        return default_engine()

    def read_example(self) -> None:
        if self.template is None or not self.example or self.controller() is None:
            return
        if self._read_task is not None:
            self._reread = True
            return
        template = template_from_dict(template_to_dict(self.template))
        # Everything the worker needs is copied here, on the window thread.
        controller = self.controller()
        document = self._document()
        files = controller.store.batch_files(controller.job)
        rotations = dict(controller.job.rotations)
        engine = self._engine()

        def page_image(index: int):
            pid = document.page_ids[index]
            batch_id, page = parse_page_id(pid)
            return render_page(files[batch_id], page, rotations.get(pid, 0), dpi=READ_DPI)

        def work(_progress):
            reason = engine.available()
            if reason:
                raise EngineUnavailable(reason)
            return read_document(template, len(document.page_ids), page_image, engine)

        self._read_template = template
        self._read_task = Task(work)
        self._read_task.signals.done.connect(self._show_reads)
        self._read_task.signals.failed.connect(self._read_failed)
        start(self._read_task)

    def _read_finished(self) -> None:
        self._read_task = None
        if self._reread:
            self._reread = False
            self.read_example()

    def _read_failed(self, message: str) -> None:
        self.reads.clear()
        self.reads.addItem(f"Okunamadı: {message}")
        self._read_finished()

    def _show_reads(self, values) -> None:
        template = self._read_template
        self.reads.clear()
        for variable in template.variables:
            value = values.get(variable.key)
            if value is None:
                continue
            if value.flagged:
                text = f"Kontrol · {variable.name}: emin değil"
                if value.suggestion:
                    text += f" (öneri {value.suggestion})"
            else:
                section = "Bölüm 1" if not value.section else f"Varyant {value.section + 1}"
                percent = round(value.confidence * 100)
                text = f"{variable.name} · {section}: {value.value}   %{percent}"
            self.reads.addItem(text)
        self._read_finished()

    def reads_text(self) -> str:
        return "\n".join(self.reads.item(i).text() for i in range(self.reads.count()))

    def read_all_examples(self) -> None:
        self.message.setText("Her örnek için okunanlar bu panelde sırayla gösterilir.")
        self.read_example()

    # Edits: saved at once, undoable
    def _edit(self, text: str, change) -> bool:
        before = template_to_dict(self.template)
        try:
            change(self.template)
        except TemplateError as error:
            self._restore(before, refresh=False)
            self.message.setText(str(error))
            return False
        after = template_to_dict(self.template)
        if after != before:
            self.undo_stack.push(_TemplateEdit(self, text, before, after))
            self._saved()
        self.message.setText("")
        return True

    def _restore(self, data: dict, refresh: bool = True) -> None:
        self.template = template_from_dict(data)
        if refresh:
            self._saved()

    def _saved(self) -> None:
        self.store.save(self.template)
        self.pattern.setText(self.template.filename_pattern)
        self._show_variables()
        self._show_boxes()

    def save(self) -> None:
        if self.template is not None:
            self.store.save(self.template)
            self.message.setText("Şablon kaydedildi.")
