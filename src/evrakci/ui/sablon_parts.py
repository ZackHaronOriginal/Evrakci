"""Small parts of Şablonlar: one status-bar count (A .statusbar) and the undo command."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QUndoCommand
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QWidget

from evrakci.ui import icons, theme


class StatusPart(QWidget):
    """One status-bar item: an optional 14 px icon and rich text whose odd parts are the
    strong, text-coloured figures: set("Örnek ", "1", " / 4")."""

    def __init__(self, icon: str | None = None, role: str = "icon", parent=None) -> None:
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)  # A .statusbar .warn gap
        self.icon_name, self.role = icon, role
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self.icon = QLabel()
        self.icon.setFixedSize(14, 14)
        self.label = QLabel()
        self.label.setTextFormat(Qt.TextFormat.RichText)
        row.addWidget(self.icon)
        row.addWidget(self.label)
        self.icon.setVisible(bool(icon))
        self.parts: tuple[str, ...] = ()
        theme.follow(self, self._restyle, f"sablon-status-{id(self)}")

    def set_icon(self, icon: str | None, role: str) -> None:
        self.icon_name, self.role = icon, role
        self.icon.setVisible(bool(icon))
        self._restyle()

    def _restyle(self) -> None:
        m = theme.manager()
        if self.icon_name:
            self.icon.setPixmap(icons.pixmap(self.icon_name, m.hex(self.role), 14))
        self.set(*self.parts)

    def set(self, *parts: str) -> None:
        self.parts = parts
        m = theme.manager()
        html = "".join(
            f"<span style='color:{m.hex('text')}; font-weight:600'>{p}</span>" if i % 2 else p
            for i, p in enumerate(parts))
        self.label.setText(html)
        plain = "".join(parts)
        self.setAccessibleName(plain)
        self.label.setAccessibleName(plain)

    def text(self) -> str:
        return "".join(self.parts)


class TemplateEdit(QUndoCommand):
    """One undoable change of the template; the same box changed again in a row (arrow keys,
    a field) merges into one step, so Ctrl+Z undoes the whole nudge."""

    def __init__(self, screen, text: str, before: dict, after: dict, merge_id: int = -1) -> None:
        super().__init__(text)
        self.screen, self.before, self.after, self.first = screen, before, after, True
        self._id = merge_id

    def id(self) -> int:
        return self._id

    def mergeWith(self, other: QUndoCommand) -> bool:  # noqa: N802
        if self._id < 0 or other.id() != self._id:
            return False
        self.after = other.after
        return True

    def redo(self) -> None:
        if self.first:
            self.first = False
            return
        self.screen._restore(self.after)

    def undo(self) -> None:
        self.screen._restore(self.before)


def small_button_style(side: int) -> str:
    """A .iconbtn.sm: `side` px square, border included. The app stylesheet's `[size="sm"]` rule
    cannot match (a dynamic property named "size" is QWidget's own QSize), so the square is set
    here; the QSS box adds the 1 px transparent border to min/max sizes."""
    inner = side - 2
    return (f"QToolButton {{ min-width: {inner}px; max-width: {inner}px; "
            f"min-height: {inner}px; max-height: {inner}px; }}")
