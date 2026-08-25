from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
for path in (SRC, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from rubra_packager import __version__  # noqa: E402
from rubra_packager.installer.inno import compile_script, find_iscc  # noqa: E402

from build_self_binary import build_self_binary  # noqa: E402


def _zip_tree(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, (Path(source.name) / path.relative_to(source)).as_posix())
    with zipfile.ZipFile(target, "r") as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"ZIP integrity failure: {bad}")


def _inno_quote(path: Path) -> str:
    return str(path).replace('"', '""')


def _render_self_setup(core_dir: Path, output_dir: Path, *, setup_icon: Path | None = None) -> str:
    source_glob = _inno_quote(core_dir / "*")
    setup_icon_line = ""
    if setup_icon and setup_icon.is_file():
        setup_icon_line = f"SetupIconFile={_inno_quote(setup_icon)}\n"
    return f'''[Setup]\nAppId=RubraPackager\nAppName=Rubra Packager\nAppVersion={__version__}\nAppPublisher=GVibeDev\nDefaultDirName={{localappdata}}\\Programs\\Rubra Packager\nDefaultGroupName=Rubra Packager\nDisableProgramGroupPage=yes\nPrivilegesRequired=lowest\nCompression=lzma2\nSolidCompression=yes\nWizardStyle=modern\nCloseApplications=yes\nRestartApplications=no\nUninstallable=yes\nUsePreviousAppDir=yes\nUsePreviousTasks=yes\nOutputDir={_inno_quote(output_dir)}\nOutputBaseFilename=RubraPackager-{__version__}-Setup\n{setup_icon_line}\n[Files]\nSource: "{source_glob}"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs\n\n[Icons]\nName: "{{group}}\\Rubra Packager"; Filename: "{{app}}\\RubraPackager.exe"\nName: "{{autodesktop}}\\Rubra Packager"; Filename: "{{app}}\\RubraPackager.exe"; Tasks: desktopicon\n\n[Tasks]\nName: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked\n\n[Run]\nFilename: "{{app}}\\RubraPackager.exe"; Parameters: "--prepare-runtime"; Flags: runhidden waituntilterminated; StatusMsg: "Preparing the Rubra Packager build runtime..."\nFilename: "{{app}}\\RubraPackager.exe"; Description: "Launch Rubra Packager"; Flags: nowait postinstall skipifsilent\n\n[UninstallDelete]\nType: filesandordirs; Name: "{{localappdata}}\\RubraPackager\\runtime"\n'''


def _copy_core(source: Path, output_dir: Path) -> Path:
    exe = source / "RubraPackager.exe"
    if not exe.is_file():
        raise FileNotFoundError(f"Rubra Packager ONEDIR artifact is missing RubraPackager.exe: {source}")
    target = output_dir / f"RubraPackager-{__version__}-Portable"
    if target.resolve() == source.resolve():
        return target
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)
    return target


def build_release(
    output_dir: Path,
    *,
    require_setup: bool,
    tag: str | None = None,
    core_dir: Path | None = None,
    icon_path: Path | None = None,
) -> dict[str, str]:
    if tag and tag != f"v{__version__}":
        raise RuntimeError(f"Tag/version mismatch: tag={tag!r}, package=v{__version__}")

    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    work = output_dir / "_release_work"
    work.mkdir(parents=True, exist_ok=True)

    default_icon = ROOT / "assets" / "branding" / "rubra-packager.ico"
    effective_icon = icon_path if icon_path else (default_icon if default_icon.is_file() else None)

    if core_dir is None:
        self_result = build_self_binary(output_dir, icon_path=effective_icon)
        portable_dir = Path(str(self_result["bundlePath"]))
    else:
        portable_dir = _copy_core(core_dir.resolve(), output_dir)

    portable_zip = output_dir / f"RubraPackager-{__version__}-Portable.zip"
    _zip_tree(portable_dir, portable_zip)

    setup_script = work / f"RubraPackager-{__version__}.iss"
    setup_script.write_text(
        _render_self_setup(portable_dir, output_dir, setup_icon=effective_icon),
        encoding="utf-8",
        newline="\n",
    )

    setup_exe = output_dir / f"RubraPackager-{__version__}-Setup.exe"
    iscc = find_iscc()
    if iscc is None:
        if require_setup:
            raise RuntimeError("Inno Setup ISCC.exe is required for the release setup build")
    else:
        result = compile_script(iscc, setup_script)
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or "Inno Setup failed")[-8000:])
        if not setup_exe.is_file():
            raise RuntimeError(f"Expected setup was not produced: {setup_exe}")

    result = {
        "version": __version__,
        "portableDir": str(portable_dir),
        "portableExe": str(portable_dir / "RubraPackager.exe"),
        "portableZip": str(portable_zip),
        "setupScript": str(setup_script),
    }
    if setup_exe.is_file():
        result["setupExe"] = str(setup_exe)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Rubra Packager Windows release artifacts")
    parser.add_argument("--output", type=Path, default=ROOT / "release")
    parser.add_argument("--require-setup", action="store_true")
    parser.add_argument("--tag", default=None)
    parser.add_argument("--icon", type=Path, default=None)
    args = parser.parse_args()
    print(json.dumps(build_release(args.output, require_setup=args.require_setup, tag=args.tag, icon_path=args.icon), indent=2))


if __name__ == "__main__":
    main()
