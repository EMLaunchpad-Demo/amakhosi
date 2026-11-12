#!/usr/bin/env python3
"""
Maakt de verkleinde foto's van de site (SEO-plan A15, 12/11/2026).

    python beelden.py                maakt de versies die nog ontbreken
    python beelden.py --opnieuw      maakt alles opnieuw
    python beelden.py --cache=<map>  bewaart de originelen in die map

Voor elke foto in FOTOS (build.py) haalt het script het origineel uit de
mediabibliotheek (MEDIA) en maakt het in assets/foto/:
- <naam>-<breedte>.webp voor elke breedte uit foto_breedtes() (srcset);
- <naam>-<breedte>.jpg van ongeveer 1200 px breed voor og:image (delen op
  sociale media), alleen voor het hoofdbeeld van een pagina of artikel.

Daarna: python build.py. Nodig: Python 3 met Pillow (pip install Pillow).
build.py zelf heeft Pillow niet nodig: het kijkt alleen welke bestanden er in
assets/foto/ staan. De originelen komen in een tijdelijke map buiten de repo.
"""
import sys
import tempfile
import urllib.request
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageCms, ImageOps

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True  # geen __pycache__ in de repo
import build  # noqa: E402  (FOTOS, breedtes en bestandsnamen: één bron)

# Kwaliteit: visueel gelijk aan het origineel op de grootte waarop het getoond
# wordt (nagekeken op 12/11/2026 op uitvergrote stukken: houtnerf, mozaïek en
# de donkere verlopen; bij 82 werd fijne textuur al zachter).
WEBP_KWALITEIT = 85
WEBP_KWALITEIT_LOGO = 90
JPEG_KWALITEIT = 84


def origineel(f, cache):
    """Het origineel uit de mediabibliotheek (één keer downloaden)."""
    p = cache / f
    if not p.is_file():
        req = urllib.request.Request(build.MEDIA + f, headers={"User-Agent": "Mozilla/5.0 (beelden.py)"})
        with urllib.request.urlopen(req, timeout=120) as r:
            p.write_bytes(r.read())
    return p


def doelen(f):
    """(breedte, extensie) van alle versies van een foto."""
    out = [(b, "webp") for b in build.foto_breedtes(f)]
    if f in build.og_fotos():
        out.append((build.og_breedte(f), "jpg"))
    return out


def profiel(bron):
    """Het kleurprofiel van het origineel, behalve sRGB: dat is wat een browser
    zonder profiel al aanneemt (scheelt 3 KB per bestand)."""
    icc = bron.info.get("icc_profile")
    if not icc:
        return None
    try:
        naam = ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(BytesIO(icc))).strip()
    except Exception:
        return icc
    return None if naam.startswith("sRGB") else icc


def maak(f, cache, opnieuw):
    naam, w, h = build.FOTOS[f]
    todo = [(b, ext) for b, ext in doelen(f)
            if opnieuw or not (build.FOTO_DIR / build.foto_bestand(f, b, ext)).is_file()]
    if not todo:
        return []
    with Image.open(origineel(f, cache)) as bron:
        icc = profiel(bron)
        alpha = bron.mode in ("RGBA", "LA") or (bron.mode == "P" and "transparency" in bron.info)
        im = ImageOps.exif_transpose(bron).convert("RGBA" if alpha else "RGB")
    assert im.size == (w, h), f"{f} is {im.size[0]}x{im.size[1]}, in FOTOS staat {w}x{h}"
    extra = {"icc_profile": icc} if icc else {}
    gemaakt = []
    for b, ext in todo:
        maat = (b, build.foto_hoogte(f, b))
        if b == w:
            klein = im
        elif alpha:
            # Verkleinen met voorvermenigvuldigde alfa: geen donkere randjes
            klein = im.convert("RGBa").resize(maat, Image.LANCZOS).convert("RGBA")
        else:
            klein = im.resize(maat, Image.LANCZOS)
        out = build.FOTO_DIR / build.foto_bestand(f, b, ext)
        if ext == "webp":
            q = WEBP_KWALITEIT_LOGO if alpha else WEBP_KWALITEIT
            klein.save(out, "WEBP", quality=q, method=6, **extra)
        else:
            klein.convert("RGB").save(out, "JPEG", quality=JPEG_KWALITEIT, optimize=True,
                                      progressive=True, **extra)
        gemaakt.append((out.name, out.stat().st_size))
    return gemaakt


def main():
    opnieuw = "--opnieuw" in sys.argv[1:]
    cache = next((Path(a.split("=", 1)[1]) for a in sys.argv[1:] if a.startswith("--cache=")),
                 Path(tempfile.gettempdir()) / "amakhosi-originelen")
    cache.mkdir(parents=True, exist_ok=True)
    build.FOTO_DIR.mkdir(parents=True, exist_ok=True)
    totaal = 0
    for f in build.FOTOS:
        for naam, grootte in maak(f, cache, opnieuw):
            totaal += 1
            print(f"gemaakt: assets/foto/{naam} ({grootte // 1024} KB)")
    # Bestanden in assets/foto/ die bij geen enkele foto meer horen
    verwacht = {build.foto_bestand(f, b, ext) for f in build.FOTOS for b, ext in doelen(f)}
    over = sorted(p.name for p in build.FOTO_DIR.iterdir() if p.name not in verwacht)
    if over:
        print("LET OP: niet meer gebruikt in assets/foto/:", ", ".join(over))
    print(f"beelden: {totaal} gemaakt, {len(verwacht)} in totaal")


if __name__ == "__main__":
    main()
