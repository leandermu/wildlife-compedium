import asyncio
import datetime as dt
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from starlette.datastructures import UploadFile

from app.db import Base
from app.models import Observation, Profile, Species, UserPhoto
from app.queries import photo_out, to_list_item
from app.routers.photos import (
    _extract,
    ensure_browser_derivatives,
    map_photos,
    upload_photo,
    update_photo,
)
from app.schemas import PhotoUpdate
from app.storage import LocalStorage


class PhotoMetadataTest(unittest.TestCase):
    def test_manual_photo_coordinates_are_saved_on_the_linked_encounter(self) -> None:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        try:
            with Session(engine) as db:
                profile = Profile(name="Leander")
                species = Species(slug="fuchs", common_name="Fuchs", group="mammal")
                db.add_all([profile, species])
                db.flush()
                observation = Observation(profile_id=profile.id, species_id=species.id)
                db.add(observation)
                db.flush()
                photo = UserPhoto(
                    profile_id=profile.id,
                    species_id=species.id,
                    observation_id=observation.id,
                    storage_key="fuchs.jpg",
                )
                db.add(photo)
                db.commit()

                result = update_photo(
                    photo.id,
                    PhotoUpdate(
                        location_name="Isarauen",
                        latitude=48.123456,
                        longitude=11.654321,
                    ),
                    db,
                    profile,
                )

                self.assertEqual((result.latitude, result.longitude), (48.123456, 11.654321))
                self.assertEqual(observation.location_name, "Isarauen")
                self.assertEqual(
                    (observation.latitude, observation.longitude),
                    (48.123456, 11.654321),
                )
        finally:
            engine.dispose()

    def test_map_photos_respects_profile_scope_and_both_coordinate_sources(self) -> None:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        try:
            with Session(engine) as db:
                shared = Profile(name="Gemeinsam", is_shared=True)
                first = Profile(name="Leander", avatar="🦊")
                second = Profile(name="Angelika", avatar="🦉")
                species = Species(slug="eisvogel", common_name="Eisvogel", group="bird")
                db.add_all([shared, first, second, species])
                db.flush()
                observation = Observation(
                    profile_id=second.id,
                    species_id=species.id,
                    location_name="Am See",
                    latitude=48.1,
                    longitude=11.5,
                )
                db.add(observation)
                db.flush()
                db.add_all([
                    UserPhoto(
                        profile_id=first.id,
                        species_id=species.id,
                        storage_key="first.jpg",
                        location_name="Im Wald",
                        photo_metadata={"latitude": 47.9, "longitude": 11.2},
                    ),
                    UserPhoto(
                        profile_id=second.id,
                        species_id=species.id,
                        observation_id=observation.id,
                        storage_key="second.jpg",
                        location_name="Am See",
                    ),
                    UserPhoto(
                        profile_id=first.id,
                        species_id=species.id,
                        storage_key="without-location.jpg",
                    ),
                ])
                db.commit()

                personal = map_photos(db, first)
                combined = map_photos(db, shared)
                self.assertEqual(len(personal), 1)
                self.assertEqual((personal[0].latitude, personal[0].longitude), (47.9, 11.2))
                self.assertEqual(len(combined), 2)
                self.assertEqual(
                    {(photo.profile_name, photo.latitude, photo.longitude) for photo in combined},
                    {("Leander", 47.9, 11.2), ("Angelika", 48.1, 11.5)},
                )
        finally:
            engine.dispose()

    def test_heif_is_decoded_with_exif_thumbnail_and_display_copy(self) -> None:
        exif = Image.Exif()
        exif[271] = "Compedium Camera"
        exif[272] = "Test Model"
        exif[36867] = "2026:08:31 12:34:56"
        image = Image.new("RGB", (64, 48), "green")
        source = io.BytesIO()
        image.save(source, format="HEIF", exif=exif)

        metadata, taken, thumbnail, _lat, _lon, display = _extract(
            source.getvalue(),
            create_display_copy=True,
        )

        self.assertEqual(metadata["camera_make"], "Compedium Camera")
        self.assertEqual(metadata["camera_model"], "Test Model")
        self.assertEqual(metadata["file_format"], "HEIF")
        self.assertEqual(taken, dt.date(2026, 8, 31))
        self.assertTrue(metadata["exif"])
        self.assertIsNotNone(thumbnail)
        self.assertIsNotNone(display)
        with Image.open(io.BytesIO(display)) as converted:
            self.assertEqual(converted.format, "JPEG")

    def test_browser_display_copy_is_used_in_detail_and_species_card(self) -> None:
        photo = UserPhoto(
            id=4,
            species_id=2,
            storage_key="photos/original.heic",
            display_key="display/browser.jpg",
            original_filename="original.heic",
            location_name="",
            caption="",
            created_at=dt.datetime(2026, 9, 1, 12, 0),
        )
        species = Species(
            id=2,
            slug="testtier",
            common_name="Testtier",
            scientific_name="Animalia testis",
            group="mammal",
            family="Testtiere",
            difficulty=1,
            regions=[],
            habitats=[],
            size="",
        )

        self.assertEqual(photo_out(photo)["url"], "/media/display/browser.jpg")
        card = to_list_item(species, 1, 1, photo)
        self.assertEqual(card.best_photo_url, "/media/display/browser.jpg")

    def test_exif_field_name_never_replaces_storage_key_on_upload(self) -> None:
        image = Image.new("RGB", (64, 48), "blue")
        exif = Image.Exif()
        exif[306] = "2026:09:01 13:14:15"
        source = io.BytesIO()
        image.save(source, format="JPEG", exif=exif)

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        try:
            with tempfile.TemporaryDirectory() as temp_dir, Session(engine) as db:
                profile = Profile(name="Leander", is_default=True)
                species = Species(
                    slug="testtier", common_name="Testtier", group="mammal"
                )
                db.add_all([profile, species])
                db.commit()
                storage = LocalStorage(Path(temp_dir), "/media")
                upload = UploadFile(io.BytesIO(source.getvalue()), filename="foto.jpg")

                with patch("app.routers.photos.get_storage", return_value=storage):
                    asyncio.run(upload_photo(db, profile, species.id, upload))

                saved = db.scalar(select(UserPhoto))
                self.assertIsNotNone(saved)
                self.assertTrue(saved.storage_key.startswith("photos/"))
                self.assertIsNotNone(storage.path(saved.storage_key))
                self.assertNotIn(saved.storage_key, {"taken_at", "taken_at_file"})
                self.assertEqual(saved.time, dt.time(13, 14, 15))
        finally:
            engine.dispose()

    def test_startup_repair_recovers_corrupted_original_key_from_thumbnail(self) -> None:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        sessions = sessionmaker(bind=engine, expire_on_commit=False)
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                storage = LocalStorage(Path(temp_dir), "/media")
                stem = "6cf790b3b1ca4bbca114472f45f3e67c"
                original_key = f"photos/1/testtier/{stem}.jpg"
                thumb_key = f"thumbs/1/testtier/{stem}.jpg"
                storage.save_bytes(original_key, b"original")
                storage.save_bytes(thumb_key, b"thumbnail")
                with sessions() as db:
                    profile = Profile(id=1, name="Leander", is_default=True)
                    species = Species(
                        id=1, slug="testtier", common_name="Testtier", group="mammal"
                    )
                    db.add_all([profile, species])
                    db.flush()
                    db.add(UserPhoto(
                        profile_id=profile.id,
                        species_id=species.id,
                        storage_key="taken_at_file",
                        thumb_key=thumb_key,
                        original_filename="foto.jpg",
                    ))
                    db.commit()

                with (
                    patch("app.routers.photos.get_storage", return_value=storage),
                    patch("app.db.SessionLocal", sessions),
                ):
                    self.assertEqual(ensure_browser_derivatives(), 1)

                with sessions() as db:
                    repaired = db.scalar(select(UserPhoto))
                    self.assertEqual(repaired.storage_key, original_key)
        finally:
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
