# Shared synthetic data (use exactly these values on every screen)

Job: "Kasım 2026 – Faaliyet belgeleri" · 3 parti · 812 sayfa · 287 belge · 6 kontrol · 14 boş sayfa atlandı.
Parties (Yükle): Parti 1 "tarama-2026-11-04-0912.pdf" 268 sayfa; Parti 2 "tarama-2026-11-04-1047.pdf" 281 sayfa; Parti 3 "tarama-2026-11-05-0830.pdf" 263 sayfa. Other jobs: "Ekim 2026 – Kapasite raporları" (412 sayfa, dışa aktarıldı 31.10.2026), "Oda kayıt formları – Eylül" (156 sayfa, dışa aktarıldı 30.09.2026).
Templates: Kapasite Raporu (Sicil_No zorunlu, Firma_Adi zorunlu, Rapor_Tarihi, Rapor_No; dosya adı {Sicil_No}_{Firma_Adi}); Faaliyet Belgesi (Sicil_No zorunlu, Firma_Adi zorunlu, Belge_Tarihi); Oda Kayıt Formu (5 değişken).
Sicil_No variants: Bölüm 1 = örnek A (sayfa 214, "Oda Sicil No:" line top left); Varyant 2 = örnek B (sayfa 455, "ODA KAYIT" stamp lower right).

Kontrol documents (exact):
| Belge | Sayfalar | Şablon | Sicil_No | Firma_Adi | Tarih | Problem |
| 17 | 88–90 | Kapasite Raporu | 3O771 (kontrol) | Yıldız Gıda Paz. A.Ş. | 28.10.2026 | Sicil_No emin değil |
| 23 | 117–118 | Faaliyet Belgesi | 51408 | (boş, kontrol) | — | Firma_Adi okunamadı (zorunlu) |
| 41 | 214–216 | Kapasite Raporu | 48Z13 (kontrol, öneri 48213 Varyant 2 %93) | Akçay Tekstil San. ve Tic. Ltd. Şti. | 03.11.2026 | Sicil_No emin değil |
| 58 | 301–302 | Faaliyet Belgesi | 62190 (elle düzeltildi) | Kuzey Lojist1k (kontrol) | — | Firma_Adi emin değil |
| 96 | 455–457 | Kapasite Raporu | 27744 | Özen Mobilya Ltd. Şti. | 31.11.2026 (kontrol) | Geçersiz tarih |
| 131 | 602–603 | Faaliyet Belgesi | (boş, kontrol) | Ilgaz Tarım Ürünleri | — | Sicil_No okunamadı (zorunlu) |
Neighbours on Kontrol: Belge 40 = s.209–212 Faaliyet Belgesi, 48197, Ege Kalıp San. Ltd., Tamam. Belge 42 = s.217–218 (217 boş) Faaliyet Belgesi, 48226, Doğan Tekstil Ltd., Tamam. Belge 43 = s.219–220 Şablon yok, Okunmadı. Page 213 = QR ayıraç.
Export result names: 48213_Akcay_Tekstil_San_ve_Tic_Ltd_Sti.pdf, 48197_Ege_Kalip_San_Ltd.pdf, 48226_Dogan_Tekstil_Ltd.pdf, 27744_Ozen_Mobilya_Ltd_Sti.pdf, Belge_043.pdf (şablon yok), kontrol-gereken: 51408_Belge_023_[kontrol].pdf, Belge_131_[kontrol].pdf.
Shortcuts: tabs Ctrl+1..6 (Rehber also F1); N / Shift+N next/previous kontrol; F filter; K cut; T template; R rotate; Del delete; M merge; B draw box; G grid; Enter accept suggestion; F2 type a value; V new variant; Ctrl+Z / Ctrl+Y; Ctrl+S save template; Ctrl+E export.
