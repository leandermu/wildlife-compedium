from __future__ import annotations

import enum
import datetime as dt

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base
from .text import search_variants, slugify


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class SpeciesGroup(str, enum.Enum):
    bird = "bird"
    mammal = "mammal"
    butterfly = "butterfly"
    insect = "insect"
    amphibian = "amphibian"
    reptile = "reptile"
    fish = "fish"
    other = "other"


class Region(str, enum.Enum):
    bavaria = "bavaria"
    germany = "germany"
    europe = "europe"
    world = "world"


class Difficulty(int, enum.Enum):
    common = 1
    uncommon = 2
    challenging = 3
    rare = 4
    legendary = 5


class SpeciesStatus(str, enum.Enum):
    locked = "locked"
    unlocked = "unlocked"


class Profile(Base):
    """A local collection owner. Profiles deliberately have no credentials."""

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    avatar: Mapped[str | None] = mapped_column(String(20), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(12), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)


class Species(Base):
    __tablename__ = "species"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)

    common_name: Mapped[str] = mapped_column(String(160), index=True)
    scientific_name: Mapped[str] = mapped_column(String(160), default="", index=True)

    group: Mapped[str] = mapped_column(String(32), index=True)
    family: Mapped[str] = mapped_column(String(120), default="", index=True)
    order_name: Mapped[str] = mapped_column(String(120), default="")

    description: Mapped[str] = mapped_column(Text, default="")
    size: Mapped[str] = mapped_column(String(80), default="")
    wingspan: Mapped[str] = mapped_column(String(80), default="")
    weight: Mapped[str] = mapped_column(String(80), default="")

    habitats: Mapped[list[str]] = mapped_column(JSON, default=list)
    regions: Mapped[list[str]] = mapped_column(JSON, default=list)
    countries: Mapped[list[str]] = mapped_column(JSON, default=list)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)

    difficulty: Mapped[int] = mapped_column(Integer, default=1, index=True)
    rarity: Mapped[str] = mapped_column(String(40), default="")

    # Reference art is *never* the user's own photo — they live in separate columns
    # and separate storage prefixes on purpose.
    reference_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reference_thumb: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reference_credit: Mapped[str | None] = mapped_column(String(300), nullable=True)
    reference_source: Mapped[str | None] = mapped_column(String(500), nullable=True)
    distribution_map: Mapped[str | None] = mapped_column(String(500), nullable=True)

    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    sort_index: Mapped[int] = mapped_column(Integer, default=0)
    # Used only for the shared activity feed. Kept nullable so bundled and
    # imported legacy species do not pretend to have been added by a profile.
    created_by_profile_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True
    )

    search_text: Mapped[str] = mapped_column(Text, default="", index=True)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow
    )

    observations: Mapped[list[Observation]] = relationship(
        back_populates="species", cascade="all, delete-orphan", lazy="selectin"
    )
    photos: Mapped[list[UserPhoto]] = relationship(
        back_populates="species",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="UserPhoto.is_best_photo.desc(), UserPhoto.date.desc()",
    )

    def refresh_derived(self) -> None:
        if not self.slug:
            self.slug = slugify(self.common_name)
        parts = [
            self.common_name,
            self.scientific_name,
            self.family,
            self.order_name,
            self.group,
            self.rarity,
            " ".join(self.habitats or []),
            " ".join(self.regions or []),
            " ".join(self.countries or []),
            " ".join(self.tags or []),
        ]
        self.search_text = " ".join(search_variants(p) for p in parts if p)


Index("ix_species_group_difficulty", Species.group, Species.difficulty)


class Observation(Base):
    """A sighting. May exist entirely without a photo."""

    __tablename__ = "observations"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=True, index=True
    )
    species_id: Mapped[int] = mapped_column(
        ForeignKey("species.id", ondelete="CASCADE"), index=True
    )
    date: Mapped[dt.date | None] = mapped_column(Date, nullable=True, index=True)
    time: Mapped[dt.time | None] = mapped_column(Time, nullable=True)
    location_name: Mapped[str] = mapped_column(String(200), default="")
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)

    species: Mapped[Species] = relationship(back_populates="observations")
    photos: Mapped[list[UserPhoto]] = relationship(
        back_populates="observation", lazy="selectin"
    )

    @property
    def has_photo(self) -> bool:
        return bool(self.photos)


class UserPhoto(Base):
    """A personal photograph. `storage_key` is backend-agnostic; the public URL
    is resolved by the storage layer at serialisation time."""

    __tablename__ = "user_photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=True, index=True
    )
    species_id: Mapped[int] = mapped_column(
        ForeignKey("species.id", ondelete="CASCADE"), index=True
    )
    observation_id: Mapped[int | None] = mapped_column(
        ForeignKey("observations.id", ondelete="SET NULL"), nullable=True, index=True
    )

    storage_key: Mapped[str] = mapped_column(String(500))
    display_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    thumb_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    original_filename: Mapped[str] = mapped_column(String(300), default="")

    date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    time: Mapped[dt.time | None] = mapped_column(Time, nullable=True)
    location_name: Mapped[str] = mapped_column(String(200), default="")
    caption: Mapped[str] = mapped_column(Text, default="")
    is_best_photo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    # camera, lens, iso, aperture, shutter, focal_length, width, height ...
    photo_metadata: Mapped[dict] = mapped_column("metadata_json", JSON, default=dict)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)

    species: Mapped[Species] = relationship(back_populates="photos")
    observation: Mapped[Observation | None] = relationship(back_populates="photos")


class AchievementState(Base):
    """Definitions live in data files; only the *unlock moment* is persisted."""

    __tablename__ = "achievement_state"
    __table_args__ = (UniqueConstraint("achievement_id", name="uq_achievement_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    achievement_id: Mapped[str] = mapped_column(String(120), index=True)
    tier: Mapped[int] = mapped_column(Integer, default=0)
    unlocked_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)


class ProfileAchievementState(Base):
    """Achievement progress per profile; the old table stays readable for upgrades."""

    __tablename__ = "profile_achievement_state"
    __table_args__ = (
        UniqueConstraint("profile_id", "achievement_id", name="uq_profile_achievement_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), index=True
    )
    achievement_id: Mapped[str] = mapped_column(String(120), index=True)
    tier: Mapped[int] = mapped_column(Integer, default=0)
    unlocked_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)


class Setting(Base):
    """Small key/value store (collection title, owner name, …)."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON, default=dict)
