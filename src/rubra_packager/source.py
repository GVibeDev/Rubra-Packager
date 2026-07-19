from __future__ import annotations

import json
from pathlib import Path

from .process import executable, run


OUTPUT_CANDIDATES = (
    "dist",
    "build",
    "out",
    ".output/public",
)


def _contains_index(path: Path) -> bool:
    return path.is_dir() and (path / "index.html").is_file()


def locate_static_output(project_root: Path) -> Path | None:
    if _contains_index(project_root):
        return project_root
    for relative in OUTPUT_CANDIDATES:
        candidate = project_root / relative
        if _contains_index(candidate):
            return candidate
    package_json = project_root / "package.json"
    if package_json.is_file():
        try:
            package = json.loads(package_json.read_text(encoding="utf-8"))
            dependencies = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
            gatsby_public = project_root / "public"
            if "gatsby" in dependencies and _contains_index(gatsby_public):
                return gatsby_public
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass
    dist = project_root / "dist"
    if dist.is_dir():
        for child in sorted(dist.iterdir()):
            if _contains_index(child / "browser"):
                return child / "browser"
            if _contains_index(child):
                return child
    return None


def resolve_static_source(project_root: Path, *, allow_build: bool, log: list[str]) -> Path:
    project_root = project_root.resolve()
    existing = locate_static_output(project_root)
    if existing:
        log.append(f"Static source: {existing}")
        return existing

    package_json = project_root / "package.json"
    if not package_json.is_file():
        raise RuntimeError("No index.html or supported static output folder was found")
    with package_json.open("r", encoding="utf-8") as handle:
        package = json.load(handle)
    if "build" not in package.get("scripts", {}):
        raise RuntimeError("package.json has no build script and no static output is present")
    if not allow_build:
        raise RuntimeError(
            "This source needs npm install/build. Confirm that the project is trusted before enabling source execution."
        )

    npm = executable("npm")
    log.append("Running npm install in trusted source project")
    install = run([npm, "install"], cwd=project_root)
    log.extend(line for line in install.stdout.splitlines()[-80:] if line.strip())
    install.require_success("npm install")

    log.append("Running npm run build")
    build = run([npm, "run", "build"], cwd=project_root)
    log.extend(line for line in build.stdout.splitlines()[-120:] if line.strip())
    build.require_success("npm run build")

    output = locate_static_output(project_root)
    if output is None:
        raise RuntimeError(
            "The build completed but Rubra Packager could not find index.html in dist/, build/, out/, public/ or .output/public/."
        )
    log.append(f"Static output resolved: {output}")
    return output
