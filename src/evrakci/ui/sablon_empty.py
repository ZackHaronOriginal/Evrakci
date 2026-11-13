"""Empty states of Şablonlar (final-a sablonlar.html `empty`): A's empty-state component, a 48 px
mark, one heading, one sentence, a primary and a secondary action, and a quiet note, centred in
the well. The states A does not draw (no example page) reuse it."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from evrakci.ui import theme
from evrakci.ui.chrome import make_icon

MARK = 48


class EmptyState(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        m = theme.manager()
        col = QVBoxLayout(self)
        col.setContentsMargins(m.size("s6"), 0, m.size("s6"), m.size("s8"))
        col.setSpacing(0)
        col.addStretch(1)
        self.mark = QLabel()
        self.mark.setFixedSize(MARK, MARK)
        self.mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mark.setProperty("kind", "card")
        col.addWidget(self.mark, 0, Qt.AlignmentFlag.AlignHCenter)
        col.addSpacing(m.size("s4"))
        self.title = QLabel()
        self.title.setProperty("textRole", "panel")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text = QLabel()
        self.text.setProperty("textRole", "secondary")
        self.text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text.setWordWrap(True)
        col.addWidget(self.title)
        col.addSpacing(m.size("s1"))
        col.addWidget(self.text)
        col.addSpacing(m.size("s6"))
        buttons = QHBoxLayout()
        buttons.setSpacing(m.size("s2"))
        buttons.addStretch(1)
        self.primary = QPushButton()
        self.primary.setProperty("variant", "primary")
        self.secondary = QPushButton()
        for button in (self.primary, self.secondary):
            button.setProperty("sizeVariant", "lg")
            buttons.addWidget(button)
        buttons.addStretch(1)
        col.addLayout(buttons)
        col.addSpacing(m.size("s3"))
        self.note = QLabel()
        self.note.setProperty("textRole", "caption")
        self.note.setProperty("kind", "inspector-key")
        self.note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.note.setWordWrap(True)
        col.addWidget(self.note)
        col.addStretch(1)
        self._actions: dict[QPushButton, Callable[[], None] | None] = {}
        self._icons: dict[QPushButton, str] = {}
        self._mark = "layout-template"
        for button in (self.primary, self.secondary):
            button.clicked.connect(lambda _c=False, b=button: self._run(b))
        theme.follow(self, self._restyle, "sablon-empty")

    def _run(self, button: QPushButton) -> None:
        action = self._actions.get(button)
        if action is not None:
            action()

    def _restyle(self) -> None:
        m = theme.manager()
        self.mark.setPixmap(make_icon(self._mark, size=24).pixmap(24, 24))
        for button, icon in self._icons.items():
            role = "text-on-accent" if button is self.primary else "icon"
            button.setIcon(make_icon(icon, role, m.size("icon-sm")))
            button.setMinimumHeight(m.size("lg-h"))

    def show_state(self, mark: str, title: str, text: str,
                   primary: tuple[str, str, Callable[[], None]] | None = None,
                   secondary: tuple[str, str, Callable[[], None]] | None = None,
                   note: str = "") -> None:
        self._mark = mark
        self.title.setText(title)
        self.text.setText(text)
        self.note.setText(note)
        self.note.setVisible(bool(note))
        self.setAccessibleName(title)
        for button, spec in ((self.primary, primary), (self.secondary, secondary)):
            button.setVisible(spec is not None)
            if spec is not None:
                label, icon, action = spec
                button.setText(f" {label}")  # Qt's icon gap + a space = A's s2
                button.setAccessibleName(label)
                self._actions[button] = action
                self._icons[button] = icon
        self._restyle()
