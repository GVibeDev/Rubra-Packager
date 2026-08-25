from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from rubra_packager.build_python import PythonBuilder


class PythonBuilderTests(unittest.TestCase):
    def test_dependency_install_requires_trust(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "main.py").write_text("print('ok')\n", encoding="utf-8")
            (root / "requirements.txt").write_text("example-package\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "trust checkbox"):
                PythonBuilder().build(
                    project_root=root,
                    app_name="Demo",
                    entry_point="main.py",
                    bundle_mode="onefile",
                    window_mode="console",
                    dependency_mode="requirements",
                    trust_dependency_install=False,
                    icon_data=None,
                )

    def test_onefile_command_preserves_data_and_hidden_imports(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            project = temp_root / "project"
            output = temp_root / "output"
            project.mkdir()
            (project / "main.py").write_text("print('ok')\n", encoding="utf-8")
            (project / "assets").mkdir()
            (project / "assets" / "value.txt").write_text("hello\n", encoding="utf-8")

            captured: list[tuple[str, ...]] = []

            def fake_run(args, *, cwd=None, env=None, timeout=None):
                normalized = tuple(str(item) for item in args)
                captured.append(normalized)
                dist_arg = next((item for item in normalized if item.startswith("--distpath=")), None)
                name_arg = next((item for item in normalized if item.startswith("--name=")), None)
                if dist_arg and name_arg:
                    dist = Path(dist_arg.split("=", 1)[1])
                    name = name_arg.split("=", 1)[1]
                    dist.mkdir(parents=True, exist_ok=True)
                    (dist / f"{name}.exe").write_bytes(b"MZ-demo")
                return SimpleNamespace(returncode=0, stdout="ok", stderr="")

            with patch("rubra_packager.python_preflight.importlib.util.find_spec", return_value=object()), \
                 patch("rubra_packager.build_python.build_python_executable", return_value=Path(__file__)), \
                 patch("rubra_packager.build_python.run", side_effect=fake_run):
                result = PythonBuilder().build(
                    project_root=project,
                    app_name="Demo App",
                    entry_point="main.py",
                    bundle_mode="onefile",
                    window_mode="console",
                    dependency_mode="none",
                    trust_dependency_install=False,
                    icon_data=None,
                    hidden_imports=["pkg.submodule"],
                    data_paths=["assets"],
                    version="2.3.4",
                    publisher="Example Studio",
                    description="Example Python application",
                    output_dir=output,
                )

            self.assertTrue(result["success"])
            self.assertEqual(result["artifactType"], "onefile")
            self.assertTrue(Path(result["path"]).is_file())
            pyinstaller = captured[-1]
            self.assertIn("--onefile", pyinstaller)
            self.assertIn("--console", pyinstaller)
            self.assertIn("--hidden-import=pkg.submodule", pyinstaller)
            self.assertTrue(any(item.startswith("--add-data=") and "assets" in item for item in pyinstaller))
            self.assertTrue(any(item.startswith("--version-file=") for item in pyinstaller))


if __name__ == "__main__":
    unittest.main()
