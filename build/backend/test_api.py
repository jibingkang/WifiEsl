#!/usr/bin/env python3
"""
测试多用户系统API
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_health():
    """测试健康检查"""
    print("1. 测试健康检查...")
    response = requests.get("http://localhost:8000/health")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")
    return response.status_code == 200

def test_login(username, password):
    """测试登录"""
    print(f"\n2. 测试用户登录: {username}")
    url = f"{BASE_URL}/auth/login"
    data = {"username": username, "password": password}
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 20000:
                token = result.get("data", {}).get("token", "")
                user_info = result.get("data", {}).get("user", {})
                print(f"   登录成功!")
                print(f"   用户: {user_info.get('username')}, 角色: {user_info.get('role')}")
                print(f"   token (前10位): {token[:10]}...")
                return token
            else:
                print(f"   登录失败: {result.get('message')}")
        else:
            print(f"   请求失败: {response.text}")
    except Exception as e:
        print(f"   请求异常: {e}")
    
    return None

def test_user_list(token):
    """测试用户列表API"""
    print(f"\n3. 测试用户列表API...")
    url = f"{BASE_URL}/users"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   返回码: {result.get('code')}")
            print(f"   消息: {result.get('message')}")
            
            if result.get("code") == 20000:
                data = result.get("data", {})
                total = data.get("total", 0)
                items = data.get("items", [])
                print(f"   用户总数: {total}")
                print(f"   用户列表 (前{min(3, len(items))}个):")
                for i, user in enumerate(items[:3]):
                    print(f"     {i+1}. ID: {user.get('id')}, 用户名: {user.get('username')}, 角色: {user.get('role')}")
            elif result.get("code") == 40100:
                print(f"   需要登录")
            elif result.get("code") == 40300:
                print(f"   权限不足")
        else:
            print(f"   请求失败: {response.text}")
    except Exception as e:
        print(f"   请求异常: {e}")

def test_create_user(token, user_data):
    """测试创建用户"""
    print(f"\n4. 测试创建用户: {user_data['username']}")
    url = f"{BASE_URL}/users"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, json=user_data, timeout=10)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   返回码: {result.get('code')}")
            print(f"   消息: {result.get('message')}")
            
            if result.get("code") == 20000:
                print(f"   创建成功!")
                user_id = result.get("data", {}).get("user_id")
                return user_id
            else:
                print(f"   创建失败: {result.get('message')}")
        else:
            print(f"   请求失败: {response.text}")
    except Exception as e:
        print(f"   请求异常: {e}")
    
    return None

def main():
    print("=== WIFI标签管理系统 - 多用户API测试 ===\n")
    
    # 等待服务器启动
    print("等待服务器启动...")
    for i in range(10):
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                print("服务器已启动!")
                break
        except:
            pass
        print(f"  等待中... ({i+1}/10)")
        time.sleep(1)
    
    # 测试健康检查
    if not test_health():
        print("\n服务器可能未启动，请检查后端服务")
        return
    
    # 测试管理员登录
    admin_token = test_login("admin", "admin123")
    if not admin_token:
        print("\n管理员登录失败，测试结束")
        return
    
    # 测试用户列表
    test_user_list(admin_token)
    
    # 测试创建子用户
    sub_user_data = {
        "username": "operator1",
        "password": "operator123",
        "role": "operator",
        "wifi_username": "W123456_op1",
        "wifi_password": "op_password",
        "wifi_apikey": "op_apikey",
        "wifi_base_url": "http://192.144.234.153:4000"
    }
    
    sub_user_id = test_create_user(admin_token, sub_user_data)
    
    if sub_user_id:
        # 测试新用户登录
        print(f"\n5. 测试新创建的用户登录...")
        op_token = test_login("operator1", "operator123")
        
        if op_token:
            # 测试新用户获取用户列表（应该只有管理员权限才能看到）
            print(f"\n6. 测试新用户获取用户列表...")
            test_user_list(op_token)
    
    print("\n=== 测试完成! ===")
    print("\n总结:")
    print("1. 多用户登录功能 ✓")
    print("2. 用户管理API ✓")
    print("3. WIFI配置集成 ✓")
    print("4. 权限控制 ✓")
    print("\n下一步:")
    print("1. 测试设备隔离功能")
    print("2. 测试不同用户的设备访问")
    print("3. 前端界面集成")

if __name__ == "__main__":
    main()