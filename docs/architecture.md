# Architecture

## Deployment model

Evrakçı is a **desktop application** installed on the chamber's own computers (Windows first).
No document data leaves the machine. This is the main KVKK (Turkish data protection law)
argument and a core product promise.

## Components

| Part | Tech | Role |
|---|---|---|
| UI | PySide6 (Qt for Python, LGPL) | Yükle, Kontrol (thumbnails + split editor), Dışa Aktar, Rehber |
| Pipeline | Pure Python, no Qt imports | Split, OCR, classify, extract, export |
| PDF ops | pikepdf, pypdfium2 | Split, merge, render thumbnails, detect blank/QR separators |
| OCR | OCRmyPDF + Tesseract (`tur`) | Searchable text layer |
| Classification | Keyword/regex rules (later: optional local ML) | makbuz / fatura / e-arşiv / other |
| Extraction | Regex per document type | Date, amount (TL), company, sicil no, VKN/TCKN, ETTN |
| Storage | Local folder + SQLite | Jobs, pages, labels, audit log |
| Packaging | PyInstaller (folder build) + Windows installer | Qt stays dynamically linked (LGPL) |

The pipeline does not depend on Qt, so the same code can later power a command-line tool or a
hosted version.

Long-running work (OCR) runs in a background worker thread (`QThreadPool`), so the window never freezes.

## Processing flow

1. **Ingest.** Copy the selected PDF into the job folder, `<data>/jobs/<id>/original.pdf`.
2. **Split.** Find separator pages (near-blank page, or a page with an `EVRAKCI-AYIRAC` QR code)
   and propose document boundaries.
3. **OCR.** Add a Turkish text layer to each page.
4. **Classify and extract.** Run rule sets per document type. Each field stores its confidence.
5. **Kontrol.** Staff move boundaries, change types and edit fields.
6. **Dışa Aktar.** Write renamed PDFs (`YYYY-MM-DD_tur_firma.pdf`) and `index.xlsx` to a folder the user picks.

## Multi-chamber design

- Chamber-specific settings (name, logo, naming pattern, custom document types) live in a
  config file, not in code.
- Document-type rules are data (YAML), so a chamber can add its own types without forking.

## Data handling

- Job data lives in the user's app-data folder, never inside the repository.
- Configurable retention: delete job files after export or after N days.
- Tests and demos use synthetic documents only.
