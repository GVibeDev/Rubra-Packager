from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from rubra_packager.windows_metadata import version_tuple, write_version_file


class WindowsMetadataTests(unittest.TestCase):
    def test_version_tuple_supports_release_candidate_versions(self):
        self.assertEqual(version_tuple("1.0.0rc1"), (1, 0, 0, 1))
        self.assertEqual(version_tuple("2.3"), (2, 3, 0, 0))

    def test_version_resource_contains_sanitized_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            target = write_version_file(
                Path(temp) / "version.txt",
                app_name="Demo App",
                version="2.3.4",
                publisher="Example\nStudio",
                description="Demo\r\nApplication",
                original_filename="Demo_App.exe",
            )
            text = target.read_text(encoding="utf-8")
            self.assertIn("ProductName', 'Demo App", text)
            self.assertIn("CompanyName', 'Example Studio", text)
            self.assertIn("FileDescription', 'Demo Application", text)
            self.assertIn("filevers=(2, 3, 4, 0)", text)
            self.assertIn("OriginalFilename', 'Demo_App.exe", text)


if __name__ == "__main__":
    unittest.main()
