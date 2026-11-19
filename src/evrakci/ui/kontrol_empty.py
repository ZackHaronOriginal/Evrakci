"""Kontrol with no job open (final-a kontrol `?state=empty`).

The layout's skeleton stays (the command bar is there, disabled); the page says what belongs
here and offers the way to it: "Henüz açık iş yok", one sentence, the primary "Yükle'ye git"
(Ctrl+1), "Yeni iş oluştur" and the recent jobs as Settings-style rows (a click opens one).
The status bar says where jobs open.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from evrakci.ui import actions, icons, theme
from evrakci.ui.chrome import RecentJobRow, make_icon
from evrakci.ui.yukle_side import GapButton

RECENT_W = 440  # A .recent width
MARK = 48  # A .empty-state .mark


_JobRow = RecentJobRow  # shared with Yükle's empty page (chrome.RecentJobRow)


class KontrolEmpty(QWidget):
    """The Kontrol page while no job is open.

    `go_yukle()` shows Yükle, `new_job()` starts a job, `recent()` lists (name, "640 sayfa,
    dün", open callback) of the last jobs."""

    def __init__(self, go_yukle: Callable[[], None], new_job: Callable[[], None],
                 recent: Callable[[], list[tuple[str, str, Callable[[], None]]]] = list,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("page")
        self.setAccessibleName("Kontrol: açık iş yok")
        self._recent = recent
        m = theme.manager()
        outer = QVBoxLayout(self)
        outer.addStretch(1)
        column = QVBoxLayout()
        column.setSpacing(0)
        column.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.mark = QLabel()
        self.mark.setFixedSize(MARK, MARK)
        self.mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mark.setProperty("kind", "card")
        self.mark.setAccessibleName("")
        self.title = QLabel("Henüz açık iş yok")
        self.title.setProperty("textRole", "panel")
        self.text = QLabel("Kesimleri görmek için Yükle'den bir iş açın.")
        self.text.setProperty("textRole", "secondary")
        self.text.setContentsMargins(0, m.size("s1"), 0, 0)
        for widget in (self.mark, self.title, self.text):
            column.addWidget(widget, 0, Qt.AlignmentFlag.AlignHCenter)
            if widget is self.mark:
                column.addSpacing(m.size("s4"))
        buttons = QHBoxLayout()
        buttons.setSpacing(m.size("s2"))
        buttons.addStretch(1)
        key = actions.key_text("Ctrl+1")
        self.go_button = QPushButton()
        self.go_button.setProperty("variant", "primary")
        self.go_button.setProperty("sizeVariant", "lg")
        inside = QHBoxLayout(self.go_button)  # A: icon, "Yükle'ye git", the key in caption
        inside.setContentsMargins(m.size("s4"), 0, m.size("s4"), 0)
        inside.setSpacing(m.size("s2"))
        self.go_icon, self.go_text, self.go_key = QLabel(), QLabel("Yükle'ye git"), QLabel(key)
        for label in (self.go_icon, self.go_text, self.go_key):
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            if label is self.go_key:  # A: s3 before the key hint, s2 after the icon
                inside.addSpacing(m.size("s3") - m.size("s2"))
            inside.addWidget(label)
        self.go_icon.setFixedSize(16, 16)
        self.go_button.setAccessibleName(f"Yükle'ye git ({key})")
        self.go_button.setToolTip(f"Yükle sekmesine geç ({key})")
        self.go_button.clicked.connect(go_yukle)
        self.new_button = GapButton("Yeni iş oluştur")  # icon, s2, label (A .btn)
        self.new_button.setProperty("sizeVariant", "lg")
        self.new_button.setToolTip(f"Yeni iş oluştur ({actions.key_text('Ctrl+N')})")
        self.new_button.clicked.connect(new_job)
        buttons.addWidget(self.go_button)
        buttons.addWidget(self.new_button)
        buttons.addStretch(1)
        column.addSpacing(m.size("s6"))
        column.addLayout(buttons)
        self.recent_box = QWidget()
        self.recent_box.setFixedWidth(round(RECENT_W * m.text_scale() / 100))
        self.recent_box.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        recent_col = QVBoxLayout(self.recent_box)
        recent_col.setContentsMargins(0, m.size("s8"), 0, 0)
        recent_col.setSpacing(0)
        label = QLabel("Son işler")
        label.setProperty("kind", "group-label")
        recent_col.addWidget(label)
        self.card = QFrame()
        self.card.setProperty("kind", "card")
        self.rows = QVBoxLayout(self.card)
        pad = m.size("s1")
        self.rows.setContentsMargins(pad, pad, pad, pad)
        self.rows.setSpacing(0)
        recent_col.addWidget(self.card)
        column.addWidget(self.recent_box, 0, Qt.AlignmentFlag.AlignHCenter)
        outer.addLayout(column)
        outer.addStretch(2)
        theme.follow(self, self.refresh)
        self.refresh()

    def refresh(self) -> None:
        """Icons for the theme and the recent jobs as they are now."""
        m = theme.manager()
        self.mark.setPixmap(icons.pixmap("layout-grid", m.hex("icon"), 24))
        on = m.hex("text-on-accent")
        self.go_icon.setPixmap(icons.pixmap("upload", on, 16))
        self.go_text.setStyleSheet(f"color: {on}; font-weight: 600;")
        self.go_key.setStyleSheet(f"color: {on}; font-size: {m.size('fs-caption')}px;")
        self.go_button.setMinimumWidth(self.go_button.layout().sizeHint().width())
        self.new_button.setIcon(make_icon("file-plus"))
        while self.rows.count():
            item = self.rows.takeAt(0)
            if item.widget() is not None:
                item.widget().hide()
                item.widget().deleteLater()
        jobs = self._recent()[:3]
        for name, detail, open_job in jobs:
            row = _JobRow(name, detail)
            row.clicked.connect(open_job)
            self.rows.addWidget(row)
            row.show()
        self.recent_box.setVisible(bool(jobs))

    def showEvent(self, event) -> None:  # noqa: N802
        self.refresh()
        super().showEvent(event)


def for_window(window) -> KontrolEmpty:
    """The empty Kontrol page wired to a MainWindow (Yükle'ye git, Yeni iş oluştur, the
    recent jobs) with the Kontrol status line. For `MainWindow._build_screens`:
    ``self._kontrol_placeholder = kontrol_empty.for_window(self)``."""
    from evrakci.ui.kontrol_actions import KontrolStatus

    def recent() -> list[tuple[str, str, Callable[[], None]]]:
        found = []
        for job, when in window.recent_jobs():
            pages = sum(batch.page_count for batch in job.batches)
            found.append((job.name, f"{pages} sayfa, {when}",
                          lambda job=job: window.yukle.open_job(job)))
        return found

    page = KontrolEmpty(lambda: window.show_tab("yukle"),
                        lambda: window.registry.action("app.yeni_is").trigger(), recent)
    if getattr(window, "_slots", None):  # else the window fills the slot once it is built
        KontrolStatus.in_slot(window.status_slot("kontrol")).set_empty()
    return page
