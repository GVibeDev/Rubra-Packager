from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Any

from .config import default_output_dir, windows_work_root
from .icons import decode_data_uri, save_windows_ico
from .io_utils import sha256_file
from .launcher import write_launcher
from .models import BuildProfile
from .preflight import run_preflight
from .process import run
from .security import safe_filename_stem
from .source import resolve_static_source
from .staging import stage_source


class WindowsBuilder:
    def build(
        self,
        *,
        project_root: Path,
        app_name: str,
        profile: BuildProfile,
        variant_id: str,
        icon_data: str | None,
        allow_source_build: bool,
        output_dir: Path | None = None,
    ) -> dict[str, Any]:
        log: list[str] = []
        static_source = resolve_static_source(project_root, allow_build=allow_source_build, log=log)
        variant = profile.variant(variant_id)
        work = windows_work_root() / safe_filename_stem(app_name)
        stage = work / "stage"
        included, excluded = stage_source(static_source, stage, variant)
        report = run_preflight(stage, profile, variant.variant_id)
        if report.errors:
            return {"success": False, "error": "Windows preflight failed", "preflight": report.to_dict(), "log": log}

        app_id = safe_filename_stem(app_name).casefold()
        launcher = write_launcher(work / "launcher.py", {
            "title": app_name,
            "appId": app_id,
            "storageName": safe_filename_stem(app_name),
            "entryPoint": profile.entry_point,
            "width": 1440,
            "height": 900,
        })
        icon_path: Path | None = None
        if icon_data:
            icon_path = save_windows_ico(decode_data_uri(icon_data), work / "app.ico")
            log.append(f"Windows icon generated: {icon_path}")

        target_dir = (output_dir or default_output_dir()).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        dist = work / "dist"
        build = work / "pyinstaller"
        for path in (dist, build):
            if path.exists():
                shutil.rmtree(path)
        name = safe_filename_stem(app_name)
        separator = ";" if sys.platform == "win32" else ":"
        args = [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm", "--clean", "--onefile", "--windowed", "--noupx",
            f"--name={name}",
            f"--distpath={dist}",
            f"--workpath={build}",
            f"--specpath={work}",
            "--hidden-import=webview",
            "--hidden-import=webview.js",
            f"--add-data={stage}{separator}_web",
        ]
        if icon_path:
            args.append(f"--icon={icon_path}")
        args.append(str(launcher))
        log.append("Running PyInstaller through the active Python environment")
        result = run(args, cwd=work)
        log.extend(line for line in (result.stdout + "\n" + result.stderr).splitlines()[-160:] if line.strip())
        if result.returncode != 0:
            return {"success": False, "error": "PyInstaller failed", "log": log, "preflight": report.to_dict()}

        built = dist / f"{name}.exe"
        if not built.is_file():
            return {"success": False, "error": f"Expected EXE was not produced: {built}", "log": log}
        published = target_dir / built.name
        shutil.copy2(built, published)
        return {
            "success": True,
            "path": str(published),
            "bytes": published.stat().st_size,
            "sha256": sha256_file(published),
            "profile": profile.profile_id,
            "variant": variant.variant_id,
            "includedFiles": len(included),
            "excludedFiles": len(excluded),
            "preflight": report.to_dict(),
            "log": log,
        }
