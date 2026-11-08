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
