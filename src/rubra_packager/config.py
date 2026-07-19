from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "Rubra Packager"
APP_SLUG = "RubraPackager"


def user_data_dir() -> Path:
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    path = root / APP_SLUG
    path.mkdir(parents=True, exist_ok=True)
    return path


def project_registry_path() -> Path:
    return user_data_dir() / "projects.json"


def reports_dir() -> Path:
    path = user_data_dir() / "reports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def android_work_root() -> Path:
    path = user_data_dir() / "android"
    path.mkdir(parents=True, exist_ok=True)
    return path


def windows_work_root() -> Path:
    path = user_data_dir() / "windows"
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_output_dir() -> Path:
    path = Path.home() / "Downloads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def profile_dirs() -> tuple[Path, ...]:
    package_profiles = Path(__file__).resolve().parent / "profiles"
    repo_profiles = repository_root() / "profiles"
    return tuple(path for path in (package_profiles, repo_profiles) if path.exists())
