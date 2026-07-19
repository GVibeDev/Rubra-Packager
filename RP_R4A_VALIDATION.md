# RP-R4a Validation

## Purpose

Validate the Windows runtime self-repair hotfix without changing RP-R4
packaging features.

## Test procedure

1. Delete or ignore any old `.venv` inside the extracted source folder.
2. Run `run_windows.cmd` as a normal user.
3. Confirm that setup uses `%LOCALAPPDATA%\RubraPackager\runtime`.
4. Confirm the automated tests pass.
5. Confirm the UI opens.
6. Close and reopen `run_windows.cmd`; setup must not repeat.
7. Confirm the project registry is visible.
8. Run one Arena Rubra FULL preflight.
9. Build one Windows EXE or Android APK to verify no packaging regression.

## Expected result

The launcher must never report `No module named rubra_packager`. If the package
is absent or the wrong version is installed, it must repair the runtime before
launching.
