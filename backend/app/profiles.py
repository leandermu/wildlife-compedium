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
