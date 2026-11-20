"""Write-behind saving: the window thread hands over a snapshot, one thread writes it.

An edit never waits for the disk. `JobController` makes a snapshot (a plain dict from
`job_to_dict`, never changed afterwards) and calls `JobSaver.submit`. A single writer thread
(one per saver, alive only while there is something to write) takes the newest snapshot, writes
it with `JobStore.save_dict` (atomic tmp + replace) and reports back with a queued signal.

Orderings this keeps:

* Coalescing: while a write runs only the newest later snapshot is kept; older ones are dropped.
  Writes of one job are in order and never overlap (one thread at a time).
* The saver is "idle" when the newest submitted snapshot has been written (as seen by the window
  thread: `_settled` catches up with `_submitted` in `_on_result`). It is "clean" when it is
  idle and that last write worked: the file on disk then equals the job in memory.
* `when_idle(callback)` is the flush: the callback runs on the window thread, at once when the
  saver is already idle, else from the event loop when the last write has finished.
* A frozen saver (the job's folder is being deleted) takes no new snapshot; `wait_idle` lets the
  delete worker wait until the write in flight is over, so a write never recreates the folder.
* A write that hangs (an unreachable network share) must not hold the window: `when_idle` waits at
  most STALL_MS, then reports the OS's timeout text as a failed write and marks the saver
  `stalled` until the write finally ends. The writer thread is a daemon: the process can end.
* "Kaydediliyor…" is announced only after SAVING_SHOW_MS (a quick write on a local disk never
  flickers the title band), at once for a flush that someone waits for.
"""

from __future__ import annotations

import errno
import os
import threading
from collections.abc import Callable

from PySide6.QtCore import QObject, Qt, QTimer, Signal

from evrakci.pipeline.store import JobStore

SAVING_SHOW_MS = 200  # no "Kaydediliyor…" for a write that finishes sooner
STALL_MS = 10_000  # a write that takes longer than this is reported as failed (a hung share)


class JobSaver(QObject):
    saving = Signal()  # the queue is not empty and someone should see it ("Kaydediliyor…")
    saved = Signal()  # the queue is empty and the last write worked
    failed = Signal(str)  # the queue is empty and the last write raised (message for the person)
    _result = Signal(int, str)  # from the writer thread: (sequence number, error or "")

    def __init__(self, store: JobStore, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.store = store
        self.frozen = False  # the job is being deleted: no new snapshot is taken
        self.stalled = False  # a flush gave up waiting for a write that has not ended
        # Window-thread state.
        self._submitted = 0  # sequence number of the newest snapshot handed over
        self._settled = 0  # newest sequence number whose write has been reported
        self._error = ""  # message of the last write when it failed ("" = it worked)
        self._announced = False
        self._waiters: list[Callable[[bool, str], None]] = []
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._announce)
        # Writer-thread state, under the lock.
        self._lock = threading.Condition()
        self._pending: tuple[int, str, dict] | None = None
        self._running = False
        self._result.connect(self._on_result, Qt.ConnectionType.QueuedConnection)

    # -- state (window thread) ------------------------------------------------------------
    @property
    def idle(self) -> bool:
        """Nothing is queued or being written."""
        return self._settled >= self._submitted

    @property
    def error(self) -> str:
        """Why the last finished write failed; "" when it worked or none ran."""
        return self._error

    @property
    def clean(self) -> bool:
        """The file on disk is the newest snapshot that was handed over."""
        return self.idle and not self._error

    # -- handing over (window thread) -----------------------------------------------------
    def submit(self, job_id: str, data: dict) -> None:
        """Queue `data` (a snapshot nobody changes any more) to be written as job `job_id`."""
        if self.frozen:
            return
        was_idle = self.idle
        self._submitted += 1
        failure: tuple[int, str] | None = None
        with self._lock:
            self._pending = (self._submitted, job_id, data)
            if not self._running:
                self._running = True
                # A daemon: every close path waits for the saver to be idle first (the write is
                # atomic, tmp + replace), so a write hung on a dead share cannot keep the process
                # alive after the window is gone.
                try:
                    threading.Thread(target=self._run, name="evrakci-saver", daemon=True).start()
                except Exception as exc:  # e.g. "can't start new thread": report it, not hang
                    self._running = False
                    self._pending = None
                    failure = (self._submitted, str(exc) or type(exc).__name__)
        if failure is not None:
            self._result.emit(*failure)  # queued: the window thread settles it as a failed write
        if was_idle:
            self._announced = False
            self._timer.start(SAVING_SHOW_MS)

    def when_idle(self, callback: Callable[[bool, str], None], announce: bool = True) -> None:
        """Call `callback(ok, error)` on the window thread once everything handed over is
        written (`ok` False with the message when the last write failed). Immediately when the
        saver is idle now. With `announce` the title band says "Kaydediliyor…" at once. When the
        write does not end within STALL_MS the callback gets `ok` False with the OS's timeout
        text (`stalled` is set, `failed` is emitted once), so nobody waits for ever."""
        if self.idle:
            callback(not self._error, self._error)
            return
        self._waiters.append(callback)
        QTimer.singleShot(STALL_MS, self, lambda: self._stall(callback))
        if announce:
            self._announce()

    def _stall(self, callback: Callable[[bool, str], None]) -> None:
        if callback not in self._waiters:  # the write ended in time
            return
        self._waiters.remove(callback)
        message = os.strerror(errno.ETIMEDOUT)
        if not self.stalled:
            self.stalled = True
            self.failed.emit(message)
        callback(False, message)

    @property
    def stall_seconds(self) -> float:
        """How long a worker thread may wait in `wait_idle` before it gives up."""
        return STALL_MS / 1000

    def wait_idle(self, timeout: float | None = None) -> bool:
        """For a worker thread (never the window thread): block until the writer has nothing
        queued and is not writing. Pair it with `frozen` so nothing new can arrive."""
        with self._lock:
            return self._lock.wait_for(lambda: self._pending is None and not self._running,
                                       timeout)

    # -- the writer thread ----------------------------------------------------------------
    def _run(self) -> None:
        ended = False  # the loop set `_running` False itself, under the lock
        try:
            while True:
                with self._lock:
                    item, self._pending = self._pending, None
                    if item is None:
                        self._running = False
                        ended = True
                        self._lock.notify_all()
                        return
                seq, job_id, data = item
                try:
                    self.store.save_dict(job_id, data)
                    error = ""
                except Exception as exc:  # reported; the thread must not die silently
                    error = str(exc) or type(exc).__name__
                try:
                    self._result.emit(seq, error)  # before the thread ends: results stay in order
                except RuntimeError:  # the saver's C++ object is gone (the window was torn down)
                    pass
        finally:
            if not ended:  # an escape (not an Exception): never leave the saver "running"
                with self._lock:
                    self._running = False
                    self._lock.notify_all()

    # -- results (window thread) ----------------------------------------------------------
    def _announce(self) -> None:
        if not self.idle and not self._announced:
            self._announced = True
            self.saving.emit()

    def _on_result(self, seq: int, error: str) -> None:
        if seq <= self._settled:  # an older write reported late
            return
        self._settled = seq
        self.stalled = False  # the write that hung (or any later one) has ended
        if not self.idle:  # a newer snapshot is waiting; only its result counts
            return
        self._timer.stop()
        self._announced = False
        self._error = error
        waiters, self._waiters = self._waiters, []
        if error:
            self.failed.emit(error)
        else:
            self.saved.emit()
        for callback in waiters:  # after the signals: the window shows the state first
            callback(not error, error)
