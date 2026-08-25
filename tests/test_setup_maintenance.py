from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rubra_packager.build_setup import SetupBuilder
from rubra_packager.installer import bootstrap
from rubra_packager.installer.inno import render_script
from rubra_packager.installer.models import SetupArtifact, SetupOptions
from rubra_packager.process import ProcessResult


class BootstrapTests(unittest.TestCase):
    def test_existing_inno_does_not_run_winget(self):
        installed = Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe")
        with patch.object(bootstrap.os, "name", "nt"), \
             patch.object(bootstrap, "find_iscc", return_value=installed), \
             patch.object(bootstrap, "run") as mocked_run:
            result = bootstrap.install_inno(scope="user")
        self.assertTrue(result["success"])
        self.assertTrue(result["alreadyInstalled"])
        mocked_run.assert_not_called()

    def test_winget_bootstrap_uses_exact_package_and_scope(self):
        winget = Path("C:/Windows/winget.exe")
        installed = Path("C:/Users/Test/AppData/Local/Programs/Inno Setup 6/ISCC.exe")
        process = ProcessResult((str(winget),), 0, "Successfully installed", "")
        with patch.object(bootstrap.os, "name", "nt"), \
             patch.object(bootstrap, "find_iscc", side_effect=[None, installed]), \
             patch.object(bootstrap, "find_winget", return_value=winget), \
             patch.object(bootstrap, "run", return_value=process) as mocked_run:
            result = bootstrap.install_inno(scope="user")
        self.assertTrue(result["success"])
        args = tuple(str(item) for item in mocked_run.call_args.args[0])
        self.assertIn("JRSoftware.InnoSetup", args)
        self.assertIn("--exact", args)
        self.assertIn("--scope", args)
        self.assertEqual(args[args.index("--scope") + 1], "user")
        self.assertIn("--silent", args)


class MaintenanceScriptTests(unittest.TestCase):
    def _options(self) -> SetupOptions:
        return SetupOptions(
            app_name="Demo App",
            version="2.0.0",
            publisher="G Vibe Dev",
            app_id="com.gvibedev.demo",
            install_mode="per-user",
            install_dir_name="Demo App",
            desktop_shortcut=False,
            start_menu_shortcut=True,
            launch_after_install=False,
        )

    def test_script_keeps_stable_upgrade_and_safe_uninstall_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exe = root / "Demo.exe"
            exe.write_bytes(b"MZ")
            script = render_script(
                artifact=SetupArtifact(exe, "onefile", exe),
                options=self._options(),
                output_dir=root / "out",
                output_base_filename="Demo-Setup-2.0.0",
                setup_icon_file=None,
            )
        self.assertIn("AppId=com.gvibedev.demo", script)
        self.assertIn("UsePreviousAppDir=yes", script)
        self.assertIn("UsePreviousTasks=yes", script)
        self.assertIn("CloseApplications=yes", script)
        self.assertIn("RestartApplications=no", script)
        self.assertIn("Uninstallable=yes", script)
        self.assertNotIn("[UninstallDelete]", script)


class ReleaseManifestTests(unittest.TestCase):
    def test_successful_build_writes_release_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "Demo.exe"
            source.write_bytes(b"MZ-demo")
            output = root / "out"
            output.mkdir()
            built = output / "Demo_App-Setup-1.2.3.exe"
            built.write_bytes(b"MZ-setup")
            fake_iscc = root / "ISCC.exe"
            fake_iscc.write_bytes(b"fake")
            process = ProcessResult((str(fake_iscc),), 0, "compile ok", "")
            with patch("rubra_packager.build_setup.find_iscc", return_value=fake_iscc), \
                 patch("rubra_packager.build_setup.compile_script", return_value=process):
                result = SetupBuilder().build(
                    source_path=source,
                    artifact_kind="onefile",
                    primary_exe="",
                    app_name="Demo App",
                    version="1.2.3",
                    publisher="G Vibe Dev",
                    app_id="com.gvibedev.demo",
                    install_mode="per-user",
                    install_dir_name="Demo App",
                    desktop_shortcut=False,
                    start_menu_shortcut=True,
                    launch_after_install=False,
                    icon_data=None,
                    license_file=None,
                    release_notes_file=None,
                    output_dir=output,
                )
            self.assertTrue(result["success"])
            manifest_path = Path(result["releaseManifestPath"])
            self.assertTrue(manifest_path.is_file())
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(data["generator"]["version"], "1.0.0")
            self.assertEqual(data["application"]["appId"], "com.gvibedev.demo")
            self.assertEqual(data["installer"]["sha256"], result["sha256"])
            self.assertIn("repair", data["maintenance"])
            self.assertIn("userDataPolicy", data["maintenance"])
            self.assertNotIn("setupPath", data["installer"])
            self.assertNotIn("scriptPath", data["installer"])
            self.assertNotIn("path", data["artifact"])


if __name__ == "__main__":
    unittest.main()
