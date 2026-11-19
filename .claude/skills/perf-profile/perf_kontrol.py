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
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from fakes import job_from_kinds, make_pdf, text_page  # noqa: E402
from PIL import Image  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from evrakci.app import configure_application  # noqa: E402
from evrakci.pipeline.store import JobStore  # noqa: E402
from evrakci.ui.controller import JobController  # noqa: E402
from evrakci.ui.kontrol import KontrolScreen  # noqa: E402
from evrakci.ui.thumbnails import ThumbnailService, job_renderer  # noqa: E402

# Targets from SKILL.md. Frame = one full viewport repaint after a scroll step.
THRESHOLDS = {
    "frame_p95_ms": 16.7,       # one 60 Hz frame
    "frame_max_ms": 50.0,
    "settled_loaded_pct": 100.0,  # visible rows with a current thumbnail once idle, no mouse
    "settle_ms": 1500.0,          # after a jump, until every visible row is loaded
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
            return Image.new("RGB", (round(height * 0.7), height), "white")

    return JobController(store, job), renderer


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pages", type=int, default=1000)
    ap.add_argument("--delay-ms", type=float, default=15.0, help="fake render cost per page")
    ap.add_argument("--real", action="store_true", help="real PDF + pdfium rendering")
    ap.add_argument("--steps", type=int, default=150, help="scroll steps per sweep")
    ap.add_argument("--step-px", type=int, default=120, help="one wheel notch")
    ap.add_argument("--width", type=int, default=1366)
    ap.add_argument("--height", type=int, default=640)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--baseline", type=Path, help="JSON from an earlier run to compare with")
    args = ap.parse_args()

    app = QApplication.instance() or QApplication(sys.argv)
    configure_application(app)
    with tempfile.TemporaryDirectory() as tmpdir:
        ctl, renderer = build(args, Path(tmpdir))
        service = ThumbnailService(renderer, height=110)
        t0 = time.perf_counter()
        screen = KontrolScreen(ctl, service, templates=dict)
        screen.resize(args.width, args.height)
        screen.show()
        screen.timeline.viewport().repaint()
        first_paint = (time.perf_counter() - t0) * 1000
        view = screen.timeline
        bar = view.verticalScrollBar()

        settle_first = wait_loaded(app, screen)
        frames: list[float] = []
        for direction in (1, -1):  # down to the end of the sweep, then back up
            for _ in range(args.steps):
                value = bar.value() + direction * args.step_px
                bar.setValue(max(0, min(bar.maximum(), value)))
                started = time.perf_counter()
                view.viewport().repaint()
                frames.append((time.perf_counter() - started) * 1000)
                app.processEvents()
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
            "first_paint_ms": round(first_paint, 1),
            "first_settle_ms": round(settle_first, 1),
            "frames": len(frames),
            "frame_p50_ms": round(statistics.median(frames), 2),
            "frame_p95_ms": round(percentile(frames, 95), 2),
            "frame_max_ms": round(max(frames), 2),
            "frames_over_16ms": sum(f > 16.7 for f in frames),
            "frames_over_33ms": sum(f > 33.3 for f in frames),
            "settle_ms": round(max(jumps), 1),
            "settled_loaded_pct": round(100 * ok / total, 1) if total else 0.0,
            "prefetched_rows_below_view": ahead,
            "cache_size": len(service.cache),
        }
        service.stop()
        screen.close()

    for key, value in result.items():
        print(f"{key:28} {value}")
    base = json.loads(args.baseline.read_text()) if args.baseline else {}
    failed = []
    for key, limit in THRESHOLDS.items():
        value = result[key]
        bad = value < limit if key == "settled_loaded_pct" else value > limit
        mark = "FAIL" if bad else "ok"
        extra = f"  (before {base[key]})" if key in base else ""
        print(f"{mark:5}{key:26} {value} vs {limit}{extra}")
        if bad:
            failed.append(key)
    if args.out:
        args.out.write_text(json.dumps(result, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
