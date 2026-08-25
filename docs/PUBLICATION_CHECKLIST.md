# One-pass GitHub publication checklist

Before committing the final source in GitHub Desktop:

- [ ] `python scripts/validate_repository.py` reports PASS.
- [ ] `python run_tests.py` passes.
- [ ] Rubra Packager starts from `run_windows.cmd`.
- [ ] Prerequisite cards stack vertically when a detected path is long.
- [ ] `build_release_windows.cmd` successfully produces Portable + Setup locally.
- [ ] Portable launches and performs a known packaging build.
- [ ] Setup installs, installed application launches, and uninstall succeeds.
- [ ] GitHub Desktop Changes contains no `release/`, `build/`, `dist/`, EXE, ZIP, wheel, APK/AAB, keystore, runtime, backup or patch payload files.
- [ ] Repository name is `Rubra-Packager`.
- [ ] README images render in GitHub Desktop/GitHub preview.
- [ ] Commit the final source cleanup.
- [ ] Push `main`.
- [ ] Optionally create/tag `v1.0.0` after verifying the pushed tree.

Official compiled binaries remain outside the source repository under the current v1 distribution policy.
