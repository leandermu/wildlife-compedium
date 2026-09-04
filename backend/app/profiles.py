from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .models import Profile


def current_profile(
    db: Annotated[Session, Depends(get_db)],
    x_profile_id: Annotated[int | None, Header(alias="X-Profile-ID")] = None,
    profile_id: Annotated[int | None, Query()] = None,
) -> Profile:
    """Resolve the explicitly selected profile, falling back to the default."""
    selected = x_profile_id if x_profile_id is not None else profile_id
    if selected is not None:
        profile = db.get(Profile, selected)
        if profile is None:
            raise HTTPException(404, "Profil nicht gefunden")
        return profile
    profile = db.execute(
        select(Profile).order_by(Profile.is_default.desc(), Profile.id)
    ).scalars().first()
    if profile is None:  # init_db normally guarantees this
        raise HTTPException(503, "Noch kein Profil vorhanden")
    return profile


CurrentProfile = Annotated[Profile, Depends(current_profile)]


def scope_profile_id(profile: Profile) -> int | None:
    """None means the shared profile may see progress from every real profile."""
    return None if profile.is_shared else profile.id


def resolve_entry_profile(
    db: Session,
    selected_profile: Profile,
    observer_profile_id: int | None,
) -> Profile:
    """Resolve the real person responsible for a newly recorded encounter."""
    if not selected_profile.is_shared:
        if observer_profile_id not in {None, selected_profile.id}:
            raise HTTPException(403, "Einträge können nur dem aktiven Profil zugeordnet werden")
        return selected_profile
    if observer_profile_id is None:
        raise HTTPException(422, "Bitte auswählen, wer die Begegnung gemacht hat")
    observer = db.get(Profile, observer_profile_id)
    if observer is None or observer.is_shared:
        raise HTTPException(422, "Bitte ein persönliches Profil auswählen")
    return observer


def can_access_entry(selected_profile: Profile, owner_profile_id: int | None) -> bool:
    return bool(selected_profile.is_shared or owner_profile_id == selected_profile.id)
