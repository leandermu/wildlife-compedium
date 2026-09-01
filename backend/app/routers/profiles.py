from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Observation, Profile, UserPhoto
from ..schemas import ProfileCreate, ProfileOut, ProfileUpdate

router = APIRouter(prefix="/api/profiles", tags=["profiles"])
PROFILE_AVATARS = {"🐾", "🦊", "🦉", "🦌", "🐦", "🦋", "🐺", "🌿", "📷"}


def _out(db: Session, profile: Profile) -> ProfileOut:
    photo_count = int(db.execute(
        select(func.count(UserPhoto.id)).where(UserPhoto.profile_id == profile.id)
    ).scalar() or 0)
    observation_count = int(db.execute(
        select(func.count(Observation.id)).where(Observation.profile_id == profile.id)
    ).scalar() or 0)
    collected_species = int(db.execute(
        select(func.count(func.distinct(UserPhoto.species_id))).where(
            UserPhoto.profile_id == profile.id
        )
    ).scalar() or 0)
    return ProfileOut(
        id=profile.id,
        name=profile.name,
        avatar=profile.avatar or "🐾",
        is_default=profile.is_default,
        photo_count=photo_count,
        observation_count=observation_count,
        collected_species=collected_species,
        created_at=profile.created_at,
    )


@router.get("", response_model=list[ProfileOut])
def list_profiles(db: Annotated[Session, Depends(get_db)]) -> list[ProfileOut]:
    profiles = db.execute(
        select(Profile).order_by(Profile.is_default.desc(), Profile.name)
    ).scalars().all()
    return [_out(db, profile) for profile in profiles]


@router.post("", response_model=ProfileOut, status_code=201)
def create_profile(
    payload: ProfileCreate, db: Annotated[Session, Depends(get_db)]
) -> ProfileOut:
    name = " ".join(payload.name.split())
    if not name:
        raise HTTPException(422, "Bitte einen Profilnamen eingeben")
    exists = db.execute(
        select(Profile.id).where(func.lower(Profile.name) == name.casefold())
    ).first()
    if exists:
        raise HTTPException(409, f"Das Profil „{name}“ gibt es bereits")
    profile = Profile(name=name, avatar="🐾", is_default=False)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return _out(db, profile)


@router.patch("/{profile_id}", response_model=ProfileOut)
def update_profile(
    profile_id: int,
    payload: ProfileUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> ProfileOut:
    profile = db.get(Profile, profile_id)
    if profile is None:
        raise HTTPException(404, "Profil nicht gefunden")

    if payload.name is not None:
        name = " ".join(payload.name.split())
        if not name:
            raise HTTPException(422, "Bitte einen Profilnamen eingeben")
        exists = db.execute(
            select(Profile.id).where(
                Profile.id != profile.id,
                func.lower(Profile.name) == name.casefold(),
            )
        ).first()
        if exists:
            raise HTTPException(409, f"Das Profil „{name}“ gibt es bereits")
        profile.name = name

    if payload.avatar is not None:
        if payload.avatar not in PROFILE_AVATARS:
            raise HTTPException(422, "Dieses Profilbild steht nicht zur Auswahl")
        profile.avatar = payload.avatar

    db.commit()
    db.refresh(profile)
    return _out(db, profile)


@router.delete("/{profile_id}", status_code=204)
def delete_profile(
    profile_id: int, db: Annotated[Session, Depends(get_db)]
) -> None:
    profile = db.get(Profile, profile_id)
    if profile is None:
        raise HTTPException(404, "Profil nicht gefunden")

    profile_count = int(db.execute(select(func.count(Profile.id))).scalar() or 0)
    if profile_count <= 1:
        raise HTTPException(409, "Das einzige Profil kann nicht gelöscht werden")

    photo_count = int(db.execute(
        select(func.count(UserPhoto.id)).where(UserPhoto.profile_id == profile.id)
    ).scalar() or 0)
    observation_count = int(db.execute(
        select(func.count(Observation.id)).where(Observation.profile_id == profile.id)
    ).scalar() or 0)
    if photo_count or observation_count:
        raise HTTPException(
            409,
            "Nur leere Profile ohne Fotos und Begegnungen können gelöscht werden",
        )

    if profile.is_default:
        successor = db.execute(
            select(Profile)
            .where(Profile.id != profile.id)
            .order_by(Profile.id)
        ).scalars().first()
        if successor:
            successor.is_default = True
    db.delete(profile)
    db.commit()
