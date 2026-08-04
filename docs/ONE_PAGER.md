# Vel'Koz 👁️

### Güvenlik kamerası arşivinde Türkçe doğal dil arama — tamamen yerel

---

## Problem

Bir olay olduğunda (hırsızlık, kaza, kayıp eşya, izinsiz giriş) kayıtları taramak **saatler
sürer.** Site yöneticisi, AVM güvenlik müdürü, fabrika vardiya amiri — hepsi aynı işi yapar:
hızlı sarıp geri sarıp gözle arar.

Mevcut sistemler hareket algılamayla sınırlıdır. En gelişmişleri bile "araç" veya "insan"
der. Kimse *"kırmızı kıyafetli adam"* ya da *"telefonla konuşan sürücü"* diye arayamaz.

## Çözüm

Vel'Koz'a **Türkçe yazarsınız**, arşivdeki anı saniyeler içinde bulur ve videoyu tam o
saniyeden oynatır.

> "dün gece otoparka giren siyah SUV" · "kırmızı kıyafetli adam" · "telefonla konuşan sürücü"

**Ve hiçbir görüntü binadan çıkmaz.** Tüm işlem müşteri donanımında yapılır.

## Neden şimdi, neden biz

| | |
|---|---|
| **Pazar doğrulandı** | Muadili **Conntour**, Mart 2026'da General Catalyst + Y Combinator'dan **7M$** aldı. |
| **Türkiye'de rakip yok** | Muadil ürün yok; **Türkçe doğal dil desteği hiçbir üründe yok.** |
| **KVKK bir engel değil, avantajımız** | Bulut tabanlı rakipler görüntüyü üçüncü tarafa göndermek zorunda. Biz göndermiyoruz. Bu satın alma kararında belirleyici. |
| **Ucuz donanım** | Orta seviye bir GPU yeterli (8 GB). Sunucu odası gerekmiyor. |

## Kanıt — iddia değil, ölçüm

Sorgu seti sonuçlara bakılmadan **dondurulmuş** (pre-registration). Metrikler etiket tipine
göre ayrılmış, güven aralıkları raporlanmış.

| | |
|---|---:|
| Erişim Recall@5 | **0.833** |
| Erişim Recall@10 | **0.917** |
| MRR | **0.847** |
| Uçtan uca (görsel-dil doğrulamalı) | **11/12** |
| Korpusta olmayan kavramı reddetme | **4/4** |
| Kişi-renk sorgusuna araç sızması | **0** |

**Nesne-kırpık embedding'inin ölçülmüş katkısı: Recall@5'te +0.167.** 1080p geniş planda 40
piksellik bir insan tam-kare embedding'inde kaybolur; Vel'Koz her nesneyi ayrı vektör olarak
indeksler.

**Halüsinasyon yerine dürüst cevap.** Aranan nesne kayıtlarda hiç yoksa sistem makul-ama-yanlış
sonuç uydurmaz; "bu nesne arşivde yok" der. Güvenlik ürününde bu, doğruluktan daha önemlidir.

## Nasıl çalışıyor

```
Video → akıllı kare örnekleme → nesne tespiti → çift embedding → yerel vektör veritabanı
Türkçe sorgu → ayrıştırma → arama → görsel-dil modeliyle doğrulama → sonuç + zaman damgası
```

Çeviri katmanı yok: çok dilli görsel-metin modeli Türkçe sorguyu doğrudan görüntü uzayına gömer.

## Durum

- Çalışan prototip: 17 kamera kaydı, 6.231 indekslenmiş vektör, ölçülmüş sonuçlar
- Açık kaynak ölçüm altyapısı: tek komutla yeniden üretilebilir
- **Sırada:** saha pilotu — bir sitenin bir haftalık gerçek arşivi

## Ekip

**Selman Boray Asiltürk** — Bilgisayar Mühendisliği öğrencisi. Vel'Koz'un tüm mimarisi,
uygulaması ve ölçüm altyapısı. TEKNOFEST'te akıllı otopark güvenlik sistemi geliştiriyor.

## Aradığımız

- **Saha pilotu:** gerçek arşiviyle test edebileceğimiz bir site, AVM veya lojistik tesisi
- **Mentorluk:** ürünleştirme ve ilk müşteriye ulaşma
- **Destek:** TÜBİTAK 2209-A → BiGG hattında akademik danışmanlık ve kuluçka

---

<sub>Teknik detay: `docs/TEKNIK_RAPOR.md` · Mimari kararlar: `ARCHITECTURE.md` · Proje günlüğü: `PROGRESS.md`</sub>
