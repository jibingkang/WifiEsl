# WifiEsl 构建包生成脚本
$SOURCE_DIR = Split-Path -Parent $MyInvocation.MyCommand.Definition
$BUILD_DIR = Join-Path $SOURCE_DIR "build"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "WifiEsl 构建包生成脚本" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/6] 清理旧构建目录..."
if (Test-Path $BUILD_DIR) {
    Remove-Item -Recurse -Force $BUILD_DIR
    Write-Host "已清理旧目录"
}

Write-Host "[2/6] 创建构建目录结构..."
New-Item -ItemType Directory -Path $BUILD_DIR | Out-Null
New-Item -ItemType Directory -Path (Join-Path $BUILD_DIR "frontend") | Out-Null
New-Item -ItemType Directory -Path (Join-Path $BUILD_DIR "backend") | Out-Null
New-Item -ItemType Directory -Path (Join-Path $BUILD_DIR "backend\data") | Out-Null

Write-Host "[3/6] 复制前端构建产物..."
$FRONTEND_DIST = Join-Path $SOURCE_DIR "frontend\dist"
if (Test-Path $FRONTEND_DIST) {
    Copy-Item -Recurse $FRONTEND_DIST (Join-Path $BUILD_DIR "frontend\dist")
    Write-Host "前端文件已复制"
} else {
    Write-Host "警告：frontend\dist 不存在，请先构建前端" -ForegroundColor Yellow
}

Write-Host "[4/6] 复制后端代码..."
Copy-Item -Recurse (Join-Path $SOURCE_DIR "backend\*") (Join-Path $BUILD_DIR "backend")
Write-Host "后端代码已复制"

Write-Host "[5/6] 生成部署配置文件..."

# docker-compose.yml
$dockerCompose = @"version: '3.3'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: wifiesl-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./backend/data:/app/data
      - ./logs:/app/logs
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./data/wifi_esl.db
      - SECRET_KEY=`${SECRET_KEY:-change-this-secret-key}
      - ADMIN_USERNAME=`${ADMIN_USERNAME:-admin}
      - ADMIN_PASSWORD=`${ADMIN_PASSWORD:-admin123}
      - WIFI_BASE_URL=`${WIFI_BASE_URL:-}
      - WIFI_API_KEY=`${WIFI_API_KEY:-}
      - LOG_LEVEL=INFO
    networks:
      - wifiesl-network

  frontend:
    image: nginx:alpine
    container_name: wifiesl-frontend
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./frontend/dist:/usr/share/nginx/html:ro
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - backend
    networks:
      - wifiesl-network

networks:
  wifiesl-network:
    driver: bridge
"@
$dockerCompose | Out-File -FilePath (Join-Path $BUILD_DIR "docker-compose.yml") -Encoding UTF8

# nginx.conf
$nginxConf = @"server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # 前端路由支持
    location / {
        try_files `$uri `$uri/ /index.html;
    }

    # API 代理到后端
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Host `$host;
        proxy_set_header X-Real-IP `$remote_addr;
        proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto `$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket 代理到后端
    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade `$http_upgrade;
        proxy_set_header Connection ""upgrade"";
        proxy_set_header Host `$host;
        proxy_set_header X-Real-IP `$remote_addr;
        proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto `$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 静态文件缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$` {
        expires 1y;
        add_header Cache-Control ""public, immutable"";
    }
}
"@
$nginxConf | Out-File -FilePath (Join-Path $BUILD_DIR "nginx.conf") -Encoding UTF8

# deploy.sh
$deploySh = @"#!/bin/bash
set -e

echo ""==========================================""
echo ""WifiEsl 树莓派部署脚本""
echo ""==========================================""
echo """"

SCRIPT_DIR=""`$(cd ""`$(dirname ""`${BASH_SOURCE[0]}"")"" && pwd)""
cd ""`$SCRIPT_DIR""

echo ""[1/4] 检查文件...""
if [ ! -d ""frontend/dist"" ]; then
    echo ""错误：找不到 frontend/dist 目录""
    exit 1
fi

if [ ! -d ""backend"" ]; then
    echo ""错误：找不到 backend 目录""
    exit 1
fi

echo ""[2/4] 创建数据目录...""
mkdir -p backend/data
mkdir -p logs

echo ""[3/4] 检查 .env 文件...""
if [ ! -f "".env"" ]; then
    echo ""警告：.env 不存在，使用默认配置""
    cp .env.example .env 2>/dev/null || echo ""ADMIN_USERNAME=admin"" > .env && echo ""ADMIN_PASSWORD=admin123"" >> .env
fi

echo ""[4/4] 启动 Docker 容器...""
docker-compose down 2>/dev/null || true
docker-compose up -d --build

echo """"
echo ""==========================================""
echo ""部署完成！""
echo ""==========================================""
echo """"
echo ""访问地址：""
echo ""  - 前端：http://`$(hostname -I | awk '{print ""`$1""}')""
echo ""  - 后端API：http://`$(hostname -I | awk '{print ""`$1""}'):8000""
echo """"
echo ""默认账号：admin / admin123""
echo """"
echo ""查看日志：docker-compose logs -f""
"@
$deploySh | Out-File -FilePath (Join-Path $BUILD_DIR "deploy.sh") -Encoding UTF8

# .env.example
$envExample = @"# 管理员账号配置
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# JWT密钥（请修改为随机字符串）
SECRET_KEY=your-secret-key-change-this

# WiFi价签服务器配置（可选）
WIFI_BASE_URL=
WIFI_API_KEY=
"@
$envExample | Out-File -FilePath (Join-Path $BUILD_DIR ".env.example") -Encoding UTF8

# README.md
$readme = @"# WifiEsl Docker 部署包

## 文件说明

- `frontend/dist/` - 前端构建产物
- `backend/` - 后端代码
- `docker-compose.yml` - Docker 编排配置
- `nginx.conf` - Nginx 配置文件
- `deploy.sh` - 一键部署脚本
- `.env.example` - 环境变量示例

## 部署步骤

1. 将整个 `build` 文件夹复制到树莓派
2. 执行 `./deploy.sh`
3. 访问 http://树莓派IP

## 默认账号

- 用户名：admin
- 密码：admin123
"@
$readme | Out-File -FilePath (Join-Path $BUILD_DIR "README.md") -Encoding UTF8

Write-Host "[6/6] 设置完成！"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "构建包已生成：$BUILD_DIR" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "目录结构："
Get-ChildItem $BUILD_DIR | ForEach-Object { Write-Host "  $($_.Name)" }
Write-Host ""
Write-Host "请将整个 build 文件夹复制到树莓派执行部署"
Write-Host ""

Pause
