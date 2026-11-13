"""The Şablonlar screen: name variables, draw where they are, add variants from other examples.

Layout (final-a/sablonlar.html): templates and variables as cards on the left, the example page
in a well with millimetre rulers in the middle, the selected box's inspector on the right. A
QSplitter ("sablonlar") the window remembers holds the three. The zoomable, pannable page is
`sablon_canvas.PageCanvas`; the left column `sablon_nav`, the inspector `sablon_inspector`.

Once the screen sits in a MainWindow (`attach`) it hooks its registry actions, fills the status
bar slot (example, cursor or box position, save state, reads that need a check), registers its
zoom and uses toasts. Edits are saved at once and undoable (the same box edited again in a row is
one undo step). Reading is live: the whole example is read with the template as it is, a moment
after each change, and the box's reading with its confidence is shown in the inspector.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from PIL import Image
from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QIcon, QUndoStack
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMenu,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from evrakci.pipeline.job import parse_page_id
from evrakci.pipeline.render import render_page
from evrakci.pipeline.templates.model import (
    Section,
    Template,
    TemplateError,
    template_from_dict,
    template_revision,
    template_to_dict,
)
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.ui import sablon_read as reading
from evrakci.ui import theme
from evrakci.ui.chrome import make_icon
from evrakci.ui.controller import JobController
from evrakci.ui.sablon_canvas import CANVAS_DPI, BoxSpec, PageCanvas, pixels_to_mm
from evrakci.ui.sablon_empty import EmptyState
from evrakci.ui.sablon_inspector import InspectorPanel
from evrakci.ui.sablon_live import LiveReads
from evrakci.ui.sablon_nav import USER, NavPane
from evrakci.ui.sablon_parts import StatusPart, TemplateEdit
from evrakci.ui.sablon_rulers import CanvasWell
from evrakci.ui.sablon_sync import Syncing
from evrakci.ui.workers import Task

__all__ = ["CANVAS_DPI", "PageCanvas", "SablonScreen", "pixels_to_mm"]

KEY = "sablonlar"  # the splitter's name and the zoom's key
BASE = Qt.ItemDataRole.UserRole + 1  # an example's name before "· 1 kontrol"
ZOOM_RANGE = (25, 400, 10)
READ_DELAY_MS = 400  # after the last nudge
SAVE_DELAY_MS = 300
BUSY_DELAY_MS = 150  # "Okunuyor…" only for a read that takes longer than this
BAR_H = 52  # A .canvas-bar
COPY_OFFSET_MM = 5.0
BOX_MENU = ("sablonlar.kutu_cogalt", "sablonlar.kutu_sil", None, "sablonlar.yukari",
            "sablonlar.asagi", None, "sablonlar.degisken_ekle")
PAGE_MENU = ("sablonlar.kutu_ciz", "sablonlar.izgara", "sablonlar.okumalari_goster")


def _widths() -> tuple[int, int]:
    """A's left column and inspector at the current text size (360 / 400 at 150 %)."""
    m = theme.manager()
    return (360 if m.effective_density() == "comfortable" else 264, m.size("inspector-w"))


class SablonScreen(LiveReads, Syncing, QWidget):
    drawing_changed = Signal(bool)
    snap_changed = Signal(bool)

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
        self.window_ = None
        self.template: Template | None = None
        self.variable_name: str | None = None
        self.section_index: int | None = None
        self.example = 0  # document number in the open job
        self.page_number = 1  # the page of that document on the canvas
        self.job_id: str | None = None
        self.undo_stack = QUndoStack(self)
        self.zoom = None
        self.values: dict = {}  # the live read of the example on the canvas
        self.example_values: dict[int, dict] = {}  # after "Bütün örneklerde dene"
        self._docs: list = []
        self._read_number = 0
        self.read_lines: list[str] = []
        self._read_template: Template | None = None
        self._read_task: Task | None = None
        self._all_task: Task | None = None
        self._reread = False
        self._busy = False
        self._dirty = False
        self._save_error = ""
        self._saved_at: datetime | None = None
        self._syncing_zoom = False
        self._splitter_text = 0
        self._status: dict[str, StatusPart] = {}

        self._drawing = False  # "Kutu çiz" (B); the window mirrors it on its action

        self.canvas = PageCanvas()
        self.well = CanvasWell(self.canvas)
        self.nav = NavPane()
        self.templates, self.variables = self.nav.templates, self.nav.variables
        self.message = self.nav.message
        self.side = InspectorPanel()
        self.pattern, self.pattern_error = self.side.pattern, self.side.pattern_error
        self.empty = EmptyState()
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setObjectName(KEY)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.nav)
        self.splitter.addWidget(self._centre())
        self.splitter.addWidget(self.side)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setStretchFactor(2, 0)
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self.splitter)

        self._read_timer = self._timer(READ_DELAY_MS, self.read_example)
        self._save_timer = self._timer(SAVE_DELAY_MS, self._flush_save)
        self._busy_timer = self._timer(BUSY_DELAY_MS, self._show_busy)
        self._connect()
        theme.follow(self, self._restyle, "sablon-screen")
        self._make_zoom(None)
        self.refresh_templates()
        QTimer.singleShot(0, self._try_attach)

    # -- building --------------------------------------------------------------
    def _timer(self, interval: int, slot: Callable[[], None]) -> QTimer:
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.setInterval(interval)
        timer.timeout.connect(slot)
        return timer

    def _centre(self) -> QWidget:
        m = theme.manager()
        column = QWidget()
        col = QVBoxLayout(column)
        col.setContentsMargins(0, 0, 0, m.size("s3"))
        col.setSpacing(0)
        self.bar = QWidget()
        self.bar.setObjectName("sablonBar")
        bar = QHBoxLayout(self.bar)
        bar.setContentsMargins(m.size("s1"), 0, m.size("s1"), 0)
        bar.setSpacing(m.size("s2"))
        self.examples = QComboBox()
        self.examples.setAccessibleName("Örnek belge")
        self.examples.setToolTip("Kutuların çizildiği örnek belge")
        self.pages = QComboBox()
        for combo in (self.examples, self.pages):  # the longest item (" · 1 kontrol") is whole
            combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.pages.setAccessibleName("Örnek sayfa")
        self.pages.setToolTip("Örnek belgenin sayfası")
        example_label, page_label = QLabel("Örnek"), QLabel("Sayfa")
        for label, combo in ((example_label, self.examples), (page_label, self.pages)):
            label.setProperty("kind", "inspector-key")
            label.setBuddy(combo)
        bar.addWidget(example_label)
        bar.addWidget(self.examples)
        bar.addSpacing(m.size("s4"))
        bar.addWidget(page_label)
        bar.addWidget(self.pages)
        bar.addStretch(1)
        col.addWidget(self.bar)
        self.stack = QStackedWidget()
        self.stack.addWidget(self.well)
        frame = QFrame()
        frame.setProperty("kind", "well")
        inner = QVBoxLayout(frame)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.addWidget(self.empty)
        self.empty_frame = frame
        self.stack.addWidget(frame)
        col.addWidget(self.stack, 1)
        return column

    def _connect(self) -> None:
        self.nav.add_template.connect(self.new_template)
        self.nav.add_variable.connect(self.ask_variable)
        self.side.pattern_edited.connect(self._pattern_changed)
        self.templates.currentItemChanged.connect(
            lambda item, _old: item and self.open_template(item.data(USER)))
        self.variables.currentItemChanged.connect(self._tree_selected)
        self.variables.section_moved.connect(self.move_section_to)
        self.variables.variable_moved.connect(self.move_variable_to)
        self.variables.customContextMenuRequested.connect(self._variable_menu)
        self.examples.currentIndexChanged.connect(
            lambda i: self.set_example(self.examples.itemData(i) or 0))
        self.pages.currentIndexChanged.connect(
            lambda i: self.set_page_number(self.pages.itemData(i) or 1))
        canvas = self.canvas
        canvas.box_drawn.connect(self.add_box)
        canvas.box_selected.connect(self._canvas_selected)
        canvas.box_changed.connect(self._canvas_changed)
        canvas.drawing_cancelled.connect(lambda: self.set_drawing(False))
        canvas.cursor_moved.connect(self._cursor_moved)
        canvas.focus_changed.connect(lambda _on: self._sync_status())
        canvas.auto_zoomed.connect(self._auto_zoomed)
        canvas.view_changed.connect(self._sync_extent)
        canvas.escape_hook = self._escape
        canvas.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        canvas.customContextMenuRequested.connect(self._canvas_menu)
        side = self.side
        side.name_edited.connect(self._name_edited)
        side.required_toggled.connect(self._required_toggled)
        side.page_edited.connect(self._page_edited)
        side.box_edited.connect(self._box_edited)
        side.save_clicked.connect(self.save)
        side.more.setMenu(self._more_menu())

    def _more_menu(self) -> QMenu:
        menu = QMenu(self.side.more)
        menu.aboutToShow.connect(lambda: self._fill_menu(menu, BOX_MENU))
        return menu

    def _restyle(self) -> None:
        """After a theme, density or text-size switch: the column widths follow A."""
        m = theme.manager()
        if self._splitter_text != m.text_scale():
            self._splitter_text = m.text_scale()
            nav, side = _widths()
            self.splitter.setSizes([nav, max(360, self.splitter.width() - nav - side), side])
        self.bar.setFixedHeight(BAR_H)
        self.empty_frame.update()

    # -- the window: actions, status bar, zoom, toasts, prefs ------------------
    def _try_attach(self) -> None:
        window = self.window()
        if self.window_ is None and window is not self and hasattr(window, "registry"):
            self.attach(window)

    def attach(self, window) -> None:
        """Hook this tab into its MainWindow: the registry actions the window does not wire
        itself, the status bar slot, the zoom (saved in the prefs), toasts and the menus."""
        if self.window_ is window:
            return
        self.window_ = window
        r = window.registry
        own = {
            "sablonlar.kutu_sil": self.delete_selected,
            "sablonlar.kutu_cogalt": self.duplicate_box,
            "sablonlar.degisken_ekle": self.ask_variable,
            "sablonlar.yukari": lambda: self.move_selected(-1),
            "sablonlar.asagi": lambda: self.move_selected(1),
            "sablonlar.okumalari_goster": self.set_show_reads,
            # the arrows and Space work inside the canvas; the command only moves focus there
            "sablonlar.kaydir": self.focus_canvas,
            "sablonlar.kaydir_1mm": self.focus_canvas,
            "sablonlar.el": self.focus_canvas,
        }
        for action_id, slot in own.items():
            r.connect(action_id, slot)
        layout = window.status_slot(KEY).layout()
        for name, part in (("example", StatusPart()), ("box", StatusPart()),
                           ("cursor", StatusPart()), ("hint", StatusPart()),
                           ("saved", StatusPart("circle-dashed", "icon")),
                           ("check", StatusPart("triangle-alert", "rider-edge"))):
            layout.addWidget(part)
            self._status[name] = part
        layout.addStretch(1)  # the items sit at the left, not centred in the widest tab's slot
        self._make_zoom(getattr(window, "prefs", None))
        window.register_zoom(KEY, self.zoom, "Sayfa")
        self._sync_all()

    def _toaster(self):
        return getattr(self.window_, "toaster", None)

    def _toast(self, text: str, action: str | None = None, slot=None, kind: str = "info",
               timeout_ms: int = 6000) -> None:
        toaster = self._toaster()
        if toaster is not None:
            toaster.show(text, action, slot, kind=kind, timeout_ms=timeout_ms)

    def _registry(self):
        return getattr(self.window_, "registry", None)

    def _make_zoom(self, prefs) -> None:
        from evrakci.ui.zoomview import ZoomController

        if self.zoom is not None:
            self.zoom.deleteLater()
        stored = prefs.zoom(KEY, 0) if prefs is not None else 0
        self.zoom = ZoomController(self.canvas, prefs, KEY, *ZOOM_RANGE, self.canvas.fit_zoom)
        self.zoom.zoom_changed.connect(self._zoom_changed)
        if stored:  # a saved zoom is the user's: the page no longer follows the window
            self.canvas.set_zoom(self.zoom.zoom())
        else:
            self._auto_zoomed(self.canvas.zoom())

    def _zoom_changed(self, pct: int) -> None:
        if self._syncing_zoom:
            return
        if pct == self.canvas.fit_zoom():  # Ctrl+0 (or the slider on it): follow the window again
            self.canvas.refit()
        else:
            self.canvas.set_zoom(pct)

    def _auto_zoomed(self, pct: int) -> None:
        self._syncing_zoom = True
        try:
            self.zoom.set_zoom(pct, save=False)
        finally:
            self._syncing_zoom = False
        self.canvas.scroll_to_top()  # the controller keeps the centre; a fit starts at the top

    def _sync_extent(self) -> None:
        """The selected box's extent on the rulers follows it while it is dragged."""
        item = self.canvas.selected_item()
        self.well.set_extent(item.spec.box if item is not None else None)

    def focus_canvas(self) -> None:
        self.canvas.setFocus(Qt.FocusReason.ShortcutFocusReason)

    # -- templates -------------------------------------------------------------
    def refresh_templates(self) -> None:
        self.flush_save()
        found = sorted(self.store.list(), key=lambda t: t.name)
        self.templates.blockSignals(True)
        self.templates.clear()
        for template in found:
            self.templates.add_template(template.id, template.name, len(template.variables))
            if self.template is not None and template.id == self.template.id:
                self.templates.setCurrentRow(self.templates.count() - 1)
        self.templates.fit_height()
        self.templates.blockSignals(False)
        self._refresh_examples()
        if not found:
            self.template, self.variable_name, self.section_index = None, None, None
            self.undo_stack.clear()
            self._show_variables()
            self._show_boxes()
        elif self.template is None:
            self.templates.setCurrentRow(0)  # opens the first template
        self._sync_all()

    def _ask_text(self, title: str, label: str, ok: str) -> str | None:
        dialog = QInputDialog(self)
        dialog.setWindowTitle(title)
        dialog.setLabelText(label)
        dialog.setOkButtonText(ok)
        dialog.setCancelButtonText("Vazgeç")
        if dialog.exec() == QInputDialog.DialogCode.Accepted and dialog.textValue().strip():
            return dialog.textValue().strip()
        return None

    def new_template(self) -> None:
        name = self._ask_text("Yeni şablon", "Şablonun adı", "Oluştur")
        if name:
            self.flush_save()
            self.template = self.store.create(name)  # the list then marks it as the open one
            self.refresh_templates()
            self.open_template(self.template.id)

    def open_template(self, template_id: str) -> None:
        self.flush_save()
        self.template = self.store.load(template_id)
        self.undo_stack.clear()
        self._dirty, self._save_error = False, ""
        self.variable_name = self.template.variables[0].name if self.template.variables else None
        self.section_index = None
        self.values, self.example_values = {}, {}
        self.pattern.setText(self.template.filename_pattern)
        self.message.setText("")
        self._show_variables()
        self._show_boxes()
        self._sync_all()
        self.read_example()

    def _refresh_template_row(self) -> None:
        if self.template is None:
            return
        for row in range(self.templates.count()):
            item = self.templates.item(row)
            if item.data(USER) == self.template.id:
                from evrakci.ui.sablon_nav import ROLE_VALUE

                count = len(self.template.variables)
                value = "kaydedilmedi" if self._dirty else f"{count} değişken"
                item.setData(ROLE_VALUE, value)
                item.setData(Qt.ItemDataRole.AccessibleTextRole,
                             f"Şablon {self.template.name}, {value}")
                self.templates.viewport().update()

    # -- variables and selection -----------------------------------------------
    def ask_variable(self) -> None:
        if self.template is None:
            return
        name = self._ask_text("Değişken ekle", "Değişkenin adı (örn. Firma_Adi)", "Ekle")
        if name and self._edit("Değişken ekle", lambda t: t.add_variable(name)):
            self.select_variable(name)

    def select_variable(self, name: str) -> None:
        if self.template is None:
            return
        self.variable_name, self.section_index = name, None
        self._apply_selection(reveal=False)

    def select_section(self, name: str, index: int) -> None:
        if self.template is None:
            return
        self.variable_name, self.section_index = name, index
        self._apply_selection(reveal=True)

    def _tree_selected(self, item, _old=None) -> None:
        if item is None or self.template is None:
            return
        parent = item.parent()
        self.variable_name = (parent or item).data(0, USER)
        if parent is not None:
            self.section_index = item.data(0, USER)
        else:  # a variable with a single box: its row is the box
            variable = self.current_variable()
            self.section_index = 0 if variable is not None and len(variable.sections) == 1 \
                else None
        self._apply_selection(reveal=True, from_tree=True)

    def _canvas_selected(self, name: str, index: int) -> None:
        """A click on a box (or on the bare sheet, which clears the box)."""
        if self.template is None:
            return
        if name:
            self.variable_name, self.section_index = name, index
        else:
            self.section_index = None
        self._apply_selection(reveal=False, from_canvas=True)

    def _apply_selection(self, reveal: bool = False, from_tree: bool = False,
                         from_canvas: bool = False) -> None:
        name, index = self.variable_name, self.section_index
        if reveal and name and index is not None:
            self._show_section_page(name, index)
        if not from_canvas:
            self.canvas.select(name if index is not None else None,
                               index if index is not None else -1, reveal=reveal)
        if not from_tree:
            item = self.variables.item_for(name, index) if name else None
            self.variables.blockSignals(True)
            if item is not None:
                self.variables.setCurrentItem(item)
            else:
                self.variables.setCurrentItem(None)
                self.variables.clearSelection()
            self.variables.blockSignals(False)
            self.variables.viewport().update()
        self._sync_all()

    def _show_section_page(self, name: str, index: int) -> None:
        """Show the page a chosen section belongs to."""
        try:
            page = self.template.variable(name).sections[index].page
        except (TemplateError, IndexError):
            return
        count = self._page_count()
        wanted = count if page == -1 else page
        if self.example and 1 <= wanted <= count and wanted != self.page_number:
            self.set_page_number(wanted)

    def _show_variables(self) -> None:
        self.variables.blockSignals(True)
        self.variables.fill(self.template)
        names = [v.name for v in self.template.variables] if self.template else []
        if self.variable_name not in names:
            self.variable_name, self.section_index = None, None
        elif self.variables.item_for(self.variable_name, self.section_index) is None:
            self.section_index = None
        item = self.variables.item_for(self.variable_name, self.section_index) \
            if self.variable_name else None
        if item is not None:
            self.variables.setCurrentItem(item)
        self.variables.blockSignals(False)
        self.nav.set_empty(self.template is None)
        if self.template is not None and not self.template.variables:
            self.nav.foot.setText("Bu şablonda henüz değişken yok. Eklemek için + düğmesine ya "
                                  "da Ctrl+Shift+N tuşlarına basın.")
        self.variables.viewport().update()

    def current_variable(self):
        if self.template is None or not self.variable_name:
            return None
        try:
            return self.template.variable(self.variable_name)
        except TemplateError:
            return None

    def _number_of(self, name: str) -> int:
        names = [v.name for v in self.template.variables] if self.template else []
        return names.index(name) + 1 if name in names else 0

    def _required_toggled(self, value: bool) -> None:
        if self.variable_name:
            name = self.variable_name
            self._edit("Zorunlu", lambda t: t.set_required(name, value))

    def _name_edited(self, text: str) -> None:
        name = self.variable_name
        if not name or text == name:
            return
        index = self.section_index
        if self._edit("Değişken adı", lambda t: t.rename_variable(name, text)):
            self.variable_name, self.section_index = text, index
            self._apply_selection()
        else:
            self._sync_inspector()

    def _page_edited(self, page: int) -> None:
        name, index = self.variable_name, self.section_index
        if name is None or index is None:
            return

        def change(t: Template) -> None:
            sections = t.variable(name).sections
            old = sections[index]
            sections[index] = Section(page, old.box_mm, old.example)

        if self._edit("Kutunun sayfası", change):
            wanted = self._page_count() if page == -1 else page
            if self.example and 1 <= wanted <= self._page_count() and wanted != self.page_number:
                self.set_page_number(wanted)

    def _pattern_changed(self) -> None:
        if self.template is None:
            return
        text = self.pattern.text()
        if text != self.template.filename_pattern:
            if not self._edit("Dosya adı", lambda t: t.set_pattern(text)):
                # the message goes at the field and what was typed stays to be mended
                self.side.set_pattern_error(self.message.text())
                self.message.setText("")

    # -- moving things in the list ---------------------------------------------
    def move_selected_section(self, step: int) -> None:
        item = self.variables.currentItem()
        if item is None or item.parent() is None:
            self.message.setText("Önce bir bölüm seçin.")
            return
        self.move_selected(step)

    def move_selected(self, step: int) -> None:
        """Alt+Up / Alt+Down: the chosen section moves in the try order, a variable in the list."""
        if self.template is None or self.variable_name is None:
            return
        variable = self.current_variable()
        if self.section_index is not None and variable is not None and len(variable.sections) > 1:
            self.move_section_to(self.variable_name, self.section_index,
                                 self.section_index + step)
            return
        names = [v.name for v in self.template.variables]
        old = names.index(self.variable_name)
        self.move_variable_to(old, old + step)

    def move_section_to(self, name: str, old: int, new: int) -> None:
        if self._edit("Sırayı değiştir", lambda t: t.move_section(name, old, new)):
            self.select_section(name, new)

    def move_variable_to(self, old: int, new: int) -> None:
        if self.template is None or not 0 <= new < len(self.template.variables):
            return

        def change(t: Template) -> None:
            t.variables.insert(new, t.variables.pop(old))

        name = self.template.variables[old].name
        if self._edit("Sırayı değiştir", change):
            self.select_variable(name)

    # -- examples and the page -------------------------------------------------
    def _documents(self) -> list:
        """The job's documents as of the last refresh (it is cheap to ask again, not to
        recompute: 1,000 pages)."""
        return self._docs

    def _refresh_examples(self) -> None:
        controller = self.controller()
        job_id = controller.job.id if controller is not None else None
        if job_id != self.job_id:  # another job: the old example number means nothing
            self.job_id, self.example, self.page_number = job_id, 0, 1
            self.values, self.example_values = {}, {}
        self._docs = list(controller.documents()) if controller is not None else []
        self.examples.blockSignals(True)
        self.examples.clear()
        if controller is not None:
            job = controller.job
            for number, document in enumerate(self._docs, start=1):
                page = job.position_of(document.page_ids[0])
                self.examples.addItem(f"Örnek {number}, sayfa {page}", number)
                self.examples.setItemData(number - 1, self.examples.itemText(number - 1), BASE)
        if self.example > self.examples.count():
            self.example = 0
        index = self.examples.findData(self.example)
        if index >= 0:
            self.examples.setCurrentIndex(index)
        self.examples.blockSignals(False)
        self._mark_example_checks()
        if self.examples.count() and not self.example:
            self.set_example(1)
        elif not self.examples.count():
            self.example = 0
            self._load_page()
        self._sync_all()

    def _mark_example_checks(self) -> None:
        """After "Bütün örneklerde dene": an example with reads that need a check carries the
        triangle and its count in the picker (icon + word, never colour alone)."""
        warn = make_icon("triangle-alert", "check-text", theme.manager().size("icon-sm"))
        for row in range(self.examples.count()):
            flagged = reading.flagged_count(self.example_values.get(self.examples.itemData(row),
                                                                    {}))
            base = self.examples.itemData(row, BASE)
            self.examples.setItemText(row, f"{base} · {flagged} kontrol" if flagged else base)
            self.examples.setItemIcon(row, warn if flagged else QIcon())

    def set_example(self, number: int) -> None:
        controller = self.controller()
        if controller is None or not number:
            self.example = 0
            self._load_page()
            self._sync_all()
            return
        self.example, self.page_number = number, 1
        index = self.examples.findData(number)
        if index >= 0 and self.examples.currentIndex() != index:
            self.examples.blockSignals(True)
            self.examples.setCurrentIndex(index)
            self.examples.blockSignals(False)
        self.values = self.example_values.get(number, {})
        self._fill_pages()
        self._load_page()
        self._show_boxes()
        self._sync_all()
        self.read_example()

    def _page_count(self) -> int:
        if not self.example or self.controller() is None:
            return 0
        return len(self._document().page_ids)

    def _fill_pages(self) -> None:
        count = self._page_count()
        self.pages.blockSignals(True)
        self.pages.clear()
        for page in range(1, count + 1):
            self.pages.addItem(f"{page} / {count}", page)
        self.pages.setCurrentIndex(self.page_number - 1)
        self.pages.blockSignals(False)

    def set_page_number(self, page: int) -> None:
        if not self.example or not 1 <= page <= self._page_count():
            return
        self.page_number = page
        self.pages.blockSignals(True)
        self.pages.setCurrentIndex(page - 1)
        self.pages.blockSignals(False)
        self._load_page()
        self._show_boxes()
        self._apply_selection()

    def _load_page(self) -> None:
        if not self.example or self.controller() is None:
            self.canvas.set_page(None)
            return
        try:
            image = self._render(self.page_number, CANVAS_DPI)
        except Exception as error:  # a missing or damaged scan: say so, keep working
            self.canvas.set_page(None)
            self.message.setText(f"Sayfa gösterilemedi: {error}. Yükle sekmesinden işi kontrol "
                                 "edin.")
            return
        self.canvas.set_page(image, CANVAS_DPI)

    def _example_name(self) -> str:
        controller = self.controller()
        page = controller.job.position_of(self._document().page_ids[0])
        return f"{controller.job.name} · Belge {self.example} · s.{page}"

    def _document(self):
        return self._docs[self.example - 1]

    def _render(self, page: int, dpi: int) -> Image.Image:
        controller = self.controller()
        pid = self._document().page_ids[page - 1]
        batch_id, index = parse_page_id(pid)
        path = controller.store.batch_files(controller.job)[batch_id]
        return render_page(path, index, controller.job.rotations.get(pid, 0), dpi=dpi)

    # -- boxes -----------------------------------------------------------------
    def _page_matches(self, page: int) -> bool:
        count = self._page_count()
        return page == self.page_number or (page == -1 and self.page_number == count)

    def _show_boxes(self) -> None:
        specs: list[BoxSpec] = []
        if self.template is not None and self.example and self.controller() is not None:
            current = self._example_name()
            for number, variable in enumerate(self.template.variables, start=1):
                for index, section in enumerate(variable.sections):
                    if self._page_matches(section.page):
                        faint = section.example not in (None, current)
                        specs.append(BoxSpec(variable.name, index, number, section.box_mm,
                                             index > 0 or faint))
        self.canvas.set_boxes(specs)
        self._push_readings()
        if self.variable_name and self.section_index is not None:
            self.canvas.select(self.variable_name, self.section_index)

    def add_box(self, box_mm) -> None:
        if self.template is None or not self.variable_name:
            self.message.setText("Önce soldan bir değişken seçin.")
            return
        if not self.example:
            self.message.setText("Önce Yükle sekmesinden bir iş açın; örnek sayfalar oradan gelir.")
            return
        name = self.variable_name
        section = Section(self.page_number, tuple(float(v) for v in box_mm), self._example_name())
        index = len(self.template.variable(name).sections)
        if self._edit("Kutu ekle", lambda t: t.add_section(name, section)):
            self.select_section(name, index)
            self.read_example()

    def _canvas_changed(self, name: str, index: int, box: tuple) -> None:
        """A box moved, resized or nudged on the canvas."""
        self._set_box(name, index, box)

    def _box_edited(self, box: tuple) -> None:
        """The inspector's X, Y, width or height changed."""
        if self.variable_name and self.section_index is not None:
            self.canvas.update_box(self.variable_name, self.section_index, box)
            self._set_box(self.variable_name, self.section_index, box)

    def _set_box(self, name: str, index: int, box: tuple) -> None:
        box = tuple(round(float(v), 2) for v in box)

        def change(t: Template) -> None:
            sections = t.variable(name).sections
            old = sections[index]
            sections[index] = Section(old.page, box, old.example)

        try:
            old = self.template.variable(name).sections[index].box_mm
        except (TemplateError, IndexError):
            return
        same_size = abs((old[2] - old[0]) - (box[2] - box[0])) < 1e-6 and abs(
            (old[3] - old[1]) - (box[3] - box[1])) < 1e-6
        text = "Kutuyu taşı" if same_size else "Kutuyu yeniden boyutlandır"
        merge = abs(hash((text, name, index))) % (2**31 - 1)
        self._edit(text, change, merge=merge, light=True)

    def duplicate_box(self) -> None:
        """Ctrl+D: a copy of the chosen box as the variable's next section (a variant)."""
        name, index = self.variable_name, self.section_index
        if self.template is None or name is None or index is None:
            return
        old = self.template.variable(name).sections[index]
        x0, y0, x1, y1 = old.box_mm
        width, height = self.canvas.page_mm() if self.canvas.has_page() else (1e9, 1e9)
        dx = max(0.0, min(COPY_OFFSET_MM, width - x1))
        dy = max(0.0, min(COPY_OFFSET_MM, height - y1))
        copy = Section(old.page, (x0 + dx, y0 + dy, x1 + dx, y1 + dy), old.example)
        position = len(self.template.variable(name).sections)
        if self._edit("Kutuyu çoğalt", lambda t: t.add_section(name, copy)):
            self.select_section(name, position)
            self.read_example()

    def delete_selected(self) -> None:
        """Del: remove the chosen box (or the chosen variable); undoable, the toast says so."""
        if self.template is None or self.variable_name is None:
            return
        if self.templates.hasFocus():  # Del in the template list means nothing here
            return
        name, index = self.variable_name, self.section_index
        if index is not None:
            if self._edit("Kutuyu sil", lambda t: t.remove_section(name, index)):
                left = len(self.template.variable(name).sections)
                if left:
                    self.select_section(name, min(index, left - 1))
                else:
                    self.select_variable(name)
                self._toast(f"“{name}” değişkeninin {index + 1}. bölümü silindi.", "Geri al",
                            self.undo_stack.undo, timeout_ms=10000)
                self.read_example()
            return
        count = len(self.template.variable(name).sections)
        if self._edit("Değişkeni sil", lambda t: t.remove_variable(name)):
            self.variable_name = None
            self._show_variables()
            self._apply_selection()
            detail = f" ({count} kutu)" if count else ""
            self._toast(f"“{name}” değişkeni silindi{detail}.", "Geri al", self.undo_stack.undo,
                        timeout_ms=10000)
            self.read_example()

    # -- drawing, snapping, reads on the page ----------------------------------
    def is_drawing(self) -> bool:
        return self._drawing

    def toggle_draw(self) -> None:
        self.set_drawing(not self._drawing)

    def set_drawing(self, value: bool) -> None:
        """Kutu çiz on or off; `drawing_changed` tells the window's checkable action."""
        value = bool(value)
        if value == self._drawing:
            return
        self._drawing = value
        self.canvas.set_drawing(value)
        if value and self.template is not None and not self.variable_name:
            self.message.setText("Çizmeden önce soldan bir değişken seçin.")
        self.drawing_changed.emit(value)

    def is_snapping(self) -> bool:
        return bool(self.canvas.snap)

    def toggle_grid(self) -> None:
        self.set_snap(not self.canvas.snap)

    def set_snap(self, value: bool) -> None:
        """Izgaraya oturt on or off; `snap_changed` tells the window's checkable action."""
        value = bool(value)
        if value == bool(self.canvas.snap):
            return
        self.canvas.snap = value
        self.snap_changed.emit(value)

    def set_show_reads(self, on: bool = True) -> None:
        self.canvas.set_show_reads(bool(on))

    # -- menus -----------------------------------------------------------------
    def _fill_menu(self, menu: QMenu, ids) -> None:
        menu.clear()
        registry = self._registry()
        if registry is None:
            return
        for action_id in ids:
            if action_id is None:
                menu.addSeparator()
            else:
                menu.addAction(registry.action(action_id))

    def box_menu(self, ids=BOX_MENU) -> QMenu:
        menu = QMenu(self)
        menu.setAccessibleName("Kutu komutları")
        self._fill_menu(menu, ids)
        return menu

    def _variable_menu(self, pos: QPoint) -> None:
        item = self.variables.itemAt(pos)
        if item is not None:
            self.variables.setCurrentItem(item)
        menu = self.box_menu()
        if not menu.isEmpty():
            menu.exec(self.variables.viewport().mapToGlobal(pos))
        menu.deleteLater()

    def _canvas_menu(self, pos: QPoint) -> None:
        item = self.canvas.box_at(self.canvas.mapToScene(pos))
        if item is not None:
            self.canvas.select(item.spec.name, item.spec.index)
            self._canvas_selected(item.spec.name, item.spec.index)
        menu = self.box_menu(BOX_MENU if item is not None else PAGE_MENU)
        if not menu.isEmpty():
            menu.exec(self.canvas.viewport().mapToGlobal(pos))
        menu.deleteLater()

    # -- live reading ----------------------------------------------------------
    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape and self._escape():
            event.accept()
            return
        super().keyPressEvent(event)

    # -- edits: saved at once, undoable ----------------------------------------
    def _edit(self, text: str, change, merge: int = -1, light: bool = False) -> bool:
        """Apply `change` to the template. `light` is for box moves: nothing is rebuilt, the
        save and the read follow after a short pause, and the same box again merges the undo."""
        self.message.setText("")
        before = template_to_dict(self.template)
        revision = template_revision(self.template)
        try:
            change(self.template)
        except TemplateError as error:
            self._restore(before, refresh=False)
            self.message.setText(str(error))
            return False
        after = template_to_dict(self.template)
        if after != before:
            self.undo_stack.push(TemplateEdit(self, text, before, after, merge))
            if light:
                self._touched()
            else:
                self._saved()
            if template_revision(self.template) != revision:
                self._read_timer.start()  # what is read changed (a box, a page, the order)
        return True

    def _restore(self, data: dict, refresh: bool = True) -> None:
        revision = template_revision(self.template) if self.template is not None else ""
        self.template = template_from_dict(data)
        if refresh:
            self._saved()
            if template_revision(self.template) != revision:
                self._read_timer.start()

    def _touched(self) -> None:
        """A light edit: remember to save and to read, update what is shown now."""
        self._dirty = True
        self._save_timer.start()
        self._read_timer.start()
        self._refresh_template_row()
        self._sync_inspector()
        self._sync_status()

    def _saved(self) -> None:
        self._flush_save()
        self.pattern.setText(self.template.filename_pattern)
        self.side.set_pattern_error("")
        self._show_variables()
        self._show_boxes()
        self._refresh_template_row()
        self._sync_all()

    def flush_save(self) -> None:
        if self._dirty:
            self._flush_save()

    def _flush_save(self) -> None:
        self._save_timer.stop()
        if self.template is None:
            return
        try:
            self.store.save(self.template)
        except OSError as error:
            self._dirty, self._save_error = True, str(error)
            self.message.setText("Şablon kaydedilemedi. Diskte yer olduğundan emin olup "
                                 "Şablonu kaydet'e basın.")
        else:
            self._dirty, self._save_error = False, ""
            self._saved_at = datetime.now()
        self._refresh_template_row()
        self._sync_status()

    def save(self) -> None:
        """Ctrl+S and "Şablonu kaydet": saves now and says so."""
        if self.template is None:
            self.message.setText("Kaydedilecek bir şablon yok. Önce bir şablon oluşturun.")
            return
        self._flush_save()
        if not self._save_error:
            self.message.setText("")
            self._toast("Şablon kaydedildi.", kind="success")

    def hideEvent(self, event) -> None:  # noqa: N802
        self.flush_save()
        super().hideEvent(event)

    # -- keeping the parts in step ---------------------------------------------