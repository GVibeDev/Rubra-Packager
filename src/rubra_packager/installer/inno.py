from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Iterable

from ..process import ProcessResult, run
from ..security import ValidationError
from .models import SetupArtifact, SetupOptions


def _candidate_locations() -> Iterable[Path]:
    configured = os.environ.get("INNO_SETUP_PATH")
    if configured:
        yield Path(configured)

    found = shutil.which("ISCC.exe") or shutil.which("ISCC")
    if found:
        yield Path(found)

    roots = [
        os.environ.get("ProgramFiles(x86)"),
        os.environ.get("ProgramFiles"),
        os.environ.get("LOCALAPPDATA"),
    ]
    for raw_root in roots:
        if not raw_root:
            continue
        root = Path(raw_root)
        for version in ("7", "6"):
            yield root / f"Inno Setup {version}" / "ISCC.exe"
            yield root / "Programs" / f"Inno Setup {version}" / "ISCC.exe"


def find_iscc() -> Path | None:
    seen: set[str] = set()
    for candidate in _candidate_locations():
        normalized = str(candidate).casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        if candidate.is_file():
            return candidate.resolve()
    return None


def prerequisites() -> dict[str, object]:
    iscc = find_iscc()
    return {
        "inno": {
            "ok": iscc is not None,
            "message": str(iscc) if iscc else "Inno Setup 6 compiler (ISCC.exe) not found",
            "path": str(iscc) if iscc else "",
        }
    }


def _escape_constant_text(value: str) -> str:
    return value.replace("{", "{{")


def _quote(value: str | Path) -> str:
    text = _escape_constant_text(str(value)).replace('"', '""')
    return f'"{text}"'


def _param_text(value: str) -> str:
    return _escape_constant_text(value).replace('"', '""')


def _directive_value(value: str) -> str:
    return _escape_constant_text(value.strip())


def _default_dir(options: SetupOptions) -> str:
    leaf = _directive_value(options.install_dir_name or options.app_name)
    if options.install_mode == "per-machine":
        return "{autopf}\\" + leaf
    return "{localappdata}\\Programs\\" + leaf


def render_script(
    *,
    artifact: SetupArtifact,
    options: SetupOptions,
    output_dir: Path,
    output_base_filename: str,
    setup_icon_file: Path | None,
) -> str:
    if artifact.artifact_kind not in {"onefile", "onedir"}:
        raise ValidationError("Setup artifact kind must be onefile or onedir")
    if options.install_mode not in {"per-user", "per-machine"}:
        raise ValidationError("Install mode must be per-user or per-machine")

    primary_name = _param_text(artifact.primary_exe.name)
    setup_lines = [
        "[Setup]",
        f"AppId={_directive_value(options.app_id)}",
        f"AppName={_directive_value(options.app_name)}",
        f"AppVersion={_directive_value(options.version)}",
        f"DefaultDirName={_default_dir(options)}",
        f"DefaultGroupName={_directive_value(options.app_name)}",
        "DisableProgramGroupPage=yes",
        "Compression=lzma2",
        "SolidCompression=yes",
        "WizardStyle=modern",
        "UsePreviousAppDir=yes",
        "UsePreviousGroup=yes",
        "UsePreviousTasks=yes",
        "CloseApplications=yes",
        "RestartApplications=no",
        "Uninstallable=yes",
        f"PrivilegesRequired={'admin' if options.install_mode == 'per-machine' else 'lowest'}",
        f"OutputDir={_directive_value(str(output_dir))}",
        f"OutputBaseFilename={_directive_value(output_base_filename)}",
        f"UninstallDisplayIcon={{app}}\\{primary_name}",
    ]
    if options.publisher:
        setup_lines.append(f"AppPublisher={_directive_value(options.publisher)}")
    if setup_icon_file:
        setup_lines.append(f"SetupIconFile={_directive_value(str(setup_icon_file))}")
    if options.license_file:
        setup_lines.append(f"LicenseFile={_directive_value(str(options.license_file))}")
    if options.release_notes_file:
        setup_lines.append(f"InfoAfterFile={_directive_value(str(options.release_notes_file))}")

    files_lines = ["", "[Files]"]
    if artifact.artifact_kind == "onefile":
        files_lines.append(
            f"Source: {_quote(artifact.source_path)}; DestDir: \"{{app}}\"; Flags: ignoreversion"
        )
    else:
        source_glob = artifact.source_path / "*"
        files_lines.append(
            f"Source: {_quote(source_glob)}; DestDir: \"{{app}}\"; Flags: ignoreversion recursesubdirs createallsubdirs"
        )

    icon_lines = ["", "[Icons]"]
    if options.start_menu_shortcut:
        icon_lines.append(
            f"Name: \"{{group}}\\{_param_text(options.app_name)}\"; Filename: \"{{app}}\\{primary_name}\""
        )
    if options.desktop_shortcut:
        icon_lines.append(
            f"Name: \"{{autodesktop}}\\{_param_text(options.app_name)}\"; Filename: \"{{app}}\\{primary_name}\""
        )

    run_lines: list[str] = []
    if options.launch_after_install:
        run_lines.extend([
            "",
            "[Run]",
            f"Filename: \"{{app}}\\{primary_name}\"; Description: \"Launch {_param_text(options.app_name)}\"; Flags: nowait postinstall skipifsilent",
        ])

    return "\n".join(setup_lines + files_lines + icon_lines + run_lines) + "\n"


def compile_script(iscc: Path, script_path: Path) -> ProcessResult:
    return run([iscc, script_path], cwd=script_path.parent)
