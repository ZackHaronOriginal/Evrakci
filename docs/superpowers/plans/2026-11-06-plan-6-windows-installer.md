# Plan 6: Windows Installer. Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A normal Windows installer (`Evrakci-Kurulum-<sürüm>.exe`) that installs:
- the CLI (`evrakci.exe`) and the window (`evrakci-arayuz.exe`)
- Tesseract with the official Turkish data, so staff need nothing else

It is built automatically on a Windows runner in GitHub Actions.

**Architecture:**
- **cx_Freeze** (PSF-2.0) makes a **folder build**, not a single file. The Qt DLLs stay as separate,
  replaceable files, as the LGPL requires.
- **Inno Setup** (a BSD-style licence) wraps the folder into an installer with a Start-menu and
  desktop shortcut to the window.
- A bundled `tesseract/` folder (Tesseract for Windows, Apache-2.0) and `tessdata_best/tur`
  ship next to the exes. The app looks for them **beside itself first**.
- Plan 5 adds the real window later, and the same workflow then packages it unchanged.

**Tech Stack:** cx_Freeze ≥ 8, Inno Setup 6 (`iscc`), GitHub Actions `windows-latest`, Chocolatey
(only at build time, to fetch Tesseract).

**Spec:** `docs/superpowers/specs/2026-11-06-scan-and-split-design.md` §3 (Install: a normal Windows
installer built as a folder, so Qt stays replaceable)

## Global Constraints

- Folder build only; never a one-file bundle.
- Licence texts ship in `licenses/`:
  - LGPL-3.0 and GPL-3.0 (for Qt / PySide6)
  - Apache-2.0 (for Tesseract and the PaddleOCR models)
  - the Evrakçı AGPL-3.0
  - `NOTICE.txt`, listing every bundled component, its licence and where its source is
- No Ghostscript, PyMuPDF or PyQt.
- Bundled data is verified with the pinned SHA-256 before packaging.
- Frozen executables call `multiprocessing.freeze_support()` first, because OCRmyPDF uses worker
  processes.
- The CLI exe keeps its console. The window exe has no console.
- Commits are authored by ZackHaronOriginal with no Claude lines. Tests and ruff pass. No real
  documents anywhere.

## Review Focus

1. **Bundled Tesseract is found before anything on PATH**, including when the app is installed
   under `C:\Program Files\Evrakçı` (non-ASCII and spaces in the path). Test in Task 1.
2. **The bundled `tur_best` is used without a download**, and the app data folder is still used for
   anything the user downloads later. Test in Task 1.
3. **Frozen OCR worker processes don't respawn the whole CLI** (missing `freeze_support`). Test in
   Task 2 (the entry points call it; checked by a unit test plus the CI smoke run).
4. **The installer upgrades in place** (same AppId) and never deletes job data in app data on
   uninstall. Covered in Task 3 (`.iss` review plus CI).
5. **The CI build fails loudly** when a checksum or download fails. Covered in Task 3.

---

### Task 1: Find bundled Tesseract and data first

**Files:** Modify `src/evrakci/pipeline/ocr/tesseract.py`, `src/evrakci/pipeline/ocr/models.py`.
Test `tests/test_bundle_paths.py`.

**Interfaces:**
- `models.app_dir() -> Path | None`
  - returns the folder of the running executable when frozen (`sys.frozen`), otherwise `None`
  - `EVRAKCI_UYGULAMA_KLASORU` overrides it, for tests
- `find_tesseract()` order:
  1. `EVRAKCI_TESSERACT`
  2. `app_dir()/tesseract/tesseract.exe` (or `tesseract` on Linux/macOS)
  3. PATH
  4. the usual Windows install folders
- `tessdata_dir(variant)` order:
  1. the `EVRAKCI_TESSDATA_<V>` environment variable
  2. `app_dir()/tessdata_<v>`, if its file verifies
  3. `data_dir()/tessdata_<v>`
- [ ] **Steps:**
  - Tests:
    - `test_bundled_tesseract_first`: a fake executable script in `tmp/Evrakçı Uygulama/tesseract/`
      with the override set
    - `test_bundled_tessdata_used`
    - `test_not_frozen_means_no_app_dir`
  - Commit `feat: prefer bundled Tesseract and data`

### Task 2: Frozen entry points and cx_Freeze build

**Files:**
- Modify `src/evrakci/cli/main.py`, `src/evrakci/app.py`: call `freeze_support()` first in the
  `__main__` and script entries
- Create `packaging/freeze_setup.py`: cx_Freeze `setup()`
  - two executables: `evrakci` (console), and `evrakci-arayuz` (`base="gui"` on Windows)
  - `include_files`: `licenses/`, plus `tesseract/` and `tessdata_best/` when they exist
  - packages: `evrakci`, `ocrmypdf`, `pikepdf`, `pypdfium2`, `zxingcpp`, `segno`, `openpyxl`,
    `PySide6`
  - excludes: `tkinter`, `unittest`
- Create `packaging/licenses/`: `NOTICE.txt` plus the licence texts
- Create `packaging/build.py`: verifies the data, runs the freeze and prints the output folder
- Test `tests/test_packaging.py`
- **Interfaces:** `python packaging/build.py [--tesseract DIR] [--tur-best FILE]` produces
  `build/evrakci/` with the executables, `licenses/` and the optional bundles.
- [ ] **Steps:**
  - Tests:
    - `test_entry_points_call_freeze_support`: inspect the source of `main` and `app.main`
    - `test_notice_lists_components`
    - `test_build_verifies_tur_best` (a wrong file is refused; uses the `verify_tessdata` logic)
  - Then a local **Linux smoke build**: run `python packaging/build.py`, then run
    `build/evrakci/evrakci --version` and `build/evrakci/evrakci ayirac x.pdf --adet 1`
  - Commit `feat: cx_Freeze folder build`

### Task 3: Inno Setup script and Windows workflow

**Files:**
- Create `packaging/evrakci.iss`:
  - fixed `AppId` GUID
  - `{autopf}\Evrakçı`
  - Turkish installer language
  - Start-menu and optional desktop shortcut to `evrakci-arayuz.exe`
  - adds the install folder to the user's PATH (optional task) so `evrakci` works in a terminal
  - uninstall leaves app data alone
- Create `.github/workflows/windows-installer.yml`, which runs on `workflow_dispatch`, `push` of
  tags `v*`, and changes to `packaging/**` or this workflow on the working branch. Steps:
  1. checkout, then Python 3.12
  2. `pip install -e ".[dev]" cx_Freeze`
  3. `pytest -q`
  4. `choco install tesseract innosetup -y`
  5. copy the Tesseract install folder (minus its non-Turkish language data) into
     `packaging/tesseract`
  6. download `tur_best`, verify its SHA-256, and fail on a mismatch
  7. `python packaging/build.py`
  8. smoke-test the built `evrakci.exe --version` and `evrakci.exe ocr` on a generated synthetic PDF
  9. `iscc packaging/evrakci.iss`
  10. upload the installer as an artifact
- [ ] **Steps:**
  - Test `test_iss_has_required_settings`: parse the `.iss` for `AppId`, `LicenseFile`, the
    language, and that `UninstallDelete` never touches `{userappdata}`.
  - Push, then watch the workflow run through the GitHub tools until it's green, fixing failures
    with TDD where they are code.
  - Commit `feat: Windows installer and CI workflow`

### Task 4: Docs

- README (both languages): an "Kurulum (Windows)" section on how to get the installer from GitHub
  Actions artifacts or releases
- `docs/dependency-licenses.md`: cx_Freeze (PSF-2.0, build tool and runtime stubs), Inno Setup
  (BSD-style, build tool), and bundled Tesseract for Windows (Apache-2.0)

Commit `docs: Windows installer`.
