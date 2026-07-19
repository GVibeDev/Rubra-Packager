# Rubra Packager

Rubra Packager is a Windows desktop tool for validating and packaging trusted offline web games as:

- a one-file Windows executable powered by PyInstaller and PyWebView;
- an Android debug APK powered by Capacitor and Gradle.

The project is deliberately focused on web games and static HTML applications. It is not a general Python-to-EXE suite and it does not modify application source code to force unsupported server frameworks into static exports.

## Current baseline

**RP-R4c — Reference Resolver & Preflight Accuracy Hotfix**

RP-R4 replaces the earlier prototype shell with an independent public repository structure:

- a new navy-and-gold interface;
- a new project registry under `%LOCALAPPDATA%\RubraPackager`;
- profile-driven FULL/LITE packaging;
- preflight validation before Windows and Android builds;
- custom Windows and Android icons;
- APK integrity and debug-signature verification;
- optional migration of project metadata from `Documents\HTML2EXE`;
- no original HTML2EXE branding, images, Git history or UI files.

## Installation on Windows

1. Extract the complete archive to a normal folder.
2. Run `run_windows.cmd` normally, not as Administrator.

The launcher creates or repairs a per-user runtime under
`%LOCALAPPDATA%\RubraPackager\runtime`, installs a normal wheel copy of the
package and runs the automated tests. A half-created environment is never
treated as a valid installation.

## Development installation

Editable installation remains available for contributors:

```cmd
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e .
.venv\Scripts\python.exe run_tests.py
.venv\Scripts\python.exe -m rubra_packager
```

The public Windows launcher intentionally does not use this editable
environment.

## Workflow

1. Register a trusted project folder.
2. Select a build profile and FULL/LITE variant.
3. Run preflight.
4. Fix blocking errors and review warnings.
5. Build a Windows EXE or Android APK.
6. Verify the generated SHA-256 and test the application on the target device.

## Trust boundary

Rubra Packager can run `npm install` and `npm run build` when a project has no ready static output. Those commands can execute arbitrary package scripts. The UI therefore requires an explicit trust checkbox before source execution.

## Supported source layouts

The packager recognizes an existing root `index.html` or common static output folders:

- `dist/`
- `build/`
- `out/`
- `.output/public/`
- Gatsby `public/` when Gatsby is detected
- Angular-style `dist/<project>/browser/`

Framework projects must produce a real static `index.html`. Server-side rendering, backend APIs and dynamic routes are outside the current scope.

## Profiles

Built-in profiles:

- `arena-rubra`
- `generic-web-game`
- `generic-html-app`

Profiles define required paths, orientation, optional manifest names and variant exclusion patterns. Custom profiles can be added under `profiles/`.

## Android requirements

Android export requires:

- JDK 17 or newer;
- Android SDK installed through Android Studio;
- Node.js and npm.

RP-R4 produces a debug-signed APK using `assembleDebug`. Release signing and AAB output remain future milestones.

## Repository layout

```text
src/rubra_packager/       application package
  static/                 independent navy/gold UI
  profiles/               packaged build profiles
profiles/                 editable profile definitions
tests/                    automated regression tests
setup_windows.cmd         first-time setup
run_windows.cmd           normal launcher
diagnose_windows.cmd      environment report
```

## License and provenance

Rubra Packager is distributed under the Mozilla Public License 2.0. See `LICENSE`, `NOTICE.md` and `PROVENANCE.md`.


## Pip cache isolation — RP-R4b

The Windows setup does not read or write the global pip cache. All public pip
commands use `--no-cache-dir`, preventing permissions inherited from a previous
Administrator session from blocking installation.


## Preflight reference policy — RP-R4c

Preflight blocks only references that can be resolved with high confidence:
static HTML/CSS URLs, local JavaScript module imports and static
`new URL(..., import.meta.url)` assets. Dynamic filenames and runtime-generated
Blob/Data URLs are not guessed. Projects may declare dynamic required assets in
an optional asset manifest for exact verification.
