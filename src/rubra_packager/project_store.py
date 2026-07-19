from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .config import project_registry_path
from .io_utils import atomic_write_json, read_json
from .models import ProjectRecord
from .security import safe_identifier, require_existing_dir


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProjectStore:
    def __init__(self, registry_path: Path | None = None) -> None:
        self.registry_path = registry_path or project_registry_path()

    def list(self) -> list[ProjectRecord]:
        payload = read_json(self.registry_path, default={"projects": []}) or {"projects": []}
        records = [ProjectRecord.from_dict(item) for item in payload.get("projects", [])]
        return sorted(records, key=lambda item: item.name.casefold())

    def save_all(self, records: Iterable[ProjectRecord]) -> None:
        atomic_write_json(
            self.registry_path,
            {"schema": 1, "projects": [record.to_dict() for record in records]},
        )

    def upsert(self, record: ProjectRecord) -> ProjectRecord:
        record.project_id = safe_identifier(record.project_id, "project id")
        record.source_path = str(require_existing_dir(record.source_path, "project source"))
        now = _now()
        existing = {item.project_id: item for item in self.list()}
        if record.project_id in existing:
            record.created_at = existing[record.project_id].created_at or now
        else:
            record.created_at = record.created_at or now
        record.updated_at = now
        existing[record.project_id] = record
        self.save_all(existing.values())
        return record

    def get(self, project_id: str) -> ProjectRecord:
        project_id = safe_identifier(project_id, "project id")
        for record in self.list():
            if record.project_id == project_id:
                return record
        raise KeyError(f"Unknown project: {project_id}")

    def delete(self, project_id: str) -> bool:
        project_id = safe_identifier(project_id, "project id")
        records = self.list()
        remaining = [record for record in records if record.project_id != project_id]
        changed = len(remaining) != len(records)
        if changed:
            self.save_all(remaining)
        return changed

    def import_legacy(self, legacy_root: Path | None = None) -> int:
        root = legacy_root or (Path.home() / "Documents" / "HTML2EXE")
        if not root.is_dir():
            return 0
        existing_ids = {item.project_id for item in self.list()}
        imported = 0
        for metadata in sorted(root.glob("*/project.json")):
            try:
                data = read_json(metadata, default={}) or {}
                source = data.get("downloadFolder") or data.get("sourceFolder")
                if not source or not Path(source).is_dir():
                    continue
                raw_id = metadata.parent.name
                project_id = raw_id if raw_id not in existing_ids else f"legacy-{raw_id}"
                project_id = safe_identifier(project_id, "legacy project id")
                name = str(data.get("name") or raw_id)
                profile = "arena-rubra" if "arena" in name.casefold() and "rubra" in name.casefold() else "generic-web-game"
                self.upsert(ProjectRecord(
                    project_id=project_id,
                    name=name,
                    source_path=str(Path(source).resolve()),
                    description=str(data.get("description", "")),
                    author=str(data.get("author", "")),
                    version=str(data.get("version", "1.0.0")),
                    profile_id=profile,
                ))
                existing_ids.add(project_id)
                imported += 1
            except Exception:
                continue
        return imported
