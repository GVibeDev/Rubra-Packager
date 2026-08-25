from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rubra_packager import runtime_engine


class RuntimeEngineTests(unittest.TestCase):
    def test_frozen_app_never_falls_back_to_its_own_executable(self):
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(runtime_engine, "is_frozen_app", return_value=True), \
             patch.object(runtime_engine, "private_python", return_value=Path(tmp) / "missing" / "python.exe"), \
             patch.object(runtime_engine, "runtime_status", return_value={
                 "ok": False,
                 "mode": "private-runtime",
                 "python": str(Path(tmp) / "missing" / "python.exe"),
                 "versions": {},
                 "errors": ["missing"],
             }):
            with self.assertRaisesRegex(RuntimeError, "build runtime is not ready"):
                runtime_engine.build_python_executable()

    def test_engine_requirements_include_web_builder_dependencies(self):
        joined = " ".join(runtime_engine.ENGINE_REQUIREMENTS).lower()
        self.assertIn("pyinstaller", joined)
        self.assertIn("pywebview", joined)
        self.assertIn("pillow", joined)


if __name__ == "__main__":
    unittest.main()
