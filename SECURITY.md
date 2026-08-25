# Security policy

Rubra Packager is a local build tool and processes projects selected by the user.

## Important trust warning

Never enable source/dependency execution for an untrusted project.

The following operations can execute project-controlled code with the current user's permissions:

```text
npm install
npm run build
pip install -r requirements.txt
pip install .
```

RP-R5 therefore requires explicit trust approval before Python dependency or project installation. Python dependencies are staged into an isolated build directory and are not installed into Rubra Packager's own runtime, but package build backends and install hooks can still execute code while staging.

Preflight itself does not execute the selected Python entry point.

## Local API

The desktop UI communicates with a loopback-only HTTP server. API requests require a random per-launch token and reject foreign browser origins.

## Path confinement

Additional Python data paths, search paths and entry points are resolved inside the selected project root. Paths that escape the project folder are rejected before build.

## Sensitive files

Do not commit:

- Android signing keys;
- `local.properties`;
- built APK, AAB or EXE files;
- personal project registries;
- generated Gradle folders;
- `.venv`, Python build dependency staging or `node_modules`.

## Reporting

Open a private security report or contact the repository owner before publishing an exploitable issue.

## Installer inputs

Setup Builder copies and installs the Windows artifact selected by the user. Only create installers from artifacts you trust and have tested. RP-R7 invokes Inno Setup and its optional winget bootstrap through argument lists and never runs arbitrary setup commands through a shell. Inno Setup bootstrap occurs only after an explicit user action and confirmation.

The generated uninstall script does not contain `[UninstallDelete]` rules for external application data. Applications remain responsible for defining their own user-data locations and privacy policy.

## Release signing

Rubra Packager includes an optional local Authenticode helper (`scripts/sign_release.ps1`). Signing certificates and private keys are external release secrets and must never be committed. Generated Setup/Portable releases are not part of the source repository.

## v1.0 stable policy

Stable-release validation must not weaken the existing trust gates for npm/pip execution, loopback API token/origin checks, path confinement, or setup prerequisite approval. Windows metadata files are generated from single-line sanitized display values and are passed to PyInstaller as local build inputs.
