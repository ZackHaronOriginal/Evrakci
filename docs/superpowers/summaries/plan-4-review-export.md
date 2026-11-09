# Plan 4 summary: review and export

- **Works:** list and fix values; export one named PDF per document (Windows-forbidden characters
  removed, Turkish letters kept, clashes numbered); a missing or cut required value is never
  silent (numbered name plus `[kontrol]` reason); `index.xlsx` with file, pages, source pages,
  template, one column per variable and check reasons; retention setting.
- **CLI:** `evrakci is degerler`, `evrakci is deger`, `evrakci is disa-aktar`, `evrakci ayar`.
- **Decisions:** export runs through one core function (`pipeline/exporting.export_job`) shared
  by the CLI and the window; "delete after export" only after files and index are written.
- **Reviews:** `ab312cb`; fresh review 2026-11-08 → `1a4fc56` (8 new tests).
- **Second fresh review (2026-11-09, report in the session):** 18 findings, all fixed in `edaac39`
  (`tests/test_export_review2.py`, 40 tests): forbidden pattern text, device names with a
  dot, cut names marked (optional values give way), `--kontrol` shows export's own marks, job
  ids from folder names, settings files checked, `is deger --geri-al`, case-insensitive
  earlier-export check, delete-after-export only with the text layer. Kept as the spec says:
  forbidden characters are removed, not replaced (`2024/15` → `202415`).
