"""The two cards above "Ön kontrol" while and after writing (A's `.banner`): the progress card
and the outcome card (96 belge yazıldı / durduruldu / yazılamadı) with its open buttons."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from evrakci.ui import icons, theme
from evrakci.ui.chrome import make_icon
from evrakci.ui.disa_aktar_parts import PartsButton, tint


class RunBanner(QFrame):
    """"Yazılıyor: 58 / 96  metin katmanı ekleniyor", an 8 px bar and one caption line."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setProperty("kind", "card")
        col = QVBoxLayout(self)
        col.setSpacing(theme.manager().size("s2"))
        top = QHBoxLayout()
        top.setSpacing(theme.manager().size("s2"))
        self.icon = QLabel()
        self.icon.setFixedSize(20, 20)
        self.count = QLabel("Yazılıyor…")
        self.stage = QLabel("")
        self.stage.setProperty("textRole", "secondary")
        top.addWidget(self.icon)
        top.addWidget(self.count)
        top.addWidget(self.stage, 1)
        col.addLayout(top)
        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        self.bar.setAccessibleName("Yazma ilerlemesi")
        self.bar.setStyleSheet("QProgressBar { min-height: 8px; max-height: 8px; }")
        self.bar.setFixedHeight(8)
        col.addWidget(self.bar)
        self.sub = QLabel("")
        self.sub.setProperty("textRole", "caption")
        self.sub.setProperty("kind", "inspector-key")
        self.sub.setWordWrap(True)
        col.addWidget(self.sub)
        self.setAccessibleName("Yazma ilerlemesi")
        theme.follow(self, self._restyle, "run")

    def _restyle(self) -> None:
        m = theme.manager()
        s4 = m.size("s4")
        self.layout().setContentsMargins(s4, s4, s4, s4)
        self.icon.setPixmap(icons.pixmap("loader-circle", m.hex("accent"), 20))
        self.count.setFont(m.font("num-strong"))

    def set_progress(self, done: int, total: int, stage: str, sub: str) -> None:
        self.bar.setRange(0, max(1, total))
        self.bar.setValue(done)
        self.count.setText(f"Yazılıyor: {done} / {total}")
        self.stage.setText(stage)
        self.sub.setText(sub)

    def start(self, sub: str) -> None:
        self.bar.setRange(0, 0)  # busy until the first report
        self.count.setText("Yazılıyor…")
        self.stage.setText("")
        self.sub.setText(sub)


class OutcomeBanner(QFrame):
    """How the export ended: a 24 px icon, a panel title, a sentence, the Kontrol line and the
    open buttons. `message` is the sentence."""

    open_folder = Signal()
    open_index = Signal()
    reveal = Signal()
    closed = Signal()

    KINDS = {  # kind: (icon, role)
        "done": ("folder-check", "ok"),
        "stopped": ("info", "icon"),
        "failed": ("circle-x", "danger"),
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setProperty("kind", "card")
        self.kind = "done"
        m = theme.manager()
        row = QHBoxLayout(self)
        row.setSpacing(m.size("s4"))
        self.icon = QLabel()
        self.icon.setFixedSize(24, 24)
        row.addWidget(self.icon, 0, Qt.AlignmentFlag.AlignTop)
        col = QVBoxLayout()
        col.setSpacing(m.size("s2"))
        self.title = QLabel()
        self.title.setProperty("textRole", "panel")
        self.message = QLabel()
        self.message.setProperty("textRole", "secondary")
        self.message.setWordWrap(True)
        self.message.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        col.addWidget(self.title)
        col.addWidget(self.message)
        self.check_line = QWidget()
        line = QHBoxLayout(self.check_line)
        line.setContentsMargins(0, 0, 0, 0)
        line.setSpacing(m.size("s2"))
        self.check_icon = QLabel()
        self.check_icon.setFixedSize(16, 16)
        self.check_word = QLabel("Kontrol")
        self.check_text = QLabel()
        self.check_text.setWordWrap(True)
        line.addWidget(self.check_icon)
        line.addWidget(self.check_word)
        line.addWidget(self.check_text, 1)
        col.addWidget(self.check_line)
        buttons = QHBoxLayout()
        buttons.setSpacing(m.size("s2"))
        self.folder_button = PartsButton("Klasörü aç", "folder-open", primary=True)
        self.index_button = PartsButton("index.xlsx'i aç", "table")
        self.reveal_button = PartsButton("Dosya Gezgini'nde göster", "folder-open")
        for button, signal in ((self.folder_button, self.open_folder),
                               (self.index_button, self.open_index),
                               (self.reveal_button, self.reveal)):
            button.clicked.connect(signal)
            buttons.addWidget(button)
        buttons.addStretch(1)
        self.buttons = QWidget()
        self.buttons.setLayout(buttons)
        buttons.setContentsMargins(0, m.size("s1"), 0, 0)
        col.addWidget(self.buttons)
        row.addLayout(col, 1)
        self.close_button = QPushButton()
        self.close_button.setProperty("variant", "subtle")
        self.close_button.setToolTip("Mesajı kapat")
        self.close_button.setAccessibleName("Mesajı kapat")
        self.close_button.clicked.connect(self.closed)
        row.addWidget(self.close_button, 0, Qt.AlignmentFlag.AlignTop)
        tint(self.check_word, "check-text")
        tint(self.check_text, "text")
        theme.follow(self, self._restyle, "outcome")

    def _restyle(self) -> None:
        m = theme.manager()
        s4 = m.size("s4")
        self.layout().setContentsMargins(s4, s4, s4, s4)
        icon, role = self.KINDS[self.kind]
        self.icon.setPixmap(icons.pixmap(icon, m.hex(role), 24))
        self.check_icon.setPixmap(icons.pixmap("triangle-alert", m.hex("check-text"), 16))
        self.check_word.setFont(m.font("body-strong"))
        self.close_button.setIcon(make_icon("x", "icon", m.size("icon-sm")))
        self.close_button.setFixedWidth(m.size("control-h"))

    def show_outcome(self, kind: str, title: str, message: str, check: str = "",
                     folder: bool = False, index: bool = False, reveal: bool = False,
                     closable: bool = False) -> None:
        self.kind = kind
        self.title.setText(title)
        self.message.setText(message)
        self.check_line.setVisible(bool(check))
        self.check_text.setText(check)
        self.folder_button.setVisible(folder)
        self.index_button.setVisible(index)
        self.reveal_button.setVisible(reveal)
        self.buttons.setVisible(folder or index or reveal)
        self.close_button.setVisible(closable)
        self.setAccessibleName(f"{title}. {message}")
        self._restyle()
