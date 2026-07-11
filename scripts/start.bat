@echo off
setlocal enabledelayedexpansion
title WifiEsl Server

echo ==========================================
echo   WifiEsl Manager v1.1.7
echo ==========================================
echo.

set "PROJECT_DIR=%~dp0.."
cd /d "%PROJECT_DIR%"

:: ========================================
:: Step 1: Detect Python 3
:: ========================================
echo [1/5] Detecting Python 3...

set "PY="

where py >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%v in ('py -3 --version 2^>^&1') do set "PY_VER=%%v"
    if not "!PY_VER!"=="" set "PY=py -3"
)

if "!PY!"=="" (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        for /f "tokens=2" %%v in ('python --version 2^>^&1') do set "RAW_VER=%%v"
        echo !RAW_VER! | findstr /r "^3\." >nul 2>&1
        if !errorlevel! equ 0 ( set "PY=python" & set "PY_VER=!RAW_VER!" )
    )
)

if "!PY!"=="" ( where python3 >nul 2>&1 && set "PY=python3" )
if "!PY!"=="" (
    for %%d in (
        "C:\Python314\python.exe" "C:\Python313\python.exe" "C:\Python312\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    ) do if exist %%d ( set "PY=%%d" & goto :found_py )
)

:found_py
if "!PY!"=="" (
    echo [ERROR] Python 3.11+ not found! Install: https://www.python.org/
    pause & exit /b 1
)
echo    Found Python, using: !PY!
echo.

:: ========================================
:: Step 2: Venv
:: ========================================
echo [2/5] Setting up venv...

if not exist "venv\Scripts\python.exe" (
    echo    Creating venv...
    !PY! -m venv venv
    if !errorlevel! neq 0 ( echo [ERROR] Failed! & pause & exit /b 1 )
    echo    Created
) else ( echo    Already exists )

for /f "tokens=2" %%v in ('venv\Scripts\python.exe --version 2^>^&1') do set "VENV_VER=%%v"
echo    Venv Python: !VENV_VER!
echo.

:: ========================================
:: Step 3: Dependencies
:: ========================================
echo [3/5] Checking dependencies...

venv\Scripts\python.exe -c "import fastapi" >nul 2>&1
if !errorlevel! neq 0 (
    echo    Installing...
    venv\Scripts\python.exe -m pip install -r backend\requirements.txt
    if !errorlevel! neq 0 ( echo [ERROR] Failed! & pause & exit /b 1 )
    echo    Installed
) else ( echo    OK )
echo.

:: ========================================
:: Step 4: Config
:: ========================================
echo [4/5] Checking config...

if not exist "backend\.env" (
    if exist ".env" ( copy /Y ".env" "backend\.env" >nul & echo    .env copied )
    if not exist "backend\.env" ( echo    [WARNING] backend\.env not found )
) else ( echo    backend\.env OK )

if not exist "backend\data" mkdir "backend\data"
if not exist "backend\logs" mkdir "backend\logs"
echo    Dirs ready
echo.

:: ========================================
:: Step 5: Start
:: ========================================
echo [5/5] Starting server...
echo.
echo   URL:  http://localhost:8001
echo   Login: admin / admin123
echo   Press Ctrl+C to stop
echo ------------------------------------------
echo.

cd backend
..\venv\Scripts\python.exe main.py 2>&1

if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Backend failed! Check backend\.env and backend\logs\
    cd .. & pause & exit /b 1
)
cd .. & pause
