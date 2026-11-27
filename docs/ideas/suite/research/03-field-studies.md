# 03 · Field studies and research on paperwork and its automation

Written for the Evrakçı suite decision (offline Windows app for a TOBB-member chamber office). Each claim has a URL or DOI.

**Evidence labels:**
- **[peer]**: peer-reviewed study with data
- **[review]**: peer-reviewed literature review
- **[gov]**: government or official document
- **[thesis]**: student thesis
- **[industry]**: consultant or vendor claim with no published method
- **[unverified]**: I could not read the primary text, so the claim comes from a secondary summary or from memory.

---

## 1. How staff really work with paper in public offices

**Paper persists even when the people involved want to go digital.**
- Marathe & Chandra (CHI 2020), *Officers Never Type* [peer]. DOI [10.1145/3313831.3376216](https://doi.org/10.1145/3313831.3376216).
  - Ethnography at the CM Helpline, a state-wide e-governance system in central India.
  - Even "tech-savvy bureaucrats who fully supported" the paperless system made sure paper continued "in abundance".
  - Secretaries printed emails and handed them to officials. Complaints were printed, circulated and piled up after they were resolved.
  - Officials received work from about 300 unknown call-centre operators. Paper gave them back control and accountability.
  - Design advice: integrate the new system into the existing ecosystem, plan the "graceful retirement" of older technologies, be resilient to human errors as well as machine errors, and attend to local history.
  - The paper also summarises earlier HCI/ICTD work: paper persists because it is "cheap, predictable, familiar, and easily enables writing and annotation" (full text read).
- Komito (1998), *Journal of Information Technology* 13(4) [peer]. [aisel.aisnet.org/jit/vol13/iss4/3](https://aisel.aisnet.org/jit/vol13/iss4/3).
  - Ethnography of Lotus Notes in a section of the Irish civil service.
  - Meta-information carried by paper case files was "perceived as necessary for the work of the organization". This restricted the use of electronic case files.
  - Some workers also defined paper-only information as necessary for their job, partly to protect their occupational status. (Abstract only.)
- Sellen & Harper (2002), *The Myth of the Paperless Office*, MIT Press [peer book; read via reviews]. [microsoft.com/en-us/research/publication/myth-paperless-office](https://www.microsoft.com/en-us/research/publication/myth-paperless-office/) and [Emerald review, doi 10.1108/00220410310463518](https://www.emerald.com/insight/content/doi/10.1108/00220410310463518/full/html).
  - Ethnographic and cognitive work in organisations including the UK police and the IMF.
  - People print when they need to read several documents side by side, annotate, or synthesise.
  - Computers win for storage, search and frequent updates.
  - The authors recommend that paper and digital tools "work in concert" rather than chasing a paperless office.
  - The claim that email raised office paper use by 40% comes from a reviewer [unverified].
- Hull (2012), "Documents and Bureaucracy", *Annual Review of Anthropology* [review]. DOI [10.1146/annurev.anthro.012809.104953](https://doi.org/10.1146/ANNUREV.ANTHRO.012809.104953).
  - Argues that bureaucratic documents are artefacts that carry authority (signatures, stamps, registers), not just carriers of information. (Abstract only.)

**Small organisations build their own systems from whatever is at hand.**
- Voida, Harmon & Al-Ani (CHI 2011), "Homebrew databases" [peer]. DOI [10.1145/1978942.1979078](https://doi.org/10.1145/1978942.1979078).
  - Nonprofit volunteer coordinators patch together spreadsheets, paper, email and personal files into ad-hoc "homebrew databases".
  - These create their own information-management problems and expose gaps in how suitable and usable formal databases are.
  - I read only the abstract and summaries. The fine-grained findings (for example duplicate lists drifting apart) are **[unverified]**.

**Why digitisation projects stall.**
- Heeks (2003), iGovernment Working Paper 14 [peer-ish working paper]. [SSRN 3540052](https://papers.ssrn.com/Abstract=3540052).
  - Most e-government-for-development projects fail totally or partially because of "design-reality gaps".
  - Heeks's ITPOSMO dimensions: information, technology, processes, objectives, staffing/skills, management systems, other resources.
  - The often-quoted split (about 35% total failure, about 50% partial failure, about 15% success) is **[unverified]**: I could not open the full text.
- Andersson, Hallin & Ivory (2022), *Government Information Quarterly* 39(1) 101662 [peer]. DOI [10.1016/j.giq.2021.101662](https://doi.org/10.1016/j.giq.2021.101662).
  - Ethnography of a Swedish local authority building RPA in-house for processing applications.
  - Automation was an emergent, negotiated "configuring of work": vested interests, ethics and "algorithmic materialities" shaped what got automated.
  - This helps explain why digitalisation can threaten caseworkers' professional autonomy and lower service quality. (Abstract only.)
- Saydam & Yalçınkaya (2018), *Bilgi ve Belge Araştırmaları* no. 9 [peer, Turkish]. [dergipark.org.tr/en/pub/bel/article/492146](https://dergipark.org.tr/en/pub/bel/article/492146).
  - Likert survey of staff at Bağcılar Municipality and Marmara University during EBYS (electronic document management) rollout.
  - Success depended on informing staff, collecting their opinions, involving them in the project, top-management support, and **continuous** training.
  - Negative staff reactions made the system hard to sustain.

**Summary of section 1.** Paper does not persist because staff "resist technology". It persists because:
- paper carries authority, context and accountability;
- paper fits annotation and side-by-side checking;
- new systems take control away from existing actors.

Projects stall when the design assumes a cleaner process than the real one.

---

## 2. Human-in-the-loop data capture: verification, reviewer errors, automation bias

**"Look and confirm" checking is barely better than nothing.**
- Barchard & Pace (2011), *Computers in Human Behavior* 27(5):1834-1839 [peer]. DOI [10.1016/j.chb.2011.04.004](https://doi.org/10.1016/j.chb.2011.04.004).
  - Randomised experiment: 195 participants entered 30 data sheets each, under double entry, visual checking, or single entry.
  - Visual checking produced about 29 times as many errors as double entry (reported as "2958% more"). It was **not significantly better than single entry**.
  - 66% of visual checkers produced a wrong coefficient alpha.
  - In lab posters from the same group: double entry averaged 0.38 errors, visual checking 10.8, single entry 12.0. Double entry took about 31% longer than visual checking ([UNLV lab poster](https://img.faculty.unlv.edu/lab/conference-presentations/Conference%20Posters%205/Data%20Entry%2017%20kim%20july%2030.pdf)).
- Barchard & Verenikina (2013), *CHB* 29:1917-1922 [peer]. DOI [10.1016/j.chb.2013.02.021](https://doi.org/10.1016/j.chb.2013.02.021).
  - Double entry and read-aloud checking beat visual checking. Exact figures **[unverified]**, from lab summaries.
- Limits: these are lab studies with students, and human-keyed values were checked against paper, not OCR output. The OCR-review situation (a machine value shown next to an image) is closer to "visual checking" and probably at least as weak, because the pre-filled value anchors the reviewer (next block).

**Pre-filled values anchor reviewers.**
- Beck, Eckman, Kern & Kreuter (2025), "Bias in the Loop", arXiv [preprint, preregistered RCT]. [arxiv.org/abs/2509.08514](https://arxiv.org/abs/2509.08514).
  - 2,784 annotators checked AI-suggested emission values from corporate report tables. Four of seven scored items were wrong.
  - Overall accuracy was only about 66-68%.
  - Reviewers caught digit-swap "spelling" errors about 82% of the time, wrong-year or wrong-column errors about 77% of the time.
  - Errors that needed **rule knowledge** were caught only about 31% of the time.
  - Requiring the reviewer to type the correct value when rejecting gave a small accuracy gain (68% vs 66%, p=0.028).
  - Performance bonuses had no effect. AI-skeptical reviewers caught more errors.
  - Time spent on wrong and right suggestions was the same (54 vs 55 s). Reviewers did not slow down on errors.
- Fochmann, Müller & Overesch (2021), *Journal of Economic Psychology* 83:102365 [peer]. DOI [10.1016/j.joep.2021.102365](https://doi.org/10.1016/j.joep.2021.102365).
  - Tax-filing experiment: correct prefilling helps, incorrect prefilling has asymmetric effects.
  - The related literature concludes that prefilling is worthwhile "only if it is done with highly reliable information" ([Exeter repository](https://ore.exeter.ac.uk/repository/handle/10871/29935)).
- Lingren et al. (2014), *JAMIA* 21(3):406-413 [peer]. DOI [10.1136/amiajnl-2013-001837](https://doi.org/10.1136/amiajnl-2013-001837).
  - Counterpoint: dictionary pre-annotation of clinical text cut annotation time without measurable bias.
  - That held for **trained expert annotators** with good pre-annotations. The size of the speed-up is **[unverified]**.

**Automation bias is robust, and training does not remove it.**
- Parasuraman & Manzey (2010), *Human Factors* 52(3):381-410 [review]. DOI [10.1177/0018720810376055](https://doi.org/10.1177/0018720810376055).
  - Complacency and automation bias occur in novices and experts and do not go away with practice.
  - Bias produces omission errors (missing what the aid missed) and commission errors (following wrong advice).
  - It is "difficult to prevent by training or instructions". Attention is the shared mechanism.
- Goddard, Roudsari & Wyatt (2012), *JAMIA* 19(1):121-127 [systematic review, 74 studies]. DOI [10.1136/amiajnl-2011-000089](https://doi.org/10.1136/amiajnl-2011-000089), [PMC3240751](https://pmc.ncbi.nlm.nih.gov/articles/PMC3240751).
  - Wrong advice was followed more often with decision support than without (pooled RR 1.26, 95% CI 1.11-1.44).
  - Users changed correct answers to wrong ones in 6-11% of consultations.
  - Overall performance still usually **improved** with the aid.
  - Mediators: workload, time pressure, task complexity, and badly calibrated trust.
  - Mitigators:
    - per-item (not fixed) confidence display (McGuirl & Sarter);
    - less prominent advice, since prominent wrong advice was followed more often;
    - offering information rather than commands;
    - users' felt accountability.

**Does confidence highlighting help?** Mixed and weak.
- Kuhn, Kersken & Zimmermann (CHI EA 2025) [peer, short paper]. [arxiv.org/abs/2503.15124](https://arxiv.org/abs/2503.15124).
  - Speech-recognition correction study with 36 participants.
  - Confidence scores were poor error detectors: they missed real errors or flagged many correct words.
  - Confidence highlighting **did not speed up correction**, and participants did not find it helpful.
- A 1990s OCR patent states the practitioner observation that proofreaders "become complacent and overlook errors" even at high recognition rates, and that many OCR errors are not misspellings ([US 6,453,079](https://patents.google.com/patent/US6453079B1)) [industry/patent, not a study].
- I found **no controlled study** of confidence highlighting in OCR field review specifically. **[gap]**

**Large-scale public data capture.**
- The US Census Bureau evaluated OCR, OMR and key-from-image capture for Census 2000:
  - Evaluation K.1.b ([archived PDF](https://webarchive.library.unt.edu/eot2008/20081105130025/http:/www.census.gov/pred/www/rpts/K1b.pdf));
  - Topic Report TR-3 ([census.gov](https://census.gov/history/pdf/census2000datacapture-032020.pdf));
  - GAO update ([GAO AIMD-00-324R](https://www.gao.gov/products/aimd-00-324r)).
- The architecture was OCR first, with low-confidence fields routed to human key-from-image. Forms were designed for OCR ([Census working paper](https://www.census.gov/content/dam/Census/library/working-papers/2021/econ/1990_NRP2.pdf)).
- I could not open the reports, so the actual per-mode error rates are **[unverified]**.

---

## 3. RPA and intelligent document processing in the public sector

- Kaitosalmi & Ratia (HICSS 2025; KMIS 2024) [peer]. [Aalto record](https://research.aalto.fi/en/publications/from-manual-to-automated-a-multi-case-study-of-utilizing-robotic-/), [KMIS 2024 PDF](https://scitepress.org/Papers/2024/129471/129471.pdf).
  - Multi-case study of two Finnish healthcare districts.
  - RPA and intelligent automation improved efficiency, standardisation and resource use.
  - **Technical faults, poor process readiness and unmet user expectations** hindered implementation.
  - Benefits were rarely monitored after go-live.
- Lindgren, Åkesson, Thomsen & Toll (2022), in *Service Automation in the Public Sector*, Springer [peer chapter]. [IDEAS](https://ideas.repec.org/h/spr/prochp/978-3-030-92644-1_10.html).
  - Two Swedish municipal RPA cases, focused on how organising the work (ownership, competence, who maintains the bots) shapes the outcome.
  - About 16 Swedish municipalities had automated social-assistance decisions after Trelleborg's 2017 start ([Lund record](https://lup.lub.lu.se/record/e077e2a3-71b7-421e-b35d-997fe73d5329)).
  - [AlgorithmWatch](https://algorithmwatch.org/en/trelleborg-sweden-algorithm/) [NGO] documents transparency and oversight problems at Trelleborg.
- Turkish and Swedish public organisations scaling RPA [peer]. *Transforming Government*, DOI [10.1108/TG-11-2021-0193](https://www.emerald.com/insight/content/doi/10.1108/TG-11-2021-0193).
  - Problems appear "particularly when adoption outpaces the development of governance".
  - Details **[unverified]** beyond the abstract.
- Syed et al. (2020), *Computers in Industry* 115:103162 [review]. DOI [10.1016/j.compind.2019.103162](https://doi.org/10.1016/j.compind.2019.103162).
  - Structured review that finds RPA practice far ahead of theory.
  - Sets out 15 open challenges across benefits, readiness, capabilities, methods and technology.
- EY, "Get ready for robots" (2016) [industry, no method]. [PDF](https://www.eyfinancialservicesthoughtgallery.ie/wp-content/uploads/2016/11/ey-get-ready-for-robots.pdf).
  - "As many as 30 to 50% of initial RPA projects fail", based on EY's rescue engagements.
  - Widely re-quoted, but it is not a measured rate.
- Vendor and consultant success claims [industry, self-reported]:
  - Irish Road Safety Authority: a bot handles about 80% of a task, about 2,500 days saved ([UiPath](https://hubspot-proxy.uipath.com/resources/automation-case-studies/road-safety-authority-adopting-rpa)).
  - Irish government RPA framework: 14,800 working days saved ([Deloitte](https://www.deloitte.com/ie/en/Industries/government-public/research/rpa-framework-impact-report.html)).
  - There is no independent evaluation of either figure.
- Brittleness when screens or forms change is widely asserted in practitioner writing, for example ([CIO.com](https://www.cio.com/article/3433181/the-dark-side-of-robotic-process-automation.html)) [industry]. I found no peer-reviewed measurement of maintenance load. **[gap / unverified]**

**Summary of section 3.**
- Peer-reviewed cases agree: gains are real but modest and local.
- Failures come from process readiness, expectations, governance and fragile technology, not from the core idea.
- Headline savings figures come almost only from vendors.

---

## 4. End-user configurable tools and spreadsheet error research

**Spreadsheets.**
- Panko (1998), *Journal of Organizational and End User Computing* 10(2):15-21 [review]. DOI [10.4018/joeuc.1998040102](https://doi.org/10.4018/joeuc.1998040102). Updated versions: [arXiv 0802.3457](https://arxiv.org/abs/0802.3457) and [arXiv 1602.02601](https://arxiv.org/abs/1602.02601) (2016).
  - Every empirical study has found unacceptable error rates.
  - Development experiments give a cell error rate of about 1-5% (3.9% average across 14 studies, 967 participants), so most large sheets contain errors.
  - Experienced users err too.
  - Individual inspectors find only about 50-60% of seeded errors. Group inspection raises this to about 70-80%.
  - Panko argues error rates in spreadsheets match those in other human cognitive work.
- Ziemann, Eren & El-Osta (2016), *Genome Biology* 17:177 [peer]. DOI [10.1186/s13059-016-1044-7](https://doi.org/10.1186/s13059-016-1044-7).
  - 19.6% of papers with Excel gene lists had names silently auto-converted (for example to dates).
  - The 2021 follow-up found 30.9%, despite awareness ([PLoS Comp Biol](https://doaj.org/article/8b429b7b5d454a8c9aeef110207e3418)).
  - Excel's type guessing corrupts identifiers. This matters for vergi numbers, sicil numbers and leading zeros.
- Public Health England, October 2020 [gov/press].
  - 15,841 COVID cases were left out of daily figures because a pipeline used the legacy XLS format, which has a row limit ([The Register](https://www.theregister.com/2020/10/05/excel_england_coronavirus_contact_error/)).
  - Silent truncation in a file format, not human typing, caused the loss.

**End-user programming and tailoring.**
- Ko et al. (2011), *ACM Computing Surveys* 43(3):21 [review]. DOI [10.1145/1922649.1922658](https://doi.org/10.1145/1922649.1922658).
  - End users face the same problems professional programmers do: specification, reuse, testing and debugging.
  - But they do not see themselves as programmers and rarely test.
  - Risk, reward, self-efficacy and "surprise" drive whether they use quality tools.
- Gantt & Nardi (CHI 1992), "Gardeners and Gurus" [peer]. DOI [10.1145/142750.142767](https://doi.org/10.1145/142750.142767).
  - In CAD offices, customisation was done by a few **local developers**: domain experts who build and share extensions for colleagues.
  - Formally recognising that role, with time and credit, was generally successful.
- MacLean et al. (CHI 1990), "User-tailorable systems: pressing the issues with buttons" [peer]. DOI [10.1145/97243.97271](https://doi.org/10.1145/97243.97271).
  - Tailoring worked when there was a "tailoring culture" and a gradual path from small tweaks to deeper changes.
  - A "customization gulf" opens once tailoring goes beyond setting parameters ([Wulf et al. 2008](https://www.wineme.uni-siegen.de/paper/2013/wulfetal2008_compbastailor_ijhcs.pdf)).
  - These details come from secondary sources **[unverified in primary]**.

**Summary of section 4.** Non-programmers succeed at configuration when:
- the steps are small and reversible;
- results are visible immediately on real examples;
- one local expert owns the shared templates.

They fail when they author free-form logic that nobody tests.

---

## 5. Turkish context: e-Yazışma, KEP, EBYS, chambers

- The Resmî Yazışmalarda Uygulanacak Usul ve Esaslar Hakkında Yönetmelik (RG 10.06.2020, no. 31151) [gov] applies to "bütün kamu kurum ve kuruluşları" and makes the electronic medium the default for preparing, signing, sending and storing official correspondence ([CSGB PDF](https://csgb.gov.tr/Media/jcomj5ra/resmi-yazışmalarda-uygulanacak-usul-ve-esaslar-hakkında-yönetmelik.pdf)).
  - Whether, and how far, it binds chambers (kamu kurumu niteliğindeki meslek kuruluşu) is **[unverified]**. Check the definitions article or ask TOBB.
- The 2017/21 Prime Ministry circular makes KEP the default channel for official electronic correspondence unless parties agree otherwise ([Lexpera](https://www.lexpera.com.tr/mevzuat/genelgeler/e-yazisma-projesi-ile-ilgili-2017-21-sayili-basbakanlik-genelgesi-2017-21)) [gov].
  - A Türkiye Barolar Birliği report explains how KEP is used by people outside EBYS ([TBB KEP Raporu](https://d.barobirlik.org.tr/komisyon/bilisim/raporlar/KEP_Raporu.pdf)) [NGO].
- Academic work in *Bilgi Dünyası* covers KEP/e-Yazışma integration and EBYS interoperability, mostly descriptive or legal analysis, not field observation ([bd.org.tr article](https://bd.org.tr/index.php/bd/article/download/79/72/143)) [peer].
- The Oda Muamelat Yönetmeliği governs how chambers register and keep evrak, belge and defter ([Lexpera](https://www.lexpera.com.tr/resmi-gazete/metin/oda-muamelat-yonetmeligi-25934)) [gov]. Evrakçı's export and index rules should be checked against it.
- Demir (2019), Okan University master's thesis on MERSİS in trade registry offices [thesis] ([record](https://gcris.okan.edu.tr/items/44c9e9f2-9929-486b-acd4-3ca3fe205d1c)).
  - Users reported gaps in MERSİS.
  - Permit, approval and fee steps still lacked inter-agency integration.
  - The author notes that academic literature on chambers and registry work is "very limited".
- Ertuğrul & Tekin (2016) describe process management at Denizli Ticaret Odası [peer] ([DergiPark](https://dergipark.org.tr/tr/download/article-file/424154)).
- TOBB's "Dijital Dönüşüm Hareketi" and Akıllı KOBİ target member SMEs, not chamber back offices. TOBB says it is training digital-transformation specialists across its 366 chambers and exchanges ([Ekonomi Gazetesi](https://www.ekonomigazetesi.com/sektor-haberleri/hisarciklioglu-dijitallesme-bir-secenek-degil-zorunluluk-42832)) [press/industry].
- **Gap:** I found no ethnographic or time-and-motion study of Turkish chamber back-office paperwork. The field evidence for Evrakçı's users would have to come from the owner's own office observation.

---

## 6. Design rules for Evrakçı (evidence-backed)

1. **Do not rely on "look at the value and press OK" as the quality control for important fields.**
   - Visual checking was not significantly better than no checking (Barchard & Pace 2011).
   - Reviewers spend the same time on wrong and right suggestions (Beck et al. 2025).
   - For key identifiers (vergi no, sicil no, amounts, dates), require an *active* check:
     - retype the value blind, or the last N digits;
     - or check it against an independent source (checksum, TOBB export, earlier record).
2. **When a reviewer rejects a value, make them type the correct one.** This gave a measurable accuracy gain at no extra cost (Beck et al. 2025).
3. **Use rule checks as well as human eyes, especially for errors that need domain knowledge.**
   - Reviewers caught digit swaps about 82% of the time but rule-based errors only about 31% of the time (Beck et al. 2025).
   - Add the checks to the software: VKN/TCKN checksum, date ranges, totals that must add up, cross-field consistency.
4. **Leave a field empty when OCR is unsure instead of filling it with a guess.**
   - Wrong defaults are accepted and raise error rates; prefilling pays only with highly reliable data (Fochmann et al. 2021; Goddard et al. 2012).
   - Show only high-confidence values pre-filled. Show low-confidence fields empty, with the image crop beside them.
5. **Show confidence per field and keep it understated. Do not rely on it to find errors.**
   - Per-item confidence improves appropriate reliance, and prominent advice is over-followed (Goddard et al. 2012, citing McGuirl & Sarter and Berner).
   - Confidence highlighting alone did not speed up correction (Kuhn et al. 2025).
   - Measure Tesseract's confidence calibration on the chamber's own forms before using it to skip review.
6. **Expect automation bias to persist. Design against it instead of training it away.**
   - Training and instructions barely help (Parasuraman & Manzey 2010).
   - Workload and time pressure make it worse (Goddard et al. 2012).
   - Useful measures: occasional seeded known-wrong values ("kontrol örneği") to measure each reviewer's catch rate; batch sizes that avoid end-of-day rush; a visible record of who approved each value.
7. **Treat paper as part of the workflow, not as the enemy.**
   - Paper persists because it carries authority and supports side-by-side checking (Marathe & Chandra 2020; Sellen & Harper 2002; Komito 1998).
   - Support printing well: labels, cover sheets with a barcode or QR job ID, printable check lists.
   - Keep links back to the original paper (box or folder number) instead of promising "paperless".
8. **Never let Excel guess types on export.**
   - Write identifiers as text with explicit formats, use .xlsx not .xls, and check row counts after writing.
   - Silent auto-conversion and truncation are well documented: 20-31% of genomics papers affected (Ziemann et al. 2016/2021); 15,841 missing COVID cases at PHE in 2020.
9. **Make template and mapping editing a small, visible, reversible activity owned by one local expert.**
   - Local developers who share templates with colleagues are what made tailoring work (Gantt & Nardi 1992; MacLean et al. 1990).
   - Concretely:
     - templates are edited on a real sample page with an instant preview;
     - every change is versioned and can be reverted;
     - one "şablon sorumlusu" role publishes shared templates on the LAN;
     - ordinary staff only pick templates.
10. **Test user-made templates and mappings automatically, because end users don't test.**
    - About 1-5% cell error rates, and single inspectors find only about half of errors (Panko 1998/2016; Ko et al. 2011).
    - Keep a few golden sample documents per template. Re-run them when the template changes, and block publishing if expected values change.
11. **Expect forms to change and fail loudly.**
    - RPA and IDP projects break on technical faults and process changes, and benefits go unmonitored (Kaitosalmi & Ratia 2024/2025; EY 2016 [industry]).
    - Detect layout drift: anchor-box mismatch, or a sudden drop in the confidence distribution. Stop and ask instead of extracting garbage.
    - Keep a simple per-template accuracy log over time.
12. **Roll out one job at a time with staff involved, and keep the old path available.**
    - EBYS rollouts in Turkish public bodies depended on informing and involving staff and on continuous training (Saydam & Yalçınkaya 2018).
    - Projects fail on design-reality gaps (Heeks 2003).
    - New systems should plan the graceful retirement of old ones (Marathe & Chandra 2020).
    - Start with the most repetitive job (for example scan, split and send), measure time and errors before and after, and add the next module only after that.

---

## 7. What I could not verify / gaps

- Heeks's 35/50/15 failure split; Census 2000 per-mode error rates; Barchard & Verenikina 2013 figures; Lingren speed-up size; MacLean "gentle slope" wording; details of Voida 2011 and the TG-11-2021-0193 paper: only abstracts or secondaries read.
- No controlled study found of OCR confidence highlighting in form-field review, or of keying vs verifying speed with OCR pre-fill in an office setting.
- No peer-reviewed measurement of RPA or IDP maintenance load after form changes.
- No field study of Turkish chamber back-office paperwork. Whether the 2020 correspondence regulation applies to chambers is unconfirmed.
