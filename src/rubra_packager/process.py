from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping


@dataclass(frozen=True)
class ProcessResult:
    args: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    def require_success(self, label: str = "command") -> "ProcessResult":
        if self.returncode != 0:
            details = (self.stderr or self.stdout).strip()
            raise RuntimeError(f"{label} failed with code {self.returncode}:\n{details[-5000:]}")
        return self


def executable(name: str) -> str:
    candidates = [name]
    if os.name == "nt" and not name.lower().endswith((".exe", ".cmd", ".bat")):
        candidates = [f"{name}.cmd", f"{name}.exe", name]
    for candidate in candidates:
        found = shutil.which(candidate)
        if found:
            return found
    raise FileNotFoundError(f"Executable not found in PATH: {name}")


def run(
    args: Iterable[str | Path],
    *,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
    timeout: int | None = None,
) -> ProcessResult:
    normalized = tuple(str(item) for item in args)
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    completed = subprocess.run(
        normalized,
        cwd=str(cwd) if cwd else None,
        env=dict(env) if env else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
        timeout=timeout,
        creationflags=flags,
    )
    return ProcessResult(normalized, completed.returncode, completed.stdout, completed.stderr)
