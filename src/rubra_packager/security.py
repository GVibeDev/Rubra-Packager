from __future__ import annotations

import re
from pathlib import Path

_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
_PACKAGE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z][a-zA-Z0-9_]*)+$")


class ValidationError(ValueError):
    pass


def safe_identifier(value: str, label: str = "identifier") -> str:
    value = (value or "").strip()
    if not _IDENTIFIER.fullmatch(value):
        raise ValidationError(
            f"Invalid {label}. Use 1-80 letters, digits, dots, dashes or underscores; "
            "the first character must be alphanumeric."
        )
    return value


def safe_filename_stem(value: str) -> str:
    value = (value or "").strip()
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-")
    if not cleaned:
        raise ValidationError("The output name does not contain any usable characters.")
    return cleaned[:96]


def validate_package_name(value: str) -> str:
    value = (value or "").strip()
    if not _PACKAGE.fullmatch(value):
        raise ValidationError("Android package name must look like com.example.application")
    return value.lower()


def confine(root: Path, candidate: Path) -> Path:
    root = root.resolve()
    candidate = candidate.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValidationError(f"Path escapes allowed root: {candidate}") from exc
    return candidate


def require_existing_dir(value: str | Path, label: str = "folder") -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise ValidationError(f"{label.capitalize()} not found: {path}")
    return path


def parse_hex_color(value: str) -> str:
    value = (value or "").strip()
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        raise ValidationError("Color must use #RRGGBB format")
    return value.upper()
