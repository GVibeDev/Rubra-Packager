# Development history

Rubra Packager began as packaging infrastructure for our own application/game builds. The internal workflow proved reliable enough to justify an independent public implementation and a broader packaging UI.

## RP-R4 — independent public foundation

The public codebase was rebuilt around a new `src/` architecture, local-token API, project registry, profile system, deterministic preflight, independent UI and public licensing/provenance documents. Follow-up R4a/R4b/R4c work hardened per-user runtime repair, pip-cache isolation and web reference resolution.

## RP-R5 — Python packaging

Added a separate Python → Windows pipeline with preflight, ONEFILE/ONEDIR output, GUI/console modes, icons, hidden imports, project-confined data/search paths and explicit trust before dependency installation.

## RP-R6 — Setup Builder

Added an independent Inno Setup provider for already-built Windows artifacts, supporting ONEFILE and ONEDIR, stable AppId, install modes, shortcuts, metadata and installer hashing.

## RP-R7 — maintenance lifecycle

Added explicit Inno Setup bootstrap through winget, upgrade/repair conventions, safe uninstall policy and release manifests.

## RP-R8 — release engineering

Added reproducible release assembly, wheel/build smoke tests, checksum finalization and optional code-signing hooks.

## v1 release candidates

RC1 synchronized Windows metadata and formalized the v1 validation matrix. RC2 separated the real frozen RubraPackager.exe desktop core from the private Python/PyInstaller build runtime. RC3 integrated final branding and UI alignment polish; RC3A corrected a test-scope false positive caused by generated third-party release files.

## v1.0.0

The first stable public source release finalizes branding, prerequisite-path layout, source-only GitHub publication policy, clean repository structure and curated user/build documentation.

See `CHANGELOG.md` for detailed technical changes.
