"""Portable full backups for the complete shared collection."""

from __future__ import annotations

import datetime as dt
import json
import shutil
import tempfile
import uuid
import zipfile
from enum import Enum
from pathlib import Path, PurePosixPath
from threading import Lock
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import Date, DateTime, Time, delete, inspect as sa_inspect, text, update
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask

from ..db import get_db
from ..models import (
    AchievementState,
    Observation,
    Profile,
    ProfileAchievementState,
    Setting,
    Species,
    UserPhoto,
)
from ..storage import LocalStorage, get_storage

router = APIRouter(prefix="/api/backup", tags=["backup"])

BACKUP_VERSION = 2
BACKUP_TABLES: list[tuple[str, type]] = [
    ("profiles", Profile),
    ("species", Species),
    ("observations", Observation),
    ("photos", UserPhoto),
    ("profile_achievements", ProfileAchievementState),
    ("legacy_achievements", AchievementState),
    ("settings", Setting),
]
DELETE_ORDER = [
    UserPhoto,
    Observation,
    ProfileAchievementState,
    AchievementState,
    Setting,
    Species,
    Profile,
]
ID_MODELS = [
    Profile,
    Species,
    Observation,
    UserPhoto,
    ProfileAchievementState,
    AchievementState,
]
_restore_lock = Lock()


def _stamp() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d_%H-%M")


def _local_storage() -> LocalStorage:
    storage = get_storage()
    if not isinstance(storage, LocalStorage):
        raise HTTPException(501, "Backups werden derzeit nur mit lokalem Medienspeicher unterstützt")
    return storage


def _json_value(value: Any) -> Any:
    if isinstance(value, (dt.datetime, dt.date, dt.time)):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return value


def _row(item: Any) -> dict[str, Any]:
    return {
        prop.key: _json_value(getattr(item, prop.key))
        for prop in sa_inspect(type(item)).column_attrs
    }


def _manifest(db: Session) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "format": "wildlife-compedium-backup",
        "version": BACKUP_VERSION,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    for key, model in BACKUP_TABLES:
        payload[key] = [_row(item) for item in db.query(model).all()]
    return payload


def _remove_file(path: str) -> None:
    Path(path).unlink(missing_ok=True)


@router.get("/save")
def save_backup(db: Annotated[Session, Depends(get_db)]) -> FileResponse:
    """Download the database contents and every locally stored media file."""
    storage = _local_storage()
    handle = tempfile.NamedTemporaryFile(prefix="compedium-", suffix=".wcbackup", delete=False)
    archive_path = Path(handle.name)
    handle.close()

    try:
        manifest = _manifest(db)
        for photo in manifest["photos"]:
            storage_key = photo.get("storage_key")
            if not storage_key or storage.path(storage_key) is None:
                raise HTTPException(
                    409,
                    f"Das Foto „{photo.get('original_filename') or photo.get('id')}“ fehlt im Medienspeicher",
                )
            display_key = photo.get("display_key")
            if display_key and storage.path(display_key) is None:
                raise HTTPException(409, f"Die Anzeigeversion von „{storage_key}“ fehlt")
            thumb_key = photo.get("thumb_key")
            if thumb_key and storage.path(thumb_key) is None:
                photo["thumb_key"] = None
        for species in manifest["species"]:
            for field in ("reference_image", "reference_thumb", "distribution_map"):
                key = species.get(field)
                if key and not str(key).startswith(("http://", "https://", "/")):
                    if storage.path(key) is None:
                        species[field] = None

        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as archive:
            archive.writestr(
                "backup.json",
                json.dumps(manifest, ensure_ascii=False, indent=1),
            )
            root = storage.root.resolve()
            if root.exists():
                for path in root.rglob("*"):
                    if path.is_file():
                        relative = path.relative_to(root).as_posix()
                        archive.write(path, f"media/{relative}")
    except Exception:
        archive_path.unlink(missing_ok=True)
        raise

    return FileResponse(
        archive_path,
        media_type="application/zip",
        filename=f"wildlife-compedium-{_stamp()}.wcbackup",
        background=BackgroundTask(_remove_file, str(archive_path)),
    )


def _load_manifest(archive: zipfile.ZipFile) -> dict[str, Any]:
    try:
        raw = archive.read("backup.json")
        data = json.loads(raw)
    except (KeyError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(422, "Das Archiv enthält kein gültiges Compedium-Backup") from exc

    if not isinstance(data, dict) or data.get("format") != "wildlife-compedium-backup":
        raise HTTPException(422, "Das ist kein Wildlife-Compedium-Backup")
    if data.get("version") != BACKUP_VERSION:
        raise HTTPException(422, "Diese Backup-Version wird nicht unterstützt")
    for key, _model in BACKUP_TABLES:
        if not isinstance(data.get(key), list):
            raise HTTPException(422, f"Im Backup fehlt der Bereich „{key}“")
    if not data["profiles"]:
        raise HTTPException(422, "Das Backup enthält kein Profil")
    return data


def _validate_relations(data: dict[str, Any], archive_names: set[str]) -> None:
    try:
        for row in data["profiles"]:
            row.setdefault("exclude_captive_from_progress", False)
        photo_encounters: dict[int, str] = {}
        for row in data["photos"]:
            if "encounter_type" not in row:
                metadata = row.get("photo_metadata") or {}
                value = metadata.get("encounter_type", "wild")
                row["encounter_type"] = value if value in {"wild", "captive"} else "wild"
            if row.get("observation_id") is not None:
                photo_encounters[int(row["observation_id"])] = row["encounter_type"]
        for row in data["observations"]:
            row.setdefault(
                "encounter_type",
                photo_encounters.get(int(row["id"]), "wild"),
            )

        profile_ids = {int(row["id"]) for row in data["profiles"]}
        species_ids = {int(row["id"]) for row in data["species"]}
        observation_ids = {int(row["id"]) for row in data["observations"]}
        if len(profile_ids) != len(data["profiles"]) or len(species_ids) != len(data["species"]):
            raise ValueError

        for row in data["species"]:
            creator_id = row.get("created_by_profile_id")
            if creator_id is not None and int(creator_id) not in profile_ids:
                row["created_by_profile_id"] = None

        for row in data["observations"]:
            if int(row["profile_id"]) not in profile_ids or int(row["species_id"]) not in species_ids:
                raise ValueError
        for row in data["photos"]:
            if int(row["profile_id"]) not in profile_ids or int(row["species_id"]) not in species_ids:
                raise ValueError
            observation_id = row.get("observation_id")
            if observation_id is not None and int(observation_id) not in observation_ids:
                raise ValueError
            storage_key = row.get("storage_key")
            if not storage_key or f"media/{PurePosixPath(storage_key).as_posix()}" not in archive_names:
                raise HTTPException(422, f"Im Backup fehlt die Mediendatei „{storage_key}“")
            display_key = row.get("display_key")
            if display_key and f"media/{PurePosixPath(display_key).as_posix()}" not in archive_names:
                raise HTTPException(422, f"Im Backup fehlt die Anzeigeversion „{display_key}“")
            thumb_key = row.get("thumb_key")
            if thumb_key and f"media/{PurePosixPath(thumb_key).as_posix()}" not in archive_names:
                row["thumb_key"] = None
        for row in data["profile_achievements"]:
            if int(row["profile_id"]) not in profile_ids:
                raise ValueError
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(422, "Die Datensätze im Backup sind unvollständig oder widersprüchlich") from exc


def _safe_media_parts(name: str) -> tuple[str, ...] | None:
    path = PurePosixPath(name)
    if not path.parts or path.parts[0] != "media" or len(path.parts) == 1:
        return None
    relative = path.parts[1:]
    if path.is_absolute() or any(part in {"", ".", ".."} for part in relative):
        raise HTTPException(422, "Das Backup enthält einen ungültigen Medienpfad")
    return relative


def _stage_media(archive: zipfile.ZipFile, parent: Path) -> Path:
    stage = Path(tempfile.mkdtemp(prefix=".compedium-restore-", dir=parent))
    try:
        for info in archive.infolist():
            parts = _safe_media_parts(info.filename)
            if parts is None or info.is_dir():
                continue
            target = stage.joinpath(*parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, target.open("wb") as destination:
                shutil.copyfileobj(source, destination)
        return stage
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def _decode_row(model: type, row: dict[str, Any]) -> Any:
    values: dict[str, Any] = {}
    for prop in sa_inspect(model).column_attrs:
        if prop.key not in row:
            continue
        value = row[prop.key]
        column_type = prop.columns[0].type
        if value is not None and isinstance(column_type, DateTime):
            value = dt.datetime.fromisoformat(value)
        elif value is not None and isinstance(column_type, Date):
            value = dt.date.fromisoformat(value)
        elif value is not None and isinstance(column_type, Time):
            value = dt.time.fromisoformat(value)
        values[prop.key] = value
    return model(**values)


def _reset_postgres_sequences(db: Session) -> None:
    if not db.bind or db.bind.dialect.name != "postgresql":
        return
    for model in ID_MODELS:
        table = model.__tablename__
        db.execute(text(
            f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
            f"COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) FROM \"{table}\""
        ))


def _replace_database(db: Session, data: dict[str, Any]) -> None:
    from ..encounters import reconcile_linked_encounters

    for model in DELETE_ORDER:
        db.execute(delete(model))
    db.flush()
    for key, model in BACKUP_TABLES:
        db.add_all(_decode_row(model, row) for row in data[key])
        db.flush()
    original_updates: dict[int, dt.datetime] = {}
    for species in db.query(Species).all():
        previous_update = species.updated_at
        species.refresh_derived()
        if db.is_modified(species, include_collections=False):
            original_updates[species.id] = previous_update
    db.flush()
    for species_id, updated_at in original_updates.items():
        db.execute(
            update(Species)
            .where(Species.id == species_id)
            .values(updated_at=updated_at)
        )
    reconcile_linked_encounters(db)
    _reset_postgres_sequences(db)
    db.commit()


@router.post("/load")
def load_backup(
    file: Annotated[UploadFile, File(...)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, int | str]:
    """Replace the current collection with one validated full backup."""
    if not _restore_lock.acquire(blocking=False):
        raise HTTPException(409, "Es wird bereits ein Backup geladen")

    storage = _local_storage()
    root = storage.root.resolve()
    root.parent.mkdir(parents=True, exist_ok=True)
    previous = root.with_name(f".compedium-before-restore-{uuid.uuid4().hex}")
    stage: Path | None = None
    try:
        try:
            archive = zipfile.ZipFile(file.file)
        except (zipfile.BadZipFile, OSError) as exc:
            raise HTTPException(422, "Die ausgewählte Datei ist kein gültiges Backup") from exc

        with archive:
            data = _load_manifest(archive)
            names = {info.filename for info in archive.infolist() if not info.is_dir()}
            _validate_relations(data, names)
            stage = _stage_media(archive, root.parent)

        if root.exists():
            root.rename(previous)
        try:
            stage.rename(root)
        except Exception:
            if previous.exists() and not root.exists():
                previous.rename(root)
            raise
        stage = None

        try:
            _replace_database(db, data)
        except Exception:
            db.rollback()
            if root.exists():
                shutil.rmtree(root)
            if previous.exists():
                previous.rename(root)
            raise

        if previous.exists():
            shutil.rmtree(previous)
        return {
            "message": "Backup erfolgreich geladen",
            "profiles": len(data["profiles"]),
            "species": len(data["species"]),
            "observations": len(data["observations"]),
            "photos": len(data["photos"]),
        }
    finally:
        if stage and stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
        _restore_lock.release()
