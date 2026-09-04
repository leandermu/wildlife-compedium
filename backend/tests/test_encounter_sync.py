import datetime as dt
import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db import Base
from app.encounters import reconcile_linked_encounters
from app.models import Observation, Profile, Species, UserPhoto
from app.routers.observations import update_observation
from app.routers.photos import update_photo
from app.schemas import ObservationUpdate, PhotoUpdate


class EncounterSyncTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

    def tearDown(self) -> None:
        self.engine.dispose()

    @staticmethod
    def _collection(db: Session) -> tuple[Profile, Observation, UserPhoto, UserPhoto]:
        profile = Profile(name="Leander", is_default=True)
        species = Species(slug="testtier", common_name="Testtier", group="mammal")
        db.add_all([profile, species])
        db.flush()
        observation = Observation(
            profile_id=profile.id,
            species_id=species.id,
            date=dt.date(2026, 8, 30),
            time=dt.time(9, 15),
            location_name="Am See",
            notes="Erste Notiz",
            animal_sex="female",
            measurement="42 cm",
            observed_weight="1,2 kg",
        )
        db.add(observation)
        db.flush()
        photos = [
            UserPhoto(
                profile_id=profile.id,
                species_id=species.id,
                observation_id=observation.id,
                storage_key=f"photos/{index}.jpg",
                date=dt.date(2025, 1, index),
                location_name="Alter Ort",
                caption="Alter Fototext",
            )
            for index in (1, 2)
        ]
        db.add_all(photos)
        db.commit()
        return profile, observation, photos[0], photos[1]

    def test_reconcile_prefers_encounter_and_aligns_all_photos(self) -> None:
        with Session(self.engine) as db:
            _, observation, _, _ = self._collection(db)
            self.assertEqual(reconcile_linked_encounters(db), 1)
            db.commit()
            for photo in observation.photos:
                self.assertEqual(photo.date, observation.date)
                self.assertEqual(photo.time, observation.time)
                self.assertEqual(photo.location_name, observation.location_name)
                self.assertEqual(photo.caption, observation.notes)
                self.assertEqual(photo.animal_sex, "female")
                self.assertEqual(photo.measurement, "42 cm")
                self.assertEqual(photo.observed_weight, "1,2 kg")

    def test_photo_edit_updates_encounter_and_sibling_photo(self) -> None:
        with Session(self.engine) as db:
            profile, observation, photo, sibling = self._collection(db)
            update_photo(
                photo.id,
                PhotoUpdate(
                    date=dt.date(2026, 9, 1),
                    time=dt.time(18, 20),
                    location_name="Im Wald",
                    caption="Gemeinsame Notiz",
                    animal_sex="male",
                    measurement="43 cm",
                    observed_weight="1,3 kg",
                ),
                db,
                profile,
            )
            db.refresh(observation)
            db.refresh(sibling)
            self.assertEqual(observation.date, dt.date(2026, 9, 1))
            self.assertEqual(observation.time, dt.time(18, 20))
            self.assertEqual(observation.location_name, "Im Wald")
            self.assertEqual(observation.notes, "Gemeinsame Notiz")
            self.assertEqual(observation.animal_sex, "male")
            self.assertEqual(observation.measurement, "43 cm")
            self.assertEqual(observation.observed_weight, "1,3 kg")
            self.assertEqual(sibling.date, observation.date)
            self.assertEqual(sibling.caption, observation.notes)

    def test_encounter_edit_updates_every_linked_photo(self) -> None:
        with Session(self.engine) as db:
            profile, observation, _, _ = self._collection(db)
            update_observation(
                observation.id,
                ObservationUpdate(
                    date=dt.date(2026, 9, 2),
                    time=dt.time(7, 5),
                    location_name="Im Garten",
                    notes="Zwei Fotos, eine Begegnung",
                    animal_sex="unknown",
                    measurement="44 cm",
                    observed_weight="1,4 kg",
                ),
                db,
                profile,
            )
            photos = db.scalars(
                select(UserPhoto).where(UserPhoto.observation_id == observation.id)
            ).all()
            self.assertEqual(len(photos), 2)
            for photo in photos:
                self.assertEqual(photo.date, dt.date(2026, 9, 2))
                self.assertEqual(photo.time, dt.time(7, 5))
                self.assertEqual(photo.location_name, "Im Garten")
                self.assertEqual(photo.caption, "Zwei Fotos, eine Begegnung")
                self.assertEqual(photo.animal_sex, "unknown")
                self.assertEqual(photo.measurement, "44 cm")
                self.assertEqual(photo.observed_weight, "1,4 kg")


if __name__ == "__main__":
    unittest.main()
