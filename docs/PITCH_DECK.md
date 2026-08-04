# Vel'Koz — Sunum İskeleti

12 slayt. Her slaytta: **ne söyleyeceğin** (başlık/görsel) + **nasıl söyleyeceğin** (konuşma notu).
Kuluçka başvurusu, TÜBİTAK sunumu ve yatırımcı görüşmesi için aynı iskelet kullanılabilir;
son iki slayt hedefe göre değişir.

**Süre hedefi:** 5 dakika sunum + soru. Slayt başına ~25 saniye.

---

## 1 — Açılış

> **Vel'Koz** 👁️
> Güvenlik kamerası arşivinde Türkçe doğal dil arama
> *Tamamen yerel. Görüntü binadan çıkmaz.*

**Konuşma notu:** İsmi söyle, tek cümlede ne yaptığını söyle, dur. Açılışta özellik sayma.

---

## 2 — Problem (hikâyeyle aç)

> Bir olay olduğunda kayıtları taramak **saatler** sürer.

Görsel: bir güvenlik odası, ekranda hızlı sarılan kayıt.

**Konuşma notu:** Somut bir hikâye anlat — tercihen **kendi yaptığın müşteri görüşmesinden**.
*"Geçen hafta bir site yöneticisiyle konuştum, otoparkta çizilen bir araba için 4 saat kayıt
izlemiş."* Bu cümle tüm slayttan güçlüdür. Görüşme yapılmadıysa bu slayt zayıf kalır — önce
görüşmeyi yap.

---

## 3 — Mevcut çözümler neden yetmiyor

| Yaklaşım | Sınırı |
|---|---|
| Hareket algılama | Yaprak kımıldasa alarm verir; "ne oldu" sorusuna cevap vermez |
| Nesne sınıflandırma | En fazla "araç/insan" der |
| Manuel izleme | Saatler, ve dikkat dağıldıkça kaçırma |

**Konuşma notu:** Rakibi kötüleme, sınırını göster. "Onlar kötü" değil, "o soru sorulmuyor".

---

## 4 — Çözüm (demo slaytı)

> Türkçe yaz. Anı bul. O saniyeden oynat.

Görsel: **canlı demo veya ekran kaydı.** Üç sorgu:
1. `"otoparkta yürüyen insan"` → sonuç ızgarası
2. `"kırmızı kıyafetli adam"` → doğru sonuç (kırmızı araba **değil**)
3. `"köpek gezdiren adam"` → **"bu nesne arşivde yok"**

**Konuşma notu:** Üçüncü sorgu en önemlisi ve çoğu kişi bunu atlar. *"Sistem burada bir şey
uydurabilirdi. Uydurmuyor."* Güvenlik ürününde bu satır satın alma kararını değiştirir.

---

## 5 — Nasıl çalışıyor

```
İNDEKSLEME:  Video → akıllı kare örnekleme → nesne tespiti → çift embedding → yerel vektör db
SORGU:       Türkçe → ayrıştırma → arama → görsel-dil doğrulama → sonuç + zaman damgası
```

**Konuşma notu:** Tek teknik slayt. Detaya girme; jüri isterse sorar. Vurgulanacak tek şey:
**çeviri katmanı yok**, Türkçe doğrudan görüntü uzayına gömülüyor.

---

## 6 — Teknik fark: küçük özneler

> 1080p geniş planda uzaktaki insan **40 piksel**. Tam-kare embedding'inde kaybolur.

Görsel: solda geniş kare (insan zar zor seçiliyor), sağda kırpılmış hâli.

> Vel'Koz her nesneyi **ayrı vektör** olarak indeksler.
> **Ölçülen katkı: Recall@5'te +0.167**

**Konuşma notu:** Bu, mimarinin en pahalı kararı ve ölçülmüş gerekçesi var. "Böyle daha iyi
olur diye düşündük" değil, "ölçtük, şu kadar katkı verdi".

---

## 7 — Teknik fark: halüsinasyon yerine dürüstlük

> Aranan nesne kayıtlarda hiç yoksa sistem **uydurmuyor.**

| | |
|---|---:|
| Korpusta olmayan kavramı reddetme | **4/4** |
| Kişi-renk sorgusuna araç sızması | **0** |

**Konuşma notu:** Anlat: *"Kırmızı kıyafetli adam" araması başta kırmızı **arabalar**
getiriyordu. Bunu bir test yazarak yakaladık ve düzelttik. Şimdi model tam da o hatayı yapmaya
kalkıyor — 6 kırmızı araba aday çıkarıyor — doğrulayıcı 6'sını da eliyor.* Bu somut hikâye,
soyut "doğruluk yüksek" iddiasından çok daha inandırıcı.

---

## 8 — Ölçüm disiplini (ayırt edici slayt)

> Sorgu seti sonuçlara **bakılmadan** donduruldu.

| Metrik | Değer | %95 GA |
|---|---:|---|
| Recall@5 | 0.833 | [0.552, 0.953] |
| Recall@10 | 0.917 | [0.646, 0.985] |
| MRR | 0.847 | — |
| Uçtan uca | 11/12 | — |

Güven aralıkları geniş — **12 sorgu**. Bunu sen söyle.

**Konuşma notu:** Bu slayt seni diğer başvurulardan ayırır. Çoğu demo gösterir; sen ölçüm
gösteriyorsun. **Sınırlamayı kendin söyle:** *"Örneklem küçük, güven aralıkları geniş, bu bir
yön göstergesi — kesin performans iddiası değil."* Bir jüri üyesi bunu senden önce söylerse
kaybedersin; sen söylersen kazanırsın.

---

## 9 — Pazar

| | |
|---|---|
| **Doğrulama** | Conntour, Mart 2026'da General Catalyst + Y Combinator'dan **7M$** |
| **Türkiye** | Muadil yok. **Türkçe doğal dil hiçbir üründe yok.** |
| **İlk segment** | Site yönetimleri, AVM'ler, lojistik depoları, fabrikalar |

**Konuşma notu:** Rakibin varlığı iyi haberdir — pazar doğrulanmış demektir. "Rakip yok"
demek çoğu zaman "pazar yok" demektir.

---

## 10 — KVKK: engel değil, kalemiz

> Bulut tabanlı rakip, müşterinin kamera görüntüsünü **üçüncü tarafa göndermek zorunda.**
> Biz göndermiyoruz.

Görüntü · embedding · sorgu · model çağrısı — **hepsi müşteri donanımında.**

**Konuşma notu:** Türkiye'de kamera verisiyle çalışan herkesin ilk sorusu budur. Rakibin
mimarisi gereği veremediği cevabı biz mimarimiz gereği veriyoruz. Bu bir özellik değil,
yapısal avantaj.

---

## 11 — Durum ve yol haritası

| Faz | Durum |
|---|---|
| MVP indeksleyici | ✅ |
| Nesne-kırpık embedding | ✅ |
| Görsel-dil doğrulama | ✅ |
| Açık lisanslı korpus + dağıtım paketi | 🔄 devam |
| **Saha pilotu** | ⏳ **aradığımız şey bu** |
| Araç takibi + plaka (giriş/çıkış zamanı) | 🔭 planlı |

**Konuşma notu:** Dürüst ol — prototip aşamasındasın. Prototip olduğunu söyleyip çalışan bir
şey göstermek, ürün gibi sunup soruda çökmekten iyidir.

---

## 12 — Kapanış: ne istiyoruz

**Kuluçka/yarışma sürümü:**
> Gerçek arşiviyle test edebileceğimiz **bir saha pilotu** ve ürünleştirme mentorluğu.

**TÜBİTAK 2209-A sürümü:**
> Akademik danışmanlık + ölçüm altyapısının genişletilmesi (sorgu seti büyütme, dereceli alaka).

**Yatırımcı sürümü:**
> İlk 3 pilot müşteri ve 12 aylık ürünleştirme.

**Konuşma notu:** Tek ve net bir istek söyle. Üçünü birden isteme.

---

## Sunum öncesi kontrol listesi

- [ ] En az 5 müşteri görüşmesi yapıldı, 3. slaytta gerçek bir alıntı var
- [ ] Demo **açık lisanslı** kayıtla çekildi (MEVA/VIRAT/UCF paylaşılamaz — lisans ihlali)
- [ ] Demo videosu yedekte (canlı demo çökerse)
- [ ] 8. slayttaki sınırlama cümlesi ezberlendi
- [ ] "Neden bunu Google/Bosch yapmasın?" sorusuna hazır cevap: *Türkçe + yerel çalışma +
      küçük müşteriye uygun maliyet — büyük oyuncu bu üçünü aynı anda hedeflemiyor*
- [ ] "Kaç müşterin var?" sorusuna dürüst cevap hazır: *Henüz yok, pilot arıyorum*
