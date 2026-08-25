@echo off
setlocal EnableExtensions

for %%I in ("%~dp0.") do set "ROOT=%%~fI"
set "APP_HOME=%LOCALAPPDATA%\RubraPackager"
set "RUNTIME=%APP_HOME%\runtime"
set "VENV=%RUNTIME%\.venv"
set "PYTHON=%VENV%\Scripts\python.exe"
set "PIP_CACHE_DIR=%RUNTIME%\pip-cache"
set "EXPECTED_VERSION=1.0.0"
set "NO_PAUSE=0"
set "RELEASE_MODE=0"

:parse_args
if "%~1"=="" goto args_done
if /I "%~1"=="--no-pause" set "NO_PAUSE=1"
if /I "%~1"=="--release" set "RELEASE_MODE=1"
shift
goto parse_args

:args_done

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set PIP_DISABLE_PIP_VERSION_CHECK=1
set PIP_NO_INPUT=1

powershell -NoProfile -Command "$p=[Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent()); if($p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){exit 1}else{exit 0}" >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Do not run Rubra Packager as Administrator.
    echo Close this window and run run_windows.cmd normally.
    goto :error
)

echo.
echo Rubra Packager v1.0.0 source runtime bootstrap
echo Source:    "%ROOT%"
echo Runtime:   "%RUNTIME%"

if not exist "%ROOT%\pyproject.toml" (
    echo ERROR: pyproject.toml was not found.
    goto :error
)
if not exist "%ROOT%\requirements.txt" (
    echo ERROR: requirements.txt was not found.
    goto :error
)

if not exist "%RUNTIME%" mkdir "%RUNTIME%"
if errorlevel 1 goto :error

if exist "%VENV%" if not exist "%PYTHON%" (
    echo Incomplete runtime detected. Recreating it...
    rmdir /s /q "%VENV%" >nul 2>&1
)

if not exist "%PYTHON%" (
    echo Creating the per-user Python runtime...
    where py >nul 2>&1
    if not errorlevel 1 (
        py -3 -m venv "%VENV%"
    ) else (
        where python >nul 2>&1
        if errorlevel 1 (
            echo ERROR: Python 3 was not found in PATH.
            goto :error
        )
        python -m venv "%VENV%"
    )
    if errorlevel 1 goto :error
)

if not exist "%PYTHON%" goto :error

"%PYTHON%" -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)"
if errorlevel 1 (
    echo ERROR: Rubra Packager requires Python 3.11 or newer.
    goto :error
)

echo.
echo Updating packaging tools without using the global pip cache...
"%PYTHON%" -m pip install --no-cache-dir --upgrade pip setuptools wheel
if errorlevel 1 goto :error

echo.
echo Installing Rubra Packager dependencies...
"%PYTHON%" -m pip install --no-cache-dir -r "%ROOT%\requirements.txt"
if errorlevel 1 goto :error

echo.
echo Installing Rubra Packager %EXPECTED_VERSION%...
"%PYTHON%" -m pip install --no-cache-dir --upgrade --force-reinstall --no-deps "%ROOT%"
if errorlevel 1 goto :error

echo.
echo Verifying the installed package...
"%PYTHON%" -c "import rubra_packager, sys; print('Installed Rubra Packager:', rubra_packager.__version__); raise SystemExit(0 if rubra_packager.__version__ == '%EXPECTED_VERSION%' else 1)"
if errorlevel 1 goto :error

if "%RELEASE_MODE%"=="1" (
    echo.
    echo Release bootstrap: automated repository tests are skipped.
) else (
    echo.
    echo Running automated tests...
    "%PYTHON%" "%ROOT%\run_tests.py"
    if errorlevel 1 goto :error
)

"%PYTHON%" -c "from pathlib import Path; import rubra_packager, sys; p=Path(r'%RUNTIME%')/'.rp-installed'; p.write_text(rubra_packager.__version__+'\n'+sys.executable, encoding='utf-8')"
if errorlevel 1 goto :error

echo.
echo Source runtime bootstrap completed successfully.
if "%NO_PAUSE%"=="0" pause
exit /b 0

:error
echo.
echo Source runtime bootstrap failed. Review the error shown above.
echo Source:  "%ROOT%"
echo Runtime: "%RUNTIME%"
if "%NO_PAUSE%"=="0" pause
exit /b 1
