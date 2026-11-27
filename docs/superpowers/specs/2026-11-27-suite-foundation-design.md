# Evrakçı suite foundation: design

**Status:** draft for the owner's approval (2026-11-27). Nothing here is built yet.
**Background:** the owner's ideas (`docs/ideas/README.md`, `docs/ideas/suite/ideas.md`) and twelve research
reports with measurements (`docs/ideas/suite/research/`). Marks used below: **[owner]** = decided by the owner;
**[call]** = the writer's call, open to correction; **[builder]** = left to whoever builds it.

## 1. Intent

Evrakçı today does one fixed job: scan a pile, split it into documents, read values with OCR, let staff check
them, export named PDFs and an Excel index. It works, but the UI looks poor, the work drifted into rules and
documents instead of product, and everything is wired around that one job.

The owner wants Evrakçı to become **the chamber's tool for repeated document and paperwork jobs that people do
by hand today** [owner]: scanning piles, checking documents against real papers, filling Excel/Word/PDF forms
from TOBB and other data, filling or checking an Excel sheet from scanned documents, printing labels and forms,
editing forms by ticking boxes and typing, and handing work between staff on the office network. It is a
manual-job replacer, not a PDF editor [owner]. It must stay easy for non-technical staff while features keep
coming for years [owner].

This document designs the **foundation** that makes that possible, and the first step on it: the existing
scan-pile job moved onto the new foundation with a new UI. Later job kinds and sharing get their own designs.

## 2. Goals, non-goals, anti-goals

**Goals**
- The backend owns all logic; the UI only draws and sends requests. Replacing the UI later means writing a new
  UI against the same API [owner].
- A UI that can be designed like a website and looks and feels excellent [owner], built in React + TypeScript
  and shipped in Electron [owner].
- Adding a job kind, field kind, data source or output is a small, isolated piece of work [owner: "scalable"].
- Saved jobs and templates keep opening after every update (versioned files, upgraded on load).
- Job storage that can later sit on an office share without a rewrite (report 5).
- The owner sees real screens early: designs in the browser and screenshots before anything is pushed.

**Non-goals (for this design)**
- Building a second job kind, the print-template library, data import, form editing or network sharing. The
  foundation must make room for them; their designs come later.
- Sending files to institutions. Staff send; Evrakçı makes finished files easy to find and take [owner].
- Users defining their own job kinds or workflows. They pick from fixed lists (report 6).
- macOS. Windows first, Linux second (Pardus); the stack does not rule macOS out.

**Anti-goals (would be failures even if it works)**
- Logic creeping back into the UI (round one's main structural problem; report 1's biggest risk).
- A big general framework designed before a second real job kind exists (report 6).
- Weeks of rules, audits and documents with nothing the owner can look at (round one).
- Any feature that plants fake or wrong values in real documents, in any form [owner].
- Any text suggesting paper originals can be thrown away after scanning [owner].
- Anything that sends data off the PC (KVKK; all data stays local or on the office network).

## 3. Constraints

- **Users and PCs:** non-technical staff; ordinary, often older Windows 10/11 PCs (the owner's test laptop:
  i3-7100, 3.9 GB RAM); Linux/Pardus matters. Offline.
- **Licence:** AGPL-3.0 with a CLA so the owner can also sell commercial licences. Every dependency must be
  permissive or weak copyleft (LGPL/MPL used dynamically). `packaging/gpl_check.py` keeps refusing GPL parts.
  Known traps: PDFsharp 6.5+ (AGPL), QuestPDF (excludes public bodies), tldraw (licence key), GPL-only Qt Quick
  modules (reports 2, 9, 10).
- **Builders:** one owner plus AI coding agents. Python and TypeScript are where agents are strongest (reports 2,
  10). Code and tests must be easy for agents to check on their own (typed boundaries, screenshot tests).
- **Measured budget** (report 12, owner's laptop, second start): pages on screen ≈ 1 s, smooth scrolling at
  1000 pages, ≈ 470 MB after heavy scrolling. The real app must stay within: start to first screen ≤ 2 s,
  ≤ 700 MB on a 1000-page job while browsing and reviewing, no dropped frames while scrolling Kontrol on that
  laptop [call]. The 700 MB counts every process (Electron, backend, render processes). During OCR and export
  the peak may reach 1 GB; the number of OCR/export workers is chosen to stay under it on a 4 GB PC [call].
- **What exists:** a Qt-free Python core (`src/evrakci/pipeline/`, ≈ 5,000 lines) and a CLI (`src/evrakci/cli/`,
  ≈ 1,800 lines) with about 3,500 tests; a PySide6 UI (`src/evrakci/ui/`, ≈ 34,000 lines) that holds some logic
  (listed in §9); packaging for Windows (cx_Freeze, vcpkg Tesseract, Inno Setup) and Linux.

## 4. Approaches considered

**Stack**
1. **Python backend + React/TypeScript UI** [owner, picked]. Keeps OCRmyPDF, PDFium, Tesseract and the tested
   core (no permissive OCRmyPDF equivalent exists in .NET or Rust; report 2). React gives design freedom and
   the best agent support (report 10). Most comparable products use a web UI over a separate core (report 11).
2. C#/.NET rewrite (Avalonia/WPF): rebuilds the PDF/OCR output, licence traps, weaker agent results, 6-9+ months.
3. Stay on PySide6 (Widgets or QML): least memory, but limited design freedom, hand-built components, no
   evidence on agent quality for QML, GPL-only modules.

**Shell** (measured, report 12)
1. **Electron + Python as a separate process** [owner, picked]. On the owner's laptop: 1.05 s to pages,
   466 MB after scrolling, 0 slow frames; smooth on Linux too. Costs: +≈100 MB installer, a second process to
   supervise, Chromium security updates ship with Evrakçı's updates.
2. pywebview (WebView2 on Windows, Qt WebEngine on Linux): 2.2 s to pages, 525 MB; stutters on Linux. Fallback.
3. Tauri 2: Linux WebKitGTK problems, a Rust toolchain, sidecar update bug (reports 9, 10).

**How UI and backend talk**
1. **Renderer ↔ Electron main over Electron IPC; main ↔ Python over stdio, JSON-RPC 2.0** [call, picked]. No
   network port is opened, so no firewall prompt and no web page can reach the backend (report 1: the Zoom
   localhost hole); the extra hop costs well under a millisecond.
2. Local WebSocket with a token (what the spike used): simplest, but an open port on the PC; kept only for
   design and development (§7.4).
3. In-process Python (pywebview style): not possible with Electron.

## 5. Decided by the owner

- The suite direction and its "scalable" meaning (more job kinds, field kinds, bigger piles, later the local
  network) [owner].
- Separate UI and backend completely; UI swappable via the API [owner].
- React + TypeScript in Electron; Python backend [owner].
- Design on the web first; the same React code is the app (no second implementation) [owner].
- Sending stays with staff; job states/tags for sharing later [owner].
- No planted errors; never suggest destroying originals; batch sampling and ASLI GİBİDİR rules dropped [owner].
- Build more, document less [owner].

## 6. Architecture

```
┌───────────────── Electron app ─────────────────┐        ┌──────── Python backend ────────┐
│ Renderer: React + TypeScript                   │        │ evrakci.api   (JSON-RPC server) │
│   window.evrakci.call / on  (typed client)     │        │ evrakci.app   (jobs, undo,      │
│        │  contextBridge, no Node in renderer   │        │                kinds, checks)   │
│ Main process (TypeScript)                      │ stdio  │ evrakci.pipeline (today's core) │
│   starts/stops Python, forwards calls/events ──┼────────┼─▶ workers: OCR, export, render  │
│   serves page images: evrakci-img://           │        │   (separate processes)          │
└────────────────────────────────────────────────┘        └─────────────────────────────────┘
                 reads image files ◀──── cache folder on disk ◀──── written by the backend
```

### 6.1 Repository layout [call]

- `backend/` — the Python package (today's `src/evrakci` minus `ui/`): `pipeline/` unchanged at first, new
  `app/` (application layer, §6.3), new `api/` (the JSON-RPC server), `cli/` (kept; a second client of `app/`).
- `contract/` — the single description of the API: methods, parameters, results, events, errors, with the
  protocol version. TypeScript types and Python models are generated from it, and contract tests run on both
  sides. Format [builder]: JSON Schema or Pydantic-first with generated TS; one source, never two hand-written.
- `ui/` — React + TypeScript + Vite.
- `shell/` — Electron main and preload (TypeScript).
- `packaging/` — extended to bundle the frozen backend inside the Electron build.

### 6.2 The API

- **Transport:** newline-delimited JSON-RPC 2.0 on the backend's stdin/stdout; logs go to a file, never stdout.
- **Handshake:** `hello` returns `{protocol: "1.x", backend_version, capabilities[]}`. The UI refuses to run
  against an incompatible major version with a clear Turkish message. Changes within a major version are
  additive only (Neovim/LSP practice, report 1).
- **Four kinds of messages** (every method belongs to exactly one):
  - *queries* read state (`job.list`, `job.pages`, `job.documents`, `values.rows` …), no side effects;
  - *commands* change a job (`kontrol.cut`, `values.confirm` …) and are undoable; each returns the new
    revision and what changed;
  - *tasks* are long-running (`job.analyse`, `values.read`, `job.export`): they return a task id at once, then
    send `task.progress` events (throttled, ≤ 10/s), finish with `task.done` or `task.failed`; `task.cancel`
    reaches the worker process;
  - *events* the backend pushes (`thumb.ready`, `job.changed`, `task.*`).
- **Plain data only:** ids, numbers, strings, lists. Page images never cross the API; the backend writes them to
  the cache folder and the UI loads them through `evrakci-img://` (main serves files under the cache folder
  only).
- **Errors** carry a code, a Turkish message for staff and a technical detail for support ("never silent").
- **Chattiness rule:** design every call as if it were remote. No per-pixel or per-keystroke calls; the canvas
  sends a finished box, not a drag.

### 6.3 Backend layers

- `pipeline/` stays as it is: analysis, cuts, templates, reading, export, naming, settings, store.
- `app/` is new and holds what the UI holds today (§9): opening jobs, the undo history per job, the value
  review rows and counts, export preparation, template sync, the "why this key cannot act" reasons, job states.
  It calls `pipeline/`; it knows nothing about Qt, Electron or JSON.
- `api/` maps JSON-RPC methods to `app/` calls and back. Thin; no logic.
- **Undo** moves into `app/`: one history per job, snapshot-based like today's `JobController`, with named steps
  ("Kesim eklendi") so any UI can show them. It lives in memory, as today: closing the job or a backend
  restart clears it, and the job reopens at its last saved state (every command is saved at once) [call].
- **One owner of PDFium:** keep `PDFIUM_LOCK`; thumbnail rendering runs in a small pool of render processes so
  cold jumps get faster than the spike's single thread (≈ 0.5 s on the owner's laptop) [builder: pool size].

### 6.4 Concepts for growth (report 6) [call]

Names the code uses from the start, without building a framework:
**JobKind** (what kind of job: today only "Tarama yığını"), **Job**, **Template**, **FieldKind** (text today;
later number, date, tick box, IBAN…; an unknown kind falls back to text), **Field**, **Source** (scan batches
today; later Excel, TOBB PDF, pasted table), **Record** (a document today; later a row), **Value**, **Check**,
**Output** (split PDFs + index today), **EditLog** (the undo history plus who/when).
Pluggable now means **registries inside the code** (a JobKind or FieldKind is one module registered in one
place). No external plugins, no user-defined workflows. The shared shape is extracted when the second job kind
is built, not guessed now.

### 6.5 Job storage, format 3

Each job stays a folder, made ready for a share later (report 5):
- `job.json` with an envelope: `format`, `version: 3`, `id` (UUID), `kind`, `created`, `created_by`
  (user and PC), `revision` (counter). No stored state yet: whether a job is finished keeps being worked out by
  the backend from its exports, as today (`job_state`, `edited_after_export` in `pipeline/job.py`). States set
  by staff come with sharing (milestone 5) and are added to the format then, by an upgrade step [call].
- `batches/` — scans copied in once and never changed (today's folder name kept, so upgrading an existing job
  moves no files) [call].
- Exports keep going to the folder staff choose, as today (including the "Kontrol gerekenler" subfolder and the
  refusal to write into a non-empty folder) [call]. The job remembers its export folders and offers "Klasörü
  aç", so finished files are easy to find and take. No `outputs/` copy inside the job: retention deletes whole
  job folders, and exported files must never go with them.
- `history.jsonl` — append-only audit: who changed what, from which PC. It is not the undo history.
- Writes: temp file, then rename, then verify, with retry. Relative paths only. No SQLite inside job folders.
- **Upgrade chain:** loading a job or template runs `v1→v2→v3…` upgrade functions; old files are never refused.
  This fixes today's template loader, which refuses any version but the current one
  (`pipeline/templates/model.py:303`). A folder of old saved jobs and templates is kept as test data.

## 7. The UI

### 7.1 Technology [call unless marked]

React + TypeScript + Vite [owner]; React Aria Components for keyboard and accessibility behaviour (Apache-2.0);
the look is Evrakçı's own design tokens; TanStack Virtual for long grids (measured smooth at 1000 pages);
box drawing on pages with plain SVG or react-konva (MIT) [builder]; Playwright for UI and screenshot tests.

### 7.2 Shape of the app [call]

- A **home screen** listing jobs (state, kind, who made it, last change), with "Yeni iş" offering the job kinds.
  Today there is one kind; the screen is built for more.
- Opening a job shows that kind's screens. For "Tarama yığını" those are today's steps (Yükle, Kontrol,
  Şablonlar, Değerler, Dışa Aktar) plus Rehber, but **their look is redesigned**, not copied from the Qt UI.

### 7.3 How the look gets decided [call]

Round one froze mockups too early and copied them literally. This time:
1. For each screen, two or three clearly different directions are built as clickable React prototypes in the
   browser on fake data; the owner picks.
2. The picked direction is built for real against the fake backend, and the owner sees screenshots before it is
   connected and pushed.
3. Kontrol (the most used screen) goes first; the others follow its style.
The design direction itself (colours, type, density) is decided in that first step, not in this document.

### 7.4 Design mode and the fake backend

The UI has two transports behind one typed client: Electron IPC (the app) and a **fake backend** written in
TypeScript that implements the same contract with invented jobs and pages. `npm run design` opens it in a normal
browser with hot reload. The fake backend is checked by the same contract tests as the real one, so designs
cannot rely on things the backend cannot do. (A dev WebSocket to the real Python backend is also available for
development, never in the shipped app.)

## 8. Electron shell

- Main starts the frozen Python backend at launch, restarts it once if it crashes (with a visible notice and
  the job reopened), and stops it on quit; on Windows the backend is placed in a Job Object so it dies with
  the app (report 1: orphaned sidecars). Single-instance lock.
- Renderer: `contextIsolation` on, no Node access, a strict Content-Security-Policy, only `app://` and
  `evrakci-img://` origins; external links open nothing.
- Packaging: per-user install on Windows without admin (NSIS via electron-builder [builder]), a tarball or
  AppImage on Linux [builder]. The frozen backend ships inside the app's resources. Licence texts for Electron
  and Chromium are bundled; `gpl_check` and `shipped-packages.txt` also cover the Electron side.
- Updates: manual installers for now; Electron upgraded at least every major security release [call].
- Follow-up from report 12: Electron's first start on the owner's laptop took 24 s to the first thumbnails
  (pages were on screen at 4.3 s). Measure this in the first packaged build; suspected antivirus scanning.

## 9. What happens to today's code

- **Keep:** `pipeline/` and its tests; the CLI (moved onto `app/` so window and CLI share one core, as today).
- **Move into `app/`** (logic now in `ui/`): `degerler_model.py`, `disa_aktar_model.py`, `sablon_sync.py`,
  `sablon_read.py`, `yukle_info.py`, `refusals.py`, `rehber_content.py` (content, not layout), and the undo
  history in `controller.py`. Their tests move with them.
- **Qt UI:** frozen (bug fixes only) until the new UI covers the scan-pile job, then removed with `tests/ui`.
  Behaviours those tests protect that are logic, not layout, get API-level tests first [call].
- **Packaging:** cx_Freeze stays for the backend; vcpkg Tesseract, tur_best and the GPL checks stay; Inno Setup
  is replaced by the Electron installer [builder: when].
- **Docs:** `docs/ui-goal/` stays as history; nothing in it binds the new UI except the decisions the owner
  re-confirms.

## 10. Rules of thumb for round two [call, from round one and the research]

1. Something the owner can look at every few days; no phase of only documents.
2. Screenshots before push for any UI change; the owner approves looks, not specs.
3. Logic lives in the backend; a test fails if `ui/` imports anything but the contract client.
4. Every saved file has a version and old versions are upgraded, never refused.
5. Generalise from two real job kinds, not from guesses.
6. One short plan per change; research only when a decision needs it.
7. Never silent: every refusal, failure and skipped item says why, in plain Turkish.
8. Data stays on the PC or the office network; nothing is sent anywhere.
9. Paper originals are never called disposable; no planted errors, ever.
10. Measure on the owner's laptop (4 GB) before calling anything fast.

## 11. Milestones

1. **Walking skeleton:** `contract/`, `api/` with `hello`, `job.list`, `job.pages`, thumbnails; Electron shell;
   the React Kontrol grid showing a real job read-only; fake backend; packaged and run on the owner's laptop
   within the §3 budget. Includes the template upgrade-chain fix. Windows only; the Linux package follows in
   milestone 3, before the Qt UI (which has a Linux build today) is removed [call].
2. **Kontrol for real:** design directions → owner picks → cuts, rotate, delete, merge, undo/redo through the
   API; `app/` undo history; keyboard shortcuts.
3. **The rest of the scan-pile job:** Yükle, Şablonlar, Değerler, Dışa Aktar, Rehber, home screen; then the
   Qt UI is removed.
4. **Second job kind** (owner picks, e.g. filling or checking an Excel sheet from scanned documents): its own
   design document; the shared concepts in §6.4 are extracted here.
5. **Sharing on the office network:** job folder on a share, lock and take-over, job states (report 5).

## 12. Left to the builder

The contract format and code generation; NSIS/electron-builder details; render pool size; SVG vs react-konva;
the CSS approach; folder names inside `ui/`; how the fake backend's invented data is generated; log file
location and rotation.

## 13. Open for the owner

- Which job kind comes second (milestone 4).
- Whether the review of values should require an active check (retype or check digit) for key fields, as the
  field studies suggest (report 3); a product decision for milestone 3, not for the foundation.
