"""Which documents staff approved on Kontrol ("Belgeyi onayla", Enter): İncelendi / İncelenmedi.

A document is remembered by its exact page list, so any later change to its pages (a cut, a
merge, a page added) makes it İncelenmedi again: an approval never covers pages nobody saw.
Undoing the change brings the document, and with it the approval, back.

The set lives in `incelendi.json` beside the job's `job.json` (the core's job format is left as
it is, D13). Approving is one entry on the job's undo stack ("Geri al: Belgeyi onayla").
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QUndoCommand

from evrakci.pipeline.cuts import Document
from evrakci.ui.controller import JobController

FILE_NAME = "incelendi.json"
FORMAT = 1


def document_key(document: Document) -> str:
    return "|".join(document.page_ids)


class _ReviewCommand(QUndoCommand):
    def __init__(self, store: ReviewStore, keys: list[str], value: bool, text: str) -> None:
        super().__init__(text)
        self._store = store
        self._keys = keys
        self._value = value
        self._before = {key: key in store.keys for key in keys}

    def redo(self) -> None:
        self._store._apply({key: self._value for key in self._keys})

    def undo(self) -> None:
        self._store._apply(self._before)


class ReviewStore(QObject):
    """The approved documents of one job; emits `changed` after every change (and undo)."""

    changed = Signal()

    def __init__(self, controller: JobController, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.keys: set[str] = set()
        self.error = ""
        self._load()

    def path(self) -> Path:
        return Path(self.controller.store.root) / self.controller.job.id / FILE_NAME

    def _load(self) -> None:
        try:
            data = json.loads(self.path().read_text(encoding="utf-8"))
        except FileNotFoundError:
            return
        except (OSError, ValueError):
            self.error = "Onaylanan belgeler okunamadı; onaylar yeniden yapılmalı."
            return
        if isinstance(data, dict) and data.get("format") == FORMAT:
            self.keys = {str(k) for k in data.get("documents", []) if isinstance(k, str)}

    def _save(self) -> None:
        data = {"format": FORMAT, "documents": sorted(self.keys)}
        try:
            self.path().write_text(json.dumps(data, ensure_ascii=False, indent=1),
                                   encoding="utf-8")
            self.error = ""
        except OSError:
            self.error = "Onay kaydedilemedi; iş klasörüne yazılamıyor."
            self.controller.status.emit(self.error)

    def _apply(self, values: dict[str, bool]) -> None:
        for key, value in values.items():
            (self.keys.add if value else self.keys.discard)(key)
        self._save()
        self.changed.emit()

    # Reading
    def is_reviewed(self, document: Document) -> bool:
        return document_key(document) in self.keys

    def reviewed_numbers(self, documents: list[Document] | None = None) -> set[int]:
        """1-based numbers of the approved documents among the current ones."""
        documents = self.controller.documents() if documents is None else documents
        return {n for n, d in enumerate(documents, start=1) if document_key(d) in self.keys}

    # Changing
    def set_reviewed(self, documents: Iterable[Document], value: bool = True,
                     text: str = "Belgeyi onayla") -> bool:
        """Approve (or un-approve) documents as one undoable step; False when nothing changes."""
        keys = [document_key(d) for d in documents]
        keys = [k for k in keys if (k in self.keys) != value]
        if not keys:
            return False
        self.controller.undo_stack.push(_ReviewCommand(self, keys, value, text))
        return True
