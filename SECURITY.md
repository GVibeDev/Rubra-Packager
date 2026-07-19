# Security policy

Rubra Packager is a local build tool and processes projects selected by the user.

## Important trust warning

Never enable npm source building for an untrusted project. `npm install` and `npm run build` can execute arbitrary lifecycle and build scripts with the user's permissions.

## Local API

The desktop UI communicates with a loopback-only HTTP server. API requests require a random per-launch token and reject foreign browser origins.

## Sensitive files

Do not commit:

- Android signing keys;
- `local.properties`;
- built APK, AAB or EXE files;
- personal project registries;
- generated Gradle folders;
- `.venv` or `node_modules`.

## Reporting

Open a private security report or contact the repository owner before publishing an exploitable issue.
