"""One shared reading engine for the screens, and its start-up warm-up.

`engine.available()` can take a third of a second (it looks for the program on disk), so it is
only ever called in a worker; the engine remembers the answer, and `warm_up` asks once after
start-up so the first "Oku" already has it.
"""

from __future__ import annotations

import threading

from evrakci.ui.workers import Task, start

_lock = threading.Lock()
_engine = None


def shared_engine():
    """The default engine, made once. Making it can read the disk (it looks for the program and
    checks the language data), so call it in a worker; the window thread uses `cached_engine`."""
    global _engine
    with _lock:
        if _engine is None:
            from evrakci.pipeline.ocr.tesseract import default_engine

            _engine = default_engine()
        return _engine


class LazyEngine:
    """Stands for the shared engine on the window thread: making the real one (which reads the
    disk) waits for the first call, and that call is made in a worker."""

    def __getattr__(self, name: str):
        return getattr(shared_engine(), name)


def cached_engine():
    """The engine if a worker has already made it, else None; never touches the disk and never
    waits on the lock a worker holds while making it."""
    return _engine


def warm_up() -> Task:
    """Probe the default engine in a worker; the answer stays cached in the engine."""
    return start(Task(lambda _progress: shared_engine().available()))
