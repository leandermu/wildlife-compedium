from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import achievements as engine
from ..db import get_db
from ..profiles import CurrentProfile
from ..schemas import AchievementOut

router = APIRouter(prefix="/api/achievements", tags=["achievements"])


@router.get("", response_model=list[AchievementOut])
def list_achievements(
    db: Annotated[Session, Depends(get_db)],
    profile: CurrentProfile,
    kind: str | None = None,
) -> list[AchievementOut]:
    items = engine.evaluate(db, profile.id)
    if kind:
        items = [i for i in items if i["kind"] == kind]
    items.sort(key=lambda i: (not i["unlocked"], i["category"], i["name"]))
    return [AchievementOut(**i) for i in items]
