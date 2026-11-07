"""One controller per open job: every edit goes through the core, can be undone, and is saved."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QUndoCommand, QUndoStack

from evrakci.pipeline import review
from evrakci.pipeline.cuts import Document, compute_documents, cut_kinds
from evrakci.pipeline.job import Job, job_from_dict, job_to_dict
from evrakci.pipeline.store import JobStore


def _turkish(error: Exception) -> str:
    """A short Turkish message for an error raised by the core."""
    text = str(error).strip("'\"")
    if isinstance(error, KeyError):
        if "/" in text:
            return f"Sayfa bulunamadı: {text}"
        return f"Bulunamadı: {text}"
    if "already cuts" in text or "cut already" in text:
        return "Bu sayfanın önünde zaten bir kesim var."
    if "no cut" in text:
        return "Bu sayfanın önünde kaldırılacak kesim yok."
    if "every_n" in text:
        return "Sayfa sayısı en az 1 olmalı."
    if "rotation" in text:
        return "Döndürme 90 derecenin katı olmalı."
    return f"Yapılamadı: {text}"


class _Snapshot(QUndoCommand):
    """An applied edit, stored as the whole job before and after it."""

    def __init__(self, controller: JobController, text: str, before: dict, after: dict) -> None:
        super().__init__(text)
        self._controller = controller
        self._before = before
        self._after = after
        self._first = True

    def redo(self) -> None:
        if self._first:  # the edit is already applied when the command is pushed
            self._first = False
            return
        self._controller._restore(self._after)

    def undo(self) -> None:
        self._controller._restore(self._before)


class JobController(QObject):
    job_changed = Signal()
    status = Signal(str)

    def __init__(self, store: JobStore, job: Job, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.store = store
        self.job = job
        self.undo_stack = QUndoStack(self)
        self._documents: list[Document] | None = None
        self._kinds: dict[str, str] | None = None

    # Reading
    def documents(self) -> list[Document]:
        if self._documents is None:
            self._documents = compute_documents(self.job)
        return self._documents

    def cut_kinds(self) -> dict[str, str]:
        if self._kinds is None:
            self._kinds = cut_kinds(self.job)
        return self._kinds

    # Edits
    def apply_filter(self, page_ids: Iterable[str], every_n: int) -> bool:
        ids = list(page_ids)
        return self._edit(f"Filtre: her {every_n} sayfa", lambda j: j.apply_filter(ids, every_n))

    def add_cut(self, pid: str) -> bool:
        return self._edit("Kesim ekle", lambda j: j.add_cut(pid))

    def remove_cut(self, pid: str) -> bool:
        return self._edit("Kesimi kaldır", lambda j: j.remove_cut(pid))

    def apply_template(self, page_ids: Iterable[str], template_id: str) -> bool:
        ids = list(page_ids)
        return self._edit("Şablon uygula", lambda j: j.apply_template(ids, template_id))

    def rotate(self, pid: str, degrees: int) -> bool:
        return self._edit("Döndür", lambda j: j.rotate(pid, degrees))

    def delete_page(self, pid: str) -> bool:
        return self._edit("Sayfayı sil", lambda j: j.delete_page(pid))

    def undelete_page(self, pid: str) -> bool:
        return self._edit("Sayfayı geri al", lambda j: j.undelete_page(pid))

    def set_drop_empty(self, value: bool) -> bool:
        def apply(job: Job) -> None:
            job.drop_empty = value

        return self._edit("Boş sayfaları at", apply)

    def set_value(self, document: Document, key: str, text: str) -> bool:
        return self._edit("Değeri düzelt", lambda j: review.set_value(j, document, key, text))

    def accept_suggestion(self, document: Document, key: str) -> bool:
        return self._edit("Öneriyi kabul et", lambda j: review.accept_suggestion(j, document, key))

    def run(self, text: str, change: Callable[[Job], None]) -> bool:
        """Any other core change (for example, recording read values) as one undoable edit."""
        return self._edit(text, change)

    def undo(self) -> None:
        self.undo_stack.undo()

    def redo(self) -> None:
        self.undo_stack.redo()

    # Internals
    def _edit(self, text: str, change: Callable[[Job], None]) -> bool:
        before = job_to_dict(self.job)
        try:
            change(self.job)
        except (ValueError, KeyError, IndexError) as error:
            self._restore(before, notify=False)  # a half-applied change never stays
            self.status.emit(_turkish(error))
            return False
        after = job_to_dict(self.job)
        if after == before:
            return True
        self.undo_stack.push(_Snapshot(self, text, before, after))
        self._changed()
        return True

    def _restore(self, data: dict, notify: bool = True) -> None:
        restored = job_from_dict(data)
        self.job.__dict__.update(restored.__dict__)  # views keep the same Job object
        if notify:
            self._changed()

    def _changed(self) -> None:
        self._documents = None
        self._kinds = None
        self.store.save(self.job)
        self.job_changed.emit()
