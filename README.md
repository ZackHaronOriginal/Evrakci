# Evrakçı

**English** | [Türkçe](README.tr.md)

[![CI](https://github.com/ZackHaronOriginal/Evrakci/actions/workflows/ci.yml/badge.svg)](https://github.com/ZackHaronOriginal/Evrakci/actions/workflows/ci.yml)

**Open-source desktop app for scanning and sorting chamber of commerce paperwork.**
Turn a stack of stapled paperwork (receipts/makbuz, invoices/fatura, member forms) into
split, searchable, correctly named PDFs plus an Excel index, without documents ever
leaving the building.

Designed to work for any chamber of commerce or commodity exchange.

## Status

🚧 Early development. Not ready for production use yet.

## How it works

```
Scanner/copier (ADF) ──► one big PDF ──► Yükle (Upload)
                                           │
                     ┌─────────────────────┘
                     ▼
   1. Split      at separator pages (blank sheet or QR separator)
   2. OCR        Turkish text layer (Tesseract `tur` via OCRmyPDF)
   3. Classify   makbuz / fatura / e-arşiv / other (keyword rules first)
   4. Extract    date, amount, company name, registry no (sicil no), tax no
   5. Kontrol    staff confirm or fix splits and labels in the app
   6. Dışa Aktar renamed PDFs + Excel index
```

## Principles

- **Local-first.** A desktop app (Windows first, Linux and macOS too) running on the chamber's own computers. No cloud OCR, no uploads to third parties.
- **Human in the loop.** The software suggests and staff confirm. OCR will make mistakes, and the review screen is where they get caught.
- **Turkish-first.** UI, guide and document rules are built for Turkish chamber paperwork.
- **Easy install.** A normal Windows installer for staff. No Python knowledge needed.

## Repository layout

```
src/evrakci/pipeline/   Processing (no Qt): split, OCR, classify, extract, export
src/evrakci/ui/         PySide6 (Qt) interface: Yükle, Kontrol, Dışa Aktar, Rehber
tests/                  Automated tests
docs/                   Architecture, licensing, Turkish scanning guide
samples/synthetic/      SYNTHETIC test documents only (see below)
```

## ⚠️ Never commit real documents

This repository is public. **Do not commit real receipts, invoices or any document containing
member data**, not even "just for testing". Use synthetic documents in `samples/synthetic/`.
Real scans belong in `data/`, which is git-ignored.

## Development

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
evrakci
```

System dependencies for OCR: Tesseract with the Turkish language pack (`tur`), Ghostscript, qpdf.

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md). All contributors
sign a short [Contributor License Agreement](CLA.md) on their first pull request.

## License

[AGPL-3.0-or-later](LICENSE). Free for any chamber to use and modify. Anyone who distributes the
app, or runs a modified version as a service for others, must share their source code. Commercial
licenses, support and hosting are available from the maintainer. See [docs/licensing.md](docs/licensing.md).
