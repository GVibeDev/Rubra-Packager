from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = "1.0.0"


def fail(message: str) -> None:
    raise SystemExit(f"REPOSITORY CHECK FAILED: {message}")


def _git_tracked_files() -> list[Path] | None:
    if not (ROOT / ".git").exists() or shutil.which("git") is None:
        return None
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return [ROOT / line for line in result.stdout.splitlines() if line.strip()]


def main() -> None:
    checks: list[str] = []
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    init = (ROOT / "src/rubra_packager/__init__.py").read_text(encoding="utf-8")
    if f'version = "{EXPECTED}"' not in pyproject:
        fail("pyproject version is not synchronized")
    if f'__version__ = "{EXPECTED}"' not in init:
        fail("package version is not synchronized")
    for name in ("run_windows.cmd", "bootstrap_source_runtime.cmd", "diagnose_windows.cmd", "build_release_windows.cmd"):
        text = (ROOT / name).read_text(encoding="utf-8")
        if f"EXPECTED_VERSION={EXPECTED}" not in text:
            fail(f"{name} version is not synchronized")
    checks.append("version synchronization")

    required = [
        "README.md", "LICENSE", "NOTICE.md", "PROVENANCE.md", "SECURITY.md", "CONTRIBUTING.md",
        "docs/USER_GUIDE.md", "docs/BUILDING.md", "docs/PUBLISHING.md", "docs/DEVELOPMENT_HISTORY.md",
        "docs/PUBLICATION_CHECKLIST.md", "scripts/build_release.py", "scripts/build_self_binary.py",
        "scripts/finalize_release.py", "scripts/validate_repository.py",
        "src/rubra_packager/windows_metadata.py", "src/rubra_packager/runtime_engine.py",
        "assets/branding/rubra-packager.ico", "build_release_windows.cmd", "bootstrap_source_runtime.cmd",
        ".github/workflows/ci.yml",
    ]
    for rel in required:
        if not (ROOT / rel).is_file():
            fail(f"required public file missing: {rel}")
    if (ROOT / ".github/workflows/release.yml").exists():
        fail("automatic GitHub binary release workflow must remain absent under the v1 source-only policy")
    checks.append("public source/release policy files")

    tracked = _git_tracked_files()
    forbidden_roots = {"release", "build", "dist", "payload", ".venv", "node_modules"}
    forbidden_suffixes = {".exe", ".msi", ".whl", ".apk", ".aab", ".pfx", ".p12", ".jks", ".keystore", ".pyc"}
    if tracked is not None:
        bad = []
        for path in tracked:
            rel = path.relative_to(ROOT)
            if rel.parts and rel.parts[0] in forbidden_roots:
                bad.append(rel)
            elif path.suffix.casefold() in forbidden_suffixes:
                bad.append(rel)
        if bad:
            fail("generated/private files are tracked by git: " + ", ".join(str(p) for p in bad[:12]))
        checks.append("no generated/private files tracked by git")
    else:
        # Source archive mode: reject release/build payloads, but ignore harmless caches
        # that may appear after somebody locally runs the tests.
        bad_dirs = [ROOT / name for name in ("release", "build", "dist", "payload", ".venv", "node_modules") if (ROOT / name).exists()]
        if bad_dirs:
            fail("generated directories present in source archive: " + ", ".join(p.name for p in bad_dirs))
        checks.append("no generated release/build directories in source archive")

    for path in (ROOT / "src").rglob("*.py"):
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    checks.append("Python source syntax")

    print("Rubra Packager public repository check: PASS")
    for item in checks:
        print(f"  [OK] {item}")


if __name__ == "__main__":
    main()
