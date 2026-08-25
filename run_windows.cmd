@echo off
setlocal EnableExtensions

for %%I in ("%~dp0.") do set "ROOT=%%~fI"
set "APP_HOME=%LOCALAPPDATA%\RubraPackager"
set "RUNTIME=%APP_HOME%\runtime"
set "VENV=%RUNTIME%\.venv"
set "PYTHON=%VENV%\Scripts\python.exe"
set "EXPECTED_VERSION=1.0.0"

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set PIP_DISABLE_PIP_VERSION_CHECK=1
set PIP_NO_INPUT=1

powershell -NoProfile -Command "$p=[Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent()); if($p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){exit 1}else{exit 0}" >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Rubra Packager must not be run as Administrator.
    pause
    exit /b 1
)

set "NEEDS_SETUP=0"
if not exist "%PYTHON%" set "NEEDS_SETUP=1"

if "%NEEDS_SETUP%"=="0" (
    "%PYTHON%" -c "import rubra_packager, sys; raise SystemExit(0 if rubra_packager.__version__ == '%EXPECTED_VERSION%' else 1)" >nul 2>&1
    if errorlevel 1 set "NEEDS_SETUP=1"
)

if "%NEEDS_SETUP%"=="1" (
    echo.
    echo Rubra Packager is missing, incomplete, or outdated.
    echo Starting automatic per-user setup...
    if not exist "%ROOT%\bootstrap_source_runtime.cmd" (
        echo ERROR: bootstrap_source_runtime.cmd is missing from this checkout.
        echo Restore the complete v1.0.0 source tree and try again.
        pause
        exit /b 1
    )
    call "%ROOT%\bootstrap_source_runtime.cmd" --no-pause
    if errorlevel 1 (
        echo.
        echo Automatic setup failed.
        echo Run diagnose_windows.cmd and send its complete output.
        pause
        exit /b 1
    )
)

"%PYTHON%" -c "import rubra_packager, sys; raise SystemExit(0 if rubra_packager.__version__ == '%EXPECTED_VERSION%' else 1)" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Rubra Packager was not installed correctly.
    pause
    exit /b 1
)

echo.
echo Starting Rubra Packager %EXPECTED_VERSION%...
"%PYTHON%" -m rubra_packager
set "CODE=%ERRORLEVEL%"

if not "%CODE%"=="0" (
    echo.
    echo Rubra Packager closed with error code %CODE%.
    pause
)
exit /b %CODE%
