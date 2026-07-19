from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepositoryContractTests(unittest.TestCase):
    def test_original_brand_assets_are_absent(self):
        names = {path.name for path in ROOT.rglob("*") if path.is_file()}
        self.assertNotIn("html2exe-image.png", names)
        self.assertNotIn("logo.png", names)
        self.assertNotIn("builder.py", names)
        self.assertNotIn("api.js", names)

    def test_ui_uses_new_files_and_brand(self):
        html = (ROOT / "src" / "rubra_packager" / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn("Rubra Packager", html)
        self.assertNotIn("HTML to EXE Builder", html)
        self.assertNotIn("Python to EXE", html)

    def test_no_shell_true_in_python_sources(self):
        for path in (ROOT / "src").rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.keyword) and node.arg == "shell":
                    self.assertFalse(isinstance(node.value, ast.Constant) and node.value.value is True, path)

    def test_source_files_compile(self):
        for path in (ROOT / "src").rglob("*.py"):
            compile(path.read_text(encoding="utf-8"), str(path), "exec")


    def test_local_api_security_contract(self):
        source = (ROOT / "src" / "rubra_packager" / "application.py").read_text(encoding="utf-8")
        self.assertIn('"127.0.0.1"', source)
        self.assertIn('X-RP-Token', source)
        self.assertNotIn('Access-Control-Allow-Origin', source)

    def test_windows_launcher_persistence_contract(self):
        source = (ROOT / "src" / "rubra_packager" / "launcher.py").read_text(encoding="utf-8")
        self.assertIn('private_mode=False', source)
        self.assertIn('storage_path=storage_path', source)
        self.assertIn('sha256', source)

    def test_public_docs_present(self):
        for name in ("LICENSE", "NOTICE.md", "PROVENANCE.md", "SECURITY.md", "CONTRIBUTING.md"):
            self.assertTrue((ROOT / name).is_file(), name)

    def test_windows_runtime_self_repairs_missing_package(self):
        run_script = (ROOT / "run_windows.cmd").read_text(encoding="utf-8")
        setup_script = (ROOT / "setup_windows.cmd").read_text(encoding="utf-8")
        self.assertIn(r"%LOCALAPPDATA%\RubraPackager", run_script)
        self.assertIn("import rubra_packager", run_script)
        self.assertIn("call \"%ROOT%\\setup_windows.cmd\" --no-pause", run_script)
        self.assertIn("--force-reinstall --no-deps", setup_script)
        self.assertNotIn("pip install -e", setup_script)

    def test_public_version_is_rp_r4c(self):
        init_source = (ROOT / "src" / "rubra_packager" / "__init__.py").read_text(encoding="utf-8")
        self.assertIn('__version__ = "0.4.3"', init_source)



class RP4bWindowsSetupTests(unittest.TestCase):
    def test_windows_setup_bypasses_global_pip_cache(self):
        setup_script = (ROOT / "setup_windows.cmd").read_text(encoding="utf-8")
        self.assertIn('set "PIP_CACHE_DIR=%RUNTIME%\\pip-cache"', setup_script)
        self.assertGreaterEqual(setup_script.count("--no-cache-dir"), 3)
        self.assertIn("Installing dependencies without using the global pip cache", setup_script)


class RP4cPreflightContractTests(unittest.TestCase):
    def test_preflight_does_not_use_generic_from_regex(self):
        source = (ROOT / "src" / "rubra_packager" / "preflight.py").read_text(encoding="utf-8")
        self.assertNotIn('re.compile(r"(?:from\\s+', source)
        self.assertIn("JS_STATIC_IMPORT_PATTERN", source)
        self.assertIn("REFERENCE_SCAN_EXCLUDED_ROOTS", source)
        self.assertIn("_append_unique", source)
