"""Demo sonuç kartı üretici — paylaşılabilir tanıtım görselleri.

Her sorgu için tek PNG: sorgu metni + dönen sonuçların kırpıkları + skorlar.
Negatif sorgularda "BULUNAMADI" gerekçesiyle birlikte basılır — ürünün en güçlü
özelliği (halüsinasyon yerine dürüst cevap) görsel olarak kanıtlanır.

YALNIZ DEMO İNDEKSİ İLE ÇALIŞTIRILIR — ölçüm korpusu (MEVA/VIRAT/UCF) araştırma
lisanslıdır, görüntüleri paylaşılamaz. Betik bunu başlangıçta zorunlu kılar.

Kullanım:
    QDRANT_PATH=.../data/qdrant_demo THUMBS_DIR=.../data/thumbnails_demo \
    python scripts/demo_kartlari.py
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from gozcu.config import settings  # noqa: E402
from gozcu.search import search  # noqa: E402

# ── Lisans emniyet kilidi: ölçüm korpusuyla tanıtım görseli üretilemez ──
if "qdrant_demo" not in str(settings.qdrant_path):
    print("HATA: Bu betik yalnız DEMO indeksiyle çalışır.")
    print(f"  Şu anki indeks: {settings.qdrant_path}")
    print("  Ölçüm korpusu (MEVA/VIRAT/UCF) araştırma lisanslıdır, görüntüsü paylaşılamaz.")
    print("  QDRANT_PATH ortam değişkenini data/qdrant_demo olarak ayarla.")
    raise SystemExit(1)

# ── Tema ──
BG = (18, 18, 22)
KART = (30, 30, 36)
METIN = (240, 240, 245)
SOLUK = (150, 150, 160)
VURGU = (110, 190, 255)
YESIL = (90, 200, 130)
KIRMIZI = (240, 110, 110)

W = 1200
KUTU = 250          # sonuç görseli kutu kenarı
BOSLUK = 20
FONT = "C:/Windows/Fonts/arial.ttf"
FONT_B = "C:/Windows/Fonts/arialbd.ttf"


def yazi(boyut: int, kalin: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_B if kalin else FONT, boyut)


def kutuya_sigdir(yol: str, kenar: int) -> Image.Image | None:
    """Görseli oranını bozmadan kare kutuya oturt (letterbox).

    Kırpık küçük resimleri 160 px üretiliyor; `thumbnail()` yalnız küçültür, bu yüzden
    kutunun ortasında minicik kalırlardı. Oranı koruyup kutuya kadar BÜYÜTÜYORUZ —
    tanıtım görselinde özne seçilebilir olmalı.
    """
    try:
        im = Image.open(yol).convert("RGB")
    except Exception:
        return None
    olcek = min(kenar / im.width, kenar / im.height)
    yeni = (max(1, int(im.width * olcek)), max(1, int(im.height * olcek)))
    im = im.resize(yeni, Image.LANCZOS)
    tuval = Image.new("RGB", (kenar, kenar), KART)
    tuval.paste(im, ((kenar - im.width) // 2, (kenar - im.height) // 2))
    return tuval


def kart_olustur(sorgu: str, aciklama: str, cikti: Path) -> None:
    """Tek sorgu çalıştır, sonucu kart görseline dök."""
    outcome = search(sorgu, use_vlm=True)
    bulunamadi = bool(outcome.not_found_reason) or not outcome.results
    hits = outcome.results[:4]

    # ── Altbilgi için ayrı pay: sonuç etiketleri (KUTU+30) ile çakışmamalı ──
    yukseklik = 150 + (KUTU + 66 if not bulunamadi else 100) + 34
    img = Image.new("RGB", (W, yukseklik), BG)
    d = ImageDraw.Draw(img)

    # ── Başlık: sorgu ──
    d.text((BOSLUK * 2, 26), "Vel'Koz", font=yazi(20, True), fill=VURGU)
    d.text((BOSLUK * 2, 56), f'"{sorgu}"', font=yazi(34, True), fill=METIN)
    d.text((BOSLUK * 2, 104), aciklama, font=yazi(17), fill=SOLUK)

    y = 150
    if bulunamadi:
        # ── Dürüst bulunamadı: ürünün ayırt edici özelliği ──
        d.rounded_rectangle([BOSLUK * 2, y, W - BOSLUK * 2, y + 78], 10, fill=KART)
        d.text((BOSLUK * 3, y + 16), "BULUNAMADI", font=yazi(22, True), fill=KIRMIZI)
        gerekce = outcome.not_found_reason or "Sonuç yok"
        if len(gerekce) > 92:
            gerekce = gerekce[:89] + "..."
        d.text((BOSLUK * 3, y + 46), gerekce, font=yazi(16), fill=SOLUK)
    else:
        for i, h in enumerate(hits):
            x = BOSLUK * 2 + i * (KUTU + BOSLUK)
            yol = h.get("crop_thumb") or h.get("thumb")
            kutu = kutuya_sigdir(yol, KUTU) if yol else None
            if kutu:
                img.paste(kutu, (x, y))
            else:
                d.rounded_rectangle([x, y, x + KUTU, y + KUTU], 8, fill=KART)
            tur = h.get("yolo_class") or "kare"
            d.text((x, y + KUTU + 8), f"{tur}  ·  {h['score']:.3f}",
                   font=yazi(15, True), fill=VURGU)
            d.text((x, y + KUTU + 30), h["video_id"][:30], font=yazi(13), fill=SOLUK)

    # ── Altbilgi: lisans künyesi (CC BY-SA zorunluluğu) ──
    d.text((BOSLUK * 2, yukseklik - 24),
           "Görüntüler: US DOT/FHWA NGSIM · Wikimedia Commons — CC BY-SA 4.0",
           font=yazi(12), fill=(95, 95, 105))

    img.save(cikti)
    durum = "BULUNAMADI" if bulunamadi else f"{len(outcome.results)} sonuç"
    print(f"  {cikti.name:<34} {durum}")


SORGULAR = [
    ("park halindeki arabalar", "Sahne sorgusu — otopark alanını bulur", "01_park_arabalar.png"),
    ("kaldırımda yürüyen yaya", "Davranış sorgusu — küçük özneyi kırpık vektöründen bulur",
     "02_yuruyen_yaya.png"),
    ("beyaz araba", "Renk sorgusu — görsel-dil modeli rengi doğrular", "03_beyaz_araba.png"),
    ("köpek gezdiren adam", "Korpusta yok → doğrulayıcı eler, sistem uydurmaz",
     "04_negatif_kopek.png"),
    ("kırmızı bisiklet süren çocuk", "Korpusta yok → nesne envanteri kapısı devrede",
     "05_negatif_bisiklet.png"),
    ("karla kaplı sokak", "Korpusta yok → dürüst bulunamadı", "06_negatif_kar.png"),
]


def main() -> None:
    cikti_dir = _ROOT / "docs" / "demo"
    cikti_dir.mkdir(parents=True, exist_ok=True)
    print(f"Demo kartları üretiliyor → {cikti_dir}\n")
    for sorgu, aciklama, dosya in SORGULAR:
        kart_olustur(sorgu, aciklama, cikti_dir / dosya)
    print(f"\nBitti: {len(SORGULAR)} kart.")


if __name__ == "__main__":
    main()
