# Contributing

1. Create a focused branch from `main`.
2. Keep Windows, Android, preflight, Setup and UI changes separated when practical.
3. Add or update automated tests for behavior changes.
4. Run `python scripts/validate_repository.py` and `python run_tests.py`.
5. Run `node --check src/rubra_packager/static/app.js` after UI JavaScript changes.
6. Do not commit generated environments, Portable/Setup builds, APK/AAB files, signing keys, project content or local runtime state.
7. Document user-visible changes in `CHANGELOG.md`.
8. Preserve the explicit trust gates around npm/pip/project-controlled build execution.
