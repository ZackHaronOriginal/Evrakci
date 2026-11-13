"""Small parts of Şablonlar: the undo command (the status-bar item is widgets.StatusPart)."""

from __future__ import annotations

from PySide6.QtGui import QUndoCommand


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
