---
name: feature-planning
description: Use when asked to plan, scope or write up a new Evrakçı feature or quality-of-life improvement before building it. Produces a one-page spec (problem, who, keyboard flow, screen sketch, data/core changes, tests, risks) checked against PRODUCT.md and DESIGN.md; ideas live in docs/ui-goal/feature-ideas.md and are not decisions.
---

# Feature planning

Plan first, build only after the owner says yes. Entries in `docs/ui-goal/feature-ideas.md`
are ideas, not decisions; a spec turns one idea into a proposal, and the owner decides. Decisions
already taken are in `docs/ui-goal/decisions.md`; do not re-open them inside a spec.

## Before writing

Read `PRODUCT.md` (users, principles, constraints), `DESIGN.md` (tokens, components, named
rules), `docs/ui-goal/shortcuts.md` (free keys), `docs/ui-goal/top25.md` (what already shipped),
and `docs/architecture.md` if the core changes. Check that the idea is not already in
`feature-ideas.md` or shipped (`grep -rn "<keyword>" src/evrakci docs/ui-goal`).
Do not use real documents in examples; invent data.

## One-page spec

Save as `docs/ui-goal/specs/<slug>.md` (create the folder when you write the first one). Keep it
to one page (about 60 lines). Sections, in this order:

1. **Problem.** One or two sentences, in the user's words, with a number if there is one
   ("checking 600 pages means opening each one"). Which Product Principle it serves
   (Never silent / The user decides what documents contain / Less paper handling / Calm for long
   sessions).
2. **Who and when.** Office staff in a long session, or the person who sets up templates.
   How often, at which step (Yükle, Kontrol, Şablonlar, Değerler, Dışa Aktar, Rehber).
3. **Keyboard flow.** The full path without a mouse, step by step, with keys. Use free keys from
   the registry (no Turkish-only letters, no I, no Ctrl+Alt, no clash on that tab; run the
   `shortcut-audit` skill's script). Name the registry action ids to add to
   `src/evrakci/ui/actions.py` and the menu they go in. Mouse path and context menu second.
4. **Screen sketch.** An ASCII or table sketch of the changed region at 1366x768, 100 %, in
   Turkish UI words (terminology from PRODUCT.md: belge, sayfa, kesim, QR ayıraç, filtre,
   şablon, değişken, kontrol, dışa aktar). Say which existing component it reuses
   (DESIGN.md "Components and their Qt names": command bar, inspector card, `CardScroll`,
   toast, infobar) and how it looks at 150 % text and in high contrast.
5. **Data and core changes.** Job file fields (`src/evrakci/pipeline/job.py`), pipeline/CLI
   functions (the window and the `evrakci` CLI call the same core, keep it so), undo step name,
   what is stored in `index.xlsx`. Prefer no core change; D13 says any core hook is minimal and
   tested. Offline and local only (KVKK): no network.
6. **Tests.** Core: `tests/test_*.py` (pytest, synthetic data from `tests/fakes.py`). UI:
   `tests/ui/` offscreen. Shortcuts: registry test plus a key-press test. Screenshots:
   which matrix shot or `states` shot shows it. State the one failure it must catch.
7. **Risks and open questions.** Silent-wrong-output risk (how is it made visible?), 800-page
   performance (see `perf-profile`), Turkish text and keyboard, accessibility, scope creep,
   what the owner must decide.

## Check against the product

Answer each in one line at the bottom, "Pass / Needs change / N/A":

- Never silent: does an unsure or skipped result show in the UI and in `index.xlsx`?
- No built-in document kinds or fields: does it hard-code a document type or variable name?
- Keyboard: every frequent action has a key and visible focus; tab order is reading order.
- Colour: only tokens; orange only for Kontrol, always icon + word; no meaning by colour alone;
  text >= 13 px, weights 400-600 (DESIGN.md Do's and Don'ts).
- Layout: fits 1366x768 at 100 % without window scroll; side panels show whole cards.
- Copy: Turkish, the project's vocabulary ("Kontrol", not "Şüpheli").
- Local-first: no data leaves the machine, no new dependency without a licence check
  (`docs/dependency-licenses.md`).

## After the spec

Update `feature-ideas.md` (link the spec, set status `specced`), then stop and report: the spec
path, the pass/needs-change list, and the owner decisions needed. Build only after approval.
