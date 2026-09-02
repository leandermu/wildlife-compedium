import asyncio
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile

from app.db import Base
from app.models import Profile, Species
from app.routers.species import update_species_manual
from app.storage import LocalStorage


class SpeciesReferenceImageTest(unittest.TestCase):
    def test_editing_species_replaces_and_processes_reference_image(self) -> None:
        source = io.BytesIO()
        Image.new("RGB", (1600, 900), "darkgreen").save(source, format="PNG")

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        try:
            with tempfile.TemporaryDirectory() as temp_dir, Session(engine) as db:
                storage = LocalStorage(Path(temp_dir), "/media")
                storage.save_bytes("reference/old.jpg", b"old reference")
                storage.save_bytes("reference-thumb/old.jpg", b"old thumbnail")
                profile = Profile(name="Leander", is_default=True)
                species = Species(
                    slug="testtier",
                    common_name="Testtier",
                    group="mammal",
                    reference_image="reference/old.jpg",
                    reference_thumb="reference-thumb/old.jpg",
                    reference_credit="Alte Quelle",
                    reference_source="https://example.com/old",
                )
                db.add_all([profile, species])
                db.commit()

                upload = UploadFile(io.BytesIO(source.getvalue()), filename="eigenes-bild.png")
                with patch("app.routers.species.get_storage", return_value=storage):
                    result = asyncio.run(
                        update_species_manual(
                            "testtier",
                            db,
                            profile,
                            json.dumps({"common_name": "Bearbeitetes Testtier"}),
                            upload,
                        )
                    )

                self.assertEqual(result.common_name, "Bearbeitetes Testtier")
                self.assertEqual(result.reference_credit, "Eigenes Referenzbild")
                self.assertIsNone(result.reference_source)
                self.assertIsNotNone(storage.path(species.reference_image))
                self.assertIsNotNone(storage.path(species.reference_thumb))
                self.assertIsNone(storage.path("reference/old.jpg"))
                self.assertIsNone(storage.path("reference-thumb/old.jpg"))

                with Image.open(storage.path(species.reference_image)) as reference:
                    self.assertEqual(reference.size, (1000, 750))
                    self.assertEqual(reference.format, "JPEG")
                with Image.open(storage.path(species.reference_thumb)) as thumbnail:
                    self.assertEqual(thumbnail.size, (480, 360))
                    self.assertEqual(thumbnail.format, "JPEG")
        finally:
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
