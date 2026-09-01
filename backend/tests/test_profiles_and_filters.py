import datetime as dt
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.achievements import evaluate
from app.db import Base
from app.models import Observation, Profile, Species
from app.queries import SpeciesQuery


class ProfileAndFilterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

    def tearDown(self) -> None:
        self.engine.dispose()

    def test_gender_changes_achievement_name(self) -> None:
        with Session(self.engine) as db:
            male = Profile(name="Laurin", gender="male")
            female = Profile(name="Angelika", gender="female")
            db.add_all([male, female])
            db.commit()
            male_names = {item["id"]: item["name"] for item in evaluate(db, male.id)}
            female_names = {item["id"]: item["name"] for item in evaluate(db, female.id)}
            self.assertEqual(male_names["alpine_hunter"], "Alpenjäger")
            self.assertEqual(female_names["alpine_hunter"], "Alpenjägerin")

    def test_seen_includes_observation_without_photo_and_systematic_sort_uses_group(self) -> None:
        with Session(self.engine) as db:
            profile = Profile(name="Leander", gender="male")
            mammal = Species(slug="m", common_name="M", group="mammal", sort_index=0)
            amphibian = Species(slug="a", common_name="A", group="amphibian", sort_index=0)
            bird = Species(slug="b", common_name="B", group="bird", sort_index=999)
            db.add_all([profile, mammal, amphibian, bird])
            db.flush()
            db.add(Observation(
                profile_id=profile.id,
                species_id=amphibian.id,
                date=dt.date(2026, 9, 1),
                time=dt.time(7, 30),
            ))
            db.commit()

            query = SpeciesQuery(profile.id)
            sorted_rows = db.execute(
                query.apply_sort(query.base(Species), "default")
            ).scalars().all()
            self.assertEqual([item.group for item in sorted_rows], ["bird", "mammal", "amphibian"])

            seen_rows = db.execute(
                query.apply_filters(query.base(Species), seen=["seen"])
            ).scalars().all()
            self.assertEqual([item.slug for item in seen_rows], ["a"])


if __name__ == "__main__":
    unittest.main()
