# Plan 3 summary: templates

- **Works:** user-named variables, sections drawn on example documents, variants tried in the
  user's order (first confident wins, otherwise flagged with every reading kept), required
  variables, file-name pattern, apply to selected pages; last-applied template wins; mixed
  documents flagged.
- **CLI:** `evrakci sablon olustur|listele|goster|sil|degisken-ekle|degisken-sil|
  degisken-adlandir|zorunlu|bolum-ekle|bolum-sil|bolum-tasi|dosya-adi|esik|disa-aktar|ice-aktar|
  test`, `evrakci is sablon-uygula`, `evrakci is oku`.
- **Decisions:** values keyed by a permanent variable key (renaming never loses values); imported
  ids are regenerated; template ids are hex only.
- **Reviews:** `19913bd`; fresh review 2026-11-08 → `924211e` (13 new tests).
- **Second fresh review (2026-11-09, report in the session):** 14 findings plus test gaps, all
  fixed in `3636dae` (`tests/test_templates_review2.py`, 39 tests): the file name is the
  template id, a failed re-read keeps corrections, values carry the template revision
  (`is oku --sadece-eksik` re-reads changed ones), strict types in template files,
  `is sablon-kaldir`, thin and top-left boxes, damaged pages recorded.
