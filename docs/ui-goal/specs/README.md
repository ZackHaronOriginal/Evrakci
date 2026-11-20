# Phase 5 specs: how the four fit together

Four specs were written at the same time by four agents, so they overlapped. This page makes them
agree. It was checked on 2026-11-20. Nothing is built yet: each spec waits for the owner's yes
(decisions.md, "Owner answers: Phase 5 build order and rules").

| Letter | File | Ideas |
|---|---|---|
| A | `kontrol-filters.md` | I-09, I-03, I-04, I-06, I-08 (choose pages in Kontrol) |
| B | `quick-wins.md` | I-17, I-19, I-21, I-22, I-23, I-28, I-47 (small fixes) |
| C | `qr-saved-filters.md` | I-07 (saved filters; I-01 dropped by the owner) |
| D | `disa-aktar.md` | I-35, I-38, I-39, I-40 (Dışa Aktar) |

A few words used below:
- **Core**: the part of Evrakçı that does the actual work on the files (`src/evrakci/pipeline/`).
  The window and the command line both use it, so they always agree.
- **CLI** (command line): the `evrakci` command typed in a terminal. It must give the same result
  as the window.
- **Job file**: the file where Evrakçı saves a job (pages, cuts, values) so it can be opened again.

---

**Rule for every new action (owner, 2026-11-20):** no action is shortcut-only. Each new action in A-D also gets a mouse path (menu bar, a button, or the right-click menu of the thing it acts on); the command palette does not count. The automatic check (`audit_shortcuts.py --paths --check`) runs in tests and CI and fails the build otherwise.

## 1. Build order

Smallest and safest first. Each step is built and tested on its own. A step marked "needs" waits
for the step it names.

**Stage 1: window only, no core change**
1. B I-47 keep the window responsive: background work with a loading view (shared `run_background` helper and loading card). *Needed by step 17.*
2. B I-21 carry the document between Kontrol and Değerler (also fixes bug B-012).
3. B I-19 every section's reading in the value card.

**Stage 2: small core changes for Değerler and Şablonlar**
4. B I-17 mark the wrong cell. Adds the shared `value_level`. *Needed by step 11.*
5. B I-23 "Okunana dön".
6. B I-22 warn on an empty required value.
7. B I-28 weakest examples first.

**Stage 3: choosing pages in Kontrol (A)**
8. A I-08 remove filter / template, restore a blank page (needs nothing new from A).
9. A §0 + I-09 the "Ölçüte göre seç…" dialog, `pipeline/select.py`, this document / odd / even, Ctrl+Space.
   *Needed by steps 10-12 and 18.*
10. A I-03 blank pages (needs 9).
11. A I-06 pages that need a check (needs 4 and 9).
12. A I-04 page size and orientation (needs 9). First new job-file field; sets the pattern C reuses.

**Stage 4: Dışa Aktar (D)**: does not depend on A or C, so it can be built in parallel with stage 3.
13. D I-40 step 1: bug B-003 (PDF/A failure counted as Kontrol); O-18 decided: Bilgi.
14. D I-35 "Belge no", job name and export time in index.xlsx.
15. D I-40 "Kontrol gerekenler" sheet (needs 13, 14).
16. D I-39 rename preview with the scan file name.
17. D I-38 print preview (needs 1).

**Stage 5: saved filters (C)**: last because it changes the template file.
18. C I-07 saved filters as chips (needs 9-12). I-01 (QR content) was dropped by the owner: QR is only the separator.

## 2. Shared pieces and their owner

One spec owns each shared piece; the others point to it.

| Shared piece | Owner | Used by | What was settled |
|---|---|---|---|
| `pipeline/select.py`: `Criterion(kind, params)`, `evaluate`, `combine`, `Match` | A §0 | C I-07 (`select_pages`) | C first had its own `select.py` design and a `select_pages(job, filters)` with "settings"; now C adds `select_pages` on top of A's `evaluate`/`combine`. A saved filter = one named criterion (A had said "a list of criteria"). |
| "Sayfaları seç" dialog (`SelectDialog`), entry "Ölçüte göre seç…" (S), status line "{n} sayfa seçildi." | A §0 | C I-07 (chips call the same core) | One dialog, title "Sayfaları seç", button "Seç", status "{n} sayfa seçildi ({ölçüt})." (C's own QR dialog went away with I-01.) |
| CLI `evrakci is sec <iş> <ölçüt>` | A §0 | C (`--sablon`, `--filtre`) | One command. A's form gained the missing `<iş>` argument. |
| `value_level` + `EMIN_AT = 0.90` in `pipeline/templates/values.py` | B I-17 | A I-06, `ui/sablon_read.level_of` | A put it in `values.py` with 4 levels, B in `review.py` with 5. Now one function, in `values.py` (it has no imports, so the select module and the UI can use it), with all 5 levels including "okunmadı". |
| Job file format | this page | A I-04, D I-35 | A and C kept version 2; D wanted version 3. Version 3 would stop older Evrakçı versions opening the job. **Plan: stays version 2.** Every new field (`width_mm`/`height_mm`, `last_export`) is added with a default, so old files open in the new app and new files open in older apps. |
| Re-reading old jobs | A I-04 `fill_page_sizes` (automatic, no rendering) | A | The only old-job helper now (C's `reread_qr` went away with I-01); uses `JobStore.batch_file`; its old-job test fixture is made by I-04. |
| `run_background` + `LoadingCard` (`ui/workers.py`, `ui/loading.py`) | B I-47 | D I-38 | There is no busy cursor (`motion.wait_cursor` is not built): D's 800-row preview is built through it, with the loading card titled "Önizleme hazırlanıyor…". |
| `ExportItem` fields `sources`, `name_note`, `pdfa_note` | D (C1) | D I-39, I-40 | `pdfa_note` (from the B-003 fix) was missing from D's shared list. |
| Kontrol keys | this page (table below) | A, B, C | D was proposed twice; see section 3. |
| Saved-filter chips | C I-07 | A | A first put the chips inside its dialog; they are a row above the timeline (C), using A's core. |

## 3. Keys

Checked against `shortcut-contract.tsv` and the Turkish keyboard rules (no Ç Ş Ğ İ Ö Ü, no I, no
Ctrl+Alt). `audit_shortcuts.py --check` today: 0 problems (nothing new is wired yet).

| Tab | Key | Command | Spec |
|---|---|---|---|
| Kontrol | S | Ölçüte göre seç… (Sayfaları seç) | A |
| Kontrol | B | Bu belgeyi seç | A |
| Kontrol | Ctrl+Space | Sayfayı seçime ekle / çıkar (local) | A |
| Kontrol | Alt+Left / Alt+Right | Seçimi bozmadan git (local) | A |
| Kontrol | Shift+F / Shift+T | Filtreyi kaldır / Şablonu kaldır | A |
| Kontrol | D | Değerlerde aç | B I-21 |
| Kontrol | Ctrl+Shift+F | Kayıtlı filtreler | C |
| Değerler | K / R | Kontrol'de aç / Okunana dön | B |
| Değerler | Alt+1 … Alt+4 | pick a reading (editor only, local) | B I-19 |
| Şablonlar | N / Shift+N / Ctrl+L | next / previous weak example, list | B I-28 |
| Dışa Aktar | Ctrl+Shift+C | Ad listesini kopyala ("Adları karşılaştır" has no key: menu and palette) | D I-39 |
| Dışa Aktar | Ctrl+P | changes to "open print preview" (O-16 decided) | D I-38 |

Settled conflict: **D on Kontrol** was "Değerlerde aç" (B I-21) and "Sonraki farklı sayfa" (A I-04,
with Shift+D). D stays with "Değerlerde aç", because it pairs with K on Değerler (each key is the
first letter of the tab it goes to). "Sonraki / Önceki farklı sayfa" are now in the Git menu and the
command palette without a key. All other proposed keys were free and used once.

At build time: B, K, R, N and Shift+N have a different label on another tab, so each needs a
page-specific line in `shortcuts.md`, or the audit fails. The "Tek tuşlu kısayollar" list in
`shortcuts.md` gains S, D.

## 4. Core changes in total

16 core changes and 10 command-line changes (O-19 decided: no separate check-list file). The job file version stays 2
and the template file version stays 1; every new field is optional.

- **A (5 core, 2 CLI):** `pipeline/select.py` (kinds belge, tek, cift, bos, farkli, guven;
  `value_page`); page width and height in `PageInfo` and `analyze_pdf`, `read_page_sizes`; the two
  fields in the job file; `JobStore.fill_page_sizes`; `Job.remove_filter`. CLI: `is sec`,
  `is filtre-kaldir`.
- **B (4 core, 2 CLI):** `values.value_level`; `review.set_value(required=)`; `review.can_revert`;
  `templates/read.weakest_examples` (with `flagged_count` moved in). CLI: new wording in
  `is degerler`; `is deger` messages.
- **C (2 core, 3 CLI):** `SavedFilter` in the template file; `select_pages`. CLI: `is sec --sablon/--filtre`,
  `sablon filtre-ekle/filtre-sil/filtreler`.
- **D (5 core, 3 CLI):** `ExportItem.sources/name_note/pdfa_note` (and the B-003
  fix); notes made in `plan_export`; `plan_names`; `write_index` ("Belge no", sheets `Özet` and
  `Kontrol gerekenler`); `Job.last_export`. CLI: name note per file, `--onizle`, a last line naming
  the check list. Optional: `write_check_report` and `--kontrol-listesi`.

index.xlsx changes only through D: one new column and two new sheets.

## 5. Decisions for the owner

**None left to choose.** On 2026-11-20 every O-n was checked against decisions.md, the phase plan's
"Already decided", PRODUCT.md, DESIGN.md, rules.json, earlier owner answers, the shortcut
conventions (`research/shortcut-conventions.md`), the Turkish terms check and published practice of
comparable tools. All 21 (O-12 for its remaining key) were settled by that evidence and moved to section 6
with their source; each spec states the decision where it applies. What the owner still does:
approve each spec (Q-22), and object to any decision in section 6 if the business sees it
differently.

**Nothing is on hold.** I-01 (QR content) was dropped by the owner on 2026-11-20 (QR is only the
Evrakçı separator; the offices' forms carry no QR codes), so **O-11** ("QR" or "karekod"), the Q key and
Shift+K are gone too.

## 6. Decided by evidence and in the reconcile (the owner may still object)

### Decided by evidence (2026-11-20)

Sources opened that day. Microsoft pages: W-DUP [duplex printing in Word](https://support.microsoft.com/en-US/Word/print-on-both-sides-of-the-paper-duplex-printing-in-word),
XL-TRI [buttons and triangles in Excel cells](https://support.microsoft.com/en-us/office/what-are-those-buttons-and-triangles-in-my-cells-203e34e6-ba90-4158-ae58-33397dda3ca9),
W-SPELL [check grammar and spelling in Word](https://support.microsoft.com/office/check-grammar-spelling-and-more-in-word-0f43bf32-ccde-40c5-b16a-c6a282c0d251),
VLOOKUP [VLOOKUP function](https://support.microsoft.com/en-us/office/vlookup-function-0bbc8083-26fe-4963-8ab8-93a18ad188a1),
OFF-PRT [printing and print preview](https://support.microsoft.com/en-us/office/printing-and-print-preview),
PRN [PowerRename](https://learn.microsoft.com/en-us/windows/powertoys/powerrename),
W-BG [Word `Options.BackgroundSave`](https://learn.microsoft.com/en-gb/office/vba/api/word.options.backgroundsave).
Sector tools: FC [ABBYY FlexiCapture, verification of recognized data](https://docs.abbyy.com/flexi-capture/operator-work/rule-validation),
NAPS2 [profile settings](https://www.naps2.com/doc/profile-settings),
PAP [Paperless-ngx usage docs](https://github.com/paperless-ngx/paperless-ngx/blob/dev/docs/usage.md),
OCRM [OCRmyPDF return codes](https://ocrmypdf.readthedocs.io/en/latest/advanced.html),
PD [platformdirs parameters](https://platformdirs.readthedocs.io/en/stable/parameters.html).
SC = `research/shortcut-conventions.md` (T1), TT = `research/turkish-terms.md`.
Acrobat's own help pages returned HTTP 403 and are not used as evidence.

| O | Decided | One-line source |
|---|---|---|
| O-1 | (a) odd / even counted from each document's first page | W-DUP: "Only Print Odd Pages" works on the pages of the document printed; each Evrakçı document is its own PDF |
| O-2 | (a) the guide-tab click keeps moving to the document; B and the context menu select it | no opened source documents a group-header-selects convention on Windows; decisions.md (round 3): approved behaviour changes only by a separate proposal |
| O-3 | (a) "looks different" marks on by default, off in Görünüm | PRODUCT.md principle "Never silent"; XL-TRI: Excel shows its cell indicator unasked |
| O-4 | **(b), changed from the draft:** add the checkable "Boş sayfaları at" (menu Araçlar, no key), using the existing undoable `set_drop_empty`; select + Del stays | NAPS2 "Exclude blank pages" is a scan setting; dropped pages stay drawn ("boş sayfa, dışa aktarılmaz", `timeline.py:229`), so nothing hides; fixes B-006 and matches the CLI |
| O-5 | (a) S, B, Ctrl+Space, Alt+Left / Alt+Right, Shift+F, Shift+T | SC §4.2, §5 rank 7: Ctrl+Space matches Windows; Alt+arrows kept because the app has no history and Ctrl+arrow is the contract's document jump |
| O-6 | (a) icon in the cell; word in tooltip and Güven | XL-TRI: an in-cell indicator, words on selecting the cell; HIG-CON-03 met by the icon |
| O-7 | (a) CLI prints "[kontrol, öneri: …]"; "[okunamadı]" only when nothing was read | decisions.md: one status vocabulary everywhere |
| O-8 | (a) click or Alt+1 … Alt+4 takes a reading, one undo step | W-SPELL: "choose the suggestion you want" from a list; SC §4.2: Alt+digit is local to the editor, access keys are letters |
| O-9 | (a) an emptied required value is saved as Kontrol with the reason | FC: rule errors are flagged on the field and checked later, input is not blocked; PRODUCT.md "Never silent" |
| O-10 | (a) D (Kontrol), K and R (Değerler), N / Shift+N and Ctrl+L (Şablonlar); "Sonraki farklı sayfa" menu only | SC §4.2: no convention for the letters; Win32 guide lists Ctrl+L for app commands; N = next kontrol (decisions.md) |
| O-12 (key) | (a) Ctrl+Shift+F = "Kayıtlı filtreler" (Shift+K and Q went with I-01) | SC §4.2: no convention; Ctrl+Shift+F clashes only with KDE's second full-screen key (ours is F11) |
| O-13 | (a) saved filters stored with the template only | PAP: saved views are set up once and reused, not per upload; PRODUCT.md "set up once per document kind" |
| O-14 | (a) the chips of the template in the inspector; with none, "Şablon seçin" | follows O-13; the existing inspector rule `_template_for_selection` |
| O-15 | (a) "Belge no" is the first column of index.xlsx | VLOOKUP: "The value you want to look up must be in the first column of the range" |
| O-16 | (a) Ctrl+P opens the preview; Enter prints; no Ctrl+Shift+P | OFF-PRT: Office prints and previews from one place with Ctrl+P; SC §5 rank 2 |
| O-17 | (a) the old name is the scan file ("Kaynak") | PRN: the preview pairs the name on disk ("Original") with "Renamed"; a document's only on-disk name is its scan |
| O-18 | (a) PDF/A failure is Bilgi everywhere; the PDF/A column says "hayır" | OCRM exit 10: "A valid PDF was created, PDF/A conversion failed. The file will be available."; D1 |
| O-19 | (a) the check list is only the index.xlsx sheet; no Ctrl+Shift+R, no `write_check_report` | the same list is already on screen before export ("Yalnızca kontrol gerekenler", `disa_aktar.py:190`); PRODUCT.md "Never silent" met |
| O-20 | (a) "Ölçüte göre seç…", "Seçimle kesiştir", "Silinen boş sayfa yok." (applied in A; the fourth word, "joker karakterli (* ve ?)", went with I-01) | TT: GIMP "Seçim ölçütü", "Seçimle Kesiştir"; LibreOffice "Joker Karakterleri"; ABBYY "Silinen ... boş sayfa" |
| O-21 | (a) keep "filtre", "Kayıtlı filtreler", "Yön" | PRODUCT.md terminology fixes "filtre"; TT: Paperless says "Filtre", ABBYY says "yön"; TT recommends keep for "Kayıtlı" |
| O-22 | (a) write-behind saving, flushed on close, Ctrl+S, export and job switch | owner's direction for I-47 (window thread never blocked); W-BG: users "continue to type" while Word saves; PD: the default job folder is local, so it is cheap there |

Also settled by SC with these: D's "Adları karşılaştır" gets no key (Ctrl+Shift+A is GNOME's
Deselect All; SC §5 rank 1), menu Görünüm and the palette only. The Turkish progressive titles of
I-47 match LibreOffice ("Belge yükleniyor...", "Belgeler Kaydediliyor").

### Decided in the reconcile

Not real owner choices (engineering, or a default the user can change on the spot), so they were
decided and written into the specs:
- A: Alt+arrows folded into O-5; blank limit stays 0,3 % (as CLI and guide); "different" pages
  compared with the whole job by default (the dialog offers "each document"); 3 % size tolerance;
  I-06 selects the value's page and leaves Orta off by default (both changeable in the dialog).
- B: readings list always shown for 2+ readings, at most 4 rows; no extra button in the Değerler
  side panel; "*" marks required columns (as in Şablonlar); "Okunana dön" wording goes to the
  Turkish terms check; `flagged_count` moves to the core; no busy cursor: long work runs through I-47's `run_background` with a loading card.
- C: A's criterion model is the shared core (was C decision 1); a chip's settings are fixed in v1 (was 3); chips only select (was 4).
- D: export time is kept in the job file, format stays 2 (was D-1); dates read "20.11.2026 14:32"
  on paper and in the sheet (was D-4; the sheet had ISO); the scan-file column is off by default
  behind a toggle (was D-6).

## 7. Already decided by the owner (do not ask again)

From decisions.md, 2026-11-20:
- Build first: Kontrol filters (I-03, I-04, I-06, I-08, I-09); quick wins (I-17, I-19, I-21, I-22,
  I-23, I-28, I-47); saved filters (I-07; I-01 QR content was dropped by the owner later the same day); Dışa Aktar (I-35, I-38, I-39,
  I-40). I-50 to I-55 are later.
- New Turkish text is written by the run after checking how Turkish software words the same thing,
  and listed in each spec.
- Each spec needs the owner's approval before it is built.
- D13 is lifted: features may change the core and the CLI, with core tests, a check that older job
  files still open, a check that window and CLI give the same output, and an agent review.

Earlier decisions these specs keep: one status vocabulary (Emin / Orta / Kontrol / Okunamadı;
İncelendi / İncelenmedi), N / Shift+N "Sonraki / Önceki kontrol", U, Enter = "Belgeyi onayla",
undoable delete, orange only for Kontrol (D1), invert selection (key I) deferred.

## 8. Checks against code and decisions

- Code citations spot-checked: A 12 (4 wrong line numbers fixed), B 21 (2 fixed), C 17 (4 fixed),
  D 16 (2 fixed: `export.py:21`, and "Kontrol gerekenler" lives in `degerler_model.py:47`).
- Nothing silently reopens a decision after the fixes. Points that touch earlier decisions are
  decided by evidence in section 6 and still reach the owner through spec approval: the Ctrl+P
  change (O-16), the CLI wording (O-7), and the new chip row in the approved Kontrol layout, which
  per the round-3 rule (decisions.md) is part of approving spec C. D's job format 3 would have
  stopped older app versions opening jobs; it is removed. A's new "Ölçüte göre seç…" icon in the
  Kontrol command bar follows direction A's rule (icon button with tooltip) and is part of
  approving spec A.
- Wording: the Turkish terms check kept the list column "Kaynak" (scan file, D I-39; LibreOffice
  "Kaynak") next to the sheet column "Kaynak sayfalar" (page numbers).
