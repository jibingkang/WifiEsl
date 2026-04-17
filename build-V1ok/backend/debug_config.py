#!/usr/bin/env python3
"""
调试配置问题
"""
import os
import sys

# 直接添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

print(f"当前目录: {current_dir}")
print(f"父目录: {parent_dir}")

try:
    from config import settings
    print("\n[OK] 配置加载成功!")
    print(f"wifi_base_url: {settings.wifi_base_url}")
    print(f"wifi_username: {settings.wifi_username}")
    print(f"wifi_password: {settings.wifi_password}")
    print(f"wifi_apikey: {settings.wifi_apikey} (长度: {len(settings.wifi_apikey)})")
    
    # 检查API Key格式
    if settings.wifi_apikey and settings.wifi_apikey.startswith('eyJ'):
        print("[OK] API Key是JWT格式 (正确)")
    elif len(settings.wifi_apikey) == 24:
        print("[WARNING] API Key是24字符字符串 (可能是旧格式)")
    else:
        print("[ERROR] API Key格式未知")
        
except Exception as e:
    print(f"\n❌ 配置加载失败: {type(e).__name__}: {e}")
    import traceback
    print(traceback.format_exc())