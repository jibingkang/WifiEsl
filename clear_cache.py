#!/usr/bin/env python3
"""
清除连接管理器缓存
"""
import asyncio
import sys
sys.path.append("backend")

async def clear_connection_cache():
    """清除连接管理器缓存"""
    try:
        from services.wifi_connection_manager import WifiConnectionManager
        
        manager = WifiConnectionManager()
        
        # 清除连接缓存
        manager._connections.clear()
        manager._user_tokens.clear()
        
        print("[OK] 连接管理器缓存已清除")
        
        # 测试获取新连接
        print("\n[TEST] 测试获取新连接...")
        conn = await manager.get_connection(1)
        
        if conn:
            print(f"  获取连接成功")
            print(f"  wifi_base_url: {conn.wifi_base_url}")
            print(f"  wifi_mqtt_broker: {conn.wifi_mqtt_broker}")
            print(f"  token: {conn.token[:16] if conn.token else 'N/A'}...")
            print(f"  api_key: {conn.api_key[:16] if conn.api_key else 'N/A'}...")
            
            # 检查配置是否正确
            if conn.wifi_base_url == 'http://192.144.234.153:4000':
                print("  [OK] wifi_base_url 配置正确")
            else:
                print(f"  [ERROR] wifi_base_url 配置错误: {conn.wifi_base_url}")
                
        else:
            print("  获取连接失败")
            
    except Exception as e:
        print(f"[ERROR] 清除缓存失败: {e}")

if __name__ == "__main__":
    print("开始清除连接管理器缓存...")
    asyncio.run(clear_connection_cache())