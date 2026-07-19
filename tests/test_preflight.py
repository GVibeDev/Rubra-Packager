from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from rubra_packager.preflight import run_preflight
from rubra_packager.profiles import ProfileRegistry


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.profile = ProfileRegistry().get("arena-rubra")

    def _report(self, root: Path, variant: str = "full"):
        return run_preflight(root, self.profile, variant)

    def test_valid_project_has_optional_manifest_warning_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "index.html").write_text('<link rel="stylesheet" href="style.css">', encoding="utf-8")
            (root / "style.css").write_text("body{}", encoding="utf-8")
            report = self._report(root)
            self.assertEqual(report.errors, 0)
            self.assertTrue(any(item.code == "MANIFEST_NOT_FOUND" for item in report.findings))

    def test_missing_html_reference_is_error(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "index.html").write_text('<script src="missing.js"></script>', encoding="utf-8")
            report = self._report(root)
            self.assertTrue(any(item.code == "REFERENCE_MISSING" for item in report.findings))

    def test_invalid_utf8_is_error(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "index.html").write_bytes(b"\x97")
            report = self._report(root)
            self.assertTrue(any(item.code == "INVALID_UTF8" for item in report.findings))

    def test_lite_excluded_reference_is_error(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "assets" / "music").mkdir(parents=True)
            (root / "index.html").write_text('<audio src="assets/music/theme.mp3"></audio>', encoding="utf-8")
            (root / "assets" / "music" / "theme.mp3").write_bytes(b"audio")
            report = self._report(root, "lite")
            self.assertTrue(any(item.code == "REFERENCE_EXCLUDED" for item in report.findings))

    def test_array_from_and_data_strings_are_not_imports(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "index.html").write_text('<script type="module" src="src/app.js"></script>', encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "app.js").write_text(
                'const a = Array.from("file"); const b = "dataUrl"; const c = "image/png";',
                encoding="utf-8",
            )
            report = self._report(root)
            self.assertEqual(report.errors, 0)

    def test_blob_urls_and_template_literals_are_not_static_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "index.html").write_text('<script type="module" src="src/app.js"></script>', encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "app.js").write_text(
                'const u = URL.createObjectURL(blob); const x = `${src}`; const y = `${asset(name)}`;',
                encoding="utf-8",
            )
            report = self._report(root)
            self.assertEqual(report.errors, 0)

    def test_local_js_import_missing_is_error(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "index.html").write_text('<script type="module" src="src/app.js"></script>', encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "app.js").write_text('import value from "./missing.js";', encoding="utf-8")
            report = self._report(root)
            self.assertTrue(any(item.code == "REFERENCE_MISSING" and item.path == "src/app.js" for item in report.findings))

    def test_extensionless_and_directory_imports_resolve(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "index.html").write_text('<script type="module" src="src/app.js"></script>', encoding="utf-8")
            (root / "src" / "lib").mkdir(parents=True)
            (root / "src" / "helper.js").write_text("export default 1;", encoding="utf-8")
            (root / "src" / "lib" / "index.js").write_text("export default 2;", encoding="utf-8")
            (root / "src" / "app.js").write_text(
                'import helper from "./helper"; import lib from "./lib";',
                encoding="utf-8",
            )
            report = self._report(root)
            self.assertEqual(report.errors, 0)

    def test_bare_module_specifier_is_not_treated_as_project_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "index.html").write_text('<script type="module" src="src/app.js"></script>', encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "app.js").write_text('import thing from "package-name";', encoding="utf-8")
            report = self._report(root)
            self.assertEqual(report.errors, 0)

    def test_new_url_import_meta_is_checked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "index.html").write_text('<script type="module" src="src/app.js"></script>', encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "app.js").write_text(
                'const icon = new URL("../assets/missing.webp", import.meta.url);',
                encoding="utf-8",
            )
            report = self._report(root)
            self.assertTrue(any(item.code == "REFERENCE_MISSING" for item in report.findings))

    def test_json_and_docs_are_utf8_checked_but_not_reference_scanned(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "index.html").write_text("<main></main>", encoding="utf-8")
            (root / "config.json").write_text('{"note":"from \\\"missing\\\""}', encoding="utf-8")
            (root / "docs").mkdir()
            (root / "docs" / "notes.md").write_text('src="missing.png"', encoding="utf-8")
            report = self._report(root)
            self.assertEqual(report.errors, 0)

    def test_test_sources_do_not_block_runtime_preflight(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "index.html").write_text("<main></main>", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests" / "smoke.js").write_text(
                'const expected = "assets/audio/missing.mp3"; import x from "./missing.js";',
                encoding="utf-8",
            )
            report = self._report(root)
            self.assertEqual(report.errors, 0)

    def test_root_relative_html_reference_resolves_from_project_root(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "assets").mkdir()
            (root / "assets" / "icon.png").write_bytes(b"png")
            (root / "index.html").write_text('<img src="/assets/icon.png">', encoding="utf-8")
            report = self._report(root)
            self.assertEqual(report.errors, 0)

    def test_duplicate_findings_are_collapsed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "index.html").write_text(
                '<img src="missing.png"><img src="missing.png">',
                encoding="utf-8",
            )
            report = self._report(root)
            matches = [item for item in report.findings if item.code == "REFERENCE_MISSING"]
            self.assertEqual(len(matches), 1)
