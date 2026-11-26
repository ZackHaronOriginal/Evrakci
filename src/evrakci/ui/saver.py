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
import itertools
import os
import threading
import weakref
from collections.abc import Callable

import shiboken6
from PySide6.QtCore import QObject, Qt, QTimer, Signal

from evrakci.pipeline.store import JobStore
from evrakci.ui import gc_guard

SAVING_SHOW_MS = 200  # no "Kaydediliyor…" for a write that finishes sooner
STALL_MS = 10_000  # a write that takes longer than this is reported as failed (a hung share)


class _Relay(QObject):
    """The one door from writer threads to the window thread. It lives for the whole process
    (created on the window thread by the first saver), so a writer thread never owns the last
    reference to a QObject: Qt objects must be destroyed on their own thread, and a saver that
    was dropped while a write was in flight used to be destroyed by the writer thread (killTimer
    from another thread, then a crash in the next `processEvents`)."""

    result = Signal(int, int, str)  # (saver token, sequence number, error or "")

    def __init__(self) -> None:
        super().__init__()
        self.result.connect(self._deliver, Qt.ConnectionType.QueuedConnection)

    def _deliver(self, token: int, seq: int, error: str) -> None:
        saver = _SAVERS.get(token)
        if saver is not None and shiboken6.isValid(saver):  # a saver that is gone: nobody to tell
            saver._on_result(seq, error)


_SAVERS: weakref.WeakValueDictionary[int, JobSaver] = weakref.WeakValueDictionary()
_TOKENS = itertools.count(1)
_relay: _Relay | None = None


class _Core:
    """What the writer thread shares with its saver, under one lock. Plain Python: the thread
    holds this and the relay, never the saver (a QObject)."""

    def __init__(self, store: JobStore, token: int, relay: _Relay) -> None:
        self.store = store
        self.token = token
        self.relay = relay
        self.lock = threading.Condition()
        self.pending: tuple[int, str, dict] | None = None
        self.running = False

    def run(self) -> None:
        with gc_guard.working():
            self._run()

    def _run(self) -> None:
        ended = False  # the loop set `running` False itself, under the lock
        try:
            while True:
                with self.lock:
                    item, self.pending = self.pending, None
                    if item is None:
                        self.running = False
                        ended = True
                        self.lock.notify_all()
                        return
                seq, job_id, data = item
                try:
                    self.store.save_dict(job_id, data)
                    error = ""
                except Exception as exc:  # reported; the thread must not die silently
                    error = str(exc) or type(exc).__name__
                try:
                    self.relay.result.emit(self.token, seq, error)  # results stay in order
                except RuntimeError:  # the relay's C++ object is gone (the process is ending)
                    pass
        finally:
            if not ended:  # an escape (not an Exception): never leave the saver "running"
                with self.lock:
                    self.running = False
                    self.lock.notify_all()


class JobSaver(QObject):
    saving = Signal()  # the queue is not empty and someone should see it ("Kaydediliyor…")
    saved = Signal()  # the queue is empty and the last write worked
    failed = Signal(str)  # the queue is empty and the last write raised (message for the person)

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
        # Cyclic garbage (Qt objects in it) is collected on the window thread only, never by
        # the writer thread that happens to allocate (ui/gc_guard.py).
        gc_guard.install()
        # Writer-thread state (a plain object, never this QObject: see `_Relay`).
        global _relay
        if _relay is None:
            _relay = _Relay()
        self._token = next(_TOKENS)
        _SAVERS[self._token] = self
        self._core = _Core(store, self._token, _relay)

    # -- state (window thread) ------------------------------------------------------------
    @property
    def idle(self) -> bool:
        """Nothing is queued or being written."""
        return self._settled >= self._submitted

    @property
    def _running(self) -> bool:
        """A writer thread is alive (it holds the lock-protected state in `_core`)."""
        return self._core.running

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
        gc_guard.install()  # cheap when installed (by __init__); see ui/gc_guard.py
        was_idle = self.idle
        self._submitted += 1
        failure: tuple[int, str] | None = None
        core = self._core
        with core.lock:
            core.pending = (self._submitted, job_id, data)
            if not core.running:
                core.running = True
                # A daemon: every close path waits for the saver to be idle first (the write is
                # atomic, tmp + replace), so a write hung on a dead share cannot keep the process
                # alive after the window is gone.
                try:
                    threading.Thread(target=core.run, name="evrakci-saver", daemon=True).start()
                except Exception as exc:  # e.g. "can't start new thread": report it, not hang
                    core.running = False
                    core.pending = None
                    failure = (self._submitted, str(exc) or type(exc).__name__)
        if failure is not None:
            # queued: the window thread settles it as a failed write
            core.relay.result.emit(self._token, *failure)
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
        core = self._core
        with core.lock:
            return core.lock.wait_for(lambda: core.pending is None and not core.running, timeout)

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
