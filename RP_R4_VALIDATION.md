# RP-R4 validation checklist

RP-R4 is a fresh public implementation and must be runtime-tested even though RP-R3 was previously validated.

## Automated gate

- [x] Python sources compile.
- [x] JavaScript syntax passes `node --check`.
- [x] 32 automated tests pass.
- [x] No `shell=True` in application Python sources.
- [x] No original branding images or original UI filenames.
- [x] No byte-identical source/UI files found against the supplied original snapshot.

## Windows manual gate

- [ ] `setup_windows.cmd` completes from a clean folder.
- [ ] `run_windows.cmd` opens the new navy/gold interface.
- [ ] Legacy project metadata import finds Arena Rubra, or Arena Rubra can be registered manually.
- [ ] Arena Rubra FULL preflight reports 0 errors; optional manifest warning is acceptable.
- [ ] Windows EXE build succeeds.
- [ ] Custom Windows icon is applied.
- [ ] EXE starts and preserves settings/localStorage after closing and reopening.
- [ ] Arena Rubra menu, audio, assets and a short match work.

## Android manual gate

- [ ] JDK, SDK and Node checks pass.
- [ ] Arena Rubra FULL APK build succeeds.
- [ ] Custom adaptive Android icon is applied.
- [ ] APK ZIP integrity passes.
- [ ] Debug signature verifies with `apksigner` when available.
- [ ] APK installs on a real device.
- [ ] Icon, landscape startup, audio, assets, persistence and a short match work.

## Validation rule

Do not replace the validated private RP-R3 baseline until both Windows and Android manual gates are complete. After success, RP-R4 can become the first validated public-repository baseline.
