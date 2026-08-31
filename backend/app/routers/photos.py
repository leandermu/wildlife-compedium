from __future__ import annotations

import datetime as dt
import io
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from PIL import Image, ImageOps
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Observation, Species, UserPhoto
from ..queries import photo_out
from ..schemas import PhotoOut, PhotoUpdate
from ..storage import ALLOWED_SUFFIXES, LocalStorage, get_storage

router = APIRouter(prefix="/api/photos", tags=["photos"])

THUMB_MAX = 800
MAX_UPLOAD_BYTES = 40 * 1024 * 1024

# EXIF tags we lift into photo_metadata automatically.
_EXIF_FIELDS = {
    271: "camera_make", 272: "camera_model", 33434: "shutter", 33437: "aperture",
    34855: "iso", 37386: "focal_length",
    # DateTimeOriginal is preferred; DateTimeDigitized and the general
    # DateTime tag cover phones and editors that omit the original tag.
    36867: "taken_at", 36868: "taken_at_digitized", 306: "taken_at_file",
}


def _parse_date(value: str | None) -> dt.date | None:
    if not value:
        return None
    try:
        return dt.date.fromisoformat(value[:10])
    except ValueError:
        return None


def _gps_coordinate(value, reference) -> float | None:
    """Convert EXIF degrees/minutes/seconds plus N/S/E/W into decimal GPS."""
    try:
        degrees, minutes, seconds = (float(part) for part in value)
        coordinate = degrees + minutes / 60 + seconds / 3600
        ref = str(reference).upper()
        return -coordinate if ref in {"S", "W"} else coordinate
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def _extract(data: bytes) -> tuple[dict, dt.date | None, bytes | None, float | None, float | None]:
    """Returns metadata, EXIF date, thumbnail and GPS coordinates. Never fatal — an
    unreadable image still gets stored as-is."""
    meta: dict = {}
    taken: dt.date | None = None
    thumb: bytes | None = None
    latitude: float | None = None
    longitude: float | None = None
    try:
        with Image.open(io.BytesIO(data)) as img:
            img = ImageOps.exif_transpose(img)
            meta["width"], meta["height"] = img.size
            try:
                exif = img.getexif()
                for tag, name in _EXIF_FIELDS.items():
                    if (val := exif.get(tag)) is not None:
                        meta[name] = str(val).strip("\x00 ")
                for key in ("taken_at", "taken_at_digitized", "taken_at_file"):
                    if raw := meta.get(key):
                        taken = _parse_date(raw.replace(":", "-", 2).split(" ")[0])
                        if taken:
                            break
                gps = exif.get_ifd(34853)
                latitude = _gps_coordinate(gps.get(2), gps.get(1))
                longitude = _gps_coordinate(gps.get(4), gps.get(3))
                if latitude is not None and longitude is not None:
                    meta["latitude"] = latitude
                    meta["longitude"] = longitude
            except Exception:
                pass
            copy = img.convert("RGB")
            copy.thumbnail((THUMB_MAX, THUMB_MAX), Image.LANCZOS)
            buf = io.BytesIO()
            copy.save(buf, "JPEG", quality=85, optimize=True)
            thumb = buf.getvalue()
    except Exception:
        pass
    return meta, taken, thumb, latitude, longitude


@router.post("", response_model=PhotoOut, status_code=201)
async def upload_photo(
    db: Annotated[Session, Depends(get_db)],
    species_id: Annotated[int, Form()],
    file: Annotated[UploadFile, File()],
    date: Annotated[str | None, Form()] = None,
    location_name: Annotated[str, Form()] = "",
    caption: Annotated[str, Form()] = "",
    observation_id: Annotated[int | None, Form()] = None,
    latitude: Annotated[float | None, Form()] = None,
    longitude: Annotated[float | None, Form()] = None,
    create_observation: Annotated[bool, Form()] = True,
    encounter_type: Annotated[Literal["wild", "captive"], Form()] = "wild",
) -> PhotoOut:
    sp = db.get(Species, species_id)
    if sp is None:
        raise HTTPException(404, "Art nicht gefunden")

    data = await file.read()
    if not data:
        raise HTTPException(400, "Leere Datei")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Datei größer als 40 MB")
    suffix = "." + (file.filename or "foto.jpg").rsplit(".", 1)[-1].lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(415, f"Dateityp {suffix} wird nicht unterstützt")

    meta, exif_date, thumb, exif_latitude, exif_longitude = _extract(data)
    meta["encounter_type"] = encounter_type
    storage = get_storage()
    key = storage.save(f"photos/{sp.slug}", file.filename or "foto.jpg", io.BytesIO(data))
    thumb_key = None
    if thumb and isinstance(storage, LocalStorage):
        stem = key.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        thumb_key = storage.save_bytes(f"thumbs/{sp.slug}/{stem}.jpg", thumb)

    photo_date = _parse_date(date) or exif_date
    latitude = latitude if latitude is not None else exif_latitude
    longitude = longitude if longitude is not None else exif_longitude
    if not location_name.strip() and latitude is not None and longitude is not None:
        location_name = f"GPS: {latitude:.5f}, {longitude:.5f}"

    if observation_id is None and create_observation:
        obs = Observation(
            species_id=sp.id, date=photo_date, location_name=location_name,
            latitude=latitude, longitude=longitude,
        )
        db.add(obs)
        db.flush()
        observation_id = obs.id

    photo = UserPhoto(
        species_id=sp.id,
        observation_id=observation_id,
        storage_key=key,
        thumb_key=thumb_key,
        original_filename=file.filename or "",
        date=photo_date,
        location_name=location_name,
        caption=caption,
        photo_metadata=meta,
    )
    # first photo of a species is automatically the best one
    existing = db.execute(
        select(UserPhoto.id).where(UserPhoto.species_id == sp.id).limit(1)
    ).first()
    photo.is_best_photo = existing is None
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return PhotoOut(**photo_out(photo))


@router.get("", response_model=list[PhotoOut])
def list_photos(
    db: Annotated[Session, Depends(get_db)],
    species_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[PhotoOut]:
    stmt = select(UserPhoto)
    if species_id:
        stmt = stmt.where(UserPhoto.species_id == species_id)
    stmt = stmt.order_by(UserPhoto.created_at.desc()).offset(offset).limit(limit)
    return [PhotoOut(**photo_out(p)) for p in db.execute(stmt).scalars()]


@router.patch("/{photo_id}", response_model=PhotoOut)
def update_photo(
    photo_id: int, payload: PhotoUpdate, db: Annotated[Session, Depends(get_db)]
) -> PhotoOut:
    photo = db.get(UserPhoto, photo_id)
    if photo is None:
        raise HTTPException(404, "Foto nicht gefunden")
    data = payload.model_dump(exclude_unset=True)
    if data.pop("is_best_photo", None):
        db.execute(
            update(UserPhoto)
            .where(UserPhoto.species_id == photo.species_id)
            .values(is_best_photo=False)
        )
        photo.is_best_photo = True
    for field, value in data.items():
        setattr(photo, field, value)
    db.commit()
    db.refresh(photo)
    return PhotoOut(**photo_out(photo))


@router.delete("/{photo_id}", status_code=204)
def delete_photo(photo_id: int, db: Annotated[Session, Depends(get_db)]) -> None:
    photo = db.get(UserPhoto, photo_id)
    if photo is None:
        raise HTTPException(404, "Foto nicht gefunden")
    storage = get_storage()
    species_id, was_best = photo.species_id, photo.is_best_photo
    observation = photo.observation
    storage.delete(photo.storage_key)
    if photo.thumb_key:
        storage.delete(photo.thumb_key)
    db.delete(photo)
    db.flush()
    # Eine beim Upload automatisch angelegte Begegnung ohne eigene Notiz und ohne
    # weitere Fotos trägt keine Information mehr — sonst bleibt sie als
    # "Begegnung ohne Foto" zurück. Selbst notierte Begegnungen bleiben erhalten.
    if observation is not None and not observation.notes.strip():
        remaining = db.execute(
            select(func.count(UserPhoto.id)).where(
                UserPhoto.observation_id == observation.id
            )
        ).scalar()
        if not remaining:
            db.delete(observation)
    if was_best:  # promote the next photo so the card never loses its image
        nxt = db.execute(
            select(UserPhoto)
            .where(UserPhoto.species_id == species_id)
            .order_by(UserPhoto.date.asc().nullslast(), UserPhoto.id.asc())
            .limit(1)
        ).scalar_one_or_none()
        if nxt:
            nxt.is_best_photo = True
    db.commit()
