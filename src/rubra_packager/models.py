from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ProjectRecord:
    project_id: str
    name: str
    source_path: str
    description: str = ""
    author: str = ""
    version: str = "1.0.0"
    profile_id: str = "generic-web-game"
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectRecord":
        return cls(
            project_id=str(data["project_id"]),
            name=str(data.get("name", data["project_id"])),
            source_path=str(data["source_path"]),
            description=str(data.get("description", "")),
            author=str(data.get("author", "")),
            version=str(data.get("version", "1.0.0")),
            profile_id=str(data.get("profile_id", "generic-web-game")),
            created_at=str(data.get("created_at", "")),
            updated_at=str(data.get("updated_at", "")),
        )


@dataclass(frozen=True)
class Variant:
    variant_id: str
    label: str
    description: str
    exclude_globs: tuple[str, ...] = ()


@dataclass(frozen=True)
class BuildProfile:
    profile_id: str
    label: str
    description: str
    entry_point: str
    orientation: str
    default_variant: str
    required_paths: tuple[str, ...]
    manifest_candidates: tuple[str, ...]
    variants: tuple[Variant, ...]

    def variant(self, variant_id: str | None) -> Variant:
        selected = variant_id or self.default_variant
        for variant in self.variants:
            if variant.variant_id == selected:
                return variant
        raise KeyError(f"Unknown variant {selected!r} for profile {self.profile_id}")


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PreflightReport:
    profile_id: str
    variant_id: str
    source_path: str
    scanned_files: int
    included_files: int
    excluded_files: int
    included_bytes: int
    findings: list[Finding] = field(default_factory=list)
    included_paths: list[str] = field(default_factory=list)
    excluded_paths: list[str] = field(default_factory=list)

    @property
    def errors(self) -> int:
        return sum(item.severity == "error" for item in self.findings)

    @property
    def warnings(self) -> int:
        return sum(item.severity == "warning" for item in self.findings)

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "errors": self.errors,
            "warnings": self.warnings,
            "ok": self.errors == 0,
        }
