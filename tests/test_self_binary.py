from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SelfBinaryTests(unittest.TestCase):
    def test_self_builder_is_onedir_and_collects_runtime_ui_data(self):
        module = load_script("build_self_binary.py")
        captured: list[str] = []

        def fake_run(args, *, cwd=None, env=None, timeout=None):
            normalized = [str(item) for item in args]
            captured.extend(normalized)
            dist = Path(next(item.split("=", 1)[1] for item in normalized if item.startswith("--distpath=")))
            built = dist / "RubraPackager"
            built.mkdir(parents=True, exist_ok=True)
            (built / "RubraPackager.exe").write_bytes(b"MZ-self")
            (built / "_internal").mkdir()
            return SimpleNamespace(returncode=0, stdout="ok", stderr="")

        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(module, "_windows_host", return_value=True), \
             patch.object(module, "run", side_effect=fake_run):
            result = module.build_self_binary(Path(tmp))

        self.assertTrue(result["success"])
        self.assertIn("--onedir", captured)
        self.assertIn("--windowed", captured)
        self.assertIn("--collect-data=rubra_packager", captured)
        self.assertIn("--collect-all=webview", captured)
        self.assertTrue(str(result["path"]).endswith("RubraPackager.exe"))


if __name__ == "__main__":
    unittest.main()
