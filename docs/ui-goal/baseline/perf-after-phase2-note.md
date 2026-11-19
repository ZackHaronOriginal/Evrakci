# Phase 2 note: Kontrol scroll performance

Hypotheses (measured on the old code, fake 1000 pages): scrollContentsBy does nothing: TRUE (old 0 % loaded, 269 wrong, 307 stale; with `viewport().scroll` alone 100 % / 0 / 0). One-rect update in `_thumbnail_ready`: not shown (stale 0 after the scroll fix). `_forget_hidden` drops pending requests: true as waste (440 dropped in 310 calls), not a cause. Synchronous ready emit inside paint: false (0 emits, `_scan` requests only when not current). Count-capped cache explains the 1186 MB real RSS: false (real 300 pages: 461 MB right after building the job, 501 MB after the sweep, cache 28 MB). True cause: `TimelineView` did not blit or repaint on scroll (B-032), and thumbnails were requested only from paint. The one-rect update and the synchronous emit are not causes. The real-run RSS comes from building the job, not from the thumbnail cache.

Changes: `TimelineView.scrollContentsBy` scrolls the viewport; `load_thumbnails` (on scroll and after a layout) requests the pages in view plus a margin (1 viewport ahead, 0.5 behind, nearest first) and keeps only those; separators are never requested; the cache is capped at 400 images (raised to 1.5 x the requested pages on large screens at low zoom) and 150 MB of pixels (`CACHE_MAX_BYTES`); over a cap it drops to 90 % in one batch, farthest page from the viewport first (about 0.003 ms per arrival, max 0.9 ms, in the 1000-page sweep). The old job's service is stopped, invalidated and released on job switch.

| Metric (median of 5 runs, fake 1000 pages) | Before | After, set 1 | After, set 2 |
|---|---|---|---|
| settled_loaded_pct_real | 0.0 | 100.0 | 100.0 |
| frames_with_wrong / frames_with_stale | 269 / 307 | 0 / 0 | 0 / 0 |
| settle_ms | 133.7 | 142.2 | 145.3 |
| paint_cost_p95_ms / max | 14.18 / 17.29 | 14.45 / 20.46 | 14.11 / 17.69 |
| first_paint_ms (renders) | 79.1 (12) | 80.7 (24) | 80.5 (24) |
| prefetched rows below view | 0 | 12 | 12 |
| RSS fake (MB) | 211 | 210.9 | 210.9 |
| RSS real, 300 pages | 501 MB | 501 MB (not re-run) | |

Source: `perf-after-phase2.json` (the official numbers; this table copies its fake_1 and fake_2 medians). Real PDFs (real_1, real_2): the settle time rose from 184/187 ms to 204/243 ms because the prefetch margin competes with the visible pages for the two workers, and paint max rose from about 17-18 ms to 21-23 ms. Both stay inside the targets (settle limit 1500 ms, paint max limit 50 ms).

Caveats: the 1186 MB real 1000-page figure was not re-measured in this step; the "RSS real 501 -> 501" row is the same-size 300-page run before and after, so it shows only that the cache change does not move RSS. At 1000 pages and 100 % zoom the byte ceiling (150 MB, a tile is about 92 KB) does not bind; the 400-image cap does (about 37 MB). The byte cap matters at high zoom or a high device pixel ratio: tile bytes scale with zoom squared times the device pixel ratio squared (about 1.47 MB at zoom 200 and ratio 2, so 150 MB holds about 100 tiles).
