@echo off
setlocal EnableExtensions

for %%I in ("%~dp0.") do set "ROOT=%%~fI"
set "APP_HOME=%LOCALAPPDATA%\RubraPackager"
set "RUNTIME=%APP_HOME%\runtime"
set "VENV=%RUNTIME%\.venv"
set "PYTHON=%VENV%\Scripts\python.exe"
set "PIP_CACHE_DIR=%RUNTIME%\pip-cache"
set "EXPECTED_VERSION=0.4.3"

echo ============================================================
echo RUBRA PACKAGER RP-R4c DIAGNOSTIC
echo ============================================================
echo Source root:       "%ROOT%"
echo Current folder:    "%CD%"
echo Runtime folder:    "%RUNTIME%"
echo Runtime Python:    "%PYTHON%"
echo Private pip cache: "%PIP_CACHE_DIR%"
echo Expected version:  %EXPECTED_VERSION%
echo.

powershell -NoProfile -Command "$p=[Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent()); if($p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){Write-Host '[WARNING] Elevated Administrator session'}else{Write-Host '[OK] Standard user session'}"

if exist "%ROOT%\pyproject.toml" (echo [OK] pyproject.toml) else (echo [MISSING] pyproject.toml)
if exist "%ROOT%\requirements.txt" (echo [OK] requirements.txt) else (echo [MISSING] requirements.txt)

if exist "%ROOT%\.venv" (
    echo [NOTICE] Legacy source-local .venv found. RP-R4c does not use it.
) else (
    echo [OK] No legacy source-local .venv
)

if exist "%PIP_CACHE_DIR%" (echo [OK] private pip cache directory) else (echo [MISSING] private pip cache directory)

if exist "%PYTHON%" (
    echo [OK] per-user runtime Python
    "%PYTHON%" --version
    "%PYTHON%" -m pip --version
    "%PYTHON%" -c "import sys; print('Executable:', sys.executable)"
    "%PYTHON%" -c "import rubra_packager; print('Rubra Packager:', rubra_packager.__version__)"
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
echo Global pip cache reported by pip:
if exist "%PYTHON%" (
    "%PYTHON%" -m pip cache dir 2>nul
) else (
    py -3 -m pip cache dir 2>nul
)

echo.
echo ============================================================
pause
