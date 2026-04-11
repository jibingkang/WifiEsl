@echo off
echo 激活Python虚拟环境...
call venv\Scripts\activate.bat
echo 虚拟环境已激活！
echo.
echo 安装依赖请运行: pip install -r requirements.txt
echo 运行PDF解析脚本: python parse_pdf.py
echo.