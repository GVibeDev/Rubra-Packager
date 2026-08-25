from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class StableReleaseContractTests(unittest.TestCase):
    def test_public_guides_exist(self):
        for rel in (
            "docs/USER_GUIDE.md",
            "docs/BUILDING.md",
            "docs/PUBLISHING.md",
            "docs/DEVELOPMENT_HISTORY.md",
            "docs/PUBLICATION_CHECKLIST.md",
        ):
            self.assertTrue((ROOT / rel).is_file(), rel)

    def test_github_is_source_only_for_v1(self):
        self.assertFalse((ROOT / ".github/workflows/release.yml").exists())
        publishing = (ROOT / "docs/PUBLISHING.md").read_text(encoding="utf-8")
        self.assertIn("does **not** contain generated", publishing)
        self.assertIn("external product channels", publishing)

    def test_web_and_python_builders_use_windows_version_metadata(self):
        for name in ("build_windows.py", "build_python.py"):
            text = (ROOT / "src/rubra_packager" / name).read_text(encoding="utf-8")
            self.assertIn("write_version_file", text)
            self.assertIn("--version-file=", text)

    def test_setup_manifest_version_is_not_hardcoded(self):
        text = (ROOT / "src/rubra_packager/build_setup.py").read_text(encoding="utf-8")
        self.assertIn('"version": __version__', text)


if __name__ == "__main__":
    unittest.main()
