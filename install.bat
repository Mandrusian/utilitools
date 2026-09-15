@echo off
setlocal enabledelayedexpansion

if "%UTILITOOLS_REPO%"=="" set "UTILITOOLS_REPO=https://github.com/Mandrusian/utilitools.git"
if "%UTILITOOLS_DIR%"==""  set "UTILITOOLS_DIR=%USERPROFILE%\utilitools"

echo.
echo   utilitools installer
echo.

REM --- 1. Python ---
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo   * Python not found - trying winget
    where winget >nul 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo   X winget not found.
        echo     Install Python 3 from https://python.org and rerun.
        exit /b 1
    )
    winget install -e --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
    if %ERRORLEVEL% NEQ 0 (
        echo   X Python install failed
        exit /b 1
    )
)
for /f "delims=" %%v in ('python --version 2^>^&1') do echo   . python: %%v

REM --- 2. git ---
where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo   * git not found - trying winget
    where winget >nul 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo   X winget not found. Install Git from https://git-scm.com and rerun.
        exit /b 1
    )
    winget install -e --id Git.Git --silent --accept-package-agreements --accept-source-agreements
)
for /f "delims=" %%v in ('git --version 2^>^&1') do echo   . git: %%v

REM --- 3. clone or pull ---
if exist "%UTILITOOLS_DIR%\.git" (
    echo   * updating %UTILITOOLS_DIR%
    git -C "%UTILITOOLS_DIR%" pull --ff-only
) else (
    echo   * cloning into %UTILITOOLS_DIR%
    git clone "%UTILITOOLS_REPO%" "%UTILITOOLS_DIR%"
    if %ERRORLEVEL% NEQ 0 (
        echo   X clone failed
        exit /b 1
    )
)

REM --- 4. install pyinit ---
if exist "%UTILITOOLS_DIR%\pyinit\install_pyinit.py" (
    echo   * installing pyinit launcher
    python "%UTILITOOLS_DIR%\pyinit\install_pyinit.py"
)

echo.
echo   done
echo.
echo   run:    pyinit
echo.
endlocal
