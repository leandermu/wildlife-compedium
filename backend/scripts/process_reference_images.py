"""Macht aus den Wikipedia-Downloads Referenzplatten im Stil des Compediums.

Die Platten sind absichtlich entsättigt und leicht ins Papier zurückgenommen:
Sie zeigen, *was* zu finden ist, sehen aber sichtbar unfertig aus – das eigene
Foto in Farbe ist die Belohnung.

    images/original/<slug>.jpg
        → data/media/reference/<slug>.jpg        (1000 px, Detailseite)
        → data/media/reference-thumb/<slug>.jpg  ( 480 px, Karten)
    + Eintrag in der Datenbank (reference_image, reference_thumb, credit, source)

Rein offline, beliebig oft wiederholbar:

    python scripts/process_reference_images.py
    python scripts/process_reference_images.py --only eisvogel --preview
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.db import SessionLocal, init_db  # noqa: E402
from app.models import Species  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent
ORIGINALS = ROOT / "images" / "original"
CREDITS_FILE = ROOT / "images" / "credits.json"

PLATE_WIDTH = 1000
THUMB_WIDTH = 480
ASPECT = 4 / 3

# Tinte und Papier aus dem Frontend-Farbschema (index.css)
INK = (36, 42, 33)
PAPER = (243, 237, 223)
PAPER_MIX = 0.16   # so viel Papier wird über das Bild gelegt
CONTRAST = 1.08


def duotone_ramp(dark: tuple[int, int, int], light: tuple[int, int, int]) -> list[int]:
    """256-Werte-Palette von Tinte nach Papier, für Image.point auf L-Bildern."""
    ramp: list[int] = []
    for channel in range(3):
        for i in range(256):
            t = i / 255
            # leichte S-Kurve: Lichter bleiben luftig, Tiefen laufen nicht zu
            t = t * t * (3 - 2 * t) * 0.82 + t * 0.18
            ramp.append(round(dark[channel] + (light[channel] - dark[channel]) * t))
    return ramp


RAMP = duotone_ramp(INK, PAPER)


def crop_to_aspect(img: Image.Image, aspect: float) -> Image.Image:
    w, h = img.size
    if w / h > aspect:          # zu breit → seitlich beschneiden
        new_w = int(h * aspect)
        left = (w - new_w) // 2
        return img.crop((left, 0, left + new_w, h))
    new_h = int(w / aspect)     # zu hoch → oben/unten beschneiden, leicht nach oben
    top = int((h - new_h) * 0.4)
    return img.crop((0, top, w, top + new_h))


def make_plate(path: Path) -> Image.Image:
    with Image.open(path) as raw:
        img = ImageOps.exif_transpose(raw).convert("RGB")
        img = crop_to_aspect(img, ASPECT)
        # niemals hochrechnen – kleine Vorlagen bleiben lieber klein als matschig
        width = min(PLATE_WIDTH, img.width)
        img = img.resize((width, round(width / ASPECT)), Image.LANCZOS)

        gray = ImageOps.autocontrast(img.convert("L"), cutoff=(1, 2))
        gray = ImageEnhance.Contrast(gray).enhance(CONTRAST)

        # Graustufen in die Papier/Tinte-Palette übersetzen
        plate = gray.convert("RGB").point(RAMP)

        # ein Hauch Papier darüber: nimmt die letzte Härte raus
        veil = Image.new("RGB", plate.size, PAPER)
        return Image.blend(plate, veil, PAPER_MIX)


def save_jpeg(img: Image.Image, dest: Path, width: int, quality: int) -> int:
    target = min(width, img.width)
    out = (
        img.resize((target, round(target / ASPECT)), Image.LANCZOS)
        if img.width != target
        else img
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.save(dest, "JPEG", quality=quality, optimize=True, progressive=True)
    return dest.stat().st_size


def credit_line(entry: dict) -> str:
    author = (entry.get("author") or "").strip()
    lic = (entry.get("license") or "").strip()
    parts = [p for p in (author, lic) if p]
    return " · ".join(parts) if parts else "Wikimedia Commons"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="Kommaliste von Slugs")
    ap.add_argument("--preview", action="store_true", help="Platte zusätzlich nach images/preview/")
    ap.add_argument("--missing", action="store_true", help="Nur fehlende Platten erzeugen")
    args = ap.parse_args()
    only = {s.strip() for s in args.only.split(",") if s.strip()}

    credits = json.loads(CREDITS_FILE.read_text("utf-8")) if CREDITS_FILE.exists() else {}
    media = settings.local_media_path

    init_db()
    done = missing = 0
    total_bytes = 0
    with SessionLocal() as db:
        species = {s.slug: s for s in db.query(Species).all()}
        for slug, sp in sorted(species.items()):
            if only and slug not in only:
                continue
            source = ORIGINALS / f"{slug}.jpg"
            if not source.exists():
                missing += 1
                continue

            plate_dest = media / "reference" / f"{slug}.jpg"
            thumb_dest = media / "reference-thumb" / f"{slug}.jpg"
            if (
                args.missing
                and plate_dest.exists()
                and thumb_dest.exists()
                and sp.reference_image == f"reference/{slug}.jpg"
                and sp.reference_thumb == f"reference-thumb/{slug}.jpg"
            ):
                continue

            plate = make_plate(source)
            total_bytes += save_jpeg(plate, plate_dest, PLATE_WIDTH, 82)
            total_bytes += save_jpeg(plate, thumb_dest, THUMB_WIDTH, 78)
            if args.preview:
                save_jpeg(plate, ROOT / "images" / "preview" / f"{slug}.jpg", PLATE_WIDTH, 88)

            entry = credits.get(slug, {})
            sp.reference_image = f"reference/{slug}.jpg"
            sp.reference_thumb = f"reference-thumb/{slug}.jpg"
            sp.reference_credit = credit_line(entry)
            sp.reference_source = entry.get("file_page") or entry.get("article_url") or None
            done += 1
        db.commit()

    print(f"{done} Platten erzeugt ({total_bytes / 1024 / 1024:.1f} MB), {missing} ohne Vorlage")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
