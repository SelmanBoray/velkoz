"""Komut satırı arayüzü.

Kullanım:
    python -m gozcu index C:/videolar/
    python -m gozcu search "dün gece giren beyaz Transit"
    python -m gozcu stats
    python -m gozcu ui
"""

import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import typer

from gozcu.config import settings

# ── Windows konsolunda Türkçe karakter güvencesi ──
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

app = typer.Typer(help="Vel'Koz — kamera arşivinde Türkçe doğal dil arama", no_args_is_help=True)

VIDEO_EXTS = {".mp4", ".avi", ".mkv", ".mov", ".ts", ".dav"}


@app.command()
def index(
    folder: Path,
    camera_id: str = typer.Option(None, help="Kamera kimliği (boşsa video adı kullanılır)"),
) -> None:
    """Klasördeki tüm videoları örnekle, embedle ve indeksle."""
    # ── Ağır importlar komut içinde: 'search --help' model yüklemesin ──
    from gozcu.detector import Detection, Detector, cap_crops, crop_image, suppress_static
    from gozcu.embedder import Embedder
    from gozcu.sampler import FrameRecord, sample_video, video_start_ts
    from gozcu.store import FrameStore
    from gozcu.thumbs import write_crop_thumb, write_thumb

    videos = sorted(p for p in folder.iterdir() if p.suffix.lower() in VIDEO_EXTS)
    if not videos:
        typer.echo(f"HATA: {folder} içinde video bulunamadı ({', '.join(sorted(VIDEO_EXTS))})")
        raise typer.Exit(1)

    typer.echo(f"Cihaz seçiliyor, modeller yükleniyor ({settings.model_id} + {settings.yolo_model})...")
    embedder = Embedder(device=settings.device)
    detector = Detector(device=settings.device)
    store = FrameStore()
    typer.echo(f"Modeller hazır (cihaz: {embedder.device}). {len(videos)} video indekslenecek.\n")

    total_kept = 0
    total_crops = 0
    grand_start = time.perf_counter()

    for video in videos:
        # ── Video başına: örnekle → embedle → tespit et → kırpıkları embedle → upsert ──
        cam = camera_id or video.stem
        base_ts = video_start_ts(video)
        video_start = time.perf_counter()
        kept = 0
        crops = 0
        batch: list[FrameRecord] = []
        prev_dets: list[Detection] = []  # statik nesne bastırma referansı

        def flush(batch: list[FrameRecord]) -> None:
            nonlocal prev_dets, crops
            # ── Kare vektörleri ──
            vectors = embedder.encode_images([r.image for r in batch])
            thumbs = [str(write_thumb(r.image, r.video_id, r.frame_idx)) for r in batch]
            store.upsert(batch, vectors, thumbs)

            # ── YOLO kırpıkları: tespit → statik bastırma → kırp → embedle ──
            items, crop_imgs, parent_thumbs = [], [], []
            for record, fthumb in zip(batch, thumbs):
                detections = detector.detect(record.image)
                fresh = cap_crops(suppress_static(detections, prev_dets))
                prev_dets = detections  # referans HAM tespitler — statik nesne hep bastırılır
                for k, det in enumerate(fresh):
                    img = crop_image(record.image, det)
                    if img.size == 0:
                        continue
                    items.append((record, det, k))
                    crop_imgs.append(img)
                    parent_thumbs.append(fthumb)
            if items:
                crop_vecs = embedder.encode_images(crop_imgs)
                crop_thumbs = [
                    str(write_crop_thumb(img, rec.video_id, rec.frame_idx, k))
                    for img, (rec, _, k) in zip(crop_imgs, items)
                ]
                store.upsert_crops(items, crop_vecs, parent_thumbs, crop_thumbs)
                crops += len(items)

        for record in sample_video(video, cam, base_ts):
            batch.append(record)
            kept += 1
            if len(batch) >= embedder.batch_size:
                flush(batch)
                batch = []
        if batch:
            flush(batch)

        elapsed = time.perf_counter() - video_start
        total_kept += kept
        total_crops += crops
        start_str = datetime.fromtimestamp(base_ts).strftime("%d.%m.%Y %H:%M:%S")
        typer.echo(
            f"  {video.name}: {kept} kare + {crops} kırpık indekslendi ({elapsed:.1f} sn) "
            f"— tahmini başlangıç: {start_str}"
        )

    grand_elapsed = time.perf_counter() - grand_start
    typer.echo(
        f"\nBitti: {total_kept} kare + {total_crops} kırpık, toplam süre {grand_elapsed:.1f} sn. "
        f"İndeksteki toplam vektör: {store.count()}"
    )


@app.command()
def search(
    query: str,
    top_k: int = typer.Option(settings.default_top_k, help="Kaç sonuç gösterilsin"),
) -> None:
    """Türkçe sorguyla indekste ara, sonuçları tabloda göster."""
    from gozcu.search import search as run_search

    outcome = run_search(query, top_k=top_k)
    parsed = outcome.parsed

    # ── Ayrıştırma özeti: ne embedlendi, hangi zaman aralığı filtrelendi ──
    typer.echo(f'Görsel sorgu : "{parsed.visual_text or query}"')
    if parsed.ts_from is not None:
        fmt = "%d.%m.%Y %H:%M"
        span = (
            f"{datetime.fromtimestamp(parsed.ts_from):{fmt}} — "
            f"{datetime.fromtimestamp(parsed.ts_to):{fmt}}"
        )
        typer.echo(f'Zaman filtresi: "{parsed.time_phrase}" → {span}')
    if outcome.time_filter_dropped:
        typer.echo("UYARI: Zaman aralığında sonuç yok — filtre kaldırılıp tüm arşivde arandı.")
    typer.echo("")

    # ── Bulunamadı kapısı: sorgulanan nesne sınıfı korpusta yok ──
    if outcome.not_found_reason:
        typer.echo(f"BULUNAMADI: {outcome.not_found_reason}")
        raise typer.Exit(0)

    if not outcome.results:
        typer.echo("Sonuç bulunamadı. Önce `python -m gozcu index <klasör>` çalıştırıldı mı?")
        raise typer.Exit(1)

    # ── Sonuç tablosu ──
    typer.echo(f"{'#':>2}  {'skor':>6}  {'tür':<12} {'video':<14} {'zaman':<19} {'offset':>8}")
    for i, hit in enumerate(outcome.results, 1):
        when = datetime.fromtimestamp(hit["ts"]).strftime("%d.%m.%Y %H:%M:%S")
        offset = f"{int(hit['offset_s'] // 60):02d}:{hit['offset_s'] % 60:04.1f}"
        kind = f"🎯 {hit['yolo_class']}" if hit.get("source") == "crop" else "kare"
        typer.echo(
            f"{i:>2}  {hit['score']:>6.3f}  {kind:<12} {hit['video_id']:<14} {when:<19} "
            f"{offset:>8}"
        )


@app.command()
def stats() -> None:
    """İndeks istatistiklerini göster."""
    from gozcu.store import FrameStore

    store = FrameStore()
    typer.echo(f"İndeksteki toplam kare: {store.count()}")
    typer.echo(f"Qdrant yolu           : {settings.qdrant_path}")
    typer.echo(f"Küçük resim klasörü   : {settings.thumbs_dir}")


@app.command()
def doctor() -> None:
    """Kurulumu denetle: her bileşen hazır mı, değilse düzeltme komutu nedir.

    Amaç: "bende çalışmıyor" sorusunu tahminden çıkarıp tek komuta indirmek. En sinsi
    arıza sessiz olanı — CPU-only torch kurulursa proje ÇALIŞIR ama ~20x yavaşlar ve
    hiçbir hata mesajı çıkmaz. Bu komut onu açıkça söyler.
    """
    # ── Bulgular burada birikir: (ad, durum, detay, düzeltme) ──
    rows: list[tuple[str, str, str, str]] = []
    OK, WARN, FAIL = "✅", "⚠️ ", "❌"

    def add(name: str, state: str, detail: str, fix: str = "") -> None:
        rows.append((name, state, detail, fix))

    # ── 1. Python sürümü ──
    v = sys.version_info
    add("Python", OK if v >= (3, 10) else FAIL, f"{v.major}.{v.minor}.{v.micro}",
        "" if v >= (3, 10) else "Python 3.12 önerilir")

    # ── 2. torch + CUDA — en kritik kontrol (sessiz CPU-only tuzağı) ──
    cuda_ok = False
    try:
        import torch

        cuda_ok = torch.cuda.is_available()
        if cuda_ok:
            gpu = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
            add("torch (CUDA)", OK, f"{torch.__version__} · {gpu} · {vram:.1f} GB")
        elif "+cu" in torch.__version__:
            add("torch (CUDA)", WARN, f"{torch.__version__} — CUDA derlemesi var ama GPU görünmüyor",
                "NVIDIA sürücüsünü güncelle; GPU yoksa CPU'da çalışır (yavaş)")
        else:
            add("torch (CUDA)", FAIL, f"{torch.__version__} — CPU-ONLY wheel kurulmuş",
                "pip install --force-reinstall torch torchvision "
                "--index-url https://download.pytorch.org/whl/cu126")
    except ImportError:
        add("torch (CUDA)", FAIL, "kurulu değil", "pip install -r requirements.txt")

    # ── 3. torchvision aynı CUDA indeksinden mi (YOLO NMS GPU'da mı) ──
    try:
        import torchvision

        tv_cuda = "+cu" in torchvision.__version__
        add("torchvision", OK if (tv_cuda or not cuda_ok) else FAIL,
            torchvision.__version__ + ("" if tv_cuda else " — CPU-only, YOLO NMS GPU'da çalışmaz"),
            "" if (tv_cuda or not cuda_ok) else
            "pip install --force-reinstall torchvision "
            "--index-url https://download.pytorch.org/whl/cu126")
    except ImportError:
        add("torchvision", FAIL, "kurulu değil", "pip install -r requirements.txt")

    # ── 4. transformers sürüm kilidi (jina-clip-v2 uzak kodu <4.50 ister) ──
    try:
        import transformers

        major, minor = (int(x) for x in transformers.__version__.split(".")[:2])
        locked = (major, minor) < (4, 50)
        add("transformers", OK if locked else FAIL,
            transformers.__version__ + ("" if locked else " — jina-clip-v2 uzak kodu kırılır"),
            "" if locked else 'pip install "transformers<4.50"')
    except ImportError:
        add("transformers", FAIL, "kurulu değil", "pip install -r requirements.txt")

    # ── 5. YOLO ağırlığı (git'te YOK — ilk çalıştırmada indirilir) ──
    weight = Path(settings.yolo_model)
    if not weight.is_absolute():
        weight = Path(__file__).resolve().parent.parent / settings.yolo_model
    add("YOLO ağırlığı", OK if weight.exists() else WARN,
        f"{settings.yolo_model} — {'var' if weight.exists() else 'yok'}"
        + (f" ({weight.stat().st_size / 1024**2:.0f} MB)" if weight.exists() else ""),
        "" if weight.exists() else "İlk indekslemede otomatik indirilir (~40 MB, internet gerekir)")

    # ── 6. jina-clip-v2 önbelleği (~1.7 GB; ilk çalıştırma uzun sürer) ──
    hub = Path.home() / ".cache" / "huggingface" / "hub"
    cached = list(hub.glob("models--jinaai--jina-clip-v2")) if hub.exists() else []
    add("jina-clip-v2", OK if cached else WARN,
        "önbellekte" if cached else "indirilmemiş",
        "" if cached else "İlk çalıştırmada ~1.7 GB indirilir (internet gerekir)")

    # ── 7. Qdrant indeksi — dolu mu, kaç vektör ──
    try:
        from gozcu.store import FrameStore

        n = FrameStore().count()
        add("Qdrant indeksi", OK if n else WARN, f"{n} vektör",
            "" if n else "python -m gozcu index <video_klasörü>")
    except Exception as exc:  # depo bozuk/kilitli — kurulum sorunu olarak raporla
        add("Qdrant indeksi", FAIL, f"açılamadı: {type(exc).__name__}",
            f"{settings.qdrant_path} kilitli olabilir — diğer süreçleri kapat")

    # ── 7b. Çevrimdışı kilit — ürünün "veri dışarı çıkmaz" sözünün teknik güvencesi ──
    offline = os.environ.get("HF_HUB_OFFLINE")
    add("Çevrimdışı kilit", OK if offline == "1" else WARN,
        "etkin — model önbellekten yüklenir, ağa çıkılmaz" if offline == "1"
        else "kapalı — model önbelleği eksik, ilk yükleme ağ gerektirir",
        "" if offline == "1" else "Modeller bir kez indirilince kilit kendiliğinden etkinleşir")

    # ── 8. Ollama + VLM (opsiyonel: yoksa CLIP-only çalışır) ──
    try:
        from gozcu.search import vlm_available

        if vlm_available():
            add("Ollama + VLM", OK, settings.vlm_model)
        else:
            add("Ollama + VLM", WARN, f"{settings.vlm_model} erişilemez — VLM doğrulama devre dışı",
                f"ollama serve  +  ollama pull {settings.vlm_model}")
    except Exception as exc:
        add("Ollama + VLM", WARN, f"denetlenemedi: {type(exc).__name__}",
            f"ollama serve  +  ollama pull {settings.vlm_model}")

    # ── Tablo ──
    typer.echo(f"\n{'bileşen':<16} {'':<3} durum")
    typer.echo("─" * 78)
    for name, state, detail, _fix in rows:
        typer.echo(f"{name:<16} {state:<3} {detail}")

    fixes = [(n, f) for n, _s, _d, f in rows if f]
    if fixes:
        typer.echo("\nYapılacaklar:")
        for name, fix in fixes:
            typer.echo(f"  · {name}: {fix}")

    n_fail = sum(1 for _n, s, _d, _f in rows if s == FAIL)
    n_warn = sum(1 for _n, s, _d, _f in rows if s == WARN)
    typer.echo("")
    if n_fail:
        typer.echo(f"{n_fail} kritik sorun var — yukarıdaki komutları çalıştır.")
        raise typer.Exit(1)
    if n_warn:
        typer.echo(f"Kurulum çalışır durumda ({n_warn} uyarı — opsiyonel bileşen eksik).")
    else:
        typer.echo("Her şey hazır.")


@app.command()
def ui() -> None:
    """Streamlit arayüzünü başlat."""
    viewer_path = Path(__file__).resolve().parent / "viewer.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(viewer_path)], check=False)


if __name__ == "__main__":
    app()
