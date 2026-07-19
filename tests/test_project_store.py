from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from rubra_packager.models import ProjectRecord
from rubra_packager.project_store import ProjectStore


class ProjectStoreTests(unittest.TestCase):
    def test_upsert_roundtrip_and_delete(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            store = ProjectStore(root / "projects.json")
            store.upsert(ProjectRecord(project_id="demo", name="Demo", source_path=str(source)))
            self.assertEqual(store.get("demo").name, "Demo")
            self.assertTrue(store.delete("demo"))
            self.assertEqual(store.list(), [])

    def test_registry_does_not_copy_project_content(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "large-source"
            source.mkdir()
            (source / "index.html").write_text("hello", encoding="utf-8")
            registry = root / "projects.json"
            store = ProjectStore(registry)
            store.upsert(ProjectRecord(project_id="demo", name="Demo", source_path=str(source)))
            self.assertLess(registry.stat().st_size, 4096)
