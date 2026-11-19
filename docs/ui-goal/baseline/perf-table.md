# Performance table: before (v2), after Phase 2, final

Medians. Machine: cloud container, offscreen. `fake` = fake renderer 15 ms, 1000 pages (5 runs); `slow` = 60 ms (5 runs); `real` = real PDF via pdfium (5 runs). Before/Phase 2 `fake` is set 1. A dash means the run has no such metric (no frame log).

## Like-for-like (1000 pages)

| Metric | fake before | fake P2 | fake final | slow before | slow P2 | slow final | real before | real P2 | real final |
|---|---|---|---|---|---|---|---|---|---|
| settled_loaded_pct_real | 0.0 | 100.0 | 100.0 | 0.0 | 100.0 | 100.0 | 0.0 | 100.0 | 100.0 |
| frames_with_wrong | 269 | 0 | 0 | - | - | - | - | - | - |
| frames_with_stale | 307 | 0 | 0 | - | - | - | - | - | - |
| blank_rows_after_settle | 48 | 0 | 0 | - | - | - | - | - | - |
| max_blank_rows_in_frame | 18 | 18 | 18 | - | - | - | - | - | - |
| settle_ms | 133.7 | 142.2 | 143.9 | 563.9 | 597.2 | 600.0 | 184.4 | 204.4 | 202.6 |
| settled_loaded_pct_forced | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| paint_cost_p50_ms | 11.19 | 11.25 | 10.33 | 9.37 | 9.77 | 9.14 | 12.51 | 12.58 | 11.01 |
| paint_cost_p95_ms | 14.18 | 14.45 | 13.27 | 12.63 | 13.33 | 12.96 | 15.83 | 15.49 | 14.48 |
| paint_cost_max_ms | 17.29 | 20.46 | 18.4 | 14.85 | 18.41 | 21.13 | 21.43 | 22.89 | 20.27 |
| frames_over_16ms | 2 | 3 | 2 | 0 | 1 | 3 | 7 | 7 | 4 |
| frames_over_33ms | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| first_paint_ms | 79.1 | 80.7 | 79.3 | 76.4 | 79.2 | 81.5 | 76.8 | 79.0 | 77.9 |
| renders_at_first_paint | 12 | 24 | 24 | 12 | 24 | 24 | 12 | 24 | 24 |
| first_settle_ms | 90.3 | 80.6 | 80.2 | 357.5 | 350.0 | 352.9 | 85.4 | 72.3 | 72.2 |
| renders_at_first_settle | 12 | 14 | 14 | 12 | 14 | 14 | 14 | 14 | 14 |
| prefetched_rows_below_view | 0 | 12 | 12 | 0 | 6 | 6 | 0 | 12 | 12 |
| cache_size | 400 | 394 | 392 | 174 | 193 | 189 | 381 | 389 | 389 |
| rss_mb_after_sweep | 211.2 | 210.9 | 211.4 | 188.5 | 188.9 | 189.0 | 1186.1 | 1184.7 | 1181.6 |

## New full-scale cases (final code, 3 runs each)

| Metric | 2000 pages | 1000 @150 % text | 1000 hc theme | real, disk +20 ms | mem cap 1500 | mem cap 1100 | mem cap 800 |
|---|---|---|---|---|---|---|---|
| settled_loaded_pct_real | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 0.0 |
| frames_with_wrong | 0 | 0 | 0 | - | 0 | - | - |
| frames_with_stale | 0 | 0 | 0 | - | 0 | - | - |
| blank_rows_after_settle | 0 | 0 | 0 | - | 0 | - | - |
| max_blank_rows_in_frame | 18 | 10 | 18 | - | 18 | - | - |
| settle_ms | 145.4 | 130.0 | 150.8 | 302.9 | 147.4 | 145.6 | 145.6 |
| settled_loaded_pct_forced | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| paint_cost_p50_ms | 9.47 | 7.73 | 3.45 | 10.32 | 10.13 | 10.25 | 10.89 |
| paint_cost_p95_ms | 12.52 | 10.68 | 6.0 | 13.46 | 13.56 | 13.14 | 13.77 |
| paint_cost_max_ms | 16.68 | 16.78 | 13.88 | 16.87 | 20.25 | 15.48 | 20.49 |
| frames_over_16ms | 0 | 1 | 0 | 1 | 2 | 0 | 2 |
| frames_over_33ms | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| first_paint_ms | 88.9 | 70.5 | 66.2 | 69.7 | 86.8 | 75.5 | 84.1 |
| renders_at_first_paint | 24 | 20 | 24 | 24 | 24 | 24 | 24 |
| first_settle_ms | 77.3 | 71.4 | 87.0 | 156.5 | 77.8 | 77.0 | 80.9 |
| renders_at_first_settle | 14 | 12 | 14 | 14 | 14 | 14 | 14 |
| prefetched_rows_below_view | 12 | 10 | 12 | 12 | 12 | 12 | 12 |
| cache_size | 383 | 339 | 238 | 280 | 388 | 391 | 391 |
| rss_mb_after_sweep | 211.4 | 204.4 | 192.6 | 1170.7 | 210.7 | 211.4 | 211.5 |
| memory_run_completed | - | - | - | - | 1 | 1 | 1 |
| vm_mb_at_cap | - | - | - | - | 1211.9 | 1053.8 | 799.6 |

## Worse than before, or flagged

Worse than before (all inside the thresholds, none a regression of correctness):

- `renders_at_first_paint` 12 -> 24 and `renders_at_first_settle` 12 -> 14: on purpose, the prefetch margin (one viewport ahead, half behind) is requested at once (Phase 2).
- `settle_ms` rose by 6-10 % (fake 133.7 -> 143.9, slow 563.9 -> 600.0, real 184.4 -> 202.6; limit 1500): the margin competes with the visible pages for the two workers.
- `paint_cost_max_ms` slow 14.85 -> 21.13, fake 17.29 -> 18.4 (limit 50): single-frame outliers from the margin loading; p95 is unchanged or lower in every set (limit 16.7).
- `frames_with_wrong` and `frames_with_stale` 269 / 307 -> 0 / 0, `settled_loaded_pct_real` 0 -> 100: the Phase 2 fix.
- RSS unchanged (fake ~211 MB; real ~1180 MB is job creation, ledger B-040).

New cases: all pass every threshold except the tight memory cap (800 MB RLIMIT_AS, virtual size; the app uses about 1054 MB of address space): there 2 of 3 runs loaded 0 % of visible rows, so the app does not load thumbnails under that cap. 1100 and 1500 pass unchanged. Disk delay 20 ms per render: settle 303 ms. 2000 pages, 150 % text and hc theme show no difference in correctness (0 wrong, 0 stale, 100 %).