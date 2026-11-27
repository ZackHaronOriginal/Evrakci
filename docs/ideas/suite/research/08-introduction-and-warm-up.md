# 08 — Introducing Evrakçı to an office: getting in the door, the first demo, and the first weeks

Scope: this report covers what happens before adoption and right at its start: how the tool reaches a chamber, how the first demo goes, how the first weeks are staged, what the app does on first run, and what makes officials trust it. Adoption inside the office (resistance, champions, one-to-one training, paper fallbacks, the 13-step playbook) is in `07-adoption-and-physical-workflow.md` and is not repeated here.

Evidence labels used below:
- **[A]** peer-reviewed or academic source
- **[G]** government, OECD or EU source
- **[C]** case study (usually self-reported by the adopter)
- **[P]** practitioner or vendor source (opinion or the vendor's own data)
- **[U]** unverified: I could not check it against a primary source, or it is my inference

---

## 1. Getting in the door

### 1.1 What the diffusion research says, applied to public bodies

- **Three attributes predict adoption most reliably.** Tornatzky and Klein's meta-analysis of 75 studies found that compatibility, relative advantage and complexity had the most consistent links to adoption [A] (IEEE Trans. Eng. Mgmt. EM-29(1):28–45, 1982, DOI 10.1109/TEM.1982.6447463; summary via https://ieeexplore.ieee.org/document/6447463). For Evrakçı this means three things:
  - **Relative advantage:** hours saved on a job the office already does.
  - **Compatibility:** it produces the same PDFs, Excel and Word files the office already files.
  - **Low complexity:** one guided job, not a platform.
- **People deciding whether to adopt judge differently from people already using a tool.** Karahanna, Straub and Chervany (MIS Quarterly 23(2):183–213, 1999, DOI 10.2307/249751) found two differences [A] (https://www.terry.uga.edu/wp-content/uploads/Karahanna-et-al-1999.pdf):
  - Before adoption, attitude rests on usefulness, ease of use, result demonstrability, visibility and trialability. After adoption it rests mainly on usefulness.
  - For potential adopters, the intention to adopt was determined *solely by normative pressure*, meaning what respected others think and do.
  - **Implication:** at the door, "who else uses it" and "can I see the result" count for more than features. Once staff use it, only real usefulness keeps them.
- **Being told to use something affects acceptance.** Agarwal and Prasad (Decision Sciences 28(3):557–582, 1997) found that different innovation characteristics predicted initial use and continued use, and that perceived voluntariness affected acceptance [A] (https://iaorifors.com/paper/60135). I could not check their specific trialability coefficients **[U]**.
- **Social influence fades with experience.** TAM2 found that social influence matters in mandatory settings and weakens as people gain hands-on experience [A] (Venkatesh & Davis, Management Science 46(2):186–204, 2000, DOI 10.1287/mnsc.46.2.186.11926). UTAUT adds "facilitating conditions" (support and resources) as a direct predictor of actual use [A] (Venkatesh et al., MIS Quarterly 27(3):425–478, 2003, DOI 10.2307/30036540).
- **Public-sector reviews agree.** A systematic review of public-sector innovation lists innovation attributes (relative advantage, compatibility, trialability, observability), peer networks and leadership among the main antecedents of diffusion [A] (De Vries, Tummers & Bekkers, Perspectives on Public Management and Governance 1(3), 2018, https://academic.oup.com/ppmg/article/1/3/159/4841633).
- **Public bodies copy respected peers.** Institutional theory calls this "mimetic isomorphism": organisations imitate peers they see as successful when they are uncertain (DiMaggio & Powell 1983, DOI 10.2307/2095101) [A]. Policy-diffusion research names learning, imitation, competition and coercion as the mechanisms [A] (Shipan & Volden 2008, DOI 10.1111/j.1540-5907.2008.00346.x). US municipal e-government adoption was driven more by external motivations than by internal bureaucratic politics [A] (Jun & Weare, JPART 2011, DOI 10.1093/jopart/muq020).

### 1.2 Who decides

- **A political or top-level sponsor matters more than the business case.** In a study of Dutch municipalities' open-source adoption (input from 51 of 415), "top-down decisions by politicians in the municipality are the most important factor" [A] (van Loon & Toshkov, Government Information Quarterly, 2015; summary at https://interoperable-europe.ec.europa.eu/node/142808). Two other findings:
  - Innovative "boundary spanners" inside the organisation were crucial.
  - Potential cost savings had no discernible effect. I took this from the news summary and could not confirm it in the paper **[U]**.
- **Turkish case: management sponsored, IT recommended.** At Eyüpsultan Municipality (Istanbul), management asked for a cost-cutting study, IT recommended Pardus and LibreOffice, and the municipal administration approved the project [C] (FSF profile, https://www.fsf.org/working-together/profiles/eyupsultan-district-of-turkey; OSOR, https://interoperable-europe.ec.europa.eu/node/702808).
- **Mapping this onto a chamber:**
  - The **secretary general (genel sekreter)** is the operational decision-maker.
  - The **board or president** is the sponsor whose approval gives cover.
  - The **IT person** (often one person, or an outside contractor) can veto on technical grounds.
  - I found no study of software procurement decisions inside Turkish chambers. This mapping is my inference from the chamber structure in Law 5174 **[U]**.
- **Lack of support is the most-cited barrier to open source in public bodies.** A survey of 14 Macedonian municipalities emphasised "lack of support for OSS" as one of the most important obstacles. It also named missing functionality and compatibility with existing software [A] (https://link.springer.com/content/pdf/10.1007/978-3-319-17837-0_11.pdf). This is why Section 5 (trust signals) matters as much as the demo.

### 1.3 Umbrella bodies and word of mouth: the Turkish chamber network

- **TOBB already distributes shared software to chambers.** A TOBB presentation lists three systems [G/C] (https://mobil.tobb.org.tr/HaberResimleri/5614-8.pdf):
  - a central member-registry system used centrally by 306 chambers/exchanges and locally by 27
  - an accounting package used by 230
  - an ATR (export certificate) system used by 159

  The presentation is undated, probably around 2010, so treat the figures as historical **[U]**. TOBB's president has also said the member-management software was "opened to all chambers" (https://uzmanpara.milliyet.com.tr/haber-detay/gundem2/hisarciklioglu-sistemimizi-ogrenmek-istiyorlar/91000/91033/).
  - **Implication:** chambers are used to tools spreading through the TOBB channel. A tool that clashes with TOBB systems, or seems to compete with them, will meet suspicion **[U]**.
- **The accreditation system is a built-in channel for learning from peers.** TOBB's Oda/Borsa Akreditasyon system was modelled on British and German chamber practice. It explicitly includes "networking", "benchmarking" and "good practices" mechanisms [G] (https://tobb.org.tr/EgitimveKaliteMudurlugu/SiteAssets/Sayfalar/OdaBorsaAkreditasyonSistemi/akreditasyon2011.pdf).
  - In July 2026, 73 chambers received certificates, and 289 had completed accreditation against a target of 367.
  - The TOBB president said anyone can see which chamber scored highest in each area [G/press] (https://www.gazetebirlik.com/ekonomi/tobb-tarafindan-2026-akreditasyon-sertifika-toreni-duzenlendi/1051118).
  - **Implication:** an Evrakçı job that produces measurable service or efficiency gains could be presented as an accreditation "good practice". This is an inference **[U]**.
- **Secretaries general already meet regularly.** TOBB holds information seminars for secretaries general, regional consultation meetings that bring together chamber presidents and secretaries general, and pre-election training [G/press] (https://www.haberkenti.com/ayto-genel-sekreteri-kahraman-tobb-seminerinde-yer-aldi; https://haber.tobb.org.tr/ekonomikforum/2017/276/030_039.pdf; https://www.ensonhaber.com/tobb-romada-toplandi.html). These are the natural rooms for peer word of mouth.
- **Geography alone does not spread innovation between Turkish municipalities.** Sobacı and Eryiğit found that neither geographic contiguity nor shared party membership affected e-democracy adoption. Size, status, budget and internet penetration did [A] (Local Government Studies 41(3):445–469, 2015, DOI 10.1080/03003930.2014.995296; https://ideas.repec.org/a/taf/flgsxx/v41y2015i3p445-469.html).
  - **Implication:** spread will come through *networks*, such as TOBB meetings, secretary-general contacts and regional councils, not through being the chamber next door. Better-resourced chambers are likelier first adopters.

---

## 2. The first contact and the demo

### 2.1 What to show

- **Show the result first.** The practitioner "Great Demo!" method (Peter Cohan) recommends "do the last thing first": open with the finished output, then show how it was made [P] (https://pragmaticinstitute.com/resources/webinars/product/create-and-deliver-surprisingly-compelling-software-demonstrations; Gong-based claims via https://salespop.net/sales-management/flip-your-sales-demo-upside-down/, vendor data **[U]**). This matches the pre-adoption importance of *result demonstrability* and *visibility* found by Karahanna et al. [A].
- **Run the demo on their own pile.** Trialability and result demonstrability both drive pre-adoption attitude [A] (Karahanna et al. 1999). Running Evrakçı on a pile the office brought, such as yesterday's membership-certificate requests, combines both. I found no controlled study comparing demos on own documents with demos on generic ones; this is inferred from the attribute evidence **[U]**.
- **Measure the time in front of them.** Relative advantage is the most consistent predictor [A] (Tornatzky & Klein). The demo should time the manual way against the guided way on the same pile and write down both numbers.
- **Keep the scope to one job.** A Dutch-municipality study found that human agency, not rational cost-benefit calculation, explained real diffusion [A] (Homburg & Dijkshoorn 2013, summarised via https://repub.eur.nl/pub/39183/LGS.pdf). One vivid, relevant job persuades more than a full feature list **[U]**.

### 2.2 What never to show

| Avoid | Why |
|---|---|
| Settings, plugin architecture, network sharing, "everything it can do" | Complexity is the attribute that is consistently negative [A] (Tornatzky & Klein) |
| An OCR error left unexplained | Breaks result demonstrability. Show the check step catching it instead: the staff-verification step *is* the safety story |
| Anything implying staff will be replaced or monitored | Normative pressure works both ways. A secretary general will not sponsor what staff will resent **[U]** |
| Live installation struggles | Stage the machine in advance; Eyüpsultan's IT team stressed standardised, quickly prepared desktops (new PC ready in 15 minutes) [C] (https://interoperable-europe.ec.europa.eu/node/702808) |

### 2.3 Leave-behind material

- **One-page summary in plain Turkish.** Write it for the board file:
  - what problem it solves
  - minutes saved on the pile from the demo
  - where data lives
  - licence and cost
  - who made it, and how to get help
  - which chambers already use it

  This follows the normative-pressure finding [A] and the "lack of support" barrier [A].
- **Short video (2–3 minutes) of the same job on generic documents.** Older adults without disabilities often favour self-directed learning with manuals or videos alongside one-to-one help [A] (Frontiers in Computer Science 2021, DOI 10.3389/fcomp.2021.803740, https://www.frontiersin.org/articles/10.3389/fcomp.2021.803740/full).
- **Printed one-job guide.** The minimal-manual research found shorter, task-oriented manuals let first-time users learn about 40% faster with better retention than conventional manuals. This comes from IBM-era studies with method caveats [A] (Carroll et al. 1987, https://davis68.github.io/2016-12-12-ttt-uiuc/files/papers/carroll-minimal-manual-1987.pdf; critique: https://faculty.washington.edu/farkas/dfpubs/Williams-Farkas-MinimalismReconsidered.pdf).

---

## 3. The warm-up period

### 3.1 Pilot one job with one or two people, side by side with the old way

- **Pilots find what lab testing cannot.** Many design shortcomings surface only once a system is used in its real environment [A] (Hertzum, Bansler, Havn & Simonsen, CAIS 30, 2012, https://rucforsk.ruc.dk/ws/files/64454210/Hertzum_et_al_2012_Preprint.pdf). Bansler and Havn also document pilots that "fail" because they produce no lasting result. A pilot needs a defined end and a decision point **[A, via same source]**.
- **Running the old way in parallel guards against the performance dip.** The ERP literature describes a "shakedown" phase after go-live with reduced productivity and more negative user evaluations [A] (Markus et al. 2000, https://castle.eiu.edu/a_illia/MBA5670/ERPsuccess-Markus-et-al2000.pdf). A secondary source puts ERP stabilisation at 3–9 months **[U]** (via https://www.cambridge.org/core/books/secondwave-enterprise-resource-planning-systems/learning-from-adopters-experiences-with-erp-problems-encountered-and-success-achieved/94D8867ED89F52AAC1029598D21A39A5). Evrakçı is much smaller than an ERP. Expect a dip of days, not months, but expect one **[U]**.
- **Train and familiarise before switching.** Eyüpsultan made all users familiar with Linux and LibreOffice before migrating ("doing this before migration helps smooth the transition"). It trained staff for about a year and cited regular training as a main success factor [C] (https://interoperable-europe.ec.europa.eu/node/702808; https://www.linuxcareer.com/pardus-linux-migration-at-eyuepsultan-municipality-in-turkey). Its OS migration was still only about 40% by 2020 [C] (https://www.linuxjournal.com/node/1340817). Warm-up for a whole-desktop change is long; for one job tool it should be far shorter **[U]**.

### 3.2 How long, and why early users drop off

- **Early value is the strongest practitioner signal.** SaaS practitioner data says most churn happens in week one, and users who reach a first value event within days are retained far better. The figures vary and are often anecdotal: "80–90% churn without value in week 1", "82% vs 42% retention" [P **U**] (https://amplitude.com/blog/time-to-value-drives-user-retention; https://www.appcues.com/blog/time-to-value). Treat these as directional only. They come from self-serve web products, not offices.
- **Older or less confident users avoid exploring.** Computer anxiety and low self-efficacy are strong predictors of technology use among adults aged 18–91 (n=1,204) [A] (Czaja et al., Psychology and Aging 21(2):333–352, 2006, DOI 10.1037/0882-7974.21.2.333, https://pmc.ncbi.nlm.nih.gov/articles/PMC1524856). Older adults can be fearful of exploring new applications and less confident [A] (Mahmud et al. 2020, https://www.cs.ubc.ca/labs/edapt/papers/mahmud2020.pdf). The likely early-drop-off causes therefore are:
  - one bad experience, such as an error or lost work, with no one to ask
  - no visible win
  - the tool used only when the champion is present

  This last list is my inference **[U]**.
- **People skip learning when they have work to do.** Carroll and Rosson's "paradox of the active user": people skip manuals and practice to get work done, even when this costs them long term [A] (1987; secondary account via https://threadreaderapp.com/thread/1055166206108467200.html; original not retrieved **[U]**). Warm-up material must therefore be embedded in real work, not scheduled as separate learning.

### 3.3 Celebrate the first saved hours

- **Make the gain visible.** Observability is a Rogers attribute [A] (Rogers, *Diffusion of Innovations*, 5th ed., 2003). Post-adoption attitude is driven by usefulness and image [A] (Karahanna et al. 1999). Make the first win visible to the secretary general and the board. A number ("this week: 412 pages split, about 6 hours saved") gives the sponsor something to repeat at TOBB meetings, which closes the loop with Section 1.3 **[U]**.

---

## 4. In-app onboarding for non-technical users

### 4.1 Tours are skipped and add little

- **NN/g test of tutorials.** In a between-subjects test (n=70) of deck-of-cards tutorials [A-grade practitioner research] (Kendrick, NN/g, 2020, https://www.nngroup.com/articles/mobile-tutorials/):
  - tutorial readers had no better success (91% vs 94% for skippers) and no faster task times
  - readers rated tasks as *harder* (SEQ 4.92 vs 5.49, p=0.047)
  - NN/g recommends contextual help instead
- **Vendor benchmarks on tour completion** [P]:
  - median completion 29% (88 companies)
  - auto-started tours 23% vs user-started 69%
  - 1–2-step tours 73% vs 9+-step tours 8%

  Source: Produktly 2026, https://produktly.com/research/saas-onboarding-benchmarks-2026. Chameleon reports click-triggered 67% vs delay-triggered 31% [P] (https://www.chameleon.io/blog/effective-product-tour-metrics).
  - **Implication:** no auto-playing tour. If there is guidance, it is short, the user chooses to open it, and it is tied to the step they are on.

### 4.2 What to build instead

| Feature | Evidence |
|---|---|
| **Sample job with fake documents** (e.g. 12 generic scanned pages, fake names), runnable in 3 minutes without touching real data | Trialability [A]. The worked-example effect: studying worked examples speeds novice learning (Sweller & Cooper 1985, DOI 10.1207/s1532690xci0201_3) [A]. A low-risk first try also addresses computer anxiety (Czaja 2006) [A] |
| **Reduced first-run surface ("training wheels")**: show only the one job type the office piloted; hide the rest until enabled | Carroll and Carrithers' training-wheels interface blocked common error states. Novices were reportedly faster and more successful (CACM 27(8):800–806, 1984, https://cacmb4.acm.org/magazines/1984/8/10472-training-wheels-in-a-user-interface; the 21% figure comes from a secondary source **[U]**) |
| **Empty states that teach**: an empty job list says what goes here, how to start, and has a "Start the sample job" button | NN/g's three guidelines: communicate status, give learning cues, give direct pathways to key tasks (Kaplan 2021, https://www.nngroup.com/articles/empty-state-interface-design/) [A-grade practitioner research] |
| **Guided first real job**: the same steps as the sample, on the office's own pile, with undo and "nothing is deleted" reassurance | Error-blocking and low anxiety (Carroll; Czaja) [A]. Confirms compatibility with real work [A] |
| **Short checklist** ("1. Try the sample job 2. Do one real job 3. Show the result to your manager") | Practitioner pattern only, with no controlled evidence found [P **U**] |
| **Contextual help on each step** ("?" opens a short plain-Turkish explanation and one picture) | NN/g recommends contextual help over upfront tutorials [A-grade practitioner research] |
| **Printable quick-start sheet** generated from the app, A4, one job per sheet | Minimal manual [A]. Some older adults prefer manuals [A] (Frontiers 2021) |
| **Plain Turkish, no English or technical terms** | In OECD PIAAC (2014–15), almost 40% of Turkish adults reported no computer experience or failed the computer-skills test, against about 15% on average. Only 0.9% reached the top problem-solving level, against 5.4% [G] (https://t4.oecd.org/turkiye/Skills-Matter-Turkey.pdf; https://hurriyetdailynews.com/turkish-adults-score-low-in-literacy-numeracy-problem-solving-oecd-101058). The data is a decade old **[U]** for current office staff |

### 4.3 Preferred learning mode for older and low-digital-literacy staff

- **One-to-one guided learning is the most preferred format** among older adults [A] (Frontiers 2021, above). In-app features should therefore *support* a person-to-person session (handled in report 07), not replace it.
- **Write for someone who has never seen the product.** The app's help should let a colleague teach a colleague: the champion says "press the green button that says *Sıradaki sayfa*" and the screen agrees **[U]**.

---

## 5. Trust signals for officials

### 5.1 Data stays local

- **Turkish public policy already distrusts the cloud.** Presidential Circular 2019/12 says public institutions' data shall not be stored in cloud services except in the institution's own systems or domestic providers under its control. Critical data must be stored securely inside the country [G] (summary: https://www.trthaber.com/haber/bilim-teknoloji/kamu-verileri-bulutta-saklanmayacak-421986.html; https://www.alomaliye.com/2019/07/06/bilgi-ve-iletisim-guvenligi-tedbirleri-2019-12/).
- **Supporting guidance:** The Bilgi ve İletişim Güvenliği Rehberi (first published 24 July 2020) requires critical data to stay in the country. Its version 1.1 (March 2026) notes the Digital Transformation Office was abolished and its powers moved to the Siber Güvenlik Başkanlığı [G] (https://cdn.siberguvenlik.gov.tr/public/docs/bg_rehber.pdf).
- **The legal fit is still open.** Chambers are "public-institution-like professional organisations". Whether the circular binds them directly is something I could not confirm **[U]**.
- **The design argument holds either way.** "Nothing leaves this PC; no internet needed" speaks directly to the policy climate officials know.
- **KVKK language should mirror the Authority's own.** The KVKK Authority publishes a Personal Data Security Guide on technical and administrative measures [G] (https://kvkk.gov.tr/Icerik/2040/Veri-Guvenligine-Iliskin-Yukumlulukler; 2018 edition mirrored at https://www.turmob.org.tr/arsiv/mbs/resmigazete/-veri_guvenligi_rehberi.pdf). In July 2026 it also issued a KVKK compliance guide for public institutions [G] (https://www.kvkk.gov.tr/Icerik/8833/kamu-kurumlari-icin-kisisel-verilerin-korunmasi-kanununa-uyum-rehberi; page unavailable when checked, contents **[U]**).
  - **Proposed KVKK statement:** a one-page statement mapped to the guide's headings, covering where files are stored, who on the network can see what, logs, deletion, and the fact that the developer receives no data. The chamber remains the data controller **[U]** (legal review needed).

### 5.2 Open source, who made it, and the "what if the developer disappears" question

- **Single-maintainer risk is real.** Among popular GitHub projects, most have a truck factor of 1 or 2. Avelino et al. studied 1,932 projects for what happens when all key developers leave [A] (ESEM 2019, DOI 10.1109/ESEM.2019.8870181, https://arxiv.org/pdf/1906.08058.pdf). An early preprint reported 34–46% of projects with a truck factor of 1 (https://peerj.com/preprints/1233v2.pdf). Evrakçı's truck factor is 1, and saying so honestly is better than having an IT person discover it.
- **What reassures, given that support is the top barrier** [A]:
  1. **The app keeps working offline indefinitely.** No licence server, no account, no expiry.
  2. **Outputs are ordinary files** (PDF, XLSX, DOCX) in ordinary folders, so leaving Evrakçı loses nothing (compatibility [A]).
  3. **The AGPL source is public.** Another developer, or TOBB, could continue it.
  4. **A named person with a phone, e-mail and response-time promise**, plus a list of chambers using it.
  5. **The installer and documentation are mirrored somewhere the chamber controls.**

  Items 1–5 are my proposals, not tested **[U]**.
- **Cost and procurement framing:** "Free" removes the procurement step but can read as "unsupported". OSOR's 2025 local-government study treats governance, support and reuse as the sustainability issues for public open source [G] (https://interoperable-europe.ec.europa.eu/collection/open-source-observatory-osor/news/multiple-case-study-public-sector-open-source). Present it as "free to use; support is from the developer; the code belongs to everyone".
- **Peers using it is the strongest signal** at this stage (normative pressure [A]). The first chamber's secretary general's permission to be named is worth more than any feature.

---

## 6. Deliverable: the Evrakçı introduction kit

### 6.1 What to make, in priority order

| # | Item | Type | Why (section) |
|---|---|---|---|
| 1 | **Sample job + fake document set** (one per core job type: split pile, OCR check) built into first run | In-app | Trialability, low anxiety, worked example (2.1, 4.2) |
| 2 | **Training-wheels first run**: choose one job type; others hidden until "Diğer işleri göster" | In-app | Complexity, error-blocking (1.1, 4.2) |
| 3 | **Teaching empty states + per-step "?" help in plain Turkish** | In-app | NN/g; PIAAC Turkey (4.2) |
| 4 | **Saved-time counter** per job and per week, exportable as one line or one page for the manager | In-app | Observability, post-adoption usefulness (3.3) |
| 5 | **One-page summary for the board file** (problem, minutes saved, local data, licence, support, peers) | Print/PDF | Normative pressure, support barrier (1.2, 2.3) |
| 6 | **KVKK and data-location statement** (one page, mapped to KVKK guide headings; legal review) | Print/PDF | Circular 2019/12 climate, KVKK (5.1) |
| 7 | **Continuity statement**: offline forever, plain-file outputs, AGPL, named support, mirror | Print/PDF | Truck-factor and support evidence (5.2) |
| 8 | **Printable A4 quick-start sheet per job**, generated from the app | Print | Minimal manual (2.3, 4.2) |
| 9 | **Demo script**: result first, their pile, timed side by side, one job only, a never-show list | Internal | Great Demo! [P]; Tornatzky & Klein (2.1) |
| 10 | **2–3-minute video** of the sample job, playable offline | Video | Self-directed learners (2.3) |
| 11 | **"Our chamber's result" template** for a secretary general to present at TOBB regional or secretary-general meetings | Print/slides | Network diffusion (1.3) |

Items 1–4 should be built before approaching the first chamber. Items 5–9 can be made in a week. Items 10–11 can wait until the first pilot has produced real numbers.

### 6.2 Step-by-step plan for one chamber, from first contact to three months

**Before contact (week −2 to 0)**
1. **Find the way in.** Get an introduction through someone the secretary general already trusts: another chamber, a TOBB contact, or a local IT contractor. Normative pressure [A] and network-based diffusion [A] support this.
2. **Ask by phone which paper job hurts most** and request a real sample pile for the demo (anonymised if needed).

**First meeting (day 0, 45 minutes, secretary general + IT person + the staff member who does the job)**
3. **Show the finished result first**: named PDFs in a folder, then the steps [P].
4. **Run the job on their pile and time it** against their estimate for doing it by hand. Write both numbers on the one-pager [A, relative advantage].
5. **Show the staff-check step catching an OCR mistake** on purpose. Accuracy is the reason to trust it.
6. **Answer the three trust questions before they are asked**: where the data is, who supports it, and what happens if the developer stops (5.1–5.2).
7. **Leave behind** the one-pager, KVKK statement, continuity statement and quick-start sheet. Offer installation on one PC.

**Week 1: pilot, one job, one or two people**
8. **Install on one PC** (or two on the network if the job is handed between people). Staff run the **sample job first**, then the guided first real job with the developer present or on the phone.
9. **Keep the paper or manual way running in parallel** for the same pile; the dip is expected [A].
10. **Agree a decision point** with the secretary general: "after 20 working days we look at the numbers". This stops a pilot that never ends [A].

**Weeks 2–4: first wins, fix friction**
11. **Call or visit the users at day 3 and day 10.** Early drop-off follows a bad first experience or no visible win [P/A].
12. **Fix the top annoyances quickly.** Pilots exist to find these [A].
13. **At the first full week, send the saved-time line to the secretary general** ("this week: N piles, about X hours"). This is the first celebration, and the sponsor should hear it before anyone asks.

**Day 20–30: decision**
14. **Review the numbers with the secretary general.** If good, stop the parallel run for that job, put the quick-start sheet on the desk, and agree job 2. Handing over to the in-office playbook (report 07) starts here.

**Month 2: widen carefully**
15. **Add a second job or a second staff member, not both.** Enable the hidden job types only for the people who need them (training wheels) [A].

**Month 3: make it observable outside**
16. **Ask permission to name the chamber and its number** in the one-pager for the next chamber.
17. **Offer the "our result" template** for the next TOBB regional or secretary-general meeting.
18. **Record what broke and what convinced them** to feed the next chamber's kit.

---

## 7. Gaps and unverified points

- No study found on how software spreads among Turkish chambers specifically. The TOBB usage figures are old and undated.
- The decision-roles mapping in a chamber (secretary general, board, IT) is inferred, not researched.
- Whether Circular 2019/12 binds chambers directly is not confirmed. The contents of the July 2026 KVKK public-institution guide were not checked (page unavailable).
- No controlled evidence found for "demo on own documents" beyond the trialability and result-demonstrability literature. Onboarding checklists have practitioner support only.
- Time-to-value and churn numbers are vendor data from web SaaS and may not transfer to offline desktop tools in offices.
- The training-wheels 21% figure, the van Loon and Toshkov "cost savings no effect" finding, and the Carroll and Rosson original were seen only through secondary sources.
- PIAAC Turkey data is from 2014–15. I did not confirm whether Turkey took part in the 2023 cycle.
