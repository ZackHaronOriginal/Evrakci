# Yükle audit: copy

Phase 4, Görev A, screen Yükle. Every Turkish string a user can see or hear on the screen, collected from the code (an AST pass over `yukle.py`,
`yukle_parts.py`, `yukle_side.py`, `yukle_table.py`, `yukle_info.py` and the Yükle entries of `actions.py` and `main_window.py`) and checked against the
vocabulary Kontrol / Emin / Orta / Kontrol / Okunamadı / İncelendi / İncelenmedi. On this screen Kontrol and Okunamadı occur; İncelendi / İncelenmedi and Emin / Orta
do not (they belong to Kontrol and Değerler), but "Dosyalar inceleniyor" and "Hazır" collide with that vocabulary (F-yukle-33). This file records findings only;
proposed rewrites go to `yukle-proposals.md`, which the fix task writes after the owner answers.

Verdicts: ok / unclear / inconsistent / no next step. "Next step" is judged for messages that report a refusal or an error. Findings reference
`yukle-findings.md`. Turkish was read by the auditor; a native-speaker check by the owner is still needed for tone (not done). Pure style strings
(font sizes, object names) and the Windows-only surfaces are left out.

Rows: 84. ok 61, unclear 11, inconsistent 8, no next step 4.

| ID | Where | String | Verdict | Note / finding |
|---|---|---|---|---|
| C-01 | `ui/actions.py (L163)` | Yeni iş oluştur… (menu), Yeni iş oluştur (Ctrl+N) (tooltip) | ok | The dialog it opens is titled "Yeni iş" (C-13), which is fine |
| C-02 | `ui/actions.py (L164)`, `main_window.py (L95)` | Dosya ekle… (menu and bar label), Dosya ekle (Ctrl+O) (tooltip) | inconsistent | The user adds "dosya"; the dialog is "Parti ekle" and the result "N parti eklendi." (F-yukle-33) |
| C-03 | `ui/actions.py (L166)` | Klasör ekle… (menu), Klasör ekle (tooltip) | ok | Tooltip has no key (there is none) |
| C-04 | `ui/actions.py (L218-L220)` | Partiyi yukarı taşı (Alt+Yukarı), Partiyi aşağı taşı (Alt+Aşağı) | inconsistent | Key spelled "Alt+Yukarı" here, "Alt+↑" in the heading hint (F-yukle-34) |
| C-05 | `ui/actions.py (L222)` | Partiyi çıkar (geri alınabilir) (Del) | unclear | Two parentheses in a row (F-yukle-34); "geri alınabilir" is good news worth keeping |
| C-06 | `ui/actions.py (L171)` | Dosya Gezgini'nde göster (Ctrl+Shift+O) | unclear | The user expects the original scan; the app shows its internal copy bN.pdf (O-8) |
| C-07 | `ui/actions.py (L226)` | İptal et (Ctrl+.) | ok |  |
| C-08 | `ui/yukle_side.py (L283-L289)` | Kontrol'e geç, Kontrol sekmesine geç (Ctrl+2) | ok | Accessible name and tooltip differ slightly: both clear |
| C-09 | `ui/main_window.py (L753)` | Ayrıntı panelini gizle (F9) / göster | ok |  |
| C-10 | `ui/actions.py (L224)` | Yeniden adlandır (F2) | ok |  |
| C-11 | `ui/actions.py (L183)`, `yukle_side.py (L290)` | İşi kapat (Ctrl+W) | ok |  |
| C-12 | `ui/yukle.py (L415)` | Taranmış PDF'leri seçin; filter "PDF (*.pdf)" | ok | The dialog title for adding to an open job is "Parti ekle" (C-14) |
| C-13 | `ui/yukle.py (L420)` | Yeni iş / İşin adı: | ok | Buttons are Qt's English OK and Cancel (F-yukle-39) |
| C-14 | `ui/yukle.py (L431)` | Parti ekle (file dialog title) | inconsistent | "Parti" is not in PRODUCT.md's terminology list (O-14, F-yukle-33) |
| C-15 | `ui/yukle.py (L439)` | PDF klasörü seçin | ok |  |
| C-16 | `ui/yukle.py (L451)` | PDF bulunamadı. Yalnızca PDF dosyaları ve klasörleri eklenir. | ok | Says what is accepted |
| C-17 | `ui/yukle.py (L454)` | N dosya alındı, M dosya alınmadı (bir seferde en çok 5.000 dosya). Kalanları ayrı bir parti olarak ekleyin. | unclear | The rest become one batch per file, not "bir parti"; otherwise a good next step |
| C-18 | `ui/yukle.py (L459)` | N dosya sıraya alındı; okuma bitince eklenir. | ok | Not shown for Ctrl+O (F-yukle-17) |
| C-19 | `ui/yukle.py (L413, L426)` | Okuma sürüyor; bitince yeni iş oluşturun. | ok | Also shown for "Dosya ekle…" with no job, where "yeni iş" is what Ctrl+O would do anyway |
| C-20 | `ui/yukle.py (L209)`, `main_window.py (L1441)` | Bir iş sürüyor; bitince açın. / Dışa aktarma ya da okuma sürüyor; bitince başka bir iş açın. | inconsistent | Two sentences for one refusal (F-yukle-35) |
| C-21 | `ui/yukle.py (L346)` | İş açılamadı: <reason>; reason is e.g. "İş dosyası okunamadı: 5139260178f9" | no next step | Shows the internal id, not the name; no advice (F-yukle-20) |
| C-22 | `ui/yukle.py (L520-L522)` | N parti eklendi. / <dosya> eklendi. + Geri al | ok | Long file name: verb cut (F-yukle-08) |
| C-23 | `ui/yukle.py (L557)` | <dosya> işten çıkarıldı. + Geri al | ok | Verb is the first thing lost with a long name (F-yukle-08) |
| C-24 | `ui/yukle.py (L511, L537, L550, L565)` | Parti ekle, N parti ekle, Partiyi taşı, Partiyi çıkar, İşi yeniden adlandır (undo step names) | ok | Shown in "Geri al: …" |
| C-25 | `ui/yukle.py (L565)` | İşi yeniden adlandır / İşin adı: | ok | Buttons are English OK and Cancel (F-yukle-39) |
| C-26 | `ui/yukle.py (L580)` | İşin klasörü bulunamadı. | no next step | Does not say whether to delete the entry or look elsewhere |
| C-27 | `ui/yukle.py (L599)` | Dosya bulunamadı; iş klasörü silinmiş olabilir. | no next step | States a likely cause only |
| C-28 | `ui/yukle.py (L657)` | N. parti bitince belge sayısı ve uyarılar burada görünür. | ok |  |
| C-29 | `ui/yukle.py (L682)` | Evrakçı 0.0.2 – <iş adı> | ok | No length limit on the name |
| C-30 | `ui/yukle.py (L809)` | Ctrl+N ile yeni iş oluşturabilirsiniz | ok | Shown only with no job |
| C-31 | `ui/yukle.py (L817-L828)` | N parti, N sayfa, N belge, N belge kontrol bekliyor | ok | "kontrol bekliyor" matches Kontrol's status bar; Kontrol also says "gerekiyor" (F-kontrol-18) |
| C-32 | `ui/yukle.py (L822)` | Okunuyor: x / y | ok |  |
| C-33 | `ui/yukle.py (L906)` | Dosyalar inceleniyor: N | inconsistent | Shares the stem of İncelendi / İncelenmedi (the review state of documents) (F-yukle-33) |
| C-34 | `ui/yukle.py (L928, L987)` | İptal ediliyor… | ok |  |
| C-35 | `ui/yukle.py (L964)` | İptal edildi; hiçbir şey değişmedi. | ok | Good: says what state the job is in |
| C-36 | `ui/yukle.py (L978-L980)` | Sıradaki N dosya eklenmedi; önceki okuma iptal edildi / tamamlanamadı. + Yine de ekle | ok | "tamamlanamadı" vs the bar's "Okunamadı": close but not the same word |
| C-37 | `ui/yukle.py (L1011-L1012)` | Okunamadı: <core message>. Dosyayı kontrol edip yeniden ekleyin. + Dosya ekle… | unclear | Has a next step; "kontrol edip" uses kontrol as a verb next to the Kontrol state; names one file only; a password-protected file gets the same text (F-yukle-19, F-yukle-33) |
| C-38 | `pipeline/analyze.py`, `store.py` (read only) | Dosya bulunamadı: X / PDF açılamadı: X / PDF boş: X / Sayfa N okunamadı: X | unclear | Say what failed, not what to do; "PDF açılamadı" covers damaged and password-protected files alike. Not edited (D13) |
| C-39 | `ui/yukle.py (L78-L80)` | Partiler / Sürükleyin ya da Alt+↑ / Alt+↓ ile sıralayın. | ok | Key spelled with arrows here, with words elsewhere (F-yukle-34) |
| C-40 | `ui/yukle.py (L101)` | PDF'leri pencerenin herhangi bir yerine bırakın ya da Dosya ekle… (Ctrl+O). Klasörler de olur. | ok | Long; elided at 1024x600 and 150 percent (F-yukle-04) |
| C-41 | `ui/yukle_parts.py (L165)` | Sayfalar okunuyor: x / y | ok |  |
| C-42 | `ui/yukle_parts.py (L62-L65, L57)` | Süre hesaplanıyor… / Yaklaşık N sn kaldı / Yaklaşık N dk kaldı / 3,2 sayfa/sn | ok | Turkish decimal comma |
| C-43 | `ui/yukle_parts.py (L145)` | İptal ederseniz hiçbir şey değişmez. | ok | Does not name the key or button that cancels |
| C-44 | `ui/yukle_parts.py (L117)` | Okuma ilerlemesi (accessible name) | ok |  |
| C-45 | `ui/yukle_parts.py (L192)` | PDF'leri bırakın | ok |  |
| C-46 | `ui/yukle_parts.py (L257)` | Burada PDF yok. Yalnızca PDF dosyaları ve klasörleri eklenir. | ok |  |
| C-47 | `ui/yukle_parts.py (L259)` | N parti, <b>ad</b> işinin sonuna eklenir. | ok | N is capped at 200 (F-yukle-07) |
| C-48 | `ui/yukle_parts.py (L262)` | N partiyle yeni bir iş oluşturulur. | ok |  |
| C-49 | `ui/yukle_parts.py (L274)` | ve N dosya daha | ok |  |
| C-50 | `ui/yukle_parts.py (L222)` | Klasörlerdeki PDF'ler de eklenir, diğer dosyalar atlanır. Vazgeçmek için Esc. | unclear | Whether Esc cancels an OS drag is up to the OS (O-15) |
| C-51 | `ui/yukle_parts.py (L381, L394)` | Henüz iş yok | ok | The inspector and job switch say "İş açılmadı" for the same state (C-75) |
| C-52 | `ui/yukle_parts.py (L396)` | Taradığınız PDF'leri bırakın ya da yeni bir iş oluşturun. | ok |  |
| C-53 | `ui/yukle_parts.py (L415-L426)` | Yeni iş oluştur + Ctrl+N; Dosya ekle… | ok | Button label starts with a space |
| C-54 | `ui/yukle_parts.py (L438)` | İş adı ara | ok |  |
| C-55 | `ui/yukle_parts.py (L447, L486)` | Son işler / İşler / Tüm işler | ok |  |
| C-56 | `ui/yukle_parts.py (L484)` | Açmak için bir iş seçin ya da adını yazın. | ok |  |
| C-57 | `ui/yukle_parts.py (L531-L532)` | N iş daha var; aramak için adını yazın. / aramayı daraltın. | ok | Good next steps |
| C-58 | `ui/yukle_parts.py (L528, L463)` | “x” ile eşleşen iş yok. + Aramayı temizle | ok | Repeats the whole query, also 500 characters |
| C-59 | `ui/yukle_parts.py (L45-L46)` | az önce, N dakika/saat/gün/hafta/ay/yıl önce, dün | ok |  |
| C-60 | `ui/yukle_parts.py (L494-L496)` | İşi aç, Klasörünü Dosya Gezgini'nde göster | ok |  |
| C-61 | `ui/yukle_table.py (L361)` | Taranmış dosyaların sırası. Alt+Yukarı ve Alt+Aşağı ile taşıyın, Del ile çıkarın. | inconsistent | Words here, arrows in the hint (F-yukle-34) |
| C-62 | `ui/yukle_table.py (L126)` | Sürükle (grip tooltip) | ok |  |
| C-63 | `ui/yukle_table.py (L40)` | No, Dosya, Sayfa, QR ayıraç, Durum (headers) | ok |  |
| C-64 | `ui/yukle_table.py (L47-L50)` | Hazır, Kontrol, Okunuyor, Sırada | unclear | "Hazır" is not in the owner's list; "Okunuyor" stays on finished files (F-yukle-31, F-yukle-33) |
| C-65 | `ui/yukle_table.py (L99, L141)` | Toplam, N parti | ok |  |
| C-66 | `ui/yukle_table.py (L159-L162)` | Parti 2: tarama-2.pdf, 2 sayfa, 0 QR ayıraç, Kontrol (spoken) | ok |  |
| C-67 | `ui/yukle_side.py (L222, L321-L322)` | Açık iş; N sayfa; N parti, N belge bulundu | ok | No thousands dot (F-yukle-27) |
| C-68 | `ui/yukle_side.py (L257)` | Ön kontrol | unclear | A pre-check card next to the Kontrol tab and the Kontrol state: easy to read as the same thing (F-yukle-33) |
| C-69 | `ui/yukle_side.py (L263, L328-L331, L347)` | QR ayıraç, Belge, Durum: Hazır / N belge / Okunuyor; şimdilik | unclear | "Durum: N belge" does not say Kontrol (F-yukle-21) |
| C-70 | `ui/yukle_side.py (L273, L167-L168)` | Tarama profili; Tarama bilgisi yok; Dosyalarda tarama görüntüsü bulunamadı | no next step | Does not say whether this matters or what to do; line is clipped (F-yukle-01) |
| C-71 | `ui/yukle_info.py (L138-L144)` | renkli, siyah-beyaz, gri tonlamalı, N dpi, A4 / W × H mm, dosyalardan okundu | ok |  |
| C-72 | `ui/yukle_side.py (L152-L157)` | Rehber'de tarama ayarları; Rehber sekmesinde tarama ayarlarını aç | ok | Lands at the top of Rehber, not on the scanner settings |
| C-73 | `ui/yukle_side.py (L296)` | Okuma bitince açılır. | ok |  |
| C-74 | `ui/yukle_side.py (L230-L231)` | Diğer; Diğer iş komutları | ok |  |
| C-75 | `ui/yukle_side.py (L240)`, `main_window` | İş açılmadı (inspector title, job switch) | inconsistent | "Henüz iş yok" on the page (F-yukle-33) |
| C-76 | `ui/yukle_side.py (L334-L335)` | <ad>: N sayfa, N parti, N belge. N belge kontrol bekliyor. / Hepsi hazır. (accessible description) | unclear | "Hepsi hazır" is read for a job with zero pages (F-yukle-21) |
| C-77 | `ui/yukle_info.py (L61-L62)` | Parti QR ayıraçlı. / N partinin hepsi QR ayıraçlı. | ok |  |
| C-78 | `ui/yukle_info.py (L64-L66)` | Partilerde QR ayıraç yok; belgeleri Kontrol'de filtreyle ya da elle bölün. | ok | Good: says what to do |
| C-79 | `ui/yukle_info.py (L67-L68)` | N parti QR ayıraçlı; 2., 3. … partilerde ayıraç yok, Kontrol'de filtreyle bölebilirsiniz. | unclear | Names every batch: 286 characters with 120 batches (F-yukle-11) |
| C-80 | `ui/yukle_info.py (L57)` | Henüz parti yok. Dosya ekleyin ya da PDF'leri pencereye bırakın. | ok |  |
| C-81 | `ui/main_window.py (L1453)` | Bir iş sürüyor. Durdurup kapatılsın mı? Yazılmış dosyalar klasörde kalır. | ok | Buttons are English Yes and No (F-yukle-39) |
| C-82 | `ui/main_window.py (L1463)` | Durduruluyor… Pencere iş durunca kapanır. | ok |  |
| C-83 | Qt (no translator installed) | OK, Cancel (name dialogs); Yes, No (close confirmation) | inconsistent | English buttons in a Turkish window (F-yukle-39) |
| C-84 | `ui/main_window.py (L811)` | İş kaydedildi 14:32. Değişiklikler zaten kendiliğinden kaydedilir. | ok | Shown for Ctrl+S |
