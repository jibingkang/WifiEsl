#!/usr/bin/env python3
"""
简单测试多用户配置功能
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

async def test_multi_user():
    print("=== 测试多用户配置功能 ===")
    
    try:
        # 初始化数据库
        from services.db_service import init_db, get_db
        print("初始化数据库...")
        await init_db()
        
        # 检查现有用户
        db = await get_db()
        cursor = await db.execute("SELECT id, username, role, wifi_username FROM users WHERE status='active'")
        users = await cursor.fetchall()
        
        print(f"现有用户 ({len(users)}):")
        for user in users:
            print(f"  ID: {user[0]}, 用户名: {user[1]}, 角色: {user[2]}, WIFI用户名: {user[3]}")
        
        # 测试用户管理API路由
        print("\n测试API路由...")
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        # 1. 测试用户列表API（需要认证）
        print("\n1. 测试用户列表API...")
        response = client.get("/api/v1/users")
        print(f"   响应状态码: {response.status_code}")
        print(f"   响应数据: {response.json()}")
        
        # 2. 测试登录
        print("\n2. 测试登录...")
        login_data = {"username": "admin", "password": "admin123"}
        response = client.post("/api/v1/auth/login", json=login_data)
        print(f"   登录响应状态码: {response.status_code}")
        if response.status_code == 200:
            login_result = response.json()
            print(f"   登录成功!")
            token = login_result.get("data", {}).get("token", "")
            if token:
                print(f"   获取到token (前10位): {token[:10]}...")
                
                # 3. 使用token获取用户列表
                print("\n3. 使用token获取用户列表...")
                headers = {"Authorization": f"Bearer {token}"}
                response = client.get("/api/v1/users", headers=headers)
                print(f"   带认证的用户列表响应状态码: {response.status_code}")
                result = response.json()
                if result.get("code") == 20000:
                    users_data = result.get("data", {})
                    print(f"   成功获取用户列表，总数: {users_data.get('total', 0)}")
        
        print("\n测试完成!")
        
    except Exception as e:
        print(f"测试失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_multi_user())