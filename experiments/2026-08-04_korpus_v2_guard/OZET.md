# Korpus v2 zenginleştirme — üç yargılı ölçüm (4 Ağustos 2026)

Task #4. Korpus **13 → 17 video**, **4395 → 6231 vektör** (+1836: 5117 kırpık / 1114 kare).
Eklenen: `meva_okul_G330` (30s basketbol salonu), `meva_okul_G339` (park/kampüs yolu),
`meva_hastane_G341` (dış mekân yaya), `meva_otobus_G505` (yaya sundurması).
Kaynak ve eleme gerekçeleri: `experiments/2026-07-21_korpus_v2/PROVENANCE.md`.

Ölçüm üç yargıya ayrıldı: **GUARD** (bozdum mu) · **DEDEKTİF** (temiz mi) · **İYİLEŞME** (kazandım mı).

---

## Video başına sınıf envanteri (indeks sonrası, içerik gerçeği)

| video | insan | araba | kamyon | otobüs | motosiklet |
|---|---:|---:|---:|---:|---:|
| meva_okul_G330 **(yeni)** | 1077 | 0 | 0 | 0 | 0 |
| meva_okul_G339 **(yeni)** | 0 | 101 | 27 | 0 | 0 |
| meva_hastane_G341 **(yeni)** | 205 | 1 | 0 | 0 | 0 |
| meva_otobus_G505 **(yeni)** | 59 | 84 | 3 | 0 | 0 |
| *(13 eski video toplamı)* | 317 | 1920 | 793 | 516 | 14 |

`available_object_classes()` = `[araba, insan, kamyon, motosiklet, otobüs]` — **bisiklet YOK**.
Eyeball-gate tuttu: `neg_bisiklet` envanter kapısı korundu.

---

## 1. GUARD — baseline bozuldu mu?

### Ham ölçüm C1 ground-truth ile (yanıltıcı)

| metrik | C1 (13 video) | v2 (17 video) |
|---|---:|---:|
| Recall@1 | 0.917 | 0.750 |
| Recall@5 | 0.917 | 0.833 |
| Recall@10 | 0.917 | 0.917 |
| MRR | 0.917 | 0.785 |
| Faz-1.5 marjini | +0.250 | +0.167 |
| false_gates | `scene_karanlik_yol` | `scene_karanlik_yol` (değişmedi) |
| negatives_gate_rate | 1.00 | 1.00 |

Bozulan iki sorgu, ikisi de **insan** sorgusu:

| sorgu | C1 rank | v2 rank |
|---|---:|---:|
| `beh_uzakta_yuruyen` | 1 | 4 |
| `gold_yuruyen_insan` | 1 | 6 |

### Kök neden: model değil, ground-truth eskimesi

`gold_yuruyen_insan` v2 top-5'inin **tamamı** yürüyen insan kırpığı (G505 ×4, G341 ×1) ve
skorları C1 top-1'inden yüksek (0.409 vs 0.384). Yani sistem **doğru cevap veriyor** —
ama `relevant_videos` listesi 21 Temmuz'da yazıldı, bu videoları bilmiyor.

Bu, IR literatüründeki **incomplete relevance judgments** problemi. Ölçülen düşüş modelin
değil, GT'nin kusuru.

**Gözle doğrulanan kanıt:**
- `meva_otobus_G505/crops/1845_0.jpg` → kaldırımda tek başına yürüyen yaya ✔
- `meva_hastane_G341/crops/0_0.jpg` → kaldırımda tek başına yürüyen yaya ✔

### Düzeltme: C2 GT havuzlaması

`eval/queries_c2.yaml` üretildi. `queries.yaml` (C1) **dondurulmuş kaldı, elleşilmedi**.
Genişletme kararı arama sonucuna değil videonun içeriğine bakılarak verildi; kanıtı zayıf
olan 4 genişletme reddedildi (gerekçeler dosya başlığında).

| metrik | C1 | v2 / C1-GT | v2 / C2-GT |
|---|---:|---:|---:|
| Recall@1 | 0.917 | 0.750 | **0.833** |
| Recall@5 | 0.917 | 0.833 | **0.833** |
| Recall@10 | 0.917 | 0.917 | **0.917** |
| MRR | 0.917 | 0.785 | **0.847** |

`beh_uzakta_yuruyen` havuzlama sonrası **4 → 1**'e döndü — düşüş gerçekten GT kusuruymuş.

### Kalan tek açık: `gold_yuruyen_insan` rank 6

Havuzlama bunu düzeltmedi, çünkü `gold_*` metriği **tek golden kareye** bağlı
(`VIRAT_otopark/180`) ve o kare artık 6. sırada. Korpusta ondan daha iyi 5 "yürüyen insan"
var ve hepsi meşru.

**Bu gerçek bir bulgu, saklanmıyor:** golden-frame metriği korpus boyutuna duyarlı —
korpus büyüdükçe "tek doğru kare" varsayımı kırılıyor. Ölçüm sisteminin bilinen sınırlaması
olarak kayda geçti. `golden_frame` alanına DOKUNULMADI (metriği kurtarmak için GT oynatmak
p-hacking olurdu).

**GUARD sonucu: GEÇTİ.** Gerçek regresyon yok; gözlenen düşüşün tamamı GT eksikliği veya
bilinen metrik sınırlaması olarak açıklandı.

---

## 2. DEDEKTİF — yasaklı kavramlar sızdı mı?

Korumaya alınan 5 kavram: köpek · yağmur · kar · bisiklet · mavi kamyonet.

| kontrol | sonuç |
|---|---|
| `neg_bisiklet` / `neg_kopek` / `neg_yagmur` / `neg_kar` (retrieval) | 4/4 hâlâ **GATE** ✔ |
| Faz-2 `negation` kovası | **3/3** ✔ |
| `available_object_classes()` içinde bisiklet | **yok** ✔ |
| `adv_mavi_kamyonet` top-3 | hâlâ `ucf_trafik` — yeni korpustan sızma yok ✔ |

`f2_attr_mavi_kamyonet` Faz-2'de ❌ (not_found beklenirken 9 sonuç) — **ama bu C1'de de
başarısızdı**, devralınan bilinen açık. Yeni videolar bozmadı: dönen ilk 3 sonuç eski
korpustan (`ucf_trafik/kamyon`), yeni korpus 4. sıradan itibaren ve mavi değil.

**DEDEKTİF sonucu: TEMİZ.** Hiçbir yasaklı kavram yeni korpustan sızmadı.

---

## 3. İYİLEŞME — ne kazandık?

### `hn_kirmizi_kiyafet`: not_found → has_results ✅

C1'de bu sorgu **hiç sonuç bulamıyordu** (korpusta kırmızı kıyafetli insan yoktu).
v2'de 2 doğru sonuç dönüyor, **0 araç sızıntısıyla**:

| # | video | sınıf | skor |
|---|---|---|---:|
| 1 | meva_okul_G330 | insan | 0.334 |
| 2 | meva_okul_G330 | insan | 0.328 |

Gözle doğrulandı (`G330/crops/105_12.jpg`): tribünde kırmızı kıyafetli kişi — araç değil.

Bu, **insan-renk pozitif yolunun ilk kez canlı test edilmesi** demek. Önceden bu yol
korpusta karşılığı olmadığı için ölçülemiyordu. "kırmızı kıyafetli adam → kırmızı araba"
regresyonuna karşı koruma artık *vacuous değil, gerçek*.

### Faz-2 genel skor

| kova | C1 | v2 |
|---|---|---|
| **Genel** | 11/12 | **11/12** |
| **Ayrım ekseni** | 2/2 | **2/2** |
| negation | 3/3 | 3/3 |
| positive_ctrl | 3/3 | 3/3 |
| attribute | 3/4 | 3/4 |
| hard_negative | 2/2 | 2/2 |

### Hâlâ vacuous: `hn_siyah_kiyafet`

9 sonuç dönüyor ama havuza hiç araç adayı girmiyor → forbid kontrolü tetiklenmiyor.
Zenginleştirme bunu canlıya çeviremedi. Dürüstçe ⚠ ile işaretli kalıyor.

---

## Özet

| yargı | sonuç |
|---|---|
| GUARD | **GEÇTİ** — gerçek regresyon yok (C2-GT: R@5 0.833, MRR 0.847) |
| DEDEKTİF | **TEMİZ** — 5 yasaklı kavramın hiçbiri sızmadı |
| İYİLEŞME | **KISMİ** — `hn_kirmizi_kiyafet` canlıya döndü; `hn_siyah_kiyafet` hâlâ vacuous |

## Bu turda ortaya çıkan iki yeni bilgi

1. **Korpus büyümesi GT'yi eskitir.** Zenginleştirme yapan her turda GT havuzlaması
   şart, yoksa sahte regresyon okunur. Protokol `queries_c2.yaml` başlığında yazılı.
2. **Golden-frame metriği korpus boyutuna duyarlı.** Tek doğru kare varsayımı korpus
   büyüdükçe kırılıyor. Graded relevance'a geçmek gerekebilir — açık madde.

## Üretilen dosyalar
- `eval/queries_c2.yaml` — havuzlanmış GT (C1 dondurulmuş kaldı)
- `experiments/2026-08-04_korpus_v2_guard/` — C1-GT ölçümü + Faz-2 sonucu
- `experiments/2026-08-04_korpus_v2_c2gt/` — C2-GT ölçümü
- `eval/faz2_eval.py` — `--queries` / `--out` argümanları eklendi (sürümlenebilir eval)
