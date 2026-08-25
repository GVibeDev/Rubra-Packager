from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Any, Iterable

from .config import default_output_dir, windows_work_root
from .icons import decode_data_uri, save_windows_ico
from .io_utils import sha256_file
from .process import run
from .python_preflight import inspect_python_project, run_python_preflight
from .runtime_engine import build_python_executable, ensure_build_runtime, runtime_status
from .security import ValidationError, safe_filename_stem
from .windows_metadata import write_version_file


def _tail_output(stdout: str, stderr: str, limit: int = 180) -> list[str]:
    return [line for line in (stdout + "\n" + stderr).splitlines()[-limit:] if line.strip()]


def _directory_size(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


class PythonBuilder:
    @staticmethod
    def prerequisites() -> dict[str, object]:
        status = runtime_status()
        versions = status.get("versions", {})
        return {
            "python": {
                "ok": bool(status.get("ok")),
                "message": (
                    f"Build Python {versions.get('python', 'unknown')} · {status.get('python', '')}"
                    if status.get("ok")
                    else "Private build runtime is not ready"
                ),
            },
            "pyinstaller": {
                "ok": bool(status.get("ok")),
                "message": (
                    f"PyInstaller {versions.get('pyinstaller', 'available')}"
                    if status.get("ok")
                    else "PyInstaller build runtime missing"
                ),
            },
            "runtimeMode": status.get("mode"),
        }

    @staticmethod
    def inspect(project_root: Path) -> dict[str, object]:
        return inspect_python_project(project_root)

    def build(
        self,
        *,
        project_root: Path,
        app_name: str,
        entry_point: str,
        bundle_mode: str,
        window_mode: str,
        dependency_mode: str,
        trust_dependency_install: bool,
        icon_data: str | None,
        hidden_imports: Iterable[str] | None = None,
        data_paths: Iterable[str] | None = None,
        search_paths: Iterable[str] | None = None,
        version: str = "1.0.0",
        publisher: str = "",
        description: str = "",
        output_dir: Path | None = None,
    ) -> dict[str, Any]:
        log: list[str] = []
        bundle_mode = (bundle_mode or "onefile").strip().lower()
        window_mode = (window_mode or "windowed").strip().lower()
        dependency_mode = (dependency_mode or "none").strip().lower()

        if bundle_mode not in {"onefile", "onedir"}:
            raise ValidationError("Bundle mode must be onefile or onedir")
        if window_mode not in {"windowed", "console"}:
            raise ValidationError("Window mode must be windowed or console")
        if dependency_mode != "none" and not trust_dependency_install:
            raise ValidationError(
                "Dependency installation can execute package build code. "
                "Enable the trust checkbox before using requirements or project installation."
            )

        report = run_python_preflight(
            project_root,
            entry_point=entry_point,
            dependency_mode=dependency_mode,
            hidden_imports=hidden_imports,
            data_paths=data_paths,
            search_paths=search_paths,
        )
        if report.errors:
            return {
                "success": False,
                "error": "Python preflight failed",
                "preflight": report.to_dict(),
                "log": log,
            }

        root = Path(report.project_root)
        if not report.entry_point:
            return {"success": False, "error": "Python preflight did not resolve an entry point", "preflight": report.to_dict(), "log": log}

        name = safe_filename_stem(app_name)
        work = windows_work_root() / "python" / name
        dist = work / "dist"
        build = work / "pyinstaller"
        deps = work / "deps"
        for path in (dist, build, deps):
            if path.exists():
                shutil.rmtree(path)
        work.mkdir(parents=True, exist_ok=True)

        try:
            engine_python = build_python_executable()
        except RuntimeError:
            log.append("Preparing the private Rubra Packager build runtime...")
            prepared = ensure_build_runtime()
            log.extend(str(line) for line in prepared.get("log", []))
            engine_python = build_python_executable()

        if dependency_mode == "requirements":
            deps.mkdir(parents=True, exist_ok=True)
            log.append("Installing requirements.txt into isolated build dependencies...")
            result = run(
                [
                    engine_python, "-m", "pip", "install", "--no-cache-dir",
                    "--target", deps, "-r", root / "requirements.txt",
                ],
                cwd=root,
            )
            log.extend(_tail_output(result.stdout, result.stderr))
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": "Dependency installation from requirements.txt failed",
                    "preflight": report.to_dict(),
                    "log": log,
                }
        elif dependency_mode == "project":
            deps.mkdir(parents=True, exist_ok=True)
            log.append("Installing the project into isolated build dependencies...")
            result = run(
                [
                    engine_python, "-m", "pip", "install", "--no-cache-dir",
                    "--target", deps, str(root),
                ],
                cwd=root,
            )
            log.extend(_tail_output(result.stdout, result.stderr))
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": "Project dependency installation failed",
                    "preflight": report.to_dict(),
                    "log": log,
                }

        icon_path: Path | None = None
        if icon_data:
            icon_path = save_windows_ico(decode_data_uri(icon_data), work / "app.ico")
            log.append(f"Windows icon generated: {icon_path}")

        version_file = write_version_file(
            work / "version_info.txt",
            app_name=app_name,
            version=version,
            publisher=publisher,
            description=description,
            original_filename=f"{name}.exe",
        )

        args: list[str | Path] = [
            engine_python, "-m", "PyInstaller",
            "--noconfirm", "--clean", "--noupx",
            "--onefile" if bundle_mode == "onefile" else "--onedir",
            "--windowed" if window_mode == "windowed" else "--console",
            f"--name={name}",
            f"--distpath={dist}",
            f"--workpath={build}",
            f"--specpath={work}",
            f"--version-file={version_file}",
        ]

        if deps.is_dir():
            args.append(f"--paths={deps}")
        for relative in report.search_paths:
            args.append(f"--paths={root / relative}")
        for module in report.hidden_imports:
            args.append(f"--hidden-import={module}")

        separator = ";" if os.name == "nt" else ":"
        for relative in report.data_paths:
            source = root / relative
            rel_path = Path(relative)
            if source.is_dir():
                destination = rel_path.as_posix()
            else:
                destination = rel_path.parent.as_posix()
                if destination in {"", "."}:
                    destination = "."
            args.append(f"--add-data={source}{separator}{destination}")

        if icon_path:
            args.append(f"--icon={icon_path}")

        entry = root / report.entry_point
        args.append(entry)

        log.append(f"Build Python: {engine_python}")
        log.append(f"Entry point: {report.entry_point}")
        log.append(f"Bundle mode: {bundle_mode}")
        log.append(f"Window mode: {window_mode}")
        log.append(f"Dependency setup: {dependency_mode}")
        log.append("Running PyInstaller through the Rubra Packager runtime...")
        result = run(args, cwd=root)
        log.extend(_tail_output(result.stdout, result.stderr))
        if result.returncode != 0:
            return {
                "success": False,
                "error": "PyInstaller failed",
                "preflight": report.to_dict(),
                "log": log,
            }

        target_dir = (output_dir or default_output_dir()).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        exe_name = f"{name}.exe"

        if bundle_mode == "onefile":
            built = dist / exe_name
            if not built.is_file():
                return {
                    "success": False,
                    "error": f"Expected EXE was not produced: {built}",
                    "preflight": report.to_dict(),
                    "log": log,
                }
            published = target_dir / exe_name
            shutil.copy2(built, published)
            return {
                "success": True,
                "path": str(published),
                "artifactType": "onefile",
                "bytes": published.stat().st_size,
                "sha256": sha256_file(published),
                "entryPoint": report.entry_point,
                "dependencyMode": dependency_mode,
                "version": version,
                "publisher": publisher,
                "preflight": report.to_dict(),
                "log": log,
            }

        built_dir = dist / name
        built_exe = built_dir / exe_name
        if not built_exe.is_file():
            return {
                "success": False,
                "error": f"Expected ONEDIR executable was not produced: {built_exe}",
                "preflight": report.to_dict(),
                "log": log,
            }
        published_dir = target_dir / f"{name}-portable"
        if published_dir.exists():
            shutil.rmtree(published_dir)
        shutil.copytree(built_dir, published_dir)
        published_exe = published_dir / exe_name
        return {
            "success": True,
            "path": str(published_exe),
            "bundlePath": str(published_dir),
            "artifactType": "onedir",
            "bytes": _directory_size(published_dir),
            "sha256": sha256_file(published_exe),
            "entryPoint": report.entry_point,
            "dependencyMode": dependency_mode,
            "version": version,
            "publisher": publisher,
            "preflight": report.to_dict(),
            "log": log,
        }
