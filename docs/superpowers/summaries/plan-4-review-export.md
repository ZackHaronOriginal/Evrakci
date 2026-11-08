# Plan 4 summary: review and export

- **Works:** list and fix values; export one named PDF per document (Windows-forbidden characters
  removed, Turkish letters kept, clashes numbered); a missing or cut required value is never
  silent (numbered name plus `[kontrol]` reason); `index.xlsx` with file, pages, source pages,
  template, one column per variable and check reasons; retention setting.
- **CLI:** `evrakci is degerler`, `evrakci is deger`, `evrakci is disa-aktar`, `evrakci ayar`.
- **Decisions:** export runs through one core function (`pipeline/exporting.export_job`) shared
  by the CLI and the window; "delete after export" only after files and index are written.
- **Reviews:** `ab312cb`; fresh review 2026-11-08 → `1a4fc56` (8 new tests).
