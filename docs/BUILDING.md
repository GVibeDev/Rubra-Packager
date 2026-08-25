# Building Rubra Packager from source

## Supported host

The public v1 build workflow targets Windows 10/11.

Required:

- Python 3.11+;
- internet access for the first source/private build-runtime preparation;
- Inno Setup 6 or 7 for the final Setup EXE.

The repository includes the release tooling. Generated binaries are intentionally not committed.

## Source launcher

Run:

```text
run_windows.cmd
```

`run_windows.cmd` checks the expected Rubra Packager version and calls `bootstrap_source_runtime.cmd` only if the private source runtime is missing, damaged or outdated.

## Runtime bootstrap

You normally do not need to call this manually:

```text
bootstrap_source_runtime.cmd
```

Its only responsibility is to create/repair:

```text
%LOCALAPPDATA%\RubraPackager\runtime\.venv
```

and install the current source package and its core dependencies there.

This helper is deliberately separate from the release builder. Removing it would force the same bootstrap logic to be duplicated in both the source launcher and release builder.

## Automated checks

From a prepared source runtime:

```text
python run_tests.py
python scripts\validate_repository.py
node --check src\rubra_packager\static\app.js
```

The GitHub repository keeps a source CI workflow for Python 3.11 and 3.13. It tests and builds a wheel as a smoke check but does not publish binary releases.

## Build Portable + Setup

Install Inno Setup 6/7, then run:

```text
build_release_windows.cmd
```

The helper:

1. verifies a normal, non-elevated user session;
2. prepares/repairs the private source runtime when necessary;
3. verifies the exact package version;
4. runs `scripts\build_release.py --require-setup`;
5. builds Rubra Packager itself as a PyInstaller ONEDIR application;
6. creates the Portable ZIP;
7. generates and compiles the Inno Setup script;
8. builds the source wheel;
9. writes the release manifest and SHA-256 checksums.

Output is written to ignored `release\` paths.

## Build scripts

- `scripts/build_self_binary.py` — creates the RubraPackager.exe ONEDIR core.
- `scripts/build_release.py` — assembles Portable and Setup release outputs.
- `scripts/finalize_release.py` — writes release manifest and SHA256SUMS for release artifacts.
- `scripts/sign_release.ps1` — optional Authenticode hook; certificate material is never part of the repository.
- `scripts/validate_repository.py` — checks that the public source tree is clean and version-synchronized.

## Why the installed app still needs Python

The desktop GUI is a frozen Windows executable, but Web → EXE and Python → Windows need a real Python/PyInstaller engine. Rubra Packager therefore keeps the GUI and build engine separate:

```text
Installed RubraPackager.exe
        |\n        +--> %LOCALAPPDATA%\RubraPackager\runtime\.venv\Scripts\python.exe
```

The frozen GUI never tries to use itself as `python.exe`.

## What not to commit

Do not commit `release/`, `build/`, `dist/`, wheels, EXEs, APK/AAB files, Android signing keys, Authenticode private keys/certificates, local project registries, runtime environments or dependency staging directories. The repository `.gitignore` covers these standard outputs, but always inspect the GitHub Desktop change list before committing.
