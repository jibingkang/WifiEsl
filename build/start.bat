@echo off
setlocal enabledelayedexpansion
title WifiEsl Server

echo ==========================================
echo   WifiEsl Manager v1.1.7
echo ==========================================
echo.

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

set "PY="
where py >nul 2>&1 && for /f "tokens=2" %%v in ('py -3 --version 2^>^&1') do if not "%%v"=="" set "PY=py -3"
if "!PY!"=="" where python >nul 2>&1 && for /f "tokens=2" %%v in ('python --version 2^>^&1') do ( echo %%v | findstr "^3\." >nul && set "PY=python" )
if "!PY!"=="" where python3 >nul 2>&1 && set "PY=python3"
if "!PY!"=="" ( echo [ERROR] Python 3 not found & pause & exit /b 1 )

if not exist "venv\Scripts\python.exe" !PY! -m venv venv
venv\Scripts\python.exe -c "import fastapi" >nul 2>&1 || venv\Scripts\python.exe -m pip install -r backend\requirements.txt

if not exist "backend\data" mkdir "backend\data"
if not exist "backend\logs" mkdir "backend\logs"

echo Starting server on http://localhost:8001
echo Login: admin / admin123
cd backend
..\venv\Scripts\python.exe main.py
pause
