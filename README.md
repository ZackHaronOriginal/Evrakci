# Evrakçı

**English** | [Türkçe](README.tr.md)

[![CI](https://github.com/ZackHaronOriginal/Evrakci/actions/workflows/ci.yml/badge.svg)](https://github.com/ZackHaronOriginal/Evrakci/actions/workflows/ci.yml)

**An open-source, all-round quality-of-life toolbox for paperwork at chambers of commerce.**
The first module, *Tara ve Ayır* (scan and split), turns a big scanned pile into split,
searchable PDFs, one per document, named from values read off the page. Documents never
leave the building.

Built for any chamber of commerce or commodity exchange, and configurable for anyone else:
the app decides nothing about what your documents contain.

## Status

🚧 Early development. Not ready for production use yet.

## How it works

```
Pile of paper ──► unstaple once ──► feed through the copier in batches ──► scanned PDFs
                                                                              │
   1. Job          combine the batches, in order  ◄──────────────────────────┘
   2. Split        QR separator pages + filters on selected pages ("every N pages")
   3. Timeline     see every page, fix cuts, rotate or delete pages
   4. OCR          Turkish text layer, searchable PDFs
   5. Templates    your own variables, e.g. {Firma_Unvani}, drawn on example documents
   6. Review       check and fix the values read
   7. Export       one PDF per document, named from your variables, plus an Excel index
```

Steps 1–3 work today from the command line (see below). The rest is being built.
Design: [docs/superpowers/specs/2026-11-06-scan-and-split-design.md](docs/superpowers/specs/2026-11-06-scan-and-split-design.md)

## Principles

- **Local-first.** A desktop app (Windows first, Linux and macOS too) running on the chamber's own computers. No cloud OCR, no uploads to third parties.
- **Human in the loop.** The software suggests and staff confirm. OCR will make mistakes, and the review screen is where they get caught.
- **Turkish-first.** The UI, command line and guide are in Turkish.
- **Configurable, not hardcoded.** Users create their own templates and variables. Nothing about
  any specific document is built into the code.
- **CLI first.** Everything works from the `evrakci` command line. The window is a second entry
  point over the same core.
- **Easy install.** A normal Windows installer for staff. No Python knowledge needed.

## Repository layout

```
src/evrakci/pipeline/   Core processing (no Qt): jobs, page analysis, cuts, writing PDFs
src/evrakci/cli/        The `evrakci` command line
src/evrakci/ui/         PySide6 (Qt) window (`evrakci-arayuz`)
tests/                  Automated tests
docs/                   Architecture, licensing, Turkish scanning guide
samples/synthetic/      SYNTHETIC test documents only (see below)
```

## ⚠️ Never commit real documents

This repository is public. **Do not commit real documents or anything containing
member data**, not even "just for testing". Use synthetic documents in `samples/synthetic/`.
Real scans belong in `data/`, which is git-ignored.

## Development

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
ruff check . && pytest
```

`evrakci` runs the command line. `evrakci-arayuz` opens the window.

### Command line (komut satırı)

```bash
evrakci ayirac ayirac.pdf --adet 10                 # print QR separator sheets
evrakci is olustur "Seçim 2026" tarama1.pdf tarama2.pdf   # prints the job id
evrakci is filtre <id> 1-40 2                       # pages 1-40: every 2 pages is a document
evrakci is kes <id> 57                              # extra cut before page 57
evrakci is goster <id>                              # list the documents
evrakci is disa-aktar <id> --cikti cikti            # one PDF per document
```

Page numbers always match the order of the scanned pile. `evrakci --help` and
`evrakci is --help` list every command.

System dependencies for OCR (later steps): Tesseract with the Turkish language pack (`tur`).

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md). All contributors
sign a short [Contributor License Agreement](CLA.md) on their first pull request.

## License

[AGPL-3.0-or-later](LICENSE). Free for any chamber to use and modify. Anyone who distributes the
app, or runs a modified version as a service for others, must share their source code. Commercial
licenses, support and hosting are available from the maintainer. See [docs/licensing.md](docs/licensing.md).
