# Dependency licenses

Evrakçı is AGPL-3.0-or-later. The maintainer may also offer it under commercial terms
(see [CLA.md](../CLA.md)). **Every dependency must allow both uses.** The safe choices are
permissive licenses (MIT, BSD, Apache-2.0), weak copyleft (MPL-2.0, LGPL) used as a separate
library, and tools run as separate programs.

| Dependency | License | How we use it | OK for commercial/closed builds? |
|---|---|---|---|
| PySide6 / Qt | LGPL-3.0 | Dynamically linked Python package | ✅ If users can replace the Qt libraries. Ship a folder build, not a single static binary, and include the LGPL text plus the source location |
| pikepdf | MPL-2.0 | Library | ✅ Changes to pikepdf's own files must be shared |
| pypdfium2 / PDFium | Apache-2.0 / BSD-3 | Library | ✅ |
| openpyxl | MIT | Library | ✅ |
| Pillow | HPND | Library | ✅ |
| segno | BSD-3-Clause | Library (QR generation) | ✅ |
| zxing-cpp | Apache-2.0 | Library (QR reading) | ✅ |
| platformdirs | MIT | Library (app data folder) | ✅ |
| OCRmyPDF | MPL-2.0 | Library | ✅ |
| Tesseract + `tur` data | Apache-2.0 | External program | ✅ |
| Ghostscript | **AGPL-3.0** | **Not used.** OCRmyPDF 17.13+ makes PDF/A without it (`--pdfa-backend internal`) | Not bundled and never called |
| qpdf | Apache-2.0 | Via pikepdf | ✅ |

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
