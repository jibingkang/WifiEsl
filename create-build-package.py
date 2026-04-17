#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WifiEsl 构建包生成脚本"""

import os
import shutil
import sys

def main():
    source_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(source_dir, "build")

    print("=" * 50)
    print("WifiEsl 构建包生成脚本")
    print("=" * 50)
    print()

    # 1. 清理旧目录
    print("[1/6] 清理旧构建目录...")
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
        print("已清理旧目录")

    # 2. 创建目录结构
    print("[2/6] 创建构建目录结构...")
    os.makedirs(os.path.join(build_dir, "frontend"))
    os.makedirs(os.path.join(build_dir, "backend", "data"))

    # 3. 复制前端构建产物
    print("[3/6] 复制前端构建产物...")
    frontend_dist = os.path.join(source_dir, "frontend", "dist")
    if os.path.exists(frontend_dist):
        shutil.copytree(frontend_dist, os.path.join(build_dir, "frontend", "dist"))
        print("前端文件已复制")
    else:
        print("警告：frontend/dist 不存在，请先构建前端")

    # 4. 复制后端代码
    print("[4/6] 复制后端代码...")
    backend_src = os.path.join(source_dir, "backend")
    backend_dst = os.path.join(build_dir, "backend")
    for item in os.listdir(backend_src):
        if item == "data":
            continue
        src = os.path.join(backend_src, item)
        dst = os.path.join(backend_dst, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
    print("后端代码已复制")

    # 5. 生成部署配置文件
    print("[5/6] 生成部署配置文件...")

    # docker-compose.yml
    docker_compose = '''version: '3.3'

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
      - SECRET_KEY=${SECRET_KEY:-change-this-secret-key}
      - ADMIN_USERNAME=${ADMIN_USERNAME:-admin}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin123}
      - WIFI_BASE_URL=${WIFI_BASE_URL:-}
      - WIFI_API_KEY=${WIFI_API_KEY:-}
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
'''
    with open(os.path.join(build_dir, "docker-compose.yml"), "w", encoding="utf-8") as f:
        f.write(docker_compose)

    # nginx.conf
    nginx_conf = '''server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # 前端路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 代理到后端
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket 代理到后端
    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 静态文件缓存
    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
'''
    with open(os.path.join(build_dir, "nginx.conf"), "w", encoding="utf-8") as f:
        f.write(nginx_conf)

    # deploy.sh
    deploy_sh = '''#!/bin/bash
set -e

echo "=========================================="
echo "WifiEsl 树莓派部署脚本"
echo "=========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[1/4] 检查文件..."
if [ ! -d "frontend/dist" ]; then
    echo "错误：找不到 frontend/dist 目录"
    exit 1
fi

if [ ! -d "backend" ]; then
    echo "错误：找不到 backend 目录"
    exit 1
fi

echo "[2/4] 创建数据目录..."
mkdir -p backend/data
mkdir -p logs

echo "[3/4] 检查 .env 文件..."
if [ ! -f ".env" ]; then
    echo "警告：.env 不存在，使用默认配置"
    cp .env.example .env 2>/dev/null || echo "ADMIN_USERNAME=admin" > .env && echo "ADMIN_PASSWORD=admin123" >> .env
fi

echo "[4/4] 启动 Docker 容器..."
docker-compose down 2>/dev/null || true
docker-compose up -d --build

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "访问地址："
echo "  - 前端：http://$(hostname -I | awk '{print $1}')"
echo "  - 后端API：http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "默认账号：admin / admin123"
echo ""
echo "查看日志：docker-compose logs -f"
'''
    with open(os.path.join(build_dir, "deploy.sh"), "w", encoding="utf-8") as f:
        f.write(deploy_sh)

    # .env.example
    env_example = '''# 管理员账号配置
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# JWT密钥（请修改为随机字符串）
SECRET_KEY=your-secret-key-change-this

# WiFi价签服务器配置（可选）
WIFI_BASE_URL=
WIFI_API_KEY=
'''
    with open(os.path.join(build_dir, ".env.example"), "w", encoding="utf-8") as f:
        f.write(env_example)

    # README.md
    readme = '''# WifiEsl Docker 部署包

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
'''
    with open(os.path.join(build_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme)

    print("[6/6] 设置完成！")

    print()
    print("=" * 50)
    print(f"构建包已生成：{build_dir}")
    print("=" * 50)
    print()
    print("目录结构：")
    for item in os.listdir(build_dir):
        print(f"  {item}")
    print()
    print("请将整个 build 文件夹复制到树莓派执行部署")
    print()

    input("按回车键退出...")

if __name__ == "__main__":
    main()
