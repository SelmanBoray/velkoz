# Korpus v2 — MEVA-S3 zenginleştirme provenance (21 Temmuz 2026)

Task #4 korpus zenginleştirme. Kaynak: **MEVA KF1**, S3 public bucket `mevadata-public-01`
(HTTP Range destekli). Lisans: araştırma amaçlı, **redistribute YASAK** → videolar `data/`
altında lokal, git'e ASLA girmez (`.gitignore`: `data/`, `*.mp4`). Türetilmiş indeks (embedding/
thumbnail) de lokal. Çekim: `ffmpeg -t <sn> -i <s3-url> -c:v libx264 -an out.mp4`.

## Aday havuzu ve kararlar

Aday seçimi: `drop-4-hadcv22` prefix'inden mevcut 6 MEVA kamerasından FARKLI, gündüz (10-15h)
kameralar. Her aday projenin KENDİ dedektörüyle tarandı (`scan.py`) — **eval-kırıcı koşul objektif
test edildi:** YOLO `bisiklet` görürse REJECT (çünkü `available_object_classes`'a bisiklet
eklenmesi `neg_bisiklet` envanter kapısını açar → dondurulmuş test kırılır).

| video_id | S3 anahtarı (drop-4-hadcv22/...) | dedektör bulgusu | karar |
|---|---|---|---|
| meva_okul_G330 | 2018-03-10/10/...school.G330.r13.avi | zirve 55 / 8033 yaya, 0 araç, 0 bisiklet | ✅ EKLE (30s'e kısaltıldı — crop taşkını) |
| meva_okul_G339 | 2018-03-10/12/...school.G339.r13.avi | 1154 araba, 126 kamyon, 24 motosiklet, 0 bisiklet | ✅ EKLE (araç-renk; kamyonlar bordo/siyah/turuncu, MAVİ YOK) |
| meva_hastane_G341 | 2018-03-15/10/...hospital.G341.r13.avi | zirve 6 / 494 yaya, 180 araba, 0 bisiklet | ✅ EKLE (dış-mekan ulaşım, insan+araç) |
| meva_otobus_G505 | 2018-03-15/10/...bus.G505.r13.avi | 3 yaya, 260 araba, 5 kamyon, 0 bisiklet | ✅ EKLE (dış-mekan yaya; kamyon rengi → negation dedektif backstop) |
| meva_okul_G421 | 2018-03-08/11/...school.G421.r13.avi | 22 yaya AMA **bisiklet 180** | ❌ RED (bisiklet → neg_bisiklet kırardı) |
| meva_okul_G638 | 2018-03-10/10/...school.G638.r13.avi | 0 yaya, **bisiklet 180** | ❌ RED (bisiklet; gözle de doğrulandı) |
| meva_okul_G300 | 2018-03-10/12/...school.G300.r13.avi | 0 yaya, 180 araba | ⬜ ATLA (fazlalık park, değer düşük) |
| meva_okul_G328 | 2018-03-10/12/...school.G328.r13.avi | 1 yaya, 1719 araba | ⬜ ATLA (fazlalık park) |

## Nihai set: 4 klip (13 → 17 video)
- **Renk-insan hedefi:** G330 (kapalı basketbol, turuncu/mavi formalar — `hn_siyah_kiyafet`
  vacuous testini canlıya çevirme potansiyeli) + G341/G505 (dış-mekan yayalar, denge).
- **Araç-renk hedefi:** G339 (gümüş/bordo/siyah/turuncu, mavi kamyon YOK).
- **Gözle doğrulandı:** hiçbir klipte köpek/yağmur/kar/mavi-kamyonet yok (G330/G341/G339/G505 kareleri
  incelendi). Bisiklet iki klipte yakalandı ve elendi.

## İki katmanlı savunma (AI Engineer)
1. **Önleyici (eyeball-gate):** dedektör bisiklet taraması + gözle 5-yasaklı kontrolü → yapıldı.
2. **Dedektif (post-index):** 4 negation + adv_mavi_kamyonet hâlâ not_found dönmeli. Biri
   has_results'a dönerse yasaklı kavram sızmış → o klip çıkarılır (özellikle G505 kamyon rengi backstop).
