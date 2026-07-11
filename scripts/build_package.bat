@echo off
setlocal enabledelayedexpansion
title WifiEsl Build Package

echo ==========================================
echo   WifiEsl - Build Package
echo ==========================================
echo.

set "PROJECT_DIR=%~dp0.."
cd /d "%PROJECT_DIR%"

set "BUILD_DIR=%PROJECT_DIR%\build"

echo [1/7] Cleaning old build...
if exist "%BUILD_DIR%" rmdir /S /Q "%BUILD_DIR%"

echo [2/7] Creating dirs...
mkdir "%BUILD_DIR%\frontend" 2>nul
mkdir "%BUILD_DIR%\backend" 2>nul
mkdir "%BUILD_DIR%\backend\data" 2>nul
mkdir "%BUILD_DIR%\backend\logs" 2>nul
mkdir "%BUILD_DIR%\scripts" 2>nul

echo [3/7] Building frontend...
where node >nul 2>&1 || ( echo [ERROR] Node.js not found! Install Node.js 20+ & goto :error )
where nvm >nul 2>&1 && ( call nvm use 26.5.0 >nul 2>&1 )
if not exist "frontend\node_modules" (
    echo    Installing frontend deps...
    cd frontend & call npm install & cd ..
)
echo    Running npm run build...
cd frontend
call npm run build
set "BUILD_ERR=!errorlevel!"
cd ..
if !BUILD_ERR! neq 0 ( echo [ERROR] Frontend build failed! & goto :error )
echo    Build complete

echo [4/7] Copying frontend dist...
xcopy /E /I /Y "frontend\dist" "%BUILD_DIR%\frontend\dist" >nul

echo [5/7] Copying backend...
xcopy /E /I /Y "backend" "%BUILD_DIR%\backend" >nul

echo [6/7] Copying scripts...
xcopy /E /I /Y "scripts\stop.bat" "%BUILD_DIR%\scripts\" >nul
xcopy /E /I /Y "scripts\install_service.bat" "%BUILD_DIR%\scripts\" >nul
xcopy /E /I /Y "scripts\uninstall_service.bat" "%BUILD_DIR%\scripts\" >nul
xcopy /E /I /Y "scripts\deploy.bat" "%BUILD_DIR%\scripts\" >nul
xcopy /E /I /Y "scripts\README.md" "%BUILD_DIR%\scripts\" >nul

echo [7/7] Generating configs...
venv\Scripts\python.exe scripts\_gen_build_files.py "%BUILD_DIR%"
if !errorlevel! neq 0 ( echo [ERROR] Config generation failed! & goto :error )

echo.
echo ==========================================
echo   Build SUCCESS: %BUILD_DIR%
echo ==========================================
dir /B "%BUILD_DIR%"
echo.
echo   Copy "build" folder to deploy
echo.
goto :end

:error
echo.
echo ==========================================
echo   Build FAILED! See error above.
echo ==========================================

:end
echo.
echo   Press any key to close...
pause >nul

