from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SetupArtifact:
    source_path: Path
    artifact_kind: str
    primary_exe: Path

    @property
    def root(self) -> Path:
        return self.source_path if self.artifact_kind == "onedir" else self.source_path.parent


@dataclass(frozen=True)
class SetupOptions:
    app_name: str
    version: str
    publisher: str
    app_id: str
    install_mode: str
    install_dir_name: str
    desktop_shortcut: bool
    start_menu_shortcut: bool
    launch_after_install: bool
    license_file: Path | None = None
    release_notes_file: Path | None = None
