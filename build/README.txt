================================================================
  WifiEsl Manager v1.1.7 - Deployment Guide
================================================================

Windows:
  1. Install Python 3.11+ (https://www.python.org/)
  2. Edit backend\.env with your WIFI credentials
  3. Double-click start.bat
  4. Open http://localhost:8001 (admin / admin123)

  Install as Windows Service:
    Right-click scripts\install_service.bat - Run as Admin

Linux/Docker:
  1. Install Docker + Docker Compose
  2. docker-compose up -d --build
  3. Open http://<server-ip>

Default Login: admin / admin123
================================================================
