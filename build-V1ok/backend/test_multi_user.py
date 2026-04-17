#!/usr/bin/env python3
"""
测试多用户配置功能
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_multi_user_config():
    print("=== 测试多用户配置功能 ===")
    
    # 导入必要的模块
    from services.db_service import get_db, init_db
    from services.db_service_extended import create_user_with_wifi_config, get_user_wifi_config
    from services.auth_service import proxy_login
    from config import settings
    
    print(f"\n[1] 初始化数据库...")
    await init_db()
    
    print(f"\n[2] 获取当前数据库用户...")
    try:
        # 创建第一个子用户
        print(f"\n[3] 创建第一个子用户...")
        user1_id = await create_user_with_wifi_config(
            username="customer1",
            password="customer123",
            role="operator",
            wifi_username="W123456_customer1",
            wifi_password="wifi_password1",
            wifi_apikey="customer1_api_key",
            wifi_base_url="http://192.144.234.153:4000",
            parent_user_id=1,  # admin用户
            created_by=1
        )
        print(f"   用户ID: {user1_id}")
        
        # 创建第二个子用户
        print(f"\n[4] 创建第二个子用户...")
        user2_id = await create_user_with_wifi_config(
            username="customer2",
            password="customer456",
            role="operator",
            wifi_username="W123456_customer2",
            wifi_password="wifi_password2",
            wifi_apikey="customer2_api_key",
            wifi_base_url="http://192.144.234.153:4000",
            parent_user_id=1,  # admin用户
            created_by=1
        )
        print(f"   用户ID: {user2_id}")
        
        # 测试获取用户配置
        print(f"\n[5] 测试获取用户配置...")
        try:
            config1 = await get_user_wifi_config(user1_id)
            print(f"   用户 {user1_id} WIFI配置:")
            print(f"     用户名: {config1.get('wifi_username')}")
            print(f"     API地址: {config1.get('wifi_base_url')}")
            print(f"     API Key: {config1.get('wifi_apikey')}")
            print(f"     密码解密状态: {'已解密' if 'wifi_password_decrypted' in config1 else '未解密/加密'}")
        
            config2 = await get_user_wifi_config(user2_id)
            print(f"   用户 {user2_id} WIFI配置:")
            print(f"     用户名: {config2.get('wifi_username')}")
            print(f"     密码解密状态: {'已解密' if 'wifi_password_decrypted' in config2 else '未解密/加密'}")
        except Exception as e:
            print(f"   获取用户配置失败: {e}")
        
        # 测试用户登录
        print(f"\n[6] 测试用户登录...")
        try:
            # 测试用户1登录
            result1 = await proxy_login("customer1", "customer123", "127.0.0.1")
            print(f"   用户 customer1 登录成功!")
            print(f"   返回的JWT token: {result1.get('token', '')[:8]}...")
            print(f"   用户信息:")
            print(f"     用户名: {result1.get('user', {}).get('username')}")
            print(f"     角色: {result1.get('user', {}).get('role')}")
        
            # 测试用户2登录
            result2 = await proxy_login("customer2", "customer456", "127.0.0.1")
            print(f"   用户 customer2 登录成功!")
            print(f"   返回的JWT token: {result2.get('token', '')[:8]}...")
        
        except Exception as e:
            print(f"   用户登录失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    except Exception as e:
        print(f"错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n[7] 测试完成!")
    print(f"接下来需要:")
    print(f"1. 创建用户管理API")
    print(f"2. 修改前端界面")
    print(f"3. 测试设备隔离")

async def main():
    print("WIFI标签管理系统 - 多用户配置测试")
    print("=" * 50)
    
    await test_multi_user_config()

if __name__ == "__main__":
    asyncio.run(main())