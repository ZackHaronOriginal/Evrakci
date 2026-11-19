# Goal: Evrakçı UI/UX overhaul ("Ofis gibi" — calm, solid, Office-class)

You are the lead of a multi-agent UI/UX overhaul of Evrakçı's PySide6 window. The owner has opted in
to multi-agent orchestration for this goal: use a Workflow (or Agent fan-out) as described below,
load the named skills in every agent, and verify everything with independent reviewer agents.
Work on branch `claude/peaceful-clarke-i9xnod` (or the branch the session gives you); commit per
phase; push when a phase is green. Never touch `main`.

## 0. Read first (every agent)

| File | What it gives you |
|---|---|
| `PRODUCT.md` | Users, context, principles (never silent, human in the loop, calm long sessions, keyboard-heavy, Turkish) |
| `DESIGN.md` | The current "Kartotek" system. **Its palette and signatures survive; its layout and components are being redone** (see §2) |
| `docs/research/01-apple-hig.md` | Apple HIG: type, contrast, controls, alerts, undo, progress, layout (rules 1–19) |
| `docs/research/02-motion.md` | Motion tokens from Material/Fluent/Carbon/Primer/Atlassian, NN/g timing, Qt animation + reduced motion (rules 1–12) |
| `docs/research/03-fluent-and-enterprise-systems.md` | Windows 11/Fluent 2 ramp, control heights, radii, focus, density, high contrast (rules 1–17) |
| `docs/research/04-ux-research.md` | Heuristics, response times, OCR human-in-the-loop, keyboard, older users, WCAG 2.2, Turkish (rules 1–21) |
| `docs/research/05-sector-examples.md` | Acrobat, Lightroom, ABBYY, Office, Paperless-ngx, NAPS2, IDP validation screens; per-tab pattern library (rules 1–21) |
| `docs/research/06-visual-craft-and-qt.md` | Colour systems, fonts (Turkish glyphs verified), icons, tokens, what QSS can/can't do (rules 1–18) |
| `docs/research/07-qol-audit.md` | Every missing quality-of-life feature, shortcut inventory, proposed shortcut map, top-25 list |
| `docs/logo/README.md` | The new logo and its colours |

Where research files disagree, **§2 Decisions wins**. Values tagged "(unverified)" in the research
are not hard requirements.

## 1. Skills to load

Load these with the Skill tool at the start of the phase that needs them (and in every subagent
of that phase — pass the instruction "load skill X first" in each agent prompt). Names in
brackets are the plugin; if a plugin isn't installed, say so in the phase report and carry on
with the research files instead. Never skip silently.

| Phase | Skills (exact names) |
|---|---|
| Direction & system | `frontend-design:frontend-design`, `design:design-system`, `vectorlab-ux-skills:typography`, `vectorlab-ux-skills:colour-palette`, `vectorlab-ux-skills:spacing`, `vectorlab-ux-skills:surfaces`, `vectorlab-ux-skills:anti-slop`, `vectorlab-ux-skills:page-patterns`, `vectorlab-ux-skills:defaults` |
| Motion | `vectorlab-ux-skills:motion`, `vectorlab-ux-skills:transitions`, `vectorlab-ux-skills:reduced-motion`, `vectorlab-ux-skills:loaders` |
| Interaction & QoL | `vectorlab-ux-skills:keyboard`, `vectorlab-ux-skills:icon-buttons`, `vectorlab-ux-skills:forms`, `vectorlab-ux-skills:errors`, `vectorlab-ux-skills:empty-states`, `vectorlab-ux-skills:labels`, `vectorlab-ux-skills:verbs`, `ui-ux-behaves:ui-ux`, `ui-ux-behaves:ui-ux-table`, `ui-ux-behaves:ui-ux-dialog`, `ui-ux-behaves:ui-ux-form`, `ui-ux-behaves:ui-ux-tabs`, `ui-ux-behaves:ui-ux-active`, `ui-ux-behaves:ui-ux-passive`, `design:ux-copy` |
| Review (every phase) | `ui-design-review:ui-review`, `ui-design-review:ui-polish`, `ui-design-review:ui-compare`, `ui-ux-behaves:review`, `ui-ux-behaves:walkthrough`, `ui-ux-behaves:copy-check`, `vectorlab-ux-skills:ux-audit`, `design:design-critique`, `design:accessibility-review`, `code-review` |
| Logo/icon touches | `logo-design:logo-design` (assets mode only; the logo is final) |

Not for this app: `vectorlab-ux-skills:viewports` (browser widths; our canvas is 1366×768+ desktop)
and `ui-ux-behaves:ui-ux-chart`/`ui-ux-date` unless a chart or date field is added. The UXKIN MCP
server does not connect in this environment; `ui-compare` falls back to platform conventions.

The skills are written for web stacks. Translate their rules to Qt (QSS + QPalette + QPainter),
and where a skill rule conflicts with §2 or a research rule, §2 then the research wins; note the
conflict in the phase report.

## 2. Decisions (owner: confirm or change before running)

| # | Decision | Default | Why |
|---|---|---|---|
| D1 | Identity | Keep the logo palette as the brand: cabinet green `#3f5a4c` (accent), manila `#e9d9a6` (filed/document start), signal orange `#e8731a` (needs a check, nothing else). Rebuild everything else. | Logo kit is final; orange-means-kontrol is the app's core rule |
| D2 | Overall feel | "Office-class": Windows 11/Fluent proportions, a command bar per tab, quiet surfaces, 1 px hairlines, one accent; not a web dashboard | Owner asked for an Office feel; users live in Windows/Office |
| D3 | UI font | Bundle **Inter** (OFL 1.1; Turkish glyphs verified) static Regular/Medium/SemiBold; fall back to Segoe UI Variable → Segoe UI. **Bundling OFL needs owner approval** (PRODUCT.md licence list). If not approved: Segoe UI only. | Research 06 rule 6 |
| D4 | Type scale | Body **15/21 px** (older users), secondary 13/18, captions 13 px floor, section 17/24, panel 20/28, page 24/32. Tabular figures on all numbers. | Stricter than Fluent's 14 for this audience; research 01 r1, 03 r1, 04 r3 |
| D5 | UI scale & density | Text size setting 100/115/130/150 %; three densities Sıkı/Normal/Geniş = rows 32/40/48, controls 28/32/40. Default Normal. | Research 03 r4, 05 r13, 06 r8 |
| D6 | Geometry | 4 px grid; spacing {4,8,12,16,24,32,48}; radii 4 (controls), 8 (dialogs, menus, popovers), 2 (page sheets); no others | Research 03 r3/r5, 06 r9 |
| D7 | Motion | Tokens 0 / 80 / 120 / 180 / 240 ms; curves standard (0.2,0,0,1), enter (0,0,0,1), exit (0.3,0,1,1), linear; nothing > 240 ms except indeterminate progress; no motion on frequent actions (arrow keys, accept-next); reduced-motion flag from Qt 6.12 `motionPreference` or OS, overridable | Research 02 §7–8 (cap tightened from 320 to 240 per 06 r14) |
| D8 | Icons | **Lucide** (ISC) SVGs, 16/20/24 px, recoloured from tokens; replace the current sprite (keep its names as aliases) | Research 06 r12; one set only |
| D9 | Themes | Light (default), Dark, High contrast (follows OS high-contrast palette). Follow OS scheme by default; manual override in Ayarlar. | Research 01 r16, 03 r14, 04 r16, 06 r11 |
| D10 | Contrast | Body/table text ≥ 7:1; secondary ≥ 4.5:1; component edges, icons, focus ≥ 3:1. Unit-tested per token pair, per theme. | Research 04 r4, 06 r4 |
| D11 | Focus | 2 px outer + 1 px inner ring (Fluent), painted by a QProxyStyle/overlay, on every focusable widget, never hidden | Research 03 r6, 04 r5 |
| D12 | The 4 uncommitted screen files from the stopped redesign (`kontrol.py`, `sablon.py`, `timeline.py`, `yukle.py`) | **Discard** (`git checkout --` them) and start from HEAD; HEAD already has the redesigned Değerler/Dışa Aktar and the foundation | They were half-finished |
| D13 | Core | No changes to `src/evrakci/pipeline/` or the CLI unless a UI feature truly needs a core hook; then minimal and tested | Window and CLI share one core |

## 3. What "done" looks like (acceptance criteria)

### 3.1 App-wide
- **Command surfaces:** a menu bar (Dosya, Düzen, Görünüm, Git, Araçlar, Yardım) with Alt access keys
  (`&`) and shortcuts shown; a per-tab command bar (D2); right-click context menus on thumbnails,
  rows, jobs, batches, variables, boxes; a command palette (Ctrl+K / Ctrl+Shift+P) listing every action.
- **Shortcuts:** implement the full map in `07-qol-audit.md` (Turkish-keyboard-safe: no Ç Ş Ğ İ Ö Ü,
  no Ctrl+Alt+letter); one central `actions.py` registry of QActions (text, icon, shortcut, tooltip
  with shortcut, enabled-state) used by menus, command bars, context menus and the palette;
  single-key shortcuts disabled while a text field has focus; F1 = Yardım, Ctrl+/ and "?" =
  shortcut sheet showing only keys valid on the current tab; Ctrl+1…6 tabs; Ctrl+Tab cycles;
  F6 cycles regions.
- **Zoom everywhere:** Ctrl+wheel, Ctrl+plus/minus, Ctrl+0 (fit), status-bar zoom slider with %;
  on Kontrol thumbnails, page preview, Şablonlar canvas, Değerler crop; per-view zoom remembered.
- **Large page preview:** Space or double-click on any page opens a loupe (fit/width/100 %),
  arrows page through, Esc returns, thumbnail strip stays visible (Lightroom pattern).
- **Persistence (QSettings):** window geometry/maximised, last tab, splitter sizes, column widths
  and sort, zoom per view, thumbnail size, density, text size, theme, recent jobs, recent folders.
- **Undo:** one visible undo history (Düzen menu + Ctrl+Z/Ctrl+Y everywhere, label names the action:
  "Geri al: Kesim ekle"); covers Kontrol, Şablonlar, Değerler edits, batch moves.
- **Feedback:** non-blocking toasts for completed events only (InfoBar for persistent problems);
  Windows taskbar progress for OCR/export; busy cursor for > 100 ms waits; header save state
  (Kaydediliyor… / Kaydedildi 14:32 / Kaydedilemedi + retry).
- **Settings dialog (Ayarlar, Ctrl+,):** theme, text size, density, reduced motion, shortcuts list,
  retention, default export folder.
- **Help:** Yardım menu with the Rehber, shortcut sheet, Hakkında (version, licences, logo).
- **Empty states** on every screen: what goes here, why empty, the primary action (in Turkish).
- **Accessibility:** accessible names on every control, tab order = visual order, high contrast,
  all of D10/D11, nothing below 24×24 interactive (primary ≥ 32 px).

### 3.2 Per tab (patterns from `05-sector-examples.md` §pattern library)
- **Yükle:** job list with search and recent; batch table (reorder by drag and Alt+↑/↓), drop
  anywhere in the window, pre-flight counts, progress with time left and cancel; scan-profile hint.
- **Kontrol:** overview strip of the whole job above the working timeline (viewport indicated);
  thumbnail size slider; grid ⇄ loupe (Space/Esc); selection model (click, Shift/Ctrl, rubber band,
  Ctrl+A, Esc clears); "Sonraki şüpheli" and "Sonraki incelenmemiş" as separate jumps; Ctrl+G go to
  page/document; context menu with cut/merge/rotate/delete/apply template; guide tabs and riders
  per DESIGN.md signatures; never allow deleting every page of a document silently.
- **Şablonlar:** zoomable, pannable canvas (wheel, space-drag), rulers in mm, snap toggle, box
  handles with arrow-key nudge (Shift = 1 mm, plain = 0.25 mm), live read results, variants list.
- **Değerler:** dual pane — table and the page crop linked both ways; Enter = accept and go to next
  uncertain; Tab = next value; F2 edit; Esc revert; confidence marker (icon + word, 3 levels),
  sortable/filterable; uncertain characters tinted inside the value; "tümünü incele" mode and a
  spot-check sample before export; bulk accept with count + undo.
- **Dışa Aktar:** pre-flight summary (belge / şüpheli / eksik, graded block/warn/inform), file-name
  preview, progress with cancel, done state with open file/folder and "Explorer'da göster".
- **Rehber:** searchable, zoomable text; printable separator sheets; linked from Yardım and F1.

### 3.3 Verification gates (every phase)
- `QT_QPA_PLATFORM=offscreen python3 -m pytest -q` all green; `ruff check .` clean.
- New tests: token contrast per theme (D10); no hex literals outside the token file; no animation
  duration > 240 ms and all zero under reduced motion (D7); every QAction has text + tooltip, and
  shortcut uniqueness per context; persistence round-trip; zoom keys on each zoomable view.
- Screenshots with `tools/screenshots.py` (extend it): 6 tabs × {light, dark, high contrast} ×
  {1366×768, 1920×1080} × {100 %, 150 % text}; nothing clipped/elided/overlapping; no window scroll
  at 1366×768 default.
- Reviewer agents (fresh context, not the builders) run the Review skills on the screenshots and
  the diff, and report findings ranked by severity; builders fix all high/medium findings before the
  phase is green.

## 4. Workflow

Run as a Workflow (owner opted in). Keep each agent's scope to its own files; shared files
(`theme.py`, `tokens`, `widgets.py`, `icons.py`, `actions.py`, `main_window.py`) belong to the
Foundation phase only, later agents request changes through the lead.

1. **Phase 0 — Prep (lead).** Apply D12. Run tests. Read §0. Write `docs/ui-goal/decisions.md` with
   the confirmed decisions.
2. **Phase 1 — Direction (1 agent + 2 reviewers).** Load Direction skills. Produce HTML mockups
   for the 6 tabs at 1366×768 (light + dark) in `docs/ui-goal/mockups/`, using real research numbers.
   Reviewers: `ui-review` + `design:design-critique` + `accessibility-review`. **Checkpoint: show the
   owner the 6 mockups and wait for approval before Phase 2.**
3. **Phase 2 — Foundation (1–2 agents).** Tokens (DTCG JSON → generated `QPalette` + templated QSS),
   themes + ThemeManager, font bundling (if D3 approved), Lucide icons, focus ring QProxyStyle,
   motion module, `actions.py` registry, menu bar, command palette, settings dialog, QSettings
   persistence, toasts/InfoBar, taskbar progress, zoomable view base class, loupe preview.
   Update `DESIGN.md` to the new system. Gates §3.3.
4. **Phase 3 — Screens (parallel, one agent per tab: Yükle, Kontrol, Şablonlar, Değerler,
   Dışa Aktar, Rehber).** Each loads Interaction & QoL + Motion skills, implements §3.2 for its tab
   on the Foundation, keeps all existing behaviour and tests. Gates §3.3 per tab.
5. **Phase 4 — Integration review (3 reviewer agents, fresh context).** One per lens:
   (a) visual + Office feel (`ui-review`, `ui-compare` against Acrobat/Office/Lightroom patterns),
   (b) accessibility + keyboard (`accessibility-review`, `keyboard`, WCAG 2.2 items in 04),
   (c) code (`code-review` at high effort + `simplify`). Fix, re-run gates.
6. **Phase 5 — Ship.** Regenerate README screenshots, update `docs/superpowers/progress.md`,
   commit, push, and give the owner a short report with before/after images and anything left open.

## 5. Constraints that never bend
- Turkish UI text; invented data only in screenshots and mockups (never real documents).
- Licences: only MIT/BSD/Apache/MPL/ISC/HPND/LGPL (+ OFL if D3 approved); record every font/icon
  licence in `packaging/licenses/` and `docs/dependency-licenses.md`. No PyQt-Fluent-Widgets.
- Must stay smooth at 1,000 pages (paint in delegates; no widget per page).
- Orange only means "kontrol"; status never by colour alone; nothing silently wrong.
- Don't push to `main`; don't open a PR unless the owner asks.
