# Findings: search (R5c-1, 2026-11-19)

Research for ideas only. Nothing here is a decision. No code or text copied. Every claim links to a page opened with WebFetch on 2026-11-19 (summaries, paraphrased).

What we do today: Ctrl+F is one command answered per tab (A-35): Yükle job name search (Y-48), Kontrol go-to dialog for document or page number (K-70, K-77), Şablonlar variable search, Değerler and Rehber search fields, Dışa Aktar file name. F3 / Shift+F3 only on Rehber (A-36). Ctrl+G go to (A-37). Command palette Ctrl+K with Turkish-aware folding (A-29, A-30), recent commands (A-33), shortcut sheet with search (A-34). No search of page content or text in Kontrol (K-77). Ideas 5 and 14 in `docs/ui-goal/feature-ideas.md` cover text search and go-to preview.

## Source read

No open-source search implementation was read in source for this area; the shortlist apps found here are documentation-level. Paperless-ngx usage page (documentation): https://github.com/paperless-ngx/paperless-ngx/blob/dev/docs/usage.md . VS Code command palette page: https://code.visualstudio.com/docs/getstarted/userinterface .

## Comparison

| Practice | Who does it (links) | What we do (ID) | Gap | Cost to us | Perf cost | Risk |
|---|---|---|---|---|---|---|
| Full-text search where every typed word must match, any order, accents ignored | Paperless-ngx basic search (https://github.com/paperless-ngx/paperless-ngx/blob/dev/docs/usage.md) | Palette search folds Turkish case and needs every word (A-30); no page-text search | Cannot find "the page that says X" in Kontrol | L (needs OCR text per page before Değerler; offline OCR cost on 800 pages) | High at import if done up front | Wrong hits shown as truth; must show matches as suggestions |
| Field prefixes and boolean operators | Paperless advanced query (same link) | None | Not needed for staff; advanced users only | L | Index build | Complexity against calm UI; probably not wanted |
| Search over barcodes stored with the document | Paperless can store barcode values and search them (https://github.com/paperless-ngx/paperless-ngx/blob/dev/docs/advanced_usage.md; usage page lists barcodes as searchable) | QR text is checked for the prefix and not stored (Y-26) | Cannot search "all pages with code KAP-1234" | M | none | Same as splitting idea 3 |
| One keyboard-first palette that does commands, go to file and go to line | VS Code: Ctrl+Shift+P commands, Ctrl+P files, Ctrl+G line (https://code.visualstudio.com/docs/getstarted/userinterface) | Ctrl+K palette for commands (A-29); Ctrl+G go to in Kontrol and Değerler (A-37) | Palette cannot go to a document or job by name | S to M (add "Belge N" and job names as palette entries) | small list | Low; keep disabled-reason bug in mind (A-31) |
| Type `?` in the palette to list what it can do | VS Code (same link) | Palette lists commands directly (A-29) | none | none | none | none |
| Find the same field in analogous documents | ABBYY Ctrl+Alt+F shows the image of the same field in other documents (https://docs.abbyy.com/flexi-capture/operator-work/field-verification-operator-work); the page has no find field or filter | Değerler has its own search field (A-38); no cross-document view of one field | Comparing one field across documents requires moving between documents | M to L | page crops | Overlaps region-reading and value-editing areas (R5c-2) |
| Recently used first | VS Code recent files via Ctrl+Tab (https://code.visualstudio.com/docs/getstarted/userinterface) | Palette recents, process memory only (A-33) | Recents lost on restart | S | none | none |
| Search hits stepped with next / previous | Our Rehber only (A-36); no external source found | F3 on Rehber only | Disabled elsewhere | n/a | n/a | n/a |
| Preview of the target before Enter | Not found in a source read | Planned in feature-ideas item 14 | n/a | S | none | n/a |

## Ideas for the owner's ranking

1. Put documents (and jobs) into the command palette as "go to" entries. Problem: moving to "Belge 37" needs Ctrl+G and a dialog. Gains: keyboard-heavy staff. Evidence: VS Code unifies commands, files and lines in one place (https://code.visualstudio.com/docs/getstarted/userinterface). Effort S to M.
2. Persist palette recents between runs. Problem: A-33 lost at restart. Evidence: VS Code recent-file behaviour (same link). Effort S.
3. Search on page text with matches shown as a suggestion list (long term, tied to OCR). Evidence: Paperless basic search (https://github.com/paperless-ngx/paperless-ngx/blob/dev/docs/usage.md). Effort L; also feature-ideas item 5.

## Unverified

- Search behaviour in ABBYY, Transact, NAPS2 beyond what is linked (pages did not describe it).
- Autocomplete in Paperless search (not described on the usage page).
- Paperless search performance and index design (docs only, no source read).
- Typed prefixes in the VS Code palette: the page opened says it does not describe them.
