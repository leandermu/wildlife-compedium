import datetime as dt
import io
import unittest

from PIL import Image

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


if __name__ == "__main__":
    unittest.main()
