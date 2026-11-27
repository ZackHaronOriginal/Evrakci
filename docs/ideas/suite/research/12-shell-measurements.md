# Shell measurements: React grid on the Python backend (2026-11-27)

**Status: measurements for a decision, not decided.** Throwaway spike, not in the repository: a React +
TanStack Virtual grid of a 1000-page invented PDF; Python renders thumbnails with PDFium in one thread,
writes them to a cache folder and serves them as files with a token; the UI calls Python through one
JSON-RPC-shaped bridge. Same React build and the same in-page measuring script everywhere.

| | Windows 10 laptop, pywebview + WebView2 (run 1 / run 2) | Linux VM, pywebview + Qt WebEngine | Linux VM, Electron 33 + Python sidecar | Linux VM, headless Chromium | Linux VM, today's Qt UI |
|---|---|---|---|---|---|
| Machine | 4 cores, 3.9 GB RAM, real screen and GPU | 4 cores, no GPU, virtual screen | same | same, no window | same, offscreen |
| Start until pages shown | 11.5 s / 5.9 s | 0.46 s | 0.38 s | — | 0.13 s (first paint) |
| First thumbnails | 12.0 s / 6.3 s | 0.63-0.71 s | 0.58 s | 0.14-0.26 s | ~0.2 s |
| UI→Python call p50 / p95 | 1.6 / 2.7 ms, 1.5 / 2.5 ms | 0.8 / 1.2 ms | 0.1 / 0.2 ms | 0.2 / 0.7 ms | — |
| Scrolling: frames over 20 ms (of 299) | 0 / 0 | 103-119 | 0 | 0 | paint p95 14.5 ms |
| Jump, cold (ms) | 463-622 / 434-841 | 19-347 | 250-387 | 110-395 | 192 |
| Jump, warm (ms) | 0-24 / 0-33 | 0-23 | 19-58 | 12-20 | — |
| Memory idle | 408 / 399 MB | 582 MB | 611 MB | — | — |
| Memory after scrolling | 505 / 515 MB (Python ~100, WebView2 ~404) | 915 MB | 801 MB | 622 + 59 MB | 259 MB |

Findings:
- On Windows, pywebview with WebView2 scrolls smoothly and stays near 500 MB on a 4 GB PC.
- The Linux stutter is Qt WebEngine's display path: Electron on the same virtual screen had no slow frames.
- Cold jumps are slow because the spike renders with one thread; tunable.
- Startup on the Windows laptop is the open problem: 11.5 s first run, 5.9 s second run (WebView2 and the
  .NET bridge starting, first-run file scans and .pyc compilation are suspected, not yet split out).
- The spike never evicts loaded thumbnails, which inflates "after scrolling" memory everywhere.

## Windows laptop, side by side (2026-11-27, second test)

Same laptop: Intel Core i3-7100 (2 cores, 4 threads), 3.9 GB RAM, Windows 10 Home 19045. Same React build,
same Python backend code, same measuring script. Start-up split into steps. Run 1 = first start after unzip,
run 2 = second start (the everyday number).

| | pywebview 6.2.1 + WebView2 (Chromium 158), run 1 / run 2 | Electron 45.3.1 (Chromium 156) + Python sidecar, run 1 / run 2 |
|---|---|---|
| Python ready | 0.27 / 0.24 s | 3.6 / 0.76 s |
| .NET + Windows Forms loaded | 2.6 / 0.97 s | — |
| Window shown / created | 3.0 / 1.2 s | 3.7 / 0.81 s |
| Page starts loading | 4.1 / 1.9 s | 3.7 / 0.81 s |
| React running | 4.5 / 2.1 s | 4.2 / 0.97 s |
| Pages shown | 4.7 / 2.2 s | 4.3 / 1.05 s |
| First thumbnails | 5.1 / 2.5 s | 24.3 / 1.6 s (run 1 anomaly, see below) |
| UI→Python call p50 / p95 | 1.7 / 2.4, 1.5 / 2.7 ms | 0.3 / 0.6, 0.3 / 0.8 ms |
| Scrolling: frames over 20 ms (of 299) | 0 / 0 | 3 / 0 |
| Jump, cold | 446-657 ms | 202-629 ms |
| Memory idle | 403 / 400 MB (Python ~99) | 381 / 359 MB (Python ~48) |
| Memory after scrolling | 525 / 525 MB | 514 / 466 MB |

- Electron was faster to start, lighter and had faster calls on this PC; both scrolled smoothly.
- Run 1 of Electron took 24 s to the first thumbnails although pages were shown at 4.3 s; run 2 was normal.
  Suspected first-run antivirus scanning or a one-time security prompt; to check in the real build.
- Earlier pywebview runs on the same laptop (first test zip, different launcher) took 11.5 s and 5.9 s to show
  pages; the 2.2 s here is the second start of the second package.

## Decision (owner, 2026-11-27)

**The shell is Electron.** React + TypeScript UI in Electron, the Python backend as a separate process that
Electron starts and stops, talking through one versioned JSON-RPC bridge. pywebview stays as a fallback only.
Known costs accepted: a larger installer (about +100 MB), a second process to supervise, and shipping Chromium
security updates with Evrakçı's own updates.
