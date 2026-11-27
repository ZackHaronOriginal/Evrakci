# Versioning proposal (Q-35)

Status: proposal for the owner. Nothing here is decided.

## What exists today
- The app version is `0.0.2` (pyproject.toml, `evrakci.__version__`). The Windows installer workflow builds on a tag `v*`
  and refuses a tag that does not match the version ("Etiket vX ama sürüm Y").
- The files Evrakçı writes carry their own format numbers: job files `JOB_FORMAT_VERSION = 2`, template files
  `TEMPLATE_FORMAT_VERSION = 1`. A newer app opens older files; an older app opens newer files of the same format
  number (it ignores keys it does not know).
- No release tag exists yet.

## Option A: semantic versioning, MAJOR.MINOR.PATCH (recommended)
- **PATCH** (0.1.0 → 0.1.1): fixes only; nothing new to learn; files unchanged.
- **MINOR** (0.1.x → 0.2.0): new features or visible changes (new screens, keys, settings, texts); older files still
  open; a file written by the new version may lose new fields if an older version saves it (said in the release notes).
- **MAJOR** (0.x → 1.0, 1.x → 2.0): a file format number goes up (an older version can no longer open the new files), a
  setting or command is removed, or a workflow changes in a way offices must retrain for.
- **Start:** 0.1.0 for the first signed public release while offices test it; 1.0.0 when you call it ready for daily
  office use (your sign-off after the Phase 6 checks on real documents and the installer).
- **Pre-releases:** `0.2.0-rc.1` style for a build offices try before the real release (GitHub marks it "pre-release").
- Why: the number tells an office whether an update is safe to install without checking (PATCH), worth reading the
  notes (MINOR), or needs planning (MAJOR). It is what Windows installers and GitHub Releases expect, and the existing
  tag check already works with it.

## Option B: calendar versioning, YEAR.MONTH(.n)
- 2026.12, 2027.1, 2027.1.1 for a fix. Tells how recent a build is, not how risky the update is; a file-format change
  must then be announced in the notes only.

## Option C: a single build number
- Evrakçı 7, 8, 9. Simplest, but says nothing about risk or age; the installer and pip still need a three-part version
  inside.

## Where the version is shown (any option)
- Window: Rehber's "Hakkında" area and the window title tooltip; CLI: `evrakci --version`; the installer's name and
  Windows "Apps" list; index.xlsx Özet sheet ("Evrakçı 0.1.0" next to the export time) so an export can be traced to
  the version that made it.

## Release notes (any option)
- One `CHANGELOG.md` section per release, in plain Turkish for offices, with "Added / Changed / Fixed" and a line
  "Dosya biçimi değişti" whenever a format number goes up.

## What to decide
1. Option A, B or C (recommended: A).
2. The first public version number (recommended: 0.1.0).
3. Whether the Özet sheet should carry the version (recommended: yes; it is one cell, no new sentence beyond
   "Evrakçı {sürüm}").
