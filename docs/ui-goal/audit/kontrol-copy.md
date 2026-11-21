# Kontrol audit: copy

Phase 4, Görev A, screen Kontrol. Every Turkish string a user can see or hear on the screen, collected from the code (an AST pass over
`kontrol.py`, `kontrol_actions.py`, `kontrol_dialogs.py`, `kontrol_empty.py`, `kontrol_inspector.py`, `kontrol_overview.py`,
`kontrol_review.py`, `kontrol_paint.py`, `timeline.py`, `loupe.py` and the Kontrol entries of `actions.py`) and checked against the
vocabulary Kontrol / Emin / Orta / Kontrol / Okunamadı / İncelendi / İncelenmedi. On this screen only Kontrol, İncelendi and
İncelenmedi occur (Emin, Orta and Okunamadı belong to Değerler). This file records findings only; proposed rewrites go to
`kontrol-proposals.md`, which the fix task writes after the owner answers.

Verdicts: ok / unclear / inconsistent / no next step. "Next step" is judged for messages that report a refusal or an error.
Findings reference `kontrol-findings.md`. Turkish was read by the auditor; a native-speaker check by the owner is still needed for
tone (not done).

| ID | Where | String | Verdict | Note / finding |
|---|---|---|---|---|
| C-01 | Command bar tooltip, menu, context menu | "Burada kes / kesimi kaldır (K)", "Burada kes" | ok | one command, toggling; the tooltip says both halves |
| C-02 | same | "Önceki belgeyle birleştir (M)" | ok | |
| C-03 | same | "Sağa döndür (R)", "Sola döndür (Shift+R)" | ok | |
| C-04 | Command bar tooltip for Space | "Sayfayı büyük göster (Boşluk)" | inconsistent | first of three names for one command, F-kontrol-17 |
| C-05 | Menu Görünüm, palette, context menu | "Önizle" | inconsistent | second name, F-kontrol-17 |
| C-06 | Command bar, menu, context menu | "Sayfayı sil (geri alınabilir) (Del)", "N sayfayı sil", "Sayfayı geri getir", "N sayfayı geri getir" | ok | label follows the count and the state; the tooltip tells it can be undone |
| C-07 | Command bar, menu, inspector, context menu | "Şablonu uygula (T)", "Şablon uygula", "Şablon uygula ›" | ok | object case differs between tooltip (Şablonu) and rows (Şablon); both are normal imperatives |
| C-08 | Command bar, menu, dialog | "Filtre uygula (F)", "Filtre uygula…", dialog title "Filtre uygula", confirm "Filtreyi uygula" | ok | |
| C-09 | Command bar | "Sonraki kontrol (N)", "Sonraki incelenmemiş (U)" | ok | uses the vocabulary |
| C-10 | Command bar, menu | "Belgeye veya sayfaya git (Ctrl+G)"; Ctrl+F menu item "Bul…" opens the same dialog | inconsistent | "Bul…" is B-026 (S4, already in the ledger) |
| C-11 | Command bar | "Ayrıntı panelini gizle (F9)" / "göster (F9)" | ok | |
| C-12 | Command bar, inspector | "Diğer komutlar", "Diğer", "Diğer belge komutları" | ok | |
| C-13 | Command bar | "Geri al: Şablon uygula (Ctrl+Z)", "Yinele: 3 sayfayı sil (Ctrl+Y)" | unclear | the step names carry no detail (which template, which pages), O-15 |
| C-14 | Inspector button, menu, palette | "Belgeyi onayla" | inconsistent | the action is "onayla" but the state is "İncelendi", F-kontrol-14 |
| C-15 | Inspector button, context menu, menu | "Değerlerde aç" | ok | |
| C-16 | Inspector, nothing selected | "Belge seçilmedi", "Bir sayfaya tıklayın ya da oklarla gezinin." | ok | tells what to do; mentions the mouse first, the keyboard second |
| C-17 | Inspector group | "Neden burada başlıyor" | ok | clear |
| C-18 | Inspector row keys | "Kesim", "Önceki", "Durum"; values "Yok", "Belge 13, 4 sayfa" | ok | "Önceki" alone is short but the value explains it |
| C-19 | Inspector, guide tab, loupe | "İşin başı", "Elle kesim", "Filtre, her 2 sayfada", "QR ayıraç" | ok | |
| C-20 | Inspector reason | "İşin ilk belgesi.", "Elle kesildi.", "QR ayıraç sayfası ayırdı.", "QR ayıraç yok, filtre kesti." | ok | full sentences with a full stop |
| C-21 | Cut label, accessible names | "QR ayıraç" | inconsistent | spelling differs from C-22, F-kontrol-15 |
| C-22 | Separator tile | "Ayraç 4" | inconsistent | F-kontrol-15 |
| C-23 | Inspector group | "Seçim: 3 sayfa (1–3)", "(sayfa 5)" | ok | |
| C-24 | Inspector rows | "Şablon yok", "Her 2 sayfa" | ok | |
| C-25 | Inspector group | "Son değişiklikler" | ok | |
| C-26 | History rows and toasts | "Kesim eklendi, sayfa 3", "Kesim kaldırıldı, sayfa 3", "3 sayfa sağa döndürüldü", "Belge 2, Belge 1 ile birleşti" (history) and "...birleştirildi." (toast) | ok | history and toast use two verb forms for the same merge; harmless |
| C-27 | Status line (Del on a separator) | "Ayraç sayfaları zaten dışa aktarılmaz. Kesimi kaldırmak için M." | ok | says what to do; spelling per F-kontrol-15 |
| C-28 | Status line | "Önce sayfaları seçin.", "Önce bir sayfa seçin." | ok | two forms for two situations (pages vs one page) |
| C-29 | Status line (M on a filter-started document) | "Bu kesimi filtre yaptı; filtreyi değiştirin (F)." | unclear | the sentence is awkward ("this cut was made by the filter") but says what to do |
| C-30 | Page tooltip and screen reader | "Sayfa 73, Belge 16, kontrol gerekiyor, incelenmedi, silinecek" | inconsistent | "gerekiyor", F-kontrol-18 |
| C-31 | Rider accessible name and tooltip | "Kontrol gerekiyor"; "Bu belge kontrol bekliyor" | inconsistent | two verbs on one widget, F-kontrol-18 |
| C-32 | Status line | "İlk belgenin öncesi yok.", "Bu ilk belge.", "Bu son belge." | ok | refusals that say why |
| C-33 | Status line and history | "Belge 3 onaylandı; bu son belge.", "Belge 2 onaylandı" | inconsistent | "onaylandı" vs İncelendi, F-kontrol-14 |
| C-34 | Status line and toast | "Kontrol bekleyen belge yok.", "Kontrol gereken tek belge bu." | inconsistent | "bekleyen" and "gereken" add two more forms, F-kontrol-18 |
| C-35 | Status line | "Bütün belgeler incelendi." | ok | uses the vocabulary |
| C-36 | Toast, history | "Sayfa 2 silinecek." | ok | "silinecek" matches the caption "Silinecek" and says the page is only marked |
| C-37 | Toast | "Belge 1: bütün sayfaları silinecek, belge dışa aktarılmayacak." | ok | says the consequence; next step is the "Geri al" button |
| C-38 | Toast action | "Geri al" | ok | |
| C-39 | Overview accessible name and description | "Tüm iş: 3 belge"; "Belge 1–3 görünüyor, toplam 3, 1 belge kontrol bekliyor, 0 belge incelendi" | unclear | reads as one run-on list for a screen reader; "bekliyor" per F-kontrol-18 |
| C-40 | Status bar | "Belge 1 / 3", "Sayfa 1 / 15", "2 sayfa seçili" | ok | |
| C-41 | Status bar | "⚠ 1 belge kontrol bekliyor" | ok | icon and word |
| C-42 | Status bar | "✓ 0 / 3 incelendi" | ok | |
| C-43 | Empty state | "Henüz açık iş yok", "Kesimleri görmek için Yükle'den bir iş açın.", "Yükle'ye git", "Yeni iş oluştur", "Son işler", "15 sayfa, az önce"; tooltip "Yükle sekmesine geç (Ctrl+1)" | ok | says what is missing and how to get it |
| C-44 | Filter dialog | "Her belgedeki sayfa sayısı", "Seçili 6 sayfa, her biri aynı sayıda sayfadan oluşan belgelere ayrılır.", "Örnek: önlü arkalı tek yapraklı belgeler için 2.", "Vazgeç", "Filtreyi uygula" | unclear | does not say what happens to a short last group (it gets the check "Eksik sayfa"); not a wrong text |
| C-45 | Go-to dialog | "Belgeye veya sayfaya git", "Belge", "Sayfa", "Belge numarası", "Sayfa numarası", "1 ile 15 arası", "Vazgeç", "Git" | ok | |
| C-46 | Status line, menus | "Önce Şablonlar sekmesinde bir şablon oluşturun." (status), "Önce Şablonlar sekmesinde bir şablon oluşturun" (disabled menu item, no full stop), "Önce sayfaları ve bir şablonu seçin.", "Kapasite Raporu uygulandı, 5 sayfa" | ok | next step named; the menu item has no stop, which is normal for a menu |
| C-47 | Status line (on open) | "Onaylanan belgeler okunamadı; onaylar yeniden yapılmalı." | ok | says what to do; uses "onay", F-kontrol-14 |
| C-48 | History | "Filtre her 2 sayfa, sayfa 3–5" | ok | |
| C-49 | Status line (approve cannot be saved) | "Onay kaydedilemedi; iş klasörüne yazılamıyor." | no next step | F-kontrol-16 |
| C-50 | Inspector accessible name | "Belge ayrıntısı" | ok | |
| C-51 | Timeline accessible description | "Belgeler sırayla. Oklar sayfa değiştirir, Shift ile seçim genişler, Boşluk önizler, Enter belgeyi onaylar." | inconsistent | "onaylar" (F-kontrol-14); promises Shift+arrows, which select the wrong pages when a row wraps (F-kontrol-02) |
| C-52 | Inspector button accessible name | "Belge 1 onayla (Enter)" | inconsistent | F-kontrol-14; Enter does nothing on this focused button (F-kontrol-04) |
| C-53 | Captions | "73 Silinecek", "73 Boş" | ok | a capital letter after the number is a style choice |
| C-54 | Tile placeholder | "Yükleniyor" | unclear | also shown forever for a page that failed to render (B-024), so the word can be false |
| C-55 | Context menu header | "3 sayfa seçili" | ok | |
| C-56 | Loupe place | "QR ayıraç" | inconsistent | F-kontrol-15 |
| C-57 | Inspector reason | "Kontrol gerekiyor." | inconsistent | F-kontrol-18 |
| C-58 | Loupe head | "Sayfa 5 / 15", "Belge 2, 1. sayfa" | ok | |
| C-59 | Loupe chevrons | "Önceki sayfa (Sol)", "Sonraki sayfa (Sağ)" | ok | key names match the Turkish keyboard labels |
| C-60 | Loupe accessible name, status-bar slider name while open | "Önizleme" | inconsistent | third name, F-kontrol-17 |
| C-61 | Loupe close | " Kapat", "Kapat (Esc)", accessible "Önizlemeyi kapat" | ok | |
| C-62 | Loupe rider tooltip | "Bu sayfanın belgesi kontrol bekliyor" | inconsistent | F-kontrol-18 |
| C-63 | Loupe modes | "Sığdır", "Genişlik", "%100" | ok | |
| C-64 | Loupe strip | "Yakındaki sayfalar" | ok | |
| C-65 | Status-bar zoom | "Küçük resim boyutu uzaklaştır", "Küçük resim boyutu yakınlaştır", "Küçük resim boyutu yakınlaştırma düzeyi" | unclear | "Küçük resim" is the screen's word for page thumbnail; the screen otherwise says "sayfa"; fine but not the term the owner uses elsewhere |

## Summary

65 strings or groups read: 42 ok, 16 inconsistent (5 clusters: approve / incelendi, ayraç / ayıraç, gerekiyor / bekliyor / bekleyen / gereken,
three names for the preview, "Bul…"), 6 unclear, 1 with no next step. Findings: F-kontrol-14 to F-kontrol-18. Error and refusal messages:
the status-line refusals and errors (C-27, C-28, C-29, C-32, C-46, C-47) say what is wrong and mostly what to do; the one that does not is C-49.
Messages are plain labels in the status bar, never cleared and not read by a screen reader (O-05, B-037); that is a behaviour finding in the
ledger, not copy.

Not checked: tone and grammar by a native reader, the Turkish dotted/dotless I in sort order of template names, strings that belong to
the shared chrome (title band, palette, shortcut sheet).
