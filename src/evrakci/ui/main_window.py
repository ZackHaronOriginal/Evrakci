"""The main window: six tabs over the same core as the command line."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QTabWidget,
    QWidget,
)

from evrakci import __version__
from evrakci.pipeline.store import JobFileError, JobStore
from evrakci.pipeline.templates.model import TemplateError
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.ui import icons, theme
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

# The key list at the right of the status bar, per tab (DESIGN.md: Status bar).
TAB_KEYS = [
    [("Ctrl+N", "yeni iş"), ("Ctrl+O", "dosya seç"), ("Alt+↑ ↓", "sırala")],
    [("Ctrl+1…5", "sekmeler"), ("← →", "sayfa"), ("Shift", "seçimi genişlet"),
     ("N", "sonraki kontrol")],
    [("B", "kutu çiz"), ("Ctrl+T", "dene"), ("Ctrl+S", "kaydet")],
    [("Enter", "öneriyi kabul et"), ("F2", "elle yaz"), ("N", "sonraki kontrol")],
    [("Ctrl+E", "dışa aktar"), ("Esc", "iptal")],
    [("Ctrl+1…5", "sekmeler"), ("F1", "rehber")],
]


def _keys_html(keys: list[tuple[str, str]]) -> str:
    white = theme.TOKENS["on_shell"]
    return "&nbsp;&nbsp;&nbsp;&nbsp;".join(
        f'<b style="color:{white}">{key}</b> {word}' for key, word in keys)


class HeaderBar(QWidget):
    """The 40px shell band: app name, the open job, and when it was last saved."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("header")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(40)
        row = QHBoxLayout(self)
        row.setContentsMargins(20, 0, 20, 0)
        row.setSpacing(14)
        mark = QLabel()
        mark.setPixmap(icons.app_icon().pixmap(22, 22))
        name = QLabel("Evrakçı")
        name.setObjectName("app-name")
        self.job = QLabel("İş açılmadı")
        row.addWidget(mark)
        row.addWidget(name)
        row.addWidget(self.job, 1)
        self.saved_icon = QLabel()
        self.saved_icon.setPixmap(icons.pixmap("save", "on_shell_2", 16))
        self.saved = QLabel("")
        row.addWidget(self.saved_icon)
        row.addWidget(self.saved)
        self.saved_icon.hide()

    def set_saved(self, when: datetime) -> None:
        self.saved.setText(f"Kaydedildi {when:%H:%M}")
        self.saved_icon.show()


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
        self.setWindowIcon(icons.app_icon())
        self.resize(1366, 768)
        self.setMinimumSize(1100, 640)
        self.setPalette(theme.palette())
        self.setStyleSheet(theme.stylesheet())
        self.header = HeaderBar()
        self.setMenuWidget(self.header)
        self.kontrol: KontrolScreen | None = None
        self.thumbnails: ThumbnailService | None = None
        self._closing = False

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.yukle = YukleScreen(store)
        self.yukle.job_opened.connect(self._job_opened)
        self.yukle.can_switch = self._switch_refusal
        self.sablon = SablonScreen(templates, self.controller)
        self.degerler = DegerlerScreen(self.controller, self.template_map)
        self.degerler.draw_variant.connect(self._draw_variant)
        self.disa_aktar = DisaAktarScreen(self.controller, self.template_map, settings_path)
        self.disa_aktar.job_deleted.connect(self._job_deleted)
        self.rehber = RehberScreen()
        self.disa_aktar.finished.connect(self._work_stopped)
        self.yukle.task_finished.connect(self._work_stopped)
        self.degerler.finished.connect(self._work_stopped)
        self._kontrol_placeholder = self._empty_state(
            "Henüz açık iş yok",
            "Kontrol için önce Yükle sekmesinden bir iş açın ya da yeni bir iş oluşturun.")
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
        self.check_icon = QLabel()
        self.check_icon.setPixmap(icons.pixmap("warn", "rider_on_shell", 16))
        self.check_icon.hide()
        self.checks = QLabel("")
        self.message = QLabel("")
        self.message.setProperty("role", "keys")
        self.keys = QLabel("")
        self.keys.setProperty("role", "keys")
        bar = self.statusBar()
        bar.setSizeGripEnabled(False)
        bar.setContentsMargins(14, 0, 14, 0)
        bar.addWidget(self.counts)
        bar.addWidget(self.check_icon)
        bar.addWidget(self.checks)
        bar.addWidget(self.message, 1)
        bar.addPermanentWidget(self.keys)
        self._tab_changed(self.tabs.currentIndex())
        self.yukle.refused.connect(self.message.setText)
        self._open_last_job()

    def _empty_state(self, title: str, text: str) -> QWidget:
        from PySide6.QtWidgets import QVBoxLayout

        from evrakci.ui.widgets import key_button

        page = QWidget()
        page.setObjectName("page")
        layout = QVBoxLayout(page)
        layout.addStretch(2)
        for widget in (QLabel(), QLabel(title), QLabel(text)):
            widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(widget)
        picture, heading, words = (layout.itemAt(i).widget() for i in (1, 2, 3))
        picture.setPixmap(icons.pixmap("folder", "rule_strong", 56, stroke=1.25))
        heading.setProperty("role", "panel-title")
        words.setProperty("role", "muted")
        words.setWordWrap(True)
        go = key_button("Yükle'ye git", "Ctrl+1", icon="chl")
        go.clicked.connect(lambda: self.tabs.setCurrentIndex(0))
        layout.addSpacing(8)
        layout.addWidget(go, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(3)
        return page

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
        if self.thumbnails is not None:
            self.thumbnails.stop()  # the previous job's renders are no longer wanted
        self.thumbnails = ThumbnailService(
            job_renderer(job, lambda: self.store.batch_files(job)), height=110, parent=self)
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
        controller.job_changed.connect(self._saved)
        self.setWindowTitle(f"Evrakçı {__version__} – {job.name}")
        self._update_counts()

    def _job_deleted(self) -> None:
        (self.store.root / LAST_JOB).unlink(missing_ok=True)
        self.yukle.refresh_jobs()

    def _saved(self) -> None:
        self.header.set_saved(datetime.now())

    def _update_counts(self) -> None:
        controller = self.controller()
        if controller is None:
            self.counts.setText("")
            self.checks.setText("")
            self.check_icon.hide()
            self.header.job.setText("İş açılmadı")
            return
        job = controller.job
        pages = sum(b.page_count for b in job.batches)
        documents = len(controller.documents())
        checks = len(self.kontrol.strip.check_rows) if self.kontrol else 0
        text = f"{documents} belge  ·  {pages} sayfa"
        self.counts.setText(text + ("  ·" if checks else ""))
        self.check_icon.setVisible(bool(checks))
        self.checks.setText(f"{checks} belge kontrol bekliyor" if checks else "")
        self.header.job.setText(
            f"{job.name}  ·  {len(job.batches)} parti  ·  {pages} sayfa")

    def _tab_changed(self, index: int) -> None:
        if hasattr(self, "keys") and 0 <= index < len(TAB_KEYS):
            self.keys.setText(_keys_html(TAB_KEYS[index]))
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
    def _switch_refusal(self) -> str | None:
        if self._busy_screens():
            return "Dışa aktarma ya da okuma sürüyor; bitince başka bir iş açın."
        return None

    def _busy_screens(self) -> list:
        return [s for s in (self.disa_aktar, self.yukle, self.degerler) if s.busy()]

    def closeEvent(self, event) -> None:
        busy = self._busy_screens()
        if busy and not self._closing:
            answer = QMessageBox.question(
                self, "Evrakçı",
                "Bir iş sürüyor. Durdurup kapatılsın mı? Yazılmış dosyalar klasörde kalır.",
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self._closing = True
            for screen in busy:
                screen.cancel()
        if busy:  # close once the work has stopped (see _work_stopped)
            self.message.setText("Durduruluyor… Pencere iş durunca kapanır.")
            event.ignore()
            return
        event.accept()

    def _work_stopped(self) -> None:
        if self._closing and not self._busy_screens():
            QTimer.singleShot(0, self.close)
