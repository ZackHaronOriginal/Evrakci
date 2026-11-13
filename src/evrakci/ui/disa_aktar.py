"""The Dışa Aktar screen (final-a/disa-aktar.html): write the named PDFs and index.xlsx, never
silently.

Left: the pre-flight ("Ön kontrol", graded engel / kontrol / eksik / bilgi) and the file names.
Right ("Ayarlar", F9): target folder, file-name pattern, options and the primary action. While
writing, a progress card sits on top and the settings are locked; afterwards the outcome card
offers Klasörü aç / index.xlsx'i aç / Dosya Gezgini'nde göster.

Only an engel stops the export. A kontrol never does: the file is written and flagged in
index.xlsx. The window's command bar, status bar slot, toasts and taskbar progress are used once
the screen sits in a MainWindow (`attach`).
"""

from __future__ import annotations

import dataclasses
import subprocess
import sys
import time
from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QByteArray, QEvent, QModelIndex, QPoint, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QGuiApplication, QKeySequence, QUndoCommand
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHeaderView,
    QMenu,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

from evrakci.pipeline.cuts import document_template
from evrakci.pipeline.export import plan_export
from evrakci.pipeline.exporting import ExportError, export_job, may_delete_after_export
from evrakci.pipeline.job import job_from_dict, job_to_dict
from evrakci.pipeline.naming import safe_filename
from evrakci.pipeline.ocr.engine import EngineUnavailable
from evrakci.pipeline.settings import DELETE_AFTER_EXPORT, SettingsError, load_settings
from evrakci.pipeline.templates.model import Template
from evrakci.ui import theme
from evrakci.ui.controller import JobController
from evrakci.ui.degerler_parts import StatusItem
from evrakci.ui.disa_aktar_banners import OutcomeBanner, RunBanner
from evrakci.ui.disa_aktar_model import (
    FileRow,
    Finding,
    file_rows,
    findings,
    folder_state,
    pattern_problem,
    summarize,
)
from evrakci.ui.disa_aktar_parts import EmptyPane, HeadBar, PartsButton, PreflightCard, scale
from evrakci.ui.disa_aktar_side import SidePanel, mark_invalid, side_width
from evrakci.ui.disa_aktar_table import NAME_MIN, WIDTHS, WIDTHS_150, FilesModel, FilesTable
from evrakci.ui.feedback import announce
from evrakci.ui.workers import Task, start

STAGES = {"write": "dosyalar yazılıyor", "layer": "metin katmanı ekleniyor"}
HEADER_KEY = "disa_aktar/dosyalar"
SPLITTER_NAME = "disa_aktar"
STOP_HINT = ("Durdur (Ctrl+.) ile durdurursanız yazılan dosyalar kalır, index.xlsx yazılmaz.")


def open_path(path: Path) -> None:
    """Open a file or folder with the system's default app."""
    QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))


def reveal_path(path: Path) -> None:
    """Show `path` in the file manager: selected in Explorer on Windows, else its folder."""
    if sys.platform == "win32" and path.is_file():
        subprocess.Popen(["explorer", f"/select,{path}"])  # noqa: S603, S607
    else:
        open_path(path if path.is_dir() else path.parent)


class _PatternChange(QUndoCommand):
    """"Dosya adı kalıbı" as one undoable edit (Ctrl+Z names it in the Geri al tooltip)."""

    def __init__(self, screen: DisaAktarScreen, job_id: str, before: str, after: str) -> None:
        super().__init__("Dosya adı kalıbı")
        self._screen, self._job_id, self._before, self._after = screen, job_id, before, after
        self._first = True

    def redo(self) -> None:
        if self._first:  # already applied when the command is pushed
            self._first = False
            return
        self._screen._set_pattern(self._job_id, self._after)

    def undo(self) -> None:
        self._screen._set_pattern(self._job_id, self._before)


class DisaAktarScreen(QWidget):
    finished = Signal()
    job_deleted = Signal()
    go_tab = Signal(str)

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
        self.window_ = None
        self.task: Task | None = None
        self.out_dir: Path | None = None
        self._exporting: tuple[JobController, object] | None = None
        self._written = False  # the table shows what was written, not the preview
        self._written_for: JobController | None = None
        self._written_rows: list[FileRow] = []
        self._outcome: dict | None = None  # the outcome card's content (done / stopped / failed)
        self._index_written = False
        self._stage = "write"
        self._stage_seen: str | None = None
        self._stage_started = 0.0
        self._with_layer = True
        self._overrides: dict[str, str] = {}  # job id -> the user's file-name pattern
        self._default_pattern = ""
        self._multi_pattern = False
        self._variables: list[str] = []
        self._items: list = []
        self._rows: list[FileRow] = []
        self._summary = summarize([], [])
        self._findings: list[Finding] = []
        self._shown_findings: list[Finding] | None = None
        self._shown_rows: list[FileRow] | None = None
        self._folder = folder_state("")
        self._folder_touched = False
        self._problem: tuple[str, list[str]] = ("", [])
        self._job_name = ""
        self._pending_pattern = ""
        self._state = "empty"
        self._syncing = False
        self._header_loaded = False
        self.status_items: dict[str, StatusItem] = {}

        m = theme.manager()
        root = QVBoxLayout(self)
        root.setContentsMargins(m.size("s3"), 0, m.size("s3"), m.size("s3"))
        root.setSpacing(0)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setObjectName(SPLITTER_NAME)
        self.splitter.setChildrenCollapsible(False)
        root.addWidget(self.splitter, 1)

        # Left: banners, Ön kontrol, Dosya adları
        left = QWidget()
        col = QVBoxLayout(left)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(m.size("s3"))
        self.run_banner = RunBanner()
        self.run_banner.hide()
        self.outcome = OutcomeBanner()
        self.outcome.hide()
        self.outcome.open_folder.connect(lambda: self._open_out(self.out_dir))
        self.outcome.open_index.connect(self.open_index)
        self.outcome.reveal.connect(self.reveal_in_explorer)
        self.outcome.closed.connect(self.dismiss_outcome)
        self.message = self.outcome.message  # the sentence of the outcome card
        self.preflight = PreflightCard()
        self.preflight.action.connect(self._finding_action)
        self.files_card = QFrame()
        self.files_card.setProperty("kind", "table-card")
        self.files_card.setAccessibleName("Dosya adları")
        card = QVBoxLayout(self.files_card)
        card.setContentsMargins(1, 1, 1, 1)
        card.setSpacing(0)
        self.files_head = HeadBar("Dosya adları", "kontrol gerekenler üstte")
        self.filter_button = PartsButton("Yalnızca kontrol gerekenler", "list-filter", "0")
        self.filter_button.setCheckable(True)
        self.filter_button.toggled.connect(self._filter_toggled)
        self.files_head.add_widget(self.filter_button)
        card.addWidget(self.files_head)
        self.model = FilesModel(self)
        self.results = FilesTable()
        self.results.setModel(self.model)
        self.results.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.results.customContextMenuRequested.connect(self._row_menu)
        self.results.copy_requested.connect(self.copy_names)
        self.results.viewport().installEventFilter(self)
        theme.bind_style(self.results, lambda: (
            f"QTableView {{ background: {theme.manager().hex('card')}; }}"
            f"QHeaderView::section {{ background: {theme.manager().hex('card')}; }}"))
        self.empty = EmptyPane()
        self.empty.go.clicked.connect(lambda: self.go_tab.emit("yukle"))
        self.stack_host = QWidget()
        # The list takes the room that is left; its own size hint must not push the column
        self.stack_host.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)
        self.stack = QStackedLayout(self.stack_host)
        self.stack.setContentsMargins(0, 0, 0, 0)
        self.stack.addWidget(self.results)
        self.stack.addWidget(self.empty)
        card.addWidget(self.stack_host, 1)
        col.addWidget(self.run_banner)
        col.addWidget(self.outcome)
        col.addWidget(self.preflight)
        col.addWidget(self.files_card, 1)
        # At large text the left column scrolls in its own area (A's 150 % renders), with the
        # file list keeping room for a few rows.
        self.left_scroll = QScrollArea()
        self.left_scroll.setWidgetResizable(True)
        self.left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.left_scroll.setStyleSheet("QScrollArea { background: transparent; border: 0; }")
        self.left_scroll.viewport().setAutoFillBackground(False)
        left.setAutoFillBackground(False)
        self.left_scroll.setWidget(left)
        self.splitter.addWidget(self.left_scroll)

        # Right: the settings (F9 toggles it)
        self.side = SidePanel()
        self.folder = self.side.folder
        self.layer = self.side.layer
        self.pattern = self.side.pattern
        self.export_button = self.side.export_button
        self.again_button = self.side.again_button
        self.splitter.addWidget(self.side)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        self.side.choose_clicked.connect(self.choose_folder)
        self.folder.textChanged.connect(self._folder_changed)
        self.folder.textEdited.connect(self._folder_edited)
        self.side.pattern_committed.connect(self._pattern_committed)
        self.side.pattern_edited.connect(self._pattern_edited)
        self.export_button.clicked.connect(self.export)
        self.again_button.clicked.connect(self.again)

        self._header_timer = QTimer(self)
        self._header_timer.setSingleShot(True)
        self._header_timer.setInterval(300)
        self._header_timer.timeout.connect(self._save_header)
        header = self.results.horizontalHeader()
        header.sectionResized.connect(lambda *_: self._header_timer.start())
        theme.follow(self, self._restyle, "screen")
        self.refresh()
        QTimer.singleShot(0, self._try_attach)

    # -- the window -----------------------------------------------------------------------
    def _try_attach(self) -> None:
        window = self.window()
        if self.window_ is None and window is not self and hasattr(window, "registry"):
            self.attach(window)

    def attach(self, window) -> None:
        """Hook this tab into its MainWindow: the registry actions the window does not wire
        itself, the extra command-bar button, the status bar slot, the remembered columns."""
        if self.window_ is window:
            return
        self.window_ = window
        r = window.registry
        r.connect("disa_aktar.yazdir", self.print_index)
        r.connect("disa_aktar.gezginde_goster", self.reveal_in_explorer)
        self.go_tab.connect(window.show_tab)
        # The window's own labels already say "96 belge  640 sayfa  7 belge kontrol bekliyor";
        # this tab adds the state after them.
        layout = window.status_slot("disa_aktar").layout()
        item = StatusItem(None, "icon")
        layout.addWidget(item)
        self.status_items["state"] = item
        layout.addStretch(1)
        r.connect("disa_aktar.index_ac", self.open_index)
        window.tabs.currentChanged.connect(lambda _i: self._sync_actions())
        r.action("app.disa_aktar").changed.connect(self._sync_actions)
        self._restore_header()
        self.refresh()

    def _toaster(self):
        return getattr(self.window_, "toaster", None)

    def _taskbar(self):
        return getattr(self.window_, "taskbar", None)

    def _prefs(self):
        return getattr(self.window_, "prefs", None)

    def _restyle(self) -> None:
        m = theme.manager()
        self.splitter.setHandleWidth(m.size("s3"))
        self.side.setMinimumWidth(min(side_width(), 320))
        self.splitter.setSizes([max(400, self.width() - side_width()), side_width()])
        self.results.horizontalHeader().setMinimumSectionSize(round(80 * scale()))
        self.files_card.setMinimumHeight(self.files_head.height() + m.size("header-h")
                                         + 2 * m.size("row-h") + 2)
        if not self._header_loaded or self._prefs() is None:
            self._default_widths()
        self._sync()

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        if obj is self.results.viewport() and event.type() == QEvent.Type.Resize:
            QTimer.singleShot(0, self._fit_columns)
        return False

    # -- columns --------------------------------------------------------------------------
    def _default_widths(self) -> None:
        header = self.results.horizontalHeader()
        header.blockSignals(True)
        header.setStretchLastSection(False)
        k = scale()
        widths = WIDTHS if k < 1.4 else WIDTHS_150
        for column, width in enumerate(widths):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Interactive)
            if width:
                header.resizeSection(column, width if k >= 1.4 else round(width * k))
        header.blockSignals(False)
        self._fit_columns()

    def _fit_columns(self) -> None:
        """The name column takes the room the others leave (at least NAME_MIN, and the table
        scrolls sideways when that is more than there is)."""
        header = self.results.horizontalHeader()
        others = sum(header.sectionSize(c) for c in (0, 2, 3))
        room = self.results.viewport().width() - others
        header.blockSignals(True)
        header.resizeSection(1, max(round(NAME_MIN * scale()), room))
        header.blockSignals(False)

    def _restore_header(self) -> None:
        prefs = self._prefs()
        if prefs is None:
            return
        self._default_widths()
        state = prefs.header_state(HEADER_KEY)
        header = self.results.horizontalHeader()
        if not state.isEmpty():
            header.blockSignals(True)
            if not (header.restoreState(state) and header.count() == 4):
                self._default_widths()
            for column in range(4):
                header.setSectionResizeMode(column, QHeaderView.ResizeMode.Interactive)
            header.blockSignals(False)
            self._fit_columns()
        self._header_loaded = True

    def _save_header(self) -> None:
        prefs = self._prefs()
        if prefs is not None and self._header_loaded:
            prefs.set_header_state(HEADER_KEY, self.results.horizontalHeader().saveState())

    # -- planning: what would be written ---------------------------------------------------
    def _effective(self, job, templates: dict, used: set[str]) -> dict:
        override = self._overrides.get(job.id, "")
        if not override:
            return templates
        return {**templates, **{i: dataclasses.replace(templates[i], filename_pattern=override)
                                for i in used}}

    def _plan(self, controller: JobController | None) -> None:
        self._items, self._rows = [], []
        self._variables = []
        self._default_pattern, self._multi_pattern = "", False
        self._problem = ("", [])
        if controller is None:
            self._job_name = ""
            self._summary = summarize([], [])
            return
        job = controller.job
        self._job_name = job.name
        templates = dict(self.templates())
        ids = [document_template(job, d)[0] for d in controller.documents()]
        used = {i for i in ids if i is not None and templates.get(i) is not None}
        patterns = {i: templates[i].filename_pattern for i in used}
        distinct = set(patterns.values())
        self._default_pattern = next(iter(distinct)) if len(distinct) == 1 else ""
        self._multi_pattern = len(distinct) > 1
        known = {v.name for i in used for v in templates[i].variables}
        self._variables = sorted(known, key=str.casefold)
        override = self._overrides.get(job.id, "")
        effective = self._effective(job, templates, used)
        self._items = plan_export(job, effective)
        per_item = {n + 1: (effective[i].filename_pattern if i in used else "")
                    for n, i in enumerate(ids)}
        self._rows = file_rows(job, self._items, per_item)
        self._summary = summarize(self._items, self._rows)
        if override:
            self._problem = pattern_problem(override, known)

    def refresh(self) -> None:
        controller = self.controller()
        if self.task is not None:
            self._sync()
            return
        if self._written and controller is not self._written_for:
            self._written = False  # another job is open: show its names again
            self._written_rows, self._outcome = [], None
        if not self._written:
            self._plan(controller)
            self._prefill_folder(controller)
            self._folder = folder_state(self.folder.text())  # the disk may have changed
        self._sync()

    def _prefill_folder(self, controller) -> None:
        """The default export folder of Ayarlar, until the user types one (it is usually full:
        the pre-flight then offers a new sub folder named after the job)."""
        prefs = self._prefs()
        if controller is None or self._folder_touched or self.folder.text() or prefs is None:
            return
        last = prefs.export_folder()
        if last:
            self.folder.setText(last)

    # -- the state ------------------------------------------------------------------------
    def _compute_state(self) -> str:
        if self.task is not None:
            return "running"
        if self._written:
            return "done"
        if not self._items:
            return "empty"
        if any(f.level == "engel" for f in self._findings):
            return "blocked"
        return "main"

    def busy(self) -> bool:
        return self.task is not None

    def folder_hint_text(self) -> str:
        """The line under the target folder field."""
        return self.side.folder_hint.text.text()

    def state(self) -> str:
        return self._state

    def _build_findings(self) -> list[Finding]:
        if not self._items:
            return [Finding("bilgi", "", "Belge, kontrol ve eksik değer denetimi iş açılınca "
                            "burada görünür.", None, count_text="–")]
        return findings(self._summary, self._folder, self._problem)

    def _sync(self) -> None:
        """Make every part show the current state (one place; cheap when nothing changed)."""
        if self._syncing:
            return
        self._syncing = True
        try:
            self._findings = self._build_findings()
            self._state = state = self._compute_state()
            self._sync_cards(state)
            self._sync_files(state)
            self._sync_side(state)
            self._sync_status(state)
            self._sync_window_counts()
            self._sync_actions()
        finally:
            self._syncing = False

    def _sync_cards(self, state: str) -> None:
        s = self._summary
        self.run_banner.setVisible(state == "running")
        showing = state in ("main", "blocked", "empty")
        self.outcome.setVisible(state == "done" or (showing and self._outcome is not None))
        if self.outcome.isVisibleTo(self) and self._outcome is not None:
            self.outcome.show_outcome(**self._outcome)
        self.preflight.setVisible(showing)
        if showing and self._findings != self._shown_findings:
            self._shown_findings = list(self._findings)
            caption = f"{s.documents} belge, {s.pages} sayfa" if s.documents else "belge yok"
            self.preflight.set_findings(self._findings, caption)

    def _sync_files(self, state: str) -> None:
        head, model = self.files_head, self.model
        if state == "empty":
            head.set_text("Dosya adları")
            self.filter_button.hide()
            self.stack.setCurrentWidget(self.empty)
            if self._shown_rows != []:
                self._shown_rows = []
                model.set_rows([], "preview")
            return
        self.stack.setCurrentWidget(self.results)
        mode = {"running": "run", "done": "written"}.get(state, "preview")
        rows = self._written_rows if state == "done" else self._rows
        if (rows, mode) != (self._shown_rows, model.mode) or state == "running" and \
                model.mode != "run":
            self._shown_rows = list(rows)
            model.set_rows(rows, mode)
        if state in ("running", "done"):
            folder = str(self.out_dir or "")
            head.set_text("Yazılan dosyalar", self._short_path(folder))
            head.label.setToolTip(folder)
            self.filter_button.hide()
        else:
            head.set_text("Dosya adları", "kontrol gerekenler üstte")
            head.label.setToolTip("")
            count = model.kontrol_count()
            self.filter_button.set_parts(trail=str(count))
            self.filter_button.setVisible(count > 0)
            if count == 0 and self.filter_button.isChecked():
                self.filter_button.setChecked(False)

    def _short_path(self, text: str) -> str:
        from PySide6.QtGui import QFontMetrics

        font = theme.manager().font("caption")
        return QFontMetrics(font).elidedText(text, Qt.TextElideMode.ElideMiddle,
                                             round(520 * scale()))

    def _sync_side(self, state: str) -> None:
        side = self.side
        has_job = bool(self._items) or self.controller() is not None
        running = state == "running"
        side.set_locked(running)
        side.choose_button.setEnabled(not running and has_job)
        side.variable_button.setEnabled(not running and bool(self._variables))
        # Folder: the line under the field
        text = self.folder.text().strip()
        if state == "empty" and self.controller() is None:
            side.folder_hint.set("İş açılınca klasör seçilebilir.", "info")
            mark_invalid(self.folder, False)
        elif state == "done" and self.out_dir is not None and text == str(self.out_dir):
            side.folder_hint.set(self._written_hint, "ok")
            mark_invalid(self.folder, False)
        elif self._folder_error:
            side.folder_hint.set("Bir hedef klasör seçin.", "err")
            mark_invalid(self.folder, True)
        else:
            tone = self._folder.tone
            side.folder_hint.set(self._folder.text, tone)
            mark_invalid(self.folder, self._folder.blocks)
        # Pattern
        self._sync_pattern(state)
        # The primary action
        blocked = [f for f in self._findings if f.level == "engel"]
        side.export_button.setVisible(state != "done")
        side.again_button.setVisible(state == "done")
        side.export_button.setEnabled(state == "main")
        if state == "blocked":
            n = len(blocked)
            words = {1: "Önce engeli giderin.", 2: "Önce iki engeli giderin."}
            side.note.set(words.get(n, f"Önce {n} engeli giderin."), "info")
            side.note.show()
            side.export_button.setAccessibleDescription(side.note.text.text())
        else:
            side.note.hide()
            side.export_button.setAccessibleDescription("")

    def _sync_pattern(self, state: str) -> None:
        side = self.side
        job_id = self._job_id()
        if not self.pattern.hasFocus():
            shown = self._overrides.get(job_id, "") or self._default_pattern
            if self.pattern.text() != shown:
                self.pattern.blockSignals(True)
                self.pattern.setText(shown)
                self.pattern.blockSignals(False)
        self.pattern.setPlaceholderText(
            "Şablondaki kalıplar kullanılır" if self._multi_pattern else "Kalıp yok")
        kind, unknown = self._problem
        side.set_variables(self._variables)
        if not self._items:
            side.pattern_hint.set("Değişkenler işin şablonlarından gelir.", "info")
            mark_invalid(self.pattern, False)
        elif kind == "unknown":
            first = f"“{unknown[0]}” değişkeni yok. Menüden seçin."
            side.pattern_hint.set(first, "err")
            mark_invalid(self.pattern, True)
        elif kind == "brace":
            side.pattern_hint.set("Süslü parantezler eşleşmiyor. Her { için bir } olmalı.", "err")
            mark_invalid(self.pattern, True)
        else:
            example = next((r for r in self._rows if r.state != "kontrol"),
                           self._rows[0] if self._rows else None)
            side.pattern_hint.set(f"Örnek: {example.name}" if example else "", "info")
            mark_invalid(self.pattern, False)

    def _job_id(self) -> str:
        controller = self.controller()
        return controller.job.id if controller is not None else ""

    def _sync_status(self, state: str) -> None:
        item = self.status_items.get("state")
        if item is None:
            return
        blocked = sum(1 for f in self._findings if f.level == "engel")
        if state == "empty":
            self._set_status(item, None, "icon", "İşler Yükle sekmesinde açılır (Ctrl+1)")
        elif state == "blocked":
            self._set_status(item, "ban", "danger", "", str(blocked), " engel var")
        elif state == "running":
            self._set_status(item, "loader-circle", "icon", "Yazılıyor: ", str(self._done_count),
                             f" / {self._total}")
        elif state == "done":
            self._set_status(item, "folder-check", "ok", "", str(len(self._written_rows)),
                             f" belge yazıldı, {self._finished_at}")
        elif self._folder.kind in ("ok", "other", "new"):
            self._set_status(item, "circle-check", "ok", "Hedef klasör yazılabilir")
        else:
            self._set_status(item, "info", "icon", "Hedef klasör seçilmedi")

    def _sync_window_counts(self) -> None:
        """The window's own job counts start this tab's line ("96 belge  640 sayfa  7 belge
        kontrol bekliyor"); with no job A's one line "İşler Yükle sekmesinde açılır" stands
        alone at the left edge."""
        window = self.window_
        if window is not None and hasattr(window, "set_status_counts"):
            window.set_status_counts("disa_aktar", self._state != "empty")

    @staticmethod
    def _set_status(item: StatusItem, icon: str | None, role: str, *parts: str) -> None:
        item.icon_name, item.role = icon, role
        item.icon.setVisible(bool(icon))
        item.set(*parts)

    # -- actions of the window -------------------------------------------------------------
    def _sync_actions(self) -> None:
        window = self.window_
        if window is None or getattr(self, "_syncing_actions", False):
            return
        self._syncing_actions = True
        try:
            r = window.registry
            state = self._state
            has_job = self.controller() is not None
            on_tab = window.current_tab() == "disa_aktar"
            can = state == "main" or (state == "done" and has_job)
            r.set_enabled("app.disa_aktar", has_job and (not on_tab or can))
            r.set_enabled("disa_aktar.durdur", state == "running")
            r.set_enabled("disa_aktar.yazdir", state != "empty" and self.model.rowCount() > 0)
            r.set_enabled("app.yenile", not on_tab or state not in ("empty", "running"))
            r.set_enabled("disa_aktar.gezginde_goster", self._reveal_target() is not None)
            r.set_enabled("disa_aktar.index_ac",
                          self._index_written and self._index_path().is_file())
        finally:
            self._syncing_actions = False

    def _index_path(self) -> Path:
        return (self.out_dir or Path()) / "index.xlsx"

    def _reveal_target(self) -> Path | None:
        if self.out_dir is not None and self.out_dir.exists() and (
                self._written or self._outcome is not None):
            index = self._index_path()
            return index if index.is_file() else self.out_dir
        text = self.folder.text().strip()
        if text and Path(text).is_dir():
            return Path(text)
        return None

    # -- folder and pattern ---------------------------------------------------------------
    _folder_error = False
    _written_hint = ""
    _done_count = 0
    _total = 0
    _finished_at = ""

    def _folder_edited(self, _text: str) -> None:
        self._folder_touched = True
        self._folder_error = False

    def _folder_changed(self, text: str) -> None:
        self._folder = folder_state(text)
        if text.strip():
            self._folder_error = False
        self._sync()

    def choose_folder(self) -> None:
        start = self.folder.text().strip()
        prefs = self._prefs()
        if not start and prefs is not None:
            start = prefs.export_folder()
        folder = QFileDialog.getExistingDirectory(self, "Boş bir klasör seçin", start)
        if folder:
            self._folder_touched = True
            self.folder.setText(folder)
            self.folder.setFocus(Qt.FocusReason.OtherFocusReason)

    def make_subfolder(self) -> Path | None:
        """"Yeni alt klasör oluştur": a new folder inside the full one, named after the job."""
        parent = Path(self.folder.text().strip())
        base = safe_filename(self._job_name) or "Dışa aktarım"
        target, number = parent / base, 1
        while target.exists():
            number += 1
            target = parent / f"{base} ({number})"
        try:
            target.mkdir(parents=True)
        except OSError as error:
            self.side.folder_hint.set(f"Alt klasör oluşturulamadı: {error.strerror or error}. "
                                      "Başka bir klasör seçin.", "err")
            return None
        self._folder_touched = True
        self.folder.setText(str(target))
        toaster = self._toaster()
        if toaster is not None:
            toaster.show(f"“{target.name}” klasörü oluşturuldu.", kind="info")
        return target

    def _pattern_edited(self) -> None:
        """Typing clears a shown error at once (it is shown again when the field is left)."""
        if self.pattern.property("invalid"):
            mark_invalid(self.pattern, False)

    def _pattern_committed(self, text: str) -> None:
        job_id = self._job_id()
        if not job_id:
            return
        text = text.strip()
        if text == self._default_pattern:
            text = ""  # the template's own pattern needs no override
        before = self._overrides.get(job_id, "")
        if text == before:
            self._sync_after_pattern()
            return
        self._set_pattern(job_id, text)
        controller = self.controller()
        if controller is not None:
            controller.undo_stack.push(_PatternChange(self, job_id, before, text))
        self._sync_after_pattern()

    def _sync_after_pattern(self) -> None:
        self._plan(self.controller())
        self._shown_findings = None
        self._sync()

    def _set_pattern(self, job_id: str, text: str) -> None:
        """The pattern of a job (also by undo and redo)."""
        if text:
            self._overrides[job_id] = text
        else:
            self._overrides.pop(job_id, None)
        if job_id == self._job_id() and self.task is None and not self._written:
            self.pattern.blockSignals(True)
            self.pattern.setText(text or self._default_pattern)
            self.pattern.blockSignals(False)
            self._sync_after_pattern()

    def pattern_text(self) -> str:
        """The pattern in force: the user's, else the templates' own."""
        return self._overrides.get(self._job_id(), "") or self._default_pattern

    # -- the links of the pre-flight --------------------------------------------------------
    def _finding_action(self, action: str) -> None:
        if action == "choose":
            self.choose_folder()
        elif action == "subfolder":
            self.make_subfolder()
        elif action == "pattern":
            self.pattern.setFocus(Qt.FocusReason.OtherFocusReason)
            self.pattern.selectAll()
        elif action == "next_check":
            self.go_tab.emit("kontrol")
            kontrol = getattr(self.window_, "kontrol", None)
            if kontrol is not None and hasattr(kontrol, "jump_to_check"):
                QTimer.singleShot(0, lambda: kontrol.jump_to_check(1))
        elif action == "values":
            self.go_tab.emit("degerler")
        elif action == "kontrol":
            self.go_tab.emit("kontrol")
        elif action == "show_names":
            self.show_changed_names()

    def show_changed_names(self) -> None:
        """"Adları göster": the first file whose name changed, selected in the list."""
        self.filter_button.setChecked(False)
        row = self.model.row_of(lambda r: r.state == "bilgi" and r.why.startswith(
            ("Ad çakışması", "Geçersiz karakter")))
        if row >= 0:
            self.results.selectRow(row)
            self.results.scrollTo(self.model.index(row, 1))
            self.results.setFocus(Qt.FocusReason.OtherFocusReason)

    def _filter_toggled(self, on: bool) -> None:
        self.model.set_filter(on)
        self.filter_button.setAccessibleName(
            f"Yalnızca kontrol gerekenler: {self.model.kontrol_count()}"
            + (" (açık)" if on else ""))

    # -- the list -------------------------------------------------------------------------
    def selected_names(self) -> list[str]:
        rows = sorted({i.row() for i in self.results.selectionModel().selectedRows()})
        return [r.name for r in (self.model.row_at(i) for i in rows) if r is not None]

    def copy_names(self) -> None:
        names = self.selected_names()
        if names:
            QGuiApplication.clipboard().setText("\n".join(names))

    def _row_menu(self, pos: QPoint) -> None:
        index = self.results.indexAt(pos)
        if not index.isValid():
            return
        if not self.results.selectionModel().isRowSelected(index.row(), QModelIndex()):
            self.results.selectRow(index.row())
        menu = QMenu(self.results)
        copy = menu.addAction("Dosya adını kopyala")
        copy.setShortcut(QKeySequence.StandardKey.Copy)
        copy.triggered.connect(self.copy_names)
        if self.model.mode == "written":
            show = menu.addAction("Dosya Gezgini'nde göster")
            show.triggered.connect(self.reveal_selected)
        menu.popup(self.results.viewport().mapToGlobal(pos))
        self._menu = menu

    def reveal_selected(self) -> None:
        names = self.selected_names()
        if names and self.out_dir is not None and (self.out_dir / names[0]).exists():
            reveal_path(self.out_dir / names[0])

    # -- export ---------------------------------------------------------------------------
    def export(self) -> None:
        controller = self.controller()
        if controller is None or self.task is not None:
            return
        if self._written:
            self.again()
            return
        self._plan(controller)
        self._folder = folder_state(self.folder.text())
        self._outcome = None
        self._sync()
        if self._state == "blocked":
            blocked = [f for f in self._findings if f.level == "engel"]
            toaster = self._toaster()
            if toaster is not None:
                toaster.show("Dışa aktarılamıyor: " + blocked[0].title, kind="info")
            return
        text = self.folder.text().strip()
        if not text:
            self._folder_error = True
            self._sync()
            self.folder.setFocus(Qt.FocusReason.OtherFocusReason)
            announce(self.side.folder_hint, "Bir hedef klasör seçin.")
            return
        out_dir = Path(text)
        controller.store.save(controller.job)  # marks the job as in use for the day limit
        # The worker gets its own copy: the live job can still be edited meanwhile.
        job = job_from_dict(job_to_dict(controller.job))
        files = controller.store.batch_files(job)
        self._exporting = (controller, job)
        templates = dict(self.templates())
        used = {i for i in (document_template(job, d)[0] for d in controller.documents())
                if i is not None and templates.get(i) is not None}
        templates = self._effective(job, templates, used)
        with_layer = self.layer.isChecked()
        self._with_layer = with_layer

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
                                  "“Metin katmanı ekle (OCR)” kutusunu kapatın.") from None

        self.out_dir = out_dir
        self._written, self._index_written = False, False
        self._stage, self._stage_seen = "write", None
        self._done_count, self._total = 0, len(self._items)
        self.task = Task(work)
        self.task.signals.progress.connect(self._progress)
        self.task.signals.done.connect(self._done)
        self.task.signals.failed.connect(self._failed)
        self.task.signals.cancelled.connect(self._cancelled)
        self.run_banner.start(STOP_HINT)
        self._shown_rows = None
        self._sync()
        taskbar = self._taskbar()
        if taskbar is not None:
            taskbar.indeterminate()
        start(self.task)

    def _progress(self, done: int, total: int) -> None:
        stage = self._stage
        if stage != self._stage_seen:
            self._stage_seen = stage
            self._stage_started = time.monotonic()
        percent = round(done * 100 / total) if total else 0
        sub = f"%{percent}"
        if 0 < done < total:
            left = (time.monotonic() - self._stage_started) / done * (total - done)
            sub += (f", yaklaşık {max(1, round(left / 60))} dk kaldı" if left >= 60
                    else ", bir dakikadan az kaldı")
        sub += f". {STOP_HINT}"
        self.run_banner.set_progress(done, total, STAGES.get(stage, ""), sub)
        self._done_count, self._total = done, total
        final = stage == "layer" or not self._with_layer
        self.model.set_progress(done, final)
        if stage == "layer" or not self._with_layer:
            overall, whole = done + (total if self._with_layer else 0), \
                total * (2 if self._with_layer else 1)
        else:
            overall, whole = done, total * 2
        taskbar = self._taskbar()
        if taskbar is not None:
            taskbar.set(overall, max(1, whole))
        self._sync_status(self._state)

    def _done(self, result) -> None:
        controller, job = self._exporting  # the job that was exported, not the open one
        names = [p.name for p in result.paths]
        self._written_rows = file_rows(job, result.items, {}, names)
        self._written = True
        self._written_for = controller
        self._index_written = result.index_written
        self._finished_at = datetime.now().strftime("%H:%M")
        self._written_hint = (f"Klasörde {len(names)} PDF"
                              + (" ve index.xlsx var." if result.index_written else " var."))
        try:
            retention = load_settings(self.settings_path).retention
        except SettingsError:
            retention = ""  # a broken settings file never deletes a job
        count = len(result.paths)
        kept = "İş listede kalır; Yükle'den yeniden açabilirsiniz."
        if retention == DELETE_AFTER_EXPORT and may_delete_after_export(result):
            controller.store.delete(job.id)
            kept = "İş silindi (saklama ayarı)."
            self.job_deleted.emit()
        elif retention == DELETE_AFTER_EXPORT and result.paths and not result.with_layer:
            kept = "İş saklandı: metin katmanı eklenmedi."
        check = ""
        if result.needing_check:
            check = (f"{result.needing_check} belge kontrol gerektiriyor; index.xlsx'te işaretli,"
                     " nedeni yazılı.")
        self._outcome = {
            "kind": "done", "title": f"{count} belge yazıldı",
            "message": f"{self.out_dir} klasörüne, {self._finished_at}'de bitti. {kept}",
            "check": check, "folder": True, "index": result.index_written, "reveal": True,
        }
        self._finish(f"{count} belge yazıldı", "kontrol" if result.needing_check else "success")

    def _failed(self, message: str) -> None:
        exists = self.out_dir is not None and self.out_dir.exists()
        self._outcome = {"kind": "failed", "title": "Dışa aktarma tamamlanamadı",
                         "message": message, "folder": exists, "closable": True}
        taskbar = self._taskbar()
        if taskbar is not None:
            taskbar.error()
            QTimer.singleShot(5000, taskbar.clear)
        self._finish("Dışa aktarma tamamlanamadı", None)

    def _cancelled(self) -> None:
        written = sorted(p.name for p in self.out_dir.glob("*.pdf")) if self.out_dir else []
        self._outcome = {
            "kind": "stopped", "title": "Dışa aktarma durduruldu",
            "message": f"Dışa aktarma durduruldu: {len(written)} dosya yazıldı, index.xlsx "
                       "yazılmadı. Yeniden dışa aktarmak için boş bir klasör seçin.",
            "folder": bool(written), "closable": True,
        }
        self._finish("Dışa aktarma durduruldu", "info")

    def _finish(self, toast: str, kind: str | None) -> None:
        self.task = None
        self._exporting = None
        taskbar = self._taskbar()
        if taskbar is not None and kind is not None:
            taskbar.clear()
        self._shown_rows = None
        self._shown_findings = None
        self.refresh()
        outcome = self._outcome
        if outcome is not None:
            announce(self.outcome, f"{outcome['title']}. {outcome['message']}")
            if self.isVisible():
                target = (self.outcome.folder_button if outcome.get("folder")
                          else self.again_button if self._written else self.export_button)
                target.setFocus(Qt.FocusReason.OtherFocusReason)
        toaster = self._toaster()
        if toaster is not None and kind is not None and self.window_ is not None:
            if self.window_.current_tab() != "disa_aktar" or kind == "info":
                toaster.show(toast, "Klasörü aç" if self.out_dir is not None and
                             self.out_dir.exists() else None,
                             lambda: self._open_out(self.out_dir),
                             kind="success" if kind == "success" else kind,
                             timeout_ms=10000)
        self.finished.emit()

    def cancel(self) -> None:
        if self.task is not None:
            self.task.cancel()
            self.run_banner.sub.setText("Durduruluyor; o ana kadar yazılanlar kalır…")

    def dismiss_outcome(self) -> None:
        self._outcome = None
        self._sync()
        self.export_button.setFocus(Qt.FocusReason.OtherFocusReason)

    def again(self) -> None:
        """"Yeniden dışa aktar…": back to the pre-flight, with the folder field in front (the
        folder just written is full, so the pre-flight asks for a new one)."""
        self._written, self._written_rows, self._outcome = False, [], None
        self._plan(self.controller())
        self._folder = folder_state(self.folder.text())
        self._shown_rows, self._shown_findings = None, None
        self._sync()
        self.folder.setFocus(Qt.FocusReason.OtherFocusReason)
        self.folder.selectAll()

    # -- open ----------------------------------------------------------------------------
    def _open_out(self, folder: Path | None) -> None:
        if folder is not None and Path(folder).exists():
            open_path(Path(folder))

    def open_index(self) -> None:
        if self._index_written and self._index_path().is_file():
            open_path(self._index_path())

    def reveal_in_explorer(self) -> None:
        target = self._reveal_target()
        if target is not None:
            reveal_path(target)

    # -- print ---------------------------------------------------------------------------
    def index_html(self) -> str:
        """The list as a printable table (what index.xlsx lists: name, pages, template, state)."""
        from html import escape

        rows = self.model._all
        head = "".join(f"<th align='left'>{escape(t)}</th>"
                       for t in ("Durum", "Dosya adı", "Sayfalar", "Şablon", "Not"))
        body = "".join(
            f"<tr><td>{escape(self.model.word(r))}</td><td>{escape(r.name)}</td>"
            f"<td align='right'>{escape(r.pages)}</td><td>{escape(r.template or 'Şablon yok')}"
            f"</td><td>{escape(r.why)}</td></tr>" for r in rows)
        return (f"<h2>{escape(self._job_name or 'Dışa aktarma')}</h2>"
                f"<p>{len(rows)} belge, {self._summary.pages} sayfa</p>"
                f"<table border='1' cellspacing='0' cellpadding='4' width='100%'>"
                f"<tr>{head}</tr>{body}</table>")

    def print_index(self, printer=None) -> None:
        """"Dizini yazdır…": the file list on paper (or to the printer given)."""
        from PySide6.QtGui import QTextDocument
        from PySide6.QtPrintSupport import QPrintDialog, QPrinter

        if self.model.rowCount() == 0:
            return
        if printer is None:
            printer = QPrinter()
            dialog = QPrintDialog(printer, self)
            dialog.setWindowTitle("Dizini yazdır")
            if dialog.exec() != QPrintDialog.DialogCode.Accepted:
                return
        document = QTextDocument()
        document.setHtml(self.index_html())
        document.print_(printer)

    # Compatibility for the window and old callers
    def header_state(self) -> QByteArray:
        return self.results.horizontalHeader().saveState()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._try_attach()
        self._sync_actions()
