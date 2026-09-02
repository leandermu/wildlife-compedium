"""Data-driven achievement & quest engine.

Definitions are plain dicts (loadable from JSON later — see DEFINITIONS_FILE).
A definition never contains hard-coded counts of the collection; every target is
evaluated against the live database.

Rule kinds
----------
count      : collect N species matching a filter
species    : collect a specific list of species (by slug)
photos     : take N photos in total (optionally filtered)
locations  : visit N distinct locations
seasonal   : collect N species with photos taken between two months
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from .models import Profile, ProfileAchievementState, Species, UserPhoto
from .queries import SpeciesQuery
from .vocab import GROUPS

DEFINITIONS_FILE = Path(__file__).with_name("data") / "achievements.json"

MALE_NAMES = {
    "Vogelbeobachterin": "Vogelbeobachter",
    "Spurenleserin": "Spurenleser",
    "Schmetterlingssammlerin": "Schmetterlingssammler",
    "Freundin der Kleinen": "Freund der Kleinen",
    "Bayerische Heimatforscherin": "Bayerischer Heimatforscher",
    "Waldgängerin": "Waldgänger",
    "Legendenjägerin": "Legendenjäger",
    "Greifvogelspezialistin": "Greifvogelspezialist",
    "Meisterin der Nacht": "Meister der Nacht",
    "Alpenjägerin": "Alpenjäger",
    "Entdeckerin": "Entdecker",
}


def _tiered(id_, name, desc, icon, category, filt, thresholds):
    return {
        "id": id_, "name": name, "description": desc, "icon": icon,
        "kind": "achievement", "category": category,
        "rule": {"type": "count", "filter": filt, "thresholds": thresholds},
    }


BUILTIN: list[dict[str, Any]] = [
    _tiered("bird_watcher", "Vogelbeobachterin",
            "Sammle Vogelarten für dein Compedium.", "🐦", "Sammlung",
            {"group": ["bird"]}, [10, 25, 50, 100, 250]),
    _tiered("mammal_tracker", "Spurenleserin",
            "Säugetiere sind scheu – jedes Foto zählt doppelt.", "🦌", "Sammlung",
            {"group": ["mammal"]}, [5, 10, 25, 50]),
    _tiered("butterfly_collector", "Schmetterlingssammlerin",
            "Falter über Falter.", "🦋", "Sammlung",
            {"group": ["butterfly"]}, [10, 25, 50, 100]),
    _tiered("insect_friend", "Freundin der Kleinen",
            "Insekten und andere Sechsbeiner.", "🐝", "Sammlung",
            {"group": ["insect"]}, [5, 10, 25, 50]),
    _tiered("bavaria_native", "Bayerische Heimatforscherin",
            "Arten, die in Bayern vorkommen.", "🥨", "Region",
            {"region": ["bavaria"]}, [25, 50, 100, 250]),
    _tiered("water_world", "Am Wasser",
            "Arten an Seen, Flüssen und Bächen.", "💧", "Lebensraum",
            {"habitat": ["water"]}, [10, 25, 50]),
    _tiered("forest_walker", "Waldgängerin",
            "Arten des Waldes.", "🌲", "Lebensraum",
            {"habitat": ["forest"]}, [10, 25, 50]),
    _tiered("legend_hunter", "Legendenjägerin",
            "Arten der höchsten Schwierigkeitsstufe.", "✨", "Herausforderung",
            {"difficulty": [5]}, [1, 3, 5, 10]),
    _tiered("raptor_specialist", "Greifvogelspezialistin",
            "Adler, Bussarde, Milane und Falken.", "🦅", "Herausforderung",
            {"tag": ["greifvogel"]}, [3, 6, 10]),
    {
        "id": "night_master", "name": "Meisterin der Nacht",
        "description": "Fotografiere die Nachtjäger Bayerns.",
        "icon": "🌙", "kind": "achievement", "category": "Herausforderung",
        "rule": {"type": "species", "slugs": [
            "waldkauz", "uhu", "schleiereule", "waldohreule", "grosses-mausohr"]},
    },
    {
        "id": "alpine_hunter", "name": "Alpenjägerin",
        "description": "Die Hochlagen fordern Kondition und Geduld.",
        "icon": "🏔", "kind": "achievement", "category": "Herausforderung",
        "rule": {"type": "species", "slugs": [
            "steinadler", "alpenmurmeltier", "gaemse", "alpensteinbock",
            "alpendohle", "alpenschneehuhn", "bartgeier"]},
    },
    {
        "id": "woodpecker_trio", "name": "Spechtwald",
        "description": "Drei Spechte, drei Trommelwirbel.",
        "icon": "🪵", "kind": "achievement", "category": "Sammlung",
        "rule": {"type": "species", "slugs": ["buntspecht", "schwarzspecht", "gruenspecht"]},
    },
    {
        "id": "photo_volume", "name": "Fleißige Linse",
        "description": "Gesamtzahl deiner Aufnahmen im Compedium.",
        "icon": "📷", "kind": "achievement", "category": "Sammlung",
        "rule": {"type": "photos", "thresholds": [10, 50, 100, 500, 1000]},
    },
    {
        "id": "explorer", "name": "Entdeckerin",
        "description": "Fotografiere an verschiedenen Orten.",
        "icon": "📍", "kind": "achievement", "category": "Sammlung",
        "rule": {"type": "locations", "thresholds": [3, 10, 25, 50]},
    },
    # ------------------------------------------------------------- Quests --
    {
        "id": "quest_five_owls", "name": "Die fünf Eulen",
        "description": "Waldkauz, Uhu, Schleiereule, Waldohreule und Sperlingskauz.",
        "icon": "🦉", "kind": "quest", "category": "Fotoquest",
        "rule": {"type": "species", "slugs": [
            "waldkauz", "uhu", "schleiereule", "waldohreule", "sperlingskauz"]},
    },
    {
        "id": "quest_spring_bavaria", "name": "Frühling in Bayern",
        "description": "Fotografiere 20 Arten zwischen März und Mai.",
        "icon": "🌸", "kind": "quest", "category": "Fotoquest",
        "rule": {"type": "seasonal", "from_month": 3, "to_month": 5, "target": 20},
    },
    {
        "id": "quest_water_worlds", "name": "Wasserwelten",
        "description": "Fotografiere 15 Arten an Seen, Flüssen und Bächen.",
        "icon": "🌊", "kind": "quest", "category": "Fotoquest",
        "rule": {"type": "count", "filter": {"habitat": ["water"]}, "thresholds": [15]},
    },
    {
        "id": "quest_small_hunters", "name": "Kleine Jäger",
        "description": "Fotografiere 10 Raubtiere.",
        "icon": "🦊", "kind": "quest", "category": "Fotoquest",
        "rule": {"type": "count", "filter": {"tag": ["raubtier"]}, "thresholds": [10]},
    },
    {
        "id": "quest_winter", "name": "Winterlicht",
        "description": "Fotografiere 10 Arten zwischen Dezember und Februar.",
        "icon": "❄️", "kind": "quest", "category": "Fotoquest",
        "rule": {"type": "seasonal", "from_month": 12, "to_month": 2, "target": 10},
    },
]


def load_definitions() -> list[dict[str, Any]]:
    """Built-ins plus anything in data/achievements.json (same shape).
    A file entry with an existing id overrides the built-in."""
    defs = {d["id"]: d for d in BUILTIN}
    if DEFINITIONS_FILE.exists():
        try:
            extra = json.loads(DEFINITIONS_FILE.read_text(encoding="utf-8"))
            for d in extra:
                defs[d["id"]] = d
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
    return list(defs.values())


# ------------------------------------------------------------- evaluation --
def _encounter_filters(model, profile_id: int, wild_only: bool):
    filters = [model.profile_id == profile_id]
    if wild_only:
        filters.append(func.coalesce(model.encounter_type, "wild") == "wild")
    return filters


def _collected_count(
    db: Session, filt: dict[str, Any], profile_id: int, wild_only: bool
) -> int:
    sq = SpeciesQuery(profile_id, wild_only)
    stmt = sq.apply_filters(
        sq.base(func.count(func.distinct(Species.id))),
        group=filt.get("group"), habitat=filt.get("habitat"), region=filt.get("region"),
        family=filt.get("family"), tag=filt.get("tag"), difficulty=filt.get("difficulty"),
        status=["unlocked"],
    )
    return int(db.execute(stmt).scalar() or 0)


def _species_progress(
    db: Session, slugs: list[str], profile_id: int, wild_only: bool
) -> tuple[int, list[dict]]:
    rows = db.execute(
        select(Species.slug, Species.common_name, func.count(UserPhoto.id))
        .outerjoin(
            UserPhoto,
            and_(
                UserPhoto.species_id == Species.id,
                UserPhoto.profile_id == profile_id,
                *(
                    [func.coalesce(UserPhoto.encounter_type, "wild") == "wild"]
                    if wild_only else []
                ),
            ),
        )
        .where(Species.slug.in_(slugs))
        .group_by(Species.id)
    ).all()
    found = {slug: (name, cnt) for slug, name, cnt in rows}
    detail = []
    done = 0
    for slug in slugs:
        name, cnt = found.get(slug, (slug, 0))
        ok = cnt > 0
        done += 1 if ok else 0
        detail.append({"slug": slug, "common_name": name, "collected": ok})
    return done, detail


def _seasonal_progress(
    db: Session, from_month: int, to_month: int, profile_id: int, wild_only: bool
) -> int:
    months = (
        list(range(from_month, to_month + 1))
        if from_month <= to_month
        else list(range(from_month, 13)) + list(range(1, to_month + 1))
    )
    rows = db.execute(
        select(UserPhoto.species_id, UserPhoto.date).where(
            UserPhoto.date.is_not(None),
            *_encounter_filters(UserPhoto, profile_id, wild_only),
        )
    ).all()
    return len({sid for sid, d in rows if d and d.month in months})


def evaluate(db: Session, profile_id: int) -> list[dict[str, Any]]:
    definitions = load_definitions()
    profile = db.get(Profile, profile_id)
    wild_only = bool(profile and profile.exclude_captive_from_progress)
    use_male_names = profile is None or (profile.gender or "male") == "male"
    state = {
        s.achievement_id: s
        for s in db.execute(
            select(ProfileAchievementState).where(
                ProfileAchievementState.profile_id == profile_id
            )
        ).scalars()
    }
    results: list[dict[str, Any]] = []
    dirty = False

    for d in definitions:
        rule = d["rule"]
        rtype = rule["type"]
        species_detail: list[dict] = []
        tiers: list[dict] = []

        if rtype == "count":
            progress = _collected_count(
                db, rule.get("filter", {}), profile_id, wild_only
            )
            thresholds = rule.get("thresholds", [1])
        elif rtype == "species":
            progress, species_detail = _species_progress(
                db, rule["slugs"], profile_id, wild_only
            )
            thresholds = [len(rule["slugs"])]
        elif rtype == "photos":
            progress = int(db.execute(
                select(func.count(UserPhoto.id)).where(
                    *_encounter_filters(UserPhoto, profile_id, wild_only)
                )
            ).scalar() or 0)
            thresholds = rule.get("thresholds", [1])
        elif rtype == "locations":
            progress = int(
                db.execute(
                    select(func.count(func.distinct(func.lower(UserPhoto.location_name))))
                    .where(
                        UserPhoto.location_name != "",
                        UserPhoto.profile_id == profile_id,
                        *(
                            [func.coalesce(UserPhoto.encounter_type, "wild") == "wild"]
                            if wild_only else []
                        ),
                    )
                ).scalar()
                or 0
            )
            thresholds = rule.get("thresholds", [1])
        elif rtype == "seasonal":
            progress = _seasonal_progress(
                db, rule["from_month"], rule["to_month"], profile_id, wild_only
            )
            thresholds = [rule.get("target", 1)]
        else:
            continue

        thresholds = sorted(thresholds)
        reached = [t for t in thresholds if progress >= t]
        current_tier = len(reached)
        # the target shown is the next unreached tier, or the last one when done
        target = thresholds[current_tier] if current_tier < len(thresholds) else thresholds[-1]
        unlocked = current_tier > 0
        for index, t in enumerate(thresholds):
            tiers.append({
                "threshold": t,
                "label": f"Level {index + 1}",
                "unlocked": progress >= t,
            })

        st = state.get(d["id"])
        unlocked_at = st.unlocked_at if st else None
        if unlocked and (st is None or st.tier < current_tier):
            if st is None:
                st = ProfileAchievementState(
                    profile_id=profile_id,
                    achievement_id=d["id"],
                    tier=current_tier,
                )
                db.add(st)
                unlocked_at = st.unlocked_at = dt.datetime.now(dt.timezone.utc)
            else:
                st.tier = current_tier
                st.unlocked_at = dt.datetime.now(dt.timezone.utc)
                unlocked_at = st.unlocked_at
            dirty = True

        results.append({
            "id": d["id"],
            "name": MALE_NAMES.get(d["name"], d["name"]) if use_male_names else d["name"],
            "description": d["description"],
            "icon": d.get("icon", "🏅"), "kind": d.get("kind", "achievement"),
            "category": d.get("category", ""),
            "progress": progress, "target": target,
            "level": current_tier + 1,
            "unlocked": unlocked, "unlocked_at": unlocked_at,
            "tiers": tiers, "species": species_detail,
            "starts_on": d.get("starts_on"), "ends_on": d.get("ends_on"),
        })

    if dirty:
        db.commit()
    return results


def summary(db: Session, profile_id: int) -> tuple[int, int]:
    items = evaluate(db, profile_id)
    return sum(1 for i in items if i["unlocked"]), len(items)
