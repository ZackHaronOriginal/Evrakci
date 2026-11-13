"""The Değerler tab (direction A): every read value in one table, linked both ways to the page
crop on the right. Kontrol values are fixed here: Enter accepts and moves to the next one.

Layout (final-a/degerler.html): a table card (view switch with counts, search, template picker,
the table) and the "Kaynak" side (crop, Okunan / Öneri card, actions), split by a named
QSplitter the window remembers. The window's command bar, status bar slot, zoom slider,
toaster and taskbar are used once the screen sits in a MainWindow (`attach`).
"""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping

import pypdfium2 as pdfium
from PySide6.QtCore import QByteArray, QEvent, QModelIndex, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemDelegate,
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from evrakci.pipeline.cuts import _template_of, document_template, record_read_error
from evrakci.pipeline.job import Job, parse_page_id
from evrakci.pipeline.ocr.engine import EngineUnavailable
from evrakci.pipeline.render import render_page
from evrakci.pipeline.review import needs_reading, store_reading
from evrakci.pipeline.templates.model import Template, template_revision
from evrakci.pipeline.templates.read import read_document
from evrakci.ui import icons, theme
from evrakci.ui.chrome import make_icon
from evrakci.ui.controller import JobController
from evrakci.ui.degerler_model import (
    LEVELS,
    SAMPLE_SIZE,
    VIEW_NAMES,
    Cell,
    Row,
    SampleItem,
    confirm,
    count,
    display_name,
    draw_sample,
    flag_variable,
    in_view,
    joined,
    make_cell,
    matches,
    tr_lower,
)
from evrakci.ui.degerler_parts import EmptyState, HeaderBar, StatusItem, ViewSelector
from evrakci.ui.degerler_side import Crop, PageImages, SidePanel
from evrakci.ui.degerler_table import (
    SAMPLE_COLUMNS,
    VALUE_KINDS,
    WIDTHS,
    ValuesModel,
    ValuesTable,
    main_columns,
)
from evrakci.ui.thumbnails import to_qimage
from evrakci.ui.widgets import add_clear_button
from evrakci.ui.workers import Task, start

ZOOM_KEY = "degerler"
VIEW_KEY = "degerler.gorunum"  # the chosen view (prefs.view_state)
TEMPLATE_KEY = "degerler.sablon"  # the chosen template
ZOOM_DEFAULT = 200  # A's status bar: "%200"
UNDO_TEXT = "Değeri onayla"


def build_rows_fast(job: Job, documents, templates: Mapping[str, Template]) -> list[Row]:
    """`degerler_model.build_rows` with the page → template map built once, so a refresh
    stays fast at 1,000 documents (cuts.current_values rebuilds it for every document)."""
    template_of = _template_of(job)
    position = {pid: n for n, pid in enumerate(job.ordered_page_ids(), start=1)}
    rows = []
    for number, document in enumerate(documents, start=1):
        first = document.page_ids[0]
        template_id = template_of.get(first)
        if template_id is None:
            continue
        source = job.value_sources.get(first)
        current = (source is not None and source.page_ids == tuple(document.page_ids)
                   and source.template_id == template_id)
        values = job.values.get(first) if current else None
        template = templates.get(template_id)
        cells = []
        if template is not None:
            for variable in template.variables:
                cells.append(make_cell(variable, values.get(variable.key)
                                       if values is not None else None))
        error = job.read_errors.get(first) if current else None
        rows.append(Row(number, document, template_id, template, position.get(first, 0),
                        position.get(document.page_ids[-1], 0), cells, error))
    return rows


class DegerlerScreen(QWidget):
    draw_variant = Signal(int, str)  # document number, variable name
    status = Signal(str)
    finished = Signal()
    go_tab = Signal(str)

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
        self.window_ = None  # the MainWindow once attached
        self.rows: list[Row] = []  # every templated document of the job
        self.template_rows: list[Row] = []  # the picked template's documents
        self._view = "tumu"
        self._main_view = "tumu"  # where Örnek and Tümünü incele return to
        self._review_all = False
        self._template_id: str | None = None
        self._samples: dict[str, list[SampleItem]] = {}
        self._watched: JobController | None = None
        self._dirty = False
        self._started = 0.0
        self._results: list = []
        self._header_key = ""
        self._filling = False
        self._files: dict = {}
        self._rotations: dict = {}
        self._job_id = ""
        self._sample_done = False
        self.zoom = None
        self.loupe = None
        self.images = PageImages(self)
        self.images.render = self._render_page

        m = theme.manager()
        root = QVBoxLayout(self)
        root.setContentsMargins(m.size("s3"), 0, m.size("s3"), m.size("s3"))
        root.setSpacing(m.size("s3"))

        # Reading: progress, then one message until it is closed (an InfoBar)
        self.progress_band = QFrame()
        self.progress_band.setProperty("kind", "infobar")
        band = QHBoxLayout(self.progress_band)
        band.setContentsMargins(m.size("s4"), m.size("s2"), m.size("s2"), m.size("s2"))
        band.setSpacing(m.size("s3"))
        self.progress_icon = QLabel()
        self.progress_label = QLabel("")
        self.progress_label.setFont(m.font("body-strong"))
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedWidth(240)
        self.progress.setAccessibleName("Okuma ilerlemesi")
        self.progress_hint = QLabel("")
        self.progress_hint.setProperty("textRole", "secondary")
        self.cancel_button = QPushButton("Okumayı durdur")
        self.cancel_button.setToolTip("Okumayı durdur (Ctrl+.)")
        self.cancel_button.setAccessibleName("Okumayı durdur (Ctrl+.)")
        self.cancel_button.clicked.connect(self.cancel)
        self.dismiss_button = QPushButton()
        self.dismiss_button.setProperty("variant", "subtle")
        self.dismiss_button.setToolTip("Mesajı kapat")
        self.dismiss_button.setAccessibleName("Mesajı kapat")
        self.dismiss_button.clicked.connect(self._dismiss)
        for widget in (self.progress_icon, self.progress_label, self.progress):
            band.addWidget(widget)
        band.addWidget(self.progress_hint, 1)
        band.addWidget(self.cancel_button)
        band.addWidget(self.dismiss_button)
        root.addWidget(self.progress_band)

        # The two read commands live in the command bar; these buttons carry their slots and
        # enabled state (the window mirrors them into degerler.oku / degerler.eksikleri_oku).
        self.read_button = QPushButton("Değerleri oku", self)
        self.read_button.clicked.connect(lambda: self.read_values(only_missing=False))
        self.missing_button = QPushButton("Yalnızca eksikleri oku", self)
        self.missing_button.clicked.connect(lambda: self.read_values(only_missing=True))
        for button in (self.read_button, self.missing_button):
            button.hide()

        # Table card
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setObjectName("degerler")
        self.splitter.setChildrenCollapsible(False)
        self.card = QFrame()
        self.card.setProperty("kind", "table-card")
        self.card.setAccessibleName("Değerler tablosu")
        card = QVBoxLayout(self.card)
        card.setContentsMargins(1, 1, 1, m.size("s2"))
        card.setSpacing(0)
        self.selector = ViewSelector()
        self.selector.changed.connect(self.set_view)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Ara")
        self.search.setAccessibleName("Değerlerde ara")
        add_clear_button(self.search)  # a 24 px target (WCAG 2.5.8)
        self._search_icon = self.search.addAction(make_icon("search"),
                                                  QLineEdit.ActionPosition.LeadingPosition)
        self.search.textChanged.connect(self._search_changed)
        self.search.installEventFilter(self)
        self.template_combo = QComboBox()
        self.template_combo.setAccessibleName("Şablon")
        self.template_combo.setToolTip("Şablon")
        self.template_combo.setPlaceholderText("Şablon yok")  # no job, or no templated document
        self.template_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.template_combo.currentIndexChanged.connect(self._template_picked)
        self.header_bar = HeaderBar(self.selector, self.search, self.template_combo)
        card.addWidget(self.header_bar)
        self.model = ValuesModel(self)
        self.model.edited.connect(self._apply_edit)
        self.table = ValuesTable()
        self.table.setModel(self.model)
        self.table.hint_keys = self._hint_keys
        self.table.selectionModel().currentChanged.connect(self._current_changed)
        self.table.selectionModel().selectionChanged.connect(lambda *_: self._sync_actions())
        self.table.submitted.connect(self._editor_closed)
        self.table.return_pressed.connect(self.accept_current)
        header = self.table.horizontalHeader()
        header.sectionResized.connect(self._header_moved)
        header.sortIndicatorChanged.connect(self._header_moved)
        self.table.viewport().installEventFilter(self)
        theme.bind_style(self.table, lambda: (
            f"QTableView {{ background: {theme.manager().hex('card')}; }}"
            f"QHeaderView::section {{ background: {theme.manager().hex('card')}; }}"))
        card.addWidget(self.table, 1)
        self.empty = EmptyState()
        card.addWidget(self.empty, 1)
        self.empty.hide()
        self.splitter.addWidget(self.card)
        self.side = SidePanel(self.images)
        self.side.accept_button.clicked.connect(self.accept_current)
        self.side.type_button.clicked.connect(self.type_current)
        self.side.variant_button.clicked.connect(self._draw_variant)
        self.side.source.whole.clicked.connect(self.toggle_whole_page)
        self.side.source.view.box_clicked.connect(self._box_clicked)
        self.splitter.addWidget(self.side)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        root.addWidget(self.splitter, 1)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self._deferred_refresh)
        self._header_timer = QTimer(self)
        self._header_timer.setSingleShot(True)
        self._header_timer.setInterval(300)
        self._header_timer.timeout.connect(self._save_header)
        self._status_items: dict[str, StatusItem] = {}
        self._make_zoom(None)
        self._set_busy(False)
        self.selector.set_view(self._view)
        theme.follow(self, self._restyle, "degerler-screen")
        self.refresh()
        QTimer.singleShot(0, self._try_attach)

    # -- the window: command bar actions, status bar, zoom, toasts ------------------------
    def _try_attach(self) -> None:
        window = self.window()
        if self.window_ is None and window is not self and hasattr(window, "registry"):
            self.attach(window)

    def attach(self, window) -> None:
        """Hook this tab into its MainWindow: the registry actions the window does not wire
        itself, the status bar slot, the zoom slider, toasts, the taskbar and prefs."""
        if self.window_ is window:
            return
        self.window_ = window
        r = window.registry
        own = {
            "degerler.secilenleri_onayla": self.accept_selected,
            "degerler.vazgec": self.dismiss,
            "degerler.tumunu_sec": self.select_all,
            "degerler.tum_sayfa": self.toggle_whole_page,
            "degerler.onceki_kontrol": lambda: self.next_check(-1),
            "degerler.tumunu_incele": self.set_review_all,
            "degerler.ornek_kontrol": self.set_sample,
        }
        for action_id, slot in own.items():
            r.connect(action_id, slot)
        r.connect_tab("app.bul", "degerler", self.focus_search)
        r.connect_tab("app.git", "degerler", self.go_to)
        self.go_tab.connect(window.show_tab)
        prefs = getattr(window, "prefs", None)
        if prefs is not None:  # QOL 10: the chosen view and template come back next time
            view = prefs.view_state(VIEW_KEY, "")
            if view in ("kontrol", "incelenmemis", "tumu"):
                self._view = self._main_view = view
                self.selector.set_view(view)
            self._template_id = prefs.view_state(TEMPLATE_KEY, "") or self._template_id
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._context_menu)
        slot = window.status_slot("degerler")
        layout = slot.layout()
        for name, icon, role in (("doc", None, "icon"), ("kontrol", "triangle-alert",
                                                         "check-text"),
                                 ("bad", "circle-x", "danger"), ("seen", "circle-check", "ok"),
                                 ("sample", "shuffle", "icon"), ("errors", "circle-check", "ok"),
                                 ("unread", None, "icon")):
            item = StatusItem(icon, role)
            layout.addWidget(item)
            self._status_items[name] = item
        self._make_zoom(getattr(window, "prefs", None))
        window.register_zoom("degerler", self.zoom, "Kaynak kesiti")
        self._header_key = ""
        self.refresh()

    CONTEXT = ("degerler.onayla", "degerler.elle_yaz", "degerler.varyant", None,
               "degerler.secilenleri_onayla", "degerler.tumunu_sec", None,
               "degerler.tum_sayfa", "degerler.sonraki_kontrol")

    def context_menu(self, pos):
        """The right-click menu of a row: its commands with their keys (from the registry)."""
        from PySide6.QtWidgets import QMenu

        index = self.table.indexAt(pos)
        if not index.isValid() or self.window_ is None:
            return None
        if not self.table.selectionModel().isRowSelected(index.row(), QModelIndex()):
            self.table.setCurrentIndex(index)
        menu = QMenu(self)
        menu.setAccessibleName("Değer komutları")
        for action_id in self.CONTEXT:
            if action_id is None:
                menu.addSeparator()
            else:
                menu.addAction(self.window_.registry.action(action_id))
        return menu

    def _context_menu(self, pos) -> None:
        menu = self.context_menu(pos)
        if menu is not None:
            menu.exec(self.table.viewport().mapToGlobal(pos))
            menu.deleteLater()

    def _make_zoom(self, prefs) -> None:
        from evrakci.ui.zoomview import ZoomController

        if self.zoom is not None:
            self.zoom.deleteLater()
        stored = prefs.zoom(ZOOM_KEY, 0) if prefs is not None else 0
        self.zoom = ZoomController(self.side.source.view, prefs, ZOOM_KEY, 50, 400, 25,
                                   self._fit_zoom)
        if not stored:
            self.zoom.set_zoom(ZOOM_DEFAULT, save=False)
        self.zoom.zoom_changed.connect(self.side.source.view.set_zoom)
        self.side.source.view.set_zoom(self.zoom.zoom())
        for button, method in ((self.side.source.zoom_out, "zoom_out"),
                               (self.side.source.zoom_in, "zoom_in")):
            try:
                button.clicked.disconnect()
            except (RuntimeError, TypeError):
                pass
            button.clicked.connect(getattr(self.zoom, method))

    def _fit_zoom(self) -> int | None:
        """Ctrl+0: the box fills the well's width."""
        view = self.side.source.view
        crop = view.crop
        if crop is None or crop.box is None:
            return None
        width_mm = crop.box[2] - crop.box[0]
        room = view.paper_rect().width() - 96 - 16
        return int(room / max(1.0, width_mm) / (96 / 25.4) * 100)

    def _toaster(self):
        return getattr(self.window_, "toaster", None)

    def _restyle(self) -> None:
        self.dismiss_button.setIcon(make_icon("x"))
        self._update_status()

    # -- refresh ------------------------------------------------------------------------
    def _watch(self, controller: JobController | None) -> None:
        if controller is self._watched:
            return
        if self._watched is not None:
            try:
                self._watched.job_changed.disconnect(self._job_changed)
            except (RuntimeError, TypeError):
                pass
        self._watched = controller
        if controller is not None:
            controller.job_changed.connect(self._job_changed)

    def _job_changed(self) -> None:
        if self.isVisible():
            self._refresh_timer.start(0)
        else:
            self._dirty = True

    def _deferred_refresh(self) -> None:
        if not self._filling:
            self.refresh()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._try_attach()
        if self._dirty:
            self.refresh()

    def _commit_open_editor(self) -> bool:
        """Store text still being typed, so a refresh never throws it away. True when an
        editor was open."""
        if not self.table.is_editing():
            return False
        editor = self.table.open_editor_widget()
        if editor is not None:
            if editor.isModified():
                self.table.commitData(editor)
            self.table.hint.hide()
            self.table.closeEditor(editor, QAbstractItemDelegate.EndEditHint.NoHint)
        return True

    def refresh(self) -> None:
        if self._filling:
            return
        self._refresh_timer.stop()
        self._dirty = False
        reopen = self._commit_open_editor()
        self._refresh_timer.stop()  # the commit above already counts
        keep = self.current_value()
        self._filling = True
        try:
            self._fill()
        finally:
            self._filling = False
        if keep is not None:
            self.select_value(keep[0], keep[1])
        if not self.table.currentIndex().isValid():
            self._select_first()
        if reopen and self.table.currentIndex().isValid():
            self.table.open_editor(self.table.currentIndex())
        self._describe()
        self._sync_actions()
        self._update_status()

    def _fill(self) -> None:
        controller = self.controller()
        self._watch(controller)
        if controller is None:
            self.rows, self.template_rows = [], []
            self._job_id = ""
            self._set_templates([])
            self.model.set_content([], [], False)
            self.selector.set_counts({v: 0 for v in VIEW_NAMES})
            self._show_empty("folder", "Henüz açık iş yok",
                             "Değerler, açık bir işin şablonlu belgelerinden okunur.",
                             ("Yükle'ye git", "upload", lambda: self.go_tab.emit("yukle")))
            return
        job = controller.job
        if job.id != self._job_id:
            self._job_id = job.id
            self.images.clear()
            self._template_id = None
        templates = self.templates()
        self._files = controller.store.batch_files(job)
        self._rotations = dict(job.rotations)
        self.rows = build_rows_fast(job, controller.documents(), templates)
        ids = []
        for row in self.rows:
            if row.template_id not in ids:
                ids.append(row.template_id)
        self._set_templates([(tid, templates.get(tid)) for tid in ids])
        template_id = self.template_combo.currentData()
        self.template_rows = [r for r in self.rows if r.template_id == template_id]
        template = templates.get(template_id) if template_id else None
        counts = count(self.template_rows)
        sample = self._samples.get(job.id, [])
        self.selector.set_counts({"kontrol": counts.kontrol, "incelenmemis": counts.unreviewed,
                                  "tumu": counts.values, "ornek": len(sample)})
        query = self.search.text().strip()
        if self._view == "ornek":
            items = self._sample_items(sample)
            items = [(r, c) for r, c in items if matches(r, query)]
            columns = SAMPLE_COLUMNS
        else:
            nothing_read = not any(r.read for r in self.rows)
            items = [] if nothing_read else [(r, None) for r in self.template_rows
                                             if in_view(r, self._view) and matches(r, query)]
            variables = [(v.key, v.name) for v in template.variables] if template else []
            columns = main_columns(self.template_rows, variables)
        self.model.set_content(columns, items, self._view == "ornek")
        self._restore_header(template_id)
        self._update_search_hint(template)
        shown = self._view != "ornek" and bool(ids)
        if self.template_combo.isHidden() == shown:
            self.template_combo.setVisible(shown)
            self.header_bar.refit()
        # Which body: the table, or an empty state in the same card
        if not self.rows:
            self._show_empty("layout-template", "Şablonlu belge yok",
                             "Kontrol'de belgelere şablon uygulayınca değerler burada okunur.",
                             ("Kontrol'e git", "layout-grid", lambda: self.go_tab.emit("kontrol")),
                             ("Şablonlar'a git", "stamp", lambda: self.go_tab.emit("sablonlar")))
        elif not any(r.read for r in self.rows):
            names = [tr_lower(display_name(v.name)) for v in template.variables[:3]] \
                if template else []
            listed = joined(names) if names else "değerler"
            self._show_empty("scan-text", "Değerler henüz okunmadı",
                             f"Okuyunca {listed} burada listelenir.",
                             (f"{len(self.rows)} belgeyi oku", "scan-text",
                              lambda: self.read_values(only_missing=False)),
                             ("Şablonlar'a git", "stamp", lambda: self.go_tab.emit("sablonlar")),
                             "Elle yazdıklarınız yeniden okumada korunur.")
        elif not items and query:
            self._show_empty("search", "Aramayla eşleşen değer yok",
                             f"“{query}” hiçbir değerde geçmiyor. Başka bir sözcük deneyin.",
                             ("Aramayı temizle", "x", self.search.clear))
        elif not items:
            title = {"kontrol": "Kontrol bekleyen değer yok",
                     "incelenmemis": "İncelenmemiş değer yok"}.get(self._view, "Değer yok")
            self._show_empty("circle-check", title,
                             "Bu şablonun bütün değerleri emin okundu ya da incelendi.",
                             ("Tümünü göster", "table", lambda: self.set_view("tumu")))
        else:
            self._show_table()
        self.search.setEnabled(any(r.read for r in self.rows))

    def _sample_items(self, sample: list[SampleItem]) -> list[tuple[Row, Cell | None]]:
        by_first = {r.document.page_ids[0]: r for r in self.rows}
        items = []
        for item in sample:
            row = by_first.get(item.first_page)
            cell = row.cell(item.key) if row is not None else None
            if cell is not None:
                items.append((row, cell))
        return items

    def _set_templates(self, found: list[tuple[str, Template | None]]) -> None:
        wanted = self._template_id
        ids = [tid for tid, _ in found]
        if wanted not in ids:  # the template with the most to check, else the first
            wanted = max(ids, key=lambda t: count(r for r in self.rows
                                                  if r.template_id == t).kontrol,
                         default=None) if ids else None
            if ids and count(r for r in self.rows if r.template_id == wanted).kontrol == 0:
                wanted = ids[0]
        self.template_combo.blockSignals(True)
        self.template_combo.clear()
        for tid, template in sorted(found, key=lambda f: f[1].name if f[1] else f[0]):
            self.template_combo.addItem(template.name if template else "Şablon bulunamadı", tid)
        self.template_combo.setCurrentIndex(max(0, self.template_combo.findData(wanted)))
        self.template_combo.blockSignals(False)
        self._template_id = self.template_combo.currentData()

    def _update_search_hint(self, template: Template | None) -> None:
        """A's "Firma, sicil no ara": the template's first two variables, words first."""
        if template is None:
            self._search_hints = ["Ara"]
            self._fit_search_hint()
            return
        kinds = {c.key: c.style for c in self.model.columns if c.kind == "var"}
        names = sorted(template.variables, key=lambda v: kinds.get(v.key, "code") != "text")
        shown = [display_name(v.name) for v in names[:2]]
        words = [shown[0]] + [tr_lower(n) for n in shown[1:]] if shown else []
        # Longest first; the first one that fits the field is shown, never an elided hint.
        self._search_hints = [f"{', '.join(words)} ara"] if len(words) > 1 else []
        self._search_hints += [f"{words[0]} ara"] if words else []
        self._search_hints += ["Değerlerde ara", "Ara"]
        self._fit_search_hint()

    def _fit_search_hint(self) -> None:
        hints = getattr(self, "_search_hints", ["Ara"])
        field = self.search
        room = field.width() - 2 * field.height() - theme.manager().size("s2")
        metrics = field.fontMetrics()
        if not field.isVisible():  # not laid out yet: the resize that follows fits it
            fitting = hints[0]
        else:
            fitting = next((h for h in hints if metrics.horizontalAdvance(h) <= room),
                           hints[-1])
        if field.placeholderText() != fitting:
            field.setPlaceholderText(fitting)

    def _show_empty(self, mark: str, title: str, text: str, primary=None, secondary=None,
                    note: str = "") -> None:
        self.empty.show_state(mark, title, text, primary, secondary, note)
        self.empty.show()
        self._header_key = ""  # the table's own widths come back with its rows
        header = self.table.horizontalHeader()
        self.table.setFixedHeight(header.sizeHint().height() + 1)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        header.setSortIndicatorShown(False)  # A's empty state: plain column names
        self._empty_widths()

    def _empty_widths(self) -> None:
        """No rows: every column as wide as its name, the rest to the flexible one."""
        from PySide6.QtGui import QFontMetrics

        m = theme.manager()
        metrics = QFontMetrics(m.font("caption-strong"))
        header = self.table.horizontalHeader()
        header.blockSignals(True)
        for c, column in enumerate(self.model.columns):
            width = 44 if column.kind == "review" else (
                metrics.horizontalAdvance(column.title) + 2 * m.size("s3") + m.size("s4"))
            header.resizeSection(c, width)
        header.blockSignals(False)
        self._fit_columns(empty=True)

    def _show_table(self) -> None:
        self.empty.hide()
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.horizontalHeader().setSortIndicatorShown(True)
        self._fit_columns()
        self.table.setMinimumHeight(0)
        self.table.setMaximumHeight(16777215)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    # Columns: A's widths, the flexible column takes the rest; remembered per template
    def _restore_header(self, template_id: str | None) -> None:
        key = "degerler/ornek" if self._view == "ornek" else f"degerler/{template_id or '-'}"
        signature = key + "|" + ",".join(c.kind + c.key for c in self.model.columns)
        if signature == self._header_key:
            self._fit_columns()
            return
        self._header_key = signature
        header = self.table.horizontalHeader()
        prefs = getattr(self.window_, "prefs", None)
        state = prefs.header_state(key) if prefs is not None else QByteArray()
        header.blockSignals(True)
        self._default_widths()
        restored = False
        if not state.isEmpty():
            restored = header.restoreState(state) and header.count() == len(self.model.columns)
        header.blockSignals(False)
        if restored:
            self.model.sort(header.sortIndicatorSection(), header.sortIndicatorOrder())
        else:
            column, order = self.model.sort_state()
            header.setSortIndicator(column, order)
        for c in range(header.count()):
            header.setSectionResizeMode(c, header.ResizeMode.Interactive)
        self._fit_columns()

    def _scale(self) -> float:
        return theme.manager().size("fs-body") / 15

    def _default_widths(self) -> None:
        """A's widths at this text size, wider where the values need it."""
        scale = self._scale()
        for c, column in enumerate(self.model.columns):
            kind = column.style if column.kind == "var" else column.kind
            width = round(WIDTHS.get(kind, 150) * scale)
            if column.kind in ("var", "pages", "doc"):
                width = max(width, self._content_width(c))
            self.table.setColumnWidth(c, width)

    def _content_width(self, column: int) -> int:
        from PySide6.QtGui import QFontMetrics

        m = theme.manager()
        style = self.model.columns[column].style
        font = m.font("value" if style == "code" else "num" if style in ("number", "date")
                      or self.model.columns[column].kind in ("doc", "pages") else "body")
        metrics = QFontMetrics(font)
        texts = [self.model.data(self.model.index(r, column)) or ""
                 for r in range(min(self.model.rowCount(), 400))]
        widest = max([metrics.horizontalAdvance(t) for t in texts] + [0])
        return widest + 2 * m.size("s3") + 2

    def _flex_column(self) -> int:
        columns = self.model.columns
        for c, column in enumerate(columns):
            if column.kind == "value" or (column.kind == "var" and column.style == "text"):
                return c
        values = [c for c, col in enumerate(columns) if col.kind in VALUE_KINDS]
        return values[0] if values else -1

    def _fit_columns(self, empty: bool = False) -> None:
        if not empty and not self.empty.isHidden():
            return
        flex = self._flex_column()
        if flex < 0:
            return
        header = self.table.horizontalHeader()
        others = sum(header.sectionSize(c) for c in range(header.count()) if c != flex)
        room = self.table.viewport().width() - others
        need = 0 if empty else max(120, self._content_width(flex))
        if not empty and need > room:
            # The flexible (text) column gives way before the table scrolls sideways, so
            # the Güven column at the right stays in view (GOAL §3.2's confidence marker,
            # PROPOSALS item 2): its long names wrap onto more lines and the row grows
            # (A's 150 % spec; ValuesTable.fit_rows), the full text is also in the tooltip.
            # Only when even its minimum does not fit does the table scroll, as A does.
            need = max(round(160 * self._scale()), room)
            over = others + need - self.table.viewport().width()
            if over > 0:  # still too wide: the other value columns give way down to a floor
                floor = round(110 * self._scale())
                for c, column in enumerate(self.model.columns):
                    if over <= 0 or c == flex or column.kind not in VALUE_KINDS:
                        continue
                    give = min(over, header.sectionSize(c) - floor)
                    if give > 0:
                        header.blockSignals(True)
                        header.resizeSection(c, header.sectionSize(c) - give)
                        header.blockSignals(False)
                        over -= give
        header.blockSignals(True)
        header.resizeSection(flex, max(need, room))
        header.blockSignals(False)

    def _header_moved(self, *_args) -> None:
        if not self._filling:
            self._header_timer.start()

    def _save_header(self) -> None:
        prefs = getattr(self.window_, "prefs", None)
        if prefs is None or not self._header_key:
            return
        prefs.set_header_state(self._header_key.split("|")[0],
                               self.table.horizontalHeader().saveState())

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        table = getattr(self, "table", None)
        if table is not None and obj is table.viewport() and event.type() == QEvent.Type.Resize:
            QTimer.singleShot(0, self._fit_columns)
        elif obj is self.search and event.type() == QEvent.Type.Resize:
            self._fit_search_hint()
        elif obj is self.search and event.type() == QEvent.Type.KeyPress and \
                event.key() == Qt.Key.Key_Escape and self.search.text():
            self.search.clear()
            return True
        return False

    # -- Ctrl+F and Ctrl+G ------------------------------------------------------------------
    def focus_search(self) -> None:
        """Ctrl+F: the table's search field, its text selected."""
        if self.search.isEnabled():
            self.search.setFocus(Qt.FocusReason.ShortcutFocusReason)
            self.search.selectAll()

    def go_to(self) -> None:
        """Ctrl+G: a document (Belge N) or a page; its row is selected in the table."""
        from evrakci.ui.kontrol_dialogs import GoToDialog

        if not self.rows:
            return
        current = self.model.row_at(self.table.currentIndex().row()) \
            if self.table.currentIndex().isValid() else None
        pages = max((r.last for r in self.rows), default=1)
        dialog = GoToDialog(max(r.number for r in self.rows), pages, "belge",
                            current.number if current is not None else 1, self)
        if not dialog.exec():
            return
        number = dialog.value()
        if dialog.kind() == "sayfa":
            row = next((r for r in self.rows if r.first <= number <= r.last), None)
            if row is None:
                self._say(f"Sayfa {number} şablonu olan bir belgede değil.")
                return
            number = row.number
        if not self.select_value(number, ""):
            self._say(f"Belge {number} bu görünümde yok.")
        self.table.setFocus()

    def _say(self, text: str) -> None:
        controller = self.controller()
        if controller is not None:
            controller.status.emit(text)

    # -- views and modes ------------------------------------------------------------------
    def view(self) -> str:
        return self._view

    def set_view(self, view: str) -> None:
        """Kontrol gerekenler / İncelenmemiş / Tümü / Örnek."""
        if view == "ornek" and not self._samples.get(self._job_id):
            return self.set_sample(True)
        if view != "ornek":
            self._main_view = view
            if self._view == "ornek":
                self._check_action("degerler.ornek_kontrol", False)
            if view != "incelenmemis" and self._review_all:
                self._review_all = False
                self._check_action("degerler.tumunu_incele", False)
        self._view = view
        self.selector.set_view(view)
        prefs = getattr(self.window_, "prefs", None)
        if prefs is not None and view != "ornek":
            prefs.set_view_state(VIEW_KEY, view)
        self.refresh()
        return None

    def set_review_all(self, on: bool = True) -> None:
        """Tümünü incele: every unreviewed value in turn, Emin ones too."""
        self._review_all = bool(on)
        self._check_action("degerler.tumunu_incele", self._review_all)
        if self._review_all:
            if self._view == "ornek":
                self._check_action("degerler.ornek_kontrol", False)
            self._view = "incelenmemis"
        elif self._view == "incelenmemis":
            self._view = self._main_view if self._main_view != "incelenmemis" else "tumu"
        self.selector.set_view(self._view)
        self.refresh()
        self._select_first()

    def set_sample(self, on: bool = True) -> None:
        """Örnek kontrol: 20 random Emin values, each confirmed or corrected by hand."""
        if on:
            if not self._samples.get(self._job_id):
                sample = draw_sample(self.rows, self._job_id or "evrakci", SAMPLE_SIZE)
                if not sample:
                    self._check_action("degerler.ornek_kontrol", False)
                    self._say("Örnek için emin okunmuş değer yok.")
                    return
                self._samples[self._job_id] = sample
                self._sample_done = False
            if self._review_all:
                self._review_all = False
                self._check_action("degerler.tumunu_incele", False)
            self._view = "ornek"
        elif self._view == "ornek":
            self._view = self._main_view
        self._check_action("degerler.ornek_kontrol", self._view == "ornek")
        self.selector.set_view(self._view)
        self.refresh()
        self._select_first()

    def _check_action(self, action_id: str, on: bool) -> None:
        if self.window_ is None:
            return
        action = self.window_.registry.action(action_id)
        if action.isChecked() != on:
            action.blockSignals(True)
            action.setChecked(on)
            action.blockSignals(False)
            action.changed.emit()

    def _template_picked(self, _index: int) -> None:
        self._template_id = self.template_combo.currentData()
        prefs = getattr(self.window_, "prefs", None)
        if prefs is not None and self._template_id:
            prefs.set_view_state(TEMPLATE_KEY, self._template_id)
        self.refresh()
        self._select_first()

    def _search_changed(self, _text: str) -> None:
        self.refresh()

    def _stepping_all(self) -> bool:
        return self._review_all or self._view == "ornek"

    def _hint_keys(self) -> list[tuple[str, str]]:
        nxt = "sonraki değer" if self._stepping_all() else "sonraki kontrol"
        return [("Enter", f"onayla, {nxt}"), ("Esc", "vazgeç")]

    # -- the current value ----------------------------------------------------------------
    def current_value(self) -> tuple[int, str] | None:
        """(document number, variable key) of the current cell."""
        index = self.table.currentIndex()
        if not index.isValid():
            return None
        row = self.model.row_at(index.row())
        cell = self._cell_for(index)
        return (row.number, cell.key) if row is not None and cell is not None else None

    def _cell_for(self, index: QModelIndex) -> Cell | None:
        """The value a row stands for: the current cell, else its first value to check."""
        if not index.isValid():
            return None
        cell = self.model.cell_at(index)
        if cell is not None:
            return cell
        row = self.model.row_at(index.row())
        if row is None or not row.cells:
            return None
        return next((c for c in row.cells if c.needs_check), row.cells[0])

    def cell(self, number: int, name: str) -> QModelIndex:
        """The table index of document `number`'s variable `name` (tests, links)."""
        row = next((r for r in self.rows if r.number == number), None)
        if row is None:
            return QModelIndex()
        cell = next((c for c in row.cells if c.name == name), None)
        return self.model.value_index(number, cell.key) if cell is not None else QModelIndex()

    def column_of(self, name: str) -> int:
        """The column of variable `name` in the main views."""
        return next(c for c, col in enumerate(self.model.columns)
                    if col.kind == "var" and col.title == display_name(name))

    def select_value(self, number: int, key: str) -> bool:
        index = self.model.value_index(number, key)
        if not index.isValid():
            row = self.model.row_of(number)
            if row < 0:
                return False
            index = self.model.index(row, max(0, self.table.currentIndex().column()))
        self.table.setCurrentIndex(index)
        self.table.scrollTo(index)
        return True

    def _select_first(self) -> None:
        """Start on the first value to check (or to review), else the first row."""
        target = self._find(-1, -1, 1, self._target_test())
        if target.isValid():
            self.table.setCurrentIndex(target)
            self.table.scrollTo(target)
        elif self.model.rowCount():
            columns = self.model.value_columns()
            self.table.setCurrentIndex(self.model.index(0, columns[0] if columns else 0))

    def _target_test(self, kontrol_only: bool = False) -> Callable[[Cell], bool]:
        if self._stepping_all() and not kontrol_only:
            return lambda c: c.value is not None and not c.reviewed
        return lambda c: c.needs_check

    def _find(self, row: int, column: int, step: int, test: Callable[[Cell], bool],
              wrap: bool = True) -> QModelIndex:
        """The next value cell after (row, column) in view order that passes `test`."""
        columns = self.model.value_columns()
        cells = [(r, c) for r in range(self.model.rowCount()) for c in columns]
        if step < 0:
            cells.reverse()
        before = [rc for rc in cells if (rc > (row, column) if step > 0 else rc < (row, column))]
        order = before + ([rc for rc in cells if rc not in before] if wrap else [])
        for r, c in order:
            index = self.model.index(r, c)
            cell = self.model.cell_at(index)
            if cell is not None and test(cell):
                return index
        return QModelIndex()

    def next_check(self, step: int = 1) -> None:
        """N / Shift+N: the next (previous) value that needs a check."""
        index = self.table.currentIndex()
        here = (index.row(), index.column()) if index.isValid() else (-1, -1)
        if step < 0 and not index.isValid():
            here = (self.model.rowCount(), 0)
        target = self._find(*here, step, self._target_test(kontrol_only=True))
        if target.isValid():
            self.table.setCurrentIndex(target)
            self.table.scrollTo(target)
            self.table.setFocus(Qt.FocusReason.ShortcutFocusReason)
        else:
            self._say("Kontrol bekleyen değer yok.")

    def _advance(self, number: int, row: int, column: int) -> None:
        """After an accept: the next value to look at, from where the accepted one was."""
        if self.model.row_at(row) is None or self.model.row_at(row).number != number:
            column = -1  # the row left this view: its successor took its place
        target = self._find(row, column, 1, self._target_test())
        if target.isValid():
            self.table.setCurrentIndex(target)
            self.table.scrollTo(target)
            return
        # Nothing left to check: Enter goes on to the next value nobody has reviewed, so a
        # second Enter is never a silent no-op, and the message says what is left.
        unreviewed = lambda c: c.value is not None and not c.reviewed  # noqa: E731
        left = sum(1 for r in range(self.model.rowCount()) for c in self.model.value_columns()
                   if (cell := self.model.cell_at(self.model.index(r, c))) is not None
                   and unreviewed(cell))
        target = self._find(row, column, 1, unreviewed)
        if target.isValid():
            self.table.setCurrentIndex(target)
            self.table.scrollTo(target)
            self._say(f"Kontrol gereken değer kalmadı; {left} değer incelenmedi. Enter "
                      "sıradakini onaylar.")
        else:
            self._say("Bu görünümdeki bütün değerler incelendi.")

    def _current_changed(self, *_args) -> None:
        self.table.viewport().update()
        if not self._filling:
            self._describe()
            self._sync_actions()
            self._update_status()

    # -- the side: crop, Okunan / Öneri, actions -----------------------------------------
    def _describe(self) -> None:
        index = self.table.currentIndex()
        row = self.model.row_at(index.row()) if index.isValid() else None
        cell = self._cell_for(index)
        side = self.side
        if row is None or cell is None:
            side.source.show_blank("Değer seçilmedi",
                                   "Okunan değerler burada kaynağıyla görünür.")
            side.set_blank(True)
            side.set_actions(False, False, False)
            return
        side.set_blank(False)
        page = row.page_of(cell)
        pid = row.document.page_ids[page]
        position = row.first + page
        meta = f"Belge {row.number}, sayfa {position}"
        if self._view == "ornek":
            sample = self._samples.get(self._job_id, [])
            number = next((i for i, s in enumerate(sample, start=1)
                           if s.first_page == row.document.page_ids[0] and s.key == cell.key), 0)
            meta += f", örnek {number} / {len(sample)}"
        crop = self._crop(row, cell, pid)
        side.source.show_crop(cell.title, meta, crop,
                              f"Kaynak kesiti: {cell.title}, {meta.lower()}")
        card = side.value
        if cell.value is None:
            card.show_value("okunmadı", "text-2")
            card.level.set("okunmadi", None)
        elif cell.needs_check:
            card.show_flagged(cell.text, cell.uncertain, cell.suggestion, cell.suggestion_marks)
            note = f"{len(cell.uncertain)} karakter belirsiz" if cell.uncertain else ""
            card.level.set(cell.level, cell.percent, note)
        else:
            card.show_value(cell.text or "boş", "text" if cell.text else "text-2")
            note = "İncelendi" if cell.reviewed else ""
            if self._view == "ornek":
                note = meta.split(", ")[-1].replace("örnek", "Örnek")
            card.level.set(cell.level, cell.percent, note)
        if self._view == "ornek" and cell.value is not None and not cell.needs_check:
            card.why.setText("Sayfadakiyle aynıysa onaylayın, değilse elle yazın. Örnekte bulunan "
                             "bir hata, aynı değişkenin bütün değerlerini Kontrol'e alır.")
        else:
            card.why.setText(cell.why() if not row.error else f"{cell.why()} {row.error}".strip())
        card.why.setVisible(bool(card.why.text()))
        side.relayout()
        # Onayla works on every read value: it accepts, confirms, or (already reviewed) moves on
        side.set_actions(cell.value is not None, row.read, row.template is not None)

    def _crop(self, row: Row, cell: Cell, pid: str) -> Crop:
        template = row.template
        box = None
        others = []
        page = row.page_of(cell)
        if template is not None:
            for variable in template.variables:
                if not variable.sections:
                    continue
                other = row.cell(variable.key)
                if variable.key == cell.key:
                    index = min(cell.source or 0, len(variable.sections) - 1)
                    box = variable.sections[index].box_mm
                elif other is not None and row.page_of(other) == page:
                    index = min(other.source or 0, len(variable.sections) - 1)
                    others.append((variable.key, display_name(variable.name),
                                   variable.sections[index].box_mm))
        return Crop(pid, box, tuple(others))

    def _box_clicked(self, key: str) -> None:
        """Crop → table: clicking another variable's box selects that value."""
        current = self.current_value()
        if current is not None:
            self.select_value(current[0], key)
            self.table.setFocus(Qt.FocusReason.MouseFocusReason)

    def _render_page(self, pid: str, dpi: int) -> QImage:
        """A page as an image (any thread): the scan, rotated as the user rotated it."""
        batch_id, page = parse_page_id(pid)
        image = render_page(self._files[batch_id], page, self._rotations.get(pid, 0), dpi=dpi)
        return to_qimage(image)

    # Space: the whole page in the loupe
    def toggle_whole_page(self, *_args) -> None:
        from evrakci.ui.loupe import Loupe

        if self.loupe is not None and self.loupe.is_open():
            self.loupe.close_loupe()
            return
        index = self.table.currentIndex()
        row = self.model.row_at(index.row()) if index.isValid() else None
        cell = self._cell_for(index)
        if row is None:
            return
        if self.loupe is None:
            self.loupe = Loupe(self, getattr(self.window_, "prefs", None))
        pages = row.document.page_ids

        def render(i: int, size: QSize) -> QPixmap:
            dpi = max(24, round(150 * size.height() / 1754))
            try:
                image = self._render_page(pages[i], dpi)
            except (OSError, KeyError, pdfium.PdfiumError):
                return QPixmap()
            return QPixmap.fromImage(image).scaled(size, Qt.AspectRatioMode.KeepAspectRatio,
                                                   Qt.TransformationMode.SmoothTransformation)

        self.loupe.open(len(pages), render, row.page_of(cell) if cell else 0,
                        lambda i: f"Belge {row.number}, sayfa {row.first + i}")

    # -- fixing values --------------------------------------------------------------------
    def accept_current(self, *_args) -> None:
        """Enter: accept the suggestion (or confirm what was read), mark it İncelendi and go
        to the next value to check. An unreadable value opens the editor instead."""
        controller = self.controller()
        index = self.table.currentIndex()
        row = self.model.row_at(index.row()) if index.isValid() else None
        cell = self._cell_for(index)
        if controller is None or row is None or cell is None or self.table.is_editing():
            return
        if cell.level == "okunamadi" or (cell.value is None and row.read):
            self.type_current()
            return
        if cell.value is None:
            return
        anchor = (row.number, index.row(), self.model.value_index(row.number, cell.key).column())
        if not cell.reviewed or cell.value.flagged:
            text = "Öneriyi kabul et" if cell.value.flagged else UNDO_TEXT
            controller.run(text, lambda job: confirm(job, row.document, cell.key))
            self.refresh()
            self._sample_progress()
        self._advance(*anchor)

    def accept_selected(self, *_args) -> None:
        """Ctrl+Enter: confirm every value in the selected rows, as one undoable step."""
        controller = self.controller()
        rows = sorted({i.row() for i in self.table.selectionModel().selectedRows()})
        if controller is None or not rows:
            return
        targets = []
        for r in rows:
            row, sampled = self.model.items[r]
            for cell in ([sampled] if sampled is not None else row.cells):
                if cell.value is None or cell.reviewed and not cell.value.flagged:
                    continue
                targets.append((row, cell))
        doable = [(r, c) for r, c in targets if not c.value.flagged or c.suggestion]
        skipped = len(targets) - len(doable)
        if not doable:
            self._say("Seçili satırlarda onaylanacak değer yok.")
            return

        def apply(job) -> None:
            for row, cell in doable:
                confirm(job, row.document, cell.key)

        before = controller.undo_stack.index()
        controller.run(f"{len(doable)} değeri onayla", apply)
        self.refresh()
        message = f"{len(doable)} değer onaylandı"
        if skipped:
            message += f"; okunamayan {skipped} değer atlandı"
        self._toast(message, controller, before + 1, "success")
        self._sample_progress()

    def _toast(self, text: str, controller: JobController, index: int, kind: str) -> None:
        """A completed event with Geri al (only while that step is still the last one)."""
        def undo() -> None:
            if controller.undo_stack.index() == index:
                controller.undo_stack.undo()

        toaster = self._toaster()
        if toaster is not None:
            toaster.show(text, "Geri al", undo, kind=kind, timeout_ms=10000)
        else:
            self._say(text)

    def type_current(self, *_args) -> None:
        """F2: edit the value in place."""
        index = self.table.currentIndex()
        if not index.isValid():
            return
        if self.model.cell_at(index) is None:
            cell = self._cell_for(index)
            row = self.model.row_at(index.row())
            if cell is None or row is None:
                return
            index = self.model.value_index(row.number, cell.key)
        self.table.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self.table.open_editor(index)

    def _apply_edit(self, row: Row, key: str, text: str) -> None:
        """A value typed in the table (Enter, Tab, or leaving the editor)."""
        controller = self.controller()
        if controller is None:
            return
        item = None
        if self._view == "ornek":
            item = next((s for s in self._samples.get(self._job_id, [])
                         if s.first_page == row.document.page_ids[0] and s.key == key), None)
        if item is not None and " ".join(text.split()) != item.text:
            self._sample_error(controller, row, key, text)
            return
        cell = row.cell(key)
        if cell is not None and cell.value is not None and text == cell.edit_text() and (
                not cell.value.flagged or cell.suggestion):
            # Enter on what the editor showed: confirm it, like Onayla (keeps the Güven %)
            controller.run("Öneriyi kabul et" if cell.value.flagged else UNDO_TEXT,
                           lambda job: confirm(job, row.document, key))
            return
        controller.set_value(row.document, key, text)

    def _sample_error(self, controller: JobController, row: Row, key: str, text: str) -> None:
        """An error found in the sample: correct it and send the variable's other values that
        nobody has looked at to Kontrol."""
        from evrakci.pipeline.review import set_value

        name = display_name(next((c.name for c in row.cells if c.key == key), key))
        documents = [r.document for r in self.rows
                     if r.template_id == row.template_id and r is not row]
        flagged = []

        def apply(job) -> None:
            set_value(job, row.document, key, text)
            flagged.append(flag_variable(job, documents, key))

        before = controller.undo_stack.index()
        controller.run(f"Örnekte hata: {name}", apply)
        moved = flagged[0] if flagged else 0
        self._toast(f"Örnekte hata: {moved} {tr_lower(name)} değeri Kontrol'e alındı", controller,
                    before + 1, "kontrol")

    def _editor_closed(self, submitted: int) -> None:
        """The editor's Enter: the value is stored, so move on like Onayla does."""
        if not submitted:
            return
        index = self.table.currentIndex()
        row = self.model.row_at(index.row()) if index.isValid() else None
        if row is None:
            return
        anchor = (row.number, index.row(), index.column())
        self.refresh()
        self._sample_progress()
        self._advance(*anchor)

    def _draw_variant(self) -> None:
        index = self.table.currentIndex()
        row = self.model.row_at(index.row()) if index.isValid() else None
        cell = self._cell_for(index)
        if row is not None and cell is not None:
            self.draw_variant.emit(row.number, cell.name)

    def dismiss(self, *_args) -> None:
        """Esc (Vazgeç): close the page view, else drop a multi-row selection."""
        if self.loupe is not None and self.loupe.is_open():
            self.loupe.close_loupe()
            return
        current = self.table.currentIndex()
        if current.isValid() and len(self.table.selectionModel().selectedRows()) > 1:
            self.table.selectionModel().clearSelection()
            self.table.selectRow(current.row())
            self.table.setCurrentIndex(current)

    def select_all(self, *_args) -> None:
        self.table.selectAll()

    def _sample_progress(self) -> None:
        """When the last sample value is looked at: say how it went."""
        if self._view != "ornek":
            return
        items = self._sample_items(self._samples.get(self._job_id, []))
        if items and all(c.reviewed for _, c in items) and not getattr(self, "_sample_done",
                                                                       False):
            self._sample_done = True
            errors = self._sample_errors()
            self._say(f"Örnek kontrol bitti: {len(items)} değer, {errors} hata.")

    def _sample_errors(self) -> int:
        sample = self._samples.get(self._job_id, [])
        by_first = {r.document.page_ids[0]: r for r in self.rows}
        errors = 0
        for item in sample:
            row = by_first.get(item.first_page)
            cell = row.cell(item.key) if row is not None else None
            if cell is not None and cell.reviewed and cell.text != item.text:
                errors += 1
        return errors

    def _say(self, text: str) -> None:
        """A short note that needs no action: a toast in the window, else the status signal."""
        toaster = self._toaster()
        if toaster is not None:
            toaster.show(text, kind="info")
        self.status.emit(text)

    # -- actions and the status bar -------------------------------------------------------
    def _sync_actions(self) -> None:
        has_job = self.controller() is not None
        read_any = any(r.read for r in self.rows)
        busy = self.task is not None
        self.read_button.setEnabled(has_job and bool(self.rows) and not busy)
        self.missing_button.setEnabled(has_job and read_any and not busy)
        if self.window_ is None:
            return
        r = self.window_.registry
        index = self.table.currentIndex()
        cell = self._cell_for(index)
        row = self.model.row_at(index.row()) if index.isValid() else None
        has_rows = self.model.rowCount() > 0
        counts = count(self.rows)
        state = {
            "degerler.onayla": self.side.accept_button.isEnabled(),
            "degerler.secilenleri_onayla": has_rows and bool(
                self.table.selectionModel().selectedRows()),
            "degerler.elle_yaz": row is not None and row.read and cell is not None,
            "degerler.varyant": row is not None and row.template is not None,
            "degerler.vazgec": has_rows,
            "degerler.tumunu_sec": has_rows,
            "degerler.tum_sayfa": row is not None,
            "degerler.sonraki_kontrol": counts.kontrol > 0,
            "degerler.onceki_kontrol": counts.kontrol > 0,
            "degerler.tumunu_incele": read_any,
            "degerler.ornek_kontrol": read_any,
            "degerler.durdur": busy,
        }
        for action_id, enabled in state.items():
            r.set_enabled(action_id, enabled)

    def _update_status(self) -> None:
        items = self._status_items
        if not items:
            return
        controller = self.controller()
        for item in items.values():
            item.hide()
        if controller is None:
            return
        total = len(controller.documents())
        current = self.table.currentIndex()
        row = self.model.row_at(current.row()) if current.isValid() else None
        if self.rows and not any(r.read for r in self.rows):
            items["unread"].set("", str(len(self.rows)), " belgede şablon var, değer okunmadı")
            items["unread"].show()
            return
        if not self.rows:
            return
        number = row.number if row is not None else self.rows[0].number
        items["doc"].set("Belge ", str(number), f" / {total}")
        items["doc"].show()
        if self._view == "ornek":
            sample = self._sample_items(self._samples.get(self._job_id, []))
            seen = sum(1 for _, c in sample if c.reviewed)
            items["sample"].set("Örnek kontrol: ", str(seen), f" / {len(sample)} incelendi")
            items["errors"].set("", str(self._sample_errors()), " hata")
            items["sample"].show()
            items["errors"].show()
            return
        counts = count(self.rows)
        if counts.kontrol:
            items["kontrol"].set("", str(counts.kontrol), " değer kontrol bekliyor")
            items["kontrol"].show()
        if counts.okunamadi:
            items["bad"].set("", str(counts.okunamadi), " okunamadı")
            items["bad"].show()
        items["seen"].set("", str(counts.reviewed), f" / {counts.values} incelendi")
        items["seen"].show()

    # -- reading values in the background -------------------------------------------------
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
            self._show_message(f"Okunamadı: {reason}", "triangle-alert", "check-text")
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
        return len(self._results)

    def _progress(self, done: int, total: int) -> None:
        self.progress.setRange(0, max(1, total))
        self.progress.setValue(done)
        self.progress_label.setText(f"Okunuyor: {done} / {total} belge")
        hint = "elle yazdıklarınız korunur"
        if 0 < done < total:
            left = (time.monotonic() - self._started) / done * (total - done)
            hint = (f"yaklaşık {max(1, round(left / 60))} dk kaldı, {hint}" if left >= 60
                    else f"bir dakikadan az kaldı, {hint}")
        self.progress_hint.setText(hint)
        taskbar = getattr(self.window_, "taskbar", None)
        if taskbar is not None:
            taskbar.set(done, max(1, total))

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
        count_ = self._store(results)
        self._finish(f"{count_} belge okundu.", "circle-check", "ok", toast=True)

    def _read_failed(self, message: str) -> None:
        self._finish(f"Okunamadı: {message}", "triangle-alert", "check-text")

    def _read_cancelled(self) -> None:
        count_ = self._store(self._results)
        self._finish(f"Okuma durduruldu: {count_} belge okundu ve kaydedildi, kalanlar okunmadı.",
                     "info", "icon", toast=True)

    def _finish(self, message: str, icon: str, colour: str, toast: bool = False) -> None:
        self.task = None
        taskbar = getattr(self.window_, "taskbar", None)
        if taskbar is not None:
            taskbar.clear()
        self._set_busy(False)
        toaster = self._toaster()
        if toast and toaster is not None:
            self._dismiss()
            toaster.show(message, kind="success" if colour == "ok" else "info")
        else:
            self._show_message(message, icon, colour)
        self.refresh()
        window = self.window()
        if window is not None and not window.isActiveWindow():  # QOL 19: the OCR ended
            QApplication.alert(window, 0)
        self.finished.emit()

    def _show_message(self, message: str, icon: str, colour: str) -> None:
        """After a read (or a refusal) the band stays with one line until it is closed."""
        m = theme.manager()
        self.progress_icon.setPixmap(icons.pixmap(icon, m.hex(colour), m.size("icon-md")))
        self.progress_label.setText(message)
        self.progress_hint.setText("")
        self.progress_band.setVisible(True)

    def _dismiss(self) -> None:
        self.progress_label.setText("")
        self.progress_band.setVisible(False)

    def cancel(self, *_args) -> None:
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
        self._sync_actions()


__all__ = ["DegerlerScreen", "LEVELS", "build_rows_fast"]
