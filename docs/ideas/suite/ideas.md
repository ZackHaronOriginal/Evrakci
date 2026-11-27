# Evrakçı as a suite: the ideas, organised

**Status of everything below: ideas to talk about. Nothing here is decided, scheduled or approved for implementation.** The owner said so explicitly in a follow-up.

This is an interpretation of the owner's own message and of a follow-up message, written by the assistant of the session that built the standalone tool. That assistant had not seen the Evrakçı codebase. It adds structure and questions; it adds no requirements. Where it and the owner's message differ, the owner's message is right. In this public copy the owner's words are paraphrased, not quoted.

## 1. Direction: Evrakçı becomes a suite

- Today Evrakçı is mostly about reading documents.
- The owner wants it to be common ground for several tools: a suite that hosts several tools, of which document reading is one.
- Tools mentioned or implied: document reading (existing), a print-template library, spreadsheet/data import, document editing, and export to spreadsheet or PDF.
- The standalone Member Search / Bilgi Formu tool is inspiration only: an example of the kind of work meant. Evrakçı does not have to copy it. (Corrected 2026-11-27 by the owner.)

## 2. Print-template library

The trade chamber regularly prints documents with fixed sizes and layouts. Examples the owner gave:

| Template | Details given |
|---|---|
| A5 sheet | Oda sicil numarası, then ticaret sicil no, company name in the middle |
| Folder label | Printed, cut out and pasted onto a folder; it could carry a folder name or something else |
| Binder spine | A large printed strip for the side of a binder, with oda sicil no or ticaret sicil no at the bottom |
| EK-1 Bilgi Formu | Already built in the standalone tool (A4-style form, one per person) |

The owner says there are many templates like these, and the template files exist at the chamber. The idea is a library of them inside the suite so any of them can be printed when needed.

The owner does not have these template files at hand right now. Only the EK-1 Bilgi Formu is in this folder. The templates themselves are a topic the owner wants to discuss with the Evrakçı session.

What the examples have in common: a fixed physical size, a handful of fields placed at fixed positions, values that come from member/company data, and often several items per printed sheet that are cut apart afterwards.

## 3. Data in: predefined sources and pasting a spreadsheet

- Other programs the office uses export Excel files and other kinds of data.
- Two ways to handle them:
  1. **Predefined mappings** for known exports.
  2. **Generic import**: paste or load a spreadsheet, Evrakçı reads its headers, and the owner creates their own template from it. The owner reads the headers and maps them to template fields themselves.
- The stated reason for the generic route is data privacy: the owner can build a template around their own data without that data being shared with whoever builds the predefined ones.

## 4. Example spreadsheet and an editing playground

A further idea from the follow-up message, paraphrased: put an Excel sheet in, have an editing playground around it, connect spreadsheet data easily and create new files from it, the way the standalone tool does.

One way to read it:

- Evrakçı ships with (or lets the owner load) an example spreadsheet.
- A playground area lets the owner open a document or template, connect spreadsheet columns to places in it, edit freely, and produce new files from the result.
- It is the same thing the standalone tool does for one fixed workbook and one fixed form, opened up so the owner can do it with any spreadsheet and any document.

A made-up workbook with the same two sheets and headers the standalone tool expects could serve as a starting example.

The owner called this a maybe. How it relates to the template library (the same feature, or a separate free-form area) is open.

## 5. Editing and output

- Document editing, and exporting as spreadsheets or PDF, for all kinds of documents, could live inside Evrakçı too.
- The owner wants documents to be easy to edit. In the standalone tool this means: every filled value can be corrected in place, corrections are kept per person, and they flow into print and export.

## 6. What the standalone tool already shows

Details are in `member-search-reference.md`. In short, it already does one full instance of the pipeline the suite would generalise:

`spreadsheet in → headers recognised → records → fixed-layout template filled → edit in place → print / PDF / Excel out`, entirely offline, with auto-save.

One way to read the ideas is: generalise each stage of that pipeline so the Bilgi Formu is just one template among many, and member workbooks just one data source among many.

## 7. Data and privacy

- Evrakçı holds data locally and does not publish anything, so real member data living inside Evrakçı on the owner's machine is fine.
- This handoff folder contains no real member data for a simpler reason: the session that produced it was never given any. The standalone tool was built and tested on synthetic data from its own sample generator, and the only real file shared was the blank EK-1 template.
- The property worth keeping is that data stays on the machine. The standalone tool does this by running fully offline.

## 8. Questions for later

These are kept for whenever the ideas are picked up. They are not a to-do list and don't need answering now.

Suite shape
1. What is Evrakçı built with and how is it run (desktop app, local web app, hosted)? This decides whether the offline single-file approach carries over or gets replaced.
2. Should tools share one data store (one member list used by reading, templates and forms), or stay independent?
3. Does the existing document-reading output (fields extracted from documents) feed the templates directly? That would connect the two halves: read a document, then print a label or form from it.

Template library
4. How are new templates created: by a developer in code, by the owner in a visual editor, or by importing an existing Excel/Word file as the layout (the way EK-1 works now)?
5. Which templates matter most? The owner named the A5 sheet, folder label and binder spine. Exact sizes and layouts would come from the real template files, which the owner doesn't have at hand yet.
6. Label sheets: several per page with cut marks, or one per page?
7. Which printers and paper are used? A5 and long binder strips may need specific page setups.

Data import
8. Which source programs produce the exports, and in what formats? A list with one sample (fake data) per source would let predefined mappings be built.
9. For the generic paste route, should a saved mapping be reusable next time the same headers appear?
10. Where do user-made templates and mappings live, and can they be shared between computers at the chamber?

Playground
10a. Is the editing playground the template editor itself, or a separate free-form space next to a fixed template library?
10b. What would creating new files from it produce: filled copies of a template per row, one merged document, or both?

Storage
11. The standalone tool stores everything in the browser on one computer, with a manual backup file. How does Evrakçı store data locally today, and would these tools use the same store?
12. Any rule about where TC kimlik numbers may be stored or printed?

Scope
13. OCR was dropped for the standalone tool as too much work. Evrakçı already reads documents, so does that existing capability replace the need for it?
14. (Removed 2026-11-27: the member tool is inspiration only, not something to port.)

## 9. More from the owner (2026-11-27, paraphrased)

**Direction.**
- Generalise: today Evrakçı is made for one job (scan a pile, split it, read values, export). It should become a
  general tool for the chamber's document and photocopy work, for everything a chamber needs there.
- It does not try to replace PDF editors. It handles specific, repeated office jobs that are done by hand today.
- It is a manual-job replacer, so the groundwork must take future additions well and scale a lot. More QoL features
  will keep coming.
- It must not burn people's heads: the jobs should get easier, not more complicated.
- Round one lesson the owner agreed with: focus on building the product, less on rules, audits and documents.

**New ideas.**
- **Check or fill a spreadsheet from real documents.** Scan the documents and give Evrakçı an Excel template. OCR puts
  the values into the right cells, or checks the values already there against the documents and shows mismatches.
- **Easy editing on the document itself,** in the spirit of the HTML tool: tick boxes, type into fields on the form.
- **Data from several places into one document.** Download Excel data from TOBB, take other data from elsewhere, and
  fill it into a document (Excel, Word, ending as PDF).
- **Examples of manual work to replace:** checking a document by hand against the real documents; scanning a large
  number of documents only to send them off one by one; collecting data from TOBB and other sources and typing it into
  a document.

**What "scalable" means (owner, 2026-11-27).** Features and usability for the people, not server load:
- many more kinds of jobs to handle;
- many different kinds of fields;
- much bigger piles;
- maybe a local network setup (several PCs in the office), to be thought through.

**TOBB exports** come as PDF, Excel or similar formats. PDFs are already a data source today through templates (draw
boxes, read values), so a TOBB PDF can go through the same reading.

**Network: sharing and handing work on (owner, 2026-11-27).**
- Easily share files between staff, look at each other's work, take over or edit someone's work, get their outputs.
- Easily get a prepared file to the institution it is for. Today staff email it or carry it on a USB stick; that
  hand-off should be much easier.
