"""Generate config files for build package. Called by build_package.bat."""
import os, sys

build_dir = sys.argv[1]
os.makedirs(build_dir, exist_ok=True)

# docker-compose.yml
with open(os.path.join(build_dir, "docker-compose.yml"), "w", encoding="utf-8") as f:
    f.write("""version: '3.3'

services:
  backend:
    build:
      context: ./backend
    container_name: wifiesl-backend
    restart: unless-stopped
    ports: ["8000:8000"]
    volumes:
      - ./backend/data:/app/data
      - ./logs:/app/logs
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./data/wifi_esl.db
      - SECRET_KEY=${SECRET_KEY:-change-this}
      - LOG_LEVEL=INFO
    networks: [wifiesl-network]

  frontend:
    image: nginx:alpine
    container_name: wifiesl-frontend
    restart: unless-stopped
    ports: ["80:80"]
    volumes:
      - ./frontend/dist:/usr/share/nginx/html:ro
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    networks: [wifiesl-network]

networks:
  wifiesl-network:
    driver: bridge
""")

# nginx.conf
with open(os.path.join(build_dir, "nginx.conf"), "w", encoding="utf-8") as f:
    f.write("""server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;
    location / { try_files $uri $uri/ /index.html; }
    location /api/ { proxy_pass http://backend:8000/; }
    location ~* \\.(js|css|png|jpg|ico|svg)$ { expires 1y; }
}
""")

# README.txt
with open(os.path.join(build_dir, "README.txt"), "w", encoding="utf-8") as f:
    f.write("""================================================================
  WifiEsl Manager v1.1.7 - Deployment Guide
================================================================

Windows:
  1. Install Python 3.11+ (https://www.python.org/)
  2. Edit backend\\.env with your WIFI credentials
  3. Double-click start.bat
  4. Open http://localhost:8001 (admin / admin123)

  Install as Windows Service:
    Right-click scripts\\install_service.bat - Run as Admin

Linux/Docker:
  1. Install Docker + Docker Compose
  2. docker-compose up -d --build
  3. Open http://<server-ip>

Default Login: admin / admin123
================================================================
""")

# start.bat (embedded for build package)
with open(os.path.join(build_dir, "start.bat"), "w", encoding="utf-8") as f:
    f.write("""@echo off
setlocal enabledelayedexpansion
title WifiEsl Server

echo ==========================================
echo   WifiEsl Manager v1.1.7
echo ==========================================
echo.

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

set "PY="
where py >nul 2>&1 && for /f "tokens=2" %%v in ('py -3 --version 2^>^&1') do if not "%%v"=="" set "PY=py -3"
if "!PY!"=="" where python >nul 2>&1 && for /f "tokens=2" %%v in ('python --version 2^>^&1') do ( echo %%v | findstr "^3\\." >nul && set "PY=python" )
if "!PY!"=="" where python3 >nul 2>&1 && set "PY=python3"
if "!PY!"=="" ( echo [ERROR] Python 3 not found & pause & exit /b 1 )

if not exist "venv\\Scripts\\python.exe" !PY! -m venv venv
venv\\Scripts\\python.exe -c "import fastapi" >nul 2>&1 || venv\\Scripts\\python.exe -m pip install -r backend\\requirements.txt

if not exist "backend\\data" mkdir "backend\\data"
if not exist "backend\\logs" mkdir "backend\\logs"

echo Starting server on http://localhost:8001
echo Login: admin / admin123
cd backend
..\\venv\\Scripts\\python.exe main.py
pause
""")

print("Config files generated successfully")
