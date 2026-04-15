@echo off
chcp 65001 >nul
echo 启动WIFI标签管理系统后端服务...
echo.

cd /d "%~dp0backend"

REM 激活虚拟环境
if exist "..\venv\Scripts\activate.bat" (
    call "..\venv\Scripts\activate.bat"
) else (
    echo 虚拟环境未找到，使用系统Python
)

REM 启动服务
python main.py

pause