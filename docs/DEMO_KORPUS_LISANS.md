# Demo korpusu — kaynak ve lisans künyesi

**4 Ağustos 2026.** Bu dosya, Vel'Koz'un **paylaşılabilir demo korpusunun** kaynağını,
lisansını ve zorunlu atıf metinlerini kayda geçirir.

## Neden ayrı bir korpus var

Vel'Koz'un **ölçüm korpusu** (MEVA, VIRAT, UCF — 17 video) araştırma lisanslıdır ve
**yeniden dağıtılamaz.** Bu kliplerle çekilmiş bir demo videosu, ekran kaydı veya GIF
paylaşmak lisans ihlalidir.

Bu nedenle iki korpus **ayrı tutulur ve ayrı indekslerde yaşar:**

| Korpus | İçerik | İndeks yolu | Amaç | Paylaşılabilir mi |
|---|---|---|---|---|
| **Ölçüm** | MEVA · VIRAT · UCF (17 video) | `data/qdrant_storage` | Eval, regresyon takibi | ❌ Hayır |
| **Demo** | Açık lisanslı (3 klip) | `data/qdrant_demo` | Sunum, tanıtım, ekran kaydı | ✅ Evet |

**Ayrı indeks olmasının ikinci nedeni ölçüm bütünlüğüdür:** demo klipleri ölçüm korpusuna
karıştırılsaydı, dondurulmuş sorgu setinin ground-truth'u yine eskirdi ve her demo klibi
için yeniden havuzlama gerekirdi (bkz. ARCHITECTURE.md §6d). Ayrı indeks bu bağı tamamen keser.

---

## Kabul edilen klipler

### 1. `ngsim_peachtree_c1.mp4`

| | |
|---|---|
| **Kaynak** | NGSIM Programı — Peachtree Street videoları, Atlanta |
| **Yayıncı** | U.S. Department of Transportation, Federal Highway Administration (ITS DataHub) |
| **Lisans** | **CC BY-SA 4.0** — `licenseId: CC_40_BY_SA`, Socrata metadata API'sinden doğrulandı |
| **URL** | https://data.transportation.gov/Automobiles/Next-Generation-Simulation-NGSIM-Program-Peachtree/mupt-aksf |
| **Kesit** | camera1, 12:45–13:00 kaydının ilk 90 saniyesi · 640×480 |
| **İçerik** | Şehir merkezi kavşağı, yüksek eğik açı. 259 araba · 80 kamyon · 21 otobüs tespiti |

**Zorunlu atıf:**
> U.S. Department of Transportation Federal Highway Administration. (2016). *Next Generation
> Simulation (NGSIM) Program Peachtree Street Videos.* [Dataset]. Provided by ITS DataHub
> through Data.transportation.gov. http://doi.org/10.21949/1504477 — CC BY-SA 4.0

### 2. `wiki_mazatlan_otopark.mp4`

| | |
|---|---|
| **Kaynak** | Wikimedia Commons — *Estacionamiento de un Supermercado Ley, Mazatlán* |
| **Yükleyen** | DogeGamer2015MZT2 (11 Haziran 2022) |
| **Lisans** | **CC BY-SA 4.0** — Commons dosya sayfasında doğrulandı |
| **URL** | https://commons.wikimedia.org/wiki/File:Estacionamiento_de_un_Supermercado_Ley,_Mazatl%C3%A1n,_11_de_junio_de_2022.webm |
| **Kesit** | Tam klip, 50,5 sn · 632×356 |
| **İçerik** | Süpermarket otoparkı. 132 insan · 437 araba · 18 kamyon tespiti |

### 3. `wiki_roncesvalles.mp4`

| | |
|---|---|
| **Kaynak** | Wikimedia Commons — *Roncesvalles Ave crossing at Galley Ave*, Toronto |
| **Lisans** | **CC BY-SA 4.0** — Commons dosya sayfasında doğrulandı |
| **URL** | https://commons.wikimedia.org/wiki/File:Roncesvalles_Ave_crossing_at_Galley_Ave,_PXO_Type_A_lights_flashing,_July_2026.webm |
| **Kesit** | Tam klip, 13,1 sn · 1920×1080 |
| **İçerik** | Yaya geçidi, cadde. 122 insan · 243 araba · 49 kamyon tespiti |

---

## Reddedilen adaylar ve gerekçeleri

Reddedilenleri kayda geçirmek kabul edilenler kadar önemlidir — seçimin keyfî olmadığının belgesidir.

| Aday | Lisans | Ret gerekçesi |
|---|---|---|
| NGSIM Lankershim cam1 | CC BY-SA 4.0 | **Tepeden dik açı** (bina çatısından nadir görünüm). Dedektör 60 karede **0 tespit** üretti — YOLO bu açıyı tanımıyor ve gerçek CCTV geometrisi de bu değil. |
| NGSIM Lankershim cam3 | CC BY-SA 4.0 | Aynı — 0 tespit. |
| Wikimedia Montreal kavşağı | CC BY-SA 4.0 | **35 bisiklet tespiti.** Bisiklet `available_object_classes()`'a girerse `neg_bisiklet` envanter kapısı açılır ve dondurulmuş test kırılır. |
| MERL Street Scene (Zenodo) | CC BY-SA 4.0 | Veri seti tanımında **bisiklet** açıkça var; ayrıca 49 GB. |
| PKLot (HuggingFace) | CC BY 4.0 | Veri seti açıkça **yağmurlu** kareler içeriyor → `neg_yagmur` testini kırar. |
| FBI Pago Pago otoparkı | Public Domain | **Su baskını** görüntüsü — CLIP embedding'inde ıslaklık/yağmur karışması riski. |
| Pexels | Pexels License | Ham dosya yeniden dağıtımı yasak. Ayrıca şartlarda ML/AI amaçlı toplu kullanım (train/**evaluate**/develop) yasağı — indeksleme mimarisiyle doğrudan çelişiyor. |
| Pixabay | Pixabay Content License | "Standalone" yeniden dağıtım yasak. Lisans sayfası birinci elden doğrulanamadı (403). |
| Mixkit | Mixkit Free License | Değiştirilmemiş dosyanın yeniden dağıtımı yasak. |
| Coverr | Coverr License | Lisansta açık hüküm: içerik **"herhangi bir veri setinin parçası olamaz"**, AI eğitimi yasak. |
| KGM / İBB CepTrafik canlı kameralar | **Açık lisans YOK** | Türkiye'de varsayılan "her hakkı saklı" (FSEK 5846). Ayrıca izinsiz kaydedilmiş kamu kamerası ile demo çekmek, KVKK odaklı ürün anlatısıyla çelişir — itibar riski. |
| YouTube CC-BY filtresi | CC BY 3.0 | Mekanizma uygun ama yükleyicinin lisans etiketi içeriğin gerçekten ona ait olduğunu kanıtlamaz; çalıntı içeriğe yanlış etiket yaygın. |

---

## Dürüst değerlendirme: kabul edilenlerin sınırı

Kabul edilen üç klibin **hiçbiri gerçek sabit-CCTV kaydı değildir:**

- **Peachtree** — kule/çatı çekimi, gerçek CCTV'den çok daha yüksek açı
- **Roncesvalles** — sokak seviyesi sabit tripod, gözetim açısı değil
- **Mazatlán** — el kamerası, kamera hareket ediyor

**Bulgu:** Açık lisanslı, yeniden dağıtılabilir, **gerçek gözetim açılı** video pratikte
yok denecek kadar azdır. Gerçek CCTV veri setleri (MEVA, VIRAT, UCF, MERL, PKLot) istisnasız
araştırma lisanslıdır veya yasaklı kavram içerir.

**Sonuç ve strateji:**
1. **Ölçüm** gerçek CCTV korpusunda yapılmaya devam eder (bilimsel geçerlilik orada).
2. **Demo** bu açık lisanslı kliplerle çekilir (paylaşılabilirlik burada).
3. Gerçek gözetim açısı için **kendi çekimimiz** en doğru orta vadeli yoldur — bir site
   veya otopark girişine yerleştirilmiş tek kamera, birkaç saatlik kayıt. Bu aynı zamanda
   saha pilotunun ilk adımıdır.

---

## Lisans yükümlülüğü — ShareAlike uyarısı

Üç klip de **CC BY-SA 4.0**'dır. Bu iki şey demektir:

1. **Atıf zorunlu** — demo videosunun jeneriğinde/açıklamasında yukarıdaki künyeler yer almalı.
2. **ShareAlike bulaşır** — klipleri değiştirip (kırpma, overlay, hızlandırma) dağıtırsan
   **türev video da CC BY-SA 4.0** olmalıdır.

**ShareAlike yalnızca video türevine bulaşır; aynı depodaki koda bulaşmaz.** Yazılım lisansın
bundan etkilenmez.

Pratik sonuç: demo videosunun açıklamasına şu satır konmalıdır —

> Bu videoda kullanılan kamera görüntüleri CC BY-SA 4.0 lisanslıdır (kaynaklar:
> US DOT/FHWA NGSIM; Wikimedia Commons). Video CC BY-SA 4.0 ile paylaşılmaktadır.
