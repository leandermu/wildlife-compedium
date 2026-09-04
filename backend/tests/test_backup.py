import datetime as dt
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile

from app.db import Base
from app.models import Observation, Profile, Species, UserPhoto
from app.routers.backup import (
    _load_manifest,
    _manifest,
    _replace_database,
    load_backup,
    save_backup,
    storage_stats,
    _stage_media,
    _validate_relations,
)
from app.storage import LocalStorage


class BackupRoundtripTest(unittest.TestCase):
    @staticmethod
    def _collection(db: Session) -> None:
        profile = Profile(name="Angelika", avatar="🦉", gender="female", is_default=True)
        species = Species(
            slug="testvogel",
            common_name="Testvogel",
            scientific_name="Avis testis",
            group="bird",
        )
        db.add_all([profile, species])
        db.flush()
        species.created_by_profile_id = profile.id
        observation = Observation(
            profile_id=profile.id,
            species_id=species.id,
            location_name="Garten",
            date=dt.date(2026, 9, 1),
            time=dt.time(7, 45),
        )
        db.add(observation)
        db.flush()
        db.add(UserPhoto(
            profile_id=profile.id,
            species_id=species.id,
            observation_id=observation.id,
            storage_key="photos/test.jpg",
            original_filename="test.jpg",
            date=dt.date(2026, 9, 1),
            time=dt.time(7, 45),
        ))
        db.commit()

    def test_complete_roundtrip_keeps_relations_and_media(self) -> None:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        with Session(engine) as db:
            self._collection(db)
            data = _manifest(db)

        archive_bytes = io.BytesIO()
        with zipfile.ZipFile(archive_bytes, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("backup.json", json.dumps(data, ensure_ascii=False))
            archive.writestr("media/photos/test.jpg", b"photo-data")
        archive_bytes.seek(0)

        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(archive_bytes) as archive:
                restored = _load_manifest(archive)
                names = {item.filename for item in archive.infolist() if not item.is_dir()}
                _validate_relations(restored, names)
                stage = _stage_media(archive, Path(temp_dir))
            self.assertEqual((stage / "photos/test.jpg").read_bytes(), b"photo-data")

        with Session(engine) as db:
            db.add(Species(slug="spaeter", common_name="Später", group="other"))
            db.commit()
            _replace_database(db, restored)

        with Session(engine) as db:
            self.assertEqual(db.scalar(select(func.count(Profile.id))), 2)
            self.assertIsNotNone(
                db.scalar(select(Profile).where(Profile.is_shared.is_(True)))
            )
            self.assertEqual(db.scalar(select(func.count(Species.id))), 1)
            photo = db.scalar(select(UserPhoto))
            observation = db.scalar(select(Observation))
            profile = db.scalar(select(Profile))
            species = db.scalar(select(Species))
            self.assertIsNotNone(photo)
            self.assertEqual(photo.observation_id, observation.id)
            self.assertEqual(photo.profile_id, profile.id)
            self.assertEqual(profile.avatar, "🦉")
            self.assertEqual(profile.gender, "female")
            self.assertEqual(species.created_by_profile_id, profile.id)
            self.assertEqual(observation.time, dt.time(7, 45))
            self.assertEqual(photo.time, dt.time(7, 45))

        engine.dispose()

    def test_save_and_load_endpoints_replace_database_and_media_together(self) -> None:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        with tempfile.TemporaryDirectory() as temp_dir:
            media_root = Path(temp_dir) / "media"
            media_file = media_root / "photos/test.jpg"
            media_file.parent.mkdir(parents=True)
            media_file.write_bytes(b"original-photo")
            storage = LocalStorage(media_root, "/media")

            with patch("app.routers.backup.get_storage", return_value=storage):
                with Session(engine) as db:
                    self._collection(db)
                    response = save_backup(db)
                    archive_path = Path(response.path)
                    archive_bytes = archive_path.read_bytes()
                    archive_path.unlink()

                media_file.write_bytes(b"changed-photo")
                (media_root / "extra.txt").write_text("remove me", encoding="utf-8")
                with Session(engine) as db:
                    db.add(Species(slug="spaeter", common_name="Später", group="other"))
                    db.commit()
                    result = load_backup(
                        UploadFile(io.BytesIO(archive_bytes), filename="backup.wcbackup"),
                        db,
                    )

            self.assertEqual(result["species"], 1)
            self.assertEqual(media_file.read_bytes(), b"original-photo")
            self.assertFalse((media_root / "extra.txt").exists())
            with Session(engine) as db:
                self.assertEqual(db.scalar(select(func.count(Species.id))), 1)
                self.assertEqual(db.scalar(select(func.count(UserPhoto.id))), 1)

        engine.dispose()

    def test_storage_stats_include_media_database_and_collection_counts(self) -> None:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            media_root = root / "media"
            files = {
                "photos/original.jpg": b"12345",
                "display/photo.jpg": b"123",
                "thumbs/photo.jpg": b"12",
                "reference/species.jpg": b"1234",
                "reference-thumb/species.jpg": b"1",
                "misc/cache.bin": b"123456",
            }
            for key, content in files.items():
                target = media_root / key
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)

            database_path = root / "compendium.db"
            database_path.write_bytes(b"1234567")
            Path(f"{database_path}-wal").write_bytes(b"12345678")
            Path(f"{database_path}-shm").write_bytes(b"123456789")
            storage = LocalStorage(media_root, "/media")

            with Session(engine) as db:
                self._collection(db)
                with (
                    patch("app.routers.backup.get_storage", return_value=storage),
                    patch(
                        "app.routers.backup.settings",
                        SimpleNamespace(sqlite_path=database_path),
                    ),
                ):
                    result = storage_stats(db)

            self.assertEqual(result.originals_bytes, 5)
            self.assertEqual(result.derivatives_bytes, 5)
            self.assertEqual(result.references_bytes, 5)
            self.assertEqual(result.other_bytes, 6)
            self.assertEqual(result.media_bytes, 21)
            self.assertEqual(result.database_bytes, 24)
            self.assertEqual(result.total_bytes, 45)
            self.assertEqual(result.stored_file_count, 6)
            self.assertEqual(result.profile_count, 1)
            self.assertEqual(result.species_count, 1)
            self.assertEqual(result.observation_count, 1)
            self.assertEqual(result.photo_count, 1)

        engine.dispose()


if __name__ == "__main__":
    unittest.main()
