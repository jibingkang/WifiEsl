@echo off
setlocal enabledelapsedexpansion
title Install WifiEsl Service

net session >nul 2>&1
if %errorlevel% neq 0 ( echo [ERROR] Run as Administrator! & pause & exit /b 1 )

echo ================================================
echo   WifiEsl Manager - Install Service
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

if not exist "venv\Scripts\python.exe" !PY! -m venv venv
echo [OK] Venv ready
echo.

:: nssm
set "NSSM="
where nssm >nul 2>&1 && set "NSSM=nssm"
if "!NSSM!"=="" if exist "tools\nssm.exe" set "NSSM=%PROJECT_DIR%\tools\nssm.exe"
if "!NSSM!"=="" (
    echo Downloading nssm...
    if not exist "tools" mkdir "tools"
    powershell -Command "Invoke-WebRequest -Uri 'https://nssm.cc/releases/nssm-2.24.zip' -OutFile 'tools\nssm.zip'" 2>nul
    if exist "tools\nssm.zip" (
        powershell -Command "Expand-Archive -Path 'tools\nssm.zip' -DestinationPath 'tools\nssm_temp' -Force" 2>nul
        copy /Y "tools\nssm_temp\nssm-2.24\win64\nssm.exe" "tools\nssm.exe" >nul
        rmdir /S /Q "tools\nssm_temp" 2>nul & del "tools\nssm.zip" 2>nul
        set "NSSM=%PROJECT_DIR%\tools\nssm.exe"
    ) else ( echo [ERROR] Download failed! & pause & exit /b 1 )
)
echo [OK] nssm ready

:: Service runner
(
echo @echo off
echo cd /d "%PROJECT_DIR%"
echo call venv\Scripts\activate.bat
echo cd backend
echo ..\venv\Scripts\python.exe main.py
) > "%PROJECT_DIR%\backend\service_runner.bat"
echo [OK] Service runner created
echo.

:: Install
!NSSM! stop WifiEslServer >nul 2>&1
!NSSM! remove WifiEslServer confirm >nul 2>&1
!NSSM! install WifiEslServer "%PROJECT_DIR%\backend\service_runner.bat"
if !errorlevel! neq 0 ( echo [ERROR] Install failed! & pause & exit /b 1 )

!NSSM! set WifiEslServer DisplayName "WifiEsl Manager"
!NSSM! set WifiEslServer Description "WifiEsl Manager Backend v1.1.7"
!NSSM! set WifiEslServer Start SERVICE_AUTO_START
!NSSM! set WifiEslServer AppDirectory "%PROJECT_DIR%\backend"
!NSSM! set WifiEslServer AppRestartDelay 3000
!NSSM! set WifiEslServer AppStdout "%PROJECT_DIR%\backend\logs\service_stdout.log"
!NSSM! set WifiEslServer AppStderr "%PROJECT_DIR%\backend\logs\service_stderr.log"

!NSSM! start WifiEslServer

echo.
echo ================================================
echo   Service Installed: WifiEslServer
echo   URL: http://localhost:8001
echo   Login: admin / admin123
echo ================================================
echo.
pause
