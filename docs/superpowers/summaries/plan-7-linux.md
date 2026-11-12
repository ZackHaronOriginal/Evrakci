# Plan 7 summary: Linux build

Owner's request, 2026-11-09. Plan: `docs/superpowers/plans/2026-11-09-plan-7-linux.md`.

## What works

- `evrakci-<sürüm>-linux-x86_64.tar.gz` (+ `.sha256`), built by the "Linux build" workflow on
  Ubuntu 22.04 (artifact **Evrakci-Linux**). Same two programs as Windows: `evrakci` and
  `evrakci-arayuz`, as a cx_Freeze folder build (Qt replaceable, LGPL).
- Bundled Turkish OCR data (tur_best) with Tesseract's config files and English data, so a
  read-only install works with only the system's `tesseract-ocr`.
- `./kur.sh`: per-user install (no root), applications menu entry with icon, `~/.local/bin`
  links that never replace another program's, warnings for missing Tesseract or window
  libraries, and the exact uninstall command. `kaldir.sh` removes exactly what was installed;
  jobs and templates stay.
- CI proves it: tests, freeze, window start, OCR smoke test with the system's Turkish data
  removed, install from Turkish-named folders as a non-root user with a read-only install,
  uninstall, and a clean Debian 12 and Ubuntu 24.04 with only the documented packages, where
  the window opens on Xvfb. Green in run 42552347140; Windows installer green in 42552347118.

## Commands

```bash
python packaging/build.py --tur-best tur.traineddata --tessdata-configs /usr/share/tesseract-ocr/5/tessdata
```

```bash
python packaging/linux_package.py --cikti dist
```

## Decisions

- Tesseract from the distribution, not bundled (its shared libraries differ per distribution).
- GPL-only parts never ship: Qt Virtual Keyboard and Qt Wayland Compositor are deleted from
  both builds (Windows too), Readline, GDBM and curses are excluded, and the build fails if any
  remains (`packaging/gpl_check.py`).
- Licence and copyright texts of the Python runtime's libraries and ICU in `licenses/linux/`.
- Found on the way, fixed in the core with tests: Tesseract 4 (Ubuntu 22.04) does not print its
  data folder and needs `eng.traineddata` beside `tur`; the data-file hash cache now notices a
  replaced file even on coarse clocks.
- A fresh review found 18 issues in the first version; all fixed, each with a failing test first
  where a test can show it.

## Tests

383 pass; `ruff check .` is clean.
