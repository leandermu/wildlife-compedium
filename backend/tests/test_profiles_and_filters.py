import datetime as dt
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.achievements import evaluate
from app.db import Base
from app.models import Observation, Profile, Species, UserPhoto
from app.queries import SpeciesQuery, derive_status
from app.routers.species import facets as species_facets
from app.vocab import STATUSES


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

            facet_result = species_facets(db, profile)
            self.assertEqual(
                {item.value for item in facet_result.statuses},
                {"locked", "unlocked"},
            )
            self.assertEqual(
                {item.value for item in facet_result.seen},
                {"seen", "unseen"},
            )

    def test_species_status_only_has_locked_and_unlocked(self) -> None:
        self.assertEqual(derive_status(0), "locked")
        self.assertEqual(derive_status(1), "unlocked")
        self.assertEqual(derive_status(12), "unlocked")
        self.assertEqual(set(STATUSES), {"locked", "unlocked"})

    def test_legacy_tags_are_moved_into_structured_species_fields(self) -> None:
        species = Species(
            slug="adler",
            common_name="Adler",
            scientific_name="Aquila test",
            group="bird",
            order_name="Greifvögel",
            habitats=["night"],
            regions=["europe"],
            tags=["greifvogel", "afrika", "alpen", "zugvogel", "nacht"],
        )

        species.refresh_derived()

        self.assertEqual(species.class_name, "Aves")
        self.assertEqual(species.activity, "nocturnal")
        self.assertIn("africa", species.regions)
        self.assertIn("alps", species.habitats)
        self.assertNotIn("night", species.habitats)
        self.assertEqual(species.tags, ["zugvogel"])

        with Session(self.engine) as db:
            db.add(species)
            db.commit()
            query = SpeciesQuery(0)
            result = db.execute(
                query.apply_filters(
                    query.base(Species),
                    class_name=["Aves"],
                    order=["Greifvögel"],
                    activity=["nocturnal"],
                )
            ).scalars().all()
            self.assertEqual([item.slug for item in result], ["adler"])

    def test_captive_entries_can_be_excluded_and_filtered_per_profile(self) -> None:
        with Session(self.engine) as db:
            profile = Profile(
                name="Leander",
                gender="male",
                exclude_captive_from_progress=True,
            )
            captive_species = Species(
                slug="zootier", common_name="Zootier", group="mammal"
            )
            wild_species = Species(
                slug="wildtier", common_name="Wildtier", group="mammal"
            )
            db.add_all([profile, captive_species, wild_species])
            db.flush()
            captive_observation = Observation(
                profile_id=profile.id,
                species_id=captive_species.id,
                encounter_type="captive",
            )
            wild_observation = Observation(
                profile_id=profile.id,
                species_id=wild_species.id,
                encounter_type="wild",
            )
            db.add_all([captive_observation, wild_observation])
            db.flush()
            db.add_all([
                UserPhoto(
                    profile_id=profile.id,
                    species_id=captive_species.id,
                    observation_id=captive_observation.id,
                    storage_key="captive.jpg",
                    encounter_type="captive",
                ),
                UserPhoto(
                    profile_id=profile.id,
                    species_id=wild_species.id,
                    observation_id=wild_observation.id,
                    storage_key="wild.jpg",
                    encounter_type="wild",
                ),
            ])
            db.commit()

            query = SpeciesQuery(profile.id, exclude_captive=True)
            unlocked = db.execute(
                query.apply_filters(query.base(Species), status=["unlocked"])
            ).scalars().all()
            self.assertEqual([item.slug for item in unlocked], ["wildtier"])

            captive = db.execute(
                query.apply_filters(
                    query.base(Species), encounter=["captive"]
                )
            ).scalars().all()
            self.assertEqual([item.slug for item in captive], ["zootier"])

            achievements = {item["id"]: item for item in evaluate(db, profile.id)}
            self.assertEqual(achievements["photo_volume"]["progress"], 1)

            profile.exclude_captive_from_progress = False
            db.commit()
            achievements = {item["id"]: item for item in evaluate(db, profile.id)}
            self.assertEqual(achievements["photo_volume"]["progress"], 2)


if __name__ == "__main__":
    unittest.main()
