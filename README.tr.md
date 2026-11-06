# Evrakçı

[English](README.md) | **Türkçe**

[![CI](https://github.com/ZackHaronOriginal/Evrakci/actions/workflows/ci.yml/badge.svg)](https://github.com/ZackHaronOriginal/Evrakci/actions/workflows/ci.yml)

**Ticaret ve sanayi odaları için açık kaynaklı belge tarama ve ayıklama uygulaması.**
Zımbalı evrak destelerini (makbuzlar, faturalar, üye formları) ayrılmış, aranabilir ve doğru
adlandırılmış PDF'lere ve bir Excel listesine dönüştürür. Belgeler binadan hiç çıkmaz.

Her ticaret ve sanayi odasında ve borsada çalışacak şekilde tasarlanmıştır.

## Durum

🚧 Geliştirme aşamasında. Henüz günlük kullanıma hazır değil.

## Nasıl çalışır?

```
Tarayıcı / fotokopi makinesi ──► tek büyük PDF ──► Yükle
                                                    │
                       ┌────────────────────────────┘
                       ▼
   1. Ayır          ayıraç sayfalarından (boş sayfa veya QR'lı ayıraç)
   2. OCR           Türkçe metin katmanı (OCRmyPDF ile Tesseract `tur`)
   3. Sınıflandır   makbuz / fatura / e-arşiv / diğer
   4. Bilgi çıkar   tarih, tutar, firma adı, sicil no, vergi no
   5. Kontrol       personel ayrımları ve türleri uygulamada onaylar veya düzeltir
   6. Dışa Aktar    adlandırılmış PDF'ler + Excel listesi
```

## İlkeler

- **Yerel çalışır.** Odanın kendi bilgisayarlarında çalışan bir masaüstü uygulamasıdır (önce Windows, ardından Linux ve macOS). Bulut OCR yok, üçüncü taraflara yükleme yok. KVKK açısından güvenlidir.
- **Son söz insanda.** Uygulama önerir, personel onaylar. OCR hata yapabilir; Kontrol ekranı bu hataları yakalamak içindir.
- **Önce Türkçe.** Arayüz, rehber ve belge kuralları Türk odalarının evrakına göre hazırlanır.
- **Kolay kurulum.** Personel için normal bir Windows kurulum dosyası. Python bilgisi gerekmez.

## Klasör yapısı

```
src/evrakci/pipeline/   İşleme (Qt'siz): ayırma, OCR, sınıflandırma, bilgi çıkarma, dışa aktarma
src/evrakci/ui/         PySide6 (Qt) arayüzü: Yükle, Kontrol, Dışa Aktar, Rehber
tests/                  Otomatik testler
docs/                   Mimari, lisans ve tarama rehberi
samples/synthetic/      Yalnızca SAHTE test belgeleri (aşağıya bakın)
```

Tarama rehberi: [docs/tarama-rehberi.md](docs/tarama-rehberi.md)

## ⚠️ Gerçek belgeleri asla yüklemeyin

Bu depo herkese açıktır. **Gerçek makbuz, fatura veya üye bilgisi içeren hiçbir belgeyi depoya
eklemeyin.** "Sadece test için" bile olsa. `samples/synthetic/` içindeki sahte belgeleri kullanın.
Gerçek taramalar git tarafından yok sayılan `data/` klasöründe durmalıdır.

## Geliştirme

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
evrakci
```

OCR için gerekli sistem programları: Türkçe dil paketiyle (`tur`) Tesseract, Ghostscript, qpdf.

## Katkıda bulunma

Katkılarınızı bekliyoruz. Lütfen önce [CONTRIBUTING.md](CONTRIBUTING.md) dosyasını okuyun.
Tüm katkıda bulunanlar ilk pull request'lerinde kısa bir
[Katkıda Bulunan Lisans Sözleşmesi (CLA)](CLA.md) imzalar.

## Lisans

[AGPL-3.0-or-later](LICENSE). Her oda uygulamayı ücretsiz kullanabilir ve değiştirebilir. Uygulamayı
dağıtan veya değiştirilmiş bir sürümünü başkalarına hizmet olarak sunan herkes kaynak kodunu
paylaşmak zorundadır. Ticari lisans, destek ve barındırma hizmeti için proje sahibiyle iletişime
geçebilirsiniz. Ayrıntılar: [docs/licensing.md](docs/licensing.md)
