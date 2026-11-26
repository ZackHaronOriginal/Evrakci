"""Slow work off the window's thread, with progress and cancel.

`run_background` is the one helper for work that must not block the window (opening a job, the
first read, deleting a job). It shows a loading card after LOADING_SHOW_MS and keeps it up for
at least LOADING_MIN_MS once shown. Thread-safety rules, kept by every worker function:

1. A worker function gets plain data only (paths, ids, dicts, `Job` copies); it never touches a
   QWidget, QPixmap, QAction, the model or the controller. Results come back as signals and are
   applied on the window thread. QImage and PIL images may be made in a worker, QPixmap not.
2. Every PDFium call, in any thread, runs under PDFIUM_LOCK and holds it for one page at a time.
3. A worker reports progress at most about 10 times a second and checks for cancel there.
4. A worker never starts another Task and never calls processEvents.
5. A job file is written from one thread only: the JobSaver's writer (ui/saver.py).
6. A result that arrives after the owner is closed, or after a newer run started, is dropped
   (the caller's on_done also checks its own job id).
7. Python's cycle collector never runs on a worker: `start` installs ui/gc_guard.py (window-
   thread collection) and `Task.run` marks the worker busy, so no full pass stalls the window.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable

import shiboken6
from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, QTimer, Signal
from PySide6.QtWidgets import QWidget

from evrakci.ui import gc_guard
from evrakci.ui.loading import LoadingCard, assert_window_thread

LOADING_SHOW_MS = 300  # no loading card for work that finishes sooner
LOADING_MIN_MS = 400  # once shown, the card stays at least this long (never a flash)
REPORT_EVERY = 0.1  # seconds between redraws of the loading bar
BUSY_REASON = "Bir iş sürüyor; bitince açın."
CANCELLED_TEXT = "İptal edildi; hiçbir şey değişmedi."
_clock = time.monotonic  # the tests replace it


class Cancelled(Exception):
    """Raised inside a task's progress callback when the user cancels."""


class _Signals(QObject):
    progress = Signal(int, int)
    done = Signal(object)
    failed = Signal(str)
    cancelled = Signal()


class Task(QRunnable):
    """Run `work(progress)` in a worker thread.

    `progress(done, total)` reports progress and raises Cancelled after `cancel()`, so the
    core function stops and cleans up exactly as it would after any other error.
    """

    def __init__(self, work: Callable[[Callable[[int, int], None]], object]) -> None:
        super().__init__()
        self.work = work
        self.signals = _Signals()
        self._cancel = threading.Event()

    def cancel(self) -> None:
        self._cancel.set()

    def _progress(self, done: int, total: int) -> None:
        if self._cancel.is_set():
            raise Cancelled()
        self.signals.progress.emit(done, total)

    def run(self) -> None:
        with gc_guard.working():
            try:
                result = self.work(self._progress)
            except Cancelled:
                self.signals.cancelled.emit()
            except Exception as error:  # shown to the user in Turkish; the window keeps working
                self.signals.failed.emit(str(error) or type(error).__name__)
            else:
                self.signals.done.emit(result)


def start(task: Task) -> Task:
    gc_guard.install()  # cyclic garbage is never collected on the worker (ui/gc_guard.py)
    QThreadPool.globalInstance().start(task)
    return task


class Background(QObject):
    """The handle `run_background` returns: `cancel()` and `running`. It lives as long as its
    owner and is deleted with it, so a late signal never reaches a dead widget."""

    finished = Signal()  # after the work ended and its callback ran: the owner syncs its commands

    def __init__(self, owner: QWidget, task: Task, *, title: str, name: str, on_done,
                 on_failed, on_cancelled, cancellable: bool, show_after_ms: int,
                 run: int) -> None:
        super().__init__(owner)
        self._owner, self.task, self.run = owner, task, run
        self._title, self._name, self._cancellable = title, name, cancellable
        self._on_done, self._on_failed, self._on_cancelled = on_done, on_failed, on_cancelled
        self._running = True
        self._cancelled = False
        self._shown_at: float | None = None
        self._last_report = 0.0
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._show_card)
        self._timer.start(show_after_ms)
        self._close_timer: QTimer | None = None  # the delayed close of the card (minimum time)
        queued = Qt.ConnectionType.QueuedConnection
        task.signals.progress.connect(self._progress, queued)
        task.signals.done.connect(self._done, queued)
        task.signals.failed.connect(self._failed, queued)
        task.signals.cancelled.connect(self._stopped, queued)

    @property
    def running(self) -> bool:
        return self._running

    @property
    def cancellable(self) -> bool:
        return self._cancellable and not self._cancelled

    def take_over(self) -> float | None:
        """A new job starts while this one's card waits for its minimum time: the new job
        inherits that card (and the time it was shown), so no late close hits the new job."""
        timer = self._close_timer
        if timer is None or not timer.isActive():
            return None
        timer.stop()
        return self._shown_at

    def cancel(self) -> None:
        """Stop the work where it can stop; its result is dropped and on_cancelled runs."""
        if not self._running or not self._cancellable or self._cancelled:
            return
        self._cancelled = True
        self.task.cancel()
        if self._shown_at is not None:
            _card(self._owner).show_cancelling()

    def _show_card(self) -> None:
        if not self._running:
            return
        card = _card(self._owner)
        card.show_loading(self._title, self._name, self._cancellable)
        self._shown_at = _clock()

    def _progress(self, done: int, total: int) -> None:
        now = _clock()
        if self._shown_at is None or self._cancelled or (
                now - self._last_report < REPORT_EVERY and done < total):
            return
        self._last_report = now
        _card(self._owner).show_progress(done, total)

    def _finish(self) -> None:
        """The work ended: free the slot at once, hide the card after its minimum time."""
        self._running = False
        self._timer.stop()
        if self._shown_at is None:
            return
        left = LOADING_MIN_MS - round((_clock() - self._shown_at) * 1000)
        if left > 0:
            self._close_timer = QTimer(self)
            self._close_timer.setSingleShot(True)
            self._close_timer.timeout.connect(self._close_card)
            self._close_timer.start(left)
        else:
            self._close_card()

    def _release(self) -> None:
        """Done: drop the task and callbacks, so what they hold (a deleted job's controller
        and undo history) is freed while this small handle stays as the owner's last one."""
        self.task = None
        self._on_done = self._on_failed = self._on_cancelled = None

    def _close_card(self) -> None:
        """Hide the card, unless a newer job has taken it over (its card must stay)."""
        if shiboken6.isValid(self._owner) and _current(self._owner) is self:
            _card(self._owner).close()

    def _dropped(self) -> bool:
        """The owner was closed or deleted: a late result is dropped (rule 6)."""
        owner = self._owner
        if isinstance(owner, QObject) and not shiboken6.isValid(owner):
            return True
        return bool(getattr(owner, "_closed", False))

    def _done(self, result: object) -> None:
        stale = self._cancelled or _current(self._owner) is not self
        self._finish()
        try:
            if self._dropped():
                pass
            elif stale:
                self._call(self._on_cancelled)
            else:
                self._on_done(result)
        finally:
            self._release()
            self.finished.emit()

    def _failed(self, message: str) -> None:
        stale = _current(self._owner) is not self
        cancelled = self._cancelled
        self._finish()
        try:
            if self._dropped():
                pass
            elif cancelled and not stale:  # the user cancelled: an error now is not news
                self._call(self._on_cancelled)
            elif not stale and self._on_failed is not None:
                self._on_failed(message)
        finally:
            self._release()
            self.finished.emit()

    def _stopped(self) -> None:
        self._finish()
        try:
            if not self._dropped():
                self._call(self._on_cancelled)
        finally:
            self._release()
            self.finished.emit()

    @staticmethod
    def _call(callback) -> None:
        if callback is not None:
            callback()


def _current(owner: QWidget) -> Background | None:
    return getattr(owner, "_background", None)


def _card(owner: QWidget) -> LoadingCard:
    """The owner's loading card (a window supplies its own as `loading_card`, over its tab body)."""
    assert_window_thread()
    card = getattr(owner, "loading_card", None)
    if card is None or not shiboken6.isValid(card):
        card = LoadingCard(owner)
        owner.loading_card = card
    if not card.property("cancelWired"):
        card.setProperty("cancelWired", True)
        card.cancel_requested.connect(lambda: (_current(owner) or _Nothing).cancel())
    return card


class _Nothing:
    @staticmethod
    def cancel() -> None:
        return None


def run_background(owner: QWidget, work: Callable[[Callable[[int, int], None]], object], *,
                   title: str, name: str = "", on_done: Callable[[object], None],
                   on_failed: Callable[[str], None] | None = None,
                   on_cancelled: Callable[[], None] | None = None, cancellable: bool = True,
                   show_after_ms: int = LOADING_SHOW_MS) -> Background | None:
    """Run `work(progress)` in a worker; apply its result with `on_done(result)` on the window
    thread. Returns None, doing nothing, while another loading job of this owner runs (the
    caller shows BUSY_REASON). `on_failed(message)` gets the error text; `on_cancelled()` runs
    after a cancel, and then no result is applied."""
    assert_window_thread()
    previous = _current(owner)
    if previous is not None and previous.running:
        return None
    run = (previous.run + 1) if previous is not None else 1
    task = Task(work)
    inherited = previous.take_over() if previous is not None else None
    handle = Background(owner, task, title=title, name=name, on_done=on_done,
                        on_failed=on_failed, on_cancelled=on_cancelled,
                        cancellable=cancellable, show_after_ms=show_after_ms, run=run)
    if inherited is not None:  # the card is still up from the job before: reuse it at once
        handle._timer.stop()
        owner._background = handle
        handle._show_card()
        handle._shown_at = inherited
    owner._background = handle
    start(task)
    return handle
