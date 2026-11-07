"""The main window: six tabs over the same core as the command line."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QLabel, QMainWindow, QMessageBox, QTabWidget

from evrakci import __version__
from evrakci.pipeline.store import JobFileError, JobStore
from evrakci.pipeline.templates.model import TemplateError
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.ui import theme
from evrakci.ui.controller import JobController
from evrakci.ui.degerler import DegerlerScreen
from evrakci.ui.disa_aktar import DisaAktarScreen
from evrakci.ui.kontrol import KontrolScreen
from evrakci.ui.rehber import RehberScreen
from evrakci.ui.sablon import SablonScreen
from evrakci.ui.thumbnails import ThumbnailService, job_renderer
from evrakci.ui.yukle import YukleScreen

TAB_NAMES = ["Yükle", "Kontrol", "Şablonlar", "Değerler", "Dışa Aktar", "Rehber"]
LAST_JOB = "son-is.txt"


class MainWindow(QMainWindow):
    def __init__(
        self,
        store: JobStore,
        templates: TemplateStore,
        settings_path: Path | None = None,
    ) -> None:
        super().__init__()
        self.store = store
        self.template_store = templates
        self.setWindowTitle(f"Evrakçı {__version__}")
        self.resize(1366, 768)
        self.setStyleSheet(theme.stylesheet())
        self.kontrol: KontrolScreen | None = None
        self.thumbnails: ThumbnailService | None = None

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.yukle = YukleScreen(store)
        self.yukle.job_opened.connect(self._job_opened)
        self.sablon = SablonScreen(templates, self.controller)
        self.degerler = DegerlerScreen(self.controller, self.template_map)
        self.degerler.draw_variant.connect(self._draw_variant)
        self.disa_aktar = DisaAktarScreen(self.controller, self.template_map, settings_path)
        self.disa_aktar.job_deleted.connect(self._job_deleted)
        self.rehber = RehberScreen()
        self._kontrol_placeholder = QLabel("Önce Yükle sekmesinden bir iş açın.")
        for name, widget in zip(TAB_NAMES, (self.yukle, self._kontrol_placeholder, self.sablon,
                                            self.degerler, self.disa_aktar, self.rehber),
                                strict=True):
            self.tabs.addTab(widget, name)
        for number in range(5):
            self.tabs.setTabToolTip(number, f"Ctrl+{number + 1}")
            shortcut = QShortcut(QKeySequence(f"Ctrl+{number + 1}"), self)
            shortcut.activated.connect(lambda n=number: self.tabs.setCurrentIndex(n))
        self.tabs.setTabToolTip(5, "F1")
        QShortcut(QKeySequence("F1"), self).activated.connect(lambda: self.tabs.setCurrentIndex(5))
        self.tabs.currentChanged.connect(self._tab_changed)
        self.setCentralWidget(self.tabs)

        self.counts = QLabel("")
        self.message = QLabel("")
        self.statusBar().addWidget(self.counts)
        self.statusBar().addPermanentWidget(self.message)
        self._open_last_job()

    # Shared state
    def controller(self) -> JobController | None:
        return self.yukle.controller

    def template_map(self) -> dict:
        found = {}
        for template in self.template_store.list():
            found[template.id] = template
        return found

    def _open_last_job(self) -> None:
        path = self.store.root / LAST_JOB
        if not path.is_file():
            return
        try:
            job = self.store.load(path.read_text(encoding="utf-8").strip())
        except (KeyError, JobFileError, OSError):
            return
        self.yukle.open_job(job)

    def _job_opened(self, job) -> None:
        controller = self.controller()
        self.store.root.mkdir(parents=True, exist_ok=True)
        (self.store.root / LAST_JOB).write_text(job.id, encoding="utf-8")
        self.thumbnails = ThumbnailService(job_renderer(job, self.store.batch_files(job)),
                                           height=110)
        kontrol = KontrolScreen(controller, self.thumbnails, self.template_map)
        kontrol.open_values.connect(lambda _n: self.tabs.setCurrentIndex(3))
        old = self.tabs.widget(1)
        self.tabs.removeTab(1)
        self.tabs.insertTab(1, kontrol, TAB_NAMES[1])
        self.tabs.setTabToolTip(1, "Ctrl+2")
        if old is not self._kontrol_placeholder:
            old.deleteLater()
        self.kontrol = kontrol
        controller.status.connect(self.message.setText)
        controller.job_changed.connect(self._update_counts)
        self.setWindowTitle(f"Evrakçı {__version__} – {job.name}")
        self._update_counts()

    def _job_deleted(self) -> None:
        (self.store.root / LAST_JOB).unlink(missing_ok=True)
        self.yukle.refresh_jobs()

    def _update_counts(self) -> None:
        controller = self.controller()
        if controller is None:
            self.counts.setText("")
            return
        job = controller.job
        pages = sum(b.page_count for b in job.batches)
        documents = len(controller.documents())
        checks = len(self.kontrol.strip.check_rows) if self.kontrol else 0
        text = f"{documents} belge · {pages} sayfa"
        if checks:
            text += f" · {checks} belge kontrol bekliyor"
        self.counts.setText(text)

    def _tab_changed(self, index: int) -> None:
        if index == 2:
            self.sablon.refresh_templates()
        elif index == 3:
            self.degerler.refresh()
        elif index == 4:
            self.disa_aktar.refresh()

    def _draw_variant(self, document: int, variable: str) -> None:
        self.tabs.setCurrentIndex(2)
        controller = self.controller()
        template_id = None
        if controller is not None:
            from evrakci.pipeline.cuts import document_template

            template_id, _ = document_template(controller.job,
                                               controller.documents()[document - 1])
        if template_id:
            try:
                self.sablon.open_template(template_id)
            except (KeyError, TemplateError):
                return
            self.sablon.select_variable(variable)
            self.sablon.set_example(document)
            self.sablon.draw_button.setChecked(True)

    # Closing
    def closeEvent(self, event) -> None:
        if self.disa_aktar.busy() or self.yukle.busy():
            answer = QMessageBox.question(
                self, "Evrakçı",
                "Bir iş sürüyor. Durdurup kapatılsın mı? Yazılmış dosyalar klasörde kalır.",
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.disa_aktar.cancel()
            self.yukle.cancel()
        event.accept()
