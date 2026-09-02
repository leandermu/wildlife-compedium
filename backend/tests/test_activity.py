import datetime as dt
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.models import Observation, Profile, Species, UserPhoto
from app.routers.stats import _activity_entries, _recent_activity


class ActivityFeedTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

    def tearDown(self) -> None:
        self.engine.dispose()

    def test_feed_combines_profiles_without_duplicate_seen_event_for_photo(self) -> None:
        with Session(self.engine) as db:
            leander = Profile(name="Leander", avatar="🦊")
            laurin = Profile(name="Laurin", avatar="🦉")
            angelika = Profile(name="Angelika", avatar="🦋")
            db.add_all([leander, laurin, angelika])
            db.flush()
            species = Species(
                slug="fuchs",
                common_name="Rotfuchs",
                group="mammal",
                created_by_profile_id=leander.id,
                created_at=dt.datetime(2026, 9, 1, 8, 0),
            )
            db.add(species)
            db.flush()
            sighting = Observation(
                profile_id=angelika.id,
                species_id=species.id,
                created_at=dt.datetime(2026, 9, 1, 9, 0),
            )
            photo_encounter = Observation(
                profile_id=laurin.id,
                species_id=species.id,
                created_at=dt.datetime(2026, 9, 1, 10, 0),
            )
            db.add_all([sighting, photo_encounter])
            db.flush()
            db.add(UserPhoto(
                profile_id=laurin.id,
                species_id=species.id,
                observation_id=photo_encounter.id,
                storage_key="photos/fuchs.jpg",
                created_at=dt.datetime(2026, 9, 1, 10, 0),
            ))
            db.commit()

            feed = _recent_activity(db)
            self.assertEqual(
                [(entry.profile_name, entry.kind) for entry in feed],
                [
                    ("Laurin", "photographed"),
                    ("Angelika", "seen"),
                    ("Leander", "added"),
                ],
            )
            self.assertTrue(all(entry.occurred_at.tzinfo is not None for entry in feed))

            db.delete(sighting)
            db.commit()

            feed_after_delete = _activity_entries(db)
            self.assertNotIn(
                ("Angelika", "seen"),
                [(entry.profile_name, entry.kind) for entry in feed_after_delete],
            )

    def test_recent_feed_is_limited_to_ten_entries_by_default(self) -> None:
        with Session(self.engine) as db:
            profile = Profile(name="Leander", avatar="🦊")
            db.add(profile)
            db.flush()
            for index in range(12):
                species = Species(
                    slug=f"art-{index}",
                    common_name=f"Art {index}",
                    group="bird",
                )
                db.add(species)
                db.flush()
                db.add(Observation(
                    profile_id=profile.id,
                    species_id=species.id,
                    created_at=dt.datetime(2026, 9, 1, 10, index),
                ))
            db.commit()

            self.assertEqual(len(_recent_activity(db)), 10)


if __name__ == "__main__":
    unittest.main()
