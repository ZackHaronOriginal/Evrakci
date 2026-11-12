# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

(Evrakçı is a Windows desktop app built with PySide6/Qt, not a website. Design work is mocked up
in HTML for approval, then built as a Qt window. None of the iOS/Android conventions apply.)

## Users

- **Primary:** non-technical office staff at Turkish chambers of commerce and commodity exchanges.
- **How they use it:** they work through piles of 100–800 scanned pages in **long sessions**
  (an hour or more). They check splits, fix read values and export.
- **Setup:** the same staff, or one colleague, set up templates once per document kind.
- **Confirmed by the owner:** office staff in long sessions is the main use.

## Product Purpose

- **What it does:** turns a big pile of paper into one correctly split, searchable, well-named PDF
  per document, with as little paper handling as possible.
- **How:** staff unstaple once and feed the copier in batches. The computer does the splitting
  (QR separator pages and page-range filters), OCR, naming from user-made templates, and export.
- **Success:** clearly faster than scanning document by document, with no silently wrong output.
- **Bigger picture:** this is the first module of an all-round quality-of-life toolbox for
  paperwork.

## Positioning

Local-first and offline: documents never leave the building (KVKK). Fully configurable: the app
assumes nothing about what a document contains. Users name their own variables and draw where
they are, with variants from other examples of the same kind. Human in the loop: the software
suggests and staff confirm.

## Operating Context

- Ordinary Windows office PCs, often **older monitors** (around 1366×768 to 1920×1080), with
  ordinary office lighting.
- Scans come from office copiers' document feeders, in batches of a few dozen sheets.
- Work is repetitive and **keyboard-heavy**: checking hundreds of documents and values in one
  sitting.
- Turkish-language UI. Staff know the copier and Windows, and nothing about OCR or programming.

## Capabilities and Constraints

- **Window tabs:**
  - Yükle (jobs and batches)
  - Kontrol (the timeline editor: select pages, apply filters and templates; QR, filter and manual
    cuts look different; undo/redo; 800+ pages)
  - Şablonlar (template creator)
  - Değerler (review table)
  - Dışa Aktar (export)
  - Rehber (scanning guide)
- **Same core as the CLI:** the window calls exactly the same functions as the `evrakci` command
  line, which already works end to end.
- **Terminology:** belge (document), sayfa (page), kesim (cut), QR ayıraç (separator), filtre,
  şablon (template), değişken (variable), bölüm/varyant (section/variant), kontrol (needs check),
  dışa aktar (export).
- **Undecided / later:** configurable looks (themes) are planned for later; the first version
  ships one look.

## Brand Commitments

- Evrakçı is **its own neutral tool**, open source and used by many chambers. No chamber branding
  inside the app for now.
- The owner plans to make the look configurable later, so colours and type should come from
  tokens, not hard-coded values.

## Evidence on Hand

- **Real documents:** none in the repo, and none may ever be committed. Mockups use only invented
  data.
- **Existing artefacts:** the approved design spec
  (`docs/superpowers/specs/2026-11-06-scan-and-split-design.md`) and the first mockups
  (`docs/superpowers/mockups/plan-5-window.html`, which are to be replaced).

## Product Principles

1. **Never silent.** Every unsure value, missing field or odd split is visible where the user
   works, and in `index.xlsx`.
2. **The user decides what documents contain.** There are no built-in fields or document kinds.
3. **Less paper handling, not more.** The screen does the work the hands used to do.
4. **Calm for long sessions.** The screen stays dense but readable, and fast to drive with the
   keyboard.

## Accessibility & Inclusion

- Larger, very readable text and generous controls: some users have weaker eyesight.
- Works well on older 1366×768 to 1920×1080 monitors.
- Every frequent action is reachable by keyboard, with visible focus and shortcuts.
- Meets WCAG AA contrast. Meaning is never carried by colour alone: cut types also differ in
  shape or icon.
