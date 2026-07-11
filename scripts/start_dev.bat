@echo off
setlocal enabledelayedexpansion
title WifiEsl Dev Mode

echo ============================================
echo   WifiEsl Manager - Dev Mode v1.1.7
echo ============================================
echo.

set "PROJECT_DIR=%~dp0.."
cd /d "%PROJECT_DIR%"

:: ========================================
:: Detect Python 3
:: ========================================
set "PY="
where py >nul 2>&1 && for /f "tokens=2" %%v in ('py -3 --version 2^>^&1') do if not "%%v"=="" set "PY=py -3"
if "!PY!"=="" where python >nul 2>&1 && for /f "tokens=2" %%v in ('python --version 2^>^&1') do ( echo %%v | findstr "^3\." >nul && set "PY=python" )
if "!PY!"=="" where python3 >nul 2>&1 && set "PY=python3"
if "!PY!"=="" for %%d in ("C:\Python314\python.exe" "C:\Python313\python.exe" "C:\Python312\python.exe" "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" "%LOCALAPPDATA%\Programs\Python\Python312\python.exe") do if exist %%d ( set "PY=%%d" & goto :found )
:found
if "!PY!"=="" ( echo [ERROR] Python 3 not found! & pause & exit /b 1 )
echo    Python OK
echo.

:: ========================================
:: Ensure venv exists
:: ========================================
if not exist "venv\Scripts\python.exe" (
    echo    Creating venv...
    !PY! -m venv venv
    if !errorlevel! neq 0 ( echo [ERROR] Venv failed! & pause & exit /b 1 )
    echo    Venv created
) else (
    echo    Venv ready
)
echo.

:: ========================================
:: Start backend (new window)
:: ========================================
echo [1/2] Starting backend on port 8001...
start "WifiEsl-Backend" cmd /k "cd /d %PROJECT_DIR% && call venv\Scripts\activate.bat && cd backend && ..\venv\Scripts\python.exe main.py"
echo    Waiting for backend...
timeout /t 5 /nobreak >nul

:: ========================================
:: Start frontend (new window)
:: ========================================
echo [2/2] Starting frontend on port 3000...
where nvm >nul 2>&1
if %errorlevel% equ 0 (
    start "WifiEsl-Frontend" cmd /k "cd /d %PROJECT_DIR%\frontend && call nvm use 26.5.0 && npm run dev"
) else (
    start "WifiEsl-Frontend" cmd /k "cd /d %PROJECT_DIR%\frontend && npm run dev"
)

echo.
echo ============================================
echo   All services started!
echo.
echo   Frontend : http://localhost:3000
echo   Backend  : http://localhost:8001
echo   API Docs : http://localhost:8001/docs
echo.
echo   Close the two new windows to stop
echo ============================================
echo.
pause
