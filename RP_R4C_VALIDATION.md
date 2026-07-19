# RP-R4c Validation

## Target regression

Arena Rubra report `ARF9O3-arena-rubra-full.json` produced 32 false blocking
`REFERENCE_MISSING` findings under RP-R4b.

## Procedure

1. Extract RP-R4c to a new folder.
2. Run `run_windows.cmd` normally.
3. Confirm automatic update to Rubra Packager 0.4.3.
4. Select the same Arena Rubra source folder and profile `Arena Rubra / FULL`.
5. Run preflight.
6. Expected result: 0 reference errors and only the optional
   `MANIFEST_NOT_FOUND` warning, unless the project has changed.
7. Build and test one EXE.
8. Build, install and smoke-test one APK with its custom icon.

## Acceptance

The preflight must still block a real missing HTML/CSS file or a real missing
local JavaScript module while allowing Arena Rubra's dynamic asset resolver,
Blob downloads and test fixtures.
