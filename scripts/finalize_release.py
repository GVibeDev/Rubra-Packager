from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rubra_packager import __version__  # noqa: E402
from rubra_packager.io_utils import sha256_file  # noqa: E402


def _release_assets(output_dir: Path) -> list[Path]:
    patterns = (
        f"RubraPackager-{__version__}-Setup.exe",
        f"RubraPackager-{__version__}-Portable.zip",
        f"rubra_packager-{__version__}-*.whl",
    )
    assets: list[Path] = []
    for pattern in patterns:
        assets.extend(path for path in output_dir.glob(pattern) if path.is_file())
    unique = {path.name: path for path in assets}
    return [unique[name] for name in sorted(unique)]


def finalize(output_dir: Path) -> dict[str, object]:
    output_dir = output_dir.resolve()
    assets = _release_assets(output_dir)
    if not assets:
        raise RuntimeError(f"No release assets found in {output_dir}")

    manifest = {
        "schemaVersion": 2,
        "product": "Rubra Packager",
        "version": __version__,
        "publisher": "GVibeDev",
        "releaseKind": "frozen-onedir-with-private-build-runtime",
        "requirements": {
            "platform": "Windows 10/11",
            "python": ">=3.11 required for first private build-runtime preparation",
            "firstBootstrapInternet": True,
        },
        "architecture": {
            "applicationCore": "Installed RubraPackager.exe + PyInstaller ONEDIR support files",
            "buildRuntime": "%LOCALAPPDATA%\\RubraPackager\\runtime\\.venv",
            "separation": "The frozen GUI never uses itself as the Python/PyInstaller build engine.",
        },
        "maintenance": {
            "applicationInstall": "%LOCALAPPDATA%\\Programs\\Rubra Packager",
            "runtime": "%LOCALAPPDATA%\\RubraPackager\\runtime",
            "userDataPolicy": "Uninstall removes the private build runtime but preserves project registry and reports.",
        },
        "signing": {
            "supported": True,
            "requiredForDevelopment": False,
            "note": "A Setup EXE may be Authenticode-signed when release signing is configured.",
        },
        "assets": [
            {"name": path.name, "bytes": path.stat().st_size, "sha256": sha256_file(path)}
            for path in assets
        ],
    }
    manifest_path = output_dir / f"RubraPackager-{__version__}.release.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    checksum_assets = assets + [manifest_path]
    checksums = output_dir / "SHA256SUMS.txt"
    checksums.write_text(
        "\n".join(f"{sha256_file(path)}  {path.name}" for path in checksum_assets) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return {
        "version": __version__,
        "manifest": str(manifest_path),
        "checksums": str(checksums),
        "assets": [path.name for path in assets],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Finalize Rubra Packager release hashes and manifest")
    parser.add_argument("--output", type=Path, default=ROOT / "release")
    args = parser.parse_args()
    print(json.dumps(finalize(args.output), indent=2))


if __name__ == "__main__":
    main()
