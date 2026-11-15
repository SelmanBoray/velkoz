# Vel'Koz — Teknik Rapor

**Güvenlik kamerası arşivinde Türkçe doğal dil arama**
Sürüm: 4 Ağustos 2026 · Korpus C2 (17 video / 6.231 vektör)

---

## 1. Özet

Vel'Koz, güvenlik kamerası arşivinde **Türkçe doğal dil sorgusuyla** olay arama yapan,
**tamamen yerel çalışan** bir arama motorudur. Kullanıcı *"dün gece otoparka giren siyah SUV"*
yazar; sistem ilgili anları saniyeler içinde bulur ve videoyu o saniyeden oynatır.

Üç teknik iddiası vardır ve üçü de ölçülmüştür:

1. **Çeviri katmanı olmadan Türkçe.** Çok dilli görsel-metin modeli (`jina-clip-v2`) Türkçe
   sorguyu doğrudan görüntü uzayına gömer. Çeviri kaybı ve ek gecikme yoktur.
2. **Küçük özneler kaybolmaz.** 1080p geniş planda 40 piksellik bir insan tam-kare
   embedding'inde kaybolur. Vel'Koz nesne kırpıklarını ayrı vektör olarak indeksler.
   Ölçülen katkı: Recall@5'te **+0.250** (0.667 → 0.917).
3. **Halüsinasyon yerine dürüst "bulunamadı".** Skor eşiğine güvenmek yerine korpusun nesne
   envanterine bakar; aranan sınıf hiç tespit edilmemişse makul-ama-yanlış sonuç üretmez.
   Ölçülen: 4 negatif sorgunun **4'ü de** doğru şekilde kapıdan döndü.

Sistemin ayırt edici yanı yalnızca mimarisi değil, **ölçüm disiplinidir**: sorgu seti sonuçlara
bakılmadan dondurulmuş (pre-registration), metrikler etiket tipine göre ayrılmış, güven aralıkları
raporlanmış, ve korpus büyütülürken ground-truth eskimesine karşı ayrı bir protokol tanımlanmıştır.

---

## 2. Problem

Bir olay yaşandığında (hırsızlık, kaza, kayıp eşya, izinsiz giriş) kayıtları izlemek **saatler**
sürer. Mevcut sistemler ya hareket algılamayla sınırlıdır ya da yalnızca "araç/insan" gibi kaba
sınıflar sunar. *"Kırmızı kıyafetli adam"* veya *"telefonla konuşan sürücü"* gibi bir tarif ile
arama yapılamaz.

**Pazar doğrulaması.** Yurt dışındaki muadili Conntour, Mart 2026'da General Catalyst ve
Y Combinator'dan 7M$ yatırım almıştır. Türkiye'de muadili bulunmamaktadır ve **Türkçe doğal dil
desteği hiçbir üründe yoktur**.

**Yerel çalışmanın zorunluluğu (KVKK).** Güvenlik kamerası görüntüsü KVKK kapsamında özel nitelikli
kişisel veri işleme riski taşır. Bulut tabanlı bir çözüm, müşterinin görüntüsünü üçüncü tarafa
göndermeyi gerektirir. Vel'Koz'un tüm bileşenleri (embedding, vektör veritabanı, görsel-dil modeli)
**müşteri donanımında** çalışır; hiçbir görüntü, embedding veya sorgu dışarı çıkmaz. Bu, bir
özellik değil mimari ilkedir ve aynı zamanda en güçlü ticari farklılaştırıcıdır.

---

## 3. Sistem mimarisi

### 3.1 Çevrimdışı indeksleme

```
Video → akıllı kare örnekleme → YOLO nesne tespiti → çift embedding → Qdrant
```

- **Akıllı kare örnekleme.** Hareket kapısı, algısal karma ile tekilleştirme, yanık OSD (ekran
  üstü saat) maskesi, kamera başına saatlik oran sınırı ve hareketsizlikte bile atılan çapa
  kareleri. Amaç: ilgisiz kareyi indekslememek ama olayı da kaçırmamak.
- **Çift embedding (Faz 1.5).** Her tutulan kare hem **tam kare** olarak hem de içindeki
  **nesne kırpıkları** (insan/araç, `yolo11m@1280`) olarak ayrı ayrı gömülür. Bu, uzaktaki küçük
  özneleri kurtaran ana mekanizmadır.
- **Statik nesne bastırma.** Park hâlinde duran araç her karede yeniden kırpılmaz (IoU tabanlı),
  aksi hâlde indeks tek bir nesneyle dolar.

### 3.2 Sorgu anı

```
Türkçe sorgu → ayrıştırma → bulunamadı kapısı → embedding → Qdrant → VLM doğrulama → füzyon
```

- **Ayrıştırma.** Zaman ifadesi ("dün gece", "son 3 saatte") görsel metinden ayrılır; zaman
  filtresi sıfır sonuç verirse filtresiz tekrarlanır ve kullanıcıya bildirilir.
- **Niyet ayrımı (Türkçe durum eki ile).** *"araçlar**la** dolu açık otopark"* → sahne sorgusu;
  *"otopark**ta** yürüyen insan"* → nesne sorgusu. Baş isim (head) **çekim ekinden** çıkarılır,
  kelime sırasından değil — Türkçe serbest sözcük dizilişli olduğu için pozisyon güvenilmez.
  Sahne niyetinde tam-kareye yumuşak (z-normalize) ağırlık verilir, böylece kırpık seli sahne
  sorgusunu gömmez.
- **Bulunamadı kapısı.** Sorgu, korpusta hiç tespit edilmemiş bir nesne sınıfı istiyorsa
  CLIP skoruna bakılmadan boş dönülür. İndeks tamamen boşsa ayrı ve doğru bir mesaj verilir
  ("henüz hiç video indekslenmemiş") — bu ikisi karıştırılırsa sistem yalan söylemiş olur.
- **Retrieve-then-verify.** CLIP adayları küçük bir görsel-dil modeliyle (`qwen2.5vl:3b`)
  tam çözünürlükte doğrulanır.

### 3.3 Küçük VLM'i doğru kullanmak — ölçülmüş bir tasarım kararı

Küçük görsel-dil modelleri **karmaşık JSON şemasında güvenilmez**: kırmızı bir arabaya
"mavi araba mı?" diye sorulduğunda onay damgası basma eğilimindedir. Aynı model **atomik
evet/hayır** sorusunda rengi kusursuz ayırır (ölçüm: kırmızı 9/9 ↔ mavi 0/9).

Bu nedenle Vel'Koz sorguyu (nesne, renk) hedeflerine indirger ve tek tek evet/hayır sorar.
Doğrulama görüntüsü de hibrittir: renk/öznitelik sorularında **dar kırpık** (özne kadrajı
doldurur), zor kavramlarda (köpek, yağmur) **sınırlandırılmış tam kare** (nesne kırpığın dışında
olabilir).

---

## 4. Ölçüm metodolojisi

Bu bölüm projenin en ayırt edici yanıdır ve bilinçli olarak katı tutulmuştur.

### 4.1 Pre-registration

Sorgu seti (`eval/queries.yaml`) **sonuçlara bakılmadan** ground-truth'tan türetilip
dondurulmuştur. Golden kareler skora güvenilmeden **gözle** doğrulanmıştır. Bir düzeltmenin
işe yarayıp yaramadığı, hisle değil bu sabit sette ölçülerek belirlenir.

### 4.2 Etiket tipine göre metrik ayrımı

Tüm sorguları tek bir Recall sayısında toplamak yanıltıcıdır; her sorgu tipi farklı şey ölçer:

| Tip | Ne ölçer | Metrik |
|---|---|---|
| `class` / `scene` | ayırt edici video-düzeyi eşleşme | Recall@k |
| `golden` | gözle doğrulanmış tek doğru kare | Recall@1 / MRR |
| `advisory` | renk/öznitelik — ground-truth otomatik doğrulanamaz | recall'a **girmez**, denetim için raporlanır |
| `zaman` | zaman ayrıştırma + geri düşüş davranışı | recall'a **girmez** |
| `negatif` | korpusta olmayan kavram | kapı oranı |

22 sorgunun yalnızca **12'si** toplu Recall'a girer. Bu, skoru düşüren ama dürüst olan bir tercihtir.

### 4.3 İki ortogonal eksen (Faz 2)

Uçtan uca (CLIP + VLM) hattın objektif skoru iki bağımsız eksende ölçülür:

1. **Sonuç ekseni:** `not_found` / `has_results` beklentiyle uyuşuyor mu?
2. **Ayrım ekseni:** yasaklı nesne sınıfı sonuçlara **sızdı mı**?

İkinci eksen bir gerçek hatadan doğdu: *"kırmızı kıyafetli adam"* sorgusu kırmızı **arabalar**
getiriyordu. Yalnız birinci eksenle bakıldığında bu "has_results = başarılı" görünürdü. İkinci
eksen bu kör noktayı kapatır.

**Boş geçen koruma (vacuous pass) dürüstlüğü.** Yasaklı sınıf kontrolü, o sınıftan hiç aday
gelmezse kendiliğinden geçer — bu bir kanıt değildir. Eval bu durumu ⚠ ile işaretler ve
"sonuçlara sızan" ile "doğrulayıcının elediği" sayılarını karşılaştırarak korumanın gerçekten
tetiklenip tetiklenmediğini gösterir.

### 4.4 Ground-truth havuzlama protokolü

Korpus 13'ten 17 videoya çıkarıldığında ölçüm Recall@5'te 0.917 → 0.833 düşüş gösterdi.
İnceleme, düşüşün **sahte** olduğunu ortaya çıkardı: *"yürüyen insan"* sorgusunun yeni ilk beş
sonucunun tamamı **doğru** yürüyen insan kırpığıydı ve skorları eski birincininkinden yüksekti.
Kusur modelde değil, ground-truth'taydı — ilgili video listeleri yeni videoları bilmiyordu.
Bu, bilgi erişimi literatüründe **eksik alaka yargıları** (incomplete relevance judgments)
olarak bilinen problemdir.

Bunun tekrarlanmaması için bağlayıcı protokol tanımlandı:

1. Eski sorgu seti **dondurulmuş kalır**; kendi korpusunda geçerli bir kayıt olarak durur.
2. Yeni korpus sürümü **ayrı dosyaya** yazılır.
3. Genişletme kararı **arama sonucuna değil, videonun içeriğine** bakılarak verilir
   (nesne envanteri + küçük resim gözle inceleme).
4. Kanıtı zayıf genişletme **reddedilir ve gerekçesi yazılır**. Reddedilenleri kayda geçirmek,
   kabul edilenler kadar önemlidir: seçiciliğin metrik lehine çalışmadığının belgesidir.
5. `golden_frame` alanlarına asla dokunulmaz.
6. İki sürümün sonucu **yan yana** raporlanır.

Son turda 2 genişletme kabul edildi, **4'ü reddedildi**.

---

## 5. Sonuçlar

Korpus: **17 kamera/video · 6.231 vektör** (1.114 tam kare + 5.117 nesne kırpığı).
Sorgu seti: 22 sorgu (12 skorlanabilir · 4 advisory · 2 zaman · 4 negatif).
Güven aralıkları Wilson yöntemiyle, %95.

### 5.1 Erişim (retrieval)

| Metrik | Değer | %95 GA |
|---|---:|---|
| Recall@1 | 0.833 | [0.552, 0.953] |
| Recall@5 | 0.917 | [0.646, 0.985] |
| Recall@10 | 1.000 | [0.757, 1.000] |
| MRR | 0.889 | — |
| Makro Recall@5 | 0.917 | — |

### 5.2 Nesne-kırpık embedding'inin katkısı (Faz 1.5 ablasyonu)

| Hat | Recall@5 |
|---|---:|
| Yalnız tam kare | 0.667 |
| Yalnız nesne kırpığı | 0.917 |
| **Birleşik** | **0.917** |
| **Marjinal katkı** | **+0.250** |

Bu, mimarinin en pahalı kararının (her nesne için ayrı vektör) ölçülmüş gerekçesidir.

### 5.3 Uçtan uca hat (CLIP + VLM)

| Kova | Skor |
|---|---|
| Negatif (korpusta olmayan kavram) | 3/3 |
| Pozitif kontrol | 3/3 |
| Öznitelik (renk) | 3/4 |
| Zor negatif (ayrım ekseni) | 2/2 |
| **Genel** | **11/12 (%92)** |
| **Ayrım ekseni** | **2/2 — hiç araç sızmadı** |

### 5.4 Ayrım (discrimination)

| Ölçüm | Sonuç |
|---|---|
| Negatif kapı oranı | **1.00** (4/4 doğru şekilde reddedildi) |
| Yanlış kapı (false gate) | **0** |

**Kanıtlanmış regresyon koruması.** *"Kırmızı kıyafetli adam"* sorgusunda CLIP tam da eski
hatadaki gibi 6 kırmızı araba adayı üretti; doğrulayıcı **6'sını da eledi, 0 tanesi sonuçlara
sızdı**. Bu, korumanın boş geçmediğinin (non-vacuous) doğrudan kanıtıdır.

---

## 6. Bilinen sınırlamalar

Bu bölüm bilinçli olarak ayrıntılıdır; bilinmeyen sınırlama, bilinenden tehlikelidir.

1. **Örneklem küçük.** 12 skorlanabilir sorgu ile güven aralıkları geniştir
   ([0.552, 0.953]). Sonuçlar yön gösterir, kesin performans iddiası taşımaz. Sorgu setinin
   büyütülmesi öncelikli iştir.
2. **Golden-frame metriği korpus boyutuna duyarlı.** Metrik tek bir doğru kare varsayar; korpus
   büyüdükçe aynı derecede geçerli başka kareler ortaya çıkar ve metrik yanlış şekilde düşer.
   Dereceli alaka (graded relevance) modeline geçiş gerekmektedir. Metriği kurtarmak için
   ground-truth **oynatılmamıştır**.
3. **Doğrulayıcı güveni ikili.** Görsel-dil modeli {0, 1} döndürür; dolayısıyla eşik kalibrasyonu
   anlamsızdır ve yapılmamıştır. Sürekli güven skoru (çok-kareli mutabakat veya token
   log-olasılığı) bir **özellik** olarak eklenebilir; kalibrasyon değildir.
4. **Türkçe kök eşleşmesinde kalan bir sınır.** Kök + tek sesli birleşimi ("kara" =
   `kar`+`a`) dilbilgisel olarak geçerli bir yönelme hâli olduğu için ayırt edilemiyor.
   Yaygın çakışmalar (`karanlık`, `karayolu`) düzeltildi; tam çözüm morfolojik analiz ister.
5. **Renk ground-truth'u otomatik doğrulanamaz.** Renk sorguları bu nedenle advisory sayılır ve
   toplu Recall'a katılmaz.
6. **Test korpusu yeniden dağıtılamaz.** MEVA/VIRAT/UCF araştırma lisanslıdır; bu klipler demo
   veya tanıtım materyalinde **paylaşılamaz**. Açık lisanslı korpus hazırlığı ayrı iş kalemidir.
7. **Kimlik takibi yoktur.** Zaman kümeleme "görülme aralığı" verir; "aynı araç girdi ve çıktı"
   iddiası için nesne takibi gerekir ve henüz yoktur.

---

## 7. Yol haritası

| Faz | Kapsam | Durum |
|---|---|---|
| 1 — MVP indeksleyici | Video → aranabilir indeks → Türkçe sorgu | Tamam |
| 1.5 — Nesne-kırpık embedding | Küçük özneler için ayrı vektörler | Tamam |
| 2 — Görsel-dil doğrulama | Retrieve-then-verify, renk/negasyon | Tamam |
| 2.5 — Açık lisanslı korpus | Paylaşılabilir demo verisi | Devam ediyor |
| 3 — Dağıtım paketi | Windows kurulum, çift tıkla çalışma | Devam ediyor |
| 4 — Saha pilotu | Bir sitenin bir haftalık arşivi | Sırada |
| İleri | Araç takibi + plaka ile giriş/çıkış zaman çifti | Planlı |

---

## 8. Yeniden üretilebilirlik

Tüm ölçümler tek komutla tekrarlanabilir:

```bash
python -m velkoz doctor                   # ortam denetimi
python eval/run_eval.py --queries eval/queries_c2.yaml --out <klasör>
python eval/faz2_eval.py --out <klasör>   # Ollama gerekir
```

Ham çıktılar (`sonuc.json`, sorgu bazında sıralamalar, güven aralıkları) `experiments/`
altında tarih-konu klasörlerinde saklanır. Mimari kararların gerekçeleri `ARCHITECTURE.md`,
kronolojik günlük `PROGRESS.md` dosyasındadır.
