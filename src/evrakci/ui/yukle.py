"""The Yükle screen (final-a/yukle.html): the batches of the open job, the pre-flight counts
and the way to Kontrol.

Left, the batch table (drag handles, Alt+Up / Alt+Down, Del; every move and removal is one
undoable edit of the job); reading progress sits under it. Right, the inspector (Ön kontrol,
Tarama profili, "Kontrol'e geç"). With no job open the page is the empty state with the job
search and the recent jobs. PDFs and folders dropped anywhere in the window show the `drop`
overlay and then create a job or add batches.

The window's command bar, status bar slot, taskbar and toasts are used once the screen sits in
a MainWindow (`attach`); on its own the screen still works (the tests do that).
"""

from __future__ import annotations

import os
import subprocess
import time
from collections.abc import Callable
from functools import partial
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, QRectF, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
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

from evrakci import __version__
from evrakci.pipeline import export
from evrakci.pipeline.analyze import count_pages
from evrakci.pipeline.job import Job, job_from_dict, job_to_dict
from evrakci.pipeline.store import JobFileError, JobStore
from evrakci.ui import theme
from evrakci.ui.chrome import ActionButton
from evrakci.ui.controller import JobController
from evrakci.ui.feedback import InfoBar
from evrakci.ui.widgets import StatusPart
from evrakci.ui.workers import Task, start
from evrakci.ui.yukle_info import JobSummary, ScanProfile, scan_profile, summarize
from evrakci.ui.yukle_parts import (
    PDF_LIMIT,
    DropOverlay,
    EmptyPage,
    JobEntry,
    ProgressCard,
    ago,
    default_folder,
    find_pdfs,
    thousands,
)
from evrakci.ui.yukle_side import Inspector
from evrakci.ui.yukle_table import BatchModel, BatchTable

HEADER_KEY = "yukle/partiler"
REPORT_EVERY = 0.1  # seconds between redraws of the progress while pages are read


def _heading_row() -> tuple[QWidget, QLabel, QLabel]:
    """A .thead-bar .pane-title: "Partiler" and its hint, baseline-aligned, 52 px high."""
    m = theme.manager()
    bar = QWidget()
    bar.setMinimumHeight(52)
    row = QHBoxLayout(bar)
    row.setContentsMargins(m.size("s4"), 0, m.size("s3"), 0)
    row.setSpacing(m.size("s2"))
    title = QLabel("Partiler")
    title.setFont(m.font("body-strong"))
    hint = QLabel("Sürükleyin ya da Alt+↑ / Alt+↓ ile sıralayın.")
    hint.setProperty("textRole", "secondary")
    hint.setStyleSheet(f"font-size: {m.size('fs-caption')}px;")
    row.addWidget(title, 0, Qt.AlignmentFlag.AlignBaseline)
    row.addWidget(hint, 0, Qt.AlignmentFlag.AlignBaseline)
    row.addStretch(1)
    return bar, title, hint


class _Dropline(QWidget):
    """A .dropline: a hairline, then the sentence about dropping files (caption, text-2)."""

    def __init__(self) -> None:
        super().__init__()
        m = theme.manager()
        self.setMinimumHeight(52)
        row = QHBoxLayout(self)
        row.setContentsMargins(m.size("s4"), 0, m.size("s4"), 0)
        row.setSpacing(m.size("s2"))
        self.icon = QLabel()
        self.icon.setFixedSize(16, 16)
        self.text = QLabel("PDF'leri pencerenin herhangi bir yerine bırakın ya da Dosya ekle… "
                           "(Ctrl+O). Klasörler de olur.")
        self.text.setProperty("textRole", "secondary")
        row.addStretch(1)
        row.addWidget(self.icon)
        row.addWidget(self.text)
        row.addStretch(1)
        self.setAccessibleName(self.text.text())
        theme.follow(self, self.refresh, "yukle-dropline")

    def refresh(self) -> None:
        from evrakci.ui import icons

        m = theme.manager()
        self.icon.setPixmap(icons.pixmap("upload", m.hex("icon"), 16))
        self.text.setStyleSheet(f"font-size: {m.size('fs-caption')}px;")

    def paintEvent(self, _event) -> None:  # noqa: N802
        QPainter(self).fillRect(QRectF(0, 0, self.width(), 1),
                                theme.manager().color("stroke-soft"))


class _Reading:
    """Bookkeeping of one read: which files, how many pages, and the speed so far."""

    def __init__(self, files: list[Path], pages: list[int] | None = None) -> None:
        self.files = files
        self.set_pages(pages if pages is not None else [0] * len(files))
        self.done = 0
        self.started = time.monotonic()
        self.shown = 0.0
        self.cancelling = False

    def set_pages(self, pages: list[int]) -> None:
        """The files' page counts (counted by the worker before it starts reading)."""
        self.pages = list(pages)
        self.total = sum(self.pages)

    def current(self) -> int:
        """Index of the file the `done`-th page belongs to."""
        end = 0
        for index, count in enumerate(self.pages):
            end += count
            if self.done < end:
                return index
        return len(self.pages) - 1

    def rate(self) -> float | None:
        elapsed = time.monotonic() - self.started
        return self.done / elapsed if elapsed >= 0.5 and self.done > 0 else None

    def eta(self) -> float | None:
        rate = self.rate()
        return (self.total - self.done) / rate if rate else None

    def rows(self) -> list[tuple[str, int, str]]:
        current = self.current()
        return [(f.name, n, "okunuyor" if i <= current else "sirada")
                for i, (f, n) in enumerate(zip(self.files, self.pages, strict=True))]


class _WindowDrops(QObject):
    """Drag and drop on the window itself (not on a widget that takes drops): any tab."""

    def __init__(self, screen: YukleScreen) -> None:
        super().__init__(screen)
        self.screen = screen

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        kind = event.type()
        if kind in (event.Type.DragEnter, event.Type.DragMove):
            return self.screen.drag_over(event)
        if kind == event.Type.DragLeave:
            self.screen.drag_left()
            return True
        if kind == event.Type.Drop:
            return self.screen.dropped(event)
        return False


class YukleScreen(QWidget):
    job_opened = Signal(object)  # Job; `self.controller` is its controller
    task_finished = Signal()
    refused = Signal(str)
    go_tab = Signal(str)

    def __init__(self, store: JobStore, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("page")
        self.setAcceptDrops(True)
        self.store = store
        self._controller: JobController | None = None
        self.task: Task | None = None
        self._reading: _Reading | None = None
        self._on_done: Callable[[object], None] | None = None
        self._listing = False
        self._shown_name = ""
        self._profile: tuple[str, ScanProfile | None] | None = None
        self._error: InfoBar | None = None
        self._drop_key: tuple | None = None
        self._info: JobSummary | None = None
        self._queued: list[Path] = []
        self._rows: list | None = None
        self.window_ = None  # the MainWindow once attached
        self.last_message = ""
        self.status_parts: dict[str, StatusPart] = {}
        self._own: dict[str, ActionButton] = {}
        # Returns a Turkish reason when another job must not be opened now.
        self.can_switch = lambda: "Bir iş sürüyor; bitince açın." if self.task else None

        m = theme.manager()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        root.addWidget(self.stack)

        # The job: batch table card + progress | inspector
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setObjectName("yukle")
        self.splitter.setChildrenCollapsible(False)
        work = QWidget()
        self.work = QVBoxLayout(work)
        self.work.setContentsMargins(m.size("s3"), 0, m.size("s3") - 4, m.size("s3"))  # -4: gutter
        self.work.setSpacing(m.size("s3"))
        self.card = QFrame()
        self.card.setProperty("kind", "table-card")
        self.card.setAccessibleName("Partiler")
        card = QVBoxLayout(self.card)
        card.setContentsMargins(1, 1, 1, 1)
        card.setSpacing(0)
        bar, self.pane_title, self.pane_hint = _heading_row()
        card.addWidget(bar)
        self.model = BatchModel(self)
        self.model.move_requested.connect(self.move_batch_to)
        self.table = BatchTable()
        self.table.setModel(self.model)
        self.table.selectionModel().currentChanged.connect(lambda *_: self._sync_actions())
        self.table.files_dragged.connect(self.drag_over)
        self.table.files_left.connect(self.drag_left)
        self.table.files_dropped.connect(self.dropped)
        header = self.table.horizontalHeader()
        header.sectionResized.connect(self._header_moved)
        self._header_timer = QTimer(self)
        self._header_timer.setSingleShot(True)
        self._header_timer.setInterval(300)
        self._header_timer.timeout.connect(self._save_header)
        self._default_widths()
        card.addWidget(self.table, 1)
        self.dropline = _Dropline()
        card.addWidget(self.dropline)
        self.work.addWidget(self.card, 1)
        self.progress = ProgressCard()
        self.progress.hide()
        self.work.addWidget(self.progress)
        self.splitter.addWidget(work)
        self.side = Inspector(self._fill_more)
        self.side.go.connect(lambda: self.go_tab.emit("kontrol"))
        self.side.open_guide.connect(lambda: self.go_tab.emit("rehber"))
        self.side.close_job.connect(self._close_job)
        self.splitter.addWidget(self.side)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        self._sized = False
        self.splitter.installEventFilter(self)
        self.stack.addWidget(self.splitter)

        # No job: the empty page with the job search
        self.empty = EmptyPage()
        self.empty.new_job.connect(self.choose_new_job)
        self.empty.add_files.connect(self.choose_batch)
        self.empty.open_job.connect(self.open_job_id)
        self.empty.show_job_folder.connect(self.show_job_folder)
        self.stack.addWidget(self.empty)

        self.overlay = DropOverlay(self)
        self.summary = self.side.title  # the page count; the window sets "İş açılmadı" here
        self.batches = self.table  # the window clears it when a job is closed
        theme.follow(self, self._restyle, "yukle-screen")
        self.refresh_jobs()
        self._sync_state()
        QTimer.singleShot(0, self._try_attach)

    def _size_inspector(self) -> None:
        """The inspector takes its A width (312, 400 at the largest density) once the splitter
        has its real size (it first shows with the first job), unless the window restored the
        remembered split."""
        self._sized = True
        prefs = getattr(self.window_, "prefs", None)
        if prefs is not None and len(prefs.splitter_sizes("yukle")) == 2:
            return
        inspector = theme.manager().size("inspector-w")
        self.splitter.setSizes([max(200, self.splitter.width() - inspector), inspector])

    # -- the open job --------------------------------------------------------------------
    @property
    def controller(self) -> JobController | None:
        return self._controller

    @controller.setter
    def controller(self, value: JobController | None) -> None:
        self._controller = value
        if value is None:
            self._profile = None
        self._sync_state()

    def busy(self) -> bool:
        return self.task is not None

    def _sync_state(self) -> None:
        """Body when a job is open or being made, else the empty page (or the job list)."""
        body = self._controller is not None or self._reading is not None
        self.stack.setCurrentWidget(self.splitter if body and not self._listing else self.empty)
        self.empty.set_mode("all" if self._listing else "empty")
        if self._controller is not None:
            self._show_batches()
        else:
            self._show_state()

    def open_job(self, job: Job) -> None:
        reason = self.can_switch() if self._controller is not None else None
        if reason:
            self.refused.emit(reason)
            return
        if self._controller is not None:
            try:
                self._controller.job_changed.disconnect(self._show_batches)
            except (RuntimeError, TypeError):
                pass
        self._listing = False
        self._clear_error()
        controller = JobController(self.store, job)
        controller.job_changed.connect(self._show_batches)
        self._controller = controller
        self._profile = None
        self._sync_state()
        first = self.model.items[0].batch_id if self.model.items else ""
        if first:
            self.table.select_batch(first)
        self.refresh_jobs()
        self.job_opened.emit(job)

    def open_job_id(self, job_id: str) -> None:
        try:
            job = self.store.load(job_id)
        except (KeyError, JobFileError, OSError) as error:
            self._tell("İş açılamadı: " + (str(error).strip("'\"") or "dosya okunamadı"),
                       "kontrol")
            self.refresh_jobs()
            return
        self.open_job(job)

    def close_job(self) -> None:
        """İşi kapat: back to "Henüz iş yok"; the job stays in the job list."""
        if self.window_ is not None:
            self.window_.registry.action("app.isi_kapat").trigger()
        else:
            self._close_now()

    def _close_job(self) -> None:
        self.close_job()

    def _close_now(self) -> None:
        if self._controller is not None:
            try:
                self._controller.job_changed.disconnect(self._show_batches)
            except (RuntimeError, TypeError):
                pass
        self.controller = None
        self.table.clear()
        self.refresh_jobs()

    def refresh_jobs(self) -> None:
        """The recent jobs of the empty page: newest first, with pages and "3 gün önce"."""
        found = []
        for job in self.store.list_jobs():
            path = self.store._job_file(job.id)
            try:
                age = time.time() - path.stat().st_mtime
                stamp = path.stat().st_mtime
            except OSError:
                age, stamp = 0, 0
            found.append((stamp, JobEntry(job.id, job.name,
                                          sum(b.page_count for b in job.batches), ago(age))))
        found.sort(key=lambda item: item[0], reverse=True)
        self.empty.set_jobs([entry for _stamp, entry in found])

    def show_job_list(self) -> None:
        """Tüm işler…: the job search and every job, even while one is open (Esc goes back)."""
        self._listing = True
        self.refresh_jobs()
        self._sync_state()
        self.empty.search.setFocus()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape and self._listing:
            self._listing = False
            self._sync_state()
            event.accept()
            return
        super().keyPressEvent(event)

    # -- new jobs and batches ------------------------------------------------------------
    def _start_folder(self) -> str:
        return default_folder(getattr(self.window_, "prefs", None))

    def _remember_folder(self, path: Path) -> None:
        prefs = getattr(self.window_, "prefs", None)
        if prefs is not None:
            prefs.add_recent_folder(path.parent)

    def choose_new_job(self) -> None:
        if self.busy():
            self._tell("Okuma sürüyor; bitince yeni iş oluşturun.", "info")
            return
        paths, _ = QFileDialog.getOpenFileNames(self, "Taranmış PDF'leri seçin",
                                                self._start_folder(), "PDF (*.pdf)")
        if not paths:
            return
        self._remember_folder(Path(paths[0]))
        name, ok = QInputDialog.getText(self, "Yeni iş", "İşin adı:", text=Path(paths[0]).stem)
        if ok and name.strip():
            self.create_job([Path(p) for p in paths], name.strip())

    def choose_batch(self) -> None:
        if self._controller is None and self.busy():
            self._tell("Okuma sürüyor; bitince yeni iş oluşturun.", "info")
            return
        if self._controller is None:
            self.choose_new_job()
            return
        paths, _ = QFileDialog.getOpenFileNames(self, "Parti ekle", self._start_folder(),
                                                "PDF (*.pdf)")
        if paths:
            self._remember_folder(Path(paths[0]))
            self.add_batches([Path(p) for p in paths])

    def choose_folder(self) -> None:
        """Klasör ekle…: every PDF in a folder (and its subfolders)."""
        folder = QFileDialog.getExistingDirectory(self, "PDF klasörü seçin", self._start_folder())
        if folder:
            prefs = getattr(self.window_, "prefs", None)
            if prefs is not None:
                prefs.add_recent_folder(folder)
            self.add_paths([Path(folder)])

    def add_paths(self, paths: list[Path]) -> None:
        """Files and folders from a drop or a dialog: the PDFs among them become a new job (no
        job open) or batches at the end of the open one."""
        pdfs, found = find_pdfs(paths)
        if not pdfs:
            self._tell("PDF bulunamadı. Yalnızca PDF dosyaları ve klasörleri eklenir.", "kontrol")
            return
        if found > len(pdfs):  # the limit: say how many were left out, never drop them quietly
            self._tell(f"{thousands(len(pdfs))} dosya alındı, {thousands(found - len(pdfs))} "
                       f"dosya alınmadı (bir seferde en çok {thousands(PDF_LIMIT)} dosya). "
                       "Kalanları ayrı bir parti olarak ekleyin.", "kontrol")
        if self.busy():  # one read at a time: these follow it, as batches of the same job
            self._queued += [p for p in pdfs if p not in self._queued]
            self._tell(f"{len(pdfs)} dosya sıraya alındı; okuma bitince eklenir.", "info")
            return
        if self._controller is None:
            only = paths[0] if len(paths) == 1 else pdfs[0]
            name = only.name if only.is_dir() else only.stem
            self.create_job(pdfs, name)
        else:
            self.add_batches(pdfs)

    def create_job(self, paths: list[Path], name: str) -> None:
        paths = [Path(p) for p in paths]
        self._begin(paths, lambda _total: (
            lambda progress: self.store.create_job(name, paths, progress)), self.open_job)

    def add_batch(self, path: Path) -> None:
        self.add_batches([Path(path)])

    def add_batches(self, paths: list[Path]) -> None:
        """Read the files on the side, then attach them all as one undoable edit. Until then
        the job stays editable and nothing in it has changed (cancel is free)."""
        if self._controller is None:
            self.create_job(paths, Path(paths[0]).stem)
            return
        paths = [Path(p) for p in paths]
        snapshot = job_from_dict(job_to_dict(self._controller.job))
        store = self.store

        def make_work(total: int):
            def work(progress):
                made, prepared, base = [], [], 0
                try:
                    for path in paths:
                        result = store.prepare_batch(
                            snapshot, path, lambda d, _t, base=base: progress(base + d, total))
                        made.append(store.batch_file(snapshot, result.batch))
                        prepared.append(result)
                        base += result.batch.page_count
                except BaseException:  # the copies of a cancelled or failed read are not kept
                    for copy in made:
                        copy.unlink(missing_ok=True)
                    raise
                return prepared

            return work

        self._begin(paths, make_work, self._batches_prepared)

    def _batches_prepared(self, prepared: list) -> None:
        controller = self._controller
        if controller is None or not prepared:
            return
        count = len(prepared)
        text = "Parti ekle" if count == 1 else f"{count} parti ekle"

        def attach(job: Job) -> None:
            for item in prepared:
                job.attach_batch(item.batch, item.pages)

        if controller.run(text, attach):
            self.table.select_batch(prepared[0].batch.id)
            self._tell(f"{count} parti eklendi." if count > 1
                       else f"{prepared[0].batch.file_name} eklendi.", "success",
                       "Geri al", controller.undo)

    # -- batches: move and remove --------------------------------------------------------
    def move_batch(self, step: int) -> None:
        batch_id = self.table.selected_batch()
        if self._controller is None or batch_id is None:
            return
        ids = [b.id for b in self._controller.job.batches]
        target = ids.index(batch_id) + step
        if 0 <= target < len(ids):
            self.move_batch_to(batch_id, target)

    def move_batch_to(self, batch_id: str, target: int) -> None:
        if self._controller is None:
            return
        if self._controller.run("Partiyi taşı", lambda job: job.move_batch(batch_id, target)):
            self.table.select_batch(batch_id)
            self.table.scrollTo(self.table.currentIndex())

    def remove_batch(self) -> None:
        """Del: take the selected batch out of the job. Undoable, so there is no question."""
        batch_id = self.table.selected_batch()
        controller = self._controller
        if controller is None or batch_id is None:
            return
        job = controller.job
        batch = job.get_batch(batch_id)
        row = self.model.row_of(batch_id)
        if not controller.run("Partiyi çıkar", lambda j: j.remove_batch(batch_id)):
            return
        count = len(controller.job.batches)
        if count:
            self.table.selectRow(min(row, count - 1))
            self.table.setCurrentIndex(self.model.index(min(row, count - 1), 2))
        self._tell(f"{batch.file_name} işten çıkarıldı.", "info", "Geri al", controller.undo)

    def rename_job(self) -> None:
        """F2: the job's name (undoable; the title band follows)."""
        controller = self._controller
        if controller is None:
            return
        name, ok = QInputDialog.getText(self, "İşi yeniden adlandır", "İşin adı:",
                                        text=controller.job.name)
        name = name.strip()
        if ok and name and name != controller.job.name:
            def rename(job: Job) -> None:
                job.name = name

            controller.run("İşi yeniden adlandır", rename)

    def show_job_folder(self, job_id: str) -> None:
        """A job row's "Klasörünü göster": the job's own folder in the file manager."""
        folder = self.store._job_dir(job_id)  # JobStore's path; pipeline left as it is (D13)
        if folder.is_dir():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))
        else:
            self._tell("İşin klasörü bulunamadı.", "kontrol")

    def show_in_explorer(self) -> None:
        """Ctrl+Shift+O: the selected batch's file in the file manager (else the job's folder)."""
        controller = self._controller
        if controller is None:
            return
        batch_id = self.table.selected_batch()
        target = None
        if batch_id is not None:
            target = self.store.batch_file(controller.job, controller.job.get_batch(batch_id))
        folder = self.store.batch_file(controller.job, controller.job.batches[0]).parent \
            if controller.job.batches else self.store._job_dir(controller.job.id)
        if target is not None and target.is_file() and os.name == "nt":
            subprocess.Popen(["explorer", "/select,", str(target)])  # noqa: S603, S607
        elif folder.is_dir():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))
        else:
            self._tell("Dosya bulunamadı; iş klasörü silinmiş olabilir.", "kontrol")

    # -- what the job shows --------------------------------------------------------------
    def _templates(self) -> dict:
        found = getattr(self.window_, "template_map", None)
        try:
            return dict(found()) if found is not None else {}
        except Exception:  # noqa: BLE001 - a template that cannot be read is not Yükle's error
            return {}

    def _summary(self) -> JobSummary | None:
        controller = self._controller
        if controller is None:
            return None
        job = controller.job
        documents = controller.documents()
        items = export.plan_export(job, self._templates())
        return summarize(job, documents, [i.document for i in items if i.checks])

    def _scan_profile(self) -> ScanProfile | None:
        controller = self._controller
        if controller is None or not controller.job.batches:
            return None
        batch = controller.job.batches[0]
        key = (controller.job.id, batch.id)
        if self._profile is None or self._profile[0] != key:
            self._profile = (key, scan_profile(self.store.batch_file(controller.job, batch)))
        return self._profile[1]

    def _show_batches(self) -> None:
        """The job changed (opened, edited, undone): table, inspector, status, actions."""
        controller = self._controller
        if controller is None:
            self._show_state()
            return
        info = self._info = self._summary()
        keep = self.table.selected_batch()
        self.model.set_content(info.batches, self._reading.rows() if self._reading else [])
        if keep and self.model.row_of(keep) >= 0:
            self.table.select_batch(keep)
        elif self.model.items and self.table.selected_batch() is None:
            self.table.select_batch(info.batches[0].id) if info.batches else None
        if self._reading is None:
            self.side.show_job(info, self._scan_profile())
        else:
            self._show_reading_side(info.pages, info.parties, info.qr)
        name = controller.job.name
        if name != self._shown_name:
            self._shown_name = name
            self._name_changed(name)
        self._show_state(info)

    def _show_reading_side(self, pages: int, parties: int, qr: int) -> None:
        reading = self._reading
        number = parties + reading.current() + 1 if reading else parties + 1
        self.side.show_reading(
            pages + (reading.total if reading else 0),
            parties + (len(reading.files) if reading else 0), qr,
            f"{number}. parti bitince belge sayısı ve uyarılar burada görünür.",
            self._scan_profile())

    def _show_state(self, info: JobSummary | None = None) -> None:
        """Everything that depends on the job state but not on its rows."""
        if info is None and self._controller is not None:
            info = self._info
        elif self._controller is None:
            self._info = None
        reading = self._reading
        if self._controller is None and reading is not None:
            self.model.set_content([], reading.rows())
            self._show_reading_side(0, 0, 0)
        self.progress.setVisible(reading is not None)
        self.side.set_actions(self._can_go(info), self._controller is not None)
        self._sync_status(info)
        self._sync_actions()

    def _can_go(self, info: JobSummary | None) -> bool:
        return bool(self._controller is not None and info is not None and info.batches)

    def _name_changed(self, name: str) -> None:
        window = self.window_
        if window is not None and getattr(self._controller, "job", None) is not None:
            window.job_switch.set_job(name)
            window.setWindowTitle(f"Evrakçı {__version__} – {name}")

    # -- the window: command bar, status bar, toasts, taskbar, drops ---------------------
    def _try_attach(self) -> None:
        window = self.window()
        if self.window_ is None and window is not self and hasattr(window, "registry"):
            self.attach(window)

    def attach(self, window) -> None:
        """Hook this tab into its MainWindow: the registry actions the window does not wire
        itself, the command bar's extra buttons, the status bar slot, the drop overlay, the
        remembered columns."""
        if self.window_ is window:
            return
        self.window_ = window
        r = window.registry
        for action_id, slot in (("yukle.cikar", self.remove_batch),
                                ("yukle.klasor_ekle", self.choose_folder),
                                ("yukle.yeniden_adlandir", self.rename_job),
                                ("yukle.gezginde_goster", self.show_in_explorer)):
            r.connect(action_id, slot)
        self.go_tab.connect(window.show_tab)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._context_menu)
        self._extend_command_bar(window)
        layout = window.status_slot("yukle").layout()
        for name, icon, role in (("parti", None, "icon"), ("sayfa", None, "icon"),
                                 ("belge", None, "icon"), ("warn", "triangle-alert", "rider-edge"),
                                 ("busy", "loader-circle", "text-2"), ("text", None, "icon")):
            part = StatusPart(icon, role)
            layout.addWidget(part)
            self.status_parts[name] = part
        layout.addStretch(1)  # the counts keep to the left however wide the slot gets
        window.setAcceptDrops(True)
        window.installEventFilter(_WindowDrops(self))
        self.overlay.setParent(window.layer)
        self.overlay.hide()
        window.layer.installEventFilter(self)
        self._restore_header()
        theme.manager().changed.connect(self._refresh_own_buttons)
        self._show_state()
        self._sync_name_to_window()

    def _sync_name_to_window(self) -> None:
        if self._controller is not None:
            self._shown_name = ""
            self._name_changed(self._controller.job.name)

    def _extend_command_bar(self, window) -> None:
        """A's Yükle bar: "Klasör ekle" after "Dosya ekle…" and "İptal et" before "Kontrol'e
        geç" (shown only while a batch is read) are registry commands on the window's bar; the
        screen keeps their buttons and takes over "Kontrol'e geç"'s enabled state."""
        bar = window.command_bar("yukle")
        for key, action_id in (("folder", "yukle.klasor_ekle"), ("cancel", "yukle.iptal")):
            button = bar.button_for(action_id)
            if button is not None:
                self._own[key] = button
        go_button = bar.button_for("app.sekme.kontrol")
        if go_button is not None:
            self._go_button = go_button
            go_button.set_gate(self._go_usable)
        self._sync_go_button()

    def _refresh_own_buttons(self) -> None:
        for button in self._own.values():
            button.refresh()

    def _sync_go_button(self) -> None:
        """"Kontrol'e geç" in the bar: off with no batches and while reading (A: disabled).
        A gate on the button, not setEnabled from here, so the button's own sync (an action
        change, a restyle) keeps it off. Ctrl+2 stays the tab key and always switches."""
        button = getattr(self, "_go_button", None)
        if button is not None:
            button._sync()

    def _go_usable(self) -> bool:
        return self._can_go(self._info) and self._reading is None

    def _sync_actions(self) -> None:
        """Every Yükle action is enabled exactly when it can do something."""
        busy = self._reading is not None
        controller = self._controller
        batch_id = self.table.selected_batch()
        ids = [b.id for b in controller.job.batches] if controller is not None else []
        pos = ids.index(batch_id) if batch_id in ids else -1
        state = {"yukle.yukari": pos > 0, "yukle.asagi": 0 <= pos < len(ids) - 1,
                 "yukle.cikar": pos >= 0, "yukle.yeniden_adlandir": controller is not None,
                 "yukle.gezginde_goster": controller is not None, "yukle.iptal": busy,
                 }
        window = self.window_
        if window is not None:
            for action_id, enabled in state.items():
                window.registry.set_enabled(action_id, enabled)
        self._sync_go_button()

    def _fill_more(self, menu: QMenu) -> None:
        """The inspector's … menu: rename, show in the file manager, close."""
        if self.window_ is None:
            return
        r = self.window_.registry
        for action_id in ("yukle.yeniden_adlandir", "yukle.gezginde_goster"):
            menu.addAction(r.action(action_id))
        menu.addSeparator()
        menu.addAction(r.action("app.isi_kapat"))

    def _context_menu(self, pos: QPoint) -> None:
        index = self.table.indexAt(pos)
        if index.isValid() and self.model.items[index.row()].kind == "batch":
            self.table.selectRow(index.row())
        r = self.window_.registry
        menu = QMenu(self.table)
        for action_id in ("yukle.yukari", "yukle.asagi", "yukle.cikar"):
            menu.addAction(r.action(action_id))
        menu.addSeparator()
        menu.addAction(r.action("yukle.gezginde_goster"))
        menu.popup(self.table.viewport().mapToGlobal(pos))
        self._menu = menu

    # status bar
    def _sync_status(self, info: JobSummary | None) -> None:
        parts = self.status_parts
        if not parts:
            return
        reading = self._reading
        for part in parts.values():
            part.hide()
        if info is None and reading is None:
            parts["text"].set("Ctrl+N ile yeni iş oluşturabilirsiniz")
            parts["text"].show()
        else:
            batches = info.parties if info else 0
            pages = info.pages if info else 0
            if reading is not None:
                batches += len(reading.files)
                pages += reading.total
            parts["parti"].set("", str(batches), " parti")
            parts["sayfa"].set("", str(pages), " sayfa")
            parts["parti"].show()
            parts["sayfa"].show()
            if reading is not None:
                parts["busy"].set("Okunuyor: ", str(reading.done), f" / {reading.total}")
                parts["busy"].show()
            elif info is not None:
                parts["belge"].set("", str(info.documents), " belge")
                parts["belge"].show()
                if info.checks:
                    parts["warn"].set("", str(info.checks), " belge kontrol bekliyor")
                    parts["warn"].show()

    # -- drops ---------------------------------------------------------------------------
    @staticmethod
    def _local_paths(event) -> list[Path]:
        return [Path(u.toLocalFile()) for u in event.mimeData().urls() if u.isLocalFile()]

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        self.drag_over(event)

    def dragMoveEvent(self, event) -> None:  # noqa: N802
        self.drag_over(event)

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        self.drag_left()

    def dropEvent(self, event) -> None:  # noqa: N802
        self.dropped(event)

    def drag_over(self, event) -> bool:
        """Files over the window: show what a drop would do (and accept the drag)."""
        if not event.mimeData().hasUrls():
            return False
        paths = self._local_paths(event)
        key = tuple(paths)
        if key != self._drop_key or not self.overlay.isVisible():
            self._drop_key = key
            self.overlay.show_drop(paths, self._controller.job.name if self._controller
                                   else None)
        event.acceptProposedAction()
        return True

    def drag_left(self) -> None:
        self._drop_key = None
        self.overlay.hide()

    def dropped(self, event) -> bool:
        if not event.mimeData().hasUrls():
            return False
        self.drag_left()
        paths = self._local_paths(event)
        event.acceptProposedAction()
        if self.window_ is not None and self.window_.current_tab() != "yukle":
            self.window_.show_tab("yukle")
        QTimer.singleShot(0, partial(self.add_paths, paths))  # after the drag has ended
        return True

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        if obj is self.splitter and event.type() == event.Type.Show and not self._sized:
            QTimer.singleShot(0, self._size_inspector)  # after the first layout
        if (self.window_ is not None and obj is self.window_.layer
                and event.type() == event.Type.Resize and self.overlay.isVisible()):
            self.overlay.place()
        return False

    # -- background work -----------------------------------------------------------------
    def _begin(self, files: list[Path], make_work, on_done) -> None:
        """Start reading `files`: `make_work(total pages)` returns the function the worker runs
        (it reports pages done of the total)."""
        if self.task is not None:
            return
        self._clear_error()
        reading = _Reading(files)

        def work(progress):
            # Counting opens every file: it runs here, in the worker, never on the GUI
            # thread (a folder of thousands of scans would freeze the window first).
            reading.set_pages([count_pages(p) for p in files])
            return make_work(reading.total)(progress)

        self._reading = reading
        self._on_done = on_done
        self.task = Task(work)
        self.task.signals.progress.connect(self._progress)
        self.task.signals.done.connect(self._done)
        self.task.signals.failed.connect(self._failed)
        self.task.signals.cancelled.connect(self._cancelled)
        self.progress.show_waiting(f"Dosyalar inceleniyor: {len(files)}", files[0].name)
        self.setCursor(Qt.CursorShape.BusyCursor)
        taskbar = getattr(self.window_, "taskbar", None)
        if taskbar is not None:
            taskbar.indeterminate()
        self._sync_state()
        start(self.task)

    def _progress(self, done: int, total: int) -> None:
        reading = self._reading
        if reading is None:
            return
        reading.done = min(done, reading.total)
        now = time.monotonic()
        if now - reading.shown < REPORT_EVERY and reading.done < reading.total:
            return
        reading.shown = now
        current = reading.current()
        name = reading.files[current].name
        self.progress.show_progress(reading.done, reading.total, name, reading.eta(),
                                    reading.rate())
        if reading.cancelling:
            self.progress.title.setText("İptal ediliyor…")
        taskbar = getattr(self.window_, "taskbar", None)
        if taskbar is not None:
            taskbar.set(reading.done, reading.total)
        rows = reading.rows()
        if rows != getattr(self, "_rows", None):
            self._rows = rows
            self.model.set_pending(rows)
        info = self._info if self._controller is not None else None
        self._show_reading_side(info.pages if info else 0, info.parties if info else 0,
                                info.qr if info else 0)
        self._sync_status(info)

    def _done(self, result) -> None:
        self._finish(self._on_done, result)

    def _failed(self, message: str) -> None:
        self._finish(None, None, error=message)

    def _cancelled(self) -> None:
        self._finish(None, None, cancelled=True)

    def _finish(self, on_done, result, error: str | None = None, cancelled: bool = False) -> None:
        self.task = None
        self._reading = None
        self._rows = None
        self.unsetCursor()
        taskbar = getattr(self.window_, "taskbar", None)
        if taskbar is not None:
            taskbar.clear()
        self.progress.hide()
        if self._controller is None and on_done is None:
            self.table.clear()
        if error is not None:
            self._fail(error)
        elif cancelled:
            self._tell("İptal edildi; hiçbir şey değişmedi.", "info")
        if on_done is not None:
            on_done(result)
        queued, self._queued = self._queued, []
        self._sync_state()
        self._attention()
        self.task_finished.emit()
        if not queued:
            return
        if error is None and not cancelled and self._controller is not None:
            self.add_batches(queued)
            return
        # The read these files waited for did not finish: they are not dropped silently.
        count = len(queued)
        self._tell(f"Sıradaki {count} dosya eklenmedi; önceki okuma "
                   f"{'iptal edildi' if cancelled else 'tamamlanamadı'}.", "kontrol",
                   "Yine de ekle", partial(self.add_paths, queued))

    def cancel(self) -> None:
        """İptal et (Ctrl+.): stop reading; nothing in the job changes. Esc does not cancel."""
        if self.task is not None and self._reading is not None:
            self._reading.cancelling = True
            self.task.cancel()
            self.progress.title.setText("İptal ediliyor…")

    def _attention(self) -> None:
        """Flash the taskbar button when the window is not the active one (QOL 19)."""
        window = self.window_
        if window is not None and not window.isActiveWindow():
            QApplication.alert(window, 0)

    # -- messages ------------------------------------------------------------------------
    def _tell(self, text: str, kind: str = "info", action: str | None = None,
              on_action: Callable[[], None] | None = None) -> None:
        """A short note: a toast in the window (with Geri al where it can be undone)."""
        self.last_message = text
        toaster = getattr(self.window_, "toaster", None)
        if toaster is not None:
            toaster.show(text, action, on_action, kind=kind, timeout_ms=10000 if action else 6000)
        else:
            self.refused.emit(text)

    def _fail(self, message: str) -> None:
        """A read that failed: an info bar above the table that stays until it is closed."""
        self._clear_error()
        text = message.rstrip(".") + ". Dosyayı kontrol edip yeniden ekleyin."
        bar = InfoBar("error", "Okunamadı", text, "Dosya ekle…", self.choose_batch, True, self)
        self._error = bar
        self.work.insertWidget(0, bar)
        self.last_message = text
        taskbar = getattr(self.window_, "taskbar", None)
        if taskbar is not None:
            taskbar.error()
            QTimer.singleShot(4000, lambda: taskbar.clear() if self.task is None else None)

    def _clear_error(self) -> None:
        if self._error is not None:
            self._error.hide()
            self._error.deleteLater()
            self._error = None

    # -- columns, look -------------------------------------------------------------------
    def _default_widths(self) -> None:
        from evrakci.ui.yukle_table import FILE, WIDTHS

        header = self.table.horizontalHeader()
        header.blockSignals(True)
        for column, width in WIDTHS.items():
            header.setSectionResizeMode(column, header.ResizeMode.Interactive)
            self.table.setColumnWidth(column, width)  # A's colgroup is in px at every text size
        header.setSectionResizeMode(FILE, header.ResizeMode.Stretch)
        header.blockSignals(False)

    def _restore_header(self) -> None:
        from evrakci.ui.yukle_table import FILE, WIDTHS

        prefs = getattr(self.window_, "prefs", None)
        state = prefs.header_state(HEADER_KEY) if prefs is not None else None
        if state is None or state.isEmpty():
            return
        header = self.table.horizontalHeader()
        header.blockSignals(True)
        restored = header.restoreState(state) and header.count() == 6
        if not restored:
            self._default_widths()
        for column in WIDTHS:
            header.setSectionResizeMode(column, header.ResizeMode.Interactive)
        header.setSectionResizeMode(FILE, header.ResizeMode.Stretch)
        header.blockSignals(False)

    def _header_moved(self, *_args) -> None:
        self._header_timer.start()

    def _save_header(self) -> None:
        prefs = getattr(self.window_, "prefs", None)
        if prefs is not None:
            prefs.set_header_state(HEADER_KEY, self.table.horizontalHeader().saveState())

    def _restyle(self) -> None:
        """After a theme or text-size switch: the extra bar buttons and, with no remembered
        columns, A's widths at the new size."""
        for button in self._own.values():
            button.refresh()
        if getattr(self.window_, "prefs", None) is None:
            self._default_widths()
