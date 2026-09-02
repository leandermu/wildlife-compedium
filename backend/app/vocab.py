"""Human-facing vocabulary. Single source of truth — the frontend pulls these
labels from /api/meta so new habitats or groups never need a frontend release."""

import unicodedata

GROUPS: dict[str, dict] = {
    "bird": {"label": "Vögel", "singular": "Vogel", "icon": "🐦", "order": 1},
    "mammal": {"label": "Säugetiere", "singular": "Säugetier", "icon": "🦌", "order": 2},
    "butterfly": {"label": "Schmetterlinge", "singular": "Schmetterling", "icon": "🦋", "order": 3},
    "insect": {"label": "Insekten", "singular": "Insekt", "icon": "🐝", "order": 4},
    "amphibian": {"label": "Amphibien", "singular": "Amphibie", "icon": "🐸", "order": 5},
    "reptile": {"label": "Reptilien", "singular": "Reptil", "icon": "🦎", "order": 6},
    "fish": {"label": "Fische", "singular": "Fisch", "icon": "🐟", "order": 7},
    "other": {"label": "Sonstige", "singular": "Sonstiges", "icon": "🐾", "order": 8},
}

GROUP_CLASSES: dict[str, str] = {
    "bird": "Aves",
    "mammal": "Mammalia",
    "butterfly": "Insecta",
    "insect": "Insecta",
    "amphibian": "Amphibia",
    "reptile": "Reptilia",
    "fish": "Actinopterygii",
    "other": "Animalia",
}

CLASS_LABELS: dict[str, str] = {
    "Aves": "Vögel",
    "Mammalia": "Säugetiere",
    "Insecta": "Insekten",
    "Amphibia": "Amphibien",
    "Reptilia": "Reptilien",
    "Actinopterygii": "Strahlenflosser",
    "Chondrichthyes": "Knorpelfische",
    "Arachnida": "Spinnentiere",
    "Gastropoda": "Schnecken",
    "Malacostraca": "Höhere Krebse",
    "Animalia": "Tiere",
}

HABITATS: dict[str, dict] = {
    "garden": {"label": "Garten", "icon": "🌿", "order": 1},
    "city": {"label": "Stadt", "icon": "🏘", "order": 2},
    "park": {"label": "Park", "icon": "🌳", "order": 3},
    "forest": {"label": "Wald", "icon": "🌲", "order": 4},
    "field": {"label": "Feld & Wiese", "icon": "🌾", "order": 5},
    "water": {"label": "Gewässer", "icon": "💧", "order": 6},
    "moor": {"label": "Moor", "icon": "🪴", "order": 7},
    "heath": {"label": "Heide & Trockenrasen", "icon": "🌼", "order": 8},
    "alps": {"label": "Berge & Alpen", "icon": "🏔", "order": 9},
    "coast": {"label": "Küste", "icon": "🐚", "order": 10},
    "savanna": {"label": "Savanne", "icon": "🦁", "order": 11},
    "rainforest": {"label": "Regenwald", "icon": "🌴", "order": 12},
    "ocean": {"label": "Offenes Meer", "icon": "🌊", "order": 13},
}

REGIONS: dict[str, dict] = {
    "bavaria": {"label": "Bayern", "icon": "🥨", "order": 1},
    "germany": {"label": "Deutschland", "icon": "🇩🇪", "order": 2},
    "europe": {"label": "Europa", "icon": "🌍", "order": 3},
    "africa": {"label": "Afrika", "icon": "🌍", "order": 4},
    "asia": {"label": "Asien", "icon": "🌏", "order": 5},
    "north_america": {"label": "Nordamerika", "icon": "🌎", "order": 6},
    "south_america": {"label": "Südamerika", "icon": "🌎", "order": 7},
    "oceania": {"label": "Australien & Ozeanien", "icon": "🌏", "order": 8},
    "antarctica": {"label": "Antarktis", "icon": "🧊", "order": 9},
    "arctic": {"label": "Arktis", "icon": "❄️", "order": 10},
    "world": {"label": "Weltweit / Expedition", "icon": "🧭", "order": 11},
}

ACTIVITIES: dict[str, dict] = {
    "diurnal": {"label": "Tagaktiv", "icon": "☀️", "order": 1},
    "nocturnal": {"label": "Nachtaktiv", "icon": "🌙", "order": 2},
}

TAGS: dict[str, dict] = {
    "zugvogel": {"label": "Zugvogel", "order": 1},
    "standvogel": {"label": "Standvogel", "order": 2},
    "wanderfalter": {"label": "Wanderfalter", "order": 3},
    "wiesenbrueter": {"label": "Wiesenbrüter", "order": 4},
    "stadtvogel": {"label": "Stadtvogel", "order": 5},
    "bestaeuber": {"label": "Bestäuber", "order": 6},
    "farbenpracht": {"label": "Farbenprächtig", "order": 7},
    "waermeliebend": {"label": "Wärmeliebend", "order": 8},
    "futterhaus": {"label": "Am Futterhaus", "order": 9},
    "schwarm": {"label": "Schwarmtier", "order": 10},
    "brunft": {"label": "Brunft", "order": 11},
    "neozoon": {"label": "Neozoon", "order": 12},
    "geschuetzt": {"label": "Geschützt", "order": 13},
    "giftig": {"label": "Giftig", "order": 14},
    "haeufig": {"label": "Häufig", "order": 15},
    "vorsicht": {"label": "Besonders vorsichtig", "order": 16},
    "fruehling": {"label": "Im Frühling", "order": 17},
    "winter": {"label": "Im Winter", "order": 18},
    "regen": {"label": "Bei Regen aktiv", "order": 19},
    "legende": {"label": "Legendäre Sichtung", "order": 20},
}

_TAXONOMIC_TAGS = {
    "bird", "mammal", "butterfly", "insect", "amphibian", "reptile", "fish",
    "greifvogel", "raubtier", "eule", "libelle", "specht", "singvogel",
    "kaefer", "käfer", "hautfluegler", "hautflügler", "fledermaus",
    "heuschrecke", "greifvögel", "raubtiere", "eulen", "libellen",
    "spechtvögel", "singvögel", "fledermäuse", "heuschrecken",
}

_HABITAT_TAGS = {
    "alpen": "alps", "moor": "moor", "gewaesser": "water", "meer": "ocean",
}

_REGION_TAGS = {
    "afrika": "africa", "arktis": "arctic", "expedition": "world",
}


def group_from_taxonomy(class_name: str, order_name: str, fallback: str) -> str:
    cls = (class_name or "").casefold()
    order = (order_name or "").casefold()
    if any(value in cls for value in ("aves", "vögel", "voegel")):
        return "bird"
    if any(value in cls for value in ("mammalia", "säuget", "saeuget")):
        return "mammal"
    if any(value in cls for value in ("insecta", "insekten")):
        if any(value in order for value in ("lepidoptera", "schmetterling")):
            return "butterfly"
        return "insect"
    if "amphibia" in cls or "amphib" in cls:
        return "amphibian"
    if "reptilia" in cls or "reptil" in cls:
        return "reptile"
    if any(value in cls for value in (
        "actinopteri", "actinopterygii", "chondrichthyes", "strahlenflosser",
        "knorpelfische", "fische",
    )):
        return "fish"
    return fallback if fallback in GROUPS else "other"


def normalize_species_metadata(
    *,
    group: str,
    class_name: str | None,
    order_name: str,
    habitats: list[str] | None,
    regions: list[str] | None,
    tags: list[str] | None,
    activity: str | None,
) -> dict:
    clean_tags = list(dict.fromkeys(str(tag).strip() for tag in (tags or []) if str(tag).strip()))
    clean_habitats = list(dict.fromkeys(habitats or []))
    clean_regions = list(dict.fromkeys(regions or []))

    if activity not in ACTIVITIES:
        activity = "nocturnal" if (
            "night" in clean_habitats
            or any(tag in {"nacht", "nachtaktiv", "daemmerung"} for tag in clean_tags)
        ) else "diurnal"
    clean_habitats = [value for value in clean_habitats if value != "night"]
    for tag, habitat in _HABITAT_TAGS.items():
        if tag in clean_tags and habitat not in clean_habitats:
            clean_habitats.append(habitat)
    for tag, region in _REGION_TAGS.items():
        if tag in clean_tags and region not in clean_regions:
            clean_regions.append(region)

    def token(value: str) -> str:
        folded = unicodedata.normalize("NFKD", value.casefold())
        return "".join(char for char in folded if char.isalnum() and not unicodedata.combining(char))

    structural = (
        {token(value) for value in _TAXONOMIC_TAGS}
        | set(_HABITAT_TAGS)
        | set(_REGION_TAGS)
        | {"nacht", "nachtaktiv", "daemmerung"}
    )
    order_token = token(order_name or "")
    clean_tags = [
        tag for tag in clean_tags
        if token(tag) not in structural and (not order_token or token(tag) != order_token)
    ]
    clean_class = (class_name or GROUP_CLASSES.get(group, "Animalia")).strip()
    clean_order = "" if (order_name or "").strip().casefold() == "keine" else (order_name or "").strip()
    clean_group = group_from_taxonomy(clean_class, clean_order, group)
    if clean_class.casefold() in {
        "vögel", "voegel", "säugetiere", "saeugetiere", "insekten",
        "amphibien", "reptilien", "fische", "actinopteri",
    }:
        clean_class = GROUP_CLASSES[clean_group]
    return {
        "group": clean_group,
        "class_name": clean_class,
        "order_name": clean_order,
        "habitats": clean_habitats,
        "regions": clean_regions,
        "tags": clean_tags,
        "activity": activity,
    }

DIFFICULTIES: dict[int, dict] = {
    1: {"label": "Häufig", "key": "common", "order": 1},
    2: {"label": "Ungewöhnlich", "key": "uncommon", "order": 2},
    3: {"label": "Anspruchsvoll", "key": "challenging", "order": 3},
    4: {"label": "Sehr selten", "key": "rare", "order": 4},
    5: {"label": "Legendär", "key": "legendary", "order": 5},
}

STATUSES: dict[str, dict] = {
    "locked": {"label": "Noch nicht fotografiert", "icon": "🔒", "order": 1},
    "unlocked": {"label": "Fotografiert", "icon": "✓", "order": 2},
}


def group_label(key: str) -> str:
    return GROUPS.get(key, {}).get("label", key)


def habitat_label(key: str) -> str:
    return HABITATS.get(key, {}).get("label", key)


def region_label(key: str) -> str:
    return REGIONS.get(key, {}).get("label", key)


def difficulty_label(value: int) -> str:
    return DIFFICULTIES.get(value, {}).get("label", str(value))


def meta_payload() -> dict:
    return {
        "groups": [
            {"value": k, **v} for k, v in sorted(GROUPS.items(), key=lambda i: i[1]["order"])
        ],
        "classes": [
            {"value": key, "label": label}
            for key, label in CLASS_LABELS.items()
        ],
        "habitats": [
            {"value": k, **v} for k, v in sorted(HABITATS.items(), key=lambda i: i[1]["order"])
        ],
        "regions": [
            {"value": k, **v} for k, v in sorted(REGIONS.items(), key=lambda i: i[1]["order"])
        ],
        "activities": [
            {"value": k, **v} for k, v in sorted(ACTIVITIES.items(), key=lambda i: i[1]["order"])
        ],
        "tags": [
            {"value": k, **v} for k, v in sorted(TAGS.items(), key=lambda i: i[1]["order"])
        ],
        "difficulties": [
            {"value": k, **v} for k, v in sorted(DIFFICULTIES.items(), key=lambda i: i[1]["order"])
        ],
        "statuses": [
            {"value": k, **v} for k, v in sorted(STATUSES.items(), key=lambda i: i[1]["order"])
        ],
    }
