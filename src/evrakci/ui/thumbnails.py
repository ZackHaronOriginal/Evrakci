"""Page thumbnails: rendered in worker threads, only on request, kept in a small LRU cache.

The service renders at one height (`set_height`, the Kontrol zoom). After a height change the
old images stay in the cache and are still drawn, scaled, until the new ones arrive, so zooming
never flashes empty pages.
"""

from __future__ import annotations

import threading
from collections import OrderedDict
from collections.abc import Callable, Mapping
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Signal
from PySide6.QtGui import QImage

from evrakci.pipeline.job import Job, parse_page_id
from evrakci.pipeline.render import render_page
from evrakci.ui import gc_guard

Renderer = Callable[[str, int], Image.Image]

# The cache holds at most this many bytes of QImage pixels, whatever the zoom: a count cap lets
# memory grow with the thumbnail size (a 200 % tile is four times a 100 % tile). Pages farthest
# from the viewport go first. A 100 % tile is about 92 KB at device pixel ratio 1; the bytes of a
# tile scale with zoom squared times the device pixel ratio squared (about 1.47 MB at zoom 200 and
# ratio 2). At normal zoom and ratio 1 the count cap (`capacity`, 400 or more) binds first; the
# byte cap binds at high zoom or a high device pixel ratio.
CACHE_MAX_BYTES = 150 * 1024 * 1024


def to_qimage(image: Image.Image) -> QImage:
    rgb = image.convert("RGB")
    data = rgb.tobytes()
    qimage = QImage(data, rgb.width, rgb.height, rgb.width * 3, QImage.Format.Format_RGB888)
    return qimage.copy()  # own the pixels; `data` goes away


A4_INCHES = 11.7  # the long side of an A4 page


def render_dpi(height: int, minimum: int = 30) -> int:
    """Enough resolution for an A4 page `height` pixels tall (at least `minimum`)."""
    return max(minimum, -(-height * 10 // round(A4_INCHES * 10)) + 1)


def job_renderer(
    job: Job, batch_files: Callable[[], Mapping[str, Path]], dpi: int = 30
) -> Renderer:
    """Render a page of `job` from its batch file, rotated as the user rotated it.

    `batch_files` is asked on every render, so batches added later are found too. `dpi` is the
    lowest resolution; taller thumbnails (zoomed in) are rendered with as much as they need.
    """

    def render(pid: str, height: int) -> Image.Image:
        batch_id, index = parse_page_id(pid)
        path = batch_files()[batch_id]
        image = render_page(path, index, job.rotations.get(pid, 0),
                            dpi=render_dpi(height, dpi))
        width = max(1, round(image.width * height / image.height))
        return image.resize((width, height))

    return render


# Retired services stay referenced here until no runnable is left: deleting a service (and its
# pool and relay) under a worker thread that is inside the renderer crashes natively.
_RETIRING: list[ThumbnailService] = []
_RETIRE_POLL_MS = 20


def _sweep_retired() -> None:
    for service in list(_RETIRING):
        if service._settled():
            _RETIRING.remove(service)
            service.deleteLater()
    if _RETIRING:
        QTimer.singleShot(_RETIRE_POLL_MS, _sweep_retired)


class _Relay(QObject):
    done = Signal(str, QImage, int, int)


class _Job(QRunnable):
    def __init__(self, service: ThumbnailService, pid: str) -> None:
        super().__init__()
        self.service = service
        self.pid = pid

    def run(self) -> None:
        with gc_guard.working():
            self.service._render(self.pid)


class ThumbnailService(QObject):
    ready = Signal(str, QImage)

    def __init__(
        self,
        renderer: Renderer,
        height: int = 100,
        capacity: int = 400,
        workers: int = 2,
        max_bytes: int = CACHE_MAX_BYTES,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.renderer = renderer
        self.height = height
        self.capacity = capacity
        self.min_capacity = capacity  # the view may raise `capacity` above this, never below
        self.max_bytes = max_bytes
        self.cache_bytes = 0
        # How far a page is from the viewport (smaller is nearer); set by the view. Without it
        # the least recently used page is evicted first.
        self.distance: Callable[[str], float] | None = None
        self.cache: OrderedDict[str, QImage] = OrderedDict()
        self._heights: dict[str, int] = {}  # the height each cached image was rendered for
        self._wanted: set[str] = set()
        self._version: dict[str, int] = {}  # bumped by invalidate; older renders are dropped
        self._busy = 0
        self._retired = False
        self._lock = threading.Lock()
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(workers)
        self._relay = _Relay()
        self._relay.done.connect(self._finished)

    def set_height(self, height: int) -> None:
        """Render at `height` from now on; cached images of the old height stay usable (drawn
        scaled) until each page is asked for again and re-rendered."""
        height = max(1, int(height))
        if height == self.height:
            return
        with self._lock:
            self.height = height
            for key in self._wanted:
                self._version[key] = self._version.get(key, 0) + 1
            self._wanted.clear()

    def is_current(self, pid: str) -> bool:
        """True when the cached image of `pid` has the service's height."""
        return pid in self.cache and self._heights.get(pid) == self.height

    def request(self, pid: str) -> None:
        if self.is_current(pid):
            self.cache.move_to_end(pid)
            self.ready.emit(pid, self.cache[pid])
            return
        with self._lock:
            if pid in self._wanted:
                return
            self._wanted.add(pid)
            self._busy += 1
        gc_guard.install()  # cyclic garbage is never collected on the worker
        self._pool.start(_Job(self, pid))

    def keep_only(self, pids: set[str]) -> None:
        """Forget requests for pages that scrolled out of view."""
        with self._lock:
            self._wanted &= set(pids)

    def invalidate(self, pid: str | None = None) -> None:
        """Drop cached images (one page, or all); renders already running are thrown away."""
        with self._lock:
            pids = list(self.cache) + list(self._wanted) if pid is None else [pid]
            for key in pids:
                self._version[key] = self._version.get(key, 0) + 1
                self._wanted.discard(key)
        if pid is None:
            self.cache.clear()
            self._heights.clear()
            self.cache_bytes = 0
        else:
            self._drop(pid)

    def stop(self) -> None:
        """Forget all pending work, for example when another job is opened.

        Queued renders still run but skip their page, so the busy count stays right.
        """
        self.keep_only(set())

    def retire(self) -> None:
        """Stop and release the service once its workers are done (never while one is running).

        The service is detached from its parent and kept alive by the module until the pool is
        idle; only then is it deleted. Workers stop emitting as soon as it is retired.
        """
        self._retired = True
        self.stop()
        self.invalidate()
        self.distance = None
        self.setParent(None)
        if self not in _RETIRING:
            _RETIRING.append(self)
        _sweep_retired()

    def _settled(self) -> bool:
        return self.idle() and self._pool.activeThreadCount() == 0

    def idle(self) -> bool:
        with self._lock:
            return self._busy == 0

    def _render(self, pid: str) -> None:
        image = None
        try:
            with self._lock:
                wanted = pid in self._wanted
                version = self._version.get(pid, 0)
                height = self.height
            if wanted:
                try:
                    image = to_qimage(self.renderer(pid, height))
                except Exception:  # a broken page shows no thumbnail, never stops the window
                    image = None
        finally:
            with self._lock:
                if self._version.get(pid, 0) == version:
                    self._wanted.discard(pid)
                self._busy -= 1
        if image is not None and not self._retired:
            self._relay.done.emit(pid, image, version, height)

    def _finished(self, pid: str, image: QImage, version: int, height: int) -> None:
        if self._version.get(pid, 0) != version:
            return  # invalidated while rendering: an old picture
        self._drop(pid)
        self.cache[pid] = image
        self.cache_bytes += image.sizeInBytes()
        self._heights[pid] = height
        self._evict(keep=pid)
        self.ready.emit(pid, image)

    def _drop(self, pid: str) -> None:
        image = self.cache.pop(pid, None)
        if image is not None:
            self.cache_bytes -= image.sizeInBytes()
        self._heights.pop(pid, None)

    def _evict(self, keep: str) -> None:
        """Bring the cache under its count and byte caps, never dropping `keep` (the page that
        just arrived). Over a cap it drops down to 90 % of it in one go, farthest page from
        the viewport first (else least recent), so the distances are computed once per batch
        and not on every arrival (about 1 ms each at 400 pages)."""
        if len(self.cache) <= max(1, self.capacity) and self.cache_bytes <= self.max_bytes:
            return
        others = [pid for pid in self.cache if pid != keep]  # least recent first
        if self.distance is not None:
            others.sort(key=self.distance, reverse=True)
        count_goal = self.capacity - self.capacity // 10
        bytes_goal = self.max_bytes - self.max_bytes // 10
        for victim in others:
            if len(self.cache) <= count_goal and self.cache_bytes <= bytes_goal:
                break
            self._drop(victim)
