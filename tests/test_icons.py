from __future__ import annotations

import base64
import io
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from rubra_packager.icons import decode_data_uri, save_windows_ico, write_android_icons


class IconTests(unittest.TestCase):
    def data_uri(self) -> str:
        image = Image.new("RGBA", (300, 180), (220, 170, 50, 255))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")

    def test_decode_and_windows_ico(self):
        with tempfile.TemporaryDirectory() as temp:
            image = decode_data_uri(self.data_uri())
            target = save_windows_ico(image, Path(temp) / "app.ico")
            self.assertTrue(target.is_file())
            self.assertGreater(target.stat().st_size, 100)

    def test_android_icon_resources(self):
        with tempfile.TemporaryDirectory() as temp:
            image = decode_data_uri(self.data_uri())
            created = write_android_icons(image, Path(temp), "#071426")
            self.assertGreaterEqual(len(created), 20)
            self.assertTrue((Path(temp) / "mipmap-xxxhdpi" / "ic_launcher.png").is_file())
            self.assertTrue((Path(temp) / "mipmap-anydpi-v26" / "ic_launcher.xml").is_file())
