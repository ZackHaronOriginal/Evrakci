# Suite research (2026-11-27): summary

**Status: research for a decision, not decided.** Seven agents researched in parallel, each with sources cited inline
and unverified points marked. The reports were not re-checked claim by claim; treat single striking numbers as leads.

| # | Report | One-line finding |
|---|---|---|
| 1 | [UI/backend separation](01-ui-backend-separation.md) | Separate completely in code, not necessarily in processes: a protocol-shaped API inside the app; a pipe only when a non-Python UI exists. |
| 2 | [Tech stack](02-tech-stack.md) | Keep Python for the backend; no permissive replacement for OCRmyPDF elsewhere; AI agents do better in Python; a .NET UI can sit on the Python backend later. |
| 3 | [Field studies](03-field-studies.md) | "Look and press OK" barely catches errors; machine values anchor reviewers; paper persists for real reasons. |
| 4 | [Prior art](04-prior-art.md) | Nobody covers this for a small offline Windows office; open-source DMS are Linux servers; fill tools break leading zeros and dates. |
| 5 | [Local network sharing](05-local-network-sharing.md) | Local work plus check-out/check-in on a shared folder; no live database on a share; no server for offices without IT. |
| 6 | [Extensible architecture](06-extensible-architecture.md) | Pull the abstraction from 2-3 real job kinds; design only boundaries and saved-file formats up front; version every file. |
| 8 | [Introduction and warm-up](08-introduction-and-warm-up.md) | Naming chambers already using it beats features; demo on their own pile, one job; tours get skipped, so a sample job, teaching empty screens and printed sheets; an 18-step plan for one chamber. |
| 9 | [React UI on Python](09-react-ui-on-python.md) | pywebview shell around a React/Vite UI (Python stays the only native language, WebView2); Tauri 2 + Python sidecar as plan B; versioned JSON-RPC, thumbnails as files; measure first. |
| 10 | [UI framework comparison](10-ui-framework-comparison.md) | Scored head-to-head: React in pywebview and React in Electron tie (56/60); Tauri 51, Flutter 49, PySide6 QML 48, Avalonia 46; MAUI, WinUI/WPF and Qt C++ out. |
| 11 | [What big products use](11-what-big-products-use.md) | Most big apps (Notion, Slack, VS Code, Figma, 1Password, Teams, new Outlook) use web UIs; more moved to web than away; about half keep a separate native core; Calibre and Anki are the closest matches. |
| 12 | [Shell measurements](12-shell-measurements.md) | On a 4 GB Windows laptop Electron started in 1.05 s (pywebview 2.2 s), used 466 MB after scrolling (pywebview 525) and both scrolled smoothly; on Linux only Electron was smooth. **Decision: Electron.** |
| 7 | [Adoption and physical workflow](07-adoption-and-physical-workflow.md) | Paper prep is the hidden cost; usefulness and fit with current work drive adoption; champions, small wins, a 13-step playbook for office heads. |

## Where the reports agree

- **Backend owns everything that is not drawing:** commands with undo, job state, validation, progress and cancel.
  Plain data across the boundary; page images as ids or file paths. (1, 2, 6)
- **Version every saved file and upgrade old ones on load.** Today templates refuse any other version
  (`src/evrakci/pipeline/templates/model.py:303`), so the first format change would lock users out. (5, 6)
- **A job is a self-contained folder:** a unique id, scans written once, small JSON files written safely, a fixed
  `outputs/` folder, a history of who changed what from which PC. Ready to sit on a shared folder later. (5, 6)
- **Generalise from real cases, not up front.** Build the second job kind, then extract what is shared. (2, 6)
- **Review must be active for key fields** (retype or check digit), low-confidence fields left empty, rule checks,
  identifiers exported to Excel as text. (3, 4)
- **Fit the office as it is:** copier scan folders, USB, existing Excel; defaults that copy current naming; a first job
  that pays off in a day; roll out one job at a time with before/after measurement. (3, 4, 7)

## Where they disagree

- **One process or two.** Report 2 suggests running the backend as a separate process from the start. Report 1 warns
  (xi-editor retrospective) that a process boundary is costly for fine-grained screens and suggests an in-process,
  protocol-shaped API with OCR in worker processes, adding a pipe only when needed.

## Open points to verify before relying on them

- PDFsharp 6.5+ listed as AGPL on NuGet (no announcement found); QuestPDF's licence excludes public-sector bodies
  (whether a chamber counts is unclear).
- Whether the 2020 official-correspondence regulation and Devlet Arşivleri digitisation rules bind TOBB chambers.
- The AI-agent benchmark numbers (Python 70 % vs C# 40 %) come from one benchmark.

## Owner rulings on the findings (2026-11-27)

- **Rejected:** planting known wrong values to measure reviewers (report 3). These are real official documents; a
  planted error could leave the office. Not to be built in any form.
- **Wanted:** how to introduce the app and warm an office up to it, treated as important as adoption: report 8.
- **Dropped** (owner): building in batch sample checks and the ASLI GİBİDİR rules (report 7). Kept: Evrakçı never
  suggests destroying originals; what institutions do with paper is their responsibility.
- **UI technology:** the owner would like a React (npm) UI, being used to it and because good UI tooling and skills
  exist for the web. To be researched against the Python backend before deciding.
- **Shell (decided 2026-11-27): Electron.** React + TypeScript UI in Electron, Python backend as a separate
  process, one versioned JSON-RPC bridge. Measured on the owner's 4 GB Windows laptop and on Linux (report 12).
