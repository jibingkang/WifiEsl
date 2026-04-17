#!/bin/bash
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
