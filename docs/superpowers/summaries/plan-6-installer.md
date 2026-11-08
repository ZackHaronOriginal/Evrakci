# Plan 6 summary: Windows installer

- **Works:** cx_Freeze folder build (Qt replaceable per LGPL), only `tesseract.exe` + its DLLs +
  configs and SHA-256-verified `tur_best` bundled, licence texts and NOTICE, Inno Setup per-user
  installer, built and smoke-tested on a Windows runner in GitHub Actions (window start-up,
  bundled Tesseract alone, Turkish-named folders).
- **Decisions:** cx_Freeze (PSF) instead of the GPL PyInstaller; ASCII install folder name;
  every shipped package listed in `docs/dependency-licenses.md` and checked by a test.
- **Reviews:** `b9d485e`; fresh review 2026-11-08 → `ba4c6d9` (11 new tests).
- **Last build:** run 42448379964, green, artifact `Evrakci-Kurulum`. Tests: 352.
