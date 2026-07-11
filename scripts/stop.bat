@echo off
title Stop WifiEsl

echo ==========================================
echo   Stop WifiEsl Manager Services
echo ==========================================
echo.

echo [Stop] Backend + Frontend windows...
taskkill /fi "WINDOWTITLE eq WifiEsl*" /f >nul 2>&1

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8001.*LISTENING" 2^>nul') do (
    echo [Stop] Port 8001 PID %%a
    taskkill /pid %%a /f >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000.*LISTENING" 2^>nul') do (
    echo [Stop] Port 3000 PID %%a
    taskkill /pid %%a /f >nul 2>&1
)

echo   Done
echo.
pause
