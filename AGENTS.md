# AGENTS.md — Vel'Koz Projesi Çalışma Kuralları

Bu dosya, projede çalışan tüm AI agentlerin uyması gereken kuralları tanımlar.

## Proje özeti

Vel'Koz: güvenlik kamerası arşivinde Türkçe doğal dil arama motoru. Lokal-first (KVKK — görüntü müşteri binasından çıkmaz), ucuz donanım hedefi (orta seviye GPU + CPU fallback). Detay: `README.md` ve `ARCHITECTURE.md`.

## Çalışma kuralları

1. **Dokümantasyon otomatik güncellenir:** Her teknik adımdan/işlemden sonra sormadan `AGENTS.md` (kural değiştiyse) ve `PROGRESS.md` (her zaman) güncellenir.
2. **Teknik kararlar tek başına verilmez:** Mimari/model/kütüphane seçimi gibi teknik kararlarda AI Engineer agenti çağrılır.
3. **Kod yorumları konu başlıkları şeklinde yazılır:** Kod blokları `# ── Bölüm adı ──` tarzı başlık yorumlarıyla ayrılır; satır satır açıklama değil, bölüm başlığı mantığı.
4. **Gerekli pip paketleri sorulmadan kurulur.**
5. **Test disiplini:** Her anlamlı değişiklikte eldeki tüm test videolarıyla test edilir; çıktılar `experiments/` altında sınıflandırılmış klasörlere kaydedilir (`experiments/<tarih>_<konu>/`).
6. **Kalite > hız:** Örnekleme/FPS optimizasyonları tespit kalitesini bozamaz.
7. **Dil:** Dokümantasyon ve kullanıcıya dönük metinler Türkçe; kod tanımlayıcıları (değişken/fonksiyon adları) İngilizce.

## Dizin yapısı

```
gozcu/          → Python paketi (pipeline modülleri)
eval/           → dondurulmuş sorgu seti (queries.yaml) + koşucu (run_eval.py)
data/           → test videoları + indeks (git'e girmez)
experiments/    → test çıktıları (deney notları git'e girer, görüntü girmez)
ARCHITECTURE.md → mimari kararlar ve gerekçeleri
PROGRESS.md     → proje günlüğü
```

## İki korpus, iki indeks — KARIŞTIRMA

| Korpus | İçerik | İndeks yolu | Paylaşılabilir |
|---|---|---|---|
| **Ölçüm** | MEVA · VIRAT · UCF (17 video, 6231 vektör) | `data/qdrant_storage` | ❌ araştırma lisanslı |
| **Demo** | Açık lisanslı (3 klip, 1874 vektör) | `data/qdrant_demo` | ✅ CC BY-SA 4.0 |

Ölçüm korpusu **yeniden dağıtılamaz** — o kliplerle çekilmiş demo videosu/ekran kaydı
paylaşmak lisans ihlalidir. Demo korpusu bu yüzden var ve **ayrı indekste yaşar**.

Ayrı indeks olmasının ikinci nedeni ölçüm bütünlüğü: demo klipleri ölçüm korpusuna
karıştırılsaydı dondurulmuş sorgu setinin GT'si yine eskir ve her demo klibi için yeniden
havuzlama gerekirdi. Ayrı indeks bu bağı tamamen keser.

Demo indeksiyle çalışmak için env override:
`QDRANT_PATH=.../data/qdrant_demo THUMBS_DIR=.../data/thumbnails_demo`

Yeni demo klibi eklerken: dedektörle **bisiklet kapısı** + gözle 5-yasaklı kontrolü + lisans
doğrulaması ZORUNLU; kabul/ret gerekçeleri `docs/DEMO_KORPUS_LISANS.md`'ye yazılır.

## Kurulum denetimi

`python -m gozcu doctor` — Python, torch+CUDA, torchvision, transformers kilidi, YOLO
ağırlığı, jina-clip-v2 önbelleği, Qdrant indeksi ve Ollama/VLM'i tek tek denetler; arıza
varsa **düzeltme komutunu** yazar. Kritik sorunda exit 1 döner (CI'da kullanılabilir).

**En sinsi arıza sessiz olanı:** PyPI'ın varsayılan `torch` wheel'i Windows'ta CPU-only
gelir; `device: "auto"` sessizce cpu'ya düşer, proje çalışır ama ~20x yavaşlar ve hiç hata
vermez. Bu yüzden torch **önce CUDA indeksinden** kurulur (`requirements.txt` başlığı).
Ortam sorunu bildiren herkesten önce `doctor` çıktısı istenir.

## Eval disiplini

Retrieval kalitesi `eval/queries.yaml` (dondurulmuş, pre-registration) üzerinden
`eval/run_eval.py` ile ölçülür. Metodoloji: ARCHITECTURE.md §6b. Kurallar: sorgu
seti sonuca bakmadan dondurulur; golden frame_idx'ler küçük resim gözle doğrulanır;
her model/eşik değişikliği bu sabit sette eşleştirilmiş (McNemar) karşılaştırılır.

**Faz 2 objektif skor:** uçtan uca VLM pipeline'ı `eval/faz2_eval.py` + `queries_faz2.yaml`
ile ölçülür (loop'un his yerine güvendiği metrik). İki ortogonal eksen: **outcome**
(not_found/has_results) ve **ayrım** (`forbid: vehicles` → yasaklı YOLO sınıfı sonuçlara
sızarsa FAIL; kişi-renk sorgusunun araç getirmesini kilitler). `forbid` sembolik tutulur —
depodaki `yolo_class` **Türkçe**, İngilizce liste yazma (sahte-PASS). Güncel skor **11/12**;
detay ARCHITECTURE.md §6c. Çalıştırma: `.venv/Scripts/python.exe eval/faz2_eval.py` (Ollama gerekir).

**Korpus büyütürken GT havuzlama ZORUNLU.** Korpusa video eklemek eski `relevant_videos`
listelerini eksik bırakır → sahte regresyon okunur (4 Ağu 2026'da yaşandı: R@5 0.917→0.833
görüldü, sebep model değil GT'ydi). Protokol: eski sorgu seti **dondurulmuş kalır**, yeni
sürüm ayrı dosyaya yazılır (`queries_c2.yaml`), genişletme kararı **arama sonucuna değil
videonun içeriğine** bakılarak verilir (sınıf envanteri + küçük resim gözle), kanıtı zayıf
genişletme **reddedilir ve gerekçesi yazılır**, iki sürümün sonucu **yan yana** raporlanır.
`golden_frame` alanlarına asla dokunulmaz — metriği kurtarmak için GT oynatmak p-hacking'dir.
