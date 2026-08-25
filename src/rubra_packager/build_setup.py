from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from . import __version__

from .config import default_output_dir, user_data_dir
from .icons import decode_data_uri, save_windows_ico
from .installer.bootstrap import install_inno, prerequisites as setup_prerequisites
from .installer.inno import compile_script, find_iscc, render_script
from .installer.models import SetupArtifact, SetupOptions
from .io_utils import atomic_write_json, sha256_file
from .security import ValidationError, safe_filename_stem, safe_identifier


def _tail(stdout: str, stderr: str, limit: int = 180) -> list[str]:
    return [line for line in (stdout + "\n" + stderr).splitlines()[-limit:] if line.strip()]


def _required_file(path: str | Path, label: str) -> Path:
    value = Path(path).expanduser().resolve()
    if not value.is_file():
        raise ValidationError(f"{label} not found: {value}")
    return value


def _optional_file(path: str | Path | None, label: str) -> Path | None:
    if path is None or not str(path).strip():
        return None
    return _required_file(path, label)




def _single_line(value: str, label: str, *, required: bool = False) -> str:
    text = (value or "").strip()
    if required and not text:
        raise ValidationError(f"{label} is required")
    if "\r" in text or "\n" in text:
        raise ValidationError(f"{label} must be a single line")
    return text


def _install_dir_leaf(value: str, fallback: str) -> str:
    text = _single_line(value, "Install folder name") or fallback
    if text in {".", ".."} or any(char in text for char in '<>:"/\\|?*'):
        raise ValidationError("Install folder name must be a single Windows folder name, not a path")
    if text.endswith((" ", ".")):
        raise ValidationError("Install folder name cannot end with a space or dot")
    return text

def resolve_artifact(source_path: str | Path, artifact_kind: str, primary_exe: str = "") -> SetupArtifact:
    kind = (artifact_kind or "onefile").strip().lower()
    source = Path(source_path).expanduser().resolve()
    if kind == "onefile":
        if not source.is_file() or source.suffix.casefold() != ".exe":
            raise ValidationError("ONEFILE setup source must be an existing .exe file")
        return SetupArtifact(source, kind, source)

    if kind != "onedir":
        raise ValidationError("Setup artifact kind must be onefile or onedir")
    if not source.is_dir():
        raise ValidationError("ONEDIR setup source must be an existing folder")

    raw_primary = (primary_exe or "").strip()
    if raw_primary:
        relative = Path(raw_primary)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValidationError("Primary executable must be a relative path inside the ONEDIR folder")
        resolved = (source / relative).resolve()
        try:
            resolved.relative_to(source)
        except ValueError as exc:
            raise ValidationError("Primary executable escapes the ONEDIR folder") from exc
        if not resolved.is_file() or resolved.suffix.casefold() != ".exe":
            raise ValidationError(f"Primary executable not found: {resolved}")
        return SetupArtifact(source, kind, resolved)

    executables = sorted(path for path in source.glob("*.exe") if path.is_file())
    if len(executables) == 1:
        return SetupArtifact(source, kind, executables[0].resolve())
    if not executables:
        raise ValidationError("No .exe was found at the top level of the ONEDIR folder")
    raise ValidationError("Multiple .exe files found. Specify the primary executable explicitly")


class SetupBuilder:
    @staticmethod
    def prerequisites() -> dict[str, object]:
        return setup_prerequisites()

    @staticmethod
    def bootstrap(*, scope: str = "user") -> dict[str, Any]:
        return install_inno(scope=scope)

    def build(
        self,
        *,
        source_path: str | Path,
        artifact_kind: str,
        primary_exe: str,
        app_name: str,
        version: str,
        publisher: str,
        app_id: str,
        install_mode: str,
        install_dir_name: str,
        desktop_shortcut: bool,
        start_menu_shortcut: bool,
        launch_after_install: bool,
        icon_data: str | None,
        license_file: str | Path | None,
        release_notes_file: str | Path | None,
        output_dir: Path | None = None,
    ) -> dict[str, Any]:
        log: list[str] = []
        artifact = resolve_artifact(source_path, artifact_kind, primary_exe)
        app_name = _single_line(app_name, "Application name", required=True)
        version = _single_line(version, "Application version", required=True)
        publisher = _single_line(publisher, "Publisher")
        app_id = safe_identifier(app_id, "setup AppId")
        install_mode = (install_mode or "per-user").strip().lower()
        if install_mode not in {"per-user", "per-machine"}:
            raise ValidationError("Install mode must be per-user or per-machine")

        license_path = _optional_file(license_file, "License file")
        notes_path = _optional_file(release_notes_file, "Release notes file")
        iscc = find_iscc()
        if iscc is None:
            return {
                "success": False,
                "error": "Inno Setup compiler (ISCC.exe) was not found. Install Inno Setup before building a setup package.",
                "log": log,
            }

        name = safe_filename_stem(app_name)
        work = user_data_dir() / "setup" / name
        if work.exists():
            shutil.rmtree(work)
        work.mkdir(parents=True, exist_ok=True)

        setup_icon: Path | None = None
        if icon_data:
            setup_icon = save_windows_ico(decode_data_uri(icon_data), work / "setup.ico")
            log.append(f"Setup icon generated: {setup_icon}")

        target_dir = (output_dir or default_output_dir()).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        output_base = f"{name}-Setup-{safe_filename_stem(version)}"

        options = SetupOptions(
            app_name=app_name,
            version=version,
            publisher=publisher,
            app_id=app_id,
            install_mode=install_mode,
            install_dir_name=_install_dir_leaf(install_dir_name, app_name),
            desktop_shortcut=bool(desktop_shortcut),
            start_menu_shortcut=bool(start_menu_shortcut),
            launch_after_install=bool(launch_after_install),
            license_file=license_path,
            release_notes_file=notes_path,
        )
        script = render_script(
            artifact=artifact,
            options=options,
            output_dir=target_dir,
            output_base_filename=output_base,
            setup_icon_file=setup_icon,
        )
        script_path = work / f"{name}.iss"
        script_path.write_text(script, encoding="utf-8", newline="\n")

        log.extend([
            f"Inno Setup compiler: {iscc}",
            f"Artifact: {artifact.source_path}",
            f"Artifact kind: {artifact.artifact_kind}",
            f"Primary executable: {artifact.primary_exe}",
            f"Install mode: {install_mode}",
            f"Generated script: {script_path}",
        ])

        result = compile_script(iscc, script_path)
        log.extend(_tail(result.stdout, result.stderr))
        if result.returncode != 0:
            return {
                "success": False,
                "error": "Inno Setup compilation failed",
                "scriptPath": str(script_path),
                "log": log,
            }

        built = target_dir / f"{output_base}.exe"
        if not built.is_file():
            return {
                "success": False,
                "error": f"Expected setup executable was not produced: {built}",
                "scriptPath": str(script_path),
                "log": log,
            }

        setup_sha256 = sha256_file(built)
        source_summary: dict[str, Any]
        if artifact.artifact_kind == "onefile":
            source_summary = {
                "sourceName": artifact.source_path.name,
                "files": 1,
                "bytes": artifact.source_path.stat().st_size,
                "sha256": sha256_file(artifact.source_path),
            }
        else:
            artifact_files = [item for item in artifact.source_path.rglob("*") if item.is_file()]
            source_summary = {
                "sourceName": artifact.source_path.name,
                "files": len(artifact_files),
                "bytes": sum(item.stat().st_size for item in artifact_files),
            }

        manifest_path = target_dir / f"{output_base}.release.json"
        release_manifest = {
            "schemaVersion": 1,
            "generator": {"name": "Rubra Packager", "version": __version__},
            "application": {
                "name": app_name,
                "version": version,
                "publisher": publisher,
                "appId": app_id,
                "primaryExecutable": artifact.primary_exe.name,
            },
            "artifact": {
                "kind": artifact.artifact_kind,
                **source_summary,
            },
            "installer": {
                "provider": "Inno Setup",
                "installMode": install_mode,
                "installFolderName": options.install_dir_name,
                "setupFile": built.name,
                "bytes": built.stat().st_size,
                "sha256": setup_sha256,
                "scriptFile": script_path.name,
            },
            "maintenance": {
                "upgrade": "Rebuild with the same stable AppId and run the newer setup.",
                "repair": "Run the same setup again to reinstall the application core.",
                "uninstall": "Use the generated Inno Setup uninstaller or Windows Installed Apps.",
                "userDataPolicy": "External user data is not deleted by the generated uninstall script.",
            },
        }
        atomic_write_json(manifest_path, release_manifest)
        log.append(f"Release manifest: {manifest_path}")

        return {
            "success": True,
            "path": str(built),
            "bytes": built.stat().st_size,
            "sha256": setup_sha256,
            "scriptPath": str(script_path),
            "releaseManifestPath": str(manifest_path),
            "artifactKind": artifact.artifact_kind,
            "primaryExe": artifact.primary_exe.name,
            "installMode": install_mode,
            "log": log,
        }
