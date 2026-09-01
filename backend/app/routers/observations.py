from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Observation, Species
from ..profiles import CurrentProfile
from ..schemas import ObservationCreate, ObservationOut, ObservationUpdate

router = APIRouter(prefix="/api/observations", tags=["observations"])


def _out(o: Observation) -> ObservationOut:
    return ObservationOut(
        id=o.id, species_id=o.species_id, date=o.date, location_name=o.location_name,
        latitude=o.latitude, longitude=o.longitude, notes=o.notes,
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
    stmt = select(Observation).where(Observation.profile_id == profile.id)
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
    obs = Observation(profile_id=profile.id, **payload.model_dump())
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
    if obs is None or obs.profile_id != profile.id:
        raise HTTPException(404, "Beobachtung nicht gefunden")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obs, field, value)
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
    if obs is None or obs.profile_id != profile.id:
        raise HTTPException(404, "Beobachtung nicht gefunden")
    db.delete(obs)
    db.commit()
