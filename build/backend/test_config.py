#!/usr/bin/env python3
"""
测试配置加载
"""
import sys
import os

# 确保项目根目录在路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings

print("=== 当前配置 ===")
print(f"wifi_base_url: {settings.wifi_base_url}")
print(f"wifi_username: {settings.wifi_username}")
print(f"wifi_password: {settings.wifi_password}")
print(f"wifi_apikey: {settings.wifi_apikey} (长度: {len(settings.wifi_apikey)})")
print(f"wifi_apikey[:8]: {settings.wifi_apikey[:8] if settings.wifi_apikey else '空'}")

print("\n=== 环境变量 ===")
print(f"WIFI_BASE_URL: {os.environ.get('WIFI_BASE_URL', '未设置')}")
print(f"WIFI_USERNAME: {os.environ.get('WIFI_USERNAME', '未设置')}")
print(f"WIFI_PASSWORD: {os.environ.get('WIFI_PASSWORD', '未设置')}")
print(f"WIFI_APIKEY: {os.environ.get('WIFI_APIKEY', '未设置')}")

print("\n=== 检查.env文件是否存在 ===")
env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
print(f".env文件路径: {env_file}")
print(f".env文件存在: {os.path.exists(env_file)}")

if os.path.exists(env_file):
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"\n.env文件内容:")
    print(content)