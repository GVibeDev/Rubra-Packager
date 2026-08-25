# Rubra Packager — User Guide

Rubra Packager is organized around separate packaging workspaces. Build the application first; use Setup Builder only after you have a Windows artifact to install.

## 1. Projects

Register trusted local web projects here. Rubra Packager stores project metadata, not a private copy of the project source.

For web projects, select a profile and variant. The built-in generic profiles cover common offline/static applications; specialized profiles can define required paths and variant exclusions.

## 2. Web Preflight

Run preflight before Web → Windows or Android packaging. Preflight checks UTF-8 readability, known local references, required profile files and excluded/included content.

Warnings are review items; errors are blocking. Dynamic Blob/Data URLs or runtime-generated names are not guessed.

## 3. Web → Windows

1. Select the registered project.
2. Confirm application name, profile and variant.
3. Enable source build execution only for a trusted project when npm/build steps are needed.
4. Optionally select an icon.
5. Build and test the published EXE.

The Windows output is a one-file PyInstaller executable hosting the local web application through PyWebView.

## 4. Python → Windows

1. Select the Python project folder.
2. Choose or browse to the entry point.
3. Choose ONEFILE or ONEDIR.
4. Choose Windowed or Console mode.
5. Choose dependency setup: None, `requirements.txt`, or install project metadata.
6. Enable the trust checkbox only when you accept that dependency/project installation may execute code.
7. Add hidden imports, data paths or search paths only when required.
8. Run Python preflight.
9. Build and test the artifact.

Additional data and search paths must remain inside the selected project root.

## 5. Setup Builder

Setup Builder does **not** compile source code. Give it an already-built Windows artifact.

### ONEFILE

Artifact: the `.exe` file itself.

### ONEDIR

Artifact: the complete built application directory.

Primary EXE: the executable inside that directory that should be launched by shortcuts.

Example:

```text
MyApplication\
├── MyApplication.exe   <- primary EXE
├── _internal\
└── assets\
```

Use a stable AppId for upgrades of the same application. Changing the AppId makes Windows/Inno treat it as a different product.

If Inno Setup is missing, Rubra Packager can offer an explicit winget bootstrap. It is never installed silently.

## 6. Android

Android packaging requires JDK 17+, Android SDK, Node.js and npm. Register the web project, run preflight, review any source-build trust request, configure package/application metadata and build the APK.

The v1 validation scope is device-oriented APK production. Store-signing/AAB publication should be treated as a separate release workflow.

## 7. Build reports and hashes

Published artifacts include build metadata and SHA-256 where supported. A successful Setup build also writes a release manifest describing the artifact and maintenance policy.

## Trust rules

Treat these operations as code execution, not passive file copying:

```text
npm install
npm run build
pip install -r requirements.txt
pip install .
```

Do not approve them for an untrusted project.
