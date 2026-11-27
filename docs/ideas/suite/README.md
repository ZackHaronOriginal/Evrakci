# Evrakçı as a suite (owner idea log, 2026-11-27)

**Status of everything in this folder: idea, not decided.** Nothing here is planned, scheduled, specced or approved.
Do not plan or build any of it until the owner brings it up. The owner wants to talk through the templates and the
editing side when they do. Planned and built work lives in `docs/ui-goal/` and `specs/`; this folder is kept apart
from it on purpose.

## Files

- `ideas.md`: the ideas organised into parts, with questions kept for later.
- `member-search-reference.md`: how the owner's standalone Member Search / Bilgi Formu tool (an offline HTML file, not
  in this repository) works, as background.

Everything here is anonymized and paraphrased. The standalone tool and its sample files are not part of the repository.

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
6. **Something like the standalone tool, inside Evrakçı.** The owner wants Evrakçı to do what the Member Search / Bilgi
   Formu HTML tool does (find a person in the data, fill a form, print or export). The tool itself is an example, not
   something to move in. (Corrected 2026-11-27: an earlier version said "bring the tool in", which the owner did not say.)

Data note from the owner: the handoff holds no real member data only because the session that made it never had any.
Evrakçı keeps data on the PC and publishes nothing, so holding real member data locally is fine.

Related existing ideas: `docs/ui-goal/feature-ideas.md` rows 16 and 17 (pre-filled forms from imported Excel data, and
looking up read values in imported data; ranking I-48 and I-49).
