from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


SOURCE_CONTRACT_DIRS = ("src", "scripts", "profiles", "assets")


def _source_contract_file_names() -> set[str]:
    """Return names from first-party source inputs only.

    Generated release/build output can legitimately contain third-party files
    such as pywebview's api.js and must not participate in provenance checks.
    """
    names = {path.name for path in ROOT.iterdir() if path.is_file()}
    for dirname in SOURCE_CONTRACT_DIRS:
        folder = ROOT / dirname
        if folder.is_dir():
            names.update(path.name for path in folder.rglob("*") if path.is_file())
    return names


class RepositoryContractTests(unittest.TestCase):
    def test_original_brand_assets_are_absent(self):
        names = _source_contract_file_names()
        self.assertNotIn("html2exe-image.png", names)
        self.assertNotIn("logo.png", names)
        self.assertNotIn("builder.py", names)
        self.assertNotIn("api.js", names)

    def test_generated_release_output_is_outside_provenance_scope(self):
        generated_api = ROOT / "release" / "RubraPackager-portable" / "_internal" / "webview" / "js" / "api.js"
        self.assertEqual(generated_api.name, "api.js")
        self.assertNotIn(generated_api, [
            ROOT / dirname / "api.js" for dirname in SOURCE_CONTRACT_DIRS
        ])
        self.assertNotIn("release", SOURCE_CONTRACT_DIRS)
        self.assertNotIn("build", SOURCE_CONTRACT_DIRS)

    def test_ui_uses_rubra_packager_brand_and_python_workspace(self):
        html = (ROOT / "src" / "rubra_packager" / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn("Rubra Packager", html)
        self.assertNotIn("HTML to EXE Builder", html)
        self.assertIn("Python → Windows", html)
        self.assertIn('id="view-python"', html)
        self.assertIn("Setup Builder", html)
        self.assertIn('id="view-setup"', html)

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
        self.assertIn("X-RP-Token", source)
        self.assertNotIn("Access-Control-Allow-Origin", source)

    def test_windows_launcher_persistence_contract(self):
        source = (ROOT / "src" / "rubra_packager" / "launcher.py").read_text(encoding="utf-8")
        self.assertIn("private_mode=False", source)
        self.assertIn("storage_path=storage_path", source)
        self.assertIn("sha256", source)

    def test_public_docs_present(self):
        for name in ("LICENSE", "NOTICE.md", "PROVENANCE.md", "SECURITY.md", "CONTRIBUTING.md"):
            self.assertTrue((ROOT / name).is_file(), name)

    def test_source_launcher_still_self_repairs_development_runtime(self):
        run_script = (ROOT / "run_windows.cmd").read_text(encoding="utf-8")
        setup_script = (ROOT / "bootstrap_source_runtime.cmd").read_text(encoding="utf-8")
        self.assertIn(r"%LOCALAPPDATA%\RubraPackager", run_script)
        self.assertIn("import rubra_packager", run_script)
        self.assertIn('call "%ROOT%\\bootstrap_source_runtime.cmd" --no-pause', run_script)
        self.assertIn("--force-reinstall --no-deps", setup_script)
        self.assertNotIn("pip install -e", setup_script)

    def test_frozen_app_build_engine_is_separate_from_sys_executable(self):
        runtime = (ROOT / "src/rubra_packager/runtime_engine.py").read_text(encoding="utf-8")
        python_builder = (ROOT / "src/rubra_packager/build_python.py").read_text(encoding="utf-8")
        web_builder = (ROOT / "src/rubra_packager/build_windows.py").read_text(encoding="utf-8")
        self.assertIn("def build_python_executable", runtime)
        self.assertIn("is_frozen_app", runtime)
        self.assertIn("build_python_executable()", python_builder)
        self.assertIn("build_python_executable()", web_builder)
        self.assertNotIn('sys.executable, "-m", "PyInstaller"', python_builder)
        self.assertNotIn('sys.executable, "-m", "PyInstaller"', web_builder)

    def test_windows_admin_guard_leaves_standard_user_errorlevel_zero(self):
        for name in ("run_windows.cmd", "bootstrap_source_runtime.cmd"):
            script = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn(
                "if($p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){exit 1}else{exit 0}",
                script,
            )
            self.assertIn("if errorlevel 1 (", script)
            self.assertNotIn(
                "if($p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){exit 0}else{exit 1}",
                script,
            )

    def test_public_version_is_v1_final(self):
        init_source = (ROOT / "src" / "rubra_packager" / "__init__.py").read_text(encoding="utf-8")
        self.assertIn('__version__ = "1.0.0"', init_source)
        run_script = (ROOT / "run_windows.cmd").read_text(encoding="utf-8")
        self.assertIn('EXPECTED_VERSION=1.0.0', run_script)

    def test_python_builder_is_separate_from_web_builder(self):
        self.assertTrue((ROOT / "src" / "rubra_packager" / "build_python.py").is_file())
        self.assertTrue((ROOT / "src" / "rubra_packager" / "python_preflight.py").is_file())
        web_builder = (ROOT / "src" / "rubra_packager" / "build_windows.py").read_text(encoding="utf-8")
        self.assertNotIn("class PythonBuilder", web_builder)

    def test_python_dependency_install_requires_explicit_trust(self):
        source = (ROOT / "src" / "rubra_packager" / "build_python.py").read_text(encoding="utf-8")
        self.assertIn("trust_dependency_install", source)
        self.assertIn("Enable the trust checkbox", source)
        self.assertIn('"--target", deps', source)

    def test_python_paths_are_project_confined(self):
        source = (ROOT / "src" / "rubra_packager" / "python_preflight.py").read_text(encoding="utf-8")
        self.assertIn("confine(root, root / raw)", source)
        self.assertIn("DATA_PATH_INVALID", source)
        self.assertIn("SEARCH_PATH_INVALID", source)

    def test_setup_builder_is_separate_from_application_builders(self):
        root = ROOT / "src" / "rubra_packager"
        self.assertTrue((root / "build_setup.py").is_file())
        self.assertTrue((root / "installer" / "inno.py").is_file())
        self.assertTrue((root / "installer" / "models.py").is_file())
        python_builder = (root / "build_python.py").read_text(encoding="utf-8")
        web_builder = (root / "build_windows.py").read_text(encoding="utf-8")
        self.assertNotIn("class SetupBuilder", python_builder)
        self.assertNotIn("class SetupBuilder", web_builder)

    def test_setup_builder_uses_argument_list_and_no_shell(self):
        source = (ROOT / "src" / "rubra_packager" / "installer" / "inno.py").read_text(encoding="utf-8")
        self.assertIn("run([iscc, script_path]", source)
        self.assertNotIn("shell=True", source)


    def test_rp7_setup_bootstrap_is_explicit_and_shell_free(self):
        app = (ROOT / "src" / "rubra_packager" / "application.py").read_text(encoding="utf-8")
        bootstrap = (ROOT / "src" / "rubra_packager" / "installer" / "bootstrap.py").read_text(encoding="utf-8")
        html = (ROOT / "src" / "rubra_packager" / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn('endpoint == "setup/bootstrap"', app)
        self.assertIn('WINGET_PACKAGE_ID = "JRSoftware.InnoSetup"', bootstrap)
        self.assertIn('"--accept-package-agreements"', bootstrap)
        self.assertNotIn("shell=True", bootstrap)
        self.assertIn('id="installSetupPrereqButton"', html)

    def test_rp7_release_manifest_and_maintenance_contract(self):
        builder = (ROOT / "src" / "rubra_packager" / "build_setup.py").read_text(encoding="utf-8")
        inno = (ROOT / "src" / "rubra_packager" / "installer" / "inno.py").read_text(encoding="utf-8")
        self.assertIn('releaseManifestPath', builder)
        self.assertIn('"userDataPolicy"', builder)
        self.assertIn('"CloseApplications=yes"', inno)
        self.assertIn('"RestartApplications=no"', inno)
        self.assertNotIn("[UninstallDelete]", inno)
    def test_setup_ui_exposes_stable_appid_and_install_modes(self):
        html = (ROOT / "src" / "rubra_packager" / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="setupAppId"', html)
        self.assertIn('value="per-user"', html)
        self.assertIn('value="per-machine"', html)
        self.assertIn('id="setupArtifactKind"', html)

    def test_final_branding_assets_are_integrated(self):
        icon = ROOT / "assets" / "branding" / "rubra-packager.ico"
        self.assertTrue(icon.is_file())
        self.assertTrue(icon.read_bytes().startswith(b"\x00\x00\x01\x00"))
        for name in ("brand-mark.png", "brand-logo.png", "brand-banner.png"):
            self.assertTrue((ROOT / "src" / "rubra_packager" / "static" / name).is_file(), name)

        html = (ROOT / "src" / "rubra_packager" / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn('src="/brand-mark.png"', html)
        self.assertIn('src="/brand-logo.png"', html)
        self.assertIn('src="/brand-banner.png"', html)

        app = (ROOT / "src" / "rubra_packager" / "application.py").read_text(encoding="utf-8")
        for name in ("brand-mark.png", "brand-logo.png", "brand-banner.png"):
            self.assertIn(f'"{name}"', app)

    def test_final_paired_field_and_prerequisite_layout_contract(self):
        css = (ROOT / "src" / "rubra_packager" / "static" / "app.css").read_text(encoding="utf-8")
        self.assertIn(".split > label { display: flex; flex-direction: column;", css)
        self.assertIn(".split > label > select,", css)
        self.assertIn("margin-top: auto;", css)
        self.assertIn("repeat(auto-fit, minmax(145px, 1fr))", css)
        self.assertIn(".prereq-row.stacked", css)
        self.assertIn("overflow-wrap: anywhere", css)
        app_js = (ROOT / "src" / "rubra_packager" / "static" / "app.js").read_text(encoding="utf-8")
        self.assertIn("function renderPrerequisites", app_js)
        self.assertIn("length > 64", app_js)

    def test_final_self_binary_uses_default_brand_icon(self):
        source = (ROOT / "scripts" / "build_self_binary.py").read_text(encoding="utf-8")
        self.assertIn('ROOT / "assets" / "branding" / "rubra-packager.ico"', source)
        self.assertIn("effective_icon", source)


class RP4bWindowsSetupTests(unittest.TestCase):
    def test_windows_setup_bypasses_global_pip_cache(self):
        setup_script = (ROOT / "bootstrap_source_runtime.cmd").read_text(encoding="utf-8")
        self.assertGreaterEqual(setup_script.count("--no-cache-dir"), 3)
        self.assertIn("without using the global pip cache", setup_script)


class RP4cPreflightContractTests(unittest.TestCase):
    def test_preflight_does_not_use_generic_from_regex(self):
        source = (ROOT / "src" / "rubra_packager" / "preflight.py").read_text(encoding="utf-8")
        self.assertNotIn('re.compile(r"(?:from\\s+', source)
        self.assertIn("JS_STATIC_IMPORT_PATTERN", source)
        self.assertIn("REFERENCE_SCAN_EXCLUDED_ROOTS", source)
        self.assertIn("_append_unique", source)
