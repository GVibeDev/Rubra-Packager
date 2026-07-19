from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path

from rubra_packager.launcher import launcher_source, write_launcher


class LauncherTests(unittest.TestCase):
    def test_launcher_handles_quotes_and_unicode(self):
        source = launcher_source({"title": 'Arena "Rubra" — α', "appId": "arena-rubra", "storageName": "ArenaRubra", "entryPoint": "index.html", "width": 1000, "height": 700})
        ast.parse(source)
        self.assertIn('127.0.0.1', source)
        self.assertIn('private_mode=False', source)
        self.assertIn('storage_path=storage_path', source)

    def test_launcher_is_written_as_utf8(self):
        with tempfile.TemporaryDirectory() as temp:
            path = write_launcher(Path(temp) / "launcher.py", {"title": "Rubra — Ω", "appId": "rubra", "storageName": "Rubra", "entryPoint": "index.html"})
            ast.parse(path.read_text(encoding="utf-8"))
