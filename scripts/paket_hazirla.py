"""Taşınabilir Windows paketi hazırlayıcı.

Çıktı: çift tıklanabilir bir klasör (ve istenirse ZIP). Hedef makinede Python kurulumu,
pip, internet veya yönetici hakkı GEREKMEZ — klasör açılır, `basla.bat` çalıştırılır.

NEDEN PyInstaller/Inno DEĞİL (4 Ağu 2026 kararı):
  PyInstaller denendi; arama yolu çalıştı ama `ultralytics` import'u kırıldı (matplotlib
  hidden-import) — yani tespit hattı hiç doğrulanmadı, 6.4 GB çıktı çöpe gitti. Inno Setup
  ise 4.2 GB dosya tavanı yüzünden payload'ı bölmeyi gerektiriyor. Taşınabilir klasör aynı
  sonucu onda bir emekle veriyor ve hata ayıklaması kolay (kaynak açıkta duruyor).

KAPSAM KARARI — Ollama pakete DAHİL DEĞİL:
  Ollama MIT lisanslı, gömülebilir; ama +1.1 GB çalıştırıcı +3.2 GB model demek ve sessiz
  kurulumu bozuk (bilinen sorun). Görsel-dil doğrulaması zaten OPSİYONEL: Ollama yoksa
  sistem CLIP-only çalışır ve arayüz bunu açıkça bildirir. Kullanıcı isterse ollama.com'dan
  kurar. Bu, paketi ~4.4 GB küçültür ve kırılgan tek parçayı dışarıda bırakır.

Kullanım:
    python scripts/paket_hazirla.py --hedef D:/velkoz_paket          # klasör üret
    python scripts/paket_hazirla.py --hedef D:/velkoz_paket --zip    # ZIP de üret
    python scripts/paket_hazirla.py --dry-run                        # yalnız boyut raporu
"""

import argparse
import os
import shutil
import sys
import zipfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ── Pakete girecek kod/veri (kaynak, hedef_ad, zorunlu_mu) ──
KOD_PARCALARI = [
    ("gozcu", "gozcu", True),
    ("scripts", "scripts", False),
    ("eval", "eval", False),
    ("yolo11m.pt", "yolo11m.pt", True),
    ("requirements.txt", "requirements.txt", False),
    ("README.md", "README.md", False),
    ("ARCHITECTURE.md", "ARCHITECTURE.md", False),
    ("docs", "docs", False),
]

# ── Kopyalanmayacak çöp (venv ve önbellekte çok yer kaplar, gereksiz) ──
ATLA = shutil.ignore_patterns(
    "__pycache__", "*.pyc", "*.pyo", ".git", ".pytest_cache",
    "*.lock", ".ipynb_checkpoints",
)

BASLA_BAT = r"""@echo off
REM ── Vel'Koz taşınabilir başlatıcı ──
REM Bu dosyanın bulunduğu klasör paketin köküdür; her yol ona göre çözülür.
setlocal
set "KOK=%~dp0"
set "PYTHONIOENCODING=utf-8"
REM Veri (indeks + küçük resimler) paketin yanında kalsın — tek klasör taşınabilirlik
set "DATA_DIR=%KOK%data"
REM Model önbelleği pakete gömülü: HuggingFace'e hiç çıkılmaz
set "HF_HOME=%KOK%hf_cache"
set "HF_HUB_OFFLINE=1"

echo.
echo   Vel'Koz baslatiliyor...
echo   Tarayici acilmazsa: http://localhost:8501
echo.

"%KOK%.venv\Scripts\python.exe" -m streamlit run "%KOK%gozcu\viewer.py"
if errorlevel 1 (
  echo.
  echo   HATA: baslatilamadi. Tani icin su komutu calistirin:
  echo     "%KOK%.venv\Scripts\python.exe" -m gozcu doctor
  pause
)
endlocal
"""

DENETLE_BAT = r"""@echo off
setlocal
set "KOK=%~dp0"
set "PYTHONIOENCODING=utf-8"
set "DATA_DIR=%KOK%data"
set "HF_HOME=%KOK%hf_cache"
set "HF_HUB_OFFLINE=1"
"%KOK%.venv\Scripts\python.exe" -m gozcu doctor
pause
endlocal
"""

OKUBENI = """# Vel'Koz — taşınabilir sürüm

## Çalıştırma

1. Bu klasörü istediğin yere kopyala (Program Files gerekmez).
2. **`basla.bat`** dosyasına çift tıkla.
3. Tarayıcı açılmazsa: http://localhost:8501

Python kurulumu, internet bağlantısı veya yönetici hakkı **gerekmez**.

## Kurulumu denetleme

Bir sorun olursa **`denetle.bat`** çalıştır — her bileşeni tek tek kontrol eder ve
arıza varsa çözüm komutunu yazar.

## Kendi videolarını indeksleme

`basla.bat`'ın yanındaki komut satırından:

```
.venv\\Scripts\\python.exe -m gozcu index "C:\\kayitlar"
```

İndeks ve küçük resimler bu klasörün içindeki `data\\` altına yazılır — paketi
taşıdığında indeksin de birlikte gelir.

> **Not:** Arayüz açıkken indeksleme yapılamaz (veritabanı tek süreç tarafından
> kilitlenir). Önce arayüzü kapat.

## Görsel-dil doğrulaması (opsiyonel)

Renk ve olumsuzluk sorgularında ("kırmızı kıyafetli adam", "köpek gezdiren adam")
doğruluğu artıran doğrulama katmanı **Ollama** gerektirir ve pakete dahil değildir.

Kurulum: https://ollama.com/download → ardından `ollama pull qwen2.5vl:3b`

Ollama yoksa sistem yalnız görsel-metin eşleşmesiyle çalışır; arayüz bunu açıkça bildirir.

## Gizlilik

Hiçbir görüntü, embedding veya sorgu dışarı gönderilmez. Modeller pakete gömülü
önbellekten yüklenir, ağ bağlantısı hiç kullanılmaz (`HF_HUB_OFFLINE=1`).
"""


def _boyut(yol: Path) -> int:
    if yol.is_file():
        return yol.stat().st_size
    return sum(f.stat().st_size for f in yol.rglob("*") if f.is_file())


def _mb(n: int) -> str:
    return f"{n / 1024**3:.2f} GB" if n >= 1024**3 else f"{n / 1024**2:.0f} MB"


def _hf_kaynak() -> Path | None:
    """jina-clip-v2 önbelleğinin bulunduğu HF hub klasörü."""
    hub = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface")) / "hub"
    return hub if (hub / "models--jinaai--jina-clip-v2").exists() else None


def envanter() -> list[tuple[str, Path, int]]:
    """Pakete girecek her parçanın kaynağı ve boyutu."""
    items: list[tuple[str, Path, int]] = []
    venv = _ROOT / ".venv"
    if venv.exists():
        items.append((".venv (Python + kütüphaneler)", venv, _boyut(venv)))
    hf = _hf_kaynak()
    if hf:
        items.append(("hf_cache (jina-clip-v2)", hf, _boyut(hf)))
    for kaynak, _hedef, _zorunlu in KOD_PARCALARI:
        p = _ROOT / kaynak
        if p.exists():
            items.append((kaynak, p, _boyut(p)))
    return items


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hedef", type=Path, help="Paketin oluşturulacağı klasör")
    ap.add_argument("--zip", action="store_true", help="Klasörün yanına ZIP de üret")
    ap.add_argument("--dry-run", action="store_true", help="Kopyalama yapma, yalnız rapor")
    args = ap.parse_args()

    parcalar = envanter()
    toplam = sum(b for _a, _p, b in parcalar)

    print("\nPakete girecekler:")
    for ad, _p, b in parcalar:
        print(f"  {ad:<34} {_mb(b):>9}")
    print(f"  {'-' * 34} {'-' * 9}")
    print(f"  {'TOPLAM':<34} {_mb(toplam):>9}")
    print("\n  Ollama + görsel-dil modeli DAHİL DEĞİL (opsiyonel, ~4.3 GB — bkz. betik başlığı)")

    eksikler = [k for k, _h, zorunlu in KOD_PARCALARI if zorunlu and not (_ROOT / k).exists()]
    if not _hf_kaynak():
        eksikler.append("jina-clip-v2 önbelleği (önce bir kez çalıştırıp indir)")
    if eksikler:
        print("\nEKSİK ZORUNLU PARÇALAR:")
        for e in eksikler:
            print(f"  - {e}")
        raise SystemExit(1)

    if args.dry_run:
        print("\n(dry-run — kopyalama yapılmadı)")
        return
    if not args.hedef:
        print("\nHATA: --hedef ver ya da --dry-run kullan.")
        raise SystemExit(1)

    hedef: Path = args.hedef.resolve()
    if hedef.exists() and any(hedef.iterdir()):
        print(f"\nHATA: {hedef} boş değil. Farklı bir klasör ver.")
        raise SystemExit(1)
    hedef.mkdir(parents=True, exist_ok=True)

    # ── Kopyalama ──
    print(f"\nKopyalanıyor → {hedef}")
    venv = _ROOT / ".venv"
    if venv.exists():
        print("  .venv ...")
        shutil.copytree(venv, hedef / ".venv", ignore=ATLA, dirs_exist_ok=True)
    hf = _hf_kaynak()
    if hf:
        print("  hf_cache ...")
        shutil.copytree(hf, hedef / "hf_cache" / "hub", ignore=ATLA, dirs_exist_ok=True)
    for kaynak, hedef_ad, _zorunlu in KOD_PARCALARI:
        p = _ROOT / kaynak
        if not p.exists():
            continue
        print(f"  {kaynak} ...")
        if p.is_dir():
            shutil.copytree(p, hedef / hedef_ad, ignore=ATLA, dirs_exist_ok=True)
        else:
            shutil.copy2(p, hedef / hedef_ad)

    # ── Başlatıcılar + okubeni ──
    (hedef / "basla.bat").write_text(BASLA_BAT, encoding="utf-8")
    (hedef / "denetle.bat").write_text(DENETLE_BAT, encoding="utf-8")
    (hedef / "OKUBENI.md").write_text(OKUBENI, encoding="utf-8")
    (hedef / "data").mkdir(exist_ok=True)

    print(f"\nKlasör hazır: {hedef}  ({_mb(_boyut(hedef))})")

    if args.zip:
        zip_yolu = hedef.with_suffix(".zip")
        print(f"ZIP üretiliyor → {zip_yolu} (uzun sürer)")
        with zipfile.ZipFile(zip_yolu, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for f in hedef.rglob("*"):
                if f.is_file():
                    z.write(f, f.relative_to(hedef.parent))
        print(f"ZIP hazır: {zip_yolu}  ({_mb(zip_yolu.stat().st_size)})")

    print("\nHedef makinede: klasörü aç → basla.bat")


if __name__ == "__main__":
    main()
