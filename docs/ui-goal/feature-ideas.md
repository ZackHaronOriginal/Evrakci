# Feature ideas

These are ideas, not decisions. Nothing here is approved, scheduled or promised. The owner picks;
a picked idea gets a one-page spec (see `.claude/skills/feature-planning/SKILL.md`) before any code.
Status values: `idea`, `specced`, `approved`, `rejected`, `shipped`. Everything below is `idea`.

Written against PRODUCT.md (never silent, user defines document content, less paper handling,
calm keyboard-heavy sessions) and the current registry (`src/evrakci/ui/actions.py`). Key
suggestions are only suggestions and still need a check against free keys with the
`shortcut-audit` skill. Turkish labels are drafts.

## More Kontrol filters (select pages by a property, then act on the selection)

Today Kontrol has "Filtre uygula…" (every N pages) and selection by click, Shift, Ctrl, rubber
band, Ctrl+A. The ideas below add "Sayfaları seç" filters that select matching pages, so
staff can then cut, delete, rotate or apply a template to all of them at once. Each one must show
how many pages matched and never act silently.

| # | Idea | Problem it addresses | Notes and open questions | Status |
|---|---|---|---|---|
| 1 | Select by QR content or pattern | Separator pages may carry text or numbers (a box number, a kind); staff want to jump to or cut at "all QR starting with KAP-" | Needs the decoded QR text kept per page (analysis already finds QR via zxing); a text box with wildcard or regex; how to show non-separator QR codes | idea |
| 2 | Select blank pages | Blank backs of double-sided sheets stay in the job unless dropped; the drop-empty option is all-or-nothing | Reuse the ink ratio from `pipeline/analyze.py`; a threshold slider with live count; preview of the borderline ones; never delete without the usual undoable Del | idea |
| 3 | Select by page size | A pile mixes A4 and A3 or odd-size inserts (receipts, envelopes) that belong to a different document | Page size per page is in the PDF; tolerance in mm; label in Turkish paper names | idea |
| 4 | Select by orientation | Sideways pages (landscape inside a portrait pile) need rotating, or start a new document | Combine with the rotate command (R); maybe also "probably upside down" if the OCR knows | idea |
| 5 | Select pages where OCR found a text | "Which pages contain 'Kapasite Raporu'?" to place cuts without a QR separator | Needs OCR text per page available before Değerler; cost on 800 pages; offline engines only; search box with Turkish case folding (see `actions.fold`) | idea |
| 6 | Select low-confidence pages / values | Staff want to go straight to what the machine is unsure of, per page, not per document | Related to N / Shift+N (Sonraki kontrol); a list of reasons with counts; must not create a second competing "Kontrol" colour | idea |
| 7 | Saved filter as a chip row | The same filter is used on every job of a kind | A filter is stored with the template, not hard-coded; careful with "the user decides what documents contain" | idea |

## Quality of life

| # | Idea | Problem it addresses | Notes and open questions | Status |
|---|---|---|---|---|
| 8 | Review progress and "resume where I stopped" | After an hour, staff lose their place; closing the job forgets the current document | Store last reviewed document in the job; open Kontrol at the first İncelenmedi (U already exists) | idea |
| 9 | Compare the split with last time | A new batch of the same kind usually has a similar page count per document; outliers are likely wrong cuts | A quiet Kontrol hint ("3 belge 1 sayfa; çoğu 4") with icon + word; no auto action | idea |
| 10 | Two-page spread / side-by-side view in the loupe | Checking that a cut is right means seeing the last page of one document and the first of the next | Loupe (Space) with an optional neighbour; arrows already page through | idea |
| 11 | Bulk rename preview in Dışa Aktar | Wrong file names are found only after export | A table of old name, new name, conflict flag before export; copy to clipboard | idea |
| 12 | Export a "problems only" report | A supervisor wants the list of kontrol items without opening the app | Sheet in `index.xlsx` or a separate small file; same data as the app, never silent | idea |
| 13 | Sound or taskbar flash on finished long work | Staff leave the PC during reading or export | Taskbar progress exists (top25 item 19); sound was deferred (item 25); settings switch, off by default | idea |
| 14 | Keyboard "jump to document N" with live preview | Ctrl+G exists; showing the target before Enter would avoid wrong jumps | Part of the Ctrl+G dialog in Kontrol | idea |
| 15 | Template suggestion per document | Applying the right template to each document by hand is repetitive | Suggest from the pages' OCR text or QR kind; human confirms (Positioning: "software suggests, staff confirm") | idea |

## Using the office's own data (owner idea, 2026-11-19)

| # | Idea | Problem it addresses | Notes and open questions | Status |
|---|---|---|---|---|
| 16 | Pre-filled forms from imported Excel data (ideas-ranking I-48) | Blank forms are handed out and missing fields are typed in later from data the office already holds | Import several sheets, detect header rows, map columns to user-named variables (nothing hard-coded), merge records of the same company across sheets with a visible match score, preview, print or export one filled form per record; KVKK: data never leaves the PC, imports can be deleted; how forms are designed (reuse templates or a new layout editor) is open | idea |
| 17 | Look up read values in the imported data (ideas-ranking I-49) | Unsure or missing values are re-typed although the office has them | Suggestion beside the read value, never an automatic overwrite; show which import and date it came from | idea |

## Not in scope here

First-run tour (deferred in `docs/ui-goal/top25.md` item 25), cloud sync or any network feature
(violates local-first), and per-chamber branding (PRODUCT.md "Brand Commitments").
