from __future__ import annotations

import json
from pathlib import Path

from .config import profile_dirs
from .models import BuildProfile, Variant
from .security import safe_identifier


class ProfileRegistry:
    def __init__(self, directories: tuple[Path, ...] | None = None) -> None:
        self.directories = directories or profile_dirs()
        self._profiles = self._load()

    def _load(self) -> dict[str, BuildProfile]:
        profiles: dict[str, BuildProfile] = {}
        for directory in self.directories:
            for path in sorted(directory.glob("*.json")):
                with path.open("r", encoding="utf-8") as handle:
                    data = json.load(handle)
                profile_id = safe_identifier(str(data["id"]), "profile id")
                variants = tuple(
                    Variant(
                        variant_id=safe_identifier(str(item["id"]), "variant id"),
                        label=str(item["label"]),
                        description=str(item.get("description", "")),
                        exclude_globs=tuple(str(value) for value in item.get("excludeGlobs", [])),
                    )
                    for item in data.get("variants", [])
                )
                if not variants:
                    raise ValueError(f"Profile {profile_id} defines no variants")
                profiles[profile_id] = BuildProfile(
                    profile_id=profile_id,
                    label=str(data["label"]),
                    description=str(data.get("description", "")),
                    entry_point=str(data.get("entryPoint", "index.html")),
                    orientation=str(data.get("orientation", "landscape")),
                    default_variant=str(data.get("defaultVariant", variants[0].variant_id)),
                    required_paths=tuple(str(value) for value in data.get("requiredPaths", ["index.html"])),
                    manifest_candidates=tuple(str(value) for value in data.get("manifestCandidates", [])),
                    variants=variants,
                )
        if not profiles:
            raise RuntimeError("No build profiles were found")
        return profiles

    def list(self) -> list[BuildProfile]:
        return sorted(self._profiles.values(), key=lambda item: item.label.casefold())

    def get(self, profile_id: str) -> BuildProfile:
        profile_id = safe_identifier(profile_id, "profile id")
        try:
            return self._profiles[profile_id]
        except KeyError as exc:
            raise KeyError(f"Unknown profile: {profile_id}") from exc
