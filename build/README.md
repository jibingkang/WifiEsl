# WifiEsl Docker 部署包

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
