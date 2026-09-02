"""Export endpoints — the collection must never be trapped inside this app."""

from __future__ import annotations

import csv
import datetime as dt
import io
import json
import zipfile
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Observation, Species, UserPhoto
from ..profiles import CurrentProfile
from ..queries import derive_status
from ..storage import get_storage
from ..text import slugify

router = APIRouter(prefix="/api/export", tags=["export"])

SPECIES_COLUMNS = [
    "slug", "common_name", "scientific_name", "group", "class_name", "family", "order_name", "activity",
    "description", "size", "wingspan", "weight", "habitats", "regions", "countries",
    "tags", "difficulty", "rarity", "reference_image", "distribution_map", "active",
]


def _species_dict(sp: Species) -> dict:
    return {
        "slug": sp.slug, "common_name": sp.common_name,
        "scientific_name": sp.scientific_name, "group": sp.group, "family": sp.family,
        "class_name": sp.class_name, "order_name": sp.order_name,
        "activity": sp.activity or "diurnal", "description": sp.description, "size": sp.size,
        "wingspan": sp.wingspan, "weight": sp.weight, "habitats": sp.habitats or [],
        "regions": sp.regions or [], "countries": sp.countries or [], "tags": sp.tags or [],
        "difficulty": sp.difficulty, "rarity": sp.rarity,
        "reference_image": sp.reference_image, "distribution_map": sp.distribution_map,
        "active": sp.active,
    }


def _photo_dict(p: UserPhoto) -> dict:
    return {
        "id": p.id, "species_id": p.species_id, "observation_id": p.observation_id,
        "file": p.storage_key, "original_filename": p.original_filename,
        "date": p.date.isoformat() if p.date else None, "location_name": p.location_name,
        "caption": p.caption, "is_best_photo": p.is_best_photo,
        "encounter_type": p.encounter_type or "wild",
        "metadata": p.photo_metadata or {},
        "created_at": p.created_at.isoformat(),
    }


def _observation_dict(o: Observation) -> dict:
    return {
        "id": o.id, "species_id": o.species_id,
        "date": o.date.isoformat() if o.date else None,
        "location_name": o.location_name, "latitude": o.latitude,
        "longitude": o.longitude, "notes": o.notes, "has_photo": o.has_photo,
        "encounter_type": o.encounter_type or "wild",
        "created_at": o.created_at.isoformat(),
    }


def _all(db: Session, profile_id: int):
    species = list(db.execute(select(Species).order_by(Species.id)).scalars())
    observations = list(db.execute(
        select(Observation)
        .where(Observation.profile_id == profile_id)
        .order_by(Observation.id)
    ).scalars())
    photos = list(db.execute(
        select(UserPhoto)
        .where(UserPhoto.profile_id == profile_id)
        .order_by(UserPhoto.id)
    ).scalars())
    return species, observations, photos


def _stamp() -> str:
    return dt.date.today().isoformat()


@router.get("/json")
def export_json(
    db: Annotated[Session, Depends(get_db)], profile: CurrentProfile
) -> Response:
    species, observations, photos = _all(db, profile.id)
    payload = {
        "exported_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "version": 1,
        "profile": {
            "id": profile.id,
            "name": profile.name,
            "exclude_captive_from_progress": bool(
                profile.exclude_captive_from_progress
            ),
        },
        "species": [_species_dict(s) | {"id": s.id} for s in species],
        "observations": [_observation_dict(o) for o in observations],
        "photos": [_photo_dict(p) for p in photos],
    }
    body = json.dumps(payload, ensure_ascii=False, indent=1)
    return Response(
        body,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="compedium-{_stamp()}.json"'},
    )


def _csv(rows: list[dict], columns: list[str]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({
            k: (", ".join(v) if isinstance(v, list) else "" if v is None else v)
            for k, v in row.items()
        })
    return buf.getvalue()


def _species_csv(species: list[Species], photos: list[UserPhoto]) -> str:
    photo_counts: dict[int, int] = {}
    for p in photos:
        photo_counts[p.species_id] = photo_counts.get(p.species_id, 0) + 1
    rows = [
        _species_dict(s) | {
            "photo_count": photo_counts.get(s.id, 0),
            "status": derive_status(photo_counts.get(s.id, 0)),
        }
        for s in species
    ]
    return _csv(rows, SPECIES_COLUMNS + ["photo_count", "status"])


@router.get("/csv")
def export_csv(
    db: Annotated[Session, Depends(get_db)],
    profile: CurrentProfile,
    what: str = "species",
) -> Response:
    species, observations, photos = _all(db, profile.id)
    if what == "observations":
        cols = ["id", "species_id", "date", "location_name", "latitude", "longitude",
                "notes", "encounter_type", "has_photo"]
        by_id = {s.id: s for s in species}
        rows = [
            _observation_dict(o) | {"species_slug": by_id[o.species_id].slug}
            for o in observations if o.species_id in by_id
        ]
        cols.insert(2, "species_slug")
        body = _csv(rows, cols)
    elif what == "photos":
        cols = ["id", "species_id", "species_slug", "observation_id", "file", "date",
                "location_name", "caption", "encounter_type", "is_best_photo"]
        by_id = {s.id: s for s in species}
        rows = [
            _photo_dict(p) | {"species_slug": by_id[p.species_id].slug}
            for p in photos if p.species_id in by_id
        ]
        body = _csv(rows, cols)
    else:
        body = _species_csv(species, photos)
    return Response(
        body,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{what}-{_stamp()}.csv"'},
    )


@router.get("/zip")
def export_zip(
    db: Annotated[Session, Depends(get_db)],
    profile: CurrentProfile,
    include_photos: bool = True,
):
    """Full backup: data files plus the original photo files, foldered by species."""
    species, observations, photos = _all(db, profile.id)
    by_id = {s.id: s for s in species}
    storage = get_storage()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("species.json", json.dumps(
            [_species_dict(s) | {"id": s.id} for s in species], ensure_ascii=False, indent=1))
        zf.writestr("observations.json", json.dumps(
            [_observation_dict(o) for o in observations], ensure_ascii=False, indent=1))
        zf.writestr("photos.json", json.dumps(
            [_photo_dict(p) for p in photos], ensure_ascii=False, indent=1))
        zf.writestr("species.csv", _species_csv(species, photos))
        if include_photos:
            for p in photos:
                sp = by_id.get(p.species_id)
                path = storage.path(p.storage_key)
                if not sp or not path:
                    continue
                suffix = path.suffix or ".jpg"
                name = f"photos/{slugify(sp.common_name)}/{p.date or 'ohne-datum'}-{p.id}{suffix}"
                zf.write(path, name)
        zf.writestr("README.txt",
                    f"Wildlife Compedium – Export für {profile.name}\n"
                    f"Erstellt am {dt.datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                    "species.json / observations.json / photos.json enthalten alle Daten.\n"
                    "Der Ordner photos/ enthält die Originaldateien, nach Art sortiert.\n")
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="compedium-{_stamp()}.zip"'},
    )
