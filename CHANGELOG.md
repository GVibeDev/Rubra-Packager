# v1.0.0 — First stable public source release

- Finalized the validated RC2/RC3 frozen desktop + private build-runtime architecture.
- Added automatic vertical stacking for prerequisite cards when detected tool paths are long.
- Finalized approved icon/logo/banner integration across the UI, Portable build and Setup build.
- Renamed the source-environment helper from `setup_windows.cmd` to `bootstrap_source_runtime.cmd` to distinguish it from generated product installers.
- Kept `build_release_windows.cmd` as the one-command Portable + Setup release builder; it reuses the bootstrap helper instead of duplicating environment setup.
- Removed automatic GitHub binary-release publication from the public v1 repository while retaining source CI and local release tooling.
- Rebuilt `.gitignore` for release/build/runtime/signing/backup artifacts.
- Reorganized public documentation into a concise README plus user, build, publishing and development-history guides.
- Removed internal milestone manifests, patch notes and validation scratch files from the stable public source tree; the technical history remains in this changelog.

# v1.0.0 — Branding & UI Polish

- Integrated the approved Rubra Packager 256×256 Windows ICO into self-binary and Setup builds.
- Added the approved sidebar mark, wide logo and banner to the packaged local UI.
- Extended the explicit local static-file allowlist for the three branding PNGs.
- Corrected paired-field vertical alignment and reduced form-grid crowding.
- Made prerequisite and summary grids responsive.
- Kept the RC2 frozen-binary/private-build-runtime architecture unchanged.
- GitHub automatic Release publication remains deferred / not required.

# v1.0.0rc2 — Self Binary & Build Runtime Separation

- Added a real Rubra Packager PyInstaller ONEDIR self-build producing `RubraPackager.exe`.
- Separated the frozen desktop executable from the private Python/PyInstaller build engine.
- Web → EXE and Python → Windows now resolve the build engine through `runtime_engine.py` rather than `sys.executable`.
- Added `--prepare-runtime` and `--runtime-status` maintenance commands to the application executable.
- Release Setup now installs the ONEDIR binary directly and shortcuts point to `RubraPackager.exe`.
- Release output now includes a Portable directory/ZIP instead of the old source Bootstrap ZIP.
- Added automatic branding hook for `assets/branding/rubra-packager.ico`.
- Added RC2 self-binary/runtime-separation tests and a simplified manual validation checklist.

# v1.0.0rc1 — Release Candidate 1

- Froze the v1 feature set after the validated RP-R8 baseline.
- Added deterministic Windows PE version resources to Web → EXE and Python → EXE builds.
- Web EXEs inherit project version, author/publisher and description metadata.
- Python → Windows now exposes version, publisher and description fields.
- Setup release manifests now use the package `__version__` instead of a hard-coded generator version.
- Expanded `diagnose_windows.cmd` with winget, Inno Setup and Android environment reporting.
- Updated About/UI copy for the v1.0 release candidate.
- Added a local release-candidate repository gate and permanent validation matrix.
- GitHub automatic publication remains implemented but deferred as a manual validation requirement.

# RP-R8 — Release Engineering Foundation

- Added Windows GitHub Actions CI on Python 3.11 and 3.13.
- Added tag-driven release workflow with version/tag synchronization gate.
- Added Rubra Packager self-release builder producing a Setup EXE and bootstrap ZIP.
- Added final release manifest and SHA256SUMS generation after optional signing.
- Added an optional Authenticode hook driven only by GitHub secrets; unsigned development releases remain supported.
- Added `rubra-packager-gui` GUI entry point for installed Python runtimes.
- Added `--release` bootstrap mode to skip repository tests in end-user installations while retaining package/version verification.
- Self-uninstall removes only the private Rubra Packager runtime and preserves project registry/reports.

# RP-R7 — Self-Installing Setup & Maintenance

- RP-R6 Windows Setup Builder Foundation validated as previous baseline.
- Added explicit Inno Setup bootstrap through winget (`JRSoftware.InnoSetup`).
- Added user/machine bootstrap scope selection and immediate ISCC rediscovery.
- Added optional `INNO_SETUP_PATH` discovery override.
- Added explicit upgrade/repair directives to generated Inno scripts while preserving the stable AppId model.
- Generated installers do not add destructive external-user-data uninstall rules.
- Added a `.release.json` manifest beside each successful setup with SHA-256 and maintenance metadata.
- Added UI guidance for bootstrap, upgrade, repair and uninstall lifecycle.

# RP-R6 — Windows Setup Builder Foundation

- RP-R5 Python Application Packaging Foundation validated as previous baseline.
- Added a dedicated Setup Builder workspace; Web → EXE and Python → EXE remain independent producers.
- Added Inno Setup discovery and deterministic `.iss` generation.
- Added ONEFILE and ONEDIR installer inputs.
- Added stable AppId, app version, publisher, per-user/per-machine mode and install-folder configuration.
- Added Start Menu/Desktop shortcuts, uninstaller metadata and optional post-install launch.
- Added optional installer icon, license file and release notes.
- Added setup SHA-256 and generated-script path to build reports.
- Inno compiler execution uses argument lists with `shell=False` through the shared process runner.
- Automatic/bootstrap installation of Inno Setup remains reserved for RP-R7.

# RP-R5 — Python Application Packaging Foundation

- Added a dedicated Python → Windows workspace.
- Added `python_preflight.py` with entry-point, UTF-8, syntax, dependency metadata,
  hidden-import, data-path and search-path validation.
- Added `build_python.py` with PyInstaller ONEFILE/ONEDIR and GUI/console modes.
- Added custom Windows icons to Python builds.
- Added isolated dependency staging with `pip --target` for `requirements.txt`
  or project metadata installs.
- Dependency/package build execution requires an explicit trust checkbox.
- Added Python project inspection and entry-point selection endpoints.
- Added SHA-256 and build metadata to Python artifacts.
- Existing Web → Windows and Web → Android pipelines remain separate.

# RP-R4c — Reference Resolver & Preflight Accuracy Hotfix

- Replaced the generic `from`/`import` expression with syntax-specific scanners
  for HTML, CSS and JavaScript modules.
- `Array.from(...)`, ordinary data strings, Blob URLs, template literals and
  destructuring values are no longer interpreted as files.
- JSON, XML, SVG, TXT, Markdown and CSV remain UTF-8 checked but are not treated
  as executable dependency graphs.
- `tests/`, `docs/`, `node_modules/` and `.git/` do not block runtime preflight.
- Added correct resolution for root-relative document paths, extensionless
  JavaScript imports and directory `index.js` imports.
- Added support for static `new URL("...", import.meta.url)` assets.
- Duplicate findings are collapsed.
- Dynamic asset tables remain the responsibility of the optional asset manifest.

# RP-R4b — Pip Cache Permission Hotfix

- Fixed dependency installation failures caused by unreadable files in the
  global pip cache after an elevated Windows run.
- Public setup now runs every pip installation with `--no-cache-dir`.
- Added an isolated runtime cache path under
  `%LOCALAPPDATA%\\RubraPackager\\runtime\\pip-cache`.
- The global `%LOCALAPPDATA%\\pip\\Cache` is no longer required.

# RP-R4a — Windows Runtime Self-Repair Hotfix

- Fixed `No module named rubra_packager` after an interrupted first setup.
- `run_windows.cmd` now checks the package import and exact version, not only
  whether a Python executable exists.
- Missing, partial or outdated installations automatically trigger repair.
- The public runtime moved from the source folder to
  `%LOCALAPPDATA%\\RubraPackager\\runtime`.
- Public setup now installs a normal package copy instead of editable mode.
- Administrator execution is rejected to avoid creating the runtime under the
  wrong Windows profile.
- `diagnose_windows.cmd` now reports elevation, runtime paths, package version
  and legacy source-local environments.

# Changelog

## RP-R4 — Independent Repository Foundation

- Rebuilt the public repository with an independent `src/` architecture.
- Replaced the inherited interface with a new navy-and-gold workspace.
- Added a Rubra Packager project registry under the application data directory.
- Added read-only migration of legacy HTML2EXE project metadata.
- Added profile-driven FULL/LITE staging and preflight.
- Added Windows EXE packaging with custom ICO generation.
- Added Android debug APK packaging with adaptive launcher icons.
- Added APK ZIP integrity, SHA-256 and optional `apksigner` verification.
- Removed the inherited prototype Python-to-EXE implementation together with
  the original branding and UI; RP-R5 reintroduces Python packaging as an
  independent Rubra Packager module.
- Added MPL-2.0 licensing, provenance, security and contribution documents.
