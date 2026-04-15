#!/usr/bin/env python3
"""
检查用户配置
"""
import asyncio
import sys
sys.path.append("backend")

async def check_user_config(user_id: int):
    """检查指定用户的配置"""
    try:
        from services.db_service_extended import get_user_wifi_config
        
        print(f"\n检查用户 {user_id} 的WIFI配置:")
        config = await get_user_wifi_config(user_id)
        
        print(f"  wifi_username: {config.get('wifi_username', 'N/A')}")
        print(f"  wifi_base_url: {config.get('wifi_base_url', 'N/A')}")
        print(f"  wifi_mqtt_broker: {config.get('wifi_mqtt_broker', 'N/A')}")
        
        apikey = config.get('wifi_apikey', '')
        if apikey:
            print(f"  wifi_apikey: {apikey[:8]}... (长度: {len(apikey)})")
        else:
            print(f"  wifi_apikey: N/A")
        
        # 检查URL格式
        base_url = config.get('wifi_base_url', '')
        if base_url:
            if base_url.startswith('mqtt://'):
                print(f"  ⚠️  ERROR: wifi_base_url 使用了 MQTT 协议，应该是 HTTP 协议")
                print(f"    当前: {base_url}")
                print(f"    预期格式: http://ip:port 或 https://ip:port")
            elif base_url.startswith('http://') or base_url.startswith('https://'):
                print(f"  ✅ OK: wifi_base_url 格式正确")
            else:
                print(f"  ⚠️  WARNING: wifi_base_url 格式可能不正确: {base_url}")
                print(f"    预期格式: http://ip:port 或 https://ip:port")
        else:
            print(f"  ⚠️  WARNING: wifi_base_url 为空")
        
        # 检查MQTT broker格式
        mqtt_broker = config.get('wifi_mqtt_broker', '')
        if mqtt_broker:
            if mqtt_broker.startswith('mqtt://') or mqtt_broker.startswith('ws://') or mqtt_broker.startswith('wss://'):
                print(f"  ✅ OK: wifi_mqtt_broker 格式正确")
            else:
                print(f"  ⚠️  WARNING: wifi_mqtt_broker 格式可能不正确: {mqtt_broker}")
                print(f"    预期格式: mqtt://ip:port 或 ws://ip:port 或 wss://ip:port")
        else:
            print(f"  ℹ️  INFO: wifi_mqtt_broker 为空")
        
        return config
    except Exception as e:
        print(f"  获取用户 {user_id} 配置失败: {e}")
        return None

async def main():
    print("=" * 60)
    print("用户配置检查")
    print("=" * 60)
    
    # 检查所有用户
    for user_id in [1, 5, 2]:  # 检查用户1, 5, 2
        await check_user_config(user_id)
    
    # 检查.env中的配置
    print("\n" + "=" * 60)
    print(".env配置文件检查")
    print("=" * 60)
    
    import os
    from dotenv import load_dotenv
    
    load_dotenv("backend/.env")
    
    env_config = {
        "WIFI_BASE_URL": os.getenv("WIFI_BASE_URL"),
        "WIFI_USERNAME": os.getenv("WIFI_USERNAME"),
        "WIFI_APIKEY": os.getenv("WIFI_APIKEY"),
        "MQTT_BROKER_HOST": os.getenv("MQTT_BROKER_HOST"),
        "MQTT_BROKER_PORT": os.getenv("MQTT_BROKER_PORT"),
    }
    
    print("后端.env配置:")
    for key, value in env_config.items():
        if value:
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: [未设置]")
    
    # 建议
    print("\n" + "=" * 60)
    print("配置建议")
    print("=" * 60)
    print("1. WIFI系统连接 (API调用):")
    print("   - 使用 HTTP/HTTPS 协议 (http://ip:port 或 https://ip:port)")
    print("   - 用于登录、获取设备列表、推送模板等操作")
    print("   - 对应字段: wifi_base_url")
    print()
    print("2. MQTT连接 (实时消息):")
    print("   - 使用 MQTT/WS/WSS 协议 (mqtt://ip:port 或 ws://ip:port)")
    print("   - 用于设备状态监控、实时事件接收")
    print("   - 对应字段: wifi_mqtt_broker")
    print()
    print("3. API Key:")
    print("   - 用于 MQTT 订阅和认证")
    print("   - 对应字段: wifi_apikey")
    print()
    print("4. Token:")
    print("   - 用于 WIFI 系统 API 调用 (Bearer Token)")
    print("   - 对应字段: wifi_token (通过登录获取并存储)")

if __name__ == "__main__":
    asyncio.run(main())