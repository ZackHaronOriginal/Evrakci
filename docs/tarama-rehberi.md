# Tarama rehberi

Zımbalı evrak destelerini tarama ve Evrakçı'ya yükleme adımları.

## Hazırlık

1. Her desteyi masaya **orijinal sırasıyla** koyun.
2. Zımba tellerini **zımba sökücü** ile çıkarın. Tel kalırsa besleyici sıkışır ve tarayıcı camı çizilebilir.
3. Yırtık, buruşuk veya katlanmış sayfaları düzeltin.

## QR ayraç sayfaları

1. Ayraçları sağdaki panelden yazdırın (Ctrl+P). Sayıyı yaprak olarak girersiniz: 20 yaprak = 40 sayfa, çünkü QR kod yaprağın iki yüzüne de basılır. Evrakçı yazıcıdan uzun kenardan çift taraflı baskı ister; yazıcı desteklemiyorsa her yaprak iki ayrı sayfa olarak çıkar.
2. Ayrılması gereken her belgenin önüne bir ayraç yaprağı koyun. Örneğin 5 sayfalık bir belgeyi, iki yanındaki 2 sayfalık belgelerden ayraçlarla ayırın.
3. Taramadan sonra ayraçları desteden çıkarıp saklayın; tekrar kullanılabilir.

### Bilmeniz gerekenler

- Ayraç yaprağı yalnızca “burada yeni belge başlıyor” demektir; çıktıya girmez.
- Hepsi aynı uzunlukta olan belgelerde ayraç gerekmez: taramadan sonra Kontrol sekmesinde (Ctrl+2) o sayfaları seçip “Filtre: her N sayfa” seçeneğini uygulayın.
- Boş sayfalar hiçbir zaman belge ayırmaz. Çift taraflı taramadaki boş arka yüzleri Kontrol sekmesinde “Boş sayfaları at” anahtarıyla atabilirsiniz.

## Küçük makbuzlar

- Küçük ve ince makbuzlar besleyiciden düzgün geçmeyebilir.
- Bunları **cam üzerinden** tarayın ya da birkaçını bir A4 sayfaya bantlayıp öyle tarayın.

## Tarayıcı ayarları

| Ayar | Önerilen |
|---|---|
| Çözünürlük | 300 dpi |
| Renk | Gri ton (renkli damga varsa renkli) |
| Çift taraflı | Belgeler iki yüzlüyse açık |
| Dosya türü | PDF |

Ayarı bir kez seçip tarayıcıda profil olarak kaydedin.

## Evrakı Evrakçı'ya yükleyin

1. Her partiyi ayrı PDF olarak kaydedin ve Yükle sekmesinde (Ctrl+1) hepsini aynı işe ekleyin, tarama sırasıyla.
2. Ayrımları Kontrol sekmesinde (Ctrl+2) gözden geçirin; gerekirse kesim ekleyin veya kaldırın.
3. Dışa Aktar sekmesinde (Ctrl+5) her belgeyi ayrı PDF olarak alın.

## Taramadan sonra

- Kurum kuralına göre orijinal evrakları yeniden zımbalayın ve arşive kaldırın.

### Dışa aktardıktan sonra

- Taranan sayfalar ve iş bu bilgisayarda kalır. Evrakçı hiçbir şeyi başka yere göndermez ve kullanım bilgisi toplamaz. Yalnızca siz isteyince OCR modellerini internetten (HTTPS) indirir ve SHA-256 ile doğrular.
- Dışa aktar, PDF'leri ve okunan değerleri içeren index.xlsx dosyasını seçtiğiniz klasöre yazar. O klasörü korumak sizin işinizdir. [Dışa Aktar sekmesini aç](rehber:disa-aktar)
- Dışa aktarılan iş bu bilgisayarda Ayarlar > Saklama'daki seçime göre kalır: Süresiz, tam dışa aktarınca silinir ya da 30 veya 90 gün sonra silinir. Hiç dışa aktarılmamış ya da dışa aktarıldıktan sonra değiştirilmiş iş silinmez. [Saklama ayarını aç](rehber:saklama)

## Sözlük

- **Kontrol**: hem ayrımları gözden geçirdiğiniz sekmenin adı hem de okunan bir değerin düzeylerinden biri. O değerden emin olunamamıştır; bakmanız gerekir.
- **Emin**: değer güvenle okundu.
- **Orta**: değer okundu, ama güven Emin düzeyinden düşük.
- **Şablon**: bir belge türünde nelerin nerede okunacağını tanımlar (kutular ve değişkenler).
- **İncelendi**: değeri bir kişi elle yazdı ya da onayladı; yeniden okumada korunur.
