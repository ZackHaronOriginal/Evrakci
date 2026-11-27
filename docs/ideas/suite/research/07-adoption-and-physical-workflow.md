# 07: Physical workflow, adoption and resistance, and a playbook for office heads

Research for Evrakçı (offline Windows document app for a TOBB member chamber). Date: 2026-11-27.

How to read this report: every claim has a source. Each source is tagged **[E]** (evidence: peer-reviewed study, audit report, archival or government guidance), **[G]** (official rule or standard), **[V]** (vendor or practitioner material: useful for specs and practice, not proof) or **[U]** (unverified: I could not read the primary text, or the claim is my own inference). OCR verification screens, spreadsheet errors and end-user templates are left to the other researcher.

---

## 0. Summary of findings

1. **Preparing the paper is usually the biggest and most underestimated part of scanning.** Archival guidance puts preparation first: remove staples and sticky notes, separate stuck pages, keep page order. One cost framework puts prep at about 37% of capture cost, against about 24% for the scanner itself **[V]**.
2. **Quality control should use samples and follow fixed rules.** NARA requires a visual check of at least 10 images or 10% of each batch, whichever is larger, with rescans until the sample passes in full **[G]**.
3. **People adopt what they find useful and compatible with how they already work.** Perceived usefulness was the strongest predictor of EBYS adoption in a Turkish university **[E]**. Compatibility and relative advantage are the most consistent adoption predictors across 75 studies **[E]**.
4. **Resistance is mostly about switching costs and perceived threats** (job, control, being watched), not a dislike of technology as such **[E]**. Turkish EBYS staff surveys name the same fears **[E]**.
5. **Fitting the existing office flow matters more than features.** Heeks's design-reality gap model and the UK NHS National Programme for IT (NPfIT) failure both show the cost of imposing a central design on local practice **[E]**.
6. **Paper will not disappear, and the product should not fight it.** Paper persists for good reasons such as trust, memory and ease of use. Workarounds keep growing when the system does not fit **[E]**.

---

## 1. The physical capture side

### 1.1 What archival bodies say about preparation

- **Oregon State Archives, *Digitization Guidance* (v1, Feb 2026)** [G]: preparing documents means "removing any staples, sticky notes, and paperclips, and breaking apart pages that are stuck together", checking that records "are not intermingled, with each one clearly identifiable and complete, and with pages in the correct order". It also tells offices to destroy records that have passed their retention date before scanning them, to avoid unnecessary cost. It lists "significant staff time to produce scans and review them" as a main drawback of scanning. Source: https://sos.oregon.gov/archives/records-management/Documents/digitization-guidance.pdf
- **Resolution floor (same source)** [G]: 200 dpi for documents in 10-point type or larger, and 300 dpi for smaller type. This is useful as an Evrakçı default: 300 dpi greyscale/B&W covers forms with small print.
- **NARA preparation and handling** [G/E]: NARA's in-house digitization planning document lists "How much archival preparation do the materials need?" as a scheduling input (https://www.archives.gov/files/about/policies/nara1550-s3.docx.pdf). NARA's older fastener guidance (now archived) explains how to remove staples without tearing pages (https://webarchive.library.unt.edu/web/20121007061339/http://www.archives.gov/preservation/holdings-maintenance/fastened-docs.html).
- **University of Melbourne** [E/practice]: staples damage scanner glass, both the flatbed platen and the narrow window in an ADF scanner (https://library.unimelb.edu.au/digitisation/help/how-to/business_document_scanning/document_preparation).
- **Cost share of preparation** [V]: one capture-cost framework puts preparation at about 37% of total cost, scanner purchase and running at about 24%, and post-scan processing at about 39% (https://www.ecmconnection.com/doc/the-total-cost-of-scanning-a-framework-for-an-0001). Vendors agree that prep is "the most underestimated" cost (https://www.opex.com/solutions/backfile-conversion/). The source is undated, so treat the percentages as indicative.

### 1.2 Quality control

- **NARA *Digitization Quality Management Guide* (Oct 2023)** [G]: "Agencies must perform a visual inspection by inspecting a random sample of a minimum of ten image files or 10% of each batch... whichever is larger". Inspectors check at 100% zoom that images are "not flipped, inverted, improperly cropped, or skewed". When errors turn up, the affected records are rescanned and the sample is checked again until it reaches a 100% pass rate. The guide also says quality should be built into the process rather than inspected in afterwards. https://www.archives.gov/files/records-mgmt/policy/digitization-quality-mgmt-guide.pdf
- **Oregon** [G]: check the first batch page by page ("no pages were skipped, there aren't any lingering sticky notes, pages are properly aligned"), then spot-check later batches.

**Implication for Evrakçı:** build this sampling rule in. Check the first batch of each session fully, then sample 10% (at least 10 images) and flag skewed or blank pages automatically. Keep it separate from value checking, which is the other researcher's topic.

### 1.3 Scanner types and where they break

- **Dedicated sheet-fed ADF scanners** [V specs]: a typical departmental model such as the Ricoh/Fujitsu fi-8170 is rated at 70 ppm / 140 ipm duplex, has a 100-sheet ADF and an "expected daily volume" of 10,000 sheets. It detects double feeds with an ultrasonic overlap sensor plus a length check (https://www.pfu.ricoh.com/global/scanners/fi/fi8170/). Canon's DR-series manual describes the same two methods, which can be used separately or together (https://manualsonline.com/manuals/mfg/canon/dr6080.html?p=9).
- **MFP copiers** are already in most offices. Their ADFs are slower, often lack ultrasonic double-feed detection, and usually deliver to a network folder or by email. **[U]**: this is general knowledge, and I found no neutral source comparing MFP and dedicated ADF error rates.
- **Flatbeds** suit bound, fragile or odd-sized items only, and are too slow for piles.
- **Scan-to-folder fragility** [V]: Windows 10 1709 and later builds ship without SMBv1, and many older MFPs can only scan to folders over SMBv1. Ricoh, Dell, Canon and HP support pages all report "scan to folder stopped working" after Windows updates (https://ricoh.com/products/mfp20170727_1, https://www.dell.com/support/kbdoc/en-ae/000135687/scan-to-network-smb-connection-errors-031-xxx). For Evrakçı, watching a local folder is a sensible entry point. Setup must test it, and the app should show a plain message ("Tarayıcıdan dosya gelmiyor") rather than failing silently.

### 1.4 Separator sheets and patch codes

- The standard industry approach is a separator sheet carrying a patch code or barcode. Patch 2 usually marks a new document, Patch 3 a new batch and Patch T either. Software discards the separator page (Kodak Capture Pro: https://resources.kodakalaris.com/support/Capture%20Pro%20Help/Content/Separating_batches_or_documents_with_patch_codes.htm; Dynamsoft: https://www.dynamsoft.com/Barcode-Types/Patch-Code.aspx; Tungsten: https://docshield.tungstenautomation.com/KC/en_US/11.2.0-oyj7ljfzv3/help/main/KC_scan/c_addingbatchseparatorsheets.html) [V]. Barcode sheets can also carry data such as a batch number or form type (Dynamsoft) [V]. Evrakçı's QR separators follow this established practice. A QR sheet that also encodes the document type and the batch owner can do the indexing that staff would otherwise type.
- **Failure modes worth designing for** [U, from the specs above and vendor manuals]: a separator is missed or doubled, two separators stick together (the ultrasonic sensor catches this on dedicated scanners but not always on MFPs), a separator is fed upside down, or a reused separator is creased. The app should show a "possible missing separator" warning when a document's page count is unusual for its type.

### 1.5 Who scans and when

- AIIM survey data (2009–2010, n=493 AIIM members) found organisations expected central scanning to grow despite MFP spread. Scanning at the department gives process owners more ownership, but "office staff and knowledge workers need training to index accurately" (summary: https://documentmedia.com/article-217-Local-Central-Outsource-Whats-Working-Best-with-Capture.html; deck: https://de.slideshare.net/jmancini77/distributed-capture-survey) [E-ish: industry association survey, dated].
- Vendors argue the knowledge to classify a document is greatest "at the point of transaction" (https://public.dhe.ibm.com/software/data/sw-library/ecm-programs/ImagineSolutions-BestPracticesDocumentImaging.pdf) [V].
- **Inference for a chamber office** [U]: most papers arrive at the counter (registry, certificates of origin, membership). Two patterns are realistic. In one, papers are scanned at intake when the clerk is present and the member waits. In the other, a separator sheet goes on at intake and one person scans in a back-office batch at a fixed time each day. The second pattern fits AIIM's centralisation finding and keeps one person skilled at scanning.

### 1.6 Turkish rules

- **Resmî Yazışmalarda Uygulanacak Usul ve Esaslar Hakkında Yönetmelik** (Cumhurbaşkanı Kararı 2646, RG 10.06.2020/31151) [G]: official correspondence is in principle electronic with secure e-signature (Art. 4). E-signed documents are not printed, wet-signed and stored on paper (Art. 4(1)). A copy made from a physical document is marked "ASLI GİBİDİR" and signed by an authorised official, with name, title and date (Art. 29(2)). Incoming paper must have its date of receipt and metadata registered in EBYS or a corporate document registry (Art. 31(4)), and a registry stamp or label goes on the first page (Art. 31(5)). Text: https://csgb.gov.tr/Media/jcomj5ra/resmi-yazışmalarda-uygulanacak-usul-ve-esaslar-hakkında-yönetmelik.pdf
  - **Unverified applicability [U]:** Art. 1(2) says the regulation covers "bütün kamu kurum ve kuruluşları". Chambers are "kamu kurumu niteliğinde meslek kuruluşu" under Law 5174 and Constitution Art. 135 (https://ticaret.gov.tr/ic-ticaret/odalar-ve-borsalar/odalar). Whether the regulation binds them, or binds them only in practice through TOBB, should be confirmed with the TOBB legal office. Either way, Art. 31(4)–(5) describes the intake practice that a chamber registry already follows, and Evrakçı's label printing and index should match it.
- **Devlet Arşivleri Başkanlığı, *Arşivlerde Gerçekleştirilecek Dijitalleştirme Faaliyetlerine Yönelik Usul ve Esaslar* (07.07.2020)** [G]: an institution forms a commission of at least 5 members to choose what to digitise. Records that will be destroyed at the end of their retention period and are not used in service delivery are not digitised. Digitising archival records needs the Başkanlık's approval. Original order must be kept. The work must be compatible with EBYS and TS 13298 (https://www.lexpera.com.tr/mevzuat/tebligler/arsivlerde-gerceklestirilecek-dijitallestirme-faaliyetlerine-yonelik-usul-ve-esaslar-51048475-010-04-1). Articles 7–13, which cover resolution, formats and whether originals may be destroyed, sit behind a paywall and are **unverified**. Scope is institutions under CB Kararnamesi No. 11, and whether that includes chambers is **unverified**.
- **Practical message:** nothing I found lets a chamber destroy paper originals because they have been scanned. Evrakçı should present scans as working copies, and paper stays the record unless the chamber's legal advisers decide otherwise. This is also the strongest reassurance for staff (section 5).
- **KVKK** [G]: the KVKK *Kişisel Veri Güvenliği Rehberi (Teknik ve İdari Tedbirler)* requires role-based access, access logs and defined responsibilities in job descriptions (https://kvkk.gov.tr/Icerik/2040/Veri-Guvenligine-Iliskin-Yukumlulukler). The Kurum has also published a compliance guide for public bodies (https://www.kvkk.gov.tr/Icerik/8833/kamu-kurumlari-icin-kisisel-verilerin-korunmasi-kanununa-uyum-rehberi). Specific USB rules are **unverified**.

---

## 2. Adoption and resistance

### 2.1 Acceptance models

- **TAM in a Turkish EBYS setting** [E]: Cibaroğlu & Turan (2018) studied Sakarya University's EBYS, in use since 2013, with an extended TAM. Perceived usefulness was the most important factor. Ease of use also raised intention. Higher education made use easier. Experience did *not* raise perceived ease of use (https://dergipark.org.tr/en/pub/ybs/article/287647). Esen & Büyük (2014, YÖK, n=106) found the same usefulness and ease effects (as reported in the search summary; full text **unverified**).
- **UTAUT** [E]: Venkatesh et al. (2003) name four drivers: performance expectancy, effort expectancy, social influence and facilitating conditions. Age, gender, experience and voluntariness moderate them. Facilitating conditions ("organisational and technical infrastructure exists to support use") act directly on actual use (overview: https://en.wikipedia.org/wiki/Unified_theory_of_acceptance_and_use_of_technology; original MISQ 27(3)). A Bursa Metropolitan Municipality study applied UTAUT to Turkish city managers (https://dergipark.org.tr/tr/download/article-file/1113696). Its results are **unverified** in detail.
- **Age** [E]: Morris & Venkatesh (2000, *Personnel Psychology* 53(2), DOI 10.1111/j.1744-6570.2000.tb00206.x) found that younger workers' use depends more on attitude. Older workers' use depends more on **subjective norm** (what colleagues and the boss expect) and **perceived behavioural control** (whether "I can do this"), and the norm effect fades with experience (https://zenodo.org/records/897631). The design lesson: for older staff, a respected colleague using the tool and a guarantee that they cannot break anything matter more than a feature list.
- **Innovation attributes** [E]: Tornatzky & Klein's meta-analysis of 75 studies found **compatibility, relative advantage and complexity** most consistently related to adoption (IEEE TEM EM-29(1), 1982: https://ieeexplore.ieee.org/document/6447463). A later IS meta-analysis confirmed the first two but found complexity's effect less stable (https://aisel.aisnet.org/cais/vol34/iss1/31). Rogers adds **trialability** (trying the tool on a small scale) and **observability** (results others can see) (https://en.wikipedia.org/wiki/Diffusion_of_innovations).

### 2.2 Why staff and officials resist

- **Switching costs** [E]: Kim & Kankanhalli (MISQ 33(3), 2009) found switching costs central to user resistance, and the opinions of colleagues and self-efficacy work through them (https://aisel.aisnet.org/misq/vol33/iss3/9). Status-quo bias is the default. A new tool has to cost less effort to switch to than it saves.
- **Perceived threats** [E]: Lapointe & Rivard (MISQ 29(3), 2005) found that resistance follows when people perceive threats from the system's interaction with their starting conditions. The target of resistance can shift from the system itself to what it *means*, for example a change in who holds power (https://aisel.aisnet.org/misq/vol29/iss3/6/). Their 89-case follow-up classifies implementer responses as inaction, acknowledgment, rectification and dissuasion (MISQ 36(3), 2012: https://aisel.aisnet.org/misq/vol36/iss3/13). In their earlier hospital cases, *lack of response*, antagonistic responses and support aimed at the wrong concern made resistance worse (CMAJ 2006: https://cmaj.ca/content/cmaj/174/11/1573.full-text.pdf).
- **Turkish public staff, EBYS** [E]: Saydam & Yalçınkaya (2018) surveyed 150 staff at Bağcılar Municipality and Marmara University. Their literature review lists fears of losing one's job, losing authority, being watched by superiors and checked by colleagues, and the difficulty of changing long paper habits. Outages and update problems reinforce these prejudices. Their findings: staff did *not* think EBYS required advanced skills. Staff **trusted the electronic environment**, with no age difference in preferring paper (p=0.998). Staff rated training as *not sufficient* and wanted one-to-one, continuous and multimedia formats. Staff involvement, management support and continuous training were key (https://dergipark.org.tr/en/download/article-file/588349). Saydam (2015) lists the same causes: protecting the status quo, distrust of electronic systems, unfriendly software and the wrong teaching methods (https://dergipark.org.tr/en/download/article-file/454336).
- **Digital skills base in Turkey** [E]: in OECD PIAAC (2015 round), **38.0% of Turkish adults had no computer experience or failed the basic ICT test**, against 14.7% on average, and only 0.9% reached the top problem-solving level (https://t4.oecd.org/turkiye/Skills-Matter-Turkey.pdf). The OECD *Digital Government Review of Türkiye* found a gap in the public-sector digital skills strategy. It recommends digital literacy and confidence at all levels, leaders included (https://www.oecd.org/en/publications/digital-government-review-of-turkiye_3958d102-en/full-report.html). The data is ageing, but the design rule holds: assume a sizeable share of users have very weak computer skills.
- **"The paper is the real one"** [E]: Sellen & Harper (*The Myth of the Paperless Office*, MIT Press 2002) show that paper persists because of what it lets people do: it is tangible, can be spread out and laid side by side, and can be annotated. People prefer print when they have to compare several documents (https://www.microsoft.com/en-us/research/publication/myth-paperless-office/). Saleem et al. (VA, 2009, 20 informants) found 11 categories of paper workarounds alongside an EHR, including efficiency, memory, **trust** and security (https://pubmed.ncbi.nlm.nih.gov/19464231; full text **unverified**, details from the abstract via search). In the Turkish regulation the wet-signed paper original is the legal record for paper-origin documents (Art. 29), so this attitude is partly *correct*. It should be respected rather than argued away.

---

## 3. Change management: what worked and what failed

### 3.1 Failures

- **Design-reality gaps** [E]: Heeks's iGovernment working papers argue that most e-government projects in developing and transitional countries fail totally or partially. The larger the gap between the design and the reality on seven dimensions (information, technology, processes, objectives/values, staffing/skills, management systems, time and money), the higher the risk (https://gsdrc.org/document-library/causes-of-e-government-success-and-failure-design-reality-gap-model/; SSRN: https://papers.ssrn.com/Abstract=3540052). The commonly quoted figure of 35% total and 50% partial failure is **unverified** here, because the primary page returned 404.
- **Centralised big bang** [E]: the UK NPfIT was stopped in 2011 after an estimated £9.8bn, and the National Audit Office (NAO) found it "did not deliver key benefits". The NAO's 2020 review cited weak understanding of local clinical groups and working practices, and too little support from clinicians (https://www.nao.org.uk/reports/department-of-health-the-national-programme-for-it-in-the-nhs/; summary https://www.theregister.com/2020/05/18/latest_nhs_it_revolution_is/).
- **Mandated without meaning** [E]: in Orlikowski's study of "Alpha" (CSCW 1992), the CIO made Lotus Notes the firm standard. Consultants learned about it from the trade press, had no clear idea what it was for, and in a competitive culture feared that sharing would cost them status. Usage stayed shallow (https://dspace.mit.edu/handle/1721.1/2498 ; summary https://buttondown.com/1992newsletter/archive/learning-from-notes-by-wanda-j-orlikowski/). The detail comes from secondary summaries and is partly **unverified**.
- **Big bang versus phased** [E-weak]: I found no controlled study isolating rollout strategy versus resistance. The evidence is mixed: big bang worked in some small firms, but practitioners link it to more risk (https://www.pmi.org/learning/library/big-bang-phased-approach-advantages-disadvantages-4820) [V]. For a single small office the real choice is task by task: one job type at a time.

### 3.2 Shadow workflows

- Workaround research finds workarounds tend to *increase over time* rather than fade (review: https://emeraldinsight.com/insight/content/doi/10.1108/REGE-12-2017-0015/full/html) [E]. Boonstra et al. (2021) separate in-system workarounds from out-of-system ones, where work bypasses the system (https://pmc.ncbi.nlm.nih.gov/articles/PMC8186102/) [E]. Shadow IT in the public sector is under-studied (IFIP 2019: https://dl.ifip.org/IFIP-LNBIP-375/hal-03408392) [E]. Vendor surveys claim over half of public employees use unapproved tools (https://www.ninjaone.com/blog/public-sector-shadow-it/) [V].
- **Inference [U]:** in a chamber office, the shadow workflow will be "scan on the MFP to USB, rename by hand, retype into Excel". Evrakçı should *read* those same artefacts, such as an MFP folder or an existing Excel list, so that the old path and the new one lead to the same place.

### 3.3 What worked

- **Champions and super users** [E]: Yuan et al. (2015, BMC Med Inform Decis Mak) found super users' behaviour varied a lot. The helpful ones reported problems to someone who could fix them and taught by "learning by doing". The harmful ones lost patience with colleagues or spread negative opinions (https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4407776/). The lesson is to choose a patient champion and give that person a direct line to whoever can fix the product.
- **Involvement and management support** [E]: Saydam & Yalçınkaya (above) found that informing staff, asking their views, involving them in the project, top-management support and continuous training mattered for EBYS success.
- **Training format for older or non-technical staff** [E]: older adults make more errors, need more time and need more help during training (Kelley & Charness 1995, cited in https://pmc.ncbi.nlm.nih.gov/articles/PMC2268090). Making tasks self-paced, splitting them into steps, providing assistance and allowing practice time helps (Sterns, cited in https://pmc.ncbi.nlm.nih.gov/articles/PMC2585421/). Many older learners prefer text manuals they can work through alone (https://pmc.ncbi.nlm.nih.gov/articles/PMC2817993; exact study **unverified**). Turkish EBYS users asked for one-to-one, continuous training (Saydam & Yalçınkaya).
- **Small trials and visible results** [E]: trialability and observability (Rogers) and relative advantage (Tornatzky & Klein) all argue for a first job whose time saving the whole office can *see*.
- **Facilitating conditions** [E]: UTAUT's direct path from facilitating conditions to actual use means a person to ask, a printed guide and a scanner that works matter as much as attitudes.

---

## 4. Integration with how the office already works

- **Compatibility is the strongest lever** (Tornatzky & Klein; Rogers) [E], and the design-reality gap is the strongest risk (Heeks) [E]. In a chamber office the existing flow is roughly: the counter receives paper, registry stamps it (Art. 31(5) style), a clerk keys data into TOBB systems or Excel, Word letters are produced, files go out on USB or email or onto a network share, and the paper goes to the archive cupboard.
- **TOBB central systems:** since 2005 a central member registry automation has served about 306 chambers and exchanges, and the ATR (certificate) automation about 159 chambers, according to a TOBB presentation (https://mobil.tobb.org.tr/HaberResimleri/5614-8.pdf) [E-ish, TOBB slides]. Evrakçı will not replace these. It should sit *beside* them: read their PDF/Excel exports and produce Word and Excel files in the formats staff already use.
- **MFP scan-to-folder** is the most likely capture path (section 1.3), so Evrakçı should watch a folder and accept multi-page PDF or TIFF.
- **EBYS**, where a chamber has one: the Devlet Arşivleri rules require digitisation to be compatible with the EBYS (Usul ve Esaslar Art. 6) [G]. Evrakçı's outputs (named PDF + Excel index with date, number and subject metadata) should be importable, and the index fields should mirror the registry fields of Art. 31(4) [G/U].
- **Inference [U]:** products that fit in tend to change *one step* (typing, renaming, sorting) and leave the inputs and outputs the same. Products that fail ask staff to change where paper goes, who signs, or where files live, all at once.

---

## 5. What the product itself can do

Each item is tied to the evidence above. Items marked [U] are design inferences.

1. **Defaults that match current habits** (compatibility): file names and folder layout copied from the office's current manual naming. The Excel index uses the same column order as the register they keep now. 300 dpi greyscale (Oregon) [G].
2. **Printable kit**: separator sheets with QR codes that carry document type and batch owner, a one-page "how to prepare a pile" sheet (staples out, sticky notes off, face down, separator per document; from Oregon and NARA), and a one-page "what to do if" sheet. These suit older users' preference for self-paced text material [E] and support facilitating conditions [E].
3. **A first job that pays off in a day** (trialability and observability): pick the job with the most retyping, for example TOBB export to Word form. Show "this batch: 46 documents, 12 minutes; by hand ≈ X minutes", with X measured by the office in step 3 of the playbook rather than guessed [U].
4. **"Paper is still safe" reassurance**: the app never says or implies that the paper can be thrown away. A visible line reads "Asıl belge kağıttır; bu tarama çalışma kopyasıdır". This matches Art. 29 and the absence of any destruction permission [G], and it answers the trust concern seen by Saleem and by Sellen & Harper [E].
5. **Nothing irreversible**: undo, a recycle area, and keeping the original scan file untouched lower the fear of breaking things, which matters most to older users (Morris & Venkatesh: perceived behavioural control) [E].
6. **Error-tolerant capture**: warn about possible double feeds or missing separators (unusual page count, blank pages), skewed pages and upside-down pages, following NARA's inspection list [G]. Add one-click "rescan these pages".
7. **Built-in QC sampling** following NARA's 10 images or 10% rule [G], with the result stored in the batch log, which also serves KVKK access-logging [G].
8. **Plain Turkish wording**: action verbs, no jargon ("OCR" becomes "Yazıyı oku"), and messages that say what to do next. This addresses the "unfriendly software" cause in Saydam [E].
9. **No surveillance feel**: show time saved per office, not per person, by default. Fear of being monitored is a named cause of resistance [E].
10. **Reads the shadow path** [U]: accept files from a USB stick, an MFP folder or an existing Excel sheet, so the old way feeds the new way instead of competing with it.

---

## 6. Playbook for a chamber office head (13 steps)

1. **Name one problem, not "digitalisation".** Pick the single most hated paperwork job, usually retyping TOBB exports or scanning piles to send on. *Evidence:* perceived usefulness is the strongest driver (Cibaroğlu & Turan 2018), and relative advantage the most consistent (Tornatzky & Klein 1982).
2. **Tell staff early, in person, what will *not* change.** No one loses their job, the paper stays the original, and there is no per-person monitoring. *Evidence:* these are the threats Turkish EBYS staff named (Saydam & Yalçınkaya 2018). Perceived threats drive resistance (Lapointe & Rivard 2005). Notes failed partly because staff heard about it second-hand (Orlikowski 1992).
3. **Time the current job for one week** (minutes per document, with a stopwatch). *Evidence:* observability (Rogers). Without a baseline, time saved cannot be shown.
4. **Choose a champion**: a respected, patient colleague, not necessarily the youngest. Give them a direct line to the developer. *Evidence:* the behaviour of super users decides their effect (Yuan et al. 2015). Older staff follow colleagues' norms (Morris & Venkatesh 2000).
5. **Fix the physical setup before go-live.** Decide where the scanner stands, test scan-to-folder on the real PCs, and make sure separator sheets are printed and within reach. *Evidence:* facilitating conditions (UTAUT) and the SMBv1 failures (vendor notes).
6. **Write the pile rule on one A4 sheet and post it by the scanner**: staples out, sticky notes off, one separator per document, same direction. *Evidence:* Oregon and NARA preparation guidance, and the 37% prep cost share.
7. **Pilot one job with one or two people for two weeks.** Do not roll out office-wide. *Evidence:* trialability (Rogers), and big rollouts that ignored local practice failed (NPfIT/NAO; Heeks).
8. **Run old and new side by side for the pilot**, then stop the old path for that job only. *Evidence:* status-quo bias (Kim & Kankanhalli 2009) means an indefinite parallel run becomes the permanent workaround (workaround literature).
9. **Check quality by sample, not by re-checking everything.** Check the first batch fully, then 10% (at least 10 documents). *Evidence:* NARA 2023, Oregon 2026.
10. **Train one-to-one at the desk, on their own real papers, in short sessions, with the A4 guide left behind.** *Evidence:* Turkish EBYS users found classroom training insufficient (Saydam & Yalçınkaya). Older learners benefit from self-paced, step-by-step practice (Charness/Czaja line of work).
11. **Show the numbers at the weekly meeting**: minutes saved, documents done and errors caught, at office level. *Evidence:* observability, and the fear of being watched (Saydam).
12. **Listen and act on every complaint visibly within a week**, even if the action is "not now, because…". *Evidence:* inaction and responses aimed at the wrong concern make resistance worse (Lapointe & Rivard 2006; Rivard & Lapointe 2012).
13. **Only then add the next job**, and repeat steps 3–12. Keep paper archive practice and registry stamps unchanged until TOBB's legal office confirms otherwise. *Evidence:* Devlet Arşivleri and Resmî Yazışma rules (section 1.6), and the design-reality gap (Heeks).

---

## 7. Unverified items and gaps

- Whether the Resmî Yazışma regulation and the Devlet Arşivleri digitisation rules legally bind TOBB member chambers.
- Articles 7–13 of the Devlet Arşivleri digitisation rules (resolution, formats, destruction).
- Heeks's 35%/50% failure split; the full text of Saleem 2009 and Orlikowski 1992; Esen & Büyük 2014.
- MFP versus dedicated ADF error rates in office use: I found no neutral source.
- No published study on Turkish chamber-of-commerce staff specifically: all Turkish evidence comes from universities and municipalities.
- The cost-share figure (37% prep) comes from a single undated framework.
