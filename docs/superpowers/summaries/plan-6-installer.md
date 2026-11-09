# Plan 6 summary: Windows installer

- **Works:** cx_Freeze folder build (Qt replaceable per LGPL), only `tesseract.exe` + its DLLs +
  configs and SHA-256-verified `tur_best` bundled, licence texts and NOTICE, Inno Setup per-user
  installer, built and smoke-tested on a Windows runner in GitHub Actions (window start-up,
  bundled Tesseract alone, Turkish-named folders).
- **Decisions:** cx_Freeze (PSF) instead of the GPL PyInstaller; ASCII install folder name;
  every shipped package listed in `docs/dependency-licenses.md` and checked by a test.
- **Reviews:** `b9d485e`; fresh review 2026-11-08 → `ba4c6d9` (11 new tests).
- **Second fresh review (2026-11-09, report in the session):** 16 findings, all fixed in `df04532`
  (`tests/test_packaging_review2.py`, 35 tests). Most important: the earlier Windows bundle
  shipped GPL-only `libjbig-0.dll` (via the UB Mannheim Tesseract's libtiff). Tesseract is now
  built from source by vcpkg at a pinned commit as one static `tesseract.exe` with an
  allow-list of permissive libraries and their licence texts. Licences are collected from
  what is really in `lib\`; CI pins actions, installs from a hashed lock, runs the real
  window and a silent install/upgrade/uninstall. Left for the owner: code signing (needs a
  certificate) and Inno Setup's own checksum (pinned through Chocolatey's package).
- **Last build:** run 42561985121 (commit `f1b4a2b`), green: vcpkg Tesseract, tests, freeze, real
  window, smoke tests, installer, silent install/upgrade/uninstall. Artifact `Evrakci-Kurulum`.
  Linux build run 42561985529 green. Tests: 525.
