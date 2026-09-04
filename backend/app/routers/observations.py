from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..encounters import sync_photos_from_observation
from ..models import Observation, Species
from ..profiles import (
    CurrentProfile,
    can_access_entry,
    resolve_entry_profile,
    scope_profile_id,
)
from ..schemas import ObservationCreate, ObservationOut, ObservationUpdate

router = APIRouter(prefix="/api/observations", tags=["observations"])


def _out(o: Observation) -> ObservationOut:
    return ObservationOut(
        id=o.id, species_id=o.species_id, date=o.date, time=o.time,
        location_name=o.location_name,
        latitude=o.latitude, longitude=o.longitude, notes=o.notes,
        encounter_type=o.encounter_type or "wild",
        animal_sex=o.animal_sex or "unknown",
        measurement=o.measurement or "",
        observed_weight=o.observed_weight or "",
        profile_id=o.profile_id,
        has_photo=o.has_photo, created_at=o.created_at,
    )


@router.get("", response_model=list[ObservationOut])
def list_observations(
    db: Annotated[Session, Depends(get_db)],
    profile: CurrentProfile,
    species_id: int | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[ObservationOut]:
    stmt = select(Observation)
    if (profile_id := scope_profile_id(profile)) is not None:
        stmt = stmt.where(Observation.profile_id == profile_id)
    if species_id:
        stmt = stmt.where(Observation.species_id == species_id)
    stmt = stmt.order_by(Observation.date.desc().nullslast(), Observation.id.desc())
    return [_out(o) for o in db.execute(stmt.offset(offset).limit(limit)).scalars()]


@router.post("", response_model=ObservationOut, status_code=201)
def create_observation(
    payload: ObservationCreate,
    db: Annotated[Session, Depends(get_db)],
    profile: CurrentProfile,
) -> ObservationOut:
    if db.get(Species, payload.species_id) is None:
        raise HTTPException(404, "Art nicht gefunden")
    data = payload.model_dump()
    observer_profile_id = data.pop("observer_profile_id", None)
    owner = resolve_entry_profile(db, profile, observer_profile_id)
    obs = Observation(profile_id=owner.id, **data)
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return _out(obs)


@router.patch("/{observation_id}", response_model=ObservationOut)
def update_observation(
    observation_id: int,
    payload: ObservationUpdate,
    db: Annotated[Session, Depends(get_db)],
    profile: CurrentProfile,
) -> ObservationOut:
    obs = db.get(Observation, observation_id)
    if obs is None or not can_access_entry(profile, obs.profile_id):
        raise HTTPException(404, "Beobachtung nicht gefunden")
    data = payload.model_dump(exclude_unset=True)
    coordinate_update = "latitude" in data or "longitude" in data
    for field, value in data.items():
        setattr(obs, field, value)
    if coordinate_update:
        for photo in obs.photos:
            metadata = dict(photo.photo_metadata or {})
            if obs.latitude is None or obs.longitude is None:
                metadata.pop("latitude", None)
                metadata.pop("longitude", None)
                metadata["coordinates_cleared"] = True
            else:
                metadata["latitude"] = obs.latitude
                metadata["longitude"] = obs.longitude
                metadata.pop("coordinates_cleared", None)
            photo.photo_metadata = metadata
    sync_photos_from_observation(obs)
    db.commit()
    db.refresh(obs)
    return _out(obs)


@router.delete("/{observation_id}", status_code=204)
def delete_observation(
    observation_id: int,
    db: Annotated[Session, Depends(get_db)],
    profile: CurrentProfile,
) -> None:
    obs = db.get(Observation, observation_id)
    if obs is None or not can_access_entry(profile, obs.profile_id):
        raise HTTPException(404, "Beobachtung nicht gefunden")
    db.delete(obs)
    db.commit()
