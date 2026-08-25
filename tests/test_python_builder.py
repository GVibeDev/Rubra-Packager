from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rubra_packager.python_preflight import inspect_python_project, run_python_preflight


class PythonPreflightTests(unittest.TestCase):
    def test_detects_main_entry_point(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "main.py").write_text("print('ok')\n", encoding="utf-8")
            with patch("rubra_packager.python_preflight.importlib.util.find_spec", return_value=object()):
                report = run_python_preflight(root)
            self.assertTrue(report.ok)
            self.assertEqual(report.entry_point, "main.py")
            self.assertEqual(report.warnings, 1)
            self.assertEqual(report.findings[0].code, "ENTRY_POINT_AUTO_SELECTED")

    def test_reports_python_syntax_error(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "main.py").write_text("if True print('bad')\n", encoding="utf-8")
            with patch("rubra_packager.python_preflight.importlib.util.find_spec", return_value=object()):
                report = run_python_preflight(root, entry_point="main.py")
            self.assertFalse(report.ok)
            self.assertIn("ENTRY_POINT_SYNTAX", {item.code for item in report.findings})

    def test_rejects_data_path_traversal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "main.py").write_text("print('ok')\n", encoding="utf-8")
            with patch("rubra_packager.python_preflight.importlib.util.find_spec", return_value=object()):
                report = run_python_preflight(root, entry_point="main.py", data_paths=["../secret.txt"])
            self.assertFalse(report.ok)
            self.assertIn("DATA_PATH_INVALID", {item.code for item in report.findings})

    def test_rejects_invalid_hidden_import(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "main.py").write_text("print('ok')\n", encoding="utf-8")
            with patch("rubra_packager.python_preflight.importlib.util.find_spec", return_value=object()):
                report = run_python_preflight(root, entry_point="main.py", hidden_imports=["pkg.good", "bad-module!"])
            self.assertFalse(report.ok)
            self.assertIn("HIDDEN_IMPORT_INVALID", {item.code for item in report.findings})

    def test_requirements_mode_requires_requirements_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "main.py").write_text("print('ok')\n", encoding="utf-8")
            with patch("rubra_packager.python_preflight.importlib.util.find_spec", return_value=object()):
                report = run_python_preflight(root, entry_point="main.py", dependency_mode="requirements")
            self.assertFalse(report.ok)
            self.assertIn("REQUIREMENTS_MISSING", {item.code for item in report.findings})

    def test_project_inspection_lists_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("print('ok')\n", encoding="utf-8")
            (root / "pyproject.toml").write_text("[project]\nname='demo'\nversion='0.1.0'\n", encoding="utf-8")
            with patch("rubra_packager.python_preflight.importlib.util.find_spec", return_value=object()):
                result = inspect_python_project(root)
            self.assertIn("app.py", result["suggestedEntryPoints"])
            self.assertIn("pyproject.toml", result["dependencyFiles"])


if __name__ == "__main__":
    unittest.main()
