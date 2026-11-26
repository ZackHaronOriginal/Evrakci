# Review: group D (Dışa Aktar: B-003, I-35, I-40, I-39, I-38)

Range `6afc1e5..HEAD`, group D files only. Cross-step review (Opus). Severity as in `bugs.md`.
No S1 or S2 found. Checked and agreeing: Kontrol count is `item.checks` everywhere (list,
card, `needing_check`, both sheets, CLI line, `may_delete_after_export`); PDF/A stays Bilgi
(`pdfa_note`) with "hayır" in the column; sheet order Belgeler, Kontrol gerekenler, Özet;
every new cell goes through `_set_text`; one `exported_at` for sheet and `job.last_export`;
the window flushes the saver before the export copy; a job deleted after export is not saved
back; format stays 2 and damaged `last_export` reads as None; `_name_change` and the UI
`FORBIDDEN` copy are gone; contract and `shortcuts.md` match the registry (both new actions
are in a menu and the palette).

| ID | Sev | File:line | Finding | Suggested fix | Action |
|---|---|---|---|---|---|
| R-D-1 | S3 | src/evrakci/ui/disa_aktar.py:1418 | A failed print preview build shows the toast "Dışa aktarma tamamlanamadı". Nothing was exported, so the message is wrong. | Use a print-specific text. None is approved yet, so add a row to the I-38 table (owner) and keep the old text until then. | ledger |
| R-D-2 | S3 | src/evrakci/ui/disa_aktar.py:1369-1371, disa_aktar_print.py:37 | The subtitle says "Dışa aktarıldı: <zaman>" whenever `job.last_export` is set, also after the job was edited and the list is a new plan. The paper then looks like a record of files that differ from it. (C5 wants the record line to survive a restart, so this is a gap in the spec.) | Say the record line only in the written state, or when the list still equals the last export (for example a stored count or name hash). Otherwise print the plan line. Owner decides. | ledger |
| R-D-3 | S3 | src/evrakci/pipeline/exporting.py:139-148 | A text-layer failure writes all PDFs and index.xlsx (with Özet "Dışa aktarma zamanı") but never sets `job.last_export`. Window and CLI agree, but the print still says "henüz yazılmadı" although the files are on disk. | Set `last_export` before raising when `_write_index_quietly` succeeded, and add a test. | ledger |
| R-D-4 | S3 | src/evrakci/ui/disa_aktar_print.py:243-252 | "Yazdır…" paints every page for the real printer on the window thread (HighResolution, up to 800 rows). B-096 only ledgers the preview block. | Measure it and extend B-096, or paint in the same deferred step as the preview. | ledger |
| R-D-5 | S4 | src/evrakci/pipeline/exporting.py:62-64 | The fallback `belge_NNN` (a required value cut by the folder path) keeps an earlier `name_note` from `plan_export` ("Geçersiz karakter silindi" or a clash). The copy list, "Adı değişenler" and CLI `[ad: …]` then give the wrong reason. | Set `item.name_note = ""` next to the fallback name, and add a core test. | fix now |
| R-D-6 | S4 | src/evrakci/ui/disa_aktar.py:993, tests/ui/test_disa_aktar.py:715 | The copy list is in list order (Kontrol rows first). `--onizle` is in document order. The equality test compares `sorted()` lines, so the order difference never shows. | Sort `list_text` by `row.number`, or note the order in the contract. Then compare the lines without `sorted`. | fix now |
| R-D-7 | S4 | src/evrakci/cli/jobs.py:791 | The `--onizle` help reuses the window toggle label "Adları karşılaştır". As CLI help it does not say "dry run, writes nothing". | Add a help text to the I-39 table (owner), or keep it as is. | ledger |
| R-D-8 | S4 | src/evrakci/pipeline/naming.py:147, export.py:65-100 | A name cut to the 120-character limit gets the check "dosya adı kısaltıldı" but no `name_note`. It is missing from "Adı değişenler" and the copy list, although the name differs from the pattern (C1). | Set a note there too. The 120-limit note has no approved text, so ledger it. | ledger |
| R-D-9 | S4 | src/evrakci/pipeline/index.py:17-26 | C1 gives the reason for `name_note` as "the same text in window, CLI and sheet". index.xlsx has no Kaynak or name-note column, so clash and removed-character notes appear only in the window and the CLI. | A spec gap (I-35 lists no such column). Owner decides whether the sheet gets one. | ledger |
| R-D-10 | S4 | src/evrakci/pipeline/exporting.py:66, export.py:25 | One sentence is kept as two literals: the check "dosya adı kısaltıldı (klasör yolu uzun)" and `NOTE_SHORTENED`, with different case. | Derive the check from one constant (`NOTE_SHORTENED.lower()` or the reverse). | fix now |
| R-D-11 | S4 | src/evrakci/pipeline/job.py:59-66 | `LastExport.folder`, `documents` and `needing_check` are written but never read. The CLI stores `--cikti` as given, which can be a relative path. | Store `out_dir.resolve()`, or keep the fields documented as record only. | ledger |
| R-D-12 | S4 | src/evrakci/ui/disa_aktar.py:823-835 | A folder change that is not typed can call `_sync()` twice (in `_replan_folder` and after it). `_typing` is a dynamic attribute that is never set in `__init__`. | Return after `_replan_folder()`, and set `self._typing = False` in `__init__`. | fix now |

Counts: S1 0, S2 0, S3 4, S4 8.

Suite (`QT_QPA_PLATFORM=offscreen python -X faulthandler -m pytest -q -p no:cacheprovider tests`):
2854 passed, 4 skipped, 205 xfailed, 1 warning (DeprecationWarning, QDragEnterEvent) in 657 s, exit 0. `ruff check src tests tools`: All checks passed.
