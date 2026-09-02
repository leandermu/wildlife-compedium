from __future__ import annotations

import datetime as dt
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------- profiles
class ProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    gender: str = Field(default="male", pattern="^(male|female)$")


class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    avatar: str | None = Field(default=None, min_length=1, max_length=20)
    gender: str | None = Field(default=None, pattern="^(male|female)$")
    exclude_captive_from_progress: bool | None = None


class ProfileOut(ORMModel):
    id: int
    name: str
    avatar: str = "🐾"
    gender: str = "male"
    is_default: bool = False
    exclude_captive_from_progress: bool = False
    photo_count: int = 0
    observation_count: int = 0
    collected_species: int = 0
    created_at: dt.datetime


# --------------------------------------------------------------------- photos
class PhotoBase(BaseModel):
    date: dt.date | None = None
    time: dt.time | None = None
    location_name: str = ""
    caption: str = ""
    observation_id: int | None = None
    photo_metadata: dict[str, Any] = Field(default_factory=dict)


class PhotoUpdate(BaseModel):
    date: dt.date | None = None
    time: dt.time | None = None
    location_name: str | None = None
    caption: str | None = None
    observation_id: int | None = None
    is_best_photo: bool | None = None
    photo_metadata: dict[str, Any] | None = None
    encounter_type: str | None = Field(default=None, pattern="^(wild|captive)$")


class PhotoOut(ORMModel):
    id: int
    species_id: int
    observation_id: int | None = None
    url: str | None = None
    thumb_url: str | None = None
    original_filename: str = ""
    date: dt.date | None = None
    time: dt.time | None = None
    location_name: str = ""
    caption: str = ""
    encounter_type: str = "wild"
    is_best_photo: bool = False
    photo_metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: dt.datetime


# --------------------------------------------------------------- observations
class ObservationBase(BaseModel):
    date: dt.date | None = None
    time: dt.time | None = None
    location_name: str = ""
    latitude: float | None = None
    longitude: float | None = None
    notes: str = ""
    encounter_type: str = Field(default="wild", pattern="^(wild|captive)$")


class ObservationCreate(ObservationBase):
    species_id: int


class ObservationUpdate(BaseModel):
    date: dt.date | None = None
    time: dt.time | None = None
    location_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    notes: str | None = None
    encounter_type: str | None = Field(default=None, pattern="^(wild|captive)$")


class ObservationOut(ORMModel):
    id: int
    species_id: int
    date: dt.date | None = None
    time: dt.time | None = None
    location_name: str = ""
    latitude: float | None = None
    longitude: float | None = None
    notes: str = ""
    encounter_type: str = "wild"
    has_photo: bool = False
    created_at: dt.datetime


# -------------------------------------------------------------------- species
class SpeciesBase(BaseModel):
    common_name: str
    scientific_name: str = ""
    group: str = "other"
    class_name: str = ""
    family: str = ""
    order_name: str = ""
    activity: str = Field(default="diurnal", pattern="^(diurnal|nocturnal)$")
    description: str = ""
    size: str = ""
    wingspan: str = ""
    weight: str = ""
    habitats: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    difficulty: int = 1
    rarity: str = ""
    reference_image: str | None = None
    reference_thumb: str | None = None
    reference_credit: str | None = None
    reference_source: str | None = None
    distribution_map: str | None = None
    active: bool = True


class SpeciesCreate(SpeciesBase):
    slug: str | None = None


class AutomaticSpeciesCreate(BaseModel):
    common_name: str = Field(min_length=1, max_length=160)


class SpeciesUpdate(BaseModel):
    common_name: str | None = None
    scientific_name: str | None = None
    group: str | None = None
    class_name: str | None = None
    family: str | None = None
    order_name: str | None = None
    activity: str | None = Field(default=None, pattern="^(diurnal|nocturnal)$")
    description: str | None = None
    size: str | None = None
    wingspan: str | None = None
    weight: str | None = None
    habitats: list[str] | None = None
    regions: list[str] | None = None
    countries: list[str] | None = None
    tags: list[str] | None = None
    difficulty: int | None = None
    rarity: str | None = None
    reference_image: str | None = None
    reference_thumb: str | None = None
    reference_credit: str | None = None
    reference_source: str | None = None
    distribution_map: str | None = None
    active: bool | None = None


class SpeciesListItem(ORMModel):
    """Lean payload for grid views — no descriptions, no nested photo lists."""

    id: int
    slug: str
    common_name: str
    scientific_name: str
    group: str
    class_name: str = ""
    family: str
    difficulty: int
    regions: list[str] = Field(default_factory=list)
    habitats: list[str] = Field(default_factory=list)
    activity: str = "diurnal"
    size: str = ""
    reference_image_url: str | None = None
    reference_thumb_url: str | None = None
    status: str = "locked"
    photo_count: int = 0
    observation_count: int = 0
    best_photo_url: str | None = None
    best_photo_thumb_url: str | None = None
    display_photo_date: dt.date | None = None
    display_photo_location: str = ""
    created_at: dt.datetime | None = None
    updated_at: dt.datetime | None = None


class SpeciesDetail(SpeciesListItem):
    order_name: str = ""
    description: str = ""
    wingspan: str = ""
    weight: str = ""
    countries: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    rarity: str = ""
    reference_credit: str | None = None
    reference_source: str | None = None
    distribution_map_url: str | None = None
    active: bool = True
    photos: list[PhotoOut] = Field(default_factory=list)
    observations: list[ObservationOut] = Field(default_factory=list)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


# --------------------------------------------------------------------- facets
class FacetValue(BaseModel):
    value: str
    label: str
    count: int
    collected: int = 0


class Facets(BaseModel):
    groups: list[FacetValue]
    classes: list[FacetValue]
    orders: list[FacetValue]
    habitats: list[FacetValue]
    regions: list[FacetValue]
    families: list[FacetValue]
    difficulties: list[FacetValue]
    statuses: list[FacetValue]
    seen: list[FacetValue]
    encounters: list[FacetValue]
    activities: list[FacetValue]
    tags: list[FacetValue]


# ------------------------------------------------------------------ dashboard
class ProgressBucket(BaseModel):
    key: str
    label: str
    collected: int
    total: int


class RecentUnlock(BaseModel):
    species_id: int
    slug: str
    common_name: str
    scientific_name: str
    photo_url: str | None = None
    thumb_url: str | None = None
    date: dt.date | None = None
    location_name: str = ""


class ChallengeHint(BaseModel):
    label: str
    remaining: int
    filter: dict[str, str]


class ActivityOut(BaseModel):
    kind: str
    profile_id: int
    profile_name: str
    profile_avatar: str
    species_id: int
    species_slug: str
    species_name: str
    occurred_at: dt.datetime


class DashboardOut(BaseModel):
    total_species: int
    collected: int
    photo_count: int
    observation_count: int
    by_group: list[ProgressBucket]
    by_region: list[ProgressBucket]
    by_difficulty: list[ProgressBucket]
    recent: list[RecentUnlock]
    activity: list[ActivityOut]
    challenges: list[ChallengeHint]
    achievements_unlocked: int
    achievements_total: int


# --------------------------------------------------------------- achievements
class AchievementTierOut(BaseModel):
    threshold: int
    label: str
    unlocked: bool


class AchievementOut(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    kind: str = "achievement"
    category: str = ""
    progress: int
    target: int
    level: int = 1
    unlocked: bool
    unlocked_at: dt.datetime | None = None
    tiers: list[AchievementTierOut] = Field(default_factory=list)
    species: list[dict[str, Any]] = Field(default_factory=list)
    starts_on: dt.date | None = None
    ends_on: dt.date | None = None


# --------------------------------------------------------------------- import
class ImportResult(BaseModel):
    created: int
    updated: int
    skipped: int
    errors: list[str] = Field(default_factory=list)
