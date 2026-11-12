"""The Dışa Aktar screen: write the named PDFs and index.xlsx, never silently."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path

from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
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
from evrakci.ui import theme
from evrakci.ui.controller import JobController
from evrakci.ui.kontrol import index_rule, key_button
from evrakci.ui.workers import Task, start

RETENTION = [
    (KEEP, "İşi sakla"),
    (DELETE_AFTER_EXPORT, "Tam dışa aktarınca sil"),
    ("30", "30 gün sakla"),
    ("90", "90 gün sakla"),
]


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

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        left = QFrame()
        left.setObjectName("card")
        left.setFixedWidth(420)
        form = QVBoxLayout(left)
        form.setContentsMargins(24, 16, 24, 16)
        title = QLabel("Dışa aktar")
        title.setProperty("role", "heading")
        form.addWidget(title)
        form.addWidget(index_rule())
        form.addWidget(QLabel("Hedef klasör (boş olmalı)"))
        row = QHBoxLayout()
        self.folder = QLineEdit()
        choose = key_button("Seç…", "")
        choose.clicked.connect(self.choose_folder)
        row.addWidget(self.folder, 1)
        row.addWidget(choose)
        form.addLayout(row)
        self.layer = QCheckBox("Aranabilir metin katmanı ekle (OCR, PDF/A)")
        self.layer.setChecked(True)
        form.addWidget(self.layer)
        index_note = QLabel("index.xlsx her zaman yazılır: her dosya bir satır.")
        index_note.setProperty("role", "muted")
        form.addWidget(index_note)
        row = QHBoxLayout()
        row.addWidget(QLabel("İşi sakla:"))
        self.retention = QComboBox()
        for value, text in RETENTION:
            self.retention.addItem(text, value)
        row.addWidget(self.retention, 1)
        form.addLayout(row)
        self.preflight = QLabel("")
        self.preflight.setWordWrap(True)
        form.addWidget(self.preflight)
        self.export_button = key_button("Dışa aktar", "Ctrl+E", primary=True)
        self.export_button.clicked.connect(self.export)
        form.addWidget(self.export_button)
        self.message = QLabel("")
        self.message.setWordWrap(True)
        self.message.setStyleSheet(f"color: {theme.colour('check_ink')}; font-weight: 600;")
        form.addWidget(self.message)
        form.addStretch(1)
        root.addWidget(left)

        main = QVBoxLayout()
        main.setContentsMargins(24, 16, 24, 16)
        heading = QLabel("Yazılan dosyalar")
        heading.setProperty("role", "heading")
        main.addWidget(heading)
        main.addWidget(index_rule())
        progress_row = QHBoxLayout()
        self.progress_label = QLabel("")
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.cancel_button = key_button("İptal", "Esc")
        self.cancel_button.clicked.connect(self.cancel)
        progress_row.addWidget(self.progress_label)
        progress_row.addWidget(self.progress, 1)
        progress_row.addWidget(self.cancel_button)
        main.addLayout(progress_row)
        self.results = QTableWidget(0, 4)
        self.results.setHorizontalHeaderLabels(["Dosya", "Sayfalar", "Şablon", "Durum"])
        self.results.verticalHeader().setVisible(False)
        self.results.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        main.addWidget(self.results, 1)
        buttons = QHBoxLayout()
        self.open_index = key_button("index.xlsx'i aç", "")
        self.open_folder = key_button("Klasörü aç", "")
        self.open_index.clicked.connect(lambda: self._open(self.out_dir / "index.xlsx"))
        self.open_folder.clicked.connect(lambda: self._open(self.out_dir))
        buttons.addWidget(self.open_index)
        buttons.addWidget(self.open_folder)
        buttons.addStretch(1)
        main.addLayout(buttons)
        root.addLayout(main, 1)

        self._load_settings()
        self.retention.currentIndexChanged.connect(self._save_settings)
        self._set_busy(False)
        self.open_index.setEnabled(False)
        self.open_folder.setEnabled(False)
        self.refresh()

    # Settings
    def _load_settings(self) -> None:
        try:
            value = load_settings(self.settings_path).retention
        except SettingsError as error:
            self.message.setText(str(error))
            value = KEEP
        index = self.retention.findData(value)
        if index < 0:
            self.retention.addItem(f"{value} gün sakla", value)
            index = self.retention.count() - 1
        self.retention.setCurrentIndex(index)

    def _save_settings(self) -> None:
        save_settings(Settings(self.retention.currentData()), self.settings_path)

    # Before export
    def refresh(self) -> None:
        controller = self.controller()
        if controller is None:
            self.preflight.setText("Önce Yükle sekmesinden bir iş açın.")
            self.export_button.setEnabled(False)
            return
        self.export_button.setEnabled(self.task is None)
        items = plan_export(controller.job, self.templates())
        checks = sum(1 for item in items if item.checks)
        self.preflight.setText(
            f"<b>Yazılmadan önce</b><br>Yazılacak belge: {len(items)}<br>"
            f"Tamam: {len(items) - checks}<br>Kontrol işaretli: {checks}<br>"
            "Kontrol gerekenler adında [kontrol] ile yazılır ve index.xlsx'te işaretlenir. "
            "Hiçbiri sessizce geçmez."
        )

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
            self.message.setText("Önce boş bir hedef klasör seçin.")
            return
        out_dir = Path(self.folder.text().strip())
        controller.store.save(controller.job)  # marks the job as in use for the day limit
        # The worker gets its own copy: the live job can still be edited meanwhile.
        job = job_from_dict(job_to_dict(controller.job))
        files = controller.store.batch_files(job)
        self._exporting = (controller, job)
        templates = dict(self.templates())
        with_layer = self.layer.isChecked()

        def work(progress):
            try:
                return export_job(job, files, templates, out_dir, with_layer=with_layer,
                                  progress=lambda stage, done, total: progress(done, total))
            except EngineUnavailable as error:
                raise ExportError(f"{error}. Metin katmanı olmadan yazmak için "
                                  "“Aranabilir metin katmanı ekle” kutusunu kapatın.") from None

        self.out_dir = out_dir
        self.message.setText("")
        self.results.setRowCount(0)
        self.task = Task(work)
        self.task.signals.progress.connect(self._progress)
        self.task.signals.done.connect(self._done)
        self.task.signals.failed.connect(self._failed)
        self.task.signals.cancelled.connect(self._cancelled)
        self.progress_label.setText("Yazılıyor…")
        self._set_busy(True)
        start(self.task)

    def _progress(self, done: int, total: int) -> None:
        self.progress.setRange(0, max(1, total))
        self.progress.setValue(done)
        self.progress_label.setText(f"Yazılıyor: {done} / {total}")

    def _done(self, result) -> None:
        warn = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning)
        controller, job = self._exporting  # the job that was exported, not the open one
        ordered = sorted(zip(result.paths, result.items, strict=True),
                         key=lambda pair: not pair[1].checks)  # flagged files first
        self.results.setRowCount(len(ordered))
        for row, (path, item) in enumerate(ordered):
            positions = [job.position_of(pid) for pid in item.document.page_ids]
            pages = (f"{positions[0]}–{positions[-1]}" if len(positions) > 1
                     else str(positions[0]))
            status = QTableWidgetItem("Kontrol: " + "; ".join(item.checks) if item.checks
                                      else "Yazıldı")
            if item.checks:
                status.setIcon(warn)
            for column, cell in enumerate((QTableWidgetItem(path.name), QTableWidgetItem(pages),
                                           QTableWidgetItem(item.template_name or "Şablon yok"),
                                           status)):
                self.results.setItem(row, column, cell)
        self.results.resizeColumnsToContents()
        message = (f"{len(result.paths)} belge yazıldı, {result.needing_check} belge kontrol "
                   "gerektiriyor. Liste: index.xlsx")
        if self.retention.currentData() == DELETE_AFTER_EXPORT and may_delete_after_export(result):
            controller.store.delete(job.id)
            message += " İş silindi (saklama ayarı)."
            self.job_deleted.emit()
        elif (self.retention.currentData() == DELETE_AFTER_EXPORT and result.paths
              and not result.with_layer):
            message += " İş saklandı: metin katmanı eklenmedi."
        self.open_index.setEnabled(bool(result.paths))
        self.open_folder.setEnabled(True)
        self._finish(message)

    def _failed(self, message: str) -> None:
        self._finish(message)

    def _cancelled(self) -> None:
        written = sorted(p.name for p in self.out_dir.glob("*.pdf")) if self.out_dir else []
        self._finish(
            f"Dışa aktarma durduruldu: {len(written)} dosya yazıldı, index.xlsx yazılmadı. "
            "Yeniden dışa aktarmak için boş bir klasör seçin."
        )

    def _finish(self, message: str) -> None:
        self.task = None
        self._exporting = None
        self._set_busy(False)
        self.progress_label.setText("")
        self.message.setText(message)
        self.refresh()
        self.finished.emit()

    def cancel(self) -> None:
        if self.task is not None:
            self.task.cancel()

    def busy(self) -> bool:
        return self.task is not None

    def _set_busy(self, busy: bool) -> None:
        self.progress.setVisible(busy)
        self.cancel_button.setVisible(busy)
        self.export_button.setEnabled(not busy)

    def _open(self, path: Path) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))


