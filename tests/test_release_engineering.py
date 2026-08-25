from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReleaseEngineeringTests(unittest.TestCase):
    def test_version_is_synchronized(self):
        self.assertIn('version = "1.0.0"', (ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertIn('__version__ = "1.0.0"', (ROOT / "src/rubra_packager/__init__.py").read_text(encoding="utf-8"))
        for name in ("run_windows.cmd", "bootstrap_source_runtime.cmd", "diagnose_windows.cmd"):
            self.assertIn("EXPECTED_VERSION=1.0.0", (ROOT / name).read_text(encoding="utf-8"))

    def test_gui_entry_point_is_declared(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn("[project.gui-scripts]", pyproject)
        self.assertIn('rubra-packager-gui = "rubra_packager.__main__:main"', pyproject)

    def test_windows_release_helper_targets_final_binary_release(self):
        helper = (ROOT / "build_release_windows.cmd").read_text(encoding="utf-8")
        self.assertIn("EXPECTED_VERSION=1.0.0", helper)
        self.assertIn(r"scripts\build_release.py", helper)
        self.assertIn("--require-setup", helper)
        self.assertIn(r"scripts\finalize_release.py", helper)
        self.assertIn("pip wheel", helper)
        self.assertIn(r"Portable\RubraPackager.exe", helper)

    def test_self_binary_builder_exists_and_is_onedir(self):
        source = (ROOT / "scripts/build_self_binary.py").read_text(encoding="utf-8")
        self.assertIn('"--onedir"', source)
        self.assertIn('"--windowed"', source)
        self.assertIn('"--collect-data=rubra_packager"', source)
        self.assertIn('"--collect-all=webview"', source)

    def test_release_build_packages_real_binary_core(self):
        module = load_script("build_release.py")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            core = root / "fake-core"
            core.mkdir()
            (core / "RubraPackager.exe").write_bytes(b"MZ-core")
            (core / "_internal").mkdir()
            (core / "_internal/data.bin").write_bytes(b"data")
            result = module.build_release(root / "out", require_setup=False, tag="v1.0.0", core_dir=core)
            self.assertTrue(Path(result["portableExe"]).is_file())
            with zipfile.ZipFile(result["portableZip"], "r") as archive:
                names = archive.namelist()
                self.assertTrue(any(name.endswith("/RubraPackager.exe") for name in names))
                self.assertFalse(any(name.endswith("/run_windows.cmd") for name in names))

    def test_tag_mismatch_is_rejected(self):
        module = load_script("build_release.py")
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(RuntimeError):
                module.build_release(Path(temp), require_setup=False, tag="v9.9.9", core_dir=Path(temp))

    def test_self_setup_targets_exe_and_prepares_private_runtime(self):
        module = load_script("build_release.py")
        with tempfile.TemporaryDirectory() as temp:
            core = Path(temp) / "core"
            core.mkdir()
            (core / "RubraPackager.exe").write_bytes(b"MZ")
            script = module._render_self_setup(core, Path(temp))
            self.assertIn('{app}\\RubraPackager.exe', script)
            self.assertIn('Parameters: "--prepare-runtime"', script)
            self.assertNotIn('run_windows.cmd', script)
            self.assertNotIn('bootstrap_source_runtime.cmd', script)
            self.assertIn('{localappdata}\\RubraPackager\\runtime', script)
            self.assertNotIn('projects.json', script)
            self.assertNotIn('reports', script)

    def test_release_finalizer_hashes_portable_assets(self):
        module = load_script("finalize_release.py")
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            asset = out / "RubraPackager-1.0.0-Portable.zip"
            asset.write_bytes(b"release-test")
            result = module.finalize(out)
            manifest = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
            expected = hashlib.sha256(b"release-test").hexdigest()
            self.assertEqual(manifest["assets"][0]["sha256"], expected)
            self.assertEqual(manifest["releaseKind"], "frozen-onedir-with-private-build-runtime")
            self.assertIn(expected, Path(result["checksums"]).read_text(encoding="utf-8"))

    def test_ci_exists_and_automatic_binary_release_is_absent(self):
        ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("windows-latest", ci)
        self.assertIn("3.11", ci)
        self.assertIn("3.13", ci)
        self.assertIn("validate_repository.py", ci)
        self.assertFalse((ROOT / ".github/workflows/release.yml").exists())

    def test_code_signing_hook_is_optional_and_secret_driven(self):
        signing = (ROOT / "scripts/sign_release.ps1").read_text(encoding="utf-8")
        self.assertIn("WINDOWS_CERTIFICATE_BASE64", signing)
        self.assertIn("Code signing secrets are not configured", signing)
        self.assertFalse((ROOT / ".github/workflows/release.yml").exists())


if __name__ == "__main__":
    unittest.main()
