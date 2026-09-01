"""Human-facing vocabulary. Single source of truth — the frontend pulls these
labels from /api/meta so new habitats or groups never need a frontend release."""

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
    "night": {"label": "Nacht", "icon": "🌙", "order": 11},
    "savanna": {"label": "Savanne", "icon": "🦁", "order": 12},
    "rainforest": {"label": "Regenwald", "icon": "🌴", "order": 13},
    "ocean": {"label": "Offenes Meer", "icon": "🌊", "order": 14},
}

REGIONS: dict[str, dict] = {
    "bavaria": {"label": "Bayern", "icon": "🥨", "order": 1},
    "germany": {"label": "Deutschland", "icon": "🇩🇪", "order": 2},
    "europe": {"label": "Europa", "icon": "🌍", "order": 3},
    "world": {"label": "Welt & Expedition", "icon": "🧭", "order": 4},
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
        "habitats": [
            {"value": k, **v} for k, v in sorted(HABITATS.items(), key=lambda i: i[1]["order"])
        ],
        "regions": [
            {"value": k, **v} for k, v in sorted(REGIONS.items(), key=lambda i: i[1]["order"])
        ],
        "difficulties": [
            {"value": k, **v} for k, v in sorted(DIFFICULTIES.items(), key=lambda i: i[1]["order"])
        ],
        "statuses": [
            {"value": k, **v} for k, v in sorted(STATUSES.items(), key=lambda i: i[1]["order"])
        ],
    }
