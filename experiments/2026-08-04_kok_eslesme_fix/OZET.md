# Türkçe kök eşleşme hatası — teşhis ve düzeltme (4 Ağustos 2026)

C1 baseline'ından (21 Temmuz) beri eval'de duran tek `false_gate`'in kökü bulundu ve
düzeltildi. Sanılanın aksine sorun bulunamadı kapısında değil, **sorgu ayrıştırıcısındaydı**.

---

## Belirti

`scene_karanlik_yol` sorgusu — *"karanlıkta ilerleyen araçlar"* — sürekli **BULUNAMADI**
dönüyordu. Korpusta gece araç görüntüsü (`ucf_gece`) olmasına rağmen.

Eval bunu `false_gates: ["scene_karanlik_yol"]` olarak raporluyordu; iki turdur biliniyor
ama kök nedeni araştırılmamıştı.

## Yanlış hipotez (ve neden yanlış olduğu)

İlk varsayım: **nesne envanteri kapısı** yanlış tetikleniyor. Doğrudan test bunu çürüttü:

```
"karanlıkta ilerleyen araçlar"
   required=set()  generic_vehicle=True
   EKSIK=set()  -> gecer          ← kapı sorunu YOK
```

Envanter kapısı sorguyu geçiriyordu. Sorun daha aşağıdaydı:

```
not_found_reason: 'VLM: tanımlanan nesne görüntülerde doğrulanamadı.'
sonuç: 0  |  vlm_applied: True  |  vlm_filtered: 9
```

CLIP **9 doğru aday** getiriyor, doğrulayıcı **hepsini eliyordu**.

## Kök neden

`augment_intent("karanlıkta ilerleyen araçlar")` → **`obj_en = "snow"`**

Sistem VLM'e *"bu görüntüde **KAR** var mı?"* diye soruyordu. Kar olmadığı için 9 doğru
adayın hepsi elendi ve sorgu "bulunamadı" döndü.

Sebep `query.py`'daki düz önek eşleşmesi:

```python
obj_en = next((_token_en(t) for t in toks if t.startswith(_HARD_CONCEPT_ROOTS)), None)
```

`_HARD_CONCEPT_ROOTS` içinde **`"kar"`** var. Türkçe çekim eklerini yakalamak için kök
eşleşmesi kullanılıyor (`kar`, `karda`, `karlı`, `kardan` — hepsi doğru). Ama aynı kural
**"kar" ile başlayan bambaşka kelimeleri de** yakalıyordu:

| kelime | yanlış eşleşme |
|---|---|
| **kar**anlık | → snow |
| **kar**ayolu | → snow |
| **kar**şı | → snow |
| **kar**deş | → snow |
| **kar**akter | → snow |

CCTV bağlamında *"karayolunda ilerleyen araçlar"* da aynı tuzağa düşüyordu — bu, gerçek
kullanımda çok daha olası bir sorgu.

Aynı hatalı desen dosyada **9 ayrı yerde** vardı: renk kökleri, sınıf kökleri, sahne
kökleri, genel taşıt kökleri, TR→EN çevirisi ve `needs_vlm` tetiği.

## Düzeltme

Kök eşleşmesinden sonra **kalan parçanın gerçek bir Türkçe ek dizisi olduğu** doğrulanıyor
(`query.py: _EK_DIZISI`, `_kok_eslesir`, `_herhangi_kok`):

```
"karda"    → kar + "da"      ✓ hâl eki      → snow  (doğru)
"karlı"    → kar + "lı"      ✓ yapım eki    → snow  (doğru)
"karanlık" → kar + "anlık"   ✗ ek değil     → eşleşme YOK (düzeldi)
"karayolu" → kar + "ayolu"   ✗ ek değil     → eşleşme YOK (düzeldi)
```

Tüm önek eşleşmeleri bu kontrole geçirildi.

**Bilinen sınır (dokümante edildi, gizlenmedi):** kök + tek sesli — *"kara"* = `kar`+`a` —
dilbilgisel olarak geçerli bir yönelme hâlidir, ayırt edilemez. Tam çözüm morfolojik analiz
ister. Yaygın çakışmaların tamamı bu kontrolle eleniyor.

## Ölçüm

Aynı korpus (17 video / 6.231 vektör), aynı sorgu seti (`queries_c2.yaml`). Tek değişken:
kök eşleşme düzeltmesi.

| metrik | önce | sonra | değişim |
|---|---:|---:|---|
| Recall@1 | 0.833 | 0.833 | — |
| **Recall@5** | 0.833 | **0.917** | ▲ +0.084 |
| **Recall@10** | 0.917 | **1.000** | ▲ +0.083 |
| **MRR** | 0.847 | **0.889** | ▲ +0.042 |
| **Makro Recall@5** | 0.850 | **0.917** | ▲ +0.067 |
| **Faz-1.5 marjini** | +0.167 | **+0.250** | ▲ +0.083 |
| Negatif kapı oranı | 1.00 | 1.00 | — korundu |
| **Yanlış kapı** | `scene_karanlik_yol` | **yok** | ▲ sıfırlandı |

`scene_karanlik_yol`: **BULUNAMADI → rank 2**.

Recall@5 güven aralığı: [0.646, 0.985].

### Regresyon kontrolü (Faz-2, uçtan uca VLM)

| kova | önce | sonra |
|---|---|---|
| negation | 3/3 | **3/3** |
| positive_ctrl | 3/3 | **3/3** |
| attribute | 3/4 | **3/4** |
| hard_negative | 2/2 | **2/2** |
| **Genel** | 11/12 | **11/12** |
| **Ayrım ekseni** | 2/2 | **2/2** |

Hiçbir negatif kırılmadı. Ayrıştırıcı düzeyinde ayrıca doğrulandı:

```
karla kaplı sokak         → snow  ✓ korundu
karda yürüyen insan       → snow  ✓ korundu
karlı yol                 → snow  ✓ korundu
köpek gezdiren adam       → dog   ✓ korundu
yağmurda şemsiyeli insanlar → rain ✓ korundu
kırmızı kıyafetli adam    → man/red ✓ korundu
mavi kamyonet             → pickup truck/blue ✓ korundu
karanlıkta ilerleyen araçlar  → vehicle  ▲ DÜZELDİ (eskiden snow)
karayolunda ilerleyen araçlar → vehicle  ▲ DÜZELDİ (eskiden snow)
```

## Çıkarılan ders

**Eval'in "bilinen açık" diye iki tur taşıdığı şey gerçek bir üründe bozukluktu.**
`false_gate` iki turdur raporlanıyor ama "sahne sorgusu zor" diye normalleştirilmişti.
Kök nedene inince ortaya çıkan hata, dondurulmuş test setinin dışındaki gerçek sorguları
da (`karayolu`) bozan bir ayrıştırıcı hatasıydı.

Metriğin işaret ettiği her anomali, açıklanana kadar bir hata adayıdır.
