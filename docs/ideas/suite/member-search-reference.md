# Member Search / Bilgi Formu filler: reference

What the standalone tool in `reference/member-search.html` does, how the notable parts work, and which decisions the owner already made. Function names refer to the script inside that file. The tool and `reference/` are in the private folder `.claude/ideas-private/suite-2026-11-27/` (see `README.md`); they are not in the repository.

**Status: reference for an idea, not decided.**

## Why it exists

The owner works with a trade chamber's member data. The chamber has to fill an "EK-1 Bilgi Formu" (an information form) for each person: name, company, NACE code, addresses, phones, TC kimlik number, education, chamber role and so on. The data for it sits in an Excel workbook spread over two sheets that describe the same companies and people differently, and some of it only exists on paper documents.

Doing this by hand means finding the person in two sheets, copying values into the form one by one, and repeating that for well over a hundred people. The tool was built to do the lookup and the filling automatically, let the owner correct or complete what the data doesn't have, and print or export the finished forms.

## How it grew

1. Search a member workbook and show each person's data.
2. Render the EK-1 form on screen, filled, and print it.
3. Download as Excel (first a plain table).
4. Fill the owner's real EK-1 workbook as the Excel output, as one multi-sheet file or one file per person.
5. Always-on auto-save, a hideable filter panel, and an "Edit forms" mode to go through people one by one.
6. Import of an already-filled multi-sheet EK-1 workbook as an overwriter, and a tag showing where each phone number came from.
7. Left-aligned answers and black text in the export.

## About the data

The tool was built and tested only with synthetic data from its own sample generator. The real member workbook and the real filled forms were never shared with the session that built it, which is why nothing real is in this folder. `reference/sample-member-workbook.synthetic.xlsx` reproduces the two sheets and their headers with made-up people and companies.

## What it is

One self-contained HTML file (about 1 MB) that runs offline in a browser. It bundles the SheetJS library inline and a strict Content-Security-Policy blocks all network access, so no data can leave the machine. It was built for a trade chamber's member data.

Flow: load a member workbook → search and filter people → see each person's data mapped onto the EK-1 "Bilgi Formu" → correct values → print or export.

## Data in

- **Sources:** Excel/CSV files (drop or file picker) and pasted tables. Each sheet becomes a table (`addTable`).
- **Two known sheets:** `Veriler` (member list: member/trade registry numbers, profession group, role, status, phone) and `Sayfa1` (company list: authorised person, NACE code, address, mobile, e-mail, TC). Other sheets are accepted too.
- **Header recognition:** the header row is found by scoring rows for known keywords (`headerScore`), then each header is mapped to a canonical field by fuzzy rules on the folded (lower-cased, de-accented Turkish) text (`CANON`, `mapHeaders`). Canonical fields: naceKod, naceAd, uyeSicil, ticSicil, sira, meslek, asil, gorev, yetkili, unvan, belge, cep, telefon, email, adres, durum, tc, egitim. This is the seed of the "read its headers" idea: it is currently hard-coded for one domain.
- **Record building:** rows are grouped into one record per person per company (`rebuild`), keyed by a normalised company name (`companyKey`, which strips legal suffixes) plus the folded person name. Rows from both sheets that describe the same person are linked. People at the same company are grouped.

## Search and filter

Free-text search with scoring across all fields, a scope switch (all / in both sheets / one sheet only), and facet filters with "is / is not" (document present, profession group, role, principal/alternate, status, NACE activity). The filter panel can be hidden.

## The form

- **Layout as data:** the EK-1 sheet was converted once into a JSON description (`FORM_LAYOUT`: column widths, row heights, merged cells, cell text and fonts, drawn shapes). `sheetHTML` renders it as an HTML table that looks like the paper form. This "layout as data" idea is the part most relevant to a template library.
- **Field mapping:** `FORM_FILL` maps form cells to data fields: C2 oda, C4 ad, C5 soyad, C27 unvan, C28 nace, C29 adres, C30 telefon, C31 evadres, C32 cep, C33 email, C37 tc, C38 cins, C39 baba, C40 anne, C41 dogum.
- **Editable boxes:** `FORM_EDIT` lists every answer cell; each can be typed into directly on the form. Education boxes (`FORM_TICKS`: C7…O7) and the drawn boxes (delegate yes/no, chamber role) toggle an X on click. Drawn answer boxes (countries, sectors) take text.
- **Three views per person:** Fields (labelled tiles with copy buttons and in-place correction), Form (the rendered sheet), All columns (raw source rows).
- **Edit forms mode:** the form opened large with Previous/Next and a counter, walking through the current results or the selection. Page Up / Page Down also move.

## Phone rules (agreed with the owner)

Implemented in `pickPhones`. Cells often hold several numbers, each followed by a name in brackets.

- **Mobile (cep):** 1) a mobile in the company's Sayfa1 rows tagged with this person's name; 2) an untagged mobile on the person's own Sayfa1 row; 3) the first mobile on their own Sayfa1 row unless tagged with a colleague's name; 4) the same steps on Veriler.
- **Work phone:** the first company line (area code 2xx/3xx/4xx, 850, 444, or a 7-digit local number), Sayfa1 before Veriler. A mobile is never used as the work phone.
- The source of each number is shown as a tag ("Cep: Sayfa1") and in the field label.

## Output

- **Print / PDF:** one person, the selection, or all results; the browser's "Save as PDF" gives PDF.
- **Excel, filled template** (`template`, `formFill`, `filledSheet`, `filledDrawing`, `workbookParts`): the owner's original EK-1 workbook is embedded in the page. Export unzips it and writes values straight into the sheet XML and drawing XML, then zips it again. Nothing is rebuilt, so borders, merges, shapes and print settings stay exactly as in the template. Three modes:
  - one workbook, one sheet per person, sheet names with given names shortened: "A. N. Yılmaz" (duplicates get "(2)", 31-character limit respected);
  - one workbook per person, delivered together as a .zip;
  - a plain table, one row per person.
- **Details that mattered:** answers are left-aligned with shrink-to-fit; answers are forced to black because the template formats some boxes with a red font; phone and TC values are written as text so digits are not lost; only the first sheet is marked selected so Excel does not open in group-edit mode.
- A minimal zip writer (`zipBytes`) is included because the bundled library mangles non-ASCII file names.

## Import of filled forms

`importForms` reads a workbook of filled EK-1 sheets (one sheet per person, tab names like "A.F.Güney") and overwrites the matching people's data.

- A sheet is recognised by the "BİLGİ FORMU" title; empty sheets are skipped.
- People are matched by the name written on the form, with the company name breaking ties; if the name boxes are empty, by the tab name when it points to exactly one person.
- X marks are detected three ways: typed in the box, typed in a nearby cell, or drawn over the box as a separate shape (matched by position).
- People not present in the data are added as new records.
- Tested only on files produced by the tool itself and then altered, not on the owner's real filled workbook.

## Saving

- Always on. Imported data, corrections, typed form text and X marks are written to IndexedDB as the owner works, with a "Saved" indicator (`saveNow`, `saveEdits`, `restore`).
- Manual backup to a JSON file and restore from it, plus "Clear all data".
- Storage is per browser, per computer.

## Decisions already made by the owner

- Sayfa1 is the preferred source for phones; Veriler is the fallback.
- Sheet names shorten first and middle names: "A. N. Yılmaz".
- Auto-save is always on.
- The filled workbook acts as an overwriter.
- Text in answer boxes is left-aligned everywhere.
- OCR is out of scope for this tool.

## Known limits

- Header mapping, the form layout and the field mapping are hard-coded for this one workbook and this one form.
- All testing used synthetic data generated by the tool's "sample data" button.
- X marks ticked on the form are not included in the plain-table export.
- Data lives in one browser; there is no sharing between computers other than the backup file.

## What could generalise to a suite (ideas, not a plan)

| In the standalone tool | Generalised form |
|---|---|
| `CANON` header rules | User-defined or predefined column mappings per data source |
| `FORM_LAYOUT` + `FORM_FILL` | A template = a layout (size, boxes) plus a field mapping |
| Embedded EK-1 workbook filled in place | "Bring your own Excel file as the template" |
| Print one / selection / all | Batch printing of any template, including several labels per sheet |
| Per-person overrides | Per-record edits that survive re-import of the source data |
| IndexedDB auto-save + backup file | The suite's storage layer |
