# Publishing policy

## Source repository

`GVibeDev/Rubra-Packager` is the public source repository.

The repository contains:

- application source;
- branding used by the application and release builder;
- automated tests;
- source/bootstrap helpers;
- the scripts required to build Portable and Setup releases;
- documentation and security/provenance notes.

It does **not** contain generated Portable directories, Setup EXEs, APK/AAB files, wheels or local release archives.

## Binary distribution

For v1.0.0, official binary distributions are intentionally kept separate from GitHub source publication and can be distributed through external product channels such as itch.io or other storefront/download platforms.

This is a distribution policy, not a technical restriction: because the source and build tools are public, users can build Rubra Packager themselves.

## GitHub Releases

Automatic GitHub binary-release publication was developed during release engineering but is intentionally not enabled in the final public repository. The source CI remains enabled.

A normal Git tag such as `v1.0.0` is still useful for marking the stable source state. GitHub can provide its standard source archive for the tag without adding compiled application binaries to the repository.

## Maintainer release checklist

1. Run `python scripts/validate_repository.py`.
2. Run the full test suite.
3. Run `build_release_windows.cmd` locally.
4. Test Portable launch and a known build workflow.
5. Test Setup install, installed launch and uninstall.
6. Finalize hashes/manifest when required.
7. Keep generated files outside the Git commit.
8. Commit/push the clean source state.
9. Tag the source version.
10. Publish tested binaries through the chosen external distribution channel.
