# Publishing Rubra Packager

Rubra Packager should be published as a **new repository**, not as a branch of the HTML2EXE repository.

## Before publishing

1. Complete `RP_R4_VALIDATION.md` on Windows and Android.
2. Review `RP_R4_DIFFERENTIATION_AUDIT.md`.
3. Confirm the author name and MPL-2.0 license choice.
4. Remove local environments and generated files.
5. Do not include Arena Rubra source/assets inside the packager repository.

## Create the repository

From the clean Rubra Packager directory:

```cmd
git init
git branch -M main
git add .
git commit -m "Rubra Packager RP-R4 public baseline"
```

With GitHub CLI:

```cmd
gh repo create Rubra-Packager --public --source=. --remote=origin --push
```

Or create an empty repository on GitHub and run:

```cmd
git remote add origin https://github.com/YOUR_ACCOUNT/Rubra-Packager.git
git push -u origin main
```

## First tag

After runtime validation:

```cmd
git tag -a v0.4.0 -m "RP-R4 independent repository foundation"
git push origin v0.4.0
```

Compiled EXE/APK files should be attached to a GitHub Release, not committed to the source tree.

## Suggested repository description

> Profile-driven Windows and Android packager for trusted offline web games and HTML applications.

## Suggested topics

`python`, `pywebview`, `pyinstaller`, `capacitor`, `android`, `html5`, `web-game`, `offline-first`, `packager`
