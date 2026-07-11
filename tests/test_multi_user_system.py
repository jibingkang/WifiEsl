#!/usr/bin/env python3
"""
测试多用户WIFI系统功能
"""
import asyncio
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_wifi_connection_manager():
    """测试WIFI连接管理器"""
    print("=== 测试WIFI连接管理器 ===")
    
    from services.wifi_connection_manager import wifi_connection_manager
    
    # 测试用户ID 1（假设admin用户）
    user_id = 1
    print(f"测试用户 {user_id} 的WIFI连接...")
    
    try:
        # 获取连接
        conn = await wifi_connection_manager.get_connection(user_id)
        if conn:
            print(f"✓ 用户 {user_id} WIFI连接成功")
            print(f"  - Base URL: {conn.wifi_base_url}")
            print(f"  - Token: {conn.token[:8]}... (长度: {len(conn.token)})")
            print(f"  - API Key: {conn.api_key[:8]}... (长度: {len(conn.api_key)})")
            print(f"  - MQTT Broker: {conn.wifi_mqtt_broker}")
        else:
            print(f"✗ 用户 {user_id} WIFI连接失败")
            
    except Exception as e:
        print(f"✗ WIFI连接管理器测试失败: {e}")

async def test_multi_user_mqtt_manager():
    """测试多用户MQTT管理器"""
    print("\n=== 测试多用户MQTT管理器 ===")
    
    from services.multi_user_mqtt_manager import multi_user_mqtt_manager
    from services.wifi_connection_manager import wifi_connection_manager
    
    # 测试用户ID 1
    user_id = 1
    
    try:
        # 首先确保WIFI连接可用
        conn = await wifi_connection_manager.get_connection(user_id)
        if not conn:
            print("✗ 需要先建立WIFI连接")
            return
        
        print(f"测试用户 {user_id} 的MQTT连接...")
        
        # 启动MQTT连接
        success = await multi_user_mqtt_manager.start_user_connection(user_id)
        if success:
            print(f"✓ 用户 {user_id} MQTT连接启动成功")
            
            # 检查连接状态
            is_connected = await multi_user_mqtt_manager.is_user_connected(user_id)
            print(f"  - 连接状态: {'已连接' if is_connected else '未连接'}")
            
            # 获取连接信息
            user_conn = await multi_user_mqtt_manager.get_user_connection(user_id)
            if user_conn:
                print(f"  - Broker: {user_conn.broker_host}:{user_conn.broker_port}")
                print(f"  - API Key: {user_conn.api_key[:8]}...")
            
            # 停止连接
            await multi_user_mqtt_manager.stop_user_connection(user_id)
            print(f"✓ 用户 {user_id} MQTT连接已停止")
        else:
            print(f"✗ 用户 {user_id} MQTT连接启动失败")
            
    except Exception as e:
        print(f"✗ MQTT管理器测试失败: {e}")

async def test_device_api_with_user_token():
    """测试使用用户token获取设备列表"""
    print("\n=== 测试用户token获取设备列表 ===")
    
    import httpx
    import json
    
    # 首先获取用户的token
    from services.wifi_connection_manager import wifi_connection_manager
    from services.auth_service import create_token, verify_token
    
    user_id = 1
    
    try:
        # 获取用户WIFI token
        conn = await wifi_connection_manager.get_connection(user_id)
        if not conn or not conn.token:
            print("✗ 无法获取用户WIFI token")
            return
        
        wifi_token = conn.token
        print(f"用户 {user_id} 的WIFI token: {wifi_token[:8]}...")
        
        # 创建本地系统token（用于API认证）
        local_token = create_token(username="admin", user_id=user_id, role="admin")
        print(f"本地系统token: {local_token[:8]}...")
        
        # 测试调用设备API
        async with httpx.AsyncClient(base_url="http://localhost:3001") as client:
            headers = {
                "Authorization": f"Bearer {local_token}",
                "Content-Type": "application/json"
            }
            
            print("调用设备列表API...")
            response = await client.get("/api/v1/devices", headers=headers, params={"page": 1, "page_size": 5})
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 20000:
                    devices = data.get("data", {}).get("items", [])
                    print(f"✓ 成功获取 {len(devices)} 个设备")
                    for device in devices[:3]:  # 显示前3个设备
                        print(f"  - {device.get('mac')}: {device.get('name')} (在线: {device.get('is_online')})")
                else:
                    print(f"✗ API返回错误: {data.get('message')}")
            else:
                print(f"✗ API调用失败: {response.status_code}")
                
    except Exception as e:
        print(f"✗ 设备API测试失败: {e}")

async def main():
    """主测试函数"""
    print("多用户WIFI系统功能测试")
    print("=" * 50)
    
    # 测试顺序
    await test_wifi_connection_manager()
    await test_multi_user_mqtt_manager()
    await test_device_api_with_user_token()
    
    print("\n" + "=" * 50)
    print("测试完成")

if __name__ == "__main__":
    asyncio.run(main())