from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from rubra_packager.source import locate_static_output, resolve_static_source


class SourceTests(unittest.TestCase):
    def test_root_index_wins(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "index.html").write_text("ok", encoding="utf-8")
            self.assertEqual(locate_static_output(root), root)

    def test_dist_output_found(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "dist").mkdir()
            (root / "dist" / "index.html").write_text("ok", encoding="utf-8")
            self.assertEqual(locate_static_output(root), root / "dist")

    def test_untrusted_source_build_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "package.json").write_text('{"scripts":{"build":"echo hi"}}', encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "trusted"):
                resolve_static_source(root, allow_build=False, log=[])

class FrameworkOutputSafetyTests(unittest.TestCase):
    def test_react_public_folder_is_not_mistaken_for_build_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "public").mkdir()
            (root / "public" / "index.html").write_text("template", encoding="utf-8")
            (root / "package.json").write_text('{"scripts":{"build":"react-scripts build"},"dependencies":{"react":"1"}}', encoding="utf-8")
            self.assertIsNone(locate_static_output(root))
