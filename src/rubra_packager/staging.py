from __future__ import annotations

import fnmatch
import shutil
from pathlib import Path

from .models import Variant

SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".gradle"}


def should_skip(relative: str, variant: Variant) -> bool:
    normalized = relative.replace("\\", "/")
    parts = normalized.split("/")
    if any(part in SKIP_DIRS for part in parts):
        return True
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in variant.exclude_globs)


def stage_source(source: Path, destination: Path, variant: Variant) -> tuple[list[str], list[str]]:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    included: list[str] = []
    excluded: list[str] = []
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(source).as_posix()
        if should_skip(relative, variant):
            excluded.append(relative)
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        included.append(relative)
    return included, excluded
