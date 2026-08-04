# Lisans durumu — ticarileştirme önündeki gerçek engeller

**4 Ağustos 2026.** Bu dosya Vel'Koz'un bağımlılıklarının lisans durumunu ve ticari
kullanıma etkisini kayda geçirir. **Destek/fon başvurusundan önce okunması gereken dosya budur.**

> **Özet:** Test verisinin araştırma lisanslı olması bilinen bir kısıttı. Ama daha büyük bir
> engel var: **üç çekirdek modelin üçü de ticari kullanıma kapalı veya bulaşıcı lisanslı.**
> Bu, prototip için sorun değil; **ürünleştirme için yol haritasına girmesi gereken bir madde.**

---

## Çekirdek bileşenler

| Bileşen | Rol | Lisans | Ticari kullanım |
|---|---|---|---|
| **`jinaai/jina-clip-v2`** | Görsel-metin embedding — sistemin kalbi | **CC-BY-NC-4.0** | ❌ **Yasak** |
| **`qwen2.5vl:3b`** | VLM doğrulayıcı | **Qwen Research** (non-commercial) | ❌ **Yasak** |
| **`ultralytics` YOLO11** | Nesne tespiti | **AGPL-3.0** | ⚠️ Dağıtım kaynak açmayı tetikler |
| Qdrant (client, lokal mod) | Vektör veritabanı | Apache-2.0 | ✅ Serbest |
| Streamlit | Arayüz | Apache-2.0 | ✅ Serbest |
| PyTorch, transformers, PyAV | Altyapı | BSD / Apache-2.0 | ✅ Serbest |
| Ollama | VLM çalıştırıcı | MIT | ✅ Serbest (gömülebilir) |

### Dikkat — üçüncü taraf lisans etiketlerine güvenilmez

Ollama'nın model kayıt sayfası `qwen2.5vl:3b` için **Apache-2.0** gösteriyor. Bu **yanlıştır**.
Bağlayıcı olan yukarı-akış deposudur (`Qwen/Qwen2.5-VL-3B-Instruct` → qwen-research lisansı).
Qwen2.5-VL ailesinde **yalnızca 7B** Apache-2.0'dır; 3B ve 72B araştırma lisanslıdır.

---

## Bu bugün ne anlama geliyor

**Prototip, ölçüm, akademik yayın, TÜBİTAK 2209-A, TEKNOFEST — hepsi sorunsuz.**
Araştırma ve eğitim kullanımı bu lisansların tamamı tarafından açıkça izinlidir.

**Sorun yalnızca şu noktada başlar:** ürünü bir müşteriye satmak veya ticari bir hizmet
olarak sunmak. O aşamada üç maddenin de çözülmesi gerekir.

---

## Ölçülmüş deneme: VLM'i Apache-2.0 bir modelle değiştirmek

`qwen3-vl:2b` (Apache-2.0, makinede kurulu, 1.9 GB) denendi — tek satırlık değişiklik,
yan fayda olarak paket 1,3 GB küçülecekti.

**Sonuç: reddedildi.** Ölçüm kaybı gösterdi:

| kova | qwen2.5vl:3b | qwen3-vl:2b |
|---|---|---|
| negation | 3/3 | 3/3 |
| positive_ctrl | 3/3 | 3/3 |
| **attribute (renk)** | **3/4** | **1/4** |
| hard_negative | 2/2 | 2/2 |
| **Genel** | **11/12 (%92)** | **9/12 (%75)** |

Renk sorgularının üçü birden kırıldı (`siyah SUV`, `beyaz araba`, `kırmızı araba`).
qwen3-vl:2b renk sorularına aşırı "hayır" eğilimli. `mavi kamyonet`'in "düzelmesi" bile
gerçek bir kazanç değil — aynı aşırı-negatifliğin yan etkisi.

**Ders:** lisans uyumu için model değiştirmek ücretsiz değildir. Ölçmeden yapılmamalı.
Bu deneme tek satırlık "bedava kazanç" diye önerilmişti; ölçüm kayıp gösterdi.

---

## Ürünleştirme yolu — üç madde, üç seçenek

### 1. Embedding modeli (en kritik — `jina-clip-v2` CC-BY-NC)

| Seçenek | Artı | Eksi |
|---|---|---|
| **Jina AI'dan ticari lisans** | Kod değişmez, ölçümler geçerli kalır | Ücret; fiyat sorulmalı |
| **SigLIP2** (Apache-2.0) ile değiştir | Tamamen serbest | **Tüm indeks yeniden üretilir**, tüm ölçümler tekrarlanır, Türkçe performansı yeniden doğrulanmalı |
| **LAION XLM-R CLIP** (MIT) | Serbest, çok dilli | Aynı yeniden-üretim maliyeti |

**Öneri:** demo/başvuru aşamasında **değiştirme**. Model değişimi C1 baseline'ını ve tüm
karşılaştırmaları geçersiz kılar. İlk ticari müşteri görüşmesinde Jina'ya fiyat sor;
paralelde SigLIP2'yi ayrı bir dalda ölçerek karşılaştır.

### 2. VLM doğrulayıcı (`qwen2.5vl:3b` research)

- **qwen2.5vl:7b** Apache-2.0'dır — ölçülmeye değer. 8 GB kartta CLIP ile eşzamanlı
  sığıp sığmayacağı test edilmeli (q4 ≈ 4,5 GB + CLIP 2 GB).
- qwen3-vl:2b denendi ve **reddedildi** (yukarıdaki ölçüm).

### 3. YOLO (`ultralytics` AGPL-3.0)

| Seçenek | Not |
|---|---|
| **Repoyu AGPL-3.0 yayınla** | En ucuz ve en dürüst yol. Jüri/hakem karşısında "açık kaynak" yük değil avantajdır. Ticari SaaS'ta müşteriye kaynak sunma yükümlülüğü doğar. |
| Ultralytics ticari lisans | Ücretli, kapalı kaynak dağıtıma izin verir |
| AGPL olmayan dedektöre geç | Örn. RT-DETR (Apache-2.0) — yeniden ölçüm gerektirir |

**Öneri:** şimdilik **AGPL-3.0** ile yayınla; repoda `LICENSE` dosyası yok, eklenmeli.

---

## Test verisi lisansı (ayrı ve zaten çözülmüş konu)

| Korpus | Lisans | Durum |
|---|---|---|
| Ölçüm (MEVA, VIRAT, UCF) | Araştırma lisanslı | Yeniden dağıtılamaz — `data/` git'e girmez |
| Demo (NGSIM, Wikimedia) | CC BY-SA 4.0 | Paylaşılabilir — künye: `docs/DEMO_KORPUS_LISANS.md` |

---

## Yapılacaklar

- [ ] Repoya `LICENSE` dosyası ekle (öneri: AGPL-3.0)
- [ ] `qwen2.5vl:7b` ölçümü — 8 GB kartta CLIP ile sığıyor mu, 11/12 korunuyor mu
- [ ] İlk ticari görüşme öncesi Jina AI'dan `jina-clip-v2` ticari lisans fiyatı sor
- [ ] SigLIP2'yi ayrı dalda ölç (C1 baseline'ına dokunmadan)
- [ ] `onnxruntime` bağımlılığını kaldır — kodda hiç import edilmiyor (42 MB ölü ağırlık)

**Başvuru metinlerinde bu durum gizlenmemeli.** "Prototip araştırma lisanslı modellerle
kurulu; ürünleştirmede lisans geçişi planlandı ve maliyeti ölçüldü" demek, sorulunca
yakalanmaktan çok daha güçlü bir konumdur.
