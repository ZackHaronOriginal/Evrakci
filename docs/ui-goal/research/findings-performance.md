# Findings: performance (5c, R5c-3)

Researched 2026-11-19 at commit 89c4844. Ideas only, nothing decided. Focus: the Kontrol strip with 100 to 800 (test target 1000) pages, long sessions. "We do" cites [inventory-kontrol.md](inventory-kontrol.md) (K-xx), [inventory-app-wide.md](inventory-app-wide.md) and the code. Each external claim links to a page that was opened. No measurement was run in this task.

## What we do
Thumbnails render in worker threads only when a tile is painted; scrolled-out requests are dropped; failures show nothing (K-86; `ui/thumbnails.py`). An LRU cache of 400 images (`capacity: int = 400`, thumbnails.py line 81); after a zoom change old images stay and are drawn scaled until new ones arrive (thumbnails.py module note); zoom change waits `THUMB_DELAY_MS = 150` (perf-profile skill, `.claude/skills/perf-profile/SKILL.md`). Loupe strip renders only the pages it shows, cache 400 (K-94, K-95). Placeholder "Yükleniyor" (K-83). Thresholds already fixed: frame p95 at most 16.7 ms, max 50 ms, first paint of 1000 pages under 1000 ms, settle after a jump at most 1500 ms (perf-profile skill). The busy cursor helper exists but no code calls it (A-65). The Dışa Aktar name column measures at most 500 rows (D header note); the folder check lists the directory on every keystroke (Obs. 14).

## Comparison table

| Practice | Who does it (opened links) | What we do | Gap | Cost to us | Perf cost | Risk |
|---|---|---|---|---|---|---|
| Render only what is visible, drop scrolled-out requests | PDF Arranger: visible range = items more than about half on screen; a render thread is stopped and restarted on scroll; the render call is debounced about 149 ms ([source pdfarranger.py](https://github.com/pdfarranger/pdfarranger/blob/main/pdfarranger/pdfarranger.py), read only, GPL-3.0; first 100000 characters read) | Same idea, per tile, in a thread pool (K-86) | None. We keep old images while zooming, which that code does not show | none | none | none |
| Skip drawing items with no image yet | PDF Arranger cell renderer returns without drawing when a page has no thumbnail ([source iconview.py](https://github.com/pdfarranger/pdfarranger/blob/main/pdfarranger/iconview.py), read only) | Placeholder tile with "Yükleniyor" (K-83) | Ours is friendlier | none | none | none |
| Uniform item sizes and batched layout in Qt views | `QListView.uniformItemSizes` enables optimizations when all items are equal; `Batched` layout lays out 100 items at a time (default) so visible items are usable early ([Qt docs](https://doc.qt.io/qt-6/qlistview.html)) | Kontrol is a custom flow layout with stacks and guide tabs (K-78, K-79), not a `QListView`; tile sizes vary (separator tiles 48 px, K-80) | Cannot adopt as is. Measure instead of assuming | none | none | A rewrite onto a model view would be L |
| Pixmap cache sized by bytes, least-recently-used eviction, main thread only | `QPixmapCache`: default 10,240 KB, size estimated from width, height, depth; calls from other threads fail ([Qt docs](https://doc.qt.io/qt-6/qpixmapcache.html)) | Own LRU by count, 400 entries (thumbnails.py) | A count is not a byte cap: at 200 percent zoom each tile is bigger, so memory per entry grows. Unverified: memory at 800 pages zoomed in during an 8 hour session | S to M (cap by bytes) | lowers memory | Cache too small at high zoom makes re-renders visible |
| Response-time limits | Under 0.1 s feels instant; over 1 s show that work is going on, for example a changed cursor; over 10 s show percent-done progress and a way to stop ([NN/g](https://www.nngroup.com/articles/response-times-3-important-limits/)) | Export has banner, progress, stop (D-38, D-40); the busy cursor exists but is never used (A-65); folder check on every key (Obs. 14) | Waits between 1 and 10 s on the window thread have no cue (unknown which exist; e.g. opening a big job, Obs. 14) | S (use `busy()` where a block exceeds 1 s) | none | none |
| Cheap status for long lists | Transact Validate shows per-document red or green status in a list ([Ephesoft docs](https://ephesoft.com/docs/?p=47801)) | Overview squares per page, even at 800 pages (K-73) | None | none | none | none |
| Perf regression gate | Not found in any opened product page | `perf-profile` skill with fixed thresholds | We are ahead of what was found | none | none | none |

## Ideas for the owner's ranking
1. **Cap the thumbnail cache by bytes instead of 400 entries.** Problem: memory grows with zoom; long sessions. Who gains: staff on older PCs with 4 to 8 GB. Evidence: [QPixmapCache](https://doc.qt.io/qt-6/qpixmapcache.html) sizes by pixels and depth. Effort S to M. First measure (perf-profile run at 200 percent zoom, 1000 pages).
2. **Use the busy cursor for any window-thread block longer than 1 second** (opening a large job, first paint). Problem: no cue. Evidence: [NN/g](https://www.nngroup.com/articles/response-times-3-important-limits/), A-65 (helper exists, unused). Effort S.
3. **Debounce the folder check on Dışa Aktar** (Obs. 14, directory listing per keystroke; slow on network shares). Evidence: debounce is the PDF Arranger approach ([source](https://github.com/pdfarranger/pdfarranger/blob/main/pdfarranger/pdfarranger.py)). Effort S.
4. **Extend the perf script to a 200 percent zoom sweep and an 8 hour memory soak** (not in the skill thresholds). Effort S to M.

## Unverified
- All timings: none measured here. Thresholds are quoted from our own skill file.
- Body of PDF Arranger's `PDFRenderer` thread (the order of pages inside the visible range); the last 48 kB of `pdfarranger.py` were not read.
- NAPS2, FastRawViewer or any commercial viewer's thumbnail strategy: no source page found. A search for NAPS2's thumbnail code returned nothing usable.
- TanStack Virtual (web, not usable in PySide6) was not re-opened in this task; see competitors.md.
- Real memory use with 800 pages at high zoom.
