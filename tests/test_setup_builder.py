from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from rubra_packager.build_setup import _install_dir_leaf, _single_line, resolve_artifact
from rubra_packager.installer.inno import render_script
from rubra_packager.installer.models import SetupArtifact, SetupOptions
from rubra_packager.security import ValidationError


class SetupArtifactTests(unittest.TestCase):
    def test_onefile_requires_exe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exe = root / "Demo.exe"
            exe.write_bytes(b"MZ")
            artifact = resolve_artifact(exe, "onefile")
            self.assertEqual(artifact.primary_exe, exe.resolve())
            self.assertEqual(artifact.artifact_kind, "onefile")

    def test_onedir_auto_detects_single_top_level_exe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Demo.exe").write_bytes(b"MZ")
            (root / "asset.dat").write_bytes(b"data")
            artifact = resolve_artifact(root, "onedir")
            self.assertEqual(artifact.primary_exe.name, "Demo.exe")

    def test_onedir_multiple_exes_require_primary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "A.exe").write_bytes(b"MZ")
            (root / "B.exe").write_bytes(b"MZ")
            with self.assertRaises(ValidationError):
                resolve_artifact(root, "onedir")
            artifact = resolve_artifact(root, "onedir", "B.exe")
            self.assertEqual(artifact.primary_exe.name, "B.exe")

    def test_primary_exe_cannot_escape_onedir(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            root = parent / "app"
            root.mkdir()
            (parent / "outside.exe").write_bytes(b"MZ")
            with self.assertRaises(ValidationError):
                resolve_artifact(root, "onedir", "../outside.exe")

    def test_install_folder_rejects_paths(self):
        with self.assertRaises(ValidationError):
            _install_dir_leaf("sub\\folder", "Demo")
        with self.assertRaises(ValidationError):
            _install_dir_leaf("../Demo", "Demo")

    def test_multiline_metadata_is_rejected(self):
        with self.assertRaises(ValidationError):
            _single_line("Demo\n[Files]", "Application name", required=True)


class InnoScriptTests(unittest.TestCase):
    def _options(self, **changes):
        values = dict(
            app_name="Demo App",
            version="1.2.3",
            publisher="G Vibe Dev",
            app_id="com.gvibedev.demo",
            install_mode="per-user",
            install_dir_name="Demo App",
            desktop_shortcut=True,
            start_menu_shortcut=True,
            launch_after_install=True,
            license_file=None,
            release_notes_file=None,
        )
        values.update(changes)
        return SetupOptions(**values)

    def test_onefile_script_has_uninstaller_shortcuts_and_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exe = root / "Demo.exe"
            exe.write_bytes(b"MZ")
            artifact = SetupArtifact(exe, "onefile", exe)
            script = render_script(
                artifact=artifact,
                options=self._options(),
                output_dir=root / "out",
                output_base_filename="Demo-Setup-1.2.3",
                setup_icon_file=None,
            )
            self.assertIn("AppId=com.gvibedev.demo", script)
            self.assertIn("PrivilegesRequired=lowest", script)
            self.assertIn("DefaultDirName={localappdata}\\Programs\\Demo App", script)
            self.assertIn("[Files]", script)
            self.assertIn(str(exe), script)
            self.assertIn("[Icons]", script)
            self.assertIn("{autodesktop}", script)
            self.assertIn("[Run]", script)
            self.assertIn("UninstallDisplayIcon={app}\\Demo.exe", script)

    def test_per_machine_uses_admin_and_program_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exe = root / "Demo.exe"
            exe.write_bytes(b"MZ")
            script = render_script(
                artifact=SetupArtifact(exe, "onefile", exe),
                options=self._options(install_mode="per-machine"),
                output_dir=root,
                output_base_filename="Demo-Setup",
                setup_icon_file=None,
            )
            self.assertIn("PrivilegesRequired=admin", script)
            self.assertIn("DefaultDirName={autopf}\\Demo App", script)

    def test_onedir_script_recurses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "bundle"
            root.mkdir()
            exe = root / "Demo.exe"
            exe.write_bytes(b"MZ")
            script = render_script(
                artifact=SetupArtifact(root, "onedir", exe),
                options=self._options(),
                output_dir=root.parent,
                output_base_filename="Demo-Setup",
                setup_icon_file=None,
            )
            self.assertIn("recursesubdirs createallsubdirs", script)
            self.assertIn(str(root / "*"), script)

    def test_optional_license_and_notes_are_wired(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exe = root / "Demo.exe"
            exe.write_bytes(b"MZ")
            license_file = root / "LICENSE.txt"
            notes = root / "NOTES.md"
            license_file.write_text("license", encoding="utf-8")
            notes.write_text("notes", encoding="utf-8")
            script = render_script(
                artifact=SetupArtifact(exe, "onefile", exe),
                options=self._options(license_file=license_file, release_notes_file=notes),
                output_dir=root,
                output_base_filename="Demo-Setup",
                setup_icon_file=None,
            )
            self.assertIn("LicenseFile=", script)
            self.assertIn("InfoAfterFile=", script)

    def test_user_braces_do_not_become_inno_constants(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exe = root / "Demo.exe"
            exe.write_bytes(b"MZ")
            script = render_script(
                artifact=SetupArtifact(exe, "onefile", exe),
                options=self._options(app_name="Demo {app}"),
                output_dir=root,
                output_base_filename="Demo-Setup",
                setup_icon_file=None,
            )
            self.assertIn("AppName=Demo {{app}", script)
            self.assertNotIn("AppName=Demo {app}", script)


if __name__ == "__main__":
    unittest.main()
