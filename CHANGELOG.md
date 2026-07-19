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
  `%LOCALAPPDATA%\RubraPackager\runtime\pip-cache`.
- The global `%LOCALAPPDATA%\pip\Cache` is no longer required.

# RP-R4a — Windows Runtime Self-Repair Hotfix

- Fixed `No module named rubra_packager` after an interrupted first setup.
- `run_windows.cmd` now checks the package import and exact version, not only
  whether a Python executable exists.
- Missing, partial or outdated installations automatically trigger repair.
- The public runtime moved from the source folder to
  `%LOCALAPPDATA%\RubraPackager\runtime`.
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
- Removed Python-to-EXE, project templates, original branding and original UI assets.
- Added MPL-2.0 licensing, provenance, security and contribution documents.
