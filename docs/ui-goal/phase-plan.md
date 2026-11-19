# Evrakçı: quality phase plan (draft for owner review)

Status: DRAFT for review (reviewed and corrected on Opus, 2026-11-19). Written 2026-11-19. Owner answers so far (2026-11-19): Fluent wins over Apple
where they differ; hit-target minimums 24 px / 32 px in rows / 28 px button height accepted;
performance check 1 is at the start. Everything else still needs the owner's review.
Starting point: `main` with the UI overhaul merged plus 0.0.2 (PR #5). 97 registered actions
(35 app-wide, 21 Kontrol, 15 Değerler, 12 Şablonlar, 7 Yükle, 4 Dışa Aktar, 3 Rehber), 109 key
bindings, 65 UI modules, about 26 000 lines.

## How to read this plan

- **Models (owner rule, 2026-11-19):** research and inventory agents run on Sonnet. Reviews of
  research and of every phase's diff run on Opus, in a fresh context. Research findings that pass
  the Opus review are implemented through the Phase 5 ranking.

- Seven phases, 0 to 6. Each has: goal, inputs, work steps, the exact checks, the output files,
  the exit rule, who reviews, and what the owner decides.
- **A phase is not finished until its exit rule is met and a fresh reviewer (a new agent that did
  not build it) has read the diff and the evidence.** The reviewer's findings are fixed or written
  into the bug ledger with a reason.
- Every result lands in a file in this repo (ledger, table, baseline JSON), never only in chat.
- Two performance checks bracket the work: **Check 1 in Phase 0** (before any change, the
  "before" numbers) and **Check 2 in Phase 6** (after everything, at full scale on both
  systems). Phase 2 fixes the known problem in between, and Phases 4 and 5 re-run the quick
  version as a regression gate.
- Order matters: measurements (1) before fixes, the layout-changing performance fix (2) before the
  per-element audit (4), and features (5) after the audit so new screens are built to the rules.
  The research part of Phase 5 (5a to 5c) does not change code, so it runs in the background from
  Phase 1 on; the owner's ranking (5d) is then ready before Phase 5 starts.

## How the run works (unattended goal run)

- **One step at a time through the model-akisi flow.** Each step gets a task spec, then:
  Sonnet implements; Kapı 1 (Haiku) runs `ruff check .` and the test files for what changed;
  Kapı G (Haiku) runs `tools/screenshots.py matrix` for the touched tabs, the clipping check and,
  from Phase 1 on, `tools/ui_measure.py`, and the main session (Opus) looks at 2 to 3 of the
  worst screenshots itself; four Haiku lenses (spec, edge cases, scope, project rules); a Sonnet
  reviewer sorts the lens findings; Opus accepts against what the owner asked. Research agents
  run on Sonnet. Every phase ends with a fresh Opus review of the whole phase diff and evidence.
  Every Agent call names its model.
- **The owner is not waiting at the keyboard.** Questions never stop the run while other work is
  possible. They go into `docs/ui-goal/OWNER-QUEUE.md` (one line each: phase, question, options,
  what is blocked). The run stops and asks only when every remaining step depends on an answer.
  - Blocking answers (work that depends on them waits): which rules are enforced (Phase 1),
    the feature ranking (5d), each feature spec (5e), any change to the approved look, Turkish
    copy that is new, code signing, version and publishing (Phase 6).
  - Non-blocking owner checks (collected, done on the owner's PC from a CI build): jitter gone
    (Phase 2), the shortcut checklist (Phase 3), each screen (Phase 4). The run carries on; if
    the owner reports a problem, it becomes a ledger row and is fixed before Phase 6 ends.
- **State lives in files, not in the chat.** `docs/ui-goal/STATE.md` holds: current phase and
  step, last commit, what is next, open owner questions, and links to the evidence files. It is
  updated after every accepted step. After a context compaction or a new session the run reloads
  the model-akisi skill, reads `STATE.md` and continues from there. Task specs live in
  `.claude/gorevler/` (git-ignored, because this repo is public and specs quote the owner); nothing
  private goes into committed files.
- **Commits and the PR (owner rule, 2026-11-19).** All work stays on `claude/focused-heisenberg-prspvt`.
  Commit and push after every accepted step. No pull request per phase: one pull request to `main`
  is opened at the end of Phase 6, and the owner merges it.
- **Private material never enters the repo:** the model-akisi skill, the Apple HIG pack text,
  real documents.

## Already decided (do not ask again)

From `docs/ui-goal/decisions.md` (owner answers 2026-11-12 to 2026-11-14). The phases treat these
as fixed rules, not questions:

- Look: direction A "Fluent 2 Mica" is the visual source of truth; chrome, logo, tabs, command bar,
  inspector and spacing stay exactly as approved. Any improvement is proposed separately and applied
  only after the owner says yes.
- D1 to D13: palette (orange only for "kontrol"), Inter, type scale, 4 px grid, radii, motion
  tokens, Lucide icons, three themes, contrast levels, focus ring, text sizes 100/115/130/150 %,
  densities (rows 32/40/48, controls 28/32/40).
- Wording: "Kontrol" everywhere; status words Emin / Orta / Kontrol / Okunamadı and İncelendi /
  İncelenmedi; "Şüpheli" is retired. New feedback texts in Phase 3 follow this vocabulary.
- Kontrol keys: N / Shift+N next/previous kontrol, U next unreviewed, Enter confirm document;
  deleting is undone with Ctrl+Z instead of asking for confirmation.
- At 150 % text the tabs that do not fit go into a "»" menu; side panels scroll card by card.
- Deferred on purpose: first-run tour, completion sound, invert selection (its key I is unreliable
  on Turkish keyboards). Phase 5 triage lists them as "later", not as open questions.
- Hit targets (owner, 2026-11-19): 24 px minimum, 32 px in rows, 28 px button height. These agree
  with D5 (controls 28/32/40, rows 32/40/48); where D5 is larger, D5 applies.

---

## Open conflict the owner must settle first

The approved overhaul chose **Fluent 2 (Windows 11 / Office proportions)**, Inter, a 4 px grid, a
15/21 px body, radii 4/8, motion tokens up to 240 ms and a 2 px + 1 px focus ring
(`docs/ui-goal/GOAL.md` D1 to D13). The new request is to check against **Apple's Human Interface
Guidelines**. These are different rulebooks and some numbers will disagree.

Proposal: Apple HIG is the rulebook for **principles that do not depend on the operating system**
(hierarchy, spacing rhythm, alignment, focus and selection behaviour, feedback, motion purpose,
undo, error prevention, accessibility). Where a measured number differs from an approved decision
D1 to D13, **the approved decision wins unless the owner changes it**, and the difference is listed
in `docs/ui-goal/rules-conflicts.md` for a yes/no. Apple's iOS/touch sizes (for example 44 pt tap
target) are not applied to a mouse app. **Owner confirmed 2026-11-19.**

---

## Phase 0: Ground truth and the "before" numbers (includes performance check 1)

**Goal.** Know exactly what state the app is in, with numbers, before changing anything.

**Inputs.** `main` at the PR #5 merge, the Qt libraries now installed in the build container, the
project skills in `.claude/skills/`.

**Steps.**
1. Run the full suite once with `QT_QPA_PLATFORM=offscreen python -m pytest -q` and `ruff check .`.
   Record pass, fail and skip counts and the run time. Fix test-environment problems only
   (missing system packages), not app code.
2. Run `tools/screenshots.py` for the whole matrix (6 tabs, light/dark/high contrast, 1366×768 and
   1920×1080, 100% and 150% text) and the clipping check. Store the output list, not the images, in
   `docs/ui-goal/baseline/`.
3. **Performance check 1.** Run `.claude/skills/perf-profile/perf_kontrol.py` on the synthetic
   1000-page job (fake delayed renderer) and then with `--real` on a generated PDF. Record per run:
   frame time p50, p95 and max over a full scrollbar sweep, time to first paint, number of page
   renders at first paint, share of visible rows loaded after a jump with no mouse input, settle
   time after a jump, memory after the sweep. Run it 5 times and keep median and spread, so later
   changes are judged against noise. Save as `docs/ui-goal/baseline/perf-before.json`.
4. Run `audit_shortcuts.py` to produce the first shortcut table (`docs/ui-goal/baseline/shortcuts.tsv`).
5. Run `keywalk.py` for every tab and record focus traps, unreachable areas and controls with no
   accessible name.
6. Reproduce the Kontrol jitter with a frame log (which rows are blank or show an old image after a
   scroll with no mouse event) and add it to the bug ledger with the exact repro.
7. **Triage the ledger.** The 31 `needs-repro` rows (B-001 to B-031, found while making the
   inventories) each get a reproduction (a failing test where possible) and a severity, or are
   closed as not a bug with the reason.
8. **Fix the S1 rows now** (data loss, silently wrong output, wrong merge), after the baseline above
   is saved, each with a regression test. Known candidates: a failed read loses finished values
   (B-011), M says "merged" when documents stay split (B-021), K on page 1 relabels without
   splitting (B-020), a failed autosave shows no error (B-029). S2 and lower wait for their phase.

**Checks.** Suite counts match the last recorded run of the UI overhaul (1081 passed, 6 skipped,
commit `e1e3276`) or each difference is explained. Perf runs agree with each other within 15%. If the helper scripts fail
the first time, fixing them is part of this phase, with a test for each fix.

**Outputs.** `docs/ui-goal/baseline/` (suite counts, screenshot list, perf-before.json,
shortcuts.tsv, keywalk output), first rows in `docs/ui-goal/bugs.md`.

**Exit rule.** Every number above exists in a committed file and was produced twice; every
ledger row has a repro or a reason; no S1 row is open.

**Review.** A fresh agent checks the perf script against the code it measures (does it really
exercise the real scroll and paint path, or only a fake?) before the numbers are trusted.

**Owner decides.** Nothing. You read the baseline summary.

---

## Phase 1: Rulebook and the measuring tool

**Goal.** Turn "looks right" into numbers that a program can check.

**Inputs.** Phase 0 baseline; the Apple HIG pack from `raintree-technology/apple-hig-skills`
(cloned fresh into the scratchpad at the start of the phase, never into the repo: its reference
text is Apple's); approved decisions D1 to D13; PRODUCT.md
and DESIGN.md.

**Steps.**
1. **Extract HIG values.** From the pack's foundations, components, inputs and patterns references,
   list every rule that has a number or a testable behaviour (spacing and alignment, control states,
   focus and selection, typography hierarchy, colour contrast, motion durations and purpose,
   icons, window and menu behaviour for macOS). Each line keeps its Apple source URL.
2. **Verify each line against Apple's own page** where the page can be read (Apple's pages are
   built by JavaScript: open them with the pre-installed Chromium through Playwright, not a
   plain fetch). Lines that cannot be
   verified are marked `unverified` and are not enforced, only reported.
3. **Reconcile with D1 to D13.** For each rule, mark: same as ours, differs, not applicable
   (touch, iOS, visionOS), or needs an owner decision. Differences go into `rules-conflicts.md`.
4. **Add the audience rules** that Apple does not cover: 150% text, weaker eyesight (contrast at
   least 7:1 for body text per D10), 1366×768 without window scroll, hit target minimums for a mouse
   (**owner confirmed 2026-11-19**: 24 px minimum, 32 px for controls in rows, 28 px minimum height
   for buttons), keyboard-only use of every function.
5. **Write `docs/ui-goal/rules.json`**: one entry per rule with id, category, what is measured,
   the allowed value or range, the source (HIG URL, decision id or audience), severity, and whether
   it is enforced or only reported.
6. **Build `tools/ui_measure.py`.** It opens each tab in the real app (offscreen), for each theme
   and text size, and for every visible widget records: class and object name, geometry, content
   margins, spacing to neighbours, font family, size and weight, text and background colour with the
   computed contrast ratio, hit area, focus-ring presence and size, tooltip, accessible name and
   role, enabled state, and any animation duration it owns. It compares those to `rules.json` and
   writes a pass/fail row per widget per rule.
7. Test the tool itself: feed it a deliberately broken widget (text 11 px, contrast 2:1, no
   accessible name, 20 px hit area) and require it to flag each one.

**Checks.** The tool finds all four planted defects; running it twice on the same build gives the
same rows; every rule has a source and a severity.

**Outputs.** `rules.json`, `rules-conflicts.md`, `tools/ui_measure.py` with tests, first full
report `docs/ui-goal/baseline/measure-before.tsv`.

**Exit rule.** The report covers all six tabs in all themes and sizes with no tool errors, and the
conflict list is in `OWNER-QUEUE.md`.

**Review.** A fresh agent re-derives five random rules from Apple's source and from the code and
confirms the tool measures the same thing a person would.

**Owner decides.** Every row of `rules-conflicts.md` and which rules are enforced (fail the build)
versus reported. Until the owner answers, every rule is "reported" and the run continues.

---

## Phase 2: Kontrol tab performance fix

**Goal.** Scrolling the Kontrol tab is smooth: no stale images, no thumbnails that wait for the
mouse, no jitter.

**Inputs.** `perf-before.json`, the bug ledger repro, `timeline.py`, `thumbnails.py`,
`kontrol_paint.py`.

**Steps.**
1. **Prove the cause before fixing.** The profiling skill lists four unproven hypotheses: the
   update after a thumbnail finishes only repaints one rectangle; hidden rows drop pending
   requests; loading starts only from the paint event; Qt's scroll-blit leaves old pixels. For each,
   add a temporary log or test that shows it happening. Keep only the causes that are proven.
2. Fix in this order, re-measuring after each: load thumbnails by visible rows plus a prefetch
   margin ahead of the scroll direction, independent of mouse events; keep requests for rows that
   are still near the viewport and cancel only far ones; invalidate the correct rectangle when a
   thumbnail arrives; draw a fixed-size placeholder immediately; disable scroll-blit for this view if
   that proves to be the stale-pixel source; limit cache size by pixel count and evict by distance
   from the viewport.
3. Replace the existing "at most 30 renders at first paint" bound deliberately with a bound that
   reflects the prefetch margin, and write why in the test.
4. Add regression tests that fail on the old behaviour: a jump with no mouse event must load all
   visible rows; a fast scroll must leave no row showing another page's image; memory must stay below
   a set ceiling after a long sweep.

**Checks (targets, to be confirmed against Phase 0).** Frame p95 at most 16.7 ms and max at most
50 ms during a sweep; first paint under 1 s; settle after a jump at most 1.5 s; 100% of visible rows
loaded with no mouse input; no row ever shows the wrong page. If Phase 0 shows these targets are
unreachable in the offscreen environment, they are re-set from the Phase 0 numbers, with the owner.

**Outputs.** Code fix with tests, `docs/ui-goal/baseline/perf-after-phase2.json`, a short note on
which hypotheses were true.

**Exit rule.** All targets met in three runs and no previously passing test broken. The owner's
check on their own PC (installer from CI; offscreen timing is not a real monitor) goes into
`OWNER-QUEUE.md` as a non-blocking check.

**Review.** A fresh agent reads only the diff and the before/after JSON and tries to break it
(huge job, zoom change during scroll, theme switch during load, cancel and re-add).

**Owner decides.** Whether the targets are good enough after you have scrolled it yourself.

---

## Phase 3: Shortcut contract

**Goal.** Every shortcut does the same thing on every screen, does what its label says, and shows
the right feedback. A key that has no meaning on a screen says so instead of staying silent.

**Inputs.** The registry (97 actions, 109 bindings), `shortcuts.md`, the Phase 0 shortcut table.

**Steps.**
1. **Write the contract table** `docs/ui-goal/shortcut-contract.tsv`, one row per binding per tab
   where it is active, with these columns: tab, key, action id, label, **precondition** (what must
   be true: selection, focus owner, job loaded), **expected effect** (the exact change in data or
   state), **expected feedback** (status bar text, toast text, focus move, selection or highlight
   change, undo entry name, or disabled state with its reason), **when not applicable** (the defined
   behaviour, disabled or a message), **undo behaviour**, and the test name.
2. **Cross-tab consistency rules**, enforced by the audit script: same key means the same label on
   every tab where it is active; a key meaning "next/previous/accept/delete/find/undo" behaves the
   same way everywhere; no key does something different when focus is in a text field except the
   documented typing guard; keys on the Turkish Q layout are safe (no Ç Ş Ğ İ Ö Ü, no Ctrl+Alt).
3. **Contract tests.** About 280 rows (35 app-wide actions on six tabs plus the tab actions), so
   the tests are data-driven: one parametrized test reads `shortcut-contract.tsv`, plus small
   helper functions per kind of effect and feedback. One test per row: build the real window with a demo job, go to the tab, put
   focus where the precondition says, send the real key event through `QTest`, then assert **both**
   the effect (read from the job or model, not from the UI text) **and** the feedback (the status
   bar, toast, focus widget, selection, undo stack entry). Add a second test for each row that
   sends the key when the precondition is false and asserts the defined fallback.
4. **Menu, toolbar and palette parity.** The same action started by menu, button, command palette and
   key must produce the same effect and the same feedback; a test triggers each route.
5. **Focus and typing cases.** For each typing field on each tab, press every single-key action and
   assert it types the character and does not fire the action; press the Ctrl combos and assert they
   still work.
6. Close the stale-text gap: update `shortcuts.md` (it still says the registry is not wired), and
   make the audit script read tests by action id and by a marker comment instead of free text
   search, so "NONE" is reliable.

**Checks.** `audit_shortcuts.py --check` exits 0; every contract row has a passing effect test
and feedback test and a passing "not applicable" test; no row is marked "feedback: none" without
an owner-approved reason.

**Outputs.** The contract table, the contract tests in `tests/ui/`, a cleaned `shortcuts.md`,
a list of every mismatch found and how it was fixed in the bug ledger.

**Exit rule.** 100% of bindings have all three tests passing. The owner's by-hand checklist
(`docs/ui-goal/shortcut-checklist.md`, grouped by key, every row) goes into `OWNER-QUEUE.md` as a
non-blocking check.

**Review.** A fresh agent picks 20 random rows, runs the real app by hand through
`QTest` driving, and tries to find a row where the table lies.

**Owner decides.** Every place where two tabs behave differently on purpose (kept and documented, or
changed), and every feedback text (it is Turkish copy and you will read it).

---

## Phase 4: Element-by-element audit

**Goal.** Every element, in every state, on every screen, is measured against the rulebook and
every click path has been tried.

**Inputs.** `rules.json`, `ui_measure.py`, the ui-bug-hunt skill, the new design and audit
plugins, the contract table.

**Method, one screen at a time, in this order:** Kontrol, Yükle, Değerler, Şablonlar, Dışa Aktar,
Rehber (most used first). For each screen:
1. **Inventory.** Start from the feature inventory (`research/inventory-<screen>.md`) and add every
   element it does not list: buttons, fields, tables and their cells, headers, menus and context
   menus, dialogs and popups, tooltips, icons, badges, the status bar, the inspector and the
   command bar. Save as `docs/ui-goal/audit/<screen>-inventory.md`.
2. **State matrix.** For each element: default, hover, pressed, focused (keyboard), selected,
   disabled, empty, loading, error, and long text or many items. Each cell is either a screenshot
   reference, a measured row, or "n/a" with a reason.
3. **Measure.** Run `ui_measure.py` for this screen in all themes, at 100% and 150% text, and at
   1366×768 and 1920×1080. Every failing rule becomes a ledger row.
4. **Click paths.** Every click, double click, right click, drag and drop, wheel and key on every
   element, plus the common mistakes (double click on a button, drag to the wrong place, cancel in
   the middle, close during a task, resize during a task). Each path: expected, actual, pass or fail.
5. **Motion.** For every animation: duration, curve, what triggers it, what happens with reduced
   motion, and whether it blocks input. Any motion on a frequent action is removed.
6. **Copy.** Every string in Turkish: clear, correct, consistent, error messages say what to do
   next (ux-copy and ux-writing skills as lenses).
7. **Expert lenses.** Run the design critique, accessibility, interaction and performance audit
   lenses from the installed plugins on that screen's code and screenshots. Their findings go in the
   ledger, de-duplicated against the measured ones.
8. **Fix** all S1 and S2 rows and the S3 rows that are cheap. Re-measure. Remaining S3 and S4 stay
   open in the ledger with an owner-visible reason.

**Checks.** Per screen: zero failing enforced rules; zero S1/S2 open; the keywalk reports no trap,
no unreachable area and no unnamed control; the clipping check passes in all combinations.

**Outputs.** Per-screen inventory, state matrix and click-path files, the filled bug ledger, fixes
with tests. After the last screen, the whole-app measure report `measure-after.tsv` next to
`measure-before.tsv`.

**Exit rule.** All six screens pass as above and the quick performance check (Phase 2 script)
still meets its targets. The owner's walk through each screen is a non-blocking check in
`OWNER-QUEUE.md`.

**Review.** After each screen, a fresh agent reviews that screen's diff and ledger rows. After the
last screen, one whole-app review.

**Owner decides.** Which S3/S4 rows to leave open, any rule whose enforcement turned out to be
wrong, and any visual change (anything that alters how the approved design looks needs your yes).

---

## Phase 5: Research, then features and quality-of-life

**Goal.** Decide what to add from evidence (what the sector and comparable apps really do), not
from guesses; then build only what is specified and approved.

*5a to 5c run in the background from Phase 1 on (Sonnet research agents, Opus review); they change
no code. 5d needs the owner; 5e starts after Phase 4.*

**Sub-phase 5a: Inventory of what we have.** (A first draft was made while preparing this plan, in `research/`; the goal run re-verifies it against the code and extends it.)
1. One table per tab (plus app-wide) listing every feature with an ID (K-01, V-01, ...), what it
   does, how to reach it, code evidence, whether a test covers it, and a category tag.
2. Each file ends with "Observations" (things that look missing or awkward, marked as not decided).
3. Output: `docs/ui-goal/research/inventory-*.md`. Check: every row has code evidence; a fresh agent
   spot-checks 20 random rows against the code.

**Sub-phase 5b: Find the comparable software.** (A first draft is in `research/competitors.md`; the goal run spot-checks it with Opus and extends it.)
1. List open-source, commercial and review-UI references (Paperless-ngx, NAPS2, PDFsam, ABBYY
   FlexiCapture, Kofax, Ephesoft, Acrobat and others), each with licence, link, which of our tabs it
   informs, and whether it can be inspected. Output: `research/competitors.md` with a shortlist.
2. Research ideas only. No code or text is copied (licences and the CLA).

**Sub-phase 5c: Research each feature area against the field.**
1. For every inventory category (splitting, filtering, page operations, review and QC, selection,
   undo, search, template design, region reading, value editing, naming and export formats,
   printing, accessibility, performance), study how the shortlist apps and published research
   (capture-industry practice, data-entry verification studies, large-list UX) handle it.
2. For each: what they do, what we do, the gap, evidence links, and the cost to us. Open-source
   apps on the shortlist get a source read for how they implement the feature.
3. Output: `research/findings-<area>.md`, with every claim linked to a page that was opened.
   Anything unverified is marked. A fresh agent re-checks 10 random claims against their sources.

**Sub-phase 5d: Idea list and ranking (you).**
1. I merge findings, `feature-ideas.md` and your own ideas into one list with: the problem, who gains,
   evidence, effort (S/M/L), risk, performance cost and which tab it touches.
2. You rank each: must, should, later, drop. Already deferred (first-run tour, completion sound,
   invert selection) start as "later".

**Sub-phase 5e: Spec and build.**
1. One-page spec per accepted idea (problem, who, keyboard flow, sketch, data and core changes, the
   shortcut contract rows it adds, the rules it must meet, tests, risks, performance cost). You
   approve each spec before building.
2. Kontrol filters first: QR content or pattern, blank pages, page size, orientation, OCR text found,
   low confidence, saved filters, combining filters. Each defines how it is chosen, shown, counted,
   cleared, how it interacts with selection and undo, and its keyboard path.
3. Build in small steps with core tests, UI tests, new contract rows and a `ui_measure.py` run.
4. After each feature: quick performance gate, shortcut audit, keyboard walk, fresh review against
   the spec, then you try it.

**Exit rule.** Inventory and research files exist and were spot-checked, the ranked list is
approved, and every "must" and "should" is shipped or has a written reason it moved.

**Owner decides.** The ranking, each spec, and each feature after you try it.

---

## Phase 6: Hardening, performance check 2, release

**Goal.** Prove it at full scale, on both operating systems, then ship a version.

**Steps.**
1. **Performance check 2.** Repeat the Phase 0 measurements with the same script on the final code,
   plus larger cases: 800-page real scans (OCR on and off), 2000-page synthetic, 150% text, high
   contrast theme, a slow disk (throttled), and a low-memory run. Produce
   `docs/ui-goal/baseline/perf-final.json` and a table of before, after Phase 2 and final for every
   metric. Anything worse than the "before" numbers must be explained or fixed.
2. **Real documents.** Real scans never come into this container or the repo. The run writes a
   script and a checklist; the owner runs them on their PC on real (anonymised) scans: add, read,
   check, fix values, export, and compare the exported files and index.xlsx with the CLI output
   for the same input. The owner reports the result; problems become ledger rows.
3. **Windows.** The Windows installer from CI on a clean Windows user account: install, upgrade over
   0.0.1/0.0.2, run, uninstall. Include the "unknown publisher" warning in the notes; code signing is
   a separate owner decision.
4. **Linux.** The tarball on clean Debian 12 and Ubuntu 24.04 (already automated in CI).
5. **CI gates.** Add to CI: the contract tests, `audit_shortcuts.py --check`, the measure tool with
   enforced rules, and a short performance regression test. A rule that cannot run in CI is listed.
6. **Docs and version.** Update README, `DESIGN.md`, `shortcuts.md`, and the progress file; bump the
   version; tag the release and attach installers and checksums to a GitHub Release.

**Exit rule.** CI is green on both systems with the new gates, the final performance numbers are
written down, every non-blocking owner check in `OWNER-QUEUE.md` is answered and its problems
fixed, and the owner has installed the release build and signed off.

**Review.** A last whole-repo review by a fresh agent with only the diff since Phase 0 and the
evidence files.

**Owner decides.** Code signing, the version number, and whether to publish.

---

## Where each skill and plugin is used

| Phase | Used |
|---|---|
| all | `model-akisi` (private, kept out of the repo) for every step; Opus reviews at every phase end |
| 0 | `perf-profile`, `shortcut-audit`, `ui-bug-hunt` scripts, `run` |
| 1 | Apple HIG pack (reference), `design-systems`, `design:design-system`, `impeccable` |
| 2 | `perf-profile`, `audit-as-perf-eng`, `code-review`, `simplify` |
| 3 | `shortcut-audit`, `interaction-design`, `audit-as-dx-eng` (shortcuts), `ux-writing` for feedback text |
| 4 | `ui-bug-hunt`, `design-critique`, `accessibility-audit`, `accessibility-review`, `audit-as-ux-eng`, `audit-as-a11y-eng`, `make-interfaces-feel-better`, `ux-copy`, `impeccable` |
| 5 | `deep-research`, web research agents, `feature-planning`, `ux-strategy`, `ux-research`, `interaction-design`, `code-review` |
| 6 | `audit-as-prod-readiness`, `full-audit`, `security-review`, `perf-profile` |

Note: the audit-suite and design-skills plugins are written for web projects. Their principles
apply, their React/CSS specifics do not, and the reviewer prompts must say so.

## Risks

- Offscreen Qt timing is not a real monitor, so Phase 2 and 6 numbers need the owner's PC as a
  second opinion. Mitigation: compare relative before and after, not absolute values.
- A rulebook of unverified third-party numbers could enforce wrong values. Mitigation: only
  verified rules are enforced; the rest are reported.
- Changing many things at once hides regressions. Mitigation: one screen or feature per commit
  group, the quick gates after each.
- Apple rules against the approved Fluent design could drift the look. Mitigation: any look change
  needs your yes (Phase 1 conflict list, Phase 4 owner decisions).
- Review fatigue: this plan has many owner decisions. Mitigation: they are batched at the end of
  each phase, in one short list, not asked one by one.
