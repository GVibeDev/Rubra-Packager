from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from .config import user_data_dir
from .process import ProcessResult, run

ENGINE_REQUIREMENTS = (
    "pyinstaller>=6.10",
    "pywebview>=5.0",
    "Pillow>=10.0",
)
ENGINE_SCHEMA_VERSION = "1"


def is_frozen_app() -> bool:
    return bool(getattr(sys, "frozen", False))


def runtime_root() -> Path:
    path = user_data_dir() / "runtime"
    path.mkdir(parents=True, exist_ok=True)
    return path


def runtime_venv() -> Path:
    return runtime_root() / ".venv"


def private_python() -> Path:
    if os.name == "nt":
        return runtime_venv() / "Scripts" / "python.exe"
    return runtime_venv() / "bin" / "python"


def _tail(result: ProcessResult, limit: int = 120) -> list[str]:
    return [line for line in (result.stdout + "\n" + result.stderr).splitlines()[-limit:] if line.strip()]


def _python_probe(prefix: list[str]) -> bool:
    try:
        result = run(
            [*prefix, "-c", "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 2)"],
            timeout=30,
        )
    except (OSError, FileNotFoundError):
        return False
    return result.returncode == 0


def _bootstrap_python_prefix() -> list[str]:
    # In source/development mode, the active interpreter is the safest bootstrap.
    if not is_frozen_app() and Path(sys.executable).is_file():
        prefix = [sys.executable]
        if _python_probe(prefix):
            return prefix

    if os.name == "nt":
        py = shutil.which("py")
        if py:
            prefix = [py, "-3"]
            if _python_probe(prefix):
                return prefix

    for name in ("python", "python3"):
        found = shutil.which(name)
        if found:
            prefix = [found]
            if _python_probe(prefix):
                return prefix

    raise RuntimeError("Python 3.11 or newer was not found. Install Python and retry runtime preparation.")


def _installed_engine_probe(python: Path) -> tuple[bool, dict[str, str], list[str]]:
    if not python.is_file():
        return False, {}, [f"Build runtime Python is missing: {python}"]
    code = (
        "import json,sys; "
        "import PyInstaller, webview, PIL; "
        "print(json.dumps({'python':sys.version.split()[0],"
        "'pyinstaller':PyInstaller.__version__,"
        "'pywebview':getattr(webview,'__version__','installed'),"
        "'pillow':PIL.__version__}))"
    )
    try:
        result = run([python, "-c", code], timeout=30)
    except OSError as exc:
        return False, {}, [str(exc)]
    if result.returncode != 0:
        return False, {}, _tail(result)
    try:
        info = json.loads(result.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return False, {}, ["Build runtime probe returned invalid output"]
    return True, {str(k): str(v) for k, v in info.items()}, []


def runtime_status() -> dict[str, Any]:
    python = private_python()
    ok, versions, errors = _installed_engine_probe(python)
    if not is_frozen_app() and not ok:
        # Development/source mode may legitimately use its active venv.
        source_python = Path(sys.executable)
        source_ok, source_versions, source_errors = _installed_engine_probe(source_python)
        if source_ok:
            return {
                "ok": True,
                "mode": "source-active-python",
                "python": str(source_python),
                "versions": source_versions,
                "errors": [],
            }
        errors.extend(source_errors)
    return {
        "ok": ok,
        "mode": "private-runtime",
        "python": str(python),
        "versions": versions,
        "errors": errors,
    }


def build_python_executable(*, require_ready: bool = True) -> Path:
    status = runtime_status()
    if status["ok"]:
        return Path(str(status["python"]))
    if not require_ready and not is_frozen_app():
        return Path(sys.executable)
    raise RuntimeError(
        "Rubra Packager build runtime is not ready. "
        "Run RubraPackager.exe --prepare-runtime or reinstall/repair the application."
    )


def ensure_build_runtime(*, force: bool = False) -> dict[str, Any]:
    log: list[str] = []
    python = private_python()
    venv = runtime_venv()

    if not force:
        current = runtime_status()
        if current["ok"] and current["mode"] == "private-runtime":
            current["log"] = ["Build runtime is already ready."]
            return current

    if venv.exists() and not python.is_file():
        log.append("Incomplete build runtime detected; recreating it.")
        shutil.rmtree(venv)

    if not python.is_file():
        prefix = _bootstrap_python_prefix()
        log.append(f"Creating private build runtime with: {' '.join(prefix)}")
        result = run([*prefix, "-m", "venv", venv], timeout=180)
        log.extend(_tail(result))
        if result.returncode != 0 or not python.is_file():
            raise RuntimeError("Failed to create the private Rubra Packager build runtime.\n" + "\n".join(log[-40:]))

    log.append("Updating pip/setuptools/wheel in the private build runtime...")
    result = run([python, "-m", "pip", "install", "--no-cache-dir", "--upgrade", "pip", "setuptools", "wheel"], timeout=600)
    log.extend(_tail(result))
    if result.returncode != 0:
        raise RuntimeError("Failed to update build runtime packaging tools.\n" + "\n".join(log[-60:]))

    log.append("Installing Rubra Packager build-engine dependencies...")
    result = run([python, "-m", "pip", "install", "--no-cache-dir", "--upgrade", *ENGINE_REQUIREMENTS], timeout=900)
    log.extend(_tail(result))
    if result.returncode != 0:
        raise RuntimeError("Failed to install build runtime dependencies.\n" + "\n".join(log[-80:]))

    marker = runtime_root() / ".engine-schema"
    marker.write_text(ENGINE_SCHEMA_VERSION + "\n", encoding="utf-8")

    status = runtime_status()
    if not status["ok"]:
        raise RuntimeError("Build runtime verification failed.\n" + "\n".join(status.get("errors", [])))
    status["log"] = log
    return status
