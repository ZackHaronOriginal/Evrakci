# Findings: filtering (R5c-1, 2026-11-19)

Research for ideas only. Nothing here is a decision. No code or text was copied. Every claim links to a page opened with WebFetch on 2026-11-19 (fetch tool returns summaries, so wording is paraphrased).

What we do today: one filter kind, "every N pages is one document", applied to the selected pages (K-10, K-21 to K-30). No remove-filter command (K-28). No content filter; ideas 1 to 7 in `docs/ui-goal/feature-ideas.md` are unbuilt. Next-check jumps N / Shift+N and U exist (K-65, K-66). "Filter" here also covers narrowing a list of pages or documents to those needing attention.

## Source read

- ScanTailor Advanced (GPL-3.0, read only): https://github.com/4lex4/scantailor-advanced . A deviation provider scores each page against the project; the page list can be sorted by deviation, highest first; an option marks high-deviation thumbnails with red asterisks; results are cached and recalculated on demand, not saved in the project file. Only the README was read, not the C++ source.
- Paperless-ngx usage docs: https://github.com/paperless-ngx/paperless-ngx/blob/dev/docs/usage.md (documentation, not source).

## Comparison

| Practice | Who does it (links) | What we do (ID) | Gap | Cost to us | Perf cost | Risk |
|---|---|---|---|---|---|---|
| Sort or flag pages by how much they differ from the rest, so problem pages surface first | ScanTailor Advanced deviation sort and red-asterisk option (https://github.com/4lex4/scantailor-advanced) | Per-document check rider and N / Shift+N jump (K-54, K-65); no per-page score | Odd pages inside a document (wrong size, sideways) are not surfaced | M (needs per-page size and orientation; analysis already renders each page) | Cheap if computed at import; the README says ScanTailor caches and recomputes on demand | Must use icon plus word, not asterisk or colour alone (K-13 rule) |
| Combine several criteria in one filter | Paperless-ngx combines tags, correspondents, document types (https://github.com/paperless-ngx/paperless-ngx/blob/dev/docs/usage.md) | One criterion, N pages (K-21) | Cannot say "blank pages in this batch" | M | none | Dialog gets heavier; PRODUCT.md calm rule |
| Saved views that update as new items arrive | Paperless saved views (https://github.com/paperless-ngx/paperless-ngx/blob/dev/docs/usage.md) | Last N only, session only (K-26) | Same filter recurs per job kind (feature-ideas item 7) | M | none | Stored with a template, not hard-coded (user defines content) |
| Filter categories in plain language, predictable values | Nielsen Norman Group on filter categories (https://www.nngroup.com/articles/filter-categories-values/); the page does not cover counts, applied-filter display or reset | Dialog text is Turkish plain language (K-21) | Not a gap on wording; counts and reset are not covered by this source (see Unverified) | S | none | none |
| Show what is selected after the filter ("N pages matched") | Not found in a source opened by this agent | Selection card counts (K-37, K-101) | Needs evidence before proposing | S | none | n/a |
| Document status list: green done, red needs action | Tungsten Transact Validate (https://ephesoft.com/docs/?p=47801); the page does not describe filtering or sorting that list | Overview strip segments, rider, İncelendi (K-54, K-60) | Cannot list only unreviewed documents; U jumps one by one (K-66) | M (a list or dimmer in the overview) | none | Duplicates the overview |
| Remove an applied filter | Not found in any source read | None (K-28) | Internal gap: Geri al is the only way | S (core method plus Kontrol command) | none | Low |

## Ideas for the owner's ranking

1. Per-page "looks different" marks (size, orientation) with a jump command, in icon plus word. Problem: odd pages hidden in a 400-page job. Gains: reviewers on mixed piles. Evidence: ScanTailor deviation sort and marks (https://github.com/4lex4/scantailor-advanced). Effort M. Overlaps feature-ideas items 3 and 4.
2. "Remove filter" command in Kontrol. Problem: K-28. Gains: anyone who set the wrong N. Evidence: internal (K-28, O-02), no external source. Effort S.
3. Saved filter attached to a template. Problem: repetitive setup per job kind. Evidence: Paperless saved views (https://github.com/paperless-ngx/paperless-ngx/blob/dev/docs/usage.md). Effort M.

## Unverified

- Result counts, visible applied filters, clear-all and zero-result handling: the NN/g page opened does not cover them (https://www.nngroup.com/articles/filter-categories-values/).
- Whether Transact lets operators filter the documents list (page opened does not say; https://ephesoft.com/docs/?p=47801).
- Paperless "select all of filtered results" behaviour (not covered by the usage page).
- ScanTailor source (C++) not read; only the README.
