from __future__ import annotations

import importlib.util
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from .security import ValidationError, confine, require_existing_dir

_MODULE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")
_DEPENDENCY_MODES = {"none", "requirements", "project"}


@dataclass(frozen=True)
class PythonFinding:
    severity: str
    code: str
    message: str
    path: str | None = None


@dataclass(frozen=True)
class PythonPreflightReport:
    project_root: str
    entry_point: str | None
    python_version: str
    pyinstaller_available: bool
    dependency_mode: str
    dependency_files: tuple[str, ...]
    hidden_imports: tuple[str, ...]
    data_paths: tuple[str, ...]
    search_paths: tuple[str, ...]
    suggested_entry_points: tuple[str, ...]
    findings: tuple[PythonFinding, ...]

    @property
    def errors(self) -> int:
        return sum(item.severity == "error" for item in self.findings)

    @property
    def warnings(self) -> int:
        return sum(item.severity == "warning" for item in self.findings)

    @property
    def ok(self) -> bool:
        return self.errors == 0

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["errors"] = self.errors
        payload["warnings"] = self.warnings
        payload["ok"] = self.ok
        return payload


def _clean_values(values: Iterable[str] | None) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for raw in values or ():
        value = str(raw).strip()
        if value and value not in seen:
            result.append(value)
            seen.add(value)
    return tuple(result)


def _entry_candidates(root: Path) -> tuple[str, ...]:
    preferred = ("main.py", "app.py", "__main__.py", "src/main.py", "src/app.py")
    candidates: list[str] = []
    for item in preferred:
        if (root / item).is_file():
            candidates.append(item)
    for path in sorted(root.glob("*/*/__main__.py")) + sorted(root.glob("*/__main__.py")):
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            continue
        if relative not in candidates:
            candidates.append(relative)
    return tuple(candidates[:20])


def _relative_path(root: Path, raw: str, label: str) -> tuple[Path | None, str | None]:
    try:
        candidate = confine(root, root / raw)
    except (ValidationError, OSError):
        return None, f"{label} escapes the selected project folder: {raw}"
    try:
        relative = candidate.relative_to(root).as_posix()
    except ValueError:
        return None, f"{label} escapes the selected project folder: {raw}"
    return candidate, relative


def inspect_python_project(project_root: Path) -> dict[str, object]:
    root = require_existing_dir(project_root, "Python project")
    dependency_files = tuple(
        name for name in ("requirements.txt", "pyproject.toml", "setup.cfg", "setup.py")
        if (root / name).is_file()
    )
    return {
        "projectRoot": str(root),
        "suggestedEntryPoints": list(_entry_candidates(root)),
        "dependencyFiles": list(dependency_files),
        "pythonVersion": sys.version.split()[0],
        "pyinstallerAvailable": importlib.util.find_spec("PyInstaller") is not None,
    }


def run_python_preflight(
    project_root: Path,
    *,
    entry_point: str = "",
    dependency_mode: str = "none",
    hidden_imports: Iterable[str] | None = None,
    data_paths: Iterable[str] | None = None,
    search_paths: Iterable[str] | None = None,
) -> PythonPreflightReport:
    root = require_existing_dir(project_root, "Python project")
    findings: list[PythonFinding] = []
    hidden = _clean_values(hidden_imports)
    data = _clean_values(data_paths)
    searches = _clean_values(search_paths)
    candidates = _entry_candidates(root)

    dependency_mode = (dependency_mode or "none").strip().lower()
    if dependency_mode not in _DEPENDENCY_MODES:
        raise ValidationError("Dependency mode must be one of: none, requirements, project")

    dependency_files = tuple(
        name for name in ("requirements.txt", "pyproject.toml", "setup.cfg", "setup.py")
        if (root / name).is_file()
    )

    selected_entry = entry_point.strip().replace("\\", "/")
    if not selected_entry:
        if candidates:
            selected_entry = candidates[0]
            findings.append(PythonFinding(
                "warning",
                "ENTRY_POINT_AUTO_SELECTED",
                f"No entry point was supplied; using {selected_entry}.",
                selected_entry,
            ))
        else:
            findings.append(PythonFinding(
                "error",
                "ENTRY_POINT_MISSING",
                "No Python entry point was supplied and no common entry point could be detected.",
            ))

    resolved_entry: str | None = None
    if selected_entry:
        candidate, relative_or_error = _relative_path(root, selected_entry, "Entry point")
        if candidate is None:
            findings.append(PythonFinding("error", "ENTRY_POINT_INVALID", relative_or_error or "Invalid entry point"))
        elif not candidate.is_file():
            findings.append(PythonFinding("error", "ENTRY_POINT_NOT_FOUND", f"Entry point not found: {selected_entry}", selected_entry))
        elif candidate.suffix.lower() != ".py":
            findings.append(PythonFinding("error", "ENTRY_POINT_NOT_PYTHON", "Entry point must be a .py file.", relative_or_error))
        else:
            resolved_entry = relative_or_error
            try:
                source = candidate.read_text(encoding="utf-8")
            except UnicodeDecodeError as exc:
                findings.append(PythonFinding("error", "ENTRY_POINT_UTF8", f"Entry point is not valid UTF-8: {exc}", resolved_entry))
            else:
                try:
                    compile(source, str(candidate), "exec")
                except SyntaxError as exc:
                    location = f"line {exc.lineno}" if exc.lineno else "unknown line"
                    findings.append(PythonFinding(
                        "error",
                        "ENTRY_POINT_SYNTAX",
                        f"Python syntax error at {location}: {exc.msg}",
                        resolved_entry,
                    ))

    if importlib.util.find_spec("PyInstaller") is None:
        findings.append(PythonFinding(
            "error",
            "PYINSTALLER_MISSING",
            "PyInstaller is not available in the Rubra Packager runtime.",
        ))

    if dependency_mode == "requirements" and "requirements.txt" not in dependency_files:
        findings.append(PythonFinding(
            "error",
            "REQUIREMENTS_MISSING",
            "Dependency setup is set to requirements.txt, but requirements.txt was not found.",
        ))
    elif dependency_mode == "project" and not any(
        name in dependency_files for name in ("pyproject.toml", "setup.cfg", "setup.py")
    ):
        findings.append(PythonFinding(
            "error",
            "PROJECT_METADATA_MISSING",
            "Dependency setup is set to install project, but no pyproject.toml, setup.cfg or setup.py was found.",
        ))
    elif dependency_mode == "none" and dependency_files:
        findings.append(PythonFinding(
            "warning",
            "DEPENDENCIES_NOT_ISOLATED",
            "Project dependency metadata was detected, but dependency setup is disabled. "
            "The build will use only modules already available to the active build environment.",
        ))

    valid_hidden: list[str] = []
    for module in hidden:
        if not _MODULE_NAME.fullmatch(module):
            findings.append(PythonFinding(
                "error",
                "HIDDEN_IMPORT_INVALID",
                f"Invalid hidden import module name: {module}",
            ))
        else:
            valid_hidden.append(module)

    valid_data: list[str] = []
    for raw in data:
        candidate, relative_or_error = _relative_path(root, raw, "Additional data path")
        if candidate is None:
            findings.append(PythonFinding("error", "DATA_PATH_INVALID", relative_or_error or "Invalid data path", raw))
        elif not candidate.exists():
            findings.append(PythonFinding("error", "DATA_PATH_MISSING", f"Additional data path not found: {raw}", raw))
        else:
            valid_data.append(relative_or_error or raw)

    valid_searches: list[str] = []
    for raw in searches:
        candidate, relative_or_error = _relative_path(root, raw, "Search path")
        if candidate is None:
            findings.append(PythonFinding("error", "SEARCH_PATH_INVALID", relative_or_error or "Invalid search path", raw))
        elif not candidate.is_dir():
            findings.append(PythonFinding("error", "SEARCH_PATH_MISSING", f"Search path is not a directory: {raw}", raw))
        else:
            valid_searches.append(relative_or_error or raw)

    return PythonPreflightReport(
        project_root=str(root),
        entry_point=resolved_entry,
        python_version=sys.version.split()[0],
        pyinstaller_available=importlib.util.find_spec("PyInstaller") is not None,
        dependency_mode=dependency_mode,
        dependency_files=dependency_files,
        hidden_imports=tuple(valid_hidden),
        data_paths=tuple(valid_data),
        search_paths=tuple(valid_searches),
        suggested_entry_points=candidates,
        findings=tuple(findings),
    )
