from __future__ import annotations

import datetime as dt
import base64
import io
from enum import Enum
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from PIL import ExifTags, Image, ImageOps
from pillow_heif import register_heif_opener
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from ..db import get_db
from ..encounters import sync_observation_from_photo
from ..models import Observation, Species, UserPhoto
from ..profiles import CurrentProfile
from ..queries import photo_out
from ..schemas import PhotoOut, PhotoUpdate
from ..storage import ALLOWED_SUFFIXES, LocalStorage, get_storage

router = APIRouter(prefix="/api/photos", tags=["photos"])
register_heif_opener()

THUMB_MAX = 800
MAX_UPLOAD_BYTES = 40 * 1024 * 1024

# Important EXIF tags also lifted to stable top-level keys for filters/display.
_EXIF_FIELDS = {
    271: "camera_make", 272: "camera_model", 33434: "shutter", 33437: "aperture",
    34855: "iso", 37386: "focal_length", 42035: "lens_make", 42036: "lens_model",
    305: "software", 315: "artist", 33432: "copyright",
    # DateTimeOriginal is preferred; DateTimeDigitized and the general
    # DateTime tag cover phones and editors that omit the original tag.
    36867: "taken_at", 36868: "taken_at_digitized", 306: "taken_at_file",
}
_BROWSER_UNSUPPORTED_SUFFIXES = {".heic", ".heif", ".tif", ".tiff"}


def _parse_date(value: str | None) -> dt.date | None:
    if not value:
        return None
    try:
        return dt.date.fromisoformat(value[:10])
    except ValueError:
        return None


def _parse_time(value: str | None) -> dt.time | None:
    if not value:
        return None
    cleaned = value.strip().replace(".", ":")
    try:
        return dt.time.fromisoformat(cleaned[:8])
    except ValueError:
        return None


def _metadata_time(metadata: dict) -> dt.time | None:
    for metadata_key in ("taken_at", "taken_at_digitized", "taken_at_file"):
        raw_taken_at = str(metadata.get(metadata_key) or "")
        if " " in raw_taken_at:
            parsed = _parse_time(raw_taken_at.split(" ", 1)[1])
            if parsed:
                return parsed
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


def _json_safe(value):
    """Preserve arbitrary EXIF values in a JSON column without losing binary tags."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        return {
            "encoding": "base64",
            "data": base64.b64encode(value).decode("ascii"),
        }
    if isinstance(value, Enum):
        return _json_safe(value.value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    # IFDRational and vendor-specific Pillow objects retain their readable form.
    return str(value)


def _named_tags(values: dict, names: dict[int, str]) -> dict[str, object]:
    return {
        names.get(int(tag), f"Tag 0x{int(tag):04X}"): _json_safe(value)
        for tag, value in values.items()
    }


def _extract(
    data: bytes,
    create_display_copy: bool = False,
) -> tuple[dict, dt.date | None, bytes | None, float | None, float | None, bytes | None]:
    """Return complete EXIF metadata, date, thumbnail, GPS and optional JPEG copy."""
    meta: dict = {}
    taken: dt.date | None = None
    thumb: bytes | None = None
    latitude: float | None = None
    longitude: float | None = None
    display: bytes | None = None
    try:
        with Image.open(io.BytesIO(data)) as img:
            exif = img.getexif()
            top_level = dict(exif.items())
            exif_ifd: dict = {}
            gps_ifd: dict = {}
            interop_ifd: dict = {}
            try:
                exif_ifd = dict(exif.get_ifd(34665))
            except Exception:
                pass
            try:
                gps_ifd = dict(exif.get_ifd(34853))
            except Exception:
                pass
            try:
                interop_ifd = dict(exif.get_ifd(40965))
            except Exception:
                pass

            if top_level:
                meta["exif"] = _named_tags(top_level, ExifTags.TAGS)
            nested = {}
            if exif_ifd:
                nested["Exif"] = _named_tags(exif_ifd, ExifTags.TAGS)
            if gps_ifd:
                nested["GPS"] = _named_tags(gps_ifd, ExifTags.GPSTAGS)
            if interop_ifd:
                nested["Interop"] = _named_tags(interop_ifd, ExifTags.TAGS)
            if nested:
                meta["exif_ifds"] = nested

            all_tags = top_level | exif_ifd
            for tag, name in _EXIF_FIELDS.items():
                if (value := all_tags.get(tag)) is not None:
                    meta[name] = str(value).strip("\x00 ")
            for key in ("taken_at", "taken_at_digitized", "taken_at_file"):
                if raw := meta.get(key):
                    taken = _parse_date(raw.replace(":", "-", 2).split(" ")[0])
                    if taken:
                        break

            latitude = _gps_coordinate(gps_ifd.get(2), gps_ifd.get(1))
            longitude = _gps_coordinate(gps_ifd.get(4), gps_ifd.get(3))
            if latitude is not None and longitude is not None:
                meta["latitude"] = latitude
                meta["longitude"] = longitude

            meta["file_format"] = img.format or ""
            meta["color_mode"] = img.mode
            img = ImageOps.exif_transpose(img)
            meta["width"], meta["height"] = img.size
            copy = img.convert("RGB")
            if create_display_copy:
                display_buffer = io.BytesIO()
                copy.save(display_buffer, "JPEG", quality=94, optimize=True)
                display = display_buffer.getvalue()
            copy.thumbnail((THUMB_MAX, THUMB_MAX), Image.LANCZOS)
            buf = io.BytesIO()
            copy.save(buf, "JPEG", quality=85, optimize=True)
            thumb = buf.getvalue()
    except Exception:
        pass
    return meta, taken, thumb, latitude, longitude, display


def ensure_browser_derivatives() -> int:
    """Repair missing thumbnails and JPEG display copies in local storage."""
    from ..db import SessionLocal

    storage = get_storage()
    if not isinstance(storage, LocalStorage):
        return 0
    repaired = 0
    with SessionLocal.begin() as db:
        for photo in db.execute(select(UserPhoto).order_by(UserPhoto.id)).scalars():
            source = storage.path(photo.storage_key)
            recovered_original = False
            if source is None and photo.thumb_key:
                # A former upload bug replaced storage_key with an EXIF field
                # name. The thumbnail keeps the original UUID, so the existing
                # file can be found without asking the user to upload it again.
                stem = Path(photo.thumb_key).stem
                photo_root = storage.root / "photos"
                candidates = [
                    candidate
                    for candidate in photo_root.rglob(f"{stem}.*")
                    if candidate.is_file() and candidate.suffix.lower() in ALLOWED_SUFFIXES
                ] if photo_root.exists() else []
                if len(candidates) == 1:
                    source = candidates[0]
                    photo.storage_key = source.relative_to(storage.root).as_posix()
                    recovered_original = True
            if source is None:
                continue

            suffix = source.suffix.lower()
            needs_display = suffix in _BROWSER_UNSUPPORTED_SUFFIXES and (
                not photo.display_key or storage.path(photo.display_key) is None
            )
            needs_thumb = not photo.thumb_key or storage.path(photo.thumb_key) is None
            if not needs_display and not needs_thumb:
                repaired += int(recovered_original)
                continue
            try:
                _, _, thumb, _, _, display = _extract(
                    source.read_bytes(), create_display_copy=needs_display
                )
                changed = recovered_original
                if needs_display and display:
                    photo.display_key = storage.save(
                        f"display/{photo.profile_id}/repaired",
                        f"{source.stem}.jpg",
                        io.BytesIO(display),
                    )
                    changed = True
                if needs_thumb and thumb:
                    photo.thumb_key = storage.save(
                        f"thumbs/{photo.profile_id}/repaired",
                        f"{source.stem}.jpg",
                        io.BytesIO(thumb),
                    )
                    changed = True
                repaired += int(changed)
            except OSError:
                # One damaged file must not prevent the API from starting.
                continue
    return repaired


@router.post("", response_model=PhotoOut, status_code=201)
async def upload_photo(
    db: Annotated[Session, Depends(get_db)],
    profile: CurrentProfile,
    species_id: Annotated[int, Form()],
    file: Annotated[UploadFile, File()],
    date: Annotated[str | None, Form()] = None,
    time: Annotated[str | None, Form()] = None,
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
    observation = None
    if observation_id is not None:
        observation = db.get(Observation, observation_id)
        if observation is None or observation.profile_id != profile.id:
            raise HTTPException(404, "Begegnung nicht gefunden")
        if observation.species_id != sp.id:
            raise HTTPException(400, "Begegnung gehört zu einer anderen Art")

    data = await file.read()
    if not data:
        raise HTTPException(400, "Leere Datei")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Datei größer als 40 MB")
    suffix = "." + (file.filename or "foto.jpg").rsplit(".", 1)[-1].lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(415, f"Dateityp {suffix} wird nicht unterstützt")

    needs_display_copy = suffix in _BROWSER_UNSUPPORTED_SUFFIXES
    meta, exif_date, thumb, exif_latitude, exif_longitude, display = _extract(
        data,
        create_display_copy=needs_display_copy,
    )
    if needs_display_copy and display is None:
        raise HTTPException(415, "Die Bilddatei konnte nicht browserfähig aufbereitet werden")
    meta["encounter_type"] = encounter_type
    storage = get_storage()
    storage_key = storage.save(
        f"photos/{profile.id}/{sp.slug}", file.filename or "foto.jpg", io.BytesIO(data)
    )
    display_key = None
    if display:
        display_name = f"{Path(file.filename or 'foto').stem}.jpg"
        display_key = storage.save(
            f"display/{profile.id}/{sp.slug}", display_name, io.BytesIO(display)
        )
    thumb_key = None
    if thumb and isinstance(storage, LocalStorage):
        stem = storage_key.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        thumb_key = storage.save_bytes(f"thumbs/{profile.id}/{sp.slug}/{stem}.jpg", thumb)

    explicit_date = _parse_date(date)
    exif_time = _metadata_time(meta)
    explicit_time = _parse_time(time)
    photo_date = explicit_date or (observation.date if observation else None) or exif_date
    photo_time = explicit_time or (observation.time if observation else None) or exif_time
    latitude = latitude if latitude is not None else exif_latitude
    longitude = longitude if longitude is not None else exif_longitude
    if not location_name.strip() and observation and observation.location_name:
        location_name = observation.location_name
    elif not location_name.strip() and latitude is not None and longitude is not None:
        location_name = f"GPS: {latitude:.5f}, {longitude:.5f}"
    if observation and not caption.strip():
        caption = observation.notes

    if observation_id is None and create_observation:
        obs = Observation(
            profile_id=profile.id, species_id=sp.id, date=photo_date, time=photo_time,
            location_name=location_name,
            latitude=latitude, longitude=longitude,
            notes=caption,
        )
        db.add(obs)
        db.flush()
        observation = obs
        observation_id = obs.id

    photo = UserPhoto(
        profile_id=profile.id,
        species_id=sp.id,
        observation_id=observation_id,
        storage_key=storage_key,
        display_key=display_key,
        thumb_key=thumb_key,
        original_filename=file.filename or "",
        date=photo_date,
        time=photo_time,
        location_name=location_name,
        caption=caption,
        photo_metadata=meta,
    )
    # first photo of a species is automatically the best one
    existing = db.execute(
        select(UserPhoto.id).where(
            UserPhoto.species_id == sp.id, UserPhoto.profile_id == profile.id
        ).limit(1)
    ).first()
    photo.is_best_photo = existing is None
    db.add(photo)
    if observation is not None:
        photo.observation = observation
        sync_observation_from_photo(photo)
    db.commit()
    db.refresh(photo)
    return PhotoOut(**photo_out(photo))


@router.get("", response_model=list[PhotoOut])
def list_photos(
    db: Annotated[Session, Depends(get_db)],
    profile: CurrentProfile,
    species_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[PhotoOut]:
    stmt = select(UserPhoto).where(UserPhoto.profile_id == profile.id)
    if species_id:
        stmt = stmt.where(UserPhoto.species_id == species_id)
    stmt = stmt.order_by(UserPhoto.created_at.desc()).offset(offset).limit(limit)
    return [PhotoOut(**photo_out(p)) for p in db.execute(stmt).scalars()]


@router.patch("/{photo_id}", response_model=PhotoOut)
def update_photo(
    photo_id: int,
    payload: PhotoUpdate,
    db: Annotated[Session, Depends(get_db)],
    profile: CurrentProfile,
) -> PhotoOut:
    photo = db.get(UserPhoto, photo_id)
    if photo is None or photo.profile_id != profile.id:
        raise HTTPException(404, "Foto nicht gefunden")
    data = payload.model_dump(exclude_unset=True)
    if "observation_id" in data:
        new_observation_id = data.pop("observation_id")
        observation = db.get(Observation, new_observation_id) if new_observation_id else None
        if new_observation_id and (observation is None or observation.profile_id != profile.id):
            raise HTTPException(404, "Begegnung nicht gefunden")
        if observation is not None and observation.species_id != photo.species_id:
            raise HTTPException(400, "Begegnung gehört zu einer anderen Art")
        photo.observation = observation
    if data.pop("is_best_photo", None):
        db.execute(
            update(UserPhoto)
            .where(
                UserPhoto.species_id == photo.species_id,
                UserPhoto.profile_id == profile.id,
            )
            .values(is_best_photo=False)
        )
        photo.is_best_photo = True
    for field, value in data.items():
        setattr(photo, field, value)
    sync_observation_from_photo(photo)
    db.commit()
    db.refresh(photo)
    return PhotoOut(**photo_out(photo))


@router.delete("/{photo_id}", status_code=204)
def delete_photo(
    photo_id: int,
    db: Annotated[Session, Depends(get_db)],
    profile: CurrentProfile,
) -> None:
    photo = db.get(UserPhoto, photo_id)
    if photo is None or photo.profile_id != profile.id:
        raise HTTPException(404, "Foto nicht gefunden")
    storage = get_storage()
    species_id, was_best = photo.species_id, photo.is_best_photo
    observation = photo.observation
    storage.delete(photo.storage_key)
    if photo.display_key:
        storage.delete(photo.display_key)
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
            .where(
                UserPhoto.species_id == species_id,
                UserPhoto.profile_id == profile.id,
            )
            .order_by(UserPhoto.date.asc().nullslast(), UserPhoto.id.asc())
            .limit(1)
        ).scalar_one_or_none()
        if nxt:
            nxt.is_best_photo = True
    db.commit()
