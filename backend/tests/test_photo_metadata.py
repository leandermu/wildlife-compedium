import datetime as dt
import io
import unittest

from PIL import Image

from app.models import Species, UserPhoto
from app.queries import photo_out, to_list_item
from app.routers.photos import _extract


class PhotoMetadataTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
