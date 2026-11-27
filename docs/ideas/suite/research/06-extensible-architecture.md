# Extensible document/data workflow architectures, and how they fail

Research note 06 for Evrakçı. Every claim carries a source link. Claims I could not check against a primary source are marked **(unverified)**. I read sources on 2026-11-27.

## 1. The short answer

The workflow tools that last (n8n, Node-RED, KNIME, NiFi, Camunda, Paperless-ngx) share the same small core: a **typed unit of data** moving through **named steps** that come from a **registry**, plus a **saved definition that names its own version**. The ones that hurt their users either expose too much of that machinery to non-programmers or let their plugin API grow until it can't change. Evrakçı should build that core in plain Python and register its parts with a decorator for now, with no third-party plugin loading. It should store jobs and templates as versioned JSON with a chain of upgrade functions. The next abstraction should come from the second real job kind, not be designed ahead of it.

## 2. Patterns, with real systems

### 2.1 Plugin systems: registries and entry points

- **KNIME.** Each node is a `NodeFactory` that creates a model, a dialog and a view. Nodes are registered through an Eclipse extension point in `plugin.xml` so that "the node is discoverable by the framework and will be displayed in the node repository" ([KNIME quickstart](https://docs.knime.com/latest/analytics_platform_new_node_quickstart_guide)). The useful lesson: one factory per node supplies both runtime logic and UI, so a new node is one isolated package.
- **Node-RED.** A node is a pair of files: a `.js` file for runtime behaviour and an `.html` file for "the node's properties, edit dialog and help text". Both call `RED.nodes.registerType` with the same name ([Node-RED: node HTML](https://nodered.org/docs/creating-nodes/node-html), [JS file](https://nodered.org/docs/creating-nodes/node-js)). Splitting runtime from editor this way matches Evrakçı's planned split between UI and backend. A known failure is that a node silently fails to appear when the two names don't match ([Node-RED forum](https://discourse.nodered.org/t/custom-node-is-not-adding-to-node-red/21475)). The fix is to keep **one** type id as the single source of truth.
- **Python mechanics.** Entry points let an installed package "advertise components it provides to be discovered and used by other code" ([PyPA entry points spec](https://packaging.python.org/specifications/entry-points/)). `pluggy`, "the crystallized core of plugin management and hook calling for pytest", adds hook specifications that check plugin signatures ([pluggy docs](https://pluggy.readthedocs.io/en/stable/)). Evrakçı already ships an `entry_points.txt` for its CLI (`src/evrakci.egg-info/entry_points.txt`). Both mechanisms are available, but neither is needed until outside parties write plugins.

### 2.2 Pipeline and stage models

- **Apache NiFi.** The unit is the FlowFile: a content pointer plus key/value attributes. The FlowFile repository is a write-ahead log. A provenance event is recorded each time a FlowFile is received, routed, cloned, modified, sent or dropped ([NiFi In Depth](https://nifi.apache.org/nifi-docs/nifi-in-depth.html), [NiFi overview](https://nifi.apache.org/nifi-docs/overview.html)). This is the clearest worked example of "records + steps + audit trail". The NiFi wiki also calls the provenance repository API private and subject to change ([NiFi wiki](https://cwiki.apache.org/confluence/spaces/NIFI/pages/61310698/NiFi+Components)), which shows that a mature project keeps some internals deliberately non-pluggable.
- **Apache Tika.** All format diversity sits behind one method, `parse(InputStream, ContentHandler, Metadata, ParseContext)`, which "hides the complexity of different file formats and parsing libraries". It streams, so large files need little memory, and metadata passes "both in and out of the parser" ([Tika parser API](https://tika.apache.org/3.0.0/parser.html)). The equivalent for Evrakçı is a **Source** port with one narrow method that yields records plus metadata.
- **Unstructured.io.** Every parser emits the same element vocabulary (`Title`, `NarrativeText`, `ListItem`, `Table` with `text_as_html`, and so on) with shared metadata such as `filename`, `coordinates` and `parent_id` ([Unstructured document elements](https://docs.unstructured.io/open-source/concepts/document-elements)). The lesson is that a **common intermediate record shape** is what keeps N sources × M outputs from turning into N×M adapters.
- **Paperless-ngx.** Its workflow model is the most relevant one for non-technical users. There are five fixed trigger types (Consumption Started, Document Added, Document Updated, Scheduled, Manual), filters, and a closed list of action types (assignment, removal, email, webhook, trash, password removal…). Actions apply "sequentially by sort order", and some actions only work with some triggers ([Paperless-ngx usage docs](https://raw.githubusercontent.com/paperless-ngx/paperless-ngx/dev/docs/usage.md)). Users choose from closed lists; they never write expressions. Its custom-field types are also a short, closed list: Text, Boolean, Date, URL, Integer, Number, Monetary, Document Link, Select (same source).

### 2.3 Declarative job and template definitions

- **Docassemble** writes interviews as YAML "blocks separated by `---`". The engine works backward from an end goal to whichever question supplies a missing variable. Its own docs say the hard part for authors is YAML itself, not the Python ([Docassemble interviews](https://docassemble.org/docs/interviews.html)). Docassemble is aimed at lawyers and developers, not clerks. Hand-written YAML is a format for developers and agents, not for Evrakçı's users.
- **LibreOffice mail merge** is the oldest version of "fill a document from a sheet". Column headers become fields, the data source has to be *registered* first, and a merge uses one data source ([LibreOffice Writer Guide, Mail Merge](https://books.libreoffice.org/en/WG24/WG2414-MailMerge.html)). The recurring user failures (blank data source, field names printed instead of values) come from that registration indirection ([LibreOffice bug 76226](https://www.libreoffice.org/bugzilla/show_bug.cgi?id=76226), [mailing list](https://www.libreoffice.org/lists/users/2015/msg06375.html)). Evrakçı should bind a spreadsheet to a template directly, inside the job, with no separate registration step.

### 2.4 Schema-driven forms and field-type registries

- **react-jsonschema-form** separates *widgets* (the input element) from *fields* (the wrapper that holds label and state). Custom ones are registered by name in a `registry` and referenced from a JSON `uiSchema`, because "JSON cannot carry functions" ([RJSF custom widgets and fields](https://rjsf-team.github.io/react-jsonschema-form/docs/advanced-customization/custom-widgets-fields/)).
- **JSON Forms** picks a renderer for each element through *testers* that return a rank, and the highest rank wins ([JSON Forms custom renderers](https://jsonforms.io/docs/tutorial/custom-renderers)). Users report having to raise a custom renderer's rank to beat the built-ins ([JSON Forms forum](https://jsonforms.discourse.group/t/find-the-rank-of-a-given-renderer/1987)). Rank-based dispatch is powerful but hard to see into. A plain `kind → class` dictionary is easier to debug.
- **FormKit** describes its schema as "JSON-serializable", so forms can be stored "in databases, files, or even QR codes", with conditionals and expressions ([FormKit schema](https://formkit.com/essentials/schema)).
- **Airtable** documents every field type with a cell-value format and an options format (dates as ISO 8601, percent as a decimal, checkbox as `true` or absent). It also warns that it "may add more field types in the future and this will not be considered a breaking change", so consumers must handle unknown types ([Airtable field model](https://airtable.com/developers/web/api/field-model)). That is the contract Evrakçı's field registry needs: every field kind defines how its value is stored, how it is validated, and how it is shown, and unknown kinds degrade to text instead of crashing.

### 2.5 Ports and adapters

Cockburn's intent is to "allow an application to equally be driven by users, programs, automated test or batch scripts" and be "developed and tested in isolation from its eventual run-time devices and databases". His rule is "code pertaining to the inside part should not leak into the outside part" ([Cockburn, Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)). For Evrakçı the ports are: document/data **sources**, the **OCR engine**, **outputs** (PDF/Excel/Word writers, printer), **storage** of jobs and templates, and the **UI** (through the planned separate API). The core never imports Qt, pdfium or openpyxl.

### 2.6 Event-sourced history (undo and audit)

- **Fowler** lists the gains: a complete change log, rebuilding state by replay, temporal queries, and reversing wrong events. He also lists the costs: replays must not re-send to external systems, external lookups must be recorded, code changes complicate reprocessing, and "this stuff can get very messy" ([Fowler, Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html)).
- **Industry evidence.** Interviews with 25 engineers on 19 event-sourced systems found schema evolution to be the hardest challenge ("versioning in event sourced systems is a big problem"). The study recommends starting with versioned events and weak schema, moving to upcasting later, and adding event sourcing only once the domain is stable ([Overeem et al., arXiv:2104.01146](https://ar5iv.labs.arxiv.org/html/2104.01146)). Greg Young's book makes the same case for weak-schema JSON ([Young, Versioning in an Event Sourced System](https://leanpub.com/esversioning/read)).
- **OpenRefine** shows a lighter version that works for non-programmers. Every operation goes into a per-project history that is saved with the project. Clicking an earlier step reverts to it, and a list of operations can be **extracted as JSON and applied to another project**. The limitation: "Edits to a single cell… can't be replicated" ([OpenRefine manual, History](https://openrefine.org/docs/manual/running#history-undoredo)). That is close to what Evrakçı needs: an **append-only log of review edits** for undo and audit, kept next to a normal saved snapshot of the job. The log is not the system of record.

### 2.7 Low-code platforms (Power Automate / Power Apps, n8n)

- Across about 5,000 Stack Overflow posts on nine low-code platforms, 75.9% of questions had no accepted answer ([Alamin et al., arXiv:2103.11429](https://arxiv.org/pdf/2103.11429)). That is developer-side data.
- A usability study of low-code BPM tools including Power Automate measured learnability, error rates and cognitive load for non-technical "citizen developers" ([EJCSIT 2025 abstract](https://vufind-test.katalog.k.utb.cz/SummonRecord/FETCH-LOGICAL-c1053-3b67629fb058022e48b4c230ece0a98b2f2864d55ca528e3cb886f313ce616a33)). **(unverified: I read only the abstract, not the findings.)**
- Microsoft community users describe Power Automate's error messages as "basically worthless" ([Power Automate community thread](https://jgvjg48436.lithium.com/t5/General-Power-Automate/Why-is-Power-Automate-so-difficult/m-p/2825477)). This is anecdotal.
- I did not find a primary source on Power Apps' model for non-technical authors. **(unverified; not covered further.)**

## 3. How these systems fail

**Inner-platform effect.** Papadimoulis defines it as a system "so customizable that it ends becoming a poor replica of the platform it was designed with". His example is a loan system whose "Data Structure Modeler" stored tables, fields and types as rows. It was so complex that a programmer had to be hired to add one form field ([The Daily WTF](https://thedailywtf.com/articles/The_Inner-Platform_Effect)). The database form of this is Entity-Attribute-Value, which Karwin lists as an antipattern ([SQL Antipatterns, O'Reilly](https://www.oreilly.com/library/view/sql-antipatterns/9781680500073/f_0039.html)). In one clinical study, attribute-centred queries ran about 3 to 5 times slower than on a conventional schema ([Chen et al., PMC79043](https://pmc.ncbi.nlm.nih.gov/articles/PMC79043/)).

**Configuration complexity.** Hadlow's "configuration complexity clock" goes from hard-coding, to config files, to a rules engine with a GUI (which non-technical users still can't run), to a home-grown DSL. It ends with "hard coding everything, except now in a much crappier language". His conclusion: "At a certain level of complexity, hard-coding a solution may be the least evil option" ([Hadlow](http://mikehadlow.blogspot.com/2012/05/configuration-complexity-clock.html)).

**Over-generalising too early (YAGNI).** Fowler names four costs of presumptive features: build, delay, *carry* (complexity that slows unrelated work) and repair. He estimates that at least two thirds of them turn out not to be needed. He is explicit that YAGNI does *not* forbid work that makes code easier to change ([Fowler, Yagni](https://www.martinfowler.com/bliki/Yagni.html)). On abstraction, Metz writes that "duplication is far cheaper than the wrong abstraction". Her warning sign is shared code that keeps gaining parameters and conditional paths ([Metz, The Wrong Abstraction](https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction)).

**Plugin API churn.** Firefox's old XUL/XPCOM add-on API was open enough to block browser changes. Mozilla dropped it in Firefox 57 for the much narrower WebExtensions API. Extensions that changed core components broke, and some features could never be ported ([nullprogram, 2018](https://nullprogram.com/blog/2018/09/20/), [Red Hat announcement](https://access.redhat.com/announcements/3365141), [ghacks](https://www.ghacks.net/2015/08/23/reactions-to-mozillas-announcement-about-upcoming-firefox-add-on-changes/)). The lesson is that a wide plugin surface becomes a promise you can't keep. Publish a narrow one, and only when someone outside actually needs it.

**Versioning saved definitions.** Two mature approaches stand out:
- *Pin the version and keep old code.* n8n workflows "continue to use the node version they were created with". New workflows get the latest version. Small changes use "light versioning" (one implementation with a version list), and large ones use separate per-version implementations ([n8n node versioning](https://docs.n8n.io/integrations/creating-nodes/build/reference/node-versioning)). When a node is removed outright, "workflows that use a removed node will fail" ([n8n deprecated and versioned nodes](https://docs.n8n.io/integrations/builtin/deprecated-and-versioned-nodes/)).
- *Pin the version and migrate explicitly.* In Camunda, "running process instances will continue to run in the version they were started in" ([Camunda 7 versioning](https://docs.camunda.org/manual/latest/user-guide/process-engine/process-versioning/)). Migration needs a mapping plan, is all-or-nothing, and cannot change an element's type ([Camunda 8 migration](https://docs.camunda.io/docs/components/concepts/process-instance-migration/)).

**Performance of generic layers.** The EAV numbers above are one example. Tika's streaming design is another: it exists so that generic parsing does not mean loading the whole document into memory ([Tika](https://tika.apache.org/3.0.0/parser.html)). Generic record pipelines must stay lazy (page by page), or a 1,000-page scan pays for the abstraction.

## 4. Staging: extract from real cases, or design up front?

The evidence mostly favours extraction.
- Fowler has "always seen this work badly in practice" when a platform is built first ("FoundationFramework"), because the real needs are unknown and it ends up "with far more capabilities than are really needed" ([Fowler, FoundationFramework](https://martinfowler.com/bliki/FoundationFramework.html)). Instead, "you start by not trying to build a platform, but by building an application", factoring out duplication into a proto-platform until it stabilises ([Fowler, HarvestedPlatform](https://martinfowler.com/bliki/HarvestedPlatform.html)).
- Rails was extracted from Basecamp, not designed separately ([Rails blog, 2005](https://rubyonrails.org/2005/3/11/the-story-behind-rails-at-oreilly), [DHH, Red Gate interview](https://www.red-gate.com/simple-talk/opinion/geek-of-the-week/david-heinemeier-hansson-geek-of-the-week/)).
- The rule of three (attributed to Don Roberts, popularised in Fowler's *Refactoring*): put up with duplication the second time and extract on the third ([Wikipedia, Rule of three](https://en.wikipedia.org/wiki/Rule_of_three_(computer_programming))). Critics note that the count matters less than whether the duplicated code represents the *same* concept ([Industrial Logic](https://industriallogic.com/blog/spot-and-coincidental-duplication)).

The evidence for some up-front design is weaker but real:
- YAGNI exempts work that makes code easier to change ([Fowler, Yagni](https://www.martinfowler.com/bliki/Yagni.html)). Ports, a format version field and a registry dictionary are cheap and easy to undo, so they count as that kind of work.
- The event-sourcing study warns that stored formats are the expensive thing to get wrong later ([Overeem et al.](https://ar5iv.labs.arxiv.org/html/2104.01146)). That argues for settling the **saved-file envelope and versioning scheme** now, even while the inner abstractions stay open.

My synthesis: **design the boundaries and the file envelope up front; extract the inner abstractions (Step, FieldKind behaviour, Output) from job kind #2, and confirm them with #3.** For Evrakçı, a good #2 is "check or fill an Excel sheet from scanned documents". It reuses scan → split → OCR → review but swaps the output (an Excel sheet instead of split PDFs) and adds a second source (an existing spreadsheet). A good #3 is a form fill from TOBB data with no scan at all, which tests whether "Source" is really general.

## 5. Recommendation for Evrakçı

### 5.1 Core concepts and their names

Keep the Turkish user-facing words in the UI (Şablon, Değerler, Kontrol, Dışa aktar). Use these names in backend code:

| Concept | What it is | Analogue |
|---|---|---|
| `JobKind` | A registered recipe: which sources, steps and outputs, and which UI screens it needs. Code, not user data. | n8n node type, KNIME node factory |
| `Job` | One run of a JobKind: inputs, records, review state, outputs. Saved as a versioned file. | NiFi flow instance, Camunda process instance |
| `Template` (Şablon) | A user-authored, versioned definition of fields and where to find them (boxes on pages, sheet columns, form-field names). | Docassemble interview, mail-merge main document |
| `FieldKind` | A registered value type: `text`, `number`, `date`, `checkbox`, `iban`, `tckn`, `table`, `signature`… Each defines parse, validate, normalise, display and to/from JSON. | Airtable field type, RJSF widget plus field |
| `Field` | One field instance in a Template: key, label, kind, kind options, locator(s), required. | — |
| `Source` | A port that yields `Record`s from scans, Excel, PDF exports or pasted tables. | Tika Parser |
| `Record` | The common unit: one logical document or row, with page refs, `Value`s per field, and provenance. | NiFi FlowFile, Unstructured element |
| `Value` | Raw reading + normalised value + confidence + problems + `edited` flag. | Evrakçı's existing `SectionReading` |
| `Check` | A pure function over a Record that returns problems (IBAN mod-97, required, cross-field). | Paperless filter |
| `Output` | A port that writes Records: split PDFs, filled Excel/Word/PDF, labels, index sheet. | Paperless action |
| `EditLog` | An append-only list of review edits (who, when, field, old → new) used for undo and audit. It is not the source of truth. | OpenRefine history |

### 5.2 What to make pluggable now and what to leave for later

**Now (cheap, isolated, in-repo only):**
- `FieldKind` registry: a dictionary from `kind` id to class, filled by a decorator. This is where growth will happen most often (IBAN, dates, tick boxes), and each kind is a small, self-contained, testable unit.
- `Source` and `Output` as ports, with today's scan source and PDF+Excel output as the first adapters.
- A single `kind` string as the shared type id between the backend and the separate UI (a lesson from Node-RED's name-mismatch problem). The UI looks up an editor and display widget by the same id and falls back to plain text for unknown kinds (Airtable's rule).

**Later (only once two or three real cases exist):**
- `Step` / `Check` as a general pipeline graph. Keep each JobKind's steps as ordinary Python until #2 and #3 show which steps are actually shared.
- User-defined JobKinds. Users define **Templates** (fields and locations) and choose from a **closed list** of options, as Paperless does. They never build pipelines, write expressions or edit YAML.
- Third-party plugins through entry points or pluggy. Skip these until someone outside the codebase writes one. They bring the API-stability obligations seen with Firefox.

### 5.3 How to version saved jobs and templates

1. Use the same envelope for every saved file: `{"format": "evrakci.template", "version": N, "kind_versions": {"iban": 1, ...}, ...}`. Evrakçı already writes `format`/`version` (`src/evrakci/pipeline/templates/model.py`, `src/evrakci/pipeline/job.py`).
2. **Upgrade on load, write only the current version.** Keep a chain of pure functions `upgrade_1_to_2(dict) -> dict`, ... and run them in order. This is the upcasting route the event-sourcing literature recommends before heavier rewrites ([Overeem et al.](https://ar5iv.labs.arxiv.org/html/2104.01146)). Today `template_from_dict` *rejects* any version other than the current one, so the first format change would lock users out of their own templates. Fix that before the first schema change.
3. **Pin running Jobs to the Template revision they started with** (the Camunda/n8n rule). Store a content hash or revision with the job. Evrakçı already computes a template content hash in `model.py`. Editing a template must not silently change a half-reviewed job.
4. Give each FieldKind's options their own version (n8n's "light versioning"), so a new IBAN option doesn't bump the whole template format.
5. Keep a `tests/fixtures/saved/` folder holding real files of every old version, with a test that loads each through the upgrade chain. **(This is a recommendation, not a sourced practice.)**
6. Write a backup before upgrading in place, and never drop unknown keys. Preserve them, in line with weak schema ([Young](https://leanpub.com/esversioning/read)).

### 5.4 Five traps to avoid

1. **Building a "Data Structure Modeler".** Don't give users a general schema/pipeline editor or an EAV-style field store. That is the inner-platform effect ([Daily WTF](https://thedailywtf.com/articles/The_Inner-Platform_Effect)). Users choose a field kind from a short list and draw a box.
2. **Moving round the configuration clock.** Watch for "if this rule could just be an expression…". Once logic needs conditions, write it in Python as a new `Check` or `JobKind` (an agent can do this in a small isolated change) instead of growing a DSL ([Hadlow](http://mikehadlow.blogspot.com/2012/05/configuration-complexity-clock.html)).
3. **One shared `process()` with growing flags.** If adding job kind #2 means passing `mode=` parameters through the existing pipeline, that is Metz's wrong abstraction. Duplicate first and extract at #3 ([Metz](https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction)).
4. **Saved files that only the current build can open.** A strict version check without an upgrade chain, or templates edited under a running job, will hurt users the first time the schema changes. Pin the version and upgrade on load ([n8n](https://docs.n8n.io/integrations/creating-nodes/build/reference/node-versioning), [Camunda](https://docs.camunda.org/manual/latest/user-guide/process-engine/process-versioning/)).
5. **Making the event log the source of truth, or the abstraction eager.** Full event sourcing brings replay side effects and evolution pain ([Fowler](https://martinfowler.com/eaaDev/EventSourcing.html), [Overeem et al.](https://ar5iv.labs.arxiv.org/html/2104.01146)). Keep a snapshot plus an edit log. Likewise, keep generic Record pipelines lazy and page-streamed, so a 1,000-page scan doesn't pay for the generality ([Tika](https://tika.apache.org/3.0.0/parser.html), [EAV performance, PMC79043](https://pmc.ncbi.nlm.nih.gov/articles/PMC79043/)).

## 6. What I could not verify

- The findings of the Power Automate citizen-developer usability paper (abstract only).
- Power Apps' authoring model for non-technical users (no primary source read).
- Karwin's own wording on EAV performance. The 3–5× figure comes from a separate clinical study.
- The tie-break when JSON Forms renderers have equal rank (one secondary source only; not used above).
- Paperless-ngx details come from the docs source file on GitHub (`docs/usage.md`, dev branch), not the rendered site, which returned 403.
