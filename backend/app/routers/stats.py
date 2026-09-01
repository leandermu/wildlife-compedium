from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import Text, case, func, select
from sqlalchemy.orm import Session

from .. import achievements as ach
from ..db import get_db
from ..models import Observation, Profile, Species, UserPhoto
from ..profiles import CurrentProfile
from ..queries import SpeciesQuery, display_photos
from ..schemas import ActivityOut, ChallengeHint, DashboardOut, ProgressBucket, RecentUnlock
from ..storage import media_url
from ..vocab import DIFFICULTIES, GROUPS, REGIONS, meta_payload

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/meta")
def meta() -> dict:
    return meta_payload()


def _bucket_counts(db: Session, profile_id: int) -> list[tuple]:
    """species rows with their photo count — one query, used for every bucket."""
    sq = SpeciesQuery(profile_id)
    stmt = sq.apply_filters(
        sq.base(Species.group, Species.regions, Species.difficulty, sq.photo_count)
    )
    return db.execute(stmt).all()


def _recent_activity(db: Session, limit: int = 18) -> list[ActivityOut]:
    """Build a cross-profile feed from the canonical collection records."""
    profiles = {
        profile.id: profile
        for profile in db.execute(select(Profile)).scalars()
    }
    entries: list[ActivityOut] = []

    def add(kind: str, profile_id: int | None, species: Species, occurred_at) -> None:
        profile = profiles.get(profile_id)
        if profile is None:
            return
        entries.append(ActivityOut(
            kind=kind,
            profile_id=profile.id,
            profile_name=profile.name,
            profile_avatar=profile.avatar or "🐾",
            species_id=species.id,
            species_slug=species.slug,
            species_name=species.common_name,
            occurred_at=occurred_at,
        ))

    photos = db.execute(
        select(UserPhoto, Species)
        .join(Species, Species.id == UserPhoto.species_id)
        .order_by(UserPhoto.created_at.desc(), UserPhoto.id.desc())
        .limit(limit)
    ).all()
    for photo, species in photos:
        add("photographed", photo.profile_id, species, photo.created_at)

    observations = db.execute(
        select(Observation, Species)
        .join(Species, Species.id == Observation.species_id)
        .where(~Observation.photos.any())
        .order_by(Observation.created_at.desc(), Observation.id.desc())
        .limit(limit)
    ).all()
    for observation, species in observations:
        add("seen", observation.profile_id, species, observation.created_at)

    additions = db.execute(
        select(Species)
        .where(Species.created_by_profile_id.is_not(None))
        .order_by(Species.created_at.desc(), Species.id.desc())
        .limit(limit)
    ).scalars()
    for species in additions:
        add("added", species.created_by_profile_id, species, species.created_at)

    return sorted(
        entries,
        key=lambda entry: (entry.occurred_at, entry.species_id),
        reverse=True,
    )[:limit]


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(
    db: Annotated[Session, Depends(get_db)], profile: CurrentProfile
) -> DashboardOut:
    rows = _bucket_counts(db, profile.id)

    total = len(rows)
    collected = sum(1 for r in rows if r[3] > 0)
    by_group: dict[str, list[int]] = {}
    by_region: dict[str, list[int]] = {}
    by_difficulty: dict[int, list[int]] = {}
    for group, regions, difficulty, pc in rows:
        g = by_group.setdefault(group, [0, 0])
        g[1] += 1
        g[0] += 1 if pc > 0 else 0
        for region in regions or []:
            r = by_region.setdefault(region, [0, 0])
            r[1] += 1
            r[0] += 1 if pc > 0 else 0
        d = by_difficulty.setdefault(difficulty, [0, 0])
        d[1] += 1
        d[0] += 1 if pc > 0 else 0

    group_buckets = [
        ProgressBucket(key=k, label=GROUPS.get(k, {}).get("label", k), collected=v[0], total=v[1])
        for k, v in sorted(by_group.items(), key=lambda i: GROUPS.get(i[0], {}).get("order", 99))
    ]
    region_buckets = [
        ProgressBucket(key=k, label=REGIONS.get(k, {}).get("label", k), collected=v[0], total=v[1])
        for k, v in sorted(by_region.items(), key=lambda i: REGIONS.get(i[0], {}).get("order", 99))
    ]
    difficulty_buckets = [
        ProgressBucket(key=str(k), label=DIFFICULTIES.get(k, {}).get("label", str(k)),
                       collected=v[0], total=v[1])
        for k, v in sorted(by_difficulty.items())
    ]

    # last unlocked species, newest first
    recent_rows = db.execute(
        select(UserPhoto.species_id, func.max(UserPhoto.created_at).label("last"))
        .where(UserPhoto.profile_id == profile.id)
        .group_by(UserPhoto.species_id)
        .order_by(func.max(UserPhoto.created_at).desc())
        .limit(8)
    ).all()
    recent: list[RecentUnlock] = []
    if recent_rows:
        ids = [r[0] for r in recent_rows]
        species = {
            s.id: s for s in db.execute(select(Species).where(Species.id.in_(ids))).scalars()
        }
        photos = display_photos(db, ids, profile.id)
        for sid, _last in recent_rows:
            sp = species.get(sid)
            if not sp:
                continue
            p = photos.get(sid)
            recent.append(RecentUnlock(
                species_id=sid, slug=sp.slug, common_name=sp.common_name,
                scientific_name=sp.scientific_name,
                photo_url=media_url(p.display_key or p.storage_key) if p else None,
                thumb_url=media_url(p.thumb_key or p.display_key or p.storage_key) if p else None,
                date=p.date if p else None,
                location_name=p.location_name if p else "",
            ))

    # "Nächste Herausforderungen": families/habitats where she is closest to done
    challenges: list[ChallengeHint] = []
    sq = SpeciesQuery(profile.id)
    fam_stmt = sq.apply_filters(
        sq.base(
            Species.family,
            Species.group,
            func.count(Species.id),
            func.sum(case((sq.photo_count > 0, 1), else_=0)),
        )
    ).group_by(Species.family, Species.group)
    fam_rows = db.execute(fam_stmt).all()
    for family, group, cnt, coll in fam_rows:
        coll = int(coll or 0)
        if not family or cnt < 3 or coll == 0 or coll >= cnt:
            continue
        challenges.append(ChallengeHint(
            label=f"noch {cnt - coll} × {family}",
            remaining=cnt - coll,
            filter={"family": family, "group": group},
        ))
    challenges.sort(key=lambda c: c.remaining)
    challenges = challenges[:6]

    unlocked_ach, total_ach = ach.summary(db, profile.id)

    return DashboardOut(
        total_species=total,
        collected=collected,
        photo_count=int(db.execute(
            select(func.count(UserPhoto.id)).where(UserPhoto.profile_id == profile.id)
        ).scalar() or 0),
        observation_count=int(db.execute(
            select(func.count(Observation.id)).where(Observation.profile_id == profile.id)
        ).scalar() or 0),
        by_group=group_buckets,
        by_region=region_buckets,
        by_difficulty=difficulty_buckets,
        recent=recent,
        activity=_recent_activity(db),
        challenges=challenges,
        achievements_unlocked=unlocked_ach,
        achievements_total=total_ach,
    )
