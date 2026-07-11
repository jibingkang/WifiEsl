# WifiEsl Docker 部署文档

## 快速开始（3步部署）

### 第 1 步：准备服务器

```bash
# 安装 Docker 和 Docker Compose
curl -fsSL https://get.docker.com | sh

# 验证安装
docker --version
docker compose version
```

### 第 2 步：下载代码

```bash
# 克隆代码
git clone https://github.com/yourusername/WifiEsl.git
cd WifiEsl

# 复制环境变量配置
cp .env.example .env

# 编辑 .env 文件，修改配置
vim .env
```

### 第 3 步：启动服务

```bash
# 一键启动
docker compose up -d

# 查看状态
docker compose ps

# 查看日志
docker compose logs -f
```

访问 `http://服务器IP` 即可使用。

---

## 详细部署指南

### 1. 服务器要求

| 配置 | 最低要求 |
|------|---------|
| CPU | 2核 |
| 内存 | 4GB |
| 磁盘 | 20GB |
| 系统 | Ubuntu 22.04 / CentOS 8 |

### 2. 安装 Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# 验证
docker --version
docker compose version
```

### 3. 部署配置

#### 3.1 下载代码

```bash
git clone https://github.com/yourusername/WifiEsl.git
cd WifiEsl
```

#### 3.2 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置
nano .env
```

**必须修改的配置项：**

```env
# JWT 密钥（用于加密，必须修改）
SECRET_KEY=your-random-secret-key-here

# 管理员密码
ADMIN_PASSWORD=your-admin-password

# WIFI 系统连接信息
WIFI_BASE_URL=http://your-wifi-ip:8080
WIFI_API_KEY=your-wifi-api-key
```

### 4. 启动服务

```bash
# 构建并启动
docker compose up -d --build

# 查看运行状态
docker compose ps

# 查看日志
docker compose logs -f backend
docker compose logs -f frontend
```

### 5. 访问应用

- **前端页面**: `http://服务器IP`
- **API 文档**: `http://服务器IP/api/docs`

---

## 常用命令

```bash
# 启动服务
docker compose up -d

# 停止服务
docker compose down

# 重启服务
docker compose restart

# 查看日志
docker compose logs -f

# 查看后端日志
docker compose logs -f backend

# 查看前端日志
docker compose logs -f frontend

# 进入后端容器
docker compose exec backend bash

# 进入前端容器
docker compose exec frontend sh

# 更新代码后重建
docker compose up -d --build

# 清理无用镜像
docker system prune -a
```

---

## 数据备份

### 自动备份脚本

```bash
# 创建备份脚本
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups"
mkdir -p $BACKUP_DIR

# 备份数据库
docker compose cp backend:/app/data/wifi_esl.db $BACKUP_DIR/wifi_esl_$DATE.db

# 保留最近 30 天备份
find $BACKUP_DIR -name "*.db" -mtime +30 -delete

echo "备份完成: $BACKUP_DIR/wifi_esl_$DATE.db"
EOF

chmod +x backup.sh

# 添加到定时任务（每天凌晨 2 点）
(crontab -l 2>/dev/null; echo "0 2 * * * cd $(pwd) && ./backup.sh >> backup.log 2>&1") | crontab -
```

### 手动备份

```bash
# 备份数据库
docker compose cp backend:/app/data/wifi_esl.db ./backup_$(date +%Y%m%d).db
```

### 恢复数据

```bash
# 停止服务
docker compose down

# 恢复数据库
docker compose cp ./backup_xxx.db backend:/app/data/wifi_esl.db

# 启动服务
docker compose up -d
```

---

## 更新部署

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 重新构建并启动
docker compose up -d --build

# 3. 查看状态
docker compose ps
```

---

## HTTPS 配置（SSL）

### 方式一：使用 Nginx Proxy Manager（推荐）

```yaml
# docker-compose.yml 添加
services:
  npm:
    image: jc21/nginx-proxy-manager:latest
    container_name: npm
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      - "81:81"  # 管理界面
    volumes:
      - ./npm-data:/data
      - ./npm-letsencrypt:/etc/letsencrypt
    networks:
      - wifiesl-network

networks:
  wifiesl-network:
    external: true
```

然后访问 `http://服务器IP:81` 配置 SSL。

### 方式二：使用 Certbot

```bash
# 安装 Certbot
docker run -it --rm \
  -v ./certbot-data:/etc/letsencrypt \
  -v ./frontend/dist:/data/letsencrypt \
  certbot/certbot certonly \
  --webroot -w /data/letsencrypt \
  -d your-domain.com
```

---

## 故障排查

### 1. 容器无法启动

```bash
# 查看详细日志
docker compose logs backend
docker compose logs frontend

# 检查端口占用
netstat -tlnp | grep -E '80|8000'
```

### 2. 数据库问题

```bash
# 进入后端容器检查
docker compose exec backend bash
ls -la /app/data/
```

### 3. 网络问题

```bash
# 检查容器网络
docker network ls
docker network inspect wifiesl-network

# 测试后端连通性
docker compose exec frontend wget -O- http://backend:8000/api/v1/health
```

### 4. 清理重建

```bash
# 完全清理（会删除数据！）
docker compose down -v
docker system prune -a

# 重新部署
docker compose up -d --build
```

---

## 生产环境优化

### 1. 使用外部数据库（可选）

```yaml
# docker-compose.yml 添加 PostgreSQL
services:
  db:
    image: postgres:15-alpine
    container_name: wifiesl-db
    restart: unless-stopped
    environment:
      POSTGRES_USER: wifiesl
      POSTGRES_PASSWORD: your-db-password
      POSTGRES_DB: wifiesl
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - wifiesl-network

volumes:
  postgres_data:
```

### 2. 配置资源限制

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### 3. 健康检查

```yaml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## 目录结构

```
WifiEsl/
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── ...
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── ...
├── docker-compose.yml      # Docker Compose 配置
├── .env.example            # 环境变量示例
├── .env                    # 实际环境变量（不提交到 Git）
├── backups/                # 备份目录
└── logs/                   # 日志目录
```

---

## 安全建议

1. **修改默认密钥**: 务必修改 `SECRET_KEY`
2. **强密码**: 使用复杂的管理员密码
3. **防火墙**: 只开放 80/443 端口
4. **定期备份**: 配置自动备份脚本
5. **更新镜像**: 定期更新基础镜像

---

**部署完成！** 🎉

如有问题，查看日志：`docker compose logs -f`
