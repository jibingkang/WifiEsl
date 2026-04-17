@echo off
chcp 65001 >nul
echo ==========================================
echo WifiEsl 构建包生成脚本
echo ==========================================
echo.

set "SOURCE_DIR=%~dp0"
set "BUILD_DIR=%SOURCE_DIR%build"

echo [1/6] 清理旧构建目录...
if exist "%BUILD_DIR%" (
    rmdir /S /Q "%BUILD_DIR%"
    echo 已清理旧目录
)

echo [2/6] 创建构建目录结构...
mkdir "%BUILD_DIR%"
mkdir "%BUILD_DIR%\frontend"
mkdir "%BUILD_DIR%\backend"
mkdir "%BUILD_DIR%\backend\data"

echo [3/6] 复制前端构建产物...
if exist "%SOURCE_DIR%frontend\dist" (
    xcopy /E /I /Y "%SOURCE_DIR%frontend\dist" "%BUILD_DIR%\frontend\dist" >nul
    echo 前端文件已复制
) else (
    echo 警告: frontend\dist 不存在，请先构建前端
)

echo [4/6] 复制后端代码...
xcopy /E /I /Y "%SOURCE_DIR%backend" "%BUILD_DIR%\backend" >nul
echo 后端代码已复制

echo [5/6] 复制部署配置文件...
(
echo version: '3.3'
echo.
echo services:
echo   backend:
echo     build:
echo       context: ./backend
echo       dockerfile: Dockerfile
echo     container_name: wifiesl-backend
echo     restart: unless-stopped
echo     ports:
echo       - "8000:8000"
echo     volumes:
echo       - ./backend/data:/app/data
echo       - ./logs:/app/logs
echo     environment:
echo       - DATABASE_URL=sqlite+aiosqlite:///./data/wifi_esl.db
echo       - SECRET_KEY=${SECRET_KEY:-change-this-secret-key}
echo       - ADMIN_USERNAME=${ADMIN_USERNAME:-admin}
echo       - ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin123}
echo       - WIFI_BASE_URL=${WIFI_BASE_URL:-}
echo       - WIFI_API_KEY=${WIFI_API_KEY:-}
echo       - LOG_LEVEL=INFO
echo     networks:
echo       - wifiesl-network
echo.
echo   frontend:
echo     image: nginx:alpine
echo     container_name: wifiesl-frontend
echo     restart: unless-stopped
echo     ports:
echo       - "80:80"
echo     volumes:
echo       - ./frontend/dist:/usr/share/nginx/html:ro
echo       - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
echo     depends_on:
echo       - backend
echo     networks:
echo       - wifiesl-network
echo.
echo networks:
echo   wifiesl-network:
echo     driver: bridge
) > "%BUILD_DIR%\docker-compose.yml"

echo.
echo.
(
echo server {
echo     listen 80;
echo     server_name localhost;
echo     root /usr/share/nginx/html;
echo     index index.html;
echo.
echo     # 前端路由支持
echo     location / {
echo         try_files $uri $uri/ /index.html;
echo     }
echo.
echo     # API 代理到后端
echo     location /api/ {
echo         proxy_pass http://backend:8000/;
echo         proxy_http_version 1.1;
echo         proxy_set_header Host $host;
echo         proxy_set_header X-Real-IP $remote_addr;
echo         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
echo         proxy_set_header X-Forwarded-Proto $scheme;
echo         proxy_connect_timeout 60s;
echo         proxy_send_timeout 60s;
echo         proxy_read_timeout 60s;
echo     }
echo.
echo     # 静态文件缓存
echo     location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
echo         expires 1y;
echo         add_header Cache-Control "public, immutable";
echo     }
echo }
) > "%BUILD_DIR%\nginx.conf"

echo.
echo.
(
echo #!/bin/bash
echo set -e
echo.
echo echo "=========================================="
echo echo "WifiEsl 树莓派部署脚本"
echo echo "=========================================="
echo echo ""
echo.
echo SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" ^&^& pwd)"
echo cd "$SCRIPT_DIR"
echo.
echo echo "[1/4] 检查文件..."
echo if [ ! -d "frontend/dist" ]; then
echo     echo "错误：找不到 frontend/dist 目录"
echo     exit 1
echo fi
echo.
echo if [ ! -d "backend" ]; then
echo     echo "错误：找不到 backend 目录"
echo     exit 1
echo fi
echo.
echo echo "[2/4] 创建数据目录..."
echo mkdir -p backend/data
echo mkdir -p logs
echo.
echo echo "[3/4] 检查 .env 文件..."
echo if [ ! -f ".env" ]; then
echo     echo "警告：.env 不存在，使用默认配置"
echo     cp .env.example .env 2^>/dev/null ^|^| echo "ADMIN_USERNAME=admin" ^> .env ^&^& echo "ADMIN_PASSWORD=admin123" ^>^> .env
echo fi
echo.
echo echo "[4/4] 启动 Docker 容器..."
echo docker-compose down 2^>/dev/null ^|^| true
echo docker-compose up -d --build
echo.
echo echo ""
echo echo "=========================================="
echo echo "部署完成！"
echo echo "=========================================="
echo echo ""
echo echo "访问地址："
echo echo "  - 前端：http://$(hostname -I ^| awk '{print $1}')"
echo echo "  - 后端API：http://$(hostname -I ^| awk '{print $1}'):8000"
echo echo ""
echo echo "默认账号：admin / admin123"
echo echo ""
echo echo "查看日志：docker-compose logs -f"
) > "%BUILD_DIR%\deploy.sh"

echo.
echo.
(
echo # 管理员账号配置
echo ADMIN_USERNAME=admin
echo ADMIN_PASSWORD=admin123
echo.
echo # JWT密钥（请修改为随机字符串）
echo SECRET_KEY=your-secret-key-change-this
echo.
echo # WiFi价签服务器配置（可选）
echo WIFI_BASE_URL=
echo WIFI_API_KEY=
) > "%BUILD_DIR%\.env.example"

echo.
echo.
(
echo # WifiEsl Docker 部署包
echo.
echo ## 文件说明
echo.
echo - `frontend/dist/` - 前端构建产物
echo - `backend/` - 后端代码
echo - `docker-compose.yml` - Docker 编排配置
echo - `nginx.conf` - Nginx 配置文件
echo - `deploy.sh` - 一键部署脚本
echo - `.env.example` - 环境变量示例
echo.
echo ## 部署步骤
echo.
echo 1. 将整个 `build` 文件夹复制到树莓派
echo 2. 执行 `./deploy.sh`
echo 3. 访问 http://树莓派IP
echo.
echo ## 默认账号
echo.
echo - 用户名：admin
echo - 密码：admin123
) > "%BUILD_DIR%\README.md"

echo [6/6] 设置脚本权限...
echo 完成！

echo.
echo ==========================================
echo 构建包已生成：%BUILD_DIR%
echo ==========================================
echo.
echo 目录结构：
dir /B "%BUILD_DIR%"
echo.
echo 请将整个 build 文件夹复制到树莓派执行部署
echo.
pause
