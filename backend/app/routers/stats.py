from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import Text, case, func, select
from sqlalchemy.orm import Session

from .. import achievements as ach
from ..db import get_db
from ..models import Observation, Species, UserPhoto
from ..queries import MASTERED_MIN_PHOTOS, SpeciesQuery, display_photos
from ..schemas import ChallengeHint, DashboardOut, ProgressBucket, RecentUnlock
from ..storage import media_url
from ..vocab import DIFFICULTIES, GROUPS, REGIONS, meta_payload

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/meta")
def meta() -> dict:
    return meta_payload()


def _bucket_counts(db: Session) -> list[tuple]:
    """species rows with their photo count — one query, used for every bucket."""
    sq = SpeciesQuery()
    stmt = sq.apply_filters(
        sq.base(Species.group, Species.regions, Species.difficulty, sq.photo_count, sq.has_best)
    )
    return db.execute(stmt).all()


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(db: Annotated[Session, Depends(get_db)]) -> DashboardOut:
    rows = _bucket_counts(db)

    total = len(rows)
    collected = sum(1 for r in rows if r[3] > 0)
    mastered = sum(1 for r in rows if r[3] >= MASTERED_MIN_PHOTOS and r[4])

    by_group: dict[str, list[int]] = {}
    by_region: dict[str, list[int]] = {}
    by_difficulty: dict[int, list[int]] = {}
    for group, regions, difficulty, pc, _hb in rows:
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
        photos = display_photos(db, ids)
        for sid, _last in recent_rows:
            sp = species.get(sid)
            if not sp:
                continue
            p = photos.get(sid)
            recent.append(RecentUnlock(
                species_id=sid, slug=sp.slug, common_name=sp.common_name,
                scientific_name=sp.scientific_name,
                photo_url=media_url(p.storage_key) if p else None,
                thumb_url=media_url(p.thumb_key or p.storage_key) if p else None,
                date=p.date if p else None,
                location_name=p.location_name if p else "",
            ))

    # "Nächste Herausforderungen": families/habitats where she is closest to done
    challenges: list[ChallengeHint] = []
    sq = SpeciesQuery()
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

    unlocked_ach, total_ach = ach.summary(db)

    return DashboardOut(
        total_species=total,
        collected=collected,
        mastered=mastered,
        photo_count=int(db.execute(select(func.count(UserPhoto.id))).scalar() or 0),
        observation_count=int(db.execute(select(func.count(Observation.id))).scalar() or 0),
        by_group=group_buckets,
        by_region=region_buckets,
        by_difficulty=difficulty_buckets,
        recent=recent,
        challenges=challenges,
        achievements_unlocked=unlocked_ach,
        achievements_total=total_ach,
    )
