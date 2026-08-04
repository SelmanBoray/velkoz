# PROGRESS.md — Vel'Koz Proje Günlüğü

## 4-5 Ağustos 2026 — Taşınabilir dağıtım paketi (üretildi ve test edildi)

- **`scripts/paket_hazirla.py`**: venv + jina-clip-v2 önbelleği + kod + YOLO ağırlığı +
  `basla.bat` / `denetle.bat` / `OKUBENI.md` → tek klasör. `--dry-run` boyut raporu verir,
  `--zip` sıkıştırır. Üretilen paket **6.59 GB**.
- **Uçtan uca doğrulandı — paketin İÇİNDEN, ağ kapalı (proxy blokajı):**
  `doctor` 9/9 ✅ (yollar paketin kendi içine çözüldü) · indeksleme ✅ (25 kare + 201 kırpık) ·
  arama ✅ (0.400 doğru sonuç) · bulunamadı kapısı ✅. Test paketi sonra silindi.
- **PyInstaller/Inno Setup seçilmedi.** PyInstaller denenmişti: arama yolu çalıştı ama
  `ultralytics` import'u kırıldı — tespit hattı hiç doğrulanmadı. Inno Setup 4.2 GB dosya
  tavanı yüzünden payload bölmeyi gerektiriyor. Taşınabilir klasör aynı sonucu çok daha az
  emekle veriyor ve hata ayıklaması açık (kaynak görünür).
- **Kapsam kararı: Ollama pakete dahil edilmedi.** +1.1 GB çalıştırıcı +3.2 GB model demek
  ve sessiz kurulumu bilinen bir sorun. Görsel-dil doğrulaması zaten opsiyonel — yokluğunda
  sistem CLIP-only çalışır ve arayüz durumu bildirir. Paket ~4.3 GB küçüldü, en kırılgan
  parça dışarıda kaldı. Karar ve gerekçe betik başlığında yazılı.

## 4 Ağustos 2026 — Çevrimdışı sertleştirme: iki gizli ağ çıkışı kapatıldı

Dağıtım hazırlığında "ağ kapalıyken çalışıyor mu" testi yapıldı (proxy blokajı, localhost
hariç). **İki ayrı ağ çıkışı bulundu — ikisi de ürünün "hiçbir veri dışarı çıkmaz" sözüyle
doğrudan çelişiyordu.**

- **1) YOLO ağırlığı sessizce GitHub'dan indiriliyordu.** `yolo_model = "yolo11m.pt"` çıplak
  göreli addı; ultralytics onu ÇALIŞMA DİZİNİNE göre çözüyor, bulamazsa indiriyor.
  Ölçüldü: proje kökü dışından çalıştırınca **38.8 MB çekti**. Sonuçları: (a) ağı olmayan
  müşteri makinesinde anlaşılmaz çökme, (b) KVKK anlatısının ortasında habersiz dış bağlantı.
  Düzeltme: yol proje köküne **mutlak** sabitlendi; ağırlık yoksa sessiz indirme yerine
  **çözüm komutunu içeren net hata**.
- **2) transformers her açılışta HuggingFace'e bağlanıyordu.** `from_pretrained` varsayılan
  olarak "config.json güncel mi" diye HEAD atıyor. Ağ kapalıyken 5 kez yeniden deneyip
  **42 saniye** sonra çöküyordu → ürün çevrimdışı makinede HİÇ çalışmıyordu.
  `local_files_only=True` **yetmedi**: `trust_remote_code` uzak kodu ve jina-clip-v2'nin
  bağımlı repoları (implementation, xlm-roberta-flash) ayrı çağrılarla çekiliyor.
  Düzeltme: `config.py::_cevrimdisi_kilidi()` — model önbellekte varsa `HF_HUB_OFFLINE=1`
  transformers import edilmeden ÖNCE kurulur. İlk kurulum bozulmaz (önbellek yoksa bayrak
  konmaz); kullanıcı açıkça verirse kararı ona bırakılır.
- **Doğrulandı (ağ kapalı, proxy blokajlı):** arama ✅ · indeksleme ✅ (25 kare + 201 kırpık).
- **Taşınabilirlik:** `DATA_DIR` tek başına verilince `thumbs_dir`/`qdrant_path` onu takip
  ediyor (`model_post_init`). Önceden üç değişkeni ayrı vermek gerekiyordu; biri unutulunca
  indeks bir yere, küçük resimler başka yere yazılıyordu.
- **Qdrant kilidi zarif hata veriyor.** Gömülü mod münhasır kilit kullanıyor; ham mesaj
  ("already accessed by another instance") ne yapılacağını söylemiyordu. Artık en olası
  sebebi (arayüz açıkken indeksleme) ve çözümü yazıyor. İki süreçle test edildi.
- **`doctor`'a çevrimdışı kilit satırı eklendi** — "veri dışarı çıkmaz" sözünün denetlenebilir
  kanıtı; toplam 9 bileşen kontrolü.
- **Regresyon yok:** R@1 0.833 · R@5 0.917 · R@10 1.000 · MRR 0.889 · Faz-2 11/12 · ayrım 2/2.
  `experiments/2026-08-04_cevrimdisi_sertlestirme/`

## 4 Ağustos 2026 — Lisans denetimi: ticarileştirmenin önündeki gerçek engel

Paketleme fizibilitesi araştırılırken paketlemeden daha kritik bir bulgu çıktı.

- **Üç çekirdek modelin üçü de ticari kullanıma kapalı:** `jina-clip-v2` **CC-BY-NC-4.0**
  (sistemin kalbi), `qwen2.5vl:3b` **Qwen Research** (non-commercial), `ultralytics` YOLO11
  **AGPL-3.0** (dağıtım kaynak açmayı tetikler). Prototip/akademik/TEKNOFEST kullanımı
  sorunsuz; engel yalnız satış aşamasında başlıyor.
- **Tuzak:** Ollama kayıt sayfası `qwen2.5vl:3b` için Apache-2.0 gösteriyor — YANLIŞ.
  Bağlayıcı olan yukarı-akış (`Qwen/Qwen2.5-VL-3B-Instruct`, qwen-research). Qwen2.5-VL
  ailesinde yalnız **7B** Apache-2.0.
- **Ölçülen ve REDDEDİLEN çözüm:** `qwen3-vl:2b` (Apache-2.0, zaten kurulu) tek satırlık
  "bedava kazanç" diye önerildi. A/B koşuldu: **11/12 → 9/12**. Renk sorgularının üçü
  birden kırıldı (siyah SUV, beyaz araba, kırmızı araba) — model renk sorularına aşırı
  "hayır" eğilimli. `mavi kamyonet`'in "düzelmesi" de aynı aşırı-negatifliğin yan etkisi,
  gerçek kazanç değil. **qwen2.5vl:3b'de kalındı.**
  Ders: lisans uyumu için model değiştirmek ücretsiz değil; ölçmeden yapılmaz.
- **`docs/LISANS_DURUMU.md`** yazıldı: bileşen bazında lisans tablosu, ticari etki,
  üç madde için seçenek karşılaştırması (Jina ticari lisans / SigLIP2 / LAION XLM-R;
  qwen2.5vl:7b; AGPL yayını vs RT-DETR). Öneri: demo öncesi CLIP DEĞİŞTİRİLMEMELİ —
  model değişimi C1 baseline'ını ve tüm karşılaştırmaları geçersiz kılar.
- **Paketleme kararı: portable ZIP** (PyInstaller/Inno değil). Gerekçe: PyInstaller build'i
  denendi, arama yolu çalıştı ama `ultralytics` import'u kırıldı — yani tespit hattı hiç
  doğrulanmadı; 6,4 GB çıktı temizlendi. Portable ZIP aynı boyutu onda bir emekle veriyor.
  Öncesinde 4 kod düzeltmesi gerekiyor (yazma yolları, YOLO ağırlık yolu, Qdrant kilidi,
  Streamlit başlatma) — bunlar ZIP için de gerekli.

## 4 Ağustos 2026 — Türkçe kök eşleşme hatası: "karanlık" → KAR olarak okunuyordu

C1'den (21 Tmz) beri eval'de duran tek `false_gate`'in kökü bulundu. Sorun sanılan yerde
(bulunamadı kapısı) DEĞİL, sorgu ayrıştırıcısındaydı.

- **Belirti:** "karanlıkta ilerleyen araçlar" sürekli BULUNAMADI dönüyordu, oysa korpusta
  gece araç görüntüsü var. İlk hipotez (envanter kapısı) doğrudan testle çürütüldü — kapı
  geçiriyordu. Asıl yer: CLIP 9 doğru aday getiriyor, VLM **hepsini** eliyordu.
- **Kök neden:** `augment_intent("karanlıkta…")` → `obj_en = "snow"`. Sistem VLM'e
  *"bu görüntüde KAR var mı?"* diye soruyordu. `_HARD_CONCEPT_ROOTS` içindeki **"kar"**
  kökü düz `startswith` ile eşleştiği için **"kar-anlık"**, **"kar-ayolu"**, "kar-şı",
  "kar-deş" hepsi snow'a düşüyordu. CCTV bağlamında *"karayolunda ilerleyen araçlar"*
  da aynı tuzağa düşerdi — gerçek kullanımda çok daha olası bir sorgu.
- **Kapsam:** aynı hatalı desen dosyada **9 ayrı yerde** vardı (renk/sınıf/sahne/taşıt
  kökleri, TR→EN çevirisi, `needs_vlm` tetiği). Hepsi düzeltildi.
- **Düzeltme:** kök eşleşmesinden sonra kalan parçanın **gerçek bir Türkçe ek dizisi**
  olduğu doğrulanıyor (`_EK_DIZISI`, `_kok_eslesir`). "karda"/"karlı" geçer, "karanlık"
  geçmez. Bilinen sınır dokümante edildi: kök+tek sesli ("kara") ayırt edilemez.
- **Ölçüm (aynı korpus, aynı sorgu seti, tek değişken):**
  R@5 **0.833 → 0.917** · R@10 **0.917 → 1.000** · MRR **0.847 → 0.889** ·
  Makro R@5 **0.850 → 0.917** · Faz-1.5 marjini **+0.167 → +0.250** ·
  **yanlış kapı: scene_karanlik_yol → YOK**. `scene_karanlik_yol` BULUNAMADI → rank 2.
- **Regresyon yok:** Faz-2 11/12 ve ayrım 2/2 aynen korundu; negation 3/3. Ayrıştırıcı
  düzeyinde de doğrulandı (karla/karda/karlı → snow, köpek → dog, yağmur → rain).
- **Ders:** eval'in iki turdur "bilinen açık" diye taşıdığı şey gerçek bir üründe bozukluktu.
  Metriğin işaret ettiği her anomali, açıklanana kadar bir hata adayıdır.
  Detay: `experiments/2026-08-04_kok_eslesme_fix/OZET.md`.

## 4 Ağustos 2026 — Açık lisanslı DEMO korpusu + iki-indeks ayrımı

Ölçüm korpusu (MEVA/VIRAT/UCF) araştırma lisanslı → demo videosu paylaşılamıyordu.
Çok açılı kaynak taraması yapıldı (stok platformlar, akademik açık veri, canlı kameralar,
sentetik üretim).

- **Kritik lisans bulgusu:** "ücretsiz" stok platformlarının neredeyse tamamı (Pexels,
  Pixabay, Mixkit, Coverr) **ham dosya yeniden dağıtımını yasaklıyor**. Coverr ve Pexels
  ayrıca içeriğin veri setine girmesini / ML "evaluate" amaçlı kullanımını açıkça yasaklıyor —
  bu Vel'Koz'un indeksleme mimarisiyle doğrudan çelişiyor. Hiçbiri kullanılmadı.
- **Kullanılabilir bulunan:** US DOT/FHWA **NGSIM** (CC BY-SA 4.0, Socrata API'sinden
  `licenseId: CC_40_BY_SA` doğrulandı) ve **Wikimedia Commons** (CC BY-SA 4.0).
- **6 aday indirildi, 3'ü elendi** — eleme projenin KENDİ dedektörüyle objektif yapıldı:
  Montreal kavşağı **35 bisiklet** (neg_bisiklet kapısını kırardı), NGSIM Lankershim cam1+cam3
  **0 tespit** (tepeden dik açı, YOLO tanımıyor, gerçek CCTV geometrisi değil).
- **İKİ-İNDEKS AYRIMI (mimari karar).** Demo klipleri ölçüm korpusuna KARIŞTIRILMADI.
  Ölçüm: `data/qdrant_storage` (17 video / 6231 vektör, **dokunulmadı, doğrulandı**).
  Demo: `data/qdrant_demo` (3 klip / 1874 vektör, bisiklet YOK). Gerekçe: karıştırılsaydı
  dondurulmuş GT her demo klibinde yeniden eskir ve havuzlama gerekirdi; ayrı indeks bu bağı keser.
- **Demo senaryosu doğrulandı.** Pozitifler çalışıyor ("park halindeki arabalar" 0.400,
  "kaldırımda yürüyen yaya" 0.400). Üç negatif de doğru "bulunamadı" veriyor ve **iki farklı
  mekanizma** gösterilebiliyor: bisiklet → envanter kapısı, köpek/kar → VLM elemesi.
- **Dürüst sınır:** kabul edilen 3 klibin hiçbiri gerçek sabit-CCTV değil (kule çekimi,
  sokak seviyesi, el kamerası). Açık lisanslı gerçek gözetim açılı video pratikte yok —
  gerçek CCTV setlerinin tamamı araştırma lisanslı. Orta vadede kendi çekimimiz gerekli.
  Kaynak künyeleri, zorunlu atıflar ve ret gerekçeleri: `docs/DEMO_KORPUS_LISANS.md`.

## 4 Ağustos 2026 — Hata dayanıklılığı: iki sessiz yanlış-güven yolu kapatıldı

Yeni kullanıcının karşılaşacağı arıza senaryoları gerçekten koşturularak test edildi
(env-override ile simüle: Ollama kapalı, indeks boş).

- **Boş indekste kapı YALAN SÖYLÜYORDU.** Hiç video indekslenmemişken "otobüs" araması
  `"Korpusta 'otobüs' tespit edilmedi — bu nesne kayıtlarda yok."` diyordu — sanki arşiv
  taranmış da bulunamamış gibi. Yeni kullanıcı `index` çalıştırması gerektiğini anlayamaz;
  projenin en iyi özelliği (dürüst bulunamadı kapısı) tam da ilk deneyimde yanıltıyordu.
  Düzeltme: kapıdan ÖNCE `count() == 0` kontrolü → *"İndeks boş — henüz hiç video
  indekslenmemiş. Önce: python -m gozcu index <video_klasörü>"*. Gerçek bulunamadı kapısı
  (dolu indekste `bisiklet`) aynen çalışıyor, doğrulandı.
- **`vlm_unavailable` sözleşmesi yanlıştı.** Bayrak yalnız VLM *koşarken çökerse*
  işaretleniyordu; Ollama **baştan kapalıysa** `refine_vlm` outcome'u aynen döndürüyor,
  bayrak `False` kalıyordu. Viewer kendi `vlm_available()` kontrolüyle korunuyordu (kullanıcı
  yanlış bilgi görmüyordu), ama savunma **tek hatta** kalmıştı — bayrağa güvenen herhangi bir
  çağıran "doğrulandı" sanabilirdi. Düzeltme: `refine_vlm`/`stream_verify` artık "VLM istendi
  ama alınamadı" durumunu da işaretliyor. VLM gerektirmeyen sorguda bayrak `False` kalır
  (eksiklik yok) — dört kombinasyon da test edildi.
- **Regresyon yok:** retrieval R@1 0.833 · R@5 0.833 · MRR 0.847 (C2-GT, birebir aynı),
  Faz-2 11/12 · ayrım 2/2. `experiments/2026-08-04_dayaniklilik/`.

## 4 Ağustos 2026 — Kurulabilirlik: `doctor` komutu + CPU-only torch tuzağı kapatıldı

- **Soru:** projeyi klonlayan biri (jüri/mentor/hakem) çalıştırabiliyor mu? Denetlendi,
  **6 tuzak** bulundu — hiçbiri hata vermiyor, sessizce yanlış davranıyordu.
- **En kritik: sessiz CPU-only torch.** `requirements.txt`'te `torch` düz yazılıydı →
  `pip install -r requirements.txt` Windows'ta **CPU-only wheel** getiriyor. `device: "auto"`
  sessizce cpu'ya düşüyor: proje ÇALIŞIYOR ama ~20x yavaş ve **hiçbir hata mesajı yok**.
  Kullanıcı yavaşlığın sebebini asla bulamaz. requirements.txt başlığına uyarı kutusu +
  README'ye iki-adımlı kurulum (önce CUDA indeksinden torch) eklendi.
- **`python -m gozcu doctor` eklendi** (`cli.py`). 8 bileşeni tek tek denetler: Python ·
  torch+CUDA (GPU adı + VRAM) · torchvision CUDA derlemesi (YOLO NMS) · transformers<4.50
  kilidi · YOLO ağırlığı · jina-clip-v2 önbelleği · Qdrant vektör sayısı · Ollama+VLM.
  Her arıza için **düzeltme komutu** basar; kritik sorunda exit 1 (CI'ya uygun).
  Arıza yolları env-override ile test edildi (VLM erişilemez + ağırlık yok → doğru uyarı).
- **Diğer kapatılan boşluklar:** venv adımı ve Python 3.12 gereksinimi kurulumda yoktu ·
  Ollama'nın kendisinin kurulumu yazılı değildi (yalnız `ollama pull` vardı) · ilk
  çalıştırmadaki ~1.7 GB jina-clip-v2 + ~40 MB YOLO indirmesi belirtilmemişti ·
  `yolo11m.pt` git'te yok (`.gitignore`: `*.pt`) ama README bundan bahsetmiyordu.
- README güncellendi: korpus 13→17 video / 6231 vektör, güncel eval sayıları
  (R@1 0.833 · R@5 0.833 · MRR 0.847 · VLM 11/12 · ayrım 2/2), test verisi lisans notu.

## 4 Ağustos 2026 — Korpus v2 (13→17 video) + GT havuzlama protokolü

- **Task #4 tamamlandı.** MEVA-S3'ten 4 klip indekslendi: `meva_okul_G330` (basketbol salonu,
  30s), `meva_okul_G339` (kampüs/park), `meva_hastane_G341` + `meva_otobus_G505` (dış mekân yaya).
  Korpus **13→17 video**, **4395→6231 vektör**. `available_object_classes()` içinde **bisiklet YOK**
  → eyeball-gate tuttu, `neg_bisiklet` envanter kapısı korundu.
- **Sahte regresyon yakalandı ve teşhis edildi.** C1-GT ile ölçüm R@5 0.917→0.833, MRR 0.917→0.785
  gösterdi. İnceleme: `gold_yuruyen_insan` top-5'inin **tamamı doğru yürüyen insan** (yeni
  videolardan, skorları C1 top-1'inden yüksek). Yani model değil, **GT eskimiş** — IR'deki
  *incomplete relevance judgments* problemi. Kırpık küçük resimleri gözle doğrulandı.
- **`eval/queries_c2.yaml` (GT havuzlama).** `queries.yaml` C1 için **dondurulmuş kaldı**.
  Genişletme kararı arama sonucuna DEĞİL videonun içeriğine bakılarak verildi; **kanıtı zayıf
  4 genişletme reddedildi** (G339→otopark değil, G339 kamyonu bulanık, G330 basketbol "yürüyen"
  değil, G505 park-arası değil). Yapılan 2 genişletme görsel kanıtlı.
  Sonuç C2-GT ile: **R@1 0.833 · R@5 0.833 · MRR 0.847**; `beh_uzakta_yuruyen` **4→1**.
- **Üç yargı:** GUARD **GEÇTİ** (gerçek regresyon yok) · DEDEKTİF **TEMİZ** (5 yasaklı kavramın
  hiçbiri sızmadı, negation 4/4 GATE + Faz-2 3/3) · İYİLEŞME **KISMİ**.
- **Kazanç: `hn_kirmizi_kiyafet` not_found → has_results.** C1'de hiç sonuç bulunamıyordu;
  artık G330'dan 2 doğru insan sonucu dönüyor, **0 araç sızıntısı**. İnsan-renk pozitif yolu
  ilk kez canlı test edildi. `hn_siyah_kiyafet` hâlâ vacuous (⚠ işaretli bırakıldı).
  Faz-2 **11/12, ayrım 2/2** — C1 ile aynı; `mavi kamyonet` C1'den devralınan bilinen açık.
- **Açık madde:** `gold_yuruyen_insan` rank 6'da kaldı. Havuzlama düzeltmedi çünkü `gold_*`
  metriği **tek golden kareye** bağlı ve korpus büyüdükçe bu varsayım kırılıyor. `golden_frame`'e
  DOKUNULMADI (metrik kurtarmak için GT oynatmak p-hacking olurdu). Graded relevance'a geçiş
  değerlendirilecek.
- **Araç:** `faz2_eval.py`'a `--queries` / `--out` eklendi (sürümlenebilir eval).
  Detay: `experiments/2026-08-04_korpus_v2_guard/OZET.md`.

## 21 Temmuz 2026 — Hard-negative eval kapsamı + ayrım ekseni (AI Engineer #5)

- Loop devam: en kırılgan düzeltmemizin (**"kırmızı kıyafetli adam" araba getiriyordu**)
  eval'de HİÇ regresyon koruması yoktu. Eval sadece not_found/has_results ölçüyordu →
  "sonuç doğru sınıfta mı" kör noktası. AI Engineer tasarımıyla **ortogonal ayrım ekseni** eklendi.
- **`queries_faz2.yaml`:** 2 hard-negative (`hn_kirmizi_kiyafet`, `hn_siyah_kiyafet`), şema
  `expect: any` + **`forbid: vehicles`** (sembolik → `VEHICLE_CLASSES`). Kritik: depodaki
  `yolo_class` Türkçe (araba/kamyon) — İngilizce liste yazılsa test sahte-PASS ederdi (AI Eng. yakaladı).
- **`faz2_eval.py`:** ikinci eksen — yasaklı sınıf sonuçlara sızarsa FAIL; outcome eksenine
  DOKUNMAZ → **9/10 baseline aynen korunur** (forbid'siz girdiler eski gibi ölçülür). Vacuous-pass
  dürüstlüğü: sızan (sonuç) vs elenen (`vlm_filtered`) karşılaştırılıp ⚠ ile işaretlenir.
- **Ölçüldü — 11/12 (%92), ayrım 2/2:** `hn_kirmizi_kiyafet` **non-vacuous kanıt** — CLIP tam
  eski bug'daki gibi **6 kırmızı araba adayı** çıkardı, VLM **6'sını da eledi, 0 sızdı**. Düzeltme
  artık gerçek testle kilitli. `hn_siyah_kiyafet` vacuous (kişi sorgusu siyah aracı aday yapmadı)
  → latent canary. `mavi kamyonet` hâlâ dokümante tavan FAIL (skoru şişirmiyoruz).
- **Eşik kalibrasyonu bilinçli YAPILMADI:** confidence binary {0,1} → `vlm_drop_below` no-op,
  `vlm_beta` sabit ofset. Kalibrasyon sürekli-confidence ister (feature, kapsam dışı). `config.py`
  yorumu dürüstleştirildi. Detay: ARCHITECTURE §6c · `experiments/2026-07-21_hard_negatif_eval/`.

## 6 Temmuz 2026 — Hibrit LLM sorgu-ayrıştırıcı (AI Engineer #2)

- Türkçe NL → yapısal niyet. AI Engineer: hibrit — kurallar önce (deterministik, baseline
  taşıyor), LLM sadece EKLER. Muhafazakâr yorum uygulandı: **LLM yalnız kurallar NESNE
  bulamazsa** (OOV, ör. "forklift") devreye girer → asla regres etmez.
- **`query.augment_intent` + `_llm_parse`:** qwen2.5vl text-only (ZATEN yüklü → +0 VRAM),
  format:json → {object,color} (İngilizce), cache'li, hata/Ollama-yok → kural sonucu.
  `search.verify_top_n`/worker artık `augment_intent` kullanır.
- **Ölçüldü:** kural-yolu (kırmızı araba, köpek gezdiren→dog, siyah SUV) **0ms, LLM'e
  uğramaz → eval %90 dokunulmaz**; OOV-yolu (~2.5s): forklift✓, tractor✓, vinç→car (1 kaçak,
  ama OOV korpusta yok → önemsiz). Zaman regex'te bırakıldı (deterministik, ts-filtre besler).
- Broader relation/negation LLM'i ERTELENDİ: kuralların hard-concept mantığı (köpek gezdiren→
  dog) zaten akıllı; LLM override'ı bozabilir → yalnız-boş-nesne tetiği güvenli. Detay: ARCHITECTURE §4.

## 6 Temmuz 2026 — Zaman grounding: "ne zaman görüldü" (AI Engineer #3)

- Selman zaman-aralığı özelliği istedi. AI Engineer tasarımı: tracking YOK → "girdi/çıktı"
  kimlik yalanı YAZILMAZ; dürüst **"görülme aralığı"** (zaman-yakınlığı kümeleme).
- **`search.cluster_events`:** doğrulanmış sonuçlar video+ts'e göre olaylara bölünür
  (ardışık boşluk > `event_gap_s=50s` → yeni olay); her olay ilk/son görülme + kare sayısı.
  **Saf sunum katmanı** — retrieval/verify'a dokunmaz → eval %90 baseline korunur.
- **`viewer.render_timeline`:** "İlk 21:26:07 · Son 21:28:18 (~131s, 9 kare)"; tek-hit →
  "21:33:36'te görüldü" (sahte aralık yok). Uyarı: "kimlik takibi yok". **Ölçüldü:** kırmızı
  araba 9 sonuç→1 olay (~131s); yürüyen insan→2 olay (VIRAT ~18s + meva tek an).
- Detay: ARCHITECTURE.md §9. Sıradaki: #2 sorgu-ayrıştırıcı→LLM (hibrit, LLM sadece zayıf sorguda).

## 6 Temmuz 2026 — Loop iterasyonu: eval flag'i araştırıldı (mavi/teal model tavanı)

- Loop çalışıyor: eval "mavi kamyonet"i flag'ledi (5 sonuç, beklenen bulunamadı) → araştırıldı.
- **Teşhis (gözle):** korpusta mavi kamyonet yok (ground-truth doğru). Yanlış-kabul sebebi
  gerçek model tavanı: qwen2.5vl mavi/teal'i karıştırıyor (teal otobüs→"mavi") + bulanık uzak
  kırpıkta kamyonet/otobüs/araba ayrımı zayıf.
- **Lever denendi + ELENDİ:** sıkı renk promptu ("predominantly blue, teal/yeşil değil") A/B:
  mavi True 3/4→**0/4** (düzeltti) AMA kırmızı/siyah True **6/6→2/6** (gerçek eşleşmeleri de
  öldürdü, aşırı-muhafazakâr — sıkı-presence prompt'uyla aynı desen). Temiz fix yok.
- **Karar: tavan kabul + dürüst FAIL olarak tut** (skoru şişirme). Eval %90'da kalıyor; daha
  iyi VLM/korpus gelince yükselir. Loop'un dürüst sonucu: her flag kod-fix almaz, bazıları
  araştırılıp belgelenen tavandır. Detay: `experiments/2026-07-05_vlm_latency/renk_prompt_ab.py`.

## 5 Temmuz 2026 (gece-6) — Otonom loop: streaming decouple (freeze çözüldü) + YOLO-skip latency

- Selman "tüm önerileri uygula → düşün → devam et, loop'ta çalış" dedi. AI Engineer'a
  streaming deseni + sonraki-round refleksiyonu danışıldı. Kritik meta: **loop'un objektif
  bir eval skoruna ihtiyacı var** (yoksa his'le sürüklenir) → eval sıradaki #1.
- **Streaming render-block ÇÖZÜLDÜ (freeze gitti):** senkron `stream_verify` ~40s ana thread'i
  bloke edip tarayıcıyı donduruyordu. Çözüm (AI Engineer deseni): **worker thread** hit['_vlm']'i
  doldurur (st.* YOK → context sorunu yok, module-level store + Lock), viewer **`st.fragment(
  run_every='0.5s')`** ile poller; bitince `st.rerun` → cached dal (polling durur). `search.py`:
  `StreamJob`/`start_stream_job`/`get_stream_job`/`clear_stream_job`. **TARAYICIYLA DOĞRULANDI:**
  "kırmızı araba" → verification boyunca tarayıcı YANIT VERDİ (screenshot donmadı), kartlar canlı
  doldu, temiz final (Oynat). Fragment dış-container'a yazamaz hatası düzeltildi (kendi alanına render).
- **Latency: renk sorgusunda YOLO-presence-skip** (AI Engineer #4): aday kırpığın YOLO sınıfı
  hedefle eşleşiyorsa (araba=car) presence VLM çağrısı atlanır → renk 2-sorgu 99→77s. Bonus:
  siyah SUV 7→8 (bir presence false-negative de düzeldi).
- **Town Centre elendi:** artık yalnız torrent/Kaggle (erişilemez) + gizlilik nedeniyle kaldırılmış
  (KVKK ürünü için ironik). Korpus → Selman'ın kendi klipleri (bekliyor).
- **Sıradaki round (AI Engineer refleksiyonu):** 1) eval harness (metrik — pazarlık dışı),
  2) sorgu-ayrıştırıcı→LLM, 5) hard-negatif+kalibrasyon, 3) zaman-aralığı grounding, 4) adaptif top_n.

## 5 Temmuz 2026 (gece-5) — UX cilası: bbox-vurgulu kart görseli (3/4, kısmi)

- **Kart görseli artık bbox-vurgulu:** kırpık aday için tam-kare thumb üzerine eşleşen özneyi
  KIRMIZI KUTUYLA işaretle (`viewer._card_image` + `recrop.draw_bbox`). Kullanıcı "hangi
  araç/kişi eşleşti" anında görüyor — minik kırpık/meşgul sahne yerine bağlamlı. **Tarayıcıyla
  doğrulandı:** "siyah SUV" → her kartta dark SUV'un etrafında kutu + "✅ renk doğru". Net kazanç.
- **Streaming'de reddedileni soluklaştırma** (`_card_image(dim=True)` + `_is_rejected`): doğrulanıp
  reddedilen kart "eleniyor" görünür ('sonuç' değil).
- **BİLİNEN SINIR (gelecek iş):** senkron `stream_verify` ~40s ana thread'i bloke ediyor →
  verification sırasında tarayıcı donuyor (CDP screenshot timeout). AI Engineer çözümü: worker
  thread + `st.fragment(run_every=0.5s)`. Yüksek riskli rework olduğu için ayrı, odaklı bir
  oturuma bırakıldı — mevcut akış DOĞRU sonuç üretiyor (yalnız verification boyunca janky).
  Latency kaynağı: vlm_top_n=12 × ~2 çağrı; vlm_top_n düşürülerek de kısaltılabilir.

## 5 Temmuz 2026 (gece-4) — VLM doğruluğu: hibrit doğrulama görüntüsü (2/4)

- AI Engineer (b): kırpık yerine tam-kare+bbox doğrula (küçük-kırpık yanlış-pozitifi +
  çok-nesne kapsamı). Uyguladım AMA ölçüm bir uyarı gösterdi: tam-kare renk sorgularını
  FAZLA ELİYOR (siyah SUV 7→2, gözle doğrulandı — kutulu araç açıkça siyah SUV ama VLM
  768px'e küçültülmüş meşgul sahnede "kutuda araba yok" dedi). Latency da 46s'e çıktı.
- **Karar: HİBRİT (ölçümle en iyi):**
  - **Renk/öznitelik → tight-kırpık** (özne kadrajı doldurur, renk net, hızlı — kanıtlı iyi).
  - **Zor-kavram (köpek/yağmur) → kutusuz tam-kare** (nesne kırpık dışında olabilir).
- **Sonuç:** "köpek gezdiren adam" → **BULUNAMADI** (önceki 1 yanlış-pozitif GİTTİ, tam-kare
  sayesinde). "kırmızı araba" 7/7, "siyah SUV" 7 (fazla-eleme yok). "kırmızı kıyafetli adam"
  bulunamadı. `recrop.vlm_frame_for_hit`/`draw_bbox` eklendi (bbox kart görselinde de kullanılacak).
  Detay: ARCHITECTURE.md §8, `experiments/2026-07-05_vlm_latency/tam_kare_gorsel.py`.

## 5 Temmuz 2026 (gece-3) — "Mükemmelleştirme" turu: Kararlılık (AI Engineer planı, 1/4)

- Selman "mükemmel hale getirelim" dedi, 4 alan seçildi (UX/kararlılık/VLM doğruluğu/korpus).
  AI Engineer'a danışıldı, sıra: **Kararlılık → Korpus → VLM doğruluğu (tam-kare) → UX**.
- **Kök sorun:** Ollama %91 VRAM'de arka plan GPU uygulamalarıyla OOM çöküyor → tüm kartlar
  "doğrulanamadı" (bugün bizzat çarpıldı). AI Engineer: CLIP'i CPU'ya al (GPU'yu VLM'e bırak).
- **CLIP→CPU DENENDİ, ELENDİ:** jina-clip-v2 text tower CPU'da sabit **~13s/çağrı** (561M×512
  token, thread/MKL fark etmiyor) — interaktif aramayı öldürür. GPU'da 286ms. VRAM ölçümü:
  CLIP CPU'da → 7445→5932 MiB (co-residency çözülür) AMA 13s bedeli kabul edilemez.
- **Çözüm — çökmeyi ÖNLE değil ZARİFÇE KURTAR** (CLIP GPU'da kalır):
  - **Self-healing `is_available`** (`search.py`): kısa TTL (30s) + hata-anında reset. "Bir
    kez False→hep False" bug'ı bitti; çökme/geri-gelme otomatik iyileşir.
  - **Ayrık çökme UX'i:** tekil verify-fail = kart rozeti; TOPTAN VLM-down = global banner
    "VLM kapalı → yalnız CLIP" (`SearchOutcome.vlm_unavailable`, `viewer.render_final`).
  - **Açılış warmup** (`verifier.warmup` + `viewer._warmup_vlm` arka plan thread) → ilk sorgu cold değil.
  - **timeout 20→30s** (yalnız emniyet). Supervised Ollama (masaüstü uygulaması auto-restart).
- **Test:** Ollama down iken → vlm_available False, CLIP-only sonuç, kartlarda _vlm yok, banner
  tetiklenir. Ollama up → normal. GPU encode warm 286ms. Detay: ARCHITECTURE.md §8.

## 5 Temmuz 2026 (gece-2) — "kırmızı kıyafetli adam" hâlâ araba gösteriyordu: 3 UI/füzyon düzeltmesi

- Selman bir önceki turdan sonra hâlâ kırmızı araba görüyordu. **Tarayıcıyla bizzat
  reprodüksiyon** (Chrome) kök nedeni gösterdi: sorun 3 katmanlı, hepsi düzeltildi + görsel doğrulandı.
- **Kuyruk sızıntısı:** `default_top_k=12` ama `vlm_top_n=8` → rank 9-12 DOĞRULANMADAN
  ekleniyordu (kırmızı arabalar). `vlm_top_n=12` (=default) + `_fuse_verdicts` doğrulanmamış
  kuyruğu döndürmez.
- **Renk-uymayan ana ızgarada kalıyordu:** füzyon `present=False`'u eliyordu ama `color_match
  is False`'u tutuyordu → renk uymayan kartlar "🚫 renk uymadı" rozetiyle görünmeye devam
  ediyordu. Renk artık ölçülmüş güvenilir (qwen2.5vl red/blue 9/9↔0/9) → renk sorgusunda
  `color_match is False` de elenir. Böylece hiç gerçek eşleşme yoksa → **bulunamadı** (eski
  "renk güvenilmez→rerank-only" tasarımı qwen3-vl JSON rubber-stamp içindi, artık geçersiz).
- **Bulunamadı mesajı renk-farkında:** "aranan renk/nesne bileşimi doğrulanamadı."
- **TARAYICIYLA DOĞRULANDI:** "kırmızı kıyafetli adam" → ana görünüm "🔍 Bulunamadı",
  7 kırmızı araba "VLM elenenler (7)" expander'ında. Regresyon yok: kırmızı araba 7/7,
  siyah SUV 1 eledi. Kalan UX notu: streaming ~30s CLIP adaylarını ⏳ ile gösterir (final
  reflow doğru) — kabul edilebilir. Detay: ARCHITECTURE.md §8.

## 5 Temmuz 2026 (gece) — Selman'ın 2 sorgusu: renk-giysi + füzyon düzeltmeleri

- Selman "köpek gezdiren adam" ve "kırmızı kıyafetli adam" aradı, ikisi de yanlış gösterdi.
  Gerçek hattan teşhis edildi (2 kök sorun + 1 model tavanı):
- **BUG 1 (düzeltildi) — renk insanlarda giysiye işaret eder:** "kırmızı kıyafetli adam"
  VQA hedefi `('man','red')` → VLM'e "Is the man red?" soruyordu (kimse kırmızı değil→herkes
  "no"). `verifier._PERSON_OBJECTS` eklendi: insan-tipinde "Is this man wearing red clothing?".
- **BUG 2 (düzeltildi) — füzyon renk modunda nesne-yokluğunu düşürmüyordu:** CLIP "kırmızı"ya
  takılıp kırmızı ARABALAR getirdi; VLM doğru `present=False` dedi ama attribute mod düşürmüyordu
  → 7 araba gösterildi. Eski "renk modunda düşürme" tasarımı JSON rubber-stamp güvenilmezken
  doğruydu; yes/no ile nesne-varlığı GÜVENİLİR → `_fuse_verdicts` her iki modda `conf<drop_below`
  düşürür. Sonuç: 7 araba → 5 elendi. Regresyon yok (kırmızı araba 7/7, siyah SUV 1 eşleşmeyeni eledi).
- **Rozet dürüstlüğü:** renk uymayınca "✅ VLM" değil "🚫 renk uymadı" (`viewer._verdict_badge`).
- **MODEL TAVANI (kabul):** qwen2.5vl:3b küçük/bulanık kırpıkta varlık sorusunda yes-bias'lı
  (insanda "köpek var" / arabada "adam var" yanlış-pozitif). Sıkı prompt denendi → gerçek
  uzak-insanları da reddediyor (false-negative'e çeviriyor), temiz çözüm yok → tavan kabul.
  Ayrıca korpusta HİÇ köpek yok → "köpek gezdiren adam" doğası gereği ~bulunamadı + gürültü.
  Detay: `experiments/2026-07-05_vlm_latency/varlik_prompt_ab.py`.

## 5 Temmuz 2026 (akşam) — VLM güvenilirlik: thinking modeli atıldı, yes/no VQA'ya geçildi

- **Sorun teşhis edildi (deterministik):** `qwen3-vl:2b` bir *thinking* modeli — belirsiz
  kırpıklarda sonsuz düşünme döngüsüne girip n_ctx=4096'yı doldurur, boş `content` döner
  (%33 hata). ~25s "timeout"lar aslında 2905-token kaçak *generation*. Her görüntü 2×→birebir
  aynı. `think:false`/`/no_think`/`num_predict` cap hiçbiri bu Ollama build'inde çözmedi.
- **AI Engineer kararı: B — non-thinking VLM'e geç.** Bir doğrulayıcının işi sınırsız akıl
  yürütme değil, sınırlı-süreli deterministik sınıflandırma; thinking modeli yanlış araç.
- **`qwen2.5vl:3b` (non-thinking)** — co-residency kapısı: 9/9 geçerli JSON, done hepsi
  `stop`, **`offloaded 37/37 layers to GPU`** (CPU offload yok, CLIP ile sığdı).
- **Ama JSON şeması RUBBER-STAMP'liyor:** kırmızı arabaya "mavi araba? evet, conf 1.0" der.
  Düz yes/no'da ise rengi KUSURSUZ ayırır (kırmızı 9/9, mavi 0/9). Model kör değil — JSON
  çerçevesi bozuyor. → **YES/NO VQA sözleşmesi**: sorgu (nesne, renk) hedeflerine indirgenir,
  verifier iki atomik yes/no sorar; `num_predict:4` kaçağı yapısal imkânsız kılar.
- **Sonuç her eksende kazanç:** reliability %100, ayrım kusursuz (red/blue, dog), latency
  4.8s/2.3s (JSON'un 16.8s'inden 3.5× hızlı). Uçtan uca "köpek gezdiren insan"→hedef `dog`,
  4 yanlış-pozitif elendi, 1 köpekli kaldı.
- **Kod:** `query.extract_vqa_targets` (yeni), `verifier.py` yes/no'ya yeniden yazıldı,
  `search.verify_top_n` yeni imza, `config` model+timeout(40→20). q8_0 env var registry'den
  silindi. Detay: `experiments/2026-07-05_vlm_latency/deney_notu.md` · ARCHITECTURE.md §8

## 5 Temmuz 2026 (öğle) — Per-item streaming: VLM rozetleri canlı doluyor

- `search.py` bölündü: `verify_top_n` (callback'li, her verdict'te `on_verdict(i,hit)`) +
  `_fuse_verdicts` (füzyon) + public `stream_verify`. `_apply_vlm`=ikisi (CLI batch).
- **Viewer per-item streaming:** CLIP kartları ⏳ ile gelir; her VLM verdict'i o kartın
  rozetini CANLI doldurur (⏳→✅ renk doğru/✅ conf/🚫), sonra final reflow. Cache VLM
  tarafında `@cache_data` yerine `session_state` (streaming canlı render gerektiriyor).
- **TARAYICIYLA GÖRSEL DOĞRULANDI** (Chrome): "siyah SUV araç" → kart 1 "✅ renk doğru"
  belirdi, kartlar 2-4 ⏳; sonra kart 1,3,4 "✅ renk doğru", kart 2 çözüldü. Rozetler tek
  tek canlı doldu. Ayrıca "köpek gezdiren adam" → CLIP insanlar → BULUNAMADI + "VLM
  elenenler (5)" expander (önceki batch doğrulamasında).
- Güvenilirlik: yavaş çağrı (spike) akışı kısa durdurabilir → `vlm_timeout_s=30` (21s
  spike absorbe, hang 30s'de kapanır, kart rozetsiz akış devam). Detay: ARCHITECTURE.md §8b

## 5 Temmuz 2026 — Async VLM rafine: progressive render (interaktif latency çözüldü)

- AI Engineer: gerçek thread değil **progressive render** (tek-kullanıcı demo). VLM latency
  ~4-6s/görüntü — bottleneck token DEĞİL görüntü prefill'i (num_predict:48 denendi, latency
  düşmedi + JSON'u kesti → geri alındı; out_size 384/256/224 fark etmiyor, VLM içeride resize).
- `search()` bölündü: `search(use_vlm=False)` (CLIP hızlı) + public `refine_vlm(outcome)`.
  `SearchOutcome`'a `vlm_applied` + `vlm_filtered` (elenenler expander için).
- **Viewer yeniden yazıldı:** `st.form` submit (keystroke rerun yok), `@st.cache_data`
  (Oynat tıklaması VLM'i yeniden koşmasın — kritik), CLIP `st.empty` slot'a anında →
  `st.status` altında VLM → aynı slot yerinde değişir, elenenler expander'da.
- **Prompt sıkılaştırıldı** ("açıklamanın HER parçası görünmeli"): köpek/yağmur → BULUNAMADI
  (önce 1 kısmi-eşleşme survivor kalıyordu), siyah SUV öznitelik bozulmadan (color_match 0.7-1.0).
- Doğrulandı: tüm modüller derleniyor, Streamlit HTTP 200 başlıyor, SearchOutcome pickle'lanıyor
  (cache güvenli). CLI senkron kalır. Paralel VLM yok (Ollama tek model, OOM). Detay: ARCHITECTURE.md §8b

## 4 Temmuz 2026 (gece) — Faz 2 VLM doğrulayıcı: negasyon çözüldü, retrieve-then-verify

- AI Engineer tasarımı: `qwen3-vl:2b` (Ollama, 1.9GB — CLIP ile eşzamanlı sığan tek
  sağlam seçenek), koşullu (yalnız renk/zor-kavram sorgusu), tam-çözünürlükte doğrula.
- **Kurulan hat:** Ollama v0.31.1 kuruldu (winget) + qwen3-vl:2b (100% GPU, keep_alive
  30dk). Modüller: `recrop.py` (orijinalden bbox yüksek-res kırpma — 36px thumb yetersiz),
  `query.translate_visual` (TR→EN, VLM'in Türkçesine güvenme), `verifier.py` (yapılandırılmış
  JSON verdict), `search._apply_vlm` (negasyon=filtre / öznitelik=rerank).
- **Doğrulandı (net görüntüde VLM güçlü):** beyaz araba renk=True conf=1.0, aynı arabaya
  "siyah"→renk=False; telefonlu sürücü davranış conf=1.0; köpek→False.
- **Uçtan uca:** "köpek gezdiren adam" → **BULUNAMADI** (VLM tüm adayları reddetti — CLIP+kapının
  çözemediği negatif örtüşme çözüldü). "otobüs"→VLM tetiklemez (0s, vergi yok).
- **Yol boyu düzeltilen hata:** VLM reddedince conf=0.0 (P(present)) → filtre iki moda ayrıldı:
  negasyon (düşük-conf düşür, hepsi düşerse bulunamadı) / öznitelik (renk rerank, drop yok).
- Latency ~4-6s/görüntü → koşullu tetik. LLM sorgu-ayrıştırıcı ERTELENDİ (VRAM). Detay: ARCHITECTURE.md §8
- **Ölçüldü + gözle doğrulandı:** negasyon güçlü (köpek→BULUNAMADI, yağmur 0/6); **renk — VLM
  CLIP'in hatalarını düzeltiyor** ("mavi kamyonet"te CLIP 4 aday, VLM 1 gerçek maviyi onayladı,
  3 sahteyi reddetti; 3 renk de gözle doğru — tam-res recrop mavi-korkusunu yendi). Pozitif
  kontrol otobüs 5/5, kamyon 4/4. Dürüst sınır: kar 2/6 false-accept (açık zemin→"kar").
- **Güvenilirlik düzeltildi:** ilk marathon %24 hata (CLIP+VLM 8GB spike) → timeout 20→45s +
  retry → tek-sorgu (prod) 0/8. Detay: `experiments/2026-07-04_faz2_vlm/`.

## 4 Temmuz 2026 (gece) — Olgu B çözüldü: sahne-niyetli frame boost (durum-eki tabanlı)

- AI Engineer tasarımı: niyet sinyali **durum ekiyle** (case morphology), pozisyonla değil —
  -DA/-lA/-In ekli isim adjunct, head = son nominatif isim. "araçlarLA...otopark"→sahne,
  "otoparkTA...insan"→nesne. `query.scene_or_object_intent`. Sınıflandırıcı 12/12 dev.
- Mekanizma: **z-normalize yumuşak frame-boost, yalnız sahne-niyetinde** (`_intent_rerank`,
  λ=1.0). Nesne-niyeti nötr (Faz 1.5 korunur). Hard filtre değil — cross-video relevans ezilmez.
- λ skor-boşluğundan kalibre, dev'de seçilip kilitli sette doğrulandı (dev/kilitli ayrı).
- **Ölçüldü:** dev kırpık-seli düzeliyor (kamyonlu_otopark sahne-kare sırası 10→4, garaj 6→3;
  3 iyileşme, 0 regresyon). **v1 kilitli SIFIR regresyon** (R@5=1.0 sabit), nesne+noobj
  kontroller regres etmiyor.
- **Dürüst nüans:** v2_gold_meva_otopark düzelmedi (8→6) çünkü Olgu B'nin ikinci bileşeni
  kare-açlığı (meva_okul2 statik lot=1 kare) + VIRAT_otopark meşru daha iyi cevap. Boost
  cross-video relevansı doğru şekilde EZMİYOR; kare-açlığı ayrı iş. `experiments/2026-07-04_olgu_b_frame_boost/`

**Sıradaki adım:** statik lotlara daha uzun MEVA segmenti (kare-açlığı) ya da Faz 2 VLM.

## 4 Temmuz 2026 (gece) — Statik lot zenginleştirme: kare-açlığı giderildi (Olgu B kapandı)

- meva_okul2 + meva_otobus MEVA'dan 60→180 sn yeniden çekildi: her biri **1→3 kare**.
- **Ölçüldü:** meva_okul2 "araçlarla dolu açık otopark" sahne-kare sırası **8→5**
  (zenginleşme + boost); kırpık-seli tamamen elendi (v2 Faz 1.5 marjini −0.333→0.000).
  v1 kilitli sıfır regresyon.
- **Nüans (Olgu A tekrarı):** v2 pinpoint golden (frame_idx=0) "rank 9" diyor ama SAHNE
  top-5'te — çapa karesi (60/120sn) rank 5'i alıyor. Ders: statik sahne için pinpoint
  golden yanlış, video+kare metriği doğru. Kalan (VIRAT üstte) = meşru doğru sıralama.
- Detay: `experiments/2026-07-04_lot_zenginlestirme/`

**Sıradaki adım:** Faz 2 VLM re-rank (negatif örtüşme + öznitelik + Olgu A kümeleme).

## 4 Temmuz 2026 (akşam) — Korpus büyütüldü (MEVA): eval artık ayrımcı, 2 gerçek olgu çıktı

- AI Engineer kaynak seçti: **MEVA KF1** (VIRAT halefi, S3 public, HTTP Range destekli —
  Kitware'in no-Range sorununu çözdü). ffmpeg ile URL'den ilk 60 sn çekilip normalize edildi.
- **6 farklı sabit kamera eklendi** (hastane/okul/otobüs/idari açık alan + iç mekan):
  korpus 7→**13 video**, 4080→**4391 vektör**, +54 yeni sahnede insan kırpığı. Statik lotlar
  1 kare verdi (hareket kapısı doğru; park araçları kırpık olarak yakalandı).
- **v1 (kilitli 22 sorgu) çeldiricilere rağmen SAĞLAM:** R@1=0.917, R@5=1.0 DEĞİŞMEDİ.
  MEVA kırpık düzeyinde rekabet ediyor ama doğru cevap kazanıyor → R@5=1.0 artık güvenilir,
  şişme "sahte" değilmiş, embedding gerçekten ayırıyor. (`experiments/2026-07-04_eval_meva/`)
- **v2 (pre-registered, eklemeli) 2 gerçek olgu ifşa etti** (R@1=0.333 — artık zor):
  - **Olgu A:** 8sn kümeleme spesifik golden'ı yutuyor ama DOĞRU video zirvede (retrieval
    hatası değil; `fail_attribution`=dedup/kümeleme doğru işaretledi — golden etiketim spesifikti).
  - **Olgu B (gerçek zaaf):** "araçlarla dolu otopark" sahne sorgusu, araç kırpıklarının seli
    altında rank 8'e gömülüyor. Faz 1.5 marjini v2'de −0.333 (kare > birleşik). Skor-ofsetsiz
    birleşik indeksin sınırı. (`experiments/2026-07-04_eval_v2/`)
- Detay: `experiments/2026-07-04_korpus_buyutme/deney_notu.md`

**Sıradaki adım:** Olgu B — sahne-niyetli sorgularda kareyi kırpığa tercih (niyet tespiti);
AI Engineer danışması gerekir. Gece/trafik için UA-DETRAC (Kaggle token gerekiyor).

## 4 Temmuz 2026 (öğleden sonra) — Bulunamadı kapısı: "bisiklet yok" artık boş dönüyor

- Eval'in en kritik açığı (güvenilir "bulunamadı" sinyali yok) hedefli çözüldü.
  Skor eşiği yerine **YOLO envanteri**: sorgu tespit edilebilir bir sınıf istiyorsa
  ve korpusta o sınıf hiç yoksa → CLIP'e sormadan boş dön.
- `query.extract_object_intent` (Türkçe eş anlamlı + ASCII-fold, çekim ekine dayanıklı),
  `store.available_object_classes` (önbellekli envanter), `search` kapısı (yalnız prod
  hattı; ablation atlar), cli/viewer "BULUNAMADI" mesajı.
- **Ölçüldü (aynı dondurulmuş set, eşleştirilmiş):** pozitif metrikler DEĞİŞMEDİ
  (R@1=0.917, R@5=1.0 — yanlış kapı = 0), negatif yakalama 0.25 (`neg_bisiklet` boş).
- Dürüst sınır: kapı yalnız "tespit edilebilir sınıf yok"u çözer; köpek (YOLO sınıfı
  değil) + yağmur/kar (öznitelik) geçti → kalan örtüşme -0.078 Faz 2 VLM'e kalır.
- Uçtan uca: `search "kırmızı bisiklet süren çocuk"` → "Korpusta 'bisiklet' tespit
  edilmedi". Detay: `experiments/2026-07-04_bulunamadi_kapisi/`

**Sıradaki adım:** Faz 2 VLM re-rank (öznitelik/hava/eylem doğrulaması) ya da tespit
sınıflarını genişletme (köpek/kedi → kapı kapsamı büyür).

## 4 Temmuz 2026 — Eval seti kuruldu (Risk 3 kapandı) + Faz 1.5'in değeri ölçüldü

- AI Engineer eval tasarımını inceledi, naif "video-düzeyi recall"i 3 yerde kırdı:
  golden-frame ubik/davranış için birincil; renk GT'si otomatik doğrulanamaz →
  advisory; kare vs kırpık ayrı koşulmalı. Buna göre 22 sorgu, tiered `queries.yaml`
  **dondurularak** kuruldu (golden frame_idx'ler küçük resim GÖZLE doğrulandı).
- `store.search`/`search`'e `source` filtresi eklendi (frame/crop ablation için).
  `eval/run_eval.py`: 3 yönlü koşu, Wilson CI, golden fail_attribution, Gap 1 denetimi.
- **Kanıt — Faz 1.5'in değeri artık bir sayı:** R@5 yalnız-kare 0.667 → birleşik
  **1.0** = **+0.333 marjinal katkı** (yalnız-kırpık 0.917). Kırpık nesne sorgularını
  taşıyor. Golden R@1=1.0 (3 gözle-doğrulanmış kare de rank-1).
- **Boşluk 1 çözüldü:** "gece" embed edildi (→ucf_gece rank-1), "dün gece" parse
  edildi, "son 3 saat" filtresiz geri düştü. Sınır davranışı doğru.
- **KRİTİK DÜRÜST SINIR:** negatif ayrımcılık çöktü — min-pozitif 0.282 < max-negatif
  0.36 ("köpek gezdiren **adam**" → insan'a eşleşti). **Güvenilir "bulunamadı" sinyali
  yok.** Faz 2 VLM doğrulayıcının somut gerekçesi. Kısa vade: yolo_class sertlik kapısı.
- Dürüst çerçeve: video-düzeyi R@5=1.0 şişmiş (4 sahne görsel olarak çok farklı);
  gerçek zorluk golden pinpoint + negatif ayrımda. n=12 → CI [0.757, 1.0], gösterge.
- Detay: `experiments/2026-07-04_eval/deney_notu.md`

**Sıradaki adım:** "Bulunamadı" mekanizması (yolo_class sertlik kapısı / VLM) — en
yüksek öncelikli açık. Ardından korpus büyütme (benzer sahnelerle gerçek ayrım ölçümü).

## 3 Temmuz 2026 (gece) — Faz 1.5 tamamlandı: YOLO kırpık embedding sulanmayı çözdü

- AI Engineer tasarım danışması → yolo11m@1280, düşük güven eşiği, %20 pay + kare
  kırpma, statik IoU bastırma, tek koleksiyon `source: frame|crop`.
- `detector.py` yazıldı; store/search/cli/viewer kırpık desteği aldı; arama tarafına
  kare tekilleştirme + 8 sn zaman kümeleme eklendi.
- 2 hata bulunup çözüldü: (1) CPU-only torchvision → cu126'dan yeniden kuruldu;
  (2) kırpık sınırı güven sıralamasıyla insanları kesiyordu (VIRAT'ta 0 insan kırpığı)
  → sınır statik bastırma sonrası + insan öncelikli yapıldı → 132 insan kırpığı.
- **Önce/sonra:** "uzakta tek başına yürüyen insan" Faz 1'de yanlış videoya kayıptı
  (0.228 vs 0.155); şimdi ilk 3 sonucun 3'ü de doğru insan kırpığı (0.363) — kırpık
  küçük resimleriyle görsel doğrulandı. İndeks: 647 kare + 3.323 kırpık.
- Dürüst sınır: VIRAT kampüs segmentinde insan kırpığı yok — ham YOLO bile bulamıyor
  (<10 px); boru hattı değil veri sınırı. Gerekirse SAHI döşeme (Faz 2 eval kararı).
- Detay: `experiments/2026-07-03_faz15_yolo_crop/deney_notu.md`

**Sıradaki adım:** Eval seti (30–50 Türkçe sorgu → doğru kare) — korpus ve hat hazır.

## 3 Temmuz 2026 (akşam) — Gerçek CCTV testi: örnekleyici yeniden tasarlandı, Risk 1 kesinleşti

- AI Engineer link-doğrulamalı gerçek CCTV verisi seçti: VIRAT otopark + kampüs
  (araştırma lisanslı), UCF trafik + gece. `data/cctv_test/` altına indirildi.
- **Kritik hata bulundu:** VIRAT kampüs 22 sn'den 1 kare verdi. Teşhis: pHash dedup
  global hash olduğu için 3 piksellik insana yapısal kör (Hamming=0); hareket kapısı
  eşikleri de küçük özne için 3-7 kat yüksekti.
- **Örnekleyici yeniden tasarlandı** (AI Engineer inceleme + onay): ortalama-normalize
  absdiff, bağlı bileşen gürültü filtresi, birikimli değişim dedup (pHash emekli),
  küresel olay koruması, OSD maskesi, saatlik oran sınırı. Detay: ARCHITECTURE.md §2.
- Sonuç: kampüs 1→31, otopark 3→59 kare. Yürüyen insanlı kareler artık indekste.
- 11 Türkçe sorgu testi + görsel doğrulama: "mavi kamyonet" birebir isabet; gece ve
  trafik sorguları doğru; ama küçük özne sorgularında **Risk 1 kesinleşti** — video içi
  sıralama doğru, videolar arası 0.02–0.07 puanlık sulanma yakın plan videoya yeniriyor.
- **Karar: Faz 1.5 (YOLO-crop embedding) öne çekildi — sıradaki iş.**
- Detaylar: `experiments/2026-07-03_gercek_cctv_testi/deney_notu.md`

## 3 Temmuz 2026 — Faz 1 MVP kodu tamamlandı

- Ortam kuruldu: `.venv` + CUDA torch (torch 2.12.1+cu126, `cuda: True` — RTX 4070 Laptop).
- **Tüm 8 modül gerçek koda çevrildi** (iskelet kalmadı):
  - `config.py` — tüm eşikler tek yerde; yollar proje köküne sabitlendi (çalışma dizininden bağımsız).
  - `sampler.py` — PyAV çözme, 2 fps aday, hareket kapısı, 60 sn çapa karesi, pHash dedup.
  - `embedder.py` — jina-clip-v2, GPU fp16, toplu görüntü/metin encode, L2-normalize.
  - `thumbs.py` — 480 px JPEG q=80 küçük resim yazıcı.
  - `store.py` — Qdrant lokal mod, `frames` koleksiyonu, deterministik nokta ID (yeniden indeksleme idempotent), zaman/kamera filtreli arama.
  - `query.py` — Türkçe zamansal ayrıştırıcı: "dün gece", "bu sabah", "son N saat", "dün saat 22 civarı" kalıpları + dolgu kelime temizliği. Zaman kelimeleri asla embedlenmez.
  - `search.py` — arama hattı: ayrıştır → embedle → filtreli ara; zaman filtresi boş dönerse filtresiz tekrar + kullanıcıya uyarı.
  - `cli.py` — typer: `index`, `search`, `stats`, `ui` komutları.
  - `viewer.py` — Streamlit: sorgu kutusu → 4 sütun küçük resim ızgarası → "Oynat" ile videoyu o saniyeden izleme.
- Sorgu ayrıştırıcı 6 örnek sorguyla test edildi — zaman aralıkları ve görsel metin ayrımı doğru.
- Payload şemasına `video_path` ve `offset_s` eklendi (viewer'ın videoyu doğru saniyeden açabilmesi için) — ARCHITECTURE.md tablosu güncellendi.
- Öngörülen risk gerçekleşti ve çözüldü: jina-clip-v2 uzak kodu transformers 5.12 ile uyumsuz (`clip_loss` import hatası) → `transformers<4.50` sabitlendi.
- **İlk indeksleme başarılı:** 3 Teknofest test videosu (kapalı otopark, siyah Togg SUV), 37 kare, GPU'da 10.3 sn.
- **Türkçe arama uçtan uca doğrulandı** (6 sorgu, detay: `experiments/2026-07-03_faz1_ilk_indeksleme/deney_notu.md`):
  - "telefonla konuşan sürücü" → ilk 3 sonuç doğru video, kare görsel olarak doğrulandı (sürücü telefonda). **Çeviri olmadan davranış düzeyinde eşleşme.**
  - "dün gece otoparka giren siyah araç" → zaman filtresi ayrıştı, aralıkta veri yokunca uyarıyla filtresiz geri düşüş çalıştı.
  - Skorlar genel sorgularda dar bantta (0.35–0.39) — tek mekân/tek araç verisinde beklenen; sıralama doğru.

**Sıradaki adım:** 30–50 sorguluk eval seti (Risk 3); küçük özneli gerçek dış mekân CCTV kaydıyla Risk 1 (tam-kare embedding sulanması) testi.

## 2 Temmuz 2026 — Proje başlangıcı

- Proje kararı verildi: CCTV arşivinde Türkçe doğal dil arama (Conntour muadili, Türkiye'de rakipsiz). LoL AI Koç projesiyle paralel yürüyecek.
- Repo kuruldu: `PycharmProjects/gozcu`, GitHub'a bağlandı.
- Temel dokümantasyon yazıldı: README, AGENTS.md, ARCHITECTURE.md.
- AI Engineer agentiyle mimari kararlar netleştirildi (embedding modeli, kare örnekleme stratejisi, Qdrant şeması, Türkçe sorgu hattı) — detaylar `ARCHITECTURE.md`.
- Paket iskeleti oluşturuldu.

**Sıradaki adım:** Faz 1 MVP — kare örnekleme modülünün implementasyonu ve Teknofest test videolarıyla ilk indeksleme denemesi.
