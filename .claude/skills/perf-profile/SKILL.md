---
name: perf-profile
description: Use when the Kontrol tab scrolls badly, shows stale or missing page thumbnails, or after any change to timeline.py, thumbnails.py or kontrol_paint.py. Profiles a synthetic 1000-page job (scroll frame times, thumbnail loading with no mouse input) and compares before and after against fixed thresholds.
---

# Kontrol performance profile

PRODUCT.md: jobs are 100-800 pages (Kontrol must stay smooth at 800+), on ordinary office PCs.
The 1000-page synthetic job is the stress case.

## Where the code is

- `src/evrakci/ui/timeline.py`: `TimelineView` (custom flow layout, `paintEvent` paints only
  rows from `_rows_between`), `TimelineDelegate._scan` (asks `ThumbnailService.request(pid)` while
  painting, draws `kp.paint_placeholder` when no image), `_forget_hidden` (on every
  `verticalScrollBar().valueChanged` calls `thumbnails.keep_only(visible pids)`),
  `_thumbnail_ready` (repaints one `visualRect`).
- `src/evrakci/ui/thumbnails.py`: `ThumbnailService` (2 worker threads, LRU `capacity=400`,
  `request`, `keep_only`, `set_height`, `idle()`), `job_renderer` (pdfium via `pipeline.render`).
- `src/evrakci/ui/kontrol_paint.py`: paper, placeholder, guide tabs.
- Existing guard: `tests/ui/test_kontrol.py::test_1000_pages_first_paint_is_fast_and_renders_only_visible_pages`
  (first paint < 1 s, at most 30 distinct renders). Adding a prefetch margin raises that bound:
  change it on purpose and say why.

## Known issue to target

Scrolling leaves stale images, and thumbnails only appear when the mouse hovers over them.
Expected fix: a scroll-driven loader that does not depend on paint or mouse events, i.e. compute
the visible rows plus a prefetch margin (about one viewport above and below) on scroll end /
a short timer, `request()` those (nearest to the viewport first), `keep_only(visible + margin)`,
draw placeholders until an image arrives, and repaint the whole viewport (not just a stale
rect) when images arrive after a scroll. Things to check in the code before changing it
(hypotheses, not verified): `_thumbnail_ready` updates only `visualRect(row)` using the offset
at signal time; `_forget_hidden` drops pending requests for rows that were visible a moment ago,
and a request made during `paintEvent` is the only trigger for loading; `request()` for a cached
page emits `ready` synchronously from inside a paint; `QAbstractScrollArea` blits already-painted
pixels on scroll, which keeps old content where a later partial update paints at the wrong
offset. Prove the cause with the script below (a row that stays unloaded with no mouse event)
before fixing.

## Measure (before any change)

Needs the dev environment (`pip install -e ".[dev]"`). Never run the whole suite.

```bash
# Fake renderer, 15 ms per page in the worker threads: isolates timeline + service logic
QT_QPA_PLATFORM=offscreen python .claude/skills/perf-profile/perf_kontrol.py --pages 1000 --out /tmp/before.json
# Heavier / slower renderer, to see whether loading keeps up
QT_QPA_PLATFORM=offscreen python .claude/skills/perf-profile/perf_kontrol.py --pages 1000 --delay-ms 60 --out /tmp/before-slow.json
# Real PDF through pdfium (building the job analyses 1000 pages, about a minute)
QT_QPA_PLATFORM=offscreen python .claude/skills/perf-profile/perf_kontrol.py --pages 1000 --real --out /tmp/before-real.json
```

What it does: builds a 1000-page job (`tests/fakes.py:job_from_kinds`, or a real PDF with `--real`),
shows `KontrolScreen` at 1366x640, sweeps the scrollbar down and up in 120 px steps (one
wheel notch), timing a full `viewport().repaint()` per step (`paint_cost_p50/p95/max_ms`: the cost
of a forced full paint, not a scroll frame time), then jumps to 50/90/10/70 % with a forced repaint
and waits until every visible row has a current thumbnail (`settle_ms`, `settled_loaded_pct_forced`).
`settled_loaded_pct_real` is the user-facing number: on a fresh screen, jumps with `setValue` and
event processing only (no repaint, no grab, no mouse), waiting up to 1500 ms, share of visible rows
with a current thumbnail. It prints first paint (first paint event after `show()`) with the pids
requested by then, first settle with the renders it took, frames over 16.7 and 33 ms, prefetched
rows below the view, cache size and RSS after the sweep, and exits 1 on a missed threshold.
Offscreen paint costs do not include the compositor, so compare runs on the same machine and
treat absolute numbers as a ceiling check.

Options:

- `--runs N`: N separate subprocess runs; `--out` gets `{runs, median, min, max, spread_pct}` and
  thresholds are checked on the median. `--baseline` accepts either shape.
- `--frame-log PATH` (fake renderer only): a second pass on a cold cache that scrolls like the
  app (`scrollbar.setValue` + `processEvents`, never `repaint()` or a mouse event), reads the
  window backing store with `QScreen.grabWindow` after each step (a self-check first proves it
  keeps blitted pixels) and classifies each visible row as ok / blank / wrong / stale against a
  fresh paint that is rendered without requesting thumbnails (the log never loads rows itself);
a tile showing the placeholder paper counts as blank, never wrong. One JSON line per frame; summary metrics `frames_with_wrong`, `frames_with_stale`,
  `blank_rows_after_settle`, `max_blank_rows_in_frame`. With `--runs`, run k > 1 logs to `PATH.k`.

When a threshold fails, find the hotspot:

```bash
QT_QPA_PLATFORM=offscreen python -m cProfile -o /tmp/kontrol.prof .claude/skills/perf-profile/perf_kontrol.py --pages 1000
python -c "import pstats; pstats.Stats('/tmp/kontrol.prof').sort_stats('cumtime').print_stats(25)"
```

Look at `TimelineView.paintEvent`, `_rows_between`, `TimelineDelegate._scan` (image scaling) and
`ThumbnailService._finished` (GUI-thread work per finished page).

## Thresholds to hold

| Metric | Limit | Why |
|---|---|---|
| paint_cost_p95_ms (full viewport repaint per scroll step) | <= 16.7 ms | 60 Hz |
| paint_cost_max_ms | <= 50 ms | no visible hitch |
| first paint of 1000 pages | < 1000 ms | existing test bound |
| settle after a jump (fake 15 ms renderer) | <= 1500 ms | page content arrives without input |
| settled_loaded_pct_real (jump, no repaint, no mouse) | 100 % | the hover bug must be gone |
| rows prefetched beyond the view | > 0, bounded by capacity | scrolling at normal speed never shows empty paper |
| memory | cache <= `capacity` (400) images | LRU holds |

The same limits are constants (`THRESHOLDS`) in `perf_kontrol.py`; change both together and
justify it in the commit. Do not trade correctness for speed: a thumbnail for page N must never be
drawn in page M's slot (check `pid` identity, `ThumbnailService._version` and `invalidate`).

## After the fix

1. Re-run the same commands with `--baseline /tmp/before.json --out /tmp/after.json` and paste
   the before/after table (paint cost p50/p95/max, settle, loaded % real) in the report.
2. Add or tighten tests in `tests/ui/test_kontrol.py` / `tests/ui/test_thumbnails.py` using the
   fake renderer (no PDF, no timing flakiness): scroll without mouse events, `qtbot.waitUntil`
   all visible pids are `service.is_current`, assert renders stay within visible + margin, assert
   `keep_only` is called with the margin set. Run only those files.
3. Check zoom (status-bar slider changes `set_height`, `THUMB_DELAY_MS = 150` in `kontrol.py`),
   a fast scroll to the end, rotating a page (`invalidate`), and 150 % text, with the screenshots
   matrix clipping check (see `ui-bug-hunt`) for Kontrol.
