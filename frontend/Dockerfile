FROM node:20-alpine AS builder

WORKDIR /app

# 复制 package 文件
COPY package*.json ./

# 安装依赖（使用 npm ci 更快更稳定）
RUN npm ci --only=production && npm install typescript

# 复制源码
COPY . .

# 设置 Node 内存限制并构建（跳过类型检查、禁用压缩、减少并发）
ENV NODE_OPTIONS="--max-old-space-size=1024"
ENV VITE_BUILD_CONCURRENCY=1
RUN npx vite build --emptyOutDir --minify false

# 生产环境使用 Nginx
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
