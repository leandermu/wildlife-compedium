"""Import a species and its reference plate from Wikipedia/Wikimedia.

The MediaWiki APIs are used instead of scraping article markup.  That keeps the
import resilient to layout changes and preserves the required image attribution.
"""

from __future__ import annotations

import html
import io
import json
import re
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError
from dataclasses import dataclass

from PIL import Image, ImageEnhance, ImageOps

from .storage import get_storage

USER_AGENT = "WildlifeCompendium/0.1 (private wildlife collection)"
THUMB_WIDTH = 1400
ASPECT = 4 / 3
INK = (36, 42, 33)
PAPER = (243, 237, 223)


@dataclass
class WikipediaSpecies:
    common_name: str
    scientific_name: str
    description: str
    group: str
    family: str
    order_name: str
    size: str
    wingspan: str
    weight: str
    difficulty: int
    rarity: str
    reference_image: str | None
    reference_thumb: str | None
    reference_credit: str | None
    reference_source: str | None


def _api(host: str, params: dict) -> dict:
    url = f"https://{host}/w/api.php?" + urllib.parse.urlencode({**params, "format": "json"})
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code != 429 or attempt == 2:
                raise
            # Respect throttling instead of immediately repeating the request.
            time.sleep(min(5, int(exc.headers.get("Retry-After", "2"))))
    raise RuntimeError("Wikipedia-Abfrage fehlgeschlagen")


def _first_page(host: str, title: str) -> tuple[dict, str] | None:
    data = _api(host, {
        "action": "query", "titles": title, "redirects": "1",
        "prop": "extracts|pageimages|pageprops|categories|links", "exintro": "1", "explaintext": "1",
        "pithumbsize": THUMB_WIDTH, "cllimit": "max", "pllimit": "max", "plnamespace": 0,
    })
    for page_id, page in data.get("query", {}).get("pages", {}).items():
        if page_id != "-1":
            return page, page.get("title", title)
    return None


def _find_page(name: str) -> tuple[dict, str, str]:
    for host in ("de.wikipedia.org", "en.wikipedia.org"):
        hit = _first_page(host, name)
        if hit:
            page, title = hit
            resolved = _resolve_disambiguation(host, page, title, name)
            return resolved[0], resolved[1], host
        search = _api(host, {
            "action": "query", "list": "search", "srsearch": name,
            "srnamespace": 0, "srlimit": 1,
        }).get("query", {}).get("search", [])
        if search and (hit := _first_page(host, search[0]["title"])):
            page, title = hit
            resolved = _resolve_disambiguation(host, page, title, name)
            return resolved[0], resolved[1], host
    raise LookupError("Zu diesem Namen wurde kein Wikipedia-Artikel gefunden.")


def _resolve_disambiguation(host: str, page: dict, title: str, requested_name: str) -> tuple[dict, str]:
    """Prefer the species article when an entered name is a disambiguation page."""
    categories = " ".join(c.get("title", "").lower() for c in page.get("categories", []))
    if "begriffsklärung" not in categories and "disambiguation" not in categories:
        return page, title
    links = [link.get("title", "") for link in page.get("links", [])]
    name = requested_name.casefold()
    candidates = sorted(
        (link for link in links if link.casefold().startswith(name)),
        key=lambda link: ("(art)" not in link.casefold() and "(species)" not in link.casefold(), len(link)),
    )
    # A name-specific species link is unambiguous here.  Do not walk every
    # link on the page: that creates needless API traffic and rate limiting.
    if candidates:
        if hit := _first_page(host, candidates[0]):
            return hit
    return page, title


_COLLAGE_MARKERS = ("collage", "montage", "mosaic", "gallery", "multiple")
_UNSUITABLE_IMAGE_MARKERS = _COLLAGE_MARKERS + (
    "map", "karte", "distribution", "range", "skeleton", "skull", "egg", "logo", "icon",
)


def _single_article_image(host: str, title: str) -> tuple[str, str] | None:
    """Find one ordinary photo from an article when its lead image is a collage."""
    listing = _api(host, {
        "action": "query", "titles": title, "redirects": "1", "prop": "images", "imlimit": 30,
    })
    files = [
        image.get("title", "").split(":", 1)[-1]
        for page in listing.get("query", {}).get("pages", {}).values()
        for image in page.get("images", [])
        if image.get("title", "").lower().endswith((".jpg", ".jpeg", ".png"))
        and not any(marker in image.get("title", "").lower() for marker in _UNSUITABLE_IMAGE_MARKERS)
    ]
    if not files:
        return None
    data = _api("commons.wikimedia.org", {
        "action": "query", "titles": "|".join(f"File:{file}" for file in files[:20]),
        "prop": "imageinfo", "iiprop": "url", "iiurlwidth": THUMB_WIDTH,
    })
    for page in data.get("query", {}).get("pages", {}).values():
        info = (page.get("imageinfo") or [{}])[0]
        url = info.get("thumburl") or info.get("url")
        filename = page.get("title", "").removeprefix("File:")
        if url and filename:
            return url, filename
    return None


def _strip(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(value or ""))).strip()


def _wikidata_taxonomy(entity_id: str | None) -> tuple[str, str, str, str]:
    """Return scientific name and taxonomic classification."""
    if not entity_id:
        return "", "other", "", ""
    data = _api("www.wikidata.org", {
        "action": "wbgetentities", "ids": entity_id, "props": "claims|labels",
        "languages": "de|en",
    })
    entity = data.get("entities", {}).get(entity_id, {})
    claims = entity.get("claims", {})

    def claim_value(prop: str) -> str | None:
        try:
            value = claims[prop][0]["mainsnak"]["datavalue"]["value"]
            # Entity-valued claims (such as parent taxon) carry their Q-id in
            # an object, while text claims such as P225 are plain strings.
            return value.get("id") if isinstance(value, dict) else value
        except (KeyError, IndexError, TypeError):
            return None

    scientific = claim_value("P225") or ""

    family_id, order_id = claim_value("P171"), None
    seen: set[str] = set()
    group, family, order_name = "other", "", ""
    group_ids = {
        "Q5113": "bird", "Q7377": "mammal", "Q7432": "insect",
        "Q25344": "butterfly", "Q10811": "reptile", "Q10876": "amphibian", "Q152": "fish",
    }
    current = family_id
    # The parent-taxon chain supplies order/family/class without relying on a
    # brittle Wikipedia infobox parser.
    for _ in range(6):
        if not current or current in seen:
            break
        seen.add(current)
        try:
            node_data = _api("www.wikidata.org", {
                "action": "wbgetentities", "ids": current, "props": "claims|labels",
                "languages": "de|en",
            })
        except Exception:
            # Wikidata can throttle a long lineage lookup.  Keep the article
            # import usable with the details obtained up to this point.
            break
        node = node_data.get("entities", {}).get(current, {})
        label = (node.get("labels", {}).get("de") or node.get("labels", {}).get("en") or {}).get("value", "")
        rank = ""
        try:
            rank = node["claims"]["P105"][0]["mainsnak"]["datavalue"]["value"]["id"]
        except (KeyError, IndexError, TypeError):
            pass
        if rank == "Q35409" and not family:  # family
            family = label
        elif rank == "Q36602" and not order_name:  # order
            order_name = label
        if current in group_ids:
            group = group_ids[current]
        try:
            parent = node["claims"]["P171"][0]["mainsnak"]["datavalue"]["value"]
            current = parent.get("id") if isinstance(parent, dict) else parent
        except (KeyError, IndexError, TypeError):
            current = None
    return scientific, group, family, order_name


def _article_text(host: str, title: str) -> str:
    """Read the article body only for facts; the stored description stays concise."""
    data = _api(host, {
        "action": "query", "titles": title, "redirects": "1", "prop": "extracts",
        "explaintext": "1", "exchars": 12000,
    })
    return next(iter(data.get("query", {}).get("pages", {}).values()), {}).get("extract", "")


_UNIT = r"(?:Millimeter|Zentimeter|Meter|Gramm|Kilogramm|mm|cm|kg|g|m)"
_MEASUREMENT = rf"\d+(?:[,.]\d+)?(?:\s*(?:–|-|bis)\s*\d+(?:[,.]\d+)?)?\s*{_UNIT}"


def _fact(text: str, labels: str) -> str:
    # Restrict the search to a short window after the matching label. This
    # avoids accidentally picking up values from a cited comparison species.
    match = re.search(
        rf"(?:{labels})(?:\s+(?:von|zwischen|bis|zu|etwa|ca\.?|rund|beträgt|liegt|bei|und))*\s*"
        rf"({_MEASUREMENT})",
        text[:6000], re.IGNORECASE,
    )
    if not match:
        return ""
    value = re.sub(r"\s+", " ", match.group(1)).strip()
    return (value.replace("Zentimeter", "cm").replace("Millimeter", "mm")
            .replace("Kilogramm", "kg").replace("Gramm", "g").replace("Meter", "m"))


def _facts_from_article(text: str) -> tuple[str, str, str]:
    """Extract only explicitly stated species facts; unknown is safer than guessed."""
    return (
        _fact(text, r"(?:Körper)?länge|Körpergröße"),
        _fact(text, r"Flügelspannweite|Spannweite"),
        _fact(text, r"Körpergewicht|Gewicht|wiegt"),
    )


def _difficulty_from_article(text: str) -> tuple[int, str]:
    """A conservative photo-difficulty estimate based on explicit article cues."""
    normalized = text[:8000].casefold()
    if any(term in normalized for term in ("vom aussterben bedroht", "critically endangered")):
        return 5, "Vom Aussterben bedroht"
    if any(term in normalized for term in ("stark gefährdet", "endangered", "sehr selten")):
        return 4, "Stark gefährdet / sehr selten"
    if any(term in normalized for term in ("gefährdet", "vulnerable", "selten", "nur lokal")):
        return 3, "Gefährdet / lokal selten"
    if any(term in normalized for term in ("häufig", "weit verbreitet", "nicht gefährdet")):
        return 1, "Häufig / weit verbreitet"
    if any(term in normalized for term in ("nachtaktiv", "dämmerungsaktiv", "scheu")):
        return 3, "Schwer zu beobachten"
    return 2, ""


def _make_plate(raw: bytes, width: int) -> bytes:
    with Image.open(io.BytesIO(raw)) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        w, h = image.size
        if w / h > ASPECT:
            crop_w = int(h * ASPECT)
            image = image.crop(((w - crop_w) // 2, 0, (w + crop_w) // 2, h))
        else:
            crop_h = int(w / ASPECT)
            top = int((h - crop_h) * 0.4)
            image = image.crop((0, top, w, top + crop_h))
        target = min(width, image.width)
        image = image.resize((target, round(target / ASPECT)), Image.LANCZOS)
        gray = ImageEnhance.Contrast(ImageOps.autocontrast(image.convert("L"), cutoff=(1, 2))).enhance(1.08)
        ramp = []
        for dark, light in zip(INK, PAPER):
            ramp.extend(round(dark + (light - dark) * (i / 255)) for i in range(256))
        plate = Image.blend(gray.convert("RGB").point(ramp), Image.new("RGB", image.size, PAPER), 0.16)
        out = io.BytesIO()
        plate.save(out, "JPEG", quality=82 if width > 500 else 78, optimize=True, progressive=True)
        return out.getvalue()


def _image_metadata(filename: str) -> tuple[str, str]:
    if not filename:
        return "Wikimedia Commons", ""
    data = _api("commons.wikimedia.org", {
        "action": "query", "titles": f"File:{filename}", "prop": "imageinfo",
        "iiprop": "extmetadata|url", "iiextmetadatafilter": "Artist|LicenseShortName",
    })
    for page in data.get("query", {}).get("pages", {}).values():
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        parts = [_strip(meta.get(key, {}).get("value", "")) for key in ("Artist", "LicenseShortName")]
        return " · ".join(part for part in parts if part) or "Wikimedia Commons", info.get("descriptionurl", "")
    return "Wikimedia Commons", ""


def _group_from_categories(page: dict) -> str:
    """Useful fallback while Wikidata is temporarily throttling."""
    text = " ".join(category.get("title", "") for category in page.get("categories", [])).lower()
    for needles, group in (
        (("vogel", "alken", "eulen", "enten", "falken"), "bird"),
        (("säugetier", "saeugetier", "wal", "nager", "katzen"), "mammal"),
        (("schmetterling", "falter"), "butterfly"),
        (("insekten", "käfer", "kaefer", "libelle", "biene"), "insect"),
        (("amphib", "lurch"), "amphibian"),
        (("reptil", "schlangen", "eidechsen"), "reptile"),
        (("fische", "fischart"), "fish"),
    ):
        if any(needle in text for needle in needles):
            return group
    return "other"


def import_from_wikipedia(name: str) -> WikipediaSpecies:
    page, title, host = _find_page(name.strip())
    # Wikipedia distinguishes an animal article from a family/genus using
    # suffixes such as "(Art)".  They are useful for lookup, but should never
    # become part of the collection's common name.
    common_name = re.sub(r"\s+\((?:art|species)\)$", "", title, flags=re.IGNORECASE)
    try:
        scientific, group, family, order_name = _wikidata_taxonomy(page.get("pageprops", {}).get("wikibase_item"))
    except Exception:
        scientific, group, family, order_name = "", "other", "", ""
    if group == "other":
        group = _group_from_categories(page)
    article_text = page.get("extract") or ""
    try:
        article_text = _article_text(host, title)
        size, wingspan, weight = _facts_from_article(article_text)
    except Exception:
        size = wingspan = weight = ""
    difficulty, rarity = _difficulty_from_article(article_text + " " + common_name)
    image = page.get("thumbnail", {})
    image_url, filename = image.get("source"), page.get("pageimage", "")
    if filename and any(marker in filename.lower() for marker in _COLLAGE_MARKERS):
        try:
            alternative = _single_article_image(host, title)
            if alternative:
                image_url, filename = alternative
        except Exception:
            # A collage is still preferable to no reference image if Commons
            # is temporarily unavailable.
            pass
    image_key = thumb_key = credit = source = None
    if image_url:
        request = urllib.request.Request(image_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=45) as response:
            raw = response.read()
        storage = get_storage()
        image_key = storage.save("reference", f"{title}.jpg", io.BytesIO(_make_plate(raw, 1000)))
        thumb_key = storage.save("reference-thumb", f"{title}.jpg", io.BytesIO(_make_plate(raw, 480)))
        try:
            credit, source = _image_metadata(filename)
        except Exception:
            # The article and its already downloaded image remain useful even
            # if Commons has a short-lived metadata/API problem.
            credit, source = "Wikimedia Commons", ""
    article_url = f"https://{host}/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
    return WikipediaSpecies(
        common_name=common_name, scientific_name=scientific, description=(page.get("extract") or "").strip(),
        group=group, family=family, order_name=order_name, size=size, wingspan=wingspan,
        weight=weight, difficulty=difficulty, rarity=rarity, reference_image=image_key,
        reference_thumb=thumb_key, reference_credit=credit, reference_source=source or article_url,
    )
