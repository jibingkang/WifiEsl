@echo off
echo ============================================
echo   WIFI标签系统API文档分析项目设置
echo ============================================
echo.

echo 1. 创建虚拟环境...
python -m venv venv
if %errorlevel% neq 0 (
    echo 错误: 创建虚拟环境失败
    pause
    exit /b 1
)
echo 虚拟环境创建成功！
echo.

echo 2. 激活虚拟环境...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo 错误: 激活虚拟环境失败
    pause
    exit /b 1
)
echo 虚拟环境已激活！
echo.

echo 3. 安装依赖包...
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo 错误: 安装依赖包失败
    pause
    exit /b 1
)
echo 依赖包安装成功！
echo.

echo 4. 测试PDF解析库...
python -c "import pdfplumber; print('pdfplumber版本:', pdfplumber.__version__)"
python -c "import pypdf; print('pypdf版本:', pypdf.__version__)"
echo.

echo 5. 运行PDF文档分析...
python parse_pdf.py
echo.

echo ============================================
echo   项目设置完成！
echo ============================================
echo.
echo 后续使用:
echo   1. 激活环境: activate_env.bat
echo   2. 运行分析: python parse_pdf.py
echo   3. 退出环境: deactivate
echo.
pause