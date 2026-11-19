# Context for every research agent

**Product:** Evrakçı — an open-source, local-first desktop app (PySide6/Qt 6, Windows first, Linux/macOS too)
for office staff at Turkish chambers of commerce. Turkish UI. It turns a pile of scanned paper (100–800 pages)
into split, OCR'd, well-named PDFs. Six tabs: Yükle (jobs & scan batches), Kontrol (a page-thumbnail
timeline where staff check and fix where documents split: QR separators, filters, manual cuts; undo/redo),
Şablonlar (template editor: draw variable boxes on an example page), Değerler (review table of values read by
OCR; accept suggestions, type corrections), Dışa Aktar (export PDFs + Excel index), Rehber (scanning guide).

**Users:** non-technical office staff, often older, some with weaker eyesight, working long sessions (1h+),
keyboard-heavy, on ordinary office PCs with 1366×768–1920×1080 monitors. Human-in-the-loop: software suggests,
staff confirm; nothing may be silently wrong.

**Goal of the research:** collect solid rules and hard data (numbers, specs, durations, curves, sizes, contrast
ratios, citations) to later write ONE goal prompt for a completely new UI look. Not a rehash of opinions:
concrete, citable, applicable to a dense desktop productivity tool built in Qt.

**Output rules:** write Markdown in English to your assigned file in /home/user/Evrakci/docs/research/.
Structure: TL;DR (10 bullets max) → detailed sections → "Rules we should adopt for Evrakçı" (numbered,
each rule concrete and testable) → "Qt/PySide6 feasibility notes" where relevant → Sources (URLs, with the
date you accessed them). Cite sources inline as [n]. Prefer primary sources (official design-system docs,
published guidelines, research papers, Nielsen Norman Group, W3C). Mark anything you could not verify as
"(unverified)". Do not invent numbers. 1,500–4,000 words. Do not edit any other file in the repo; do not
commit or push.

**Tools:** use web search/fetch. If WebSearch isn't loaded, load it with ToolSearch ("select:WebSearch"), or
use the Exa tools (ToolSearch "exa"), or the web-fetch agent type for reading pages.
