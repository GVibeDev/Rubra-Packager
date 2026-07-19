from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from rubra_packager.build_android import AndroidBuilder


class AndroidHelperTests(unittest.TestCase):
    def test_manifest_orientation_is_added_and_updated(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "AndroidManifest.xml"
            path.write_text('<manifest><application><activity android:name=".MainActivity"></activity></application></manifest>', encoding="utf-8")
            AndroidBuilder._patch_manifest(path, "landscape")
            self.assertIn('android:screenOrientation="landscape"', path.read_text(encoding="utf-8"))
            AndroidBuilder._patch_manifest(path, "portrait")
            text = path.read_text(encoding="utf-8")
            self.assertIn('android:screenOrientation="portrait"', text)
            self.assertNotIn('android:screenOrientation="landscape"', text)

    def test_app_strings_are_rewritten_safely(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "strings.xml"
            path.write_text('<?xml version="1.0"?><resources><string name="app_name">Old</string></resources>', encoding="utf-8")
            AndroidBuilder._patch_app_strings(path, 'Arena & Rubra', 'com.example.arena')
            text = path.read_text(encoding="utf-8")
            self.assertIn('Arena &amp; Rubra', text)
            self.assertIn('<string name="package_name">com.example.arena</string>', text)
