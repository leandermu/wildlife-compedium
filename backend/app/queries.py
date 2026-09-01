"""Species querying + serialisation.

Everything here is written so that a page of species costs a constant number of
SQL statements no matter how many species or photos exist: one aggregate join
for the counters, one query for the display photos of the current page.
"""

from __future__ import annotations

from typing import Any, Iterable, Sequence

from sqlalchemy import Select, Text, and_, case, func, or_, select
from sqlalchemy.orm import Session

from .models import Observation, Species, UserPhoto
from .schemas import SpeciesDetail, SpeciesListItem
from .storage import media_url
from .text import normalize
from .vocab import GROUPS

def _photo_agg(profile_id: int):
    return (
        select(
            UserPhoto.species_id.label("sid"),
            func.count(UserPhoto.id).label("photo_count"),
            func.max(UserPhoto.created_at).label("last_photo_at"),
        )
        .where(UserPhoto.profile_id == profile_id)
        .group_by(UserPhoto.species_id)
        .subquery()
    )


def _obs_agg(profile_id: int):
    return (
        select(
            Observation.species_id.label("sid"),
            func.count(Observation.id).label("obs_count"),
        )
        .where(Observation.profile_id == profile_id)
        .group_by(Observation.species_id)
        .subquery()
    )


def status_expr(photo_count):
    return case(
        (photo_count == 0, "locked"),
        else_="unlocked",
    )


def derive_status(photo_count: int) -> str:
    return "locked" if photo_count == 0 else "unlocked"


class SpeciesQuery:
    """Builder shared by the list endpoint, the facet counts and the exports."""

    def __init__(self, profile_id: int) -> None:
        self.profile_id = profile_id
        self.photos = _photo_agg(profile_id)
        self.obs = _obs_agg(profile_id)
        self.photo_count = func.coalesce(self.photos.c.photo_count, 0)
        self.obs_count = func.coalesce(self.obs.c.obs_count, 0)
        self.status = status_expr(self.photo_count)

    def base(self, *cols) -> Select:
        stmt = select(*cols) if cols else select(Species)
        return stmt.outerjoin(self.photos, self.photos.c.sid == Species.id).outerjoin(
            self.obs, self.obs.c.sid == Species.id
        )

    # ------------------------------------------------------------- filters --
    def apply_filters(
        self,
        stmt: Select,
        *,
        q: str | None = None,
        group: Sequence[str] | None = None,
        habitat: Sequence[str] | None = None,
        region: Sequence[str] | None = None,
        family: Sequence[str] | None = None,
        tag: Sequence[str] | None = None,
        difficulty: Sequence[int] | None = None,
        status: Sequence[str] | None = None,
        seen: Sequence[str] | None = None,
        include_inactive: bool = False,
    ) -> Select:
        if not include_inactive:
            stmt = stmt.where(Species.active.is_(True))
        if q:
            for token in normalize(q).split():
                stmt = stmt.where(Species.search_text.like(f"%{token}%"))
        if group:
            stmt = stmt.where(Species.group.in_(list(group)))
        if family:
            stmt = stmt.where(Species.family.in_(list(family)))
        if difficulty:
            stmt = stmt.where(Species.difficulty.in_([int(d) for d in difficulty]))
        # JSON list columns: SQLite and Postgres both handle this reliably as a
        # substring match on the serialised array, which is fine at this scale.
        for values, column in ((habitat, Species.habitats), (region, Species.regions), (tag, Species.tags)):
            if values:
                stmt = stmt.where(
                    or_(
                        *[
                            func.lower(func.cast(column, Text)).like(f'%"{v.lower()}"%')
                            for v in values
                        ]
                    )
                )
        if status:
            wanted = [s for s in status if s in {"locked", "unlocked"}]
            if wanted:
                conds = []
                for s in wanted:
                    if s == "locked":
                        conds.append(self.photo_count == 0)
                    elif s == "unlocked":
                        conds.append(self.photo_count > 0)
                stmt = stmt.where(or_(*conds))
        if seen:
            wanted_seen = {value for value in seen if value in {"seen", "unseen"}}
            has_encounter = or_(self.photo_count > 0, self.obs_count > 0)
            if wanted_seen == {"seen"}:
                stmt = stmt.where(has_encounter)
            elif wanted_seen == {"unseen"}:
                stmt = stmt.where(and_(self.photo_count == 0, self.obs_count == 0))
        return stmt

    def apply_sort(self, stmt: Select, sort: str) -> Select:
        if sort == "name":
            return stmt.order_by(Species.common_name.asc())
        if sort == "name_desc":
            return stmt.order_by(Species.common_name.desc())
        if sort == "difficulty":
            return stmt.order_by(Species.difficulty.asc(), Species.common_name.asc())
        if sort == "difficulty_desc":
            return stmt.order_by(Species.difficulty.desc(), Species.common_name.asc())
        if sort == "scientific":
            return stmt.order_by(Species.scientific_name.asc())
        if sort == "created_desc":
            return stmt.order_by(Species.created_at.desc(), Species.id.desc())
        if sort == "recent":
            return stmt.order_by(
                self.photos.c.last_photo_at.desc().nullslast(), Species.common_name.asc()
            )
        if sort == "status":
            return stmt.order_by(self.photo_count.desc(), Species.common_name.asc())
        # Systematic field-guide order. Do not use sort_index here: imported
        # legacy rows have values that newly created species cannot know.
        group_order = case(
            {key: meta.get("order", 99) for key, meta in GROUPS.items()},
            value=Species.group,
            else_=99,
        )
        return stmt.order_by(
            group_order.asc(), Species.order_name.asc(), Species.family.asc(),
            Species.common_name.asc(),
        )


# ---------------------------------------------------------------- photos ----
def display_photos(
    db: Session, species_ids: Iterable[int], profile_id: int
) -> dict[int, UserPhoto]:
    """One photo per species for the card: the best photo, else the oldest."""
    ids = list(species_ids)
    if not ids:
        return {}
    rows = (
        db.execute(
            select(UserPhoto)
            .where(
                UserPhoto.species_id.in_(ids),
                UserPhoto.profile_id == profile_id,
            )
            .order_by(
                UserPhoto.species_id,
                UserPhoto.is_best_photo.desc(),
                UserPhoto.date.asc().nullslast(),
                UserPhoto.id.asc(),
            )
        )
        .scalars()
        .all()
    )
    out: dict[int, UserPhoto] = {}
    for photo in rows:
        out.setdefault(photo.species_id, photo)
    return out


def photo_out(photo: UserPhoto) -> dict[str, Any]:
    return {
        "id": photo.id,
        "species_id": photo.species_id,
        "observation_id": photo.observation_id,
        "url": media_url(photo.display_key or photo.storage_key),
        "thumb_url": media_url(photo.thumb_key or photo.display_key or photo.storage_key),
        "original_filename": photo.original_filename,
        "date": photo.date,
        "time": photo.time,
        "location_name": photo.location_name,
        "caption": photo.caption,
        "is_best_photo": photo.is_best_photo,
        "photo_metadata": photo.photo_metadata or {},
        "created_at": photo.created_at,
    }


# ----------------------------------------------------------- serialisation --
def to_list_item(
    sp: Species, photo_count: int, obs_count: int, photo: UserPhoto | None
) -> SpeciesListItem:
    return SpeciesListItem(
        id=sp.id,
        slug=sp.slug,
        common_name=sp.common_name,
        scientific_name=sp.scientific_name,
        group=sp.group,
        family=sp.family,
        difficulty=sp.difficulty,
        regions=sp.regions or [],
        habitats=sp.habitats or [],
        size=sp.size,
        reference_image_url=media_url(sp.reference_image),
        reference_thumb_url=media_url(sp.reference_thumb or sp.reference_image),
        status=derive_status(photo_count),
        photo_count=photo_count,
        observation_count=obs_count,
        best_photo_url=media_url(photo.display_key or photo.storage_key) if photo else None,
        best_photo_thumb_url=media_url(
            photo.thumb_key or photo.display_key or photo.storage_key
        ) if photo else None,
        display_photo_date=photo.date if photo else None,
        display_photo_location=photo.location_name if photo else "",
    )


def to_detail(sp: Species, profile_id: int) -> SpeciesDetail:
    profile_photos = [p for p in sp.photos if p.profile_id == profile_id]
    profile_observations = [o for o in sp.observations if o.profile_id == profile_id]
    photos = sorted(
        profile_photos,
        key=lambda p: (not p.is_best_photo, p.date is None, p.date or p.created_at.date()),
    )
    display = photos[0] if photos else None
    base = to_list_item(sp, len(profile_photos), len(profile_observations), display)
    return SpeciesDetail(
        **base.model_dump(),
        order_name=sp.order_name,
        description=sp.description,
        wingspan=sp.wingspan,
        weight=sp.weight,
        countries=sp.countries or [],
        tags=sp.tags or [],
        rarity=sp.rarity,
        reference_credit=sp.reference_credit,
        reference_source=sp.reference_source,
        distribution_map_url=media_url(sp.distribution_map),
        active=sp.active,
        photos=[photo_out(p) for p in photos],
        observations=sorted(
            [
                {
                    "id": o.id,
                    "species_id": o.species_id,
                    "date": o.date,
                    "time": o.time,
                    "location_name": o.location_name,
                    "latitude": o.latitude,
                    "longitude": o.longitude,
                    "notes": o.notes,
                    "has_photo": o.has_photo,
                    "created_at": o.created_at,
                }
                for o in profile_observations
            ],
            key=lambda o: (o["date"] is None, o["date"] or o["created_at"].date()),
            reverse=True,
        ),
    )
