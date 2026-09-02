"""Import a species and its reference plate from Wikipedia/Wikimedia.

The MediaWiki APIs are used instead of scraping article markup.  That keeps the
import resilient to layout changes and preserves the required image attribution.
"""

from __future__ import annotations

import html
import io
import json
import re
import threading
import time
import urllib.parse
import urllib.request
from functools import lru_cache
from urllib.error import HTTPError
from dataclasses import dataclass

from PIL import Image, ImageEnhance, ImageOps
from pillow_heif import register_heif_opener

from .storage import get_storage
from .vocab import group_from_taxonomy

USER_AGENT = "WildlifeCompedium/0.2 (https://github.com/leandermu/wildlife-compedium)"
THUMB_WIDTH = 1400
ASPECT = 4 / 3
INK = (36, 42, 33)
PAPER = (243, 237, 223)
register_heif_opener()

_API_RATE_LOCKS: dict[str, threading.Lock] = {}
_API_LAST_REQUEST: dict[str, float] = {}
_API_BACKOFF_UNTIL: dict[str, float] = {}
_API_STATE_LOCK = threading.Lock()


def _wait_for_api_slot(host: str) -> None:
    """Space concurrent API calls and share rate-limit backoff per host."""
    with _API_STATE_LOCK:
        host_lock = _API_RATE_LOCKS.setdefault(host, threading.Lock())
    with host_lock:
        minimum_interval = 0.14 if host == "www.wikidata.org" else 0.04
        now = time.monotonic()
        wait_until = max(
            _API_BACKOFF_UNTIL.get(host, 0.0),
            _API_LAST_REQUEST.get(host, 0.0) + minimum_interval,
        )
        if wait_until > now:
            time.sleep(wait_until - now)
        _API_LAST_REQUEST[host] = time.monotonic()


@dataclass
class ImportedSpecies:
    common_name: str
    scientific_name: str
    description: str
    group: str
    class_name: str
    family: str
    order_name: str
    size: str
    wingspan: str
    weight: str
    difficulty: int
    rarity: str
    habitats: list[str]
    regions: list[str]
    countries: list[str]
    tags: list[str]
    reference_image: str | None
    reference_thumb: str | None
    reference_credit: str | None
    reference_source: str | None


def _api(host: str, params: dict) -> dict:
    url = f"https://{host}/w/api.php?" + urllib.parse.urlencode({**params, "format": "json"})
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(6):
        _wait_for_api_slot(host)
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code != 429 or attempt == 5:
                raise
            retry_after = exc.headers.get("Retry-After", "")
            try:
                delay = float(retry_after)
            except ValueError:
                delay = min(30.0, 2.0 ** (attempt + 1))
            delay = max(2.0, min(30.0, delay))
            with _API_STATE_LOCK:
                _API_BACKOFF_UNTIL[host] = max(
                    _API_BACKOFF_UNTIL.get(host, 0.0),
                    time.monotonic() + delay,
                )
    raise RuntimeError("Wikipedia-Abfrage fehlgeschlagen")


@lru_cache(maxsize=2048)
def _json_api(url: str, params: tuple[tuple[str, str], ...]) -> dict:
    request = urllib.request.Request(
        url + "?" + urllib.parse.urlencode(dict(params)),
        headers={"User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


@lru_cache(maxsize=1024)
def _first_page(host: str, title: str) -> tuple[dict, str] | None:
    data = _api(host, {
        "action": "query", "titles": title, "redirects": "1",
        "prop": "extracts|pageimages|pageprops|categories", "exintro": "1", "explaintext": "1",
        "pithumbsize": THUMB_WIDTH, "cllimit": "max",
    })
    for page_id, page in data.get("query", {}).get("pages", {}).items():
        if page_id != "-1":
            return page, page.get("title", title)
    return None


@lru_cache(maxsize=128)
def _article_links(host: str, title: str) -> list[str]:
    data = _api(host, {
        "action": "query", "titles": title, "redirects": "1",
        "prop": "links", "pllimit": 100, "plnamespace": 0,
    })
    return [
        link.get("title", "")
        for page in data.get("query", {}).get("pages", {}).values()
        for link in page.get("links", [])
    ]


def _find_page(name: str) -> tuple[dict, str, str]:
    """Find a zoological article, never merely the first similarly named hit."""
    for host in ("de.wikipedia.org", "en.wikipedia.org"):
        exact = _first_page(host, name)
        if exact:
            page, title = exact
            if _is_species_article(page):
                return page, title, host
            resolved = _resolve_disambiguation(host, page, title, name)
            if resolved != exact and _is_species_article(resolved[0]):
                return resolved[0], resolved[1], host

        for query in (f'intitle:"{name}"', f'"{name}" Tier'):
            search = _api(host, {
                "action": "query", "list": "search", "srsearch": query,
                "srnamespace": 0, "srlimit": 10,
            }).get("query", {}).get("search", [])
            candidate_titles = sorted(
                {row["title"] for row in search}, key=_animal_title_priority
            )
            for candidate in candidate_titles:
                if not _title_matches_request(candidate, name):
                    continue
                hit = _first_page(host, candidate)
                if not hit:
                    continue
                page, title = hit
                if _is_species_article(page):
                    return page, title, host
                resolved = _resolve_disambiguation(host, page, title, name)
                if resolved != (page, title) and _is_species_article(resolved[0]):
                    return resolved[0], resolved[1], host
    raise LookupError(
        "Es wurde kein eindeutig passender Tierartikel gefunden. "
        "Bitte den genaueren Artnamen eingeben."
    )


_ANIMAL_TITLE_MARKERS = (
    "(art)", "(species)", "(tier)", "(animal)", "(vogel)", "(bird)",
    "(schmetterling)", "(butterfly)", "(säugetier)", "(mammal)", "(fisch)",
    "(fish)", "(insekt)", "(insect)", "(amphibie)", "(amphibian)",
    "(reptil)", "(reptile)",
)


def _animal_title_priority(title: str) -> tuple[bool, int]:
    folded = title.casefold()
    return not any(marker in folded for marker in _ANIMAL_TITLE_MARKERS), len(title)


def _title_matches_request(title: str, requested_name: str) -> bool:
    folded_title = re.sub(r"\([^)]*\)", "", title.casefold()).strip()

    def tokens(value: str) -> list[str]:
        value = re.sub(r"\([^)]*\)", "", value.casefold())
        return re.findall(r"[a-zäöüß0-9]+", value)

    title_tokens = tokens(title)
    request_tokens = tokens(requested_name)
    if not request_tokens:
        return False
    if title_tokens == request_tokens:
        return True
    # A validated species article may add one qualifier, for example
    # "Gemeiner Schimpanse" for "Schimpanse" or "Atlantischer Hering" for
    # "Hering". The species-rank Wikidata check still rejects sculptures,
    # places and other namesakes.
    return len(request_tokens) == 1 and bool(
        re.search(
            rf"(?<![-\w]){re.escape(request_tokens[0])}(?![-\w])",
            folded_title,
        )
    )


def _resolve_disambiguation(host: str, page: dict, title: str, requested_name: str) -> tuple[dict, str]:
    """Prefer the species article when an entered name is a disambiguation page."""
    categories = " ".join(c.get("title", "").lower() for c in page.get("categories", []))
    if "begriffsklärung" not in categories and "disambiguation" not in categories:
        return page, title
    links = _article_links(host, title)
    name = requested_name.casefold()
    candidates = sorted(
        (link for link in links if name in link.casefold()),
        key=lambda link: (
            _animal_title_priority(link)[0],
            not link.casefold().startswith((name, f"haus{name}")),
            len(link),
        ),
    )
    # A name-specific species link is unambiguous here.  Do not walk every
    # link on the page: that creates needless API traffic and rate limiting.
    for candidate in candidates[:8]:
        if (hit := _first_page(host, candidate)) and _is_species_article(hit[0]):
            return hit
    return page, title


def _is_animal_article(page: dict) -> bool:
    """Validate cheaply from article metadata before doing the detailed lineage lookup."""
    categories = " ".join(c.get("title", "") for c in page.get("categories", [])).casefold()
    if any(term in categories for term in ("begriffsklärung", "disambiguation")):
        return False
    lead = (page.get("extract") or "")[:1200].casefold()
    evidence = f"{categories} {lead}"
    animal_markers = (
        "tierart", "säugetier", "saeugetier", "vogel", "fischart", "reptil",
        "amphib", "insekt", "käfer", "kaefer", "libelle", "schmetterling",
        "falter", "weichtier", "spinnentier", "krebstier", "haustier",
        "wildtier", "zoolog", "fuchsart", "wildhunde", "hirsche", "mangusten",
    )
    non_animal_markers = (
        "film", "fernsehserie", "musikalbum", "ortsteil", "familienname",
        "bauwerk", "unternehmen", "software", "fahrzeug", "steinskulptur",
        "skulptur", "plastik", "statue", "archäologischer fund",
    )
    return any(marker in evidence for marker in animal_markers) and not any(
        marker in evidence for marker in non_animal_markers
    )


def _is_species_article(page: dict) -> bool:
    """Require a species-rank Wikidata entity when available.

    Lead text alone is too ambiguous: an article about an elk sculpture can
    contain plenty of animal vocabulary. A taxonomic name plus a species or
    subspecies rank is a much stronger signal.
    """
    entity_id = page.get("pageprops", {}).get("wikibase_item")
    if not entity_id:
        return _is_animal_article(page)
    try:
        claims = _wikidata_entity(entity_id).get("claims", {})
        scientific = claims.get("P225")
        rank = claims.get("P105", [{}])[0].get("mainsnak", {}).get(
            "datavalue", {}
        ).get("value", {})
        rank_id = rank.get("id") if isinstance(rank, dict) else None
        if scientific and rank_id in {"Q7432", "Q68947"}:  # species / subspecies
            return True
        # A successfully loaded Wikidata entity without species-rank taxon
        # claims is not an animal species page (for example a heraldic ostrich).
        return False
    except Exception:
        pass
    return _is_animal_article(page)


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


@lru_cache(maxsize=4096)
def _wikidata_entity(entity_id: str) -> dict:
    data = _api("www.wikidata.org", {
        "action": "wbgetentities", "ids": entity_id,
        "props": "claims|labels|sitelinks", "languages": "de|en",
        "sitefilter": "dewiki",
    })
    return data.get("entities", {}).get(entity_id, {})


def _taxon_name(node: dict) -> str:
    """Prefer the German Wikipedia taxon title over a Latin fallback label."""
    title = node.get("sitelinks", {}).get("dewiki", {}).get("title", "")
    if title:
        return re.sub(r"\s+\([^)]*\)$", "", title).strip()
    return (
        node.get("labels", {}).get("de")
        or node.get("labels", {}).get("en")
        or {}
    ).get("value", "")


def _wikidata_taxonomy(entity_id: str | None) -> tuple[str, str, str, str, str]:
    """Return scientific name and taxonomic classification."""
    if not entity_id:
        return "", "other", "", "", ""
    entity = _wikidata_entity(entity_id)
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

    seen: set[str] = set()
    group, class_name, family, order_name = "other", "", "", ""
    group_ids = {
        "Q5113": "bird", "Q7377": "mammal", "Q1390": "insect",
        "Q28319": "butterfly", "Q10811": "reptile", "Q10876": "amphibian",
        "Q152": "fish",
    }
    current = entity_id
    # The parent-taxon chain supplies order/family/class without relying on a
    # brittle Wikipedia infobox parser.
    for _ in range(64):
        if not current or current in seen:
            break
        seen.add(current)
        try:
            node = _wikidata_entity(current)
        except Exception:
            # Wikidata can throttle a long lineage lookup.  Keep the article
            # import usable with the details obtained up to this point.
            break
        label = _taxon_name(node)
        rank = ""
        try:
            rank = node["claims"]["P105"][0]["mainsnak"]["datavalue"]["value"]["id"]
        except (KeyError, IndexError, TypeError):
            pass
        if rank == "Q35409" and not family:  # family
            family = label
        elif rank == "Q36602" and not order_name:  # order
            order_name = label
        elif rank == "Q37517" and not class_name:  # class
            class_name = label
        if current in group_ids:
            candidate_group = group_ids[current]
            # Lepidoptera is more specific than the later Insecta ancestor.
            if group == "other" or candidate_group == "butterfly":
                group = candidate_group
        if group != "other" and class_name and family and order_name:
            break
        try:
            parent = node["claims"]["P171"][0]["mainsnak"]["datavalue"]["value"]
            current = parent.get("id") if isinstance(parent, dict) else parent
        except (KeyError, IndexError, TypeError):
            current = None
    return scientific, group, class_name, family, order_name


_GERMAN_TAXON_NAMES = {
    "Carnivora": "Raubtiere",
    "Artiodactyla": "Paarhufer",
    "Cetartiodactyla": "Paarhufer",
    "Herpestidae": "Mangusten",
    "Canidae": "Hunde",
    "Cervidae": "Hirsche",
    "Equidae": "Pferde",
    "Bradypodidae": "Dreifinger-Faultiere",
    "Castoridae": "Biber",
    "Upupidae": "Wiedehopfe",
    "Pelecaniformes": "Ruderfüßer",
    "Haematopodidae": "Austernfischer",
    "Suliformes": "Tölpelartige",
    "Varanidae": "Warane",
    "Dermochelyidae": "Lederschildkröten",
    "Pelobatidae": "Europäische Schaufelfußkröten",
    "Esocidae": "Hechte",
    "Salmoniformes": "Lachsartige",
    "Myliobatidae": "Adlerrochen",
    "Xiphiidae": "Schwertfische",
    "Mantidae": "Gottesanbeterinnen",
    "Diapheromeridae": "Stabschrecken",
    "Lepismatidae": "Fischchen",
    "Forficulidae": "Eigentliche Ohrwürmer",
}


def _german_taxon_name(value: str) -> str:
    return _GERMAN_TAXON_NAMES.get(value, value)


_COMMON_NAME_ALIASES = {
    "atlantischer blauflossen-thunfisch": "Roter Thun",
    "japanischer kugelfisch": "Takifugu rubripes",
    "europäische hornisse": "Hornisse",
}


def _article_text(host: str, title: str) -> str:
    """Read the article body only for facts; the stored description stays concise."""
    data = _api(host, {
        "action": "query", "titles": title, "redirects": "1", "prop": "extracts",
        "explaintext": "1",
    })
    return next(iter(data.get("query", {}).get("pages", {}).values()), {}).get("extract", "")


_UNIT = r"(?:Millimetern?|Zentimetern?|Metern?|Gramm|Kilogramm|mm|cm|kg|g|m)"
_MEASUREMENT = rf"\d+(?:[,.]\d+)?(?:\s*(?:–|-|bis)\s*\d+(?:[,.]\d+)?)?\s*{_UNIT}"


def _fact(text: str, labels: str) -> str:
    # Restrict the search to a short window after the matching label. This
    # avoids accidentally picking up values from a cited comparison species.
    match = re.search(
        rf"(?:{labels})[^.\n:;]{{0,90}}?"
        rf"({_MEASUREMENT})",
        text[:6000], re.IGNORECASE,
    )
    if not match:
        return ""
    value = re.sub(r"\s+", " ", match.group(1)).strip()
    for pattern, unit in (
        (r"\bZentimetern?\b", "cm"), (r"\bMillimetern?\b", "mm"),
        (r"\bKilogramm\b", "kg"), (r"\bGramm\b", "g"),
        (r"\bMetern?\b", "m"),
    ):
        value = re.sub(pattern, unit, value, flags=re.IGNORECASE)
    return value


def _facts_from_article(text: str) -> tuple[str, str, str]:
    """Extract only explicitly stated species facts; unknown is safer than guessed."""
    size = _fact(
        text,
        r"Kopf[- ]?Rumpf[- ]?Länge|Kopfrumpflänge|Körperlänge|Gesamtlänge|Körpergröße",
    ) or _fact(text, r"Schulterhöhe|Widerristhöhe|Stockmaß")
    return (
        size,
        _fact(text, r"Flügelspannweite|Spannweite"),
        _fact(text, r"Körpergewicht|Gewicht|wiegt"),
    )


def _short_description(text: str, common_name: str, max_chars: int = 360) -> str:
    """Turn the lead into a compact one- or two-sentence field-guide summary."""
    clean = re.sub(r"\[[^\]]{1,20}\]", "", _strip(text))
    clean = re.sub(r"\s*\([^)]*(?:Aussprache|Hörbeispiel|anhören)[^)]*\)", "", clean)
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-ZÄÖÜ])", clean)
    picked: list[str] = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        candidate = " ".join(picked + [sentence])
        if len(candidate) > max_chars:
            break
        picked.append(sentence)
        if len(picked) == 2 or len(candidate) >= 180:
            break
    summary = " ".join(picked)
    if summary:
        return summary
    fallback = clean[:max_chars].rsplit(" ", 1)[0].rstrip(" ,;:")
    return f"{fallback}…" if fallback else f"Kurzbeschreibung zu {common_name}."


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


def _controlled_habitats_and_tags(text: str, group: str) -> tuple[list[str], list[str]]:
    """Map explicit German article cues to the app's finite vocabulary."""
    normalized = text.casefold()
    habitat_terms = {
        "forest": ("wald", "wälder", "forst", "gehölz"),
        "field": ("wiese", "grünland", "acker", "feldflur", "weide"),
        "water": ("gewässer", "fluss", "bächen", "bach", "see", "teich", "ufer", "sumpf"),
        "moor": ("moor", "feuchtgebiet"),
        "heath": ("heide", "trockenrasen", "magerrasen"),
        "alps": ("alpen", "hochgebirge", "gebirge", "baumgrenze"),
        "coast": ("küste", "watt", "düne", "salzwiese"),
        "city": ("stadt", "siedlung", "gebäude"),
        "garden": ("garten", "gärten"),
        "park": ("park", "friedhof"),
        "night": ("nachtaktiv", "dämmerungsaktiv"),
        "savanna": ("savanne", "steppe"),
        "rainforest": ("regenwald", "tropischer wald"),
        "ocean": ("offenes meer", "ozean", "pelagisch"),
    }
    habitats = [key for key, terms in habitat_terms.items() if any(t in normalized for t in terms)]
    tag_terms = {
        "nachtaktiv": ("nachtaktiv", "dämmerungsaktiv"),
        "zugvogel": ("zugvogel", "langstreckenzieher", "kurzstreckenzieher"),
        "greifvogel": ("greifvogel", "habichtartige", "falkenartige"),
        "raubtier": ("raubtier", "beutegreifer", "fleischfresser"),
        "wasserbewohner": ("aquatisch", "wasserbewohnend", "gewässer"),
        "bestäuber": ("bestäuber", "bestäubung"),
        "giftig": ("giftig", "giftzahn", "hautgift"),
        "geschützt": ("streng geschützt", "besonders geschützt"),
    }
    tags = [key for key, terms in tag_terms.items() if any(t in normalized for t in terms)]
    if group != "other":
        tags.insert(0, group)
    return habitats[:6], tags[:8]


def _regions_from_article(text: str) -> list[str]:
    """Derive broad native ranges from the article instead of raw sightings.

    Unfiltered occurrence portals also contain zoo animals and accidental
    records. Those must not turn an African species into a German one.
    """
    # The first paragraph normally states the native range. Later paragraphs
    # often mention zoos, introduced pets or comparison species and would
    # create false continents (for example North America for the Fennek).
    normalized = text.split("\n", 1)[0][:2500].casefold()
    regions: list[str] = []

    def add(value: str) -> None:
        if value not in regions:
            regions.append(value)

    if "bayern" in normalized:
        add("bavaria")
        add("germany")
        add("europe")
    elif "deutschland" in normalized:
        add("germany")
        add("europe")

    region_terms = {
        "europe": ("europa", "europäisch", "nordeuropa", "südeuropa", "osteuropa", "westeuropa"),
        "africa": ("afrika", "afrikanisch", "sahara", "sahel"),
        "asia": ("asien", "asiatisch", "sibirien", "indischer subkontinent"),
        "north_america": ("nordamerika", "kanada", "alaska"),
        "south_america": ("südamerika", "amazonas", "patagonien"),
        "oceania": ("australien", "ozeanien", "neuseeland"),
        "antarctica": ("antarktis", "antarktisch"),
        "arctic": ("arktis", "arktisch", "polarkreis"),
    }
    for region, terms in region_terms.items():
        if any(term in normalized for term in terms):
            add(region)
    return regions or ["world"]


def _gbif_enrichment(scientific_name: str, article_text: str, group: str) -> dict:
    """Supplement taxonomy and regional occurrence signals from GBIF."""
    if not scientific_name:
        return {}
    try:
        match = _json_api(
            "https://api.gbif.org/v1/species/match",
            (("name", scientific_name), ("strict", "false")),
        )
    except Exception:
        return {}
    if int(match.get("confidence") or 0) < 70 or match.get("matchType") == "NONE":
        return {}
    key = match.get("usageKey") or match.get("speciesKey")
    class_name = str(match.get("class") or "").casefold()
    gbif_group = {
        "aves": "bird", "mammalia": "mammal", "insecta": "insect",
        "amphibia": "amphibian", "reptilia": "reptile",
        "actinopterygii": "fish", "chondrichthyes": "fish",
    }.get(class_name, group)
    if str(match.get("order") or "").casefold() == "lepidoptera":
        gbif_group = "butterfly"

    def count(**params: str) -> int:
        if not key:
            return 0
        try:
            result = _json_api(
                "https://api.gbif.org/v1/occurrence/search",
                tuple(sorted({"taxon_key": str(key), "limit": "0", **params}.items())),
            )
            return int(result.get("count") or 0)
        except Exception:
            return 0

    regions = _regions_from_article(article_text)
    result = {
        "scientific_name": match.get("canonicalName") or scientific_name,
        "group": gbif_group,
        "class_name": match.get("class") or "",
        "family": _german_taxon_name(match.get("family") or ""),
        "order_name": _german_taxon_name(match.get("order") or ""),
        "regions": regions,
        "countries": ["Deutschland"] if "germany" in regions else [],
    }
    # GBIF counts are useful for locally occurring species, but not as proof
    # that an exotic species belongs to Germany (zoo records are included).
    if "germany" in regions:
        germany = count(country="DE")
        difficulty = 4
        rarity = "Keine regionalen GBIF-Nachweise"
        if germany >= 1000:
            difficulty, rarity = 1, "Viele Nachweise in Deutschland"
        elif germany >= 100:
            difficulty, rarity = 2, "Regelmäßig in Deutschland nachgewiesen"
        elif germany >= 10:
            difficulty, rarity = 3, "Wenige Nachweise in Deutschland"
        elif germany > 0:
            difficulty, rarity = 4, "Sehr wenige Nachweise in Deutschland"
        if any(term in article_text.casefold() for term in ("nachtaktiv", "dämmerungsaktiv", "sehr scheu")):
            difficulty = min(5, difficulty + 1)
        result.update(difficulty=difficulty, rarity=rarity)
    return result


def _german_fallback_description(
    common_name: str, group: str, family: str, order_name: str
) -> str:
    group_names = {
        "bird": "eine Vogelart", "mammal": "eine Säugetierart",
        "butterfly": "eine Schmetterlingsart", "insect": "eine Insektenart",
        "amphibian": "eine Amphibienart", "reptile": "eine Reptilienart",
        "fish": "eine Fischart", "other": "eine Tierart",
    }
    classification = group_names.get(group, "eine Tierart")
    detail = f" aus der Familie {family}" if family else (f" aus der Ordnung {order_name}" if order_name else "")
    return f"Der {common_name} ist {classification}{detail}."


def make_reference_plate(raw: bytes, width: int) -> bytes:
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
    text = (
        " ".join(category.get("title", "") for category in page.get("categories", []))
        + " " + (page.get("extract") or "")[:1600]
    ).casefold()
    for needles, group in (
        (("vogel", "alken", "eulen", "enten", "falken"), "bird"),
        ((
            "säugetier", "saeugetier", "pferd", "hundeart", "hundefamilie",
            "katzen", "wal", "nager", "huftier", "raubtier", "primat",
            "fledermaus", "hirsch", "bären",
        ), "mammal"),
        (("schmetterling", "falter"), "butterfly"),
        (("insekten", "käfer", "kaefer", "libelle", "biene"), "insect"),
        (("amphib", "lurch"), "amphibian"),
        (("reptil", "schlangen", "eidechsen"), "reptile"),
        (("fische", "fischart"), "fish"),
    ):
        if any(needle in text for needle in needles):
            return group
    return "other"


def import_species_automatically(
    name: str,
    *,
    save_reference: bool = True,
) -> ImportedSpecies:
    requested_name = name.strip()
    lookup_name = _COMMON_NAME_ALIASES.get(requested_name.casefold(), requested_name)
    page, title, host = _find_page(lookup_name)
    # Wikipedia distinguishes an animal article from a family/genus using
    # suffixes such as "(Art)".  They are useful for lookup, but should never
    # become part of the collection's common name.
    common_name = re.sub(r"\s+\((?:art|species)\)$", "", title, flags=re.IGNORECASE)
    if host != "de.wikipedia.org" or lookup_name != requested_name:
        common_name = requested_name
    try:
        scientific, group, class_name, family, order_name = _wikidata_taxonomy(page.get("pageprops", {}).get("wikibase_item"))
    except Exception:
        scientific, group, class_name, family, order_name = "", "other", "", "", ""
    if group == "other":
        group = _group_from_categories(page)
    article_text = page.get("extract") or ""
    try:
        article_text = _article_text(host, title)
        size, wingspan, weight = _facts_from_article(article_text)
    except Exception:
        size = wingspan = weight = ""
    difficulty, rarity = _difficulty_from_article(article_text + " " + common_name)
    enrichment = _gbif_enrichment(
        scientific,
        page.get("extract") or article_text,
        group,
    )
    scientific = enrichment.get("scientific_name", scientific)
    enriched_group = enrichment.get("group", "other")
    if group == "other" and enriched_group != "other":
        group = enriched_group
    class_name = class_name or enrichment.get("class_name", "")
    family = _german_taxon_name(family or enrichment.get("family", ""))
    order_name = _german_taxon_name(order_name or enrichment.get("order_name", ""))
    group = group_from_taxonomy(class_name, order_name, group)
    difficulty = enrichment.get("difficulty", difficulty)
    rarity = enrichment.get("rarity", rarity)
    habitats, tags = _controlled_habitats_and_tags(article_text, group)
    image = page.get("thumbnail", {})
    image_url, filename = image.get("source"), page.get("pageimage", "")
    if not image_url or (
        filename and any(marker in filename.lower() for marker in _COLLAGE_MARKERS)
    ):
        try:
            alternative = _single_article_image(host, title)
            if alternative:
                image_url, filename = alternative
        except Exception:
            # A collage is still preferable to no reference image if Commons
            # is temporarily unavailable.
            pass
    image_key = thumb_key = credit = source = None
    if image_url and save_reference:
        request = urllib.request.Request(image_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=45) as response:
            raw = response.read()
        storage = get_storage()
        image_key = storage.save(
            "reference", f"{title}.jpg", io.BytesIO(make_reference_plate(raw, 1000))
        )
        thumb_key = storage.save(
            "reference-thumb", f"{title}.jpg", io.BytesIO(make_reference_plate(raw, 480))
        )
        try:
            credit, source = _image_metadata(filename)
        except Exception:
            # The article and its already downloaded image remain useful even
            # if Commons has a short-lived metadata/API problem.
            credit, source = "Wikimedia Commons", ""
    article_url = f"https://{host}/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
    if image_url and not save_reference:
        image_key = thumb_key = image_url
        credit, source = "Wikimedia Commons", article_url
    description = (
        _short_description(page.get("extract") or article_text, common_name)
        if host == "de.wikipedia.org"
        else _german_fallback_description(common_name, group, family, order_name)
    )
    return ImportedSpecies(
        common_name=common_name, scientific_name=scientific,
        description=description,
        group=group, class_name=class_name, family=family, order_name=order_name,
        size=size, wingspan=wingspan,
        weight=weight, difficulty=difficulty, rarity=rarity,
        habitats=habitats,
        regions=enrichment.get("regions") or _regions_from_article(page.get("extract") or article_text),
        countries=enrichment.get("countries", []), tags=tags,
        reference_image=image_key,
        reference_thumb=thumb_key, reference_credit=credit, reference_source=source or article_url,
    )
