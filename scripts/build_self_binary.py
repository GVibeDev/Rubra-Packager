from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rubra_packager import __version__  # noqa: E402
from rubra_packager.io_utils import sha256_file  # noqa: E402
from rubra_packager.process import run  # noqa: E402
from rubra_packager.windows_metadata import write_version_file  # noqa: E402


def _windows_host() -> bool:
    return os.name == "nt"


def build_self_binary(output_dir: Path, *, icon_path: Path | None = None) -> dict[str, object]:
    if not _windows_host():
        raise RuntimeError("Rubra Packager self-binary builds are supported on Windows only")

    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    work = output_dir / "_self_build"
    dist = work / "dist"
    build = work / "pyinstaller"
    spec = work / "spec"
    for path in (dist, build, spec):
        if path.exists():
            shutil.rmtree(path)
    work.mkdir(parents=True, exist_ok=True)
    spec.mkdir(parents=True, exist_ok=True)

    version_file = write_version_file(
        work / "version_info.txt",
        app_name="Rubra Packager",
        version=__version__,
        publisher="GVibeDev",
        description="Desktop application and game packaging tool",
        original_filename="RubraPackager.exe",
    )

    default_icon = ROOT / "assets" / "branding" / "rubra-packager.ico"
    effective_icon = icon_path if icon_path else (default_icon if default_icon.is_file() else None)

    args: list[str | Path] = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--noupx",
        "--onedir",
        "--windowed",
        "--name=RubraPackager",
        f"--paths={SRC}",
        f"--distpath={dist}",
        f"--workpath={build}",
        f"--specpath={spec}",
        f"--version-file={version_file}",
        "--collect-data=rubra_packager",
        "--collect-all=webview",
        "--hidden-import=webview.platforms.winforms",
        "--hidden-import=webview.platforms.edgechromium",
    ]
    if effective_icon and effective_icon.is_file():
        args.append(f"--icon={effective_icon.resolve()}")
    args.append(ROOT / "scripts" / "rubra_packager_frozen_entry.py")

    result = run(args, cwd=ROOT, timeout=1800)
    if result.returncode != 0:
        details = (result.stderr or result.stdout)[-12000:]
        raise RuntimeError(f"Rubra Packager PyInstaller self-build failed:\n{details}")

    built = dist / "RubraPackager"
    exe = built / "RubraPackager.exe"
    if not exe.is_file():
        raise RuntimeError(f"Expected self-build EXE was not produced: {exe}")

    portable = output_dir / f"RubraPackager-{__version__}-Portable"
    if portable.exists():
        shutil.rmtree(portable)
    shutil.copytree(built, portable)
    published_exe = portable / "RubraPackager.exe"
    return {
        "success": True,
        "version": __version__,
        "bundlePath": str(portable),
        "path": str(published_exe),
        "sha256": sha256_file(published_exe),
        "bytes": sum(path.stat().st_size for path in portable.rglob("*") if path.is_file()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Rubra Packager Windows ONEDIR binary")
    parser.add_argument("--output", type=Path, default=ROOT / "release")
    parser.add_argument("--icon", type=Path, default=None)
    args = parser.parse_args()
    print(json.dumps(build_self_binary(args.output, icon_path=args.icon), indent=2))


if __name__ == "__main__":
    main()
