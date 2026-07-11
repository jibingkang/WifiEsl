@echo off
setlocal enabledelayedexpansion
title WifiEsl Deploy v1.1.7

echo.
echo ================================================
echo   WifiEsl Manager - Deploy v1.1.7
echo ================================================
echo.

set "PROJECT_DIR=%~dp0.."
cd /d "%PROJECT_DIR%"

:: Detect Python 3
set "PY="
where py >nul 2>&1 && for /f "tokens=2" %%v in ('py -3 --version 2^>^&1') do if not "%%v"=="" set "PY=py -3"
if "!PY!"=="" where python >nul 2>&1 && for /f "tokens=2" %%v in ('python --version 2^>^&1') do ( echo %%v | findstr "^3\." >nul && set "PY=python" )
if "!PY!"=="" where python3 >nul 2>&1 && set "PY=python3"
if "!PY!"=="" for %%d in ("C:\Python314\python.exe" "C:\Python313\python.exe" "C:\Python312\python.exe" "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" "%LOCALAPPDATA%\Programs\Python\Python312\python.exe") do if exist %%d ( set "PY=%%d" & goto :found_py )
:found_py
if "!PY!"=="" ( echo [ERROR] Python 3 not found! & pause & exit /b 1 )
echo [1/5] Python 3 detected
echo.

:: Check Node
where node >nul 2>&1 || ( echo [ERROR] Node.js not found! & pause & exit /b 1 )
echo [2/5] Node.js OK
echo.

:: Venv
echo [3/5] Setting up venv...
if not exist "venv\Scripts\python.exe" ( !PY! -m venv venv & echo    Created ) else ( echo    Exists )
venv\Scripts\python.exe -m pip install --upgrade pip -q
echo    pip updated
echo.

:: Backend deps
echo [4/5] Installing backend deps...
venv\Scripts\python.exe -m pip install -r backend\requirements.txt
if !errorlevel! neq 0 ( echo [ERROR] Failed! & pause & exit /b 1 )
echo    Installed
echo.

:: Build frontend
echo [5/5] Building frontend...
where nvm >nul 2>&1 && call nvm use 26.5.0 >nul 2>&1
if not exist "frontend\node_modules" ( cd frontend & call npm install & cd .. )
cd frontend
call npm run build
set "BUILD_ERR=!errorlevel!"
cd ..
if !BUILD_ERR! neq 0 ( echo [ERROR] Build failed! & pause & exit /b 1 )
echo    Build complete (frontend\dist\)
echo.

:: Dirs
if not exist "backend\data" mkdir "backend\data"
if not exist "backend\logs" mkdir "backend\logs"

echo ================================================
echo   Deploy Complete!
echo   Run: scripts\start.bat
echo   Login: admin / admin123
echo ================================================
pause
