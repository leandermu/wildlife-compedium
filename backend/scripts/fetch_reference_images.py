"""Lädt je Art ein Referenzbild von Wikipedia/Wikimedia Commons.

Die Bilder landen unverändert in  images/original/<slug>.jpg,
die Herkunft samt Lizenz und Urheber in  images/credits.json.

Das ist bewusst ein getrennter Schritt: einmal online holen, danach beliebig oft
offline weiterverarbeiten (siehe process_reference_images.py).

    python scripts/fetch_reference_images.py            # nur fehlende
    python scripts/fetch_reference_images.py --force    # alle neu
    python scripts/fetch_reference_images.py --only eisvogel,uhu
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.data import __file__ as _data_init  # noqa: E402
from app.text import slugify  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent
IMAGES = ROOT / "images"
ORIGINALS = IMAGES / "original"
CREDITS_FILE = IMAGES / "credits.json"
SEED = Path(_data_init).parent / "seed_species.json" if False else (
    Path(__file__).resolve().parent.parent / "app" / "data" / "seed_species.json"
)

# Wikimedia verlangt einen aussagekräftigen User-Agent mit Kontaktmöglichkeit.
UA = "WildlifeCompedium/0.2 (https://github.com/leandermu/wildlife-compedium)"
THUMB_WIDTH = 1400
PAUSE = 0.12  # freundlich bleiben


def api(host: str, params: dict) -> dict:
    url = f"https://{host}/w/api.php?" + urllib.parse.urlencode(
        {**params, "format": "json"}
    )
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8"))


def strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def page_image(host: str, title: str) -> tuple[str, str, str] | None:
    """(Bild-URL, Dateiname auf Commons, Artikeltitel) oder None."""
    data = api(host, {
        "action": "query", "titles": title, "redirects": "1",
        "prop": "pageimages", "piprop": f"thumbnail|name", "pithumbsize": THUMB_WIDTH,
    })
    pages = data.get("query", {}).get("pages", {})
    for pid, page in pages.items():
        if pid == "-1" or "thumbnail" not in page:
            continue
        source = page["thumbnail"]["source"].split("?")[0]
        return source, page.get("pageimage", ""), page.get("title", title)
    return None


def search_title(host: str, term: str) -> str | None:
    data = api(host, {
        "action": "query", "list": "search", "srsearch": term,
        "srlimit": 1, "srnamespace": 0,
    })
    hits = data.get("query", {}).get("search", [])
    return hits[0]["title"] if hits else None


def license_info(filename: str) -> dict:
    if not filename:
        return {}
    try:
        data = api("commons.wikimedia.org", {
            "action": "query", "titles": f"File:{filename}",
            "prop": "imageinfo", "iiprop": "extmetadata|url",
            "iiextmetadatafilter": "Artist|LicenseShortName|LicenseUrl|Credit",
        })
    except Exception:
        return {}
    for page in data.get("query", {}).get("pages", {}).values():
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        get = lambda k: strip_html(meta.get(k, {}).get("value", ""))  # noqa: E731
        return {
            "author": get("Artist"),
            "license": get("LicenseShortName"),
            "license_url": meta.get("LicenseUrl", {}).get("value", ""),
            "file": filename,
            "file_page": info.get("descriptionurl", ""),
        }
    return {}


def resolve(common: str, scientific: str) -> tuple[str, str, str, str] | None:
    """Sucht der Reihe nach: de-Artikel, de-Suche, en-Artikel per Fachname."""
    attempts = [
        ("de.wikipedia.org", common),
        ("de.wikipedia.org", scientific),
        ("en.wikipedia.org", scientific),
        ("en.wikipedia.org", common),
    ]
    for host, title in attempts:
        if not title:
            continue
        try:
            hit = page_image(host, title)
        except Exception:
            hit = None
        if hit:
            return hit[0], hit[1], hit[2], host
        time.sleep(PAUSE)
    # letzter Versuch: Volltextsuche
    for host, term in (("de.wikipedia.org", scientific), ("de.wikipedia.org", common)):
        if not term:
            continue
        try:
            found = search_title(host, term)
            if found and (hit := page_image(host, found)):
                return hit[0], hit[1], hit[2], host
        except Exception:
            pass
        time.sleep(PAUSE)
    return None


def download(url: str, dest: Path) -> int:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return len(data)



# --------------------------------------------------------------------------
# Nachbesserung für zu kleine Vorlagen.
#
# Gesucht wird ausschließlich in den Bildern, die im Artikel der Art selbst
# eingebunden sind – eine Commons-Volltextsuche liefert sonst Eier, Schädel und
# Präparate, die im Compedium nichts verloren haben. Zusätzlich filtert eine
# Sperrliste genau solche Motive aus.
# --------------------------------------------------------------------------
MIN_WIDTH = 1000

BLOCKED_WORDS = {
    "ei", "eier", "egg", "eggs", "gelege", "nest", "nestling",
    "schaedel", "schädel", "skull", "skelett", "skeleton", "knochen", "bones",
    "museum", "specimen", "praeparat", "präparat", "taxidermy", "mounted",
    "stuffed", "dead", "roadkill", "fossil", "coin", "muenze", "münze",
    "briefmarke", "stamp", "logo", "icon", "wappen",
    "verbreitung", "verbreitungskarte", "distribution", "range", "map", "karte",
    "illustration", "zeichnung", "drawing", "plate", "tafel", "diagram",
    "spur", "spuren", "track", "tracks", "footprint", "kot", "scat",
    "larve", "larva", "raupe", "caterpillar", "puppe", "pupa", "cocoon",
    "feder", "federn", "feather", "vergleich", "comparison", "sonagramm",
    # Sammlungskürzel: fast immer Präparate, Bälge oder Eiersammlungen
    "mwnh", "mhnt", "mnhn", "nhmw", "rmnh", "iucn", "naturkundemuseum",
    "nisthilfe", "nistkasten", "zoo", "gehege", "captive",
}
GOOD_SUFFIXES = (".jpg", ".jpeg", ".png")

# Marker, die auch ohne Trennzeichen im Dateinamen stecken können
# ("SylviaAtricapillaIUCNver2018.png" ist eine Verbreitungskarte, kein Vogel).
BLOCKED_FRAGMENTS = (
    "iucn", "mwnh", "mhnt", "mnhn", "nhmw", "rmnh",
    "verbreitung", "distribution", "rangemap", "mapof",
    "skelett", "skeleton", "schaedel", "skull", "museum",
)


def _tokens(filename: str) -> set[str]:
    return set(re.split(r"[^a-zA-ZäöüßÄÖÜ]+", filename.lower())) - {""}


def article_images(host: str, article: str, scientific: str, common: str) -> list[dict]:
    """Große Bilder aus dem Artikel der Art, Störmotive herausgefiltert."""
    try:
        listing = api(host, {
            "action": "query", "titles": article, "redirects": "1",
            "prop": "images", "imlimit": 60,
        })
    except Exception:
        return []
    # de.wikipedia liefert "Datei:…", Commons kennt nur "File:…"
    titles = [
        "File:" + img["title"].split(":", 1)[-1]
        for page in listing.get("query", {}).get("pages", {}).values()
        for img in page.get("images", [])
        if img["title"].lower().endswith(GOOD_SUFFIXES)
    ]
    if not titles:
        return []

    genus = (scientific or "").split(" ")[0].lower()
    needles = {n for n in (genus, (scientific or "").lower(), common.lower()) if len(n) > 3}

    out: list[dict] = []
    for chunk in (titles[i:i + 20] for i in range(0, len(titles), 20)):
        try:
            data = api("commons.wikimedia.org", {
                "action": "query", "titles": "|".join(chunk),
                "prop": "imageinfo", "iiprop": "url|size|extmetadata",
                "iiurlwidth": THUMB_WIDTH,
                "iiextmetadatafilter": "Artist|LicenseShortName|LicenseUrl",
            })
        except Exception:
            continue
        for page in data.get("query", {}).get("pages", {}).values():
            name = page.get("title", "").removeprefix("File:")
            flat = re.sub(r"[^a-z]", "", name.lower())
            if _tokens(name) & BLOCKED_WORDS or any(f in flat for f in BLOCKED_FRAGMENTS):
                continue
            haystack = name.lower().replace("_", " ")
            if needles and not any(n in haystack for n in needles):
                continue
            info = (page.get("imageinfo") or [{}])[0]
            if info.get("width", 0) < MIN_WIDTH:
                continue
            meta = info.get("extmetadata", {})
            out.append({
                "name": name,
                "width": info["width"],
                "url": info.get("thumburl") or info.get("url", ""),
                "author": strip_html(meta.get("Artist", {}).get("value", "")),
                "license": strip_html(meta.get("LicenseShortName", {}).get("value", "")),
                "license_url": meta.get("LicenseUrl", {}).get("value", ""),
                "file_page": info.get("descriptionurl", ""),
            })
        time.sleep(PAUSE)
    out.sort(key=lambda c: -c["width"])
    return out


def upgrade_small(
    rows: list[dict], credits: dict, min_width: int, only: set[str] | None = None
) -> int:
    """Ersetzt Vorlagen unter `min_width` Pixeln durch ein größeres Bild aus
    demselben Artikel – falls es eines gibt."""
    from PIL import Image

    upgraded = 0
    for row in rows:
        slug = row.get("slug") or slugify(row["common_name"])
        if only and slug not in only:
            continue
        dest = ORIGINALS / f"{slug}.jpg"
        entry = credits.get(slug, {})
        if not dest.exists() or not entry.get("article"):
            continue
        try:
            with Image.open(dest) as im:
                width = im.width
        except Exception:
            continue
        if width >= min_width:
            continue

        host = "de.wikipedia.org" if "de.wikipedia" in entry.get("article_url", "") else "en.wikipedia.org"
        candidates = article_images(
            host, entry["article"], row.get("scientific_name", ""), row["common_name"]
        )
        for cand in candidates[:2]:
            if cand["name"] == entry.get("file"):
                continue
            try:
                download(cand["url"], dest)
                with Image.open(dest) as im:
                    new_width = im.width
            except Exception:
                continue
            if new_width <= width:
                continue
            credits[slug] = {
                **entry,
                "source_url": cand["url"], "author": cand["author"],
                "license": cand["license"], "license_url": cand["license_url"],
                "file": cand["name"], "file_page": cand["file_page"],
            }
            print(f"  ↑ {row['common_name']:<26} {width} → {new_width} px  ({cand['name'][:44]})")
            upgraded += 1
            break
        time.sleep(PAUSE)
    return upgraded


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="auch vorhandene neu laden")
    ap.add_argument("--only", default="", help="Kommaliste von Slugs")
    ap.add_argument("--upgrade-small", type=int, default=0, metavar="PX",
                    help="vorhandene Vorlagen unter PX Pixeln durch bessere ersetzen")
    args = ap.parse_args()

    rows = json.loads(SEED.read_text(encoding="utf-8"))
    only = {s.strip() for s in args.only.split(",") if s.strip()}
    credits = json.loads(CREDITS_FILE.read_text("utf-8")) if CREDITS_FILE.exists() else {}

    ORIGINALS.mkdir(parents=True, exist_ok=True)

    if args.upgrade_small:
        n = upgrade_small(rows, credits, args.upgrade_small, only)
        CREDITS_FILE.write_text(json.dumps(credits, ensure_ascii=False, indent=1), "utf-8")
        print(f"\n{n} Vorlagen ersetzt")
        return 0

    ok = skipped = failed = 0
    missing: list[str] = []

    for i, row in enumerate(rows, 1):
        slug = row.get("slug") or slugify(row["common_name"])
        if only and slug not in only:
            continue
        dest = ORIGINALS / f"{slug}.jpg"
        if dest.exists() and not args.force:
            skipped += 1
            continue

        found = resolve(row["common_name"], row.get("scientific_name", ""))
        if not found:
            failed += 1
            missing.append(f"{row['common_name']} ({row.get('scientific_name','')})")
            print(f"[{i:3}/{len(rows)}] ✗ {row['common_name']}")
            continue

        url, filename, article, host = found
        try:
            size = download(url, dest)
        except Exception as exc:
            failed += 1
            missing.append(f"{row['common_name']} – Download: {exc}")
            print(f"[{i:3}/{len(rows)}] ✗ {row['common_name']} (Download)")
            continue

        credits[slug] = {
            "common_name": row["common_name"],
            "article": article,
            "article_url": f"https://{host}/wiki/{urllib.parse.quote(article.replace(' ', '_'))}",
            "source_url": url,
            **license_info(filename),
        }
        ok += 1
        print(f"[{i:3}/{len(rows)}] ✓ {row['common_name']:<28} {size // 1024:>4} KB  ({article})")
        time.sleep(PAUSE)

    CREDITS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CREDITS_FILE.write_text(json.dumps(credits, ensure_ascii=False, indent=1), "utf-8")

    print(f"\n{ok} geladen, {skipped} übersprungen, {failed} ohne Bild")
    if missing:
        print("Ohne Bild:")
        for m in missing:
            print("  -", m)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
