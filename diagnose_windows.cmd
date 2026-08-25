@echo off
setlocal EnableExtensions

for %%I in ("%~dp0.") do set "ROOT=%%~fI"
set "APP_HOME=%LOCALAPPDATA%\RubraPackager"
set "RUNTIME=%APP_HOME%\runtime"
set "VENV=%RUNTIME%\.venv"
set "PYTHON=%VENV%\Scripts\python.exe"
set "EXPECTED_VERSION=1.0.0"

echo ============================================================
echo RUBRA PACKAGER v1.0.0 DIAGNOSTIC
echo ============================================================
echo Source root:      "%ROOT%"
echo Current folder:   "%CD%"
echo Runtime folder:   "%RUNTIME%"
echo Runtime Python:   "%PYTHON%"
echo Expected version: %EXPECTED_VERSION%
echo.

powershell -NoProfile -Command "$p=[Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent()); if($p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){Write-Host '[WARNING] Elevated Administrator session'}else{Write-Host '[OK] Standard user session'}"

if exist "%ROOT%\pyproject.toml" (echo [OK] pyproject.toml) else (echo [MISSING] pyproject.toml)
if exist "%ROOT%\requirements.txt" (echo [OK] requirements.txt) else (echo [MISSING] requirements.txt)
if exist "%ROOT%\bootstrap_source_runtime.cmd" (echo [OK] bootstrap_source_runtime.cmd) else (echo [MISSING] bootstrap_source_runtime.cmd)

if exist "%ROOT%\.venv" (
    echo [NOTICE] Legacy source-local .venv found. v1.0.0 does not use it.
) else (
    echo [OK] No legacy source-local .venv
)

if exist "%PYTHON%" (
    echo [OK] per-user runtime Python
    "%PYTHON%" --version
    "%PYTHON%" -m pip --version
    "%PYTHON%" -c "import sys; print('Executable:', sys.executable)"
    "%PYTHON%" -c "import rubra_packager; print('Rubra Packager:', rubra_packager.__version__)"
    "%PYTHON%" -c "import PyInstaller; print('PyInstaller:', PyInstaller.__version__)"
) else (
    echo [MISSING] per-user runtime Python
)

if exist "%RUNTIME%\.rp-installed" (
    echo.
    echo Installation marker:
    type "%RUNTIME%\.rp-installed"
) else (
    echo.
    echo [MISSING] installation marker
)

echo.
echo System tools:
where py 2>nul
where python 2>nul
where node 2>nul
where npm 2>nul
where java 2>nul
where winget 2>nul
where ISCC.exe 2>nul
echo.
echo Android environment:
if defined ANDROID_SDK_ROOT (echo ANDROID_SDK_ROOT=%ANDROID_SDK_ROOT%) else (echo [NOTICE] ANDROID_SDK_ROOT is not set)
if defined ANDROID_HOME (echo ANDROID_HOME=%ANDROID_HOME%) else (echo [NOTICE] ANDROID_HOME is not set)
echo.
echo ============================================================
pause
