"""The Yükle screen: jobs, and the scan batches of the open job."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from evrakci.pipeline.job import Job
from evrakci.pipeline.store import JobStore
from evrakci.ui.controller import JobController
from evrakci.ui.kontrol import index_rule, key_button
from evrakci.ui.workers import Task, start


def _heading(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet("font-size: 20px; font-weight: 700;")
    return label


class YukleScreen(QWidget):
    job_opened = Signal(object)  # Job; `self.controller` is its controller
    task_finished = Signal()

    def __init__(self, store: JobStore, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("page")
        self.setAcceptDrops(True)
        self.store = store
        self.controller: JobController | None = None
        self.task: Task | None = None

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        left = QFrame()
        left.setObjectName("card")
        left.setFixedWidth(340)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(20, 16, 20, 16)
        top = QHBoxLayout()
        top.addWidget(_heading("İşler"))
        top.addStretch(1)
        self.new_button = key_button("Yeni iş", "Ctrl+N")
        self.new_button.clicked.connect(self.choose_new_job)
        top.addWidget(self.new_button)
        left_layout.addLayout(top)
        left_layout.addWidget(index_rule())
        self.jobs = QListWidget()
        self.jobs.itemActivated.connect(self._job_activated)
        left_layout.addWidget(self.jobs, 1)
        hint = QLabel("Bir işi açmak için seçip Enter'a basın. İşler bu bilgisayarda kalır.")
        hint.setWordWrap(True)
        hint.setProperty("role", "muted")
        left_layout.addWidget(hint)
        root.addWidget(left)

        middle = QVBoxLayout()
        middle.setContentsMargins(24, 16, 24, 16)
        head = QHBoxLayout()
        head.addWidget(_heading("Partiler"))
        sub = QLabel("Bu sırayla tek yığın olur")
        sub.setProperty("role", "muted")
        head.addWidget(sub)
        head.addStretch(1)
        self.add_button = key_button("Dosya seç…", "Ctrl+O")
        self.add_button.clicked.connect(self.choose_batch)
        head.addWidget(self.add_button)
        middle.addLayout(head)
        middle.addWidget(index_rule())
        self.batches = QListWidget()
        middle.addWidget(self.batches, 1)
        buttons = QHBoxLayout()
        self.up_button = key_button("Yukarı", "Alt+↑")
        self.down_button = key_button("Aşağı", "Alt+↓")
        self.remove_button = key_button("Partiyi çıkar", "")
        self.up_button.clicked.connect(lambda: self.move_batch(-1))
        self.down_button.clicked.connect(lambda: self.move_batch(1))
        self.remove_button.clicked.connect(self.remove_batch)
        for button in (self.up_button, self.down_button, self.remove_button):
            buttons.addWidget(button)
        buttons.addStretch(1)
        middle.addLayout(buttons)
        progress_row = QHBoxLayout()
        self.progress_label = QLabel("")
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.cancel_button = key_button("İptal", "Esc")
        self.cancel_button.clicked.connect(self.cancel)
        progress_row.addWidget(self.progress_label)
        progress_row.addWidget(self.progress, 1)
        progress_row.addWidget(self.cancel_button)
        middle.addLayout(progress_row)
        drop = QLabel("PDF'leri buraya bırakın veya Dosya seç… (Ctrl+O)")
        drop.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop.setMinimumHeight(90)
        drop.setStyleSheet("border: 1px dashed #74817a; border-radius: 6px;")
        middle.addWidget(drop)
        root.addLayout(middle, 1)

        right = QFrame()
        right.setObjectName("card")
        right.setFixedWidth(300)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(20, 16, 20, 16)
        right_layout.addWidget(_heading("İş özeti"))
        right_layout.addWidget(index_rule())
        self.summary = QLabel("İş açılmadı")
        self.summary.setWordWrap(True)
        right_layout.addWidget(self.summary)
        right_layout.addStretch(1)
        root.addWidget(right)

        for key, slot in {"Ctrl+N": self.choose_new_job, "Ctrl+O": self.choose_batch,
                          "Esc": self.cancel, "Alt+Up": lambda: self.move_batch(-1),
                          "Alt+Down": lambda: self.move_batch(1)}.items():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(slot)
        self._set_busy(False)
        self.refresh_jobs()

    # Jobs
    def refresh_jobs(self) -> None:
        self.jobs.clear()
        for job in self.store.list_jobs():
            pages = sum(b.page_count for b in job.batches)
            item = QListWidgetItem(f"{job.name}\n{pages} sayfa · {len(job.batches)} parti")
            item.setData(Qt.ItemDataRole.UserRole, job.id)
            self.jobs.addItem(item)

    def _job_activated(self, item: QListWidgetItem) -> None:
        self.open_job(self.store.load(item.data(Qt.ItemDataRole.UserRole)))

    def open_job(self, job: Job) -> None:
        if self.controller is not None:
            self.controller.job_changed.disconnect(self._show_batches)
        self.controller = JobController(self.store, job)
        self.controller.job_changed.connect(self._show_batches)
        self._show_batches()
        self.refresh_jobs()
        self.job_opened.emit(job)

    def choose_new_job(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Taranmış PDF'leri seçin", "", "PDF (*.pdf)")
        if not paths:
            return
        name, ok = QInputDialog.getText(self, "Yeni iş", "İşin adı:", text=Path(paths[0]).stem)
        if ok and name.strip():
            self.create_job([Path(p) for p in paths], name.strip())

    def create_job(self, paths: list[Path], name: str) -> None:
        self._run(
            f"{len(paths)} dosya inceleniyor",
            lambda progress: self.store.create_job(name, paths, progress),
            self.open_job,
        )

    # Batches
    def choose_batch(self) -> None:
        if self.controller is None:
            self.choose_new_job()
            return
        paths, _ = QFileDialog.getOpenFileNames(self, "Parti ekle", "", "PDF (*.pdf)")
        for path in paths:
            self.add_batch(Path(path))

    def add_batch(self, path: Path) -> None:
        job = self.controller.job
        self._run(f"{path.name} inceleniyor",
                  lambda progress: self.store.add_batch(job, path),
                  lambda _batch: self._batch_added())

    def _batch_added(self) -> None:
        self.controller.undo_stack.clear()  # the batch file is on disk now; earlier steps stay
        self.controller.job_changed.emit()

    def move_batch(self, step: int) -> None:
        row = self.batches.currentRow()
        if self.controller is None or row < 0:
            return
        target = row + step
        if not 0 <= target < len(self.controller.job.batches):
            return
        batch_id = self.controller.job.batches[row].id
        if self.controller.run("Partiyi taşı", lambda job: job.move_batch(batch_id, target)):
            self.batches.setCurrentRow(target)

    def remove_batch(self) -> None:
        row = self.batches.currentRow()
        if self.controller is None or row < 0:
            return
        batch = self.controller.job.batches[row]
        answer = QMessageBox.question(
            self, "Partiyi çıkar",
            f"{batch.file_name} işten çıkarılsın mı? Bu geri alınamaz.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.store.remove_batch(self.controller.job, batch.id)
        self.controller.undo_stack.clear()
        self.controller.job_changed.emit()

    def _show_batches(self) -> None:
        job = self.controller.job
        self.batches.clear()
        for number, batch in enumerate(job.batches, start=1):
            qr = sum(1 for i in range(batch.page_count)
                     if job.pages[f"{batch.id}/{i}"].is_separator)
            self.batches.addItem(
                f"{number}   {batch.file_name}   ·   {batch.page_count} sayfa   ·   "
                f"{qr} QR ayıraç"
            )
        documents = self.controller.documents()
        pages = sum(b.page_count for b in job.batches)
        self.summary.setText(
            f"<b>{job.name}</b><br>{pages} sayfa<br>{len(documents)} belge<br>"
            f"{len(job.batches)} parti"
        )

    # Drag and drop
    def dragEnterEvent(self, event) -> None:
        if any(u.toLocalFile().lower().endswith(".pdf") for u in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        paths = [Path(u.toLocalFile()) for u in event.mimeData().urls()
                 if u.toLocalFile().lower().endswith(".pdf")]
        if not paths:
            return
        if self.controller is None:
            self.create_job(paths, paths[0].stem)
        else:
            for path in paths:
                self.add_batch(path)

    # Background work
    def _run(self, text: str, work, on_done) -> None:
        if self.task is not None:
            return
        self.task = Task(work)
        self.task.signals.progress.connect(self._progress)
        self.task.signals.done.connect(lambda result: self._finish("", on_done, result))
        self.task.signals.failed.connect(
            lambda message: self._finish(f"Yapılamadı: {message}", None, None))
        self.task.signals.cancelled.connect(
            lambda: self._finish("İptal edildi; hiçbir şey değişmedi.", None, None))
        self.progress_label.setText(text)
        self.progress.setRange(0, 0)
        self._set_busy(True)
        start(self.task)

    def _progress(self, done: int, total: int) -> None:
        self.progress.setRange(0, max(total, 1))
        self.progress.setValue(done)
        self.progress_label.setText(f"Sayfalar inceleniyor: {done} / {total}")

    def _finish(self, message: str, on_done, result) -> None:
        self.task = None
        self._set_busy(False)
        self.progress_label.setText(message)
        if on_done is not None:
            on_done(result)
        self.task_finished.emit()

    def cancel(self) -> None:
        if self.task is not None:
            self.task.cancel()
            self.progress_label.setText("İptal ediliyor…")

    def _set_busy(self, busy: bool) -> None:
        self.progress.setVisible(busy)
        self.cancel_button.setVisible(busy)
        self.new_button.setEnabled(not busy)
        self.add_button.setEnabled(not busy)

    def busy(self) -> bool:
        return self.task is not None


