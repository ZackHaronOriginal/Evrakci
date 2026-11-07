# Dependency licenses

Evrakçı is AGPL-3.0-or-later. The maintainer may also offer it under commercial terms
(see [CLA.md](../CLA.md)). **Every dependency must allow both uses.** The safe choices are
permissive licenses (MIT, BSD, Apache-2.0), weak copyleft (MPL-2.0, LGPL) used as a separate
library, and tools run as separate programs.

| Dependency | License | How we use it | OK for commercial/closed builds? |
|---|---|---|---|
| PySide6 / Qt | LGPL-3.0 | Dynamically linked Python package | ✅ If users can replace the Qt libraries. Ship a folder build, not a single static binary, and include the LGPL text plus the source location |
| pikepdf (with `[pdfa]`) | MPL-2.0 | Library | ✅ Changes to pikepdf's own files must be shared |
| jsonschema, referencing, fonttools, rpds-py, attrs (via `pikepdf[pdfa]`) | MIT | Libraries | ✅ |
| pypdfium2 / PDFium | Apache-2.0 / BSD-3 | Library | ✅ |
| openpyxl | MIT | Library | ✅ |
| Pillow | HPND | Library | ✅ |
| segno | BSD-3-Clause | Library (QR generation) | ✅ |
| zxing-cpp | Apache-2.0 | Library (QR reading) | ✅ |
| platformdirs | MIT | Library (app data folder) | ✅ |
| OCRmyPDF | MPL-2.0 | Library | ✅ |
| Tesseract + official Turkish data (`tur_fast`, `tur` standard, `tur_best`) | Apache-2.0 | External program and data files (SHA-256 pinned) | ✅ |
| rapidocr (optional extra `rapidocr`) | Apache-2.0 | Library | ✅ |
| PaddleOCR model weights (via RapidOCR, `PP-OCRv5` det + `latin` rec) | Apache-2.0 | Model files, downloaded and SHA-256 verified | ✅ |
| onnxruntime (optional) | MIT | Library | ✅ |
| opencv-python-headless (optional, via rapidocr) | Apache-2.0 | Library | ✅ |
| shapely, pyclipper, omegaconf, PyYAML, tqdm, colorlog, six, requests (optional, via rapidocr) | BSD-3 / MIT / BSD / MIT / MPL-2.0+MIT / MIT / MIT / Apache-2.0 | Libraries | ✅ |
| Ghostscript | **AGPL-3.0** | **Not used.** OCRmyPDF 17.13+ makes PDF/A without it (`--pdfa-backend internal`) | Not bundled and never called |
| qpdf | Apache-2.0 | Via pikepdf | ✅ |

## Development only (not shipped)

| Component | License | How it is used |
|---|---|---|
| pytest, pytest-qt | MIT | Running the tests, including window tests without a screen |
| ruff | MIT | Code style checks |

## Build tools and bundled programs (Windows installer)

| Component | License | How it is used | OK for commercial/closed builds? |
|---|---|---|---|
| cx_Freeze | PSF-2.0 | Build tool; its small runtime stubs ship in the folder build | ✅ |
| Inno Setup | BSD-style (Inno Setup License) | Build tool for the installer | ✅ Keep its copyright notice |
| Tesseract for Windows (UB Mannheim build) | Apache-2.0 | Bundled external program in `tesseract\` | ✅ |
| Licence texts for all bundled parts | — | `licenses\` in the install folder, listed in `NOTICE.txt` | — |

## Avoid

- **PyQt6 / PyQt5**: GPL unless you buy a commercial license.
- **PyMuPDF (fitz)**: AGPL unless you buy a commercial license from Artifex.
- Any package with no license, or a "non-commercial" or "research only" license.
- OCR or AI models whose weights are licensed for non-commercial use only.

## How to check

```bash
pip install pip-licenses
pip-licenses --from=mixed --order=license
```

Run this before each release, and whenever you add a dependency.
