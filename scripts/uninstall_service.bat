@echo off
setlocal enabledelayedexpansion
title Uninstall WifiEsl Service

net session >nul 2>&1
if %errorlevel% neq 0 ( echo [ERROR] Run as Administrator! & pause & exit /b 1 )

set "PROJECT_DIR=%~dp0.."

set "NSSM="
where nssm >nul 2>&1 && set "NSSM=nssm"
if "!NSSM!"=="" if exist "%PROJECT_DIR%\tools\nssm.exe" set "NSSM=%PROJECT_DIR%\tools\nssm.exe"
if "!NSSM!"=="" (
    sc stop WifiEslServer >nul 2>&1
    sc delete WifiEslServer >nul 2>&1
    echo Service removed via sc
    pause & exit /b
)

echo ================================================
echo   Uninstall WifiEsl Manager Service
echo ================================================
echo.

!NSSM! stop WifiEslServer >nul 2>&1
echo [1/2] Service stopped

!NSSM! remove WifiEslServer confirm >nul 2>&1
echo [2/2] Service removed

echo.
echo   Done
echo.
pause
