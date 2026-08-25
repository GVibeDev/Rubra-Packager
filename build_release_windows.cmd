@echo off
setlocal EnableExtensions

for %%I in ("%~dp0.") do set "ROOT=%%~fI"
set "PYTHON=%LOCALAPPDATA%\RubraPackager\runtime\.venv\Scripts\python.exe"
set "EXPECTED_VERSION=1.0.0"

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set PIP_DISABLE_PIP_VERSION_CHECK=1
set PIP_NO_INPUT=1

powershell -NoProfile -Command "$p=[Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent()); if($p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){exit 1}else{exit 0}" >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Do not build Rubra Packager as Administrator.
    pause
    exit /b 1
)

if not exist "%PYTHON%" (
    echo Private source runtime is missing. Preparing it first...
    call "%ROOT%\bootstrap_source_runtime.cmd" --no-pause
    if errorlevel 1 goto :error
)

"%PYTHON%" -c "import rubra_packager, sys; raise SystemExit(0 if rubra_packager.__version__ == '%EXPECTED_VERSION%' else 1)" >nul 2>&1
if errorlevel 1 (
    echo Source runtime is outdated. Updating it first...
    call "%ROOT%\bootstrap_source_runtime.cmd" --no-pause
    if errorlevel 1 goto :error
)

echo.
echo ============================================================
echo RUBRA PACKAGER %EXPECTED_VERSION% - WINDOWS RELEASE BUILD
echo ============================================================
echo Output: "%ROOT%\release"
echo.

"%PYTHON%" "%ROOT%\scripts\build_release.py" --output "%ROOT%\release" --require-setup
if errorlevel 1 goto :error

echo.
echo Building source wheel...
"%PYTHON%" -m pip wheel --no-build-isolation --no-deps --wheel-dir "%ROOT%\release" "%ROOT%"
if errorlevel 1 goto :error

echo.
echo Finalizing release manifest and SHA-256 checksums...
"%PYTHON%" "%ROOT%\scripts\finalize_release.py" --output "%ROOT%\release"
if errorlevel 1 goto :error

echo.
echo Release build completed.
echo.
echo Expected artifacts:
echo   release\RubraPackager-%EXPECTED_VERSION%-Portable\RubraPackager.exe
echo   release\RubraPackager-%EXPECTED_VERSION%-Portable.zip
echo   release\RubraPackager-%EXPECTED_VERSION%-Setup.exe
echo   release\rubra_packager-%EXPECTED_VERSION%-py3-none-any.whl
echo   release\RubraPackager-%EXPECTED_VERSION%.release.json
echo   release\SHA256SUMS.txt
echo.
pause
exit /b 0

:error
echo.
echo RELEASE BUILD FAILED.
echo Copy the complete error shown above and send it for diagnosis.
pause
exit /b 1
