"""Profile the Kontrol timeline on a synthetic job: scroll frame times and thumbnail loading.

    QT_QPA_PLATFORM=offscreen python .claude/skills/perf-profile/perf_kontrol.py \
        --pages 1000 --out before.json
    QT_QPA_PLATFORM=offscreen python .claude/skills/perf-profile/perf_kontrol.py \
        --pages 1000 --out after.json --baseline before.json

Default (fake) mode renders blank pages after `--delay-ms` of simulated work in the service's
worker threads, so it isolates the timeline and ThumbnailService logic. `--real` builds a real
PDF of --pages pages (tests/fakes.py pages) and renders it with pdfium through
`thumbnails.job_renderer`, like the app does; creating the job analyses every page, so allow
about a minute for 1000 pages. No mouse event is ever sent: a thumbnail that only appears on
hover shows up here as a visible row that is never loaded.
Everything lives in a temp folder. Exits 1 when a threshold is missed (THRESHOLDS below).

Extra options:
  --runs N         run N times as separate subprocesses; --out then holds
                   {"runs", "median", "min", "max", "spread_pct"} and thresholds use the median.
  --frame-log P    after the sweep, a second pass on a cold cache scrolls the way the app does
                   (scrollbar.setValue + processEvents only: no repaint(), no mouse event, the
                   Qt scroll blit stays in play) and after every step reads the window's backing
                   store (QScreen.grabWindow, checked by a blit self-check first). Per visible
                   row: ok (this page's colour), blank (placeholder), wrong (another page's
                   colour), stale (differs from a fresh full paint, compared at a few pixels).
                   JSON lines go to P (with --runs, run k > 1 writes P.k); the summary metrics
                   are frames_with_wrong, frames_with_stale, blank_rows_after_settle (summed over
                   the 4 jumps) and max_blank_rows_in_frame. Needs the fake renderer, whose
                   pages are solid colours unique per page id.
  --text-scale {100,115,130,150}  text size in percent and --theme {light,dark,hc}: applied
                   through theme.manager() (set_text_scale, set_mode) before the screen is built,
                   as tools/screenshots.py does. Default: 100 and light.
  --disk-delay-ms N  slow disk: N ms of extra sleep around EVERY renderer call, inside the worker
                   thread (added to --delay-ms in fake mode, to the pdfium render with --real).
                   The real renderer's own file reads (pipeline.render) cannot be hooked without
                   touching src/, so this models the read as one delay per page render.
  --memory-ceiling-mb N  low memory: after Qt start-up (a limit set before Qt starts breaks it)
                   the subprocess sets resource.setrlimit(RLIMIT_AS, N MB) and runs the measured
                   part. RLIMIT_AS limits virtual address space, far above RSS (see vm_mb_at_cap).
                   The result has memory_run_completed (1/0); on a failure memory_error holds the
                   exception. Linux only.
  Metrics: renders_at_first_paint counts distinct pids passed to ThumbnailService.request by the
  time the first paint returns (requested, not finished); renders_at_first_settle counts renderer
  calls until the first screen is fully loaded; rss_mb_after_sweep is the resident memory after
  the scroll sweep.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from fakes import job_from_kinds, make_pdf, text_page  # noqa: E402
from PIL import Image  # noqa: E402
from PySide6.QtCore import QEvent, QObject, QPoint  # noqa: E402
from PySide6.QtGui import QColor, QPainter  # noqa: E402
from PySide6.QtWidgets import QAbstractScrollArea, QApplication  # noqa: E402

from evrakci.app import configure_application  # noqa: E402
from evrakci.pipeline.job import parse_page_id  # noqa: E402
from evrakci.pipeline.store import JobStore  # noqa: E402
from evrakci.ui.controller import JobController  # noqa: E402
from evrakci.ui.kontrol import KontrolScreen  # noqa: E402
from evrakci.ui.thumbnails import ThumbnailService, job_renderer  # noqa: E402

# Targets from SKILL.md. Frame = one full viewport repaint after a scroll step.
THRESHOLDS = {
    "paint_cost_p95_ms": 16.7,  # one forced full viewport paint: fits a 60 Hz frame
    "paint_cost_max_ms": 50.0,
    # visible rows with a current thumbnail after a jump, setValue + events only (no repaint),
    # waiting up to settle_ms
    "settled_loaded_pct_real": 100.0,
    "settle_ms": 1500.0,          # after a jump WITH a forced repaint, until all rows loaded
    "first_paint_ms": 1000.0,     # same bound as test_kontrol.py
}


def pump(app: QApplication, ms: float) -> None:
    end = time.perf_counter() + ms / 1000
    while time.perf_counter() < end:
        app.processEvents()
        time.sleep(0.001)


def visible_loaded(screen: KontrolScreen) -> tuple[int, int]:
    view, service = screen.timeline, screen.thumbnails
    model = view.model()
    rows = list(view.visible_rows())
    ok = sum(1 for r in rows if service.is_current(model.page_id(r)))
    return ok, len(rows)


def wait_loaded(app: QApplication, screen: KontrolScreen, limit_ms: float = 8000) -> float:
    """Milliseconds until every visible row has a current thumbnail (or limit_ms)."""
    start = time.perf_counter()
    while (time.perf_counter() - start) * 1000 < limit_ms:
        app.processEvents()
        ok, total = visible_loaded(screen)
        if ok == total and total:
            break
        time.sleep(0.002)
    return (time.perf_counter() - start) * 1000


def percentile(values: list[float], pct: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(pct / 100 * (len(ordered) - 1)))] if ordered else 0.0


def page_colour(pid: str) -> tuple[int, int, int]:
    """A solid colour unique per page index (up to 1000 pages): one decimal digit per channel."""
    n = parse_page_id(pid)[1] % 1000
    return tuple(20 + 24 * d for d in (n // 100, n // 10 % 10, n % 10))


class CountingRenderer:
    """Wraps a renderer and counts calls (thread-safe: called from the worker threads)."""

    def __init__(self, inner) -> None:
        self.inner = inner
        self.calls = 0
        self._lock = threading.Lock()

    def __call__(self, pid: str, height: int) -> Image.Image:
        with self._lock:
            self.calls += 1
        return self.inner(pid, height)


class PaintWatcher(QObject):
    """Counts the paint events a widget receives."""

    def __init__(self, widget) -> None:
        super().__init__(widget)
        self.paints = 0
        widget.installEventFilter(self)

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        if event.type() == QEvent.Type.Paint:
            self.paints += 1
        return False


def count_requests(service: ThumbnailService) -> set[str]:
    """Record every pid asked of `service.request` (GUI thread only)."""
    asked: set[str] = set()
    original = service.request

    def request(pid: str) -> None:
        asked.add(pid)
        original(pid)

    service.request = request  # the delegate looks the method up on the instance
    return asked


def build(args, tmp: Path):
    store = JobStore(tmp / "jobs")
    if args.real:
        pdf = make_pdf(tmp / "synthetic.pdf", [text_page(str(i)) for i in range(args.pages)])
        job = store.create_job("Sentetik", [pdf])
        renderer = job_renderer(job, lambda: store.batch_files(job))
    else:
        job = job_from_kinds({"b1": "p" * args.pages})
        store.save(job)

        def renderer(pid: str, height: int) -> Image.Image:
            time.sleep(args.delay_ms / 1000)
            return Image.new("RGB", (round(height * 0.7), height), page_colour(pid))

    if args.disk_delay_ms:
        inner = renderer

        def renderer(pid: str, height: int) -> Image.Image:  # noqa: F811
            time.sleep(args.disk_delay_ms / 1000)
            return inner(pid, height)

    return JobController(store, job), CountingRenderer(renderer)


def rss_mb() -> float:
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) / 1024
    except OSError:
        pass
    import resource

    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss  # peak, KB (bytes on macOS)
    return peak / (1024 * 1024 if sys.platform == "darwin" else 1024)


# -- frame log: what is really on screen ---------------------------------------------------------
TOLERANCE = 3  # per channel, between two renderings of the same pixel


def close(a, b, tol: int = TOLERANCE) -> bool:
    return all(abs(x - y) <= tol for x, y in zip(a, b, strict=True))


def rgb(image, x: int, y: int) -> tuple[int, int, int]:
    c = image.pixelColor(x, y)
    return c.red(), c.green(), c.blue()


def window_image(widget):
    """The top-level window's backing store (what the platform shows), not a re-render."""
    return widget.screen().grabWindow(widget.winId()).toImage()


def check_backing_store(app: QApplication) -> bool:
    """Paint stripes, scroll by blit while a fresh paint would now look different, and confirm
    that the window grab keeps the blitted (old) pixels where `widget.grab()` shows the new."""

    class Probe(QAbstractScrollArea):
        generation = 0

        def paintEvent(self, event) -> None:  # noqa: N802
            painter = QPainter(self.viewport())
            offset = self.verticalScrollBar().value()
            rect = event.rect()
            for y in range(rect.top(), rect.bottom() + 1):
                painter.fillRect(rect.left(), y, rect.width(), 1,
                                 QColor((y + offset) * 2 % 256, 40 + 100 * self.generation, 90))

        def scrollContentsBy(self, dx: int, dy: int) -> None:  # noqa: N802
            self.viewport().scroll(dx, dy)

    probe = Probe()
    probe.verticalScrollBar().setRange(0, 100)
    probe.resize(200, 100)
    probe.show()
    pump(app, 80)
    probe.verticalScrollBar().setValue(20)
    probe.generation = 1  # a fresh paint now differs from the pixels that were blitted
    pump(app, 80)
    origin = probe.viewport().mapTo(probe, QPoint(0, 0))
    backing = window_image(probe)
    fresh = probe.viewport().grab().toImage()
    ox, oy = origin.x() + 5, origin.y()
    old_kept = rgb(backing, ox, oy + 10) == ((10 + 20) * 2, 40, 90)  # blitted, generation 0
    exposed_new = rgb(backing, ox, oy + 95)[1] == 140               # repainted strip
    grab_new = rgb(fresh, 5, 10)[1] == 140                          # a re-render shows new
    probe.close()
    return old_kept and exposed_new and grab_new


def fit_line(xs: list[float], ys: list[float]) -> tuple[float, float]:
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    var = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True)) / var if var else 1.0
    return slope, my - slope * mx


class FrameLog:
    """Classifies every visible row of the backing store after a scroll step."""

    def __init__(self, screen: KontrolScreen, pages: int, path: Path) -> None:
        self.screen, self.view, self.pages = screen, screen.timeline, pages
        self.lines = path.open("w")
        self.fit: list[tuple[float, float]] = [(1.0, 0.0)] * 3
        self.records: list[dict] = []
        self.placeholder: tuple[int, int, int] | None = None

    @contextmanager
    def quiet(self, empty_cache: bool = False):
        """Render the viewport without asking the service for anything (the delegate requests a
        thumbnail from its paint, so a grab would load rows by itself). `empty_cache` makes every
        tile a placeholder. Nothing is processed inside, so no render result is lost."""
        service = self.screen.thumbnails
        cache = service.cache
        service.request = lambda pid: None  # the delegate looks the method up on the instance
        if empty_cache:
            service.cache = OrderedDict()
        try:
            yield
        finally:
            del service.request
            service.cache = cache

    def samples(self, row: int) -> list[tuple[int, int]]:
        rect = self.view.page_rect(row)
        vp = self.view.viewport()
        w, h = rect.width() // 4, rect.height() // 4
        points = [(rect.center().x() + dx, rect.center().y() + dy)
                  for dx, dy in ((0, 0), (-w, -h), (w, -h), (-w, h), (w, h))]
        return [(x, y) for x, y in points if 0 <= x < vp.width() and 0 <= y < vp.height()]

    def calibrate(self) -> None:
        """Fit how the delegate (paper, tint_scan) changes a page colour: seen = a * pid + b.
        Also sample the placeholder paper colour once, from a viewport with an empty cache."""
        with self.quiet():
            fresh = self.view.viewport().grab().toImage()
        with self.quiet(empty_cache=True):
            empty = self.view.viewport().grab().toImage()
        model = self.view.model()
        pairs = [(page_colour(model.page_id(r)), rgb(fresh, *self.samples(r)[0]))
                 for r in self.view.visible_rows() if self.samples(r)]
        self.fit = [fit_line([p[c] for p, _ in pairs], [s[c] for _, s in pairs])
                    for c in range(3)]
        for row in self.view.visible_rows():
            points = self.samples(row)
            if len(points) > 1:  # a corner point: no "Yükleniyor" text there
                self.placeholder = rgb(empty, *points[1])
                break

    def is_placeholder(self, seen: list[tuple[int, int, int]]) -> bool:
        """True when the tile shows the placeholder paper (checked at the points off the text)."""
        if self.placeholder is None:
            return False
        return all(close(s, self.placeholder) for s in (seen[1:] or seen))

    def expected(self, colour) -> tuple[int, ...]:
        return tuple(round(max(0, min(255, a * v + b)))
                     for (a, b), v in zip(self.fit, colour, strict=True))

    def page_seen(self, seen) -> int | None:
        """Index of the page whose colour `seen` is, or None when it is no page colour."""
        digits = []
        for (a, b), v in zip(self.fit, seen, strict=True):
            level = ((v - b) / a - 20) / 24 if abs(a) > 0.2 else -1
            if not -0.25 < level < 9.25 or abs(level - round(level)) * 24 > 6:
                return None
            digits.append(round(level))
        index = digits[0] * 100 + digits[1] * 10 + digits[2]
        return index if index < self.pages else None

    def frame(self, kind: str, step: int) -> dict:
        view, model = self.view, self.view.model()
        vp = view.viewport()
        origin = vp.mapTo(self.screen, QPoint(0, 0))
        backing = window_image(self.screen)  # first: it must show what the last paint left
        with self.quiet():  # the reference must not load anything itself
            fresh = vp.grab().toImage()
        counts = {"ok": 0, "blank": 0, "wrong": 0, "stale": 0}
        examples: dict[str, list] = {key: [] for key in counts}
        rows = view.visible_rows()
        for row in rows:
            points = self.samples(row)
            if not points:
                continue
            pid = model.page_id(row)
            seen = [rgb(backing, origin.x() + x, origin.y() + y) for x, y in points]
            now = [rgb(fresh, x, y) for x, y in points]
            own = parse_page_id(pid)[1] % 1000
            shown = None if self.is_placeholder(seen) else self.page_seen(seen[0])
            kinds = []
            if shown == own:
                kinds.append("ok")
            elif shown is None:
                kinds.append("blank")
            else:
                kinds.append("wrong")
            if any(not close(a, b) for a, b in zip(seen, now, strict=True)):
                kinds.append("stale")
            for name in kinds:
                counts[name] += 1
                if len(examples[name]) < 5:
                    examples[name].append({"row": row, "pid": pid,
                                           "expected": self.expected(page_colour(pid)),
                                           "seen": seen[0], "fresh": now[0]})
        record = {"step": step, "kind": kind, "scroll": view.verticalScrollBar().value(),
                  "rows": [rows.start, rows.stop - 1] if rows else [], "counts": counts,
                  "examples": {k: v for k, v in examples.items() if v}}
        self.lines.write(json.dumps(record) + "\n")
        self.records.append(record)
        return record


def run_frame_log(args, app: QApplication, ctl, renderer) -> dict:
    """Scroll through the real path and log every frame; see the module docstring."""
    verified = check_backing_store(app)
    if not verified:
        raise SystemExit("backing store check failed: the window grab does not show blitted "
                         "pixels on this platform, the frame log would be meaningless")
    service = ThumbnailService(renderer, height=110)  # cold cache
    screen = KontrolScreen(ctl, service, templates=dict)
    screen.resize(args.width, args.height)
    screen.show()
    view = screen.timeline
    bar = view.verticalScrollBar()
    pump(app, 10)
    wait_loaded(app, screen)
    pump(app, 50)
    log = FrameLog(screen, args.pages, args.frame_log)
    log.calibrate()
    step = 0
    log.frame("first", step)
    for kind, direction in (("down", 1), ("up", -1)):
        for _ in range(args.steps):
            step += 1
            bar.setValue(max(0, min(bar.maximum(), bar.value() + direction * args.step_px)))
            app.processEvents()  # the real path: no repaint(), no mouse event
            log.frame(kind, step)
            pump(app, args.frame_interval_ms)
    blank_after_settle = 0
    for fraction in (0.5, 0.9, 0.1, 0.7):
        step += 1
        bar.setValue(round(bar.maximum() * fraction))
        app.processEvents()
        log.frame("jump", step)
        wait_loaded(app, screen, THRESHOLDS["settle_ms"])
        app.processEvents()
        app.processEvents()
        step += 1
        blank_after_settle += log.frame("settled", step)["counts"]["blank"]
    log.lines.close()
    frames = log.records
    service.stop()
    screen.close()
    return {
        "frame_log_frames": len(frames),
        "frames_with_wrong": sum(f["counts"]["wrong"] > 0 for f in frames),
        "frames_with_stale": sum(f["counts"]["stale"] > 0 for f in frames),
        "blank_rows_after_settle": blank_after_settle,
        "max_blank_rows_in_frame": max(f["counts"]["blank"] for f in frames),
        "backing_store_blit_verified": int(verified),
    }


def real_jumps(args, app: QApplication, ctl, renderer) -> float:
    """% of visible rows with a current thumbnail after jumps made the way the app scrolls:
    setValue + event processing only (no repaint(), no grab, no mouse), waiting up to the settle
    limit. A cold cache and a fresh screen, so nothing was loaded for these rows before."""
    service = ThumbnailService(renderer, height=110)
    screen = KontrolScreen(ctl, service, templates=dict)
    screen.resize(args.width, args.height)
    screen.show()
    bar = screen.timeline.verticalScrollBar()
    pump(app, 10)
    wait_loaded(app, screen)
    pump(app, 50)
    loaded = total = 0
    for fraction in (0.5, 0.9, 0.1, 0.7):
        bar.setValue(round(bar.maximum() * fraction))
        wait_loaded(app, screen, THRESHOLDS["settle_ms"])
        ok, count = visible_loaded(screen)
        loaded, total = loaded + ok, total + count
    service.stop()
    screen.close()
    return round(100 * loaded / total, 1) if total else 0.0


def vm_mb() -> float:
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmSize:"):
                return int(line.split()[1]) / 1024
    except OSError:
        pass
    return 0.0


def apply_theme(args) -> None:
    from evrakci.ui import theme

    manager = theme.manager()
    manager.set_text_scale(args.text_scale)
    manager.set_mode(args.theme)


def measure(args) -> dict:
    app = QApplication.instance() or QApplication(sys.argv)
    configure_application(app)
    apply_theme(args)
    if args.memory_ceiling_mb:
        import resource

        pump(app, 50)
        cap = int(args.memory_ceiling_mb * 1024 * 1024)
        resource.setrlimit(resource.RLIMIT_AS, (cap, resource.RLIM_INFINITY))
        try:
            result = measure_part(args, app)
        except (MemoryError, OSError, RuntimeError) as exc:
            return {"pages": args.pages, "memory_run_completed": 0,
                    "memory_error": f"{type(exc).__name__}: {exc}"[:200],
                    "vm_mb_at_cap": round(vm_mb(), 1), "memory_ceiling_mb": args.memory_ceiling_mb}
        result.update(memory_run_completed=1, vm_mb_at_cap=round(vm_mb(), 1),
                      memory_ceiling_mb=args.memory_ceiling_mb)
        return result
    return measure_part(args, app)


def measure_part(args, app) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        ctl, renderer = build(args, Path(tmpdir))
        service = ThumbnailService(renderer, height=110)
        asked = count_requests(service)
        t0 = time.perf_counter()
        screen = KontrolScreen(ctl, service, templates=dict)
        screen.resize(args.width, args.height)
        watcher = PaintWatcher(screen.timeline.viewport())
        screen.show()
        # viewport().repaint() does nothing before the window is exposed (0 paints, 0 requests),
        # so the first paint is the first paint event the event loop delivers after show().
        while not watcher.paints and time.perf_counter() - t0 < 5:
            app.processEvents()
        first_paint = (time.perf_counter() - t0) * 1000
        renders_at_first_paint = len(asked)  # distinct pids requested, not finished renders
        view = screen.timeline
        bar = view.verticalScrollBar()

        settle_first = wait_loaded(app, screen)
        renders_at_first_settle = renderer.calls
        frames: list[float] = []
        for direction in (1, -1):  # down to the end of the sweep, then back up
            for _ in range(args.steps):
                value = bar.value() + direction * args.step_px
                bar.setValue(max(0, min(bar.maximum(), value)))
                started = time.perf_counter()
                view.viewport().repaint()
                frames.append((time.perf_counter() - started) * 1000)
                app.processEvents()
        rss_after_sweep = rss_mb()
        # Loading after a jump with no mouse movement: the known "loads only on hover" bug.
        jumps = []
        for fraction in (0.5, 0.9, 0.1, 0.7):
            bar.setValue(round(bar.maximum() * fraction))
            view.viewport().repaint()
            jumps.append(wait_loaded(app, screen))
        pump(app, 300)
        ok, total = visible_loaded(screen)
        rows = view.visible_rows()
        margin = 20
        ahead = sum(1 for r in range(rows.stop, min(view.model().rowCount(), rows.stop + margin))
                    if service.is_current(view.model().page_id(r)))
        result = {
            "pages": args.pages, "mode": "real" if args.real else f"fake {args.delay_ms} ms",
            "text_scale": args.text_scale, "theme": args.theme,
            "disk_delay_ms": args.disk_delay_ms,
            "first_paint_ms": round(first_paint, 1),
            "renders_at_first_paint": renders_at_first_paint,
            "first_settle_ms": round(settle_first, 1),
            "renders_at_first_settle": renders_at_first_settle,
            "frames": len(frames),
            "paint_cost_p50_ms": round(statistics.median(frames), 2),
            "paint_cost_p95_ms": round(percentile(frames, 95), 2),
            "paint_cost_max_ms": round(max(frames), 2),
            "frames_over_16ms": sum(f > 16.7 for f in frames),
            "frames_over_33ms": sum(f > 33.3 for f in frames),
            "settle_ms": round(max(jumps), 1),
            "settled_loaded_pct_forced": round(100 * ok / total, 1) if total else 0.0,
            "prefetched_rows_below_view": ahead,
            "cache_size": len(service.cache),
            "rss_mb_after_sweep": round(rss_after_sweep, 1),
        }
        service.stop()
        screen.close()
        result["settled_loaded_pct_real"] = real_jumps(args, app, ctl, renderer)
        if args.frame_log:
            result.update(run_frame_log(args, app, ctl, renderer))
    return result


def is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def aggregate(runs: list[dict]) -> dict:
    keys = [k for k, v in runs[0].items() if is_number(v)]
    median = {k: round(statistics.median(r[k] for r in runs), 2) for k in keys}
    low = {k: min(r[k] for r in runs) for k in keys}
    high = {k: max(r[k] for r in runs) for k in keys}
    spread = {k: round((high[k] - low[k]) / median[k] * 100, 1) if median[k] else 0
              for k in keys}
    for key, value in runs[0].items():
        if key not in median:
            median[key] = value  # labels such as mode
    return {"runs": runs, "median": median, "min": low, "max": high, "spread_pct": spread}


def run_subprocesses(args) -> dict:
    runs = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(1, args.runs + 1):
            out = Path(tmpdir) / f"run{i}.json"
            cmd = [sys.executable, str(Path(__file__).resolve()), "--pages", str(args.pages),
                   "--delay-ms", str(args.delay_ms), "--steps", str(args.steps),
                   "--step-px", str(args.step_px), "--width", str(args.width),
                   "--height", str(args.height), "--frame-interval-ms",
                   str(args.frame_interval_ms), "--out", str(out)]
            cmd += ["--text-scale", str(args.text_scale), "--theme", args.theme,
                    "--disk-delay-ms", str(args.disk_delay_ms)]
            if args.memory_ceiling_mb:
                cmd += ["--memory-ceiling-mb", str(args.memory_ceiling_mb)]
            if args.real:
                cmd.append("--real")
            if args.frame_log:
                log = args.frame_log if i == 1 else args.frame_log.with_name(
                    f"{args.frame_log.name}.{i}")
                cmd += ["--frame-log", str(log)]
            done = subprocess.run(cmd, capture_output=True, text=True)
            if not out.exists():  # exit 1 only means a missed threshold
                sys.stderr.write(done.stdout + done.stderr)
                raise SystemExit(f"run {i} failed (exit {done.returncode})")
            runs.append(json.loads(out.read_text()))
    return aggregate(runs)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pages", type=int, default=1000)
    ap.add_argument("--delay-ms", type=float, default=15.0, help="fake render cost per page")
    ap.add_argument("--real", action="store_true", help="real PDF + pdfium rendering")
    ap.add_argument("--steps", type=int, default=150, help="scroll steps per sweep")
    ap.add_argument("--step-px", type=int, default=120, help="one wheel notch")
    ap.add_argument("--width", type=int, default=1366)
    ap.add_argument("--height", type=int, default=640)
    ap.add_argument("--runs", type=int, default=1, help="separate subprocess runs; keep median")
    ap.add_argument("--frame-log", type=Path, help="JSON lines of the real scroll path (fake only)")
    ap.add_argument("--frame-interval-ms", type=float, default=16.0,
                    help="pause between frame-log steps (events keep running)")
    ap.add_argument("--text-scale", type=int, choices=(100, 115, 130, 150), default=100)
    ap.add_argument("--theme", choices=("light", "dark", "hc"), default="light")
    ap.add_argument("--disk-delay-ms", type=float, default=0.0,
                    help="extra sleep around every renderer call (worker thread)")
    ap.add_argument("--memory-ceiling-mb", type=int, default=0,
                    help="RLIMIT_AS (virtual MB) applied after Qt start-up; 0 = none")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--baseline", type=Path, help="JSON from an earlier run to compare with")
    args = ap.parse_args()
    if args.frame_log and args.real:
        ap.error("--frame-log needs the fake renderer (unique colour per page)")

    if args.runs > 1:
        data = run_subprocesses(args)
        result = data["median"]
        print(f"{'metric':28} {'median':>10} {'min':>10} {'max':>10} {'spread%':>8}")
        for key in data["min"]:
            print(f"{key:28} {result[key]:>10} {data['min'][key]:>10} {data['max'][key]:>10} "
                  f"{data['spread_pct'][key]:>8}")
    else:
        result = data = measure(args)
        for key, value in result.items():
            print(f"{key:28} {value}")
    base = json.loads(args.baseline.read_text()) if args.baseline else {}
    base = base.get("median", base)
    failed = []
    for key, limit in THRESHOLDS.items():
        if key not in result:  # a memory-capped run that did not complete has no metrics
            print(f"FAIL {key:26} missing")
            failed.append(key)
            continue
        value = result[key]
        bad = value < limit if key.startswith("settled_loaded_pct") else value > limit
        mark = "FAIL" if bad else "ok"
        extra = f"  (before {base[key]})" if key in base else ""
        print(f"{mark:5}{key:26} {value} vs {limit}{extra}")
        if bad:
            failed.append(key)
    if args.out:
        args.out.write_text(json.dumps(data, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
