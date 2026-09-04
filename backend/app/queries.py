"""Species querying + serialisation.

Everything here is written so that a page of species costs a constant number of
SQL statements no matter how many species or photos exist: one aggregate join
for the counters, one query for the display photos of the current page.
"""

from __future__ import annotations

from typing import Any, Iterable, Sequence

from sqlalchemy import Select, Text, and_, case, exists, func, or_, select
from sqlalchemy.orm import Session, selectinload

from .models import Observation, Profile, Species, UserPhoto
from .schemas import SpeciesDetail, SpeciesListItem
from .storage import media_url
from .text import normalize
from .vocab import GROUPS

def _photo_agg(profile_id: int | None, wild_only: bool = False):
    filters = [] if profile_id is None else [UserPhoto.profile_id == profile_id]
    if wild_only:
        filters.append(func.coalesce(UserPhoto.encounter_type, "wild") == "wild")
    photo_at = (
        func.cast(UserPhoto.date, Text)
        + " "
        + func.coalesce(func.cast(UserPhoto.time, Text), "00:00:00")
    )
    return (
        select(
            UserPhoto.species_id.label("sid"),
            func.count(UserPhoto.id).label("photo_count"),
            func.min(photo_at).label("first_photo_at"),
            func.max(UserPhoto.created_at).label("last_entry_at"),
        )
        .where(*filters)
        .group_by(UserPhoto.species_id)
        .subquery()
    )


def _obs_agg(profile_id: int | None, wild_only: bool = False):
    filters = [] if profile_id is None else [Observation.profile_id == profile_id]
    if wild_only:
        filters.append(func.coalesce(Observation.encounter_type, "wild") == "wild")
    return (
        select(
            Observation.species_id.label("sid"),
            func.count(Observation.id).label("obs_count"),
            func.max(Observation.created_at).label("last_entry_at"),
        )
        .where(*filters)
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

    def __init__(self, profile_id: int | None, exclude_captive: bool = False) -> None:
        self.profile_id = profile_id
        self.exclude_captive = exclude_captive
        self.photos = _photo_agg(profile_id, exclude_captive)
        self.obs = _obs_agg(profile_id, exclude_captive)
        self.raw_photos = _photo_agg(profile_id) if exclude_captive else self.photos
        self.raw_obs = _obs_agg(profile_id) if exclude_captive else self.obs
        self.photo_count = func.coalesce(self.photos.c.photo_count, 0)
        self.obs_count = func.coalesce(self.obs.c.obs_count, 0)
        self.raw_photo_count = func.coalesce(self.raw_photos.c.photo_count, 0)
        self.raw_obs_count = func.coalesce(self.raw_obs.c.obs_count, 0)
        self.status = status_expr(self.photo_count)

    def base(self, *cols) -> Select:
        stmt = select(*cols) if cols else select(Species)
        stmt = stmt.outerjoin(self.photos, self.photos.c.sid == Species.id).outerjoin(
            self.obs, self.obs.c.sid == Species.id
        )
        if self.exclude_captive:
            stmt = stmt.outerjoin(
                self.raw_photos, self.raw_photos.c.sid == Species.id
            ).outerjoin(self.raw_obs, self.raw_obs.c.sid == Species.id)
        return stmt

    # ------------------------------------------------------------- filters --
    def apply_filters(
        self,
        stmt: Select,
        *,
        q: str | None = None,
        group: Sequence[str] | None = None,
        class_name: Sequence[str] | None = None,
        order: Sequence[str] | None = None,
        habitat: Sequence[str] | None = None,
        region: Sequence[str] | None = None,
        family: Sequence[str] | None = None,
        tag: Sequence[str] | None = None,
        difficulty: Sequence[int] | None = None,
        status: Sequence[str] | None = None,
        seen: Sequence[str] | None = None,
        encounter: Sequence[str] | None = None,
        activity: Sequence[str] | None = None,
        include_inactive: bool = False,
    ) -> Select:
        if not include_inactive:
            stmt = stmt.where(Species.active.is_(True))
        if q:
            for token in normalize(q).split():
                stmt = stmt.where(Species.search_text.like(f"%{token}%"))
        if group:
            stmt = stmt.where(Species.group.in_(list(group)))
        if class_name:
            stmt = stmt.where(Species.class_name.in_(list(class_name)))
        if order:
            stmt = stmt.where(Species.order_name.in_(list(order)))
        if activity:
            stmt = stmt.where(Species.activity.in_(list(activity)))
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
        if encounter:
            wanted_encounters = {v for v in encounter if v in {"wild", "captive"}}
            encounter_conditions = []
            for value in wanted_encounters:
                photo_conditions = [
                    UserPhoto.species_id == Species.id,
                    func.coalesce(UserPhoto.encounter_type, "wild") == value,
                ]
                observation_conditions = [
                    Observation.species_id == Species.id,
                    func.coalesce(Observation.encounter_type, "wild") == value,
                ]
                if self.profile_id is not None:
                    photo_conditions.append(UserPhoto.profile_id == self.profile_id)
                    observation_conditions.append(
                        Observation.profile_id == self.profile_id
                    )
                photo_exists = exists(
                    select(UserPhoto.id).where(*photo_conditions)
                )
                observation_exists = exists(
                    select(Observation.id).where(*observation_conditions)
                )
                encounter_conditions.append(or_(photo_exists, observation_exists))
            if encounter_conditions:
                stmt = stmt.where(or_(*encounter_conditions))
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
        if sort == "updated_desc":
            return stmt.order_by(Species.updated_at.desc(), Species.id.desc())
        if sort == "recent":
            last_entry = case(
                (self.raw_photos.c.last_entry_at.is_(None), self.raw_obs.c.last_entry_at),
                (self.raw_obs.c.last_entry_at.is_(None), self.raw_photos.c.last_entry_at),
                (
                    self.raw_photos.c.last_entry_at >= self.raw_obs.c.last_entry_at,
                    self.raw_photos.c.last_entry_at,
                ),
                else_=self.raw_obs.c.last_entry_at,
            )
            return stmt.order_by(
                last_entry.desc().nullslast(), Species.common_name.asc()
            )
        if sort == "collected_first":
            return stmt.order_by(
                self.photos.c.first_photo_at.asc().nullslast(),
                Species.common_name.asc(),
            )
        if sort == "collected_last":
            return stmt.order_by(
                self.photos.c.first_photo_at.desc().nullslast(),
                Species.common_name.asc(),
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
    db: Session,
    species_ids: Iterable[int],
    profile_id: int | None,
    wild_only: bool = False,
) -> dict[int, UserPhoto]:
    """One photo per species for the card: the best photo, else the oldest."""
    ids = list(species_ids)
    if not ids:
        return {}
    filters = [UserPhoto.species_id.in_(ids)]
    if profile_id is not None:
        filters.append(UserPhoto.profile_id == profile_id)
    if wild_only:
        filters.append(func.coalesce(UserPhoto.encounter_type, "wild") == "wild")
    rows = (
        db.execute(
            select(UserPhoto)
            .options(selectinload(UserPhoto.observation))
            .where(*filters)
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
    preferred_profiles: dict[int, int | None] = {}
    if profile_id is None:
        preferred_profiles = dict(db.execute(
            select(Species.id, Species.shared_thumbnail_profile_id).where(
                Species.id.in_(ids)
            )
        ).all())
    out: dict[int, UserPhoto] = {}
    for photo in rows:
        selected = out.get(photo.species_id)
        preferred_profile_id = preferred_profiles.get(photo.species_id)
        if selected is None or (
            selected.profile_id != preferred_profile_id
            and photo.profile_id == preferred_profile_id
        ):
            out[photo.species_id] = photo
    return out


def photographer_profiles(
    db: Session,
    species_ids: Iterable[int],
    profile_id: int | None,
    selected_photos: dict[int, UserPhoto],
) -> dict[int, list[dict[str, Any]]]:
    """Photographers per species, with the displayed photo's owner first."""
    ids = list(species_ids)
    if not ids:
        return {}
    filters = [
        UserPhoto.species_id.in_(ids),
        Profile.is_shared.is_not(True),
    ]
    if profile_id is not None:
        filters.append(UserPhoto.profile_id == profile_id)
    rows = db.execute(
        select(UserPhoto, Profile)
        .options(selectinload(UserPhoto.observation))
        .join(Profile, Profile.id == UserPhoto.profile_id)
        .where(*filters)
        .order_by(
            UserPhoto.species_id,
            UserPhoto.profile_id,
            UserPhoto.is_best_photo.desc(),
            UserPhoto.date.asc().nullslast(),
            UserPhoto.id.asc(),
        )
    ).all()
    grouped: dict[int, list[dict[str, Any]]] = {}
    seen: set[tuple[int, int]] = set()
    for photo, owner in rows:
        key = (photo.species_id, owner.id)
        if key in seen:
            continue
        seen.add(key)
        selected = selected_photos.get(photo.species_id)
        latitude, longitude = photo_coordinates(photo)
        grouped.setdefault(photo.species_id, []).append({
            "id": owner.id,
            "name": owner.name,
            "avatar": owner.avatar or "🐾",
            "is_thumbnail": bool(selected and selected.id == photo.id),
            "photo_url": media_url(photo.display_key or photo.storage_key),
            "thumb_url": media_url(
                photo.thumb_key or photo.display_key or photo.storage_key
            ),
            "photo_date": photo.date,
            "photo_location": photo.location_name,
            "photo_latitude": latitude,
            "photo_longitude": longitude,
        })
    for badges in grouped.values():
        badges.sort(key=lambda badge: (not badge["is_thumbnail"], badge["name"].casefold()))
    return grouped


def photo_coordinates(photo: UserPhoto) -> tuple[float | None, float | None]:
    if (
        photo.observation is not None
        and photo.observation.latitude is not None
        and photo.observation.longitude is not None
    ):
        return photo.observation.latitude, photo.observation.longitude
    metadata = photo.photo_metadata or {}
    if metadata.get("coordinates_cleared") is True:
        return None, None
    try:
        latitude = float(metadata["latitude"])
        longitude = float(metadata["longitude"])
    except (KeyError, TypeError, ValueError):
        return None, None
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return None, None
    return latitude, longitude


def photo_out(photo: UserPhoto) -> dict[str, Any]:
    latitude, longitude = photo_coordinates(photo)
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
        "latitude": latitude,
        "longitude": longitude,
        "caption": photo.caption,
        "encounter_type": photo.encounter_type or "wild",
        "animal_sex": photo.animal_sex or "unknown",
        "measurement": photo.measurement or "",
        "observed_weight": photo.observed_weight or "",
        "profile_id": photo.profile_id,
        "is_best_photo": photo.is_best_photo,
        "photo_metadata": photo.photo_metadata or {},
        "created_at": photo.created_at,
    }


# ----------------------------------------------------------- serialisation --
def to_list_item(
    sp: Species,
    photo_count: int,
    obs_count: int,
    photo: UserPhoto | None,
    raw_photo_count: int | None = None,
    raw_obs_count: int | None = None,
    photographers: list[dict[str, Any]] | None = None,
) -> SpeciesListItem:
    latitude, longitude = photo_coordinates(photo) if photo else (None, None)
    return SpeciesListItem(
        id=sp.id,
        slug=sp.slug,
        common_name=sp.common_name,
        scientific_name=sp.scientific_name,
        group=sp.group,
        class_name=sp.class_name or "",
        family=sp.family,
        difficulty=sp.difficulty,
        regions=sp.regions or [],
        habitats=sp.habitats or [],
        activity=sp.activity or "diurnal",
        size=sp.size,
        reference_image_url=media_url(sp.reference_image),
        reference_thumb_url=media_url(sp.reference_thumb or sp.reference_image),
        status=derive_status(photo_count),
        photo_count=photo_count if raw_photo_count is None else raw_photo_count,
        observation_count=obs_count if raw_obs_count is None else raw_obs_count,
        best_photo_url=media_url(photo.display_key or photo.storage_key) if photo else None,
        best_photo_thumb_url=media_url(
            photo.thumb_key or photo.display_key or photo.storage_key
        ) if photo else None,
        display_photo_date=photo.date if photo else None,
        display_photo_location=photo.location_name if photo else "",
        display_photo_latitude=latitude,
        display_photo_longitude=longitude,
        photographers=photographers or [],
        created_at=sp.created_at,
        updated_at=sp.updated_at,
    )


def to_detail(
    sp: Species, profile_id: int | None, exclude_captive: bool = False
) -> SpeciesDetail:
    profile_photos = [
        p for p in sp.photos if profile_id is None or p.profile_id == profile_id
    ]
    profile_observations = [
        o for o in sp.observations if profile_id is None or o.profile_id == profile_id
    ]
    photos = sorted(
        profile_photos,
        key=lambda p: (not p.is_best_photo, p.date is None, p.date or p.created_at.date()),
    )
    display = photos[0] if photos else None
    progress_photos = [
        p for p in profile_photos
        if not exclude_captive or (p.encounter_type or "wild") == "wild"
    ]
    progress_observations = [
        o for o in profile_observations
        if not exclude_captive or (o.encounter_type or "wild") == "wild"
    ]
    base = to_list_item(
        sp,
        len(progress_photos),
        len(progress_observations),
        display,
        len(profile_photos),
        len(profile_observations),
    )
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
                    "encounter_type": o.encounter_type or "wild",
                    "animal_sex": o.animal_sex or "unknown",
                    "measurement": o.measurement or "",
                    "observed_weight": o.observed_weight or "",
                    "profile_id": o.profile_id,
                    "has_photo": o.has_photo,
                    "created_at": o.created_at,
                }
                for o in profile_observations
            ],
            key=lambda o: (o["date"] is None, o["date"] or o["created_at"].date()),
            reverse=True,
        ),
    )
