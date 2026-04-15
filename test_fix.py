#!/usr/bin/env python3
"""
快速测试修复
"""
import asyncio
import sys
sys.path.append("backend")

async def test():
    try:
        from services.db_service_extended import get_user_wifi_config
        
        print("测试 get_user_wifi_config(1)...")
        config = await get_user_wifi_config(1)
        
        print("修复后配置:")
        print(f"  wifi_username: {config.get('wifi_username')}")
        print(f"  wifi_base_url: {config.get('wifi_base_url')}")
        print(f"  wifi_mqtt_broker: {config.get('wifi_mqtt_broker')}")
        print(f"  wifi_apikey: {config.get('wifi_apikey', '')[:8] if config.get('wifi_apikey') else 'N/A'}...")
        print(f"  wifi_token: {config.get('wifi_token', '')[:8] if config.get('wifi_token') else 'N/A'}...")
        
        # 检查是否正确
        base_url = config.get('wifi_base_url', '')
        mqtt_broker = config.get('wifi_mqtt_broker', '')
        
        if base_url == 'http://192.144.234.153:4000':
            print("[OK] wifi_base_url 正确")
        else:
            print(f"[ERROR] wifi_base_url 不正确: {base_url}")
            
        if mqtt_broker == 'mqtt://192.144.234.153:8883':
            print("[OK] wifi_mqtt_broker 正确")
        else:
            print(f"[ERROR] wifi_mqtt_broker 不正确: {mqtt_broker}")
            
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test())