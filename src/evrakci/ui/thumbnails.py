"""Page thumbnails: rendered in worker threads, only on request, kept in a small LRU cache."""

from __future__ import annotations

import threading
from collections import OrderedDict
from collections.abc import Callable
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
from PySide6.QtGui import QImage

from evrakci.pipeline.job import Job, parse_page_id
from evrakci.pipeline.render import render_page

Renderer = Callable[[str, int], Image.Image]


def to_qimage(image: Image.Image) -> QImage:
    rgb = image.convert("RGB")
    data = rgb.tobytes()
    qimage = QImage(data, rgb.width, rgb.height, rgb.width * 3, QImage.Format.Format_RGB888)
    return qimage.copy()  # own the pixels; `data` goes away


def job_renderer(job: Job, batch_files: dict[str, Path], dpi: int = 30) -> Renderer:
    """Render a page of `job` from its batch file, rotated as the user rotated it."""

    def render(pid: str, height: int) -> Image.Image:
        batch_id, index = parse_page_id(pid)
        image = render_page(batch_files[batch_id], index, job.rotations.get(pid, 0), dpi=dpi)
        width = max(1, round(image.width * height / image.height))
        return image.resize((width, height))

    return render


class _Relay(QObject):
    done = Signal(str, QImage)


class _Job(QRunnable):
    def __init__(self, service: ThumbnailService, pid: str) -> None:
        super().__init__()
        self.service = service
        self.pid = pid

    def run(self) -> None:
        self.service._render(self.pid)


class ThumbnailService(QObject):
    ready = Signal(str, QImage)

    def __init__(
        self,
        renderer: Renderer,
        height: int = 100,
        capacity: int = 400,
        workers: int = 2,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.renderer = renderer
        self.height = height
        self.capacity = capacity
        self.cache: OrderedDict[str, QImage] = OrderedDict()
        self._wanted: set[str] = set()
        self._busy = 0
        self._lock = threading.Lock()
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(workers)
        self._relay = _Relay()
        self._relay.done.connect(self._finished)

    def request(self, pid: str) -> None:
        if pid in self.cache:
            self.cache.move_to_end(pid)
            self.ready.emit(pid, self.cache[pid])
            return
        with self._lock:
            if pid in self._wanted:
                return
            self._wanted.add(pid)
            self._busy += 1
        self._pool.start(_Job(self, pid))

    def keep_only(self, pids: set[str]) -> None:
        """Forget requests for pages that scrolled out of view."""
        with self._lock:
            self._wanted &= set(pids)

    def invalidate(self, pid: str | None = None) -> None:
        """Drop cached images (one page after a rotation, or all)."""
        if pid is None:
            self.cache.clear()
        else:
            self.cache.pop(pid, None)

    def idle(self) -> bool:
        with self._lock:
            return self._busy == 0

    def _render(self, pid: str) -> None:
        image = None
        try:
            with self._lock:
                wanted = pid in self._wanted
            if wanted:
                try:
                    image = to_qimage(self.renderer(pid, self.height))
                except Exception:  # a broken page shows no thumbnail, never stops the window
                    image = None
        finally:
            with self._lock:
                self._wanted.discard(pid)
                self._busy -= 1
        if image is not None:
            self._relay.done.emit(pid, image)

    def _finished(self, pid: str, image: QImage) -> None:
        self.cache[pid] = image
        self.cache.move_to_end(pid)
        while len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
        self.ready.emit(pid, image)
