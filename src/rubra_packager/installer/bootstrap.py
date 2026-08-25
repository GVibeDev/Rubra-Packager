from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from ..process import ProcessResult, run
from ..security import ValidationError
from .inno import find_iscc

WINGET_PACKAGE_ID = "JRSoftware.InnoSetup"


def find_winget() -> Path | None:
    for name in ("winget.exe", "winget"):
        found = shutil.which(name)
        if found:
            return Path(found).resolve()
    return None


def prerequisites() -> dict[str, Any]:
    iscc = find_iscc()
    winget = find_winget()
    windows = os.name == "nt"
    return {
        "inno": {
            "ok": iscc is not None,
            "message": str(iscc) if iscc else "Inno Setup compiler (ISCC.exe) not found",
            "path": str(iscc) if iscc else "",
        },
        "winget": {
            "ok": windows and winget is not None,
            "message": str(winget) if winget else ("Windows Package Manager (winget) not found" if windows else "Bootstrap is available on Windows only"),
            "path": str(winget) if winget else "",
        },
        "bootstrapSupported": bool(windows and winget is not None),
    }


def install_inno(*, scope: str = "user") -> dict[str, Any]:
    """Install Inno Setup through winget after an explicit UI action.

    This function is intentionally never called implicitly from a setup build.
    """
    if os.name != "nt":
        raise ValidationError("Inno Setup bootstrap is available on Windows only")

    normalized_scope = (scope or "user").strip().lower()
    if normalized_scope not in {"user", "machine"}:
        raise ValidationError("Inno Setup install scope must be user or machine")

    existing = find_iscc()
    if existing is not None:
        return {
            "success": True,
            "alreadyInstalled": True,
            "path": str(existing),
            "log": [f"Inno Setup already installed: {existing}"],
        }

    winget = find_winget()
    if winget is None:
        return {
            "success": False,
            "error": "Windows Package Manager (winget) was not found. Install Inno Setup manually from the official JRSoftware distribution.",
            "log": [],
        }

    args = [
        winget,
        "install",
        "--id", WINGET_PACKAGE_ID,
        "--exact",
        "--source", "winget",
        "--scope", normalized_scope,
        "--accept-package-agreements",
        "--accept-source-agreements",
        "--silent",
    ]
    result: ProcessResult = run(args)
    log = [line for line in (result.stdout + "\n" + result.stderr).splitlines()[-180:] if line.strip()]
    if result.returncode != 0:
        return {
            "success": False,
            "error": f"winget could not install Inno Setup (exit code {result.returncode})",
            "log": log,
        }

    installed = find_iscc()
    if installed is None:
        return {
            "success": False,
            "error": "winget reported success, but ISCC.exe could not be located. Restart Rubra Packager or install Inno Setup manually.",
            "log": log,
        }

    log.append(f"Inno Setup detected after bootstrap: {installed}")
    return {
        "success": True,
        "alreadyInstalled": False,
        "path": str(installed),
        "log": log,
    }
