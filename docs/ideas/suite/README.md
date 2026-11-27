# Evrakçı as a suite (owner idea log, 2026-11-27)

**Status of everything in this folder: idea, not decided.** Nothing here is planned, scheduled, specced or approved.
Do not plan or build any of it until the owner brings it up. The owner wants to talk through the templates and the
editing side when they do. Planned and built work lives in `docs/ui-goal/` and `specs/`; this folder is kept apart
from it on purpose.

## Where the material is

| What | Where | Committed? |
|---|---|---|
| This summary | `docs/ideas/suite/README.md` | yes |
| The ideas organised into parts, with questions for later | `docs/ideas/suite/ideas.md` | yes |
| How the standalone Member Search / Bilgi Formu tool works | `docs/ideas/suite/member-search-reference.md` | yes |
| The owner's own message, unchanged (the source of truth) | `.claude/ideas-private/suite-2026-11-27/01-my-words-verbatim.md` | no, private |
| The full handoff as received: prompt, original notes, the working tool (`member-search.html`), the blank EK-1 form template, synthetic sample workbooks, two screenshots | `.claude/ideas-private/suite-2026-11-27/` and the original zip at `.claude/ideas-private/evrakci-suite-handoff.zip` | no, private |

The private folder is in `.gitignore` because this repository is public. The owner's own words, a real form
template and screenshots must not be published. The folder lives only in the working copy where it was saved. A later
session that needs it must get the zip from the owner again. If the owner's message and anything in this folder
disagree, the owner's message wins.

## The ideas in one screen (paraphrased)

1. **Suite.** Evrakçı is mostly about reading documents today. The owner wants it to become common ground for several
   office tools, document reading being one of them.
2. **Print-template library.** The chamber regularly prints fixed-size items: an A5 sheet with the chamber registry
   number, the trade registry number and the company name; folder labels that are printed, cut out and stuck on;
   binder spine strips with a registry number at the bottom; and many more. These template files exist at the chamber
   (the owner does not have them at hand yet). The idea is a library of them inside the suite.
3. **Data in.** Other programs export Excel files and other data. Two ways in: predefined mappings for known exports,
   or paste/load any spreadsheet, let Evrakçı read its headers, and let the user build their own template from it. The
   do-it-yourself route also helps privacy.
4. **Editing playground (a maybe).** Load an example spreadsheet, connect its columns to places in a document, edit
   freely and produce new files from it, the way the standalone tool does for one form.
5. **Editing and output.** Documents should be easy to edit inside Evrakçı and export as spreadsheet or PDF.
6. **Bring the standalone tool in.** The Member Search / Bilgi Formu HTML tool should become part of Evrakçı.

Data note from the owner: the handoff holds no real member data only because the session that made it never had any.
Evrakçı keeps data on the PC and publishes nothing, so holding real member data locally is fine.

Related existing ideas: `docs/ui-goal/feature-ideas.md` rows 16 and 17 (pre-filled forms from imported Excel data, and
looking up read values in imported data; ranking I-48 and I-49).
