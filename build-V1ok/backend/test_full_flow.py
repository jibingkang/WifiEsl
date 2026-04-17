#!/usr/bin/env python3
"""
测试完整的登录和设备获取流程
"""
import asyncio
import httpx
import json
import logging
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置详细的日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

async def test_full_flow():
    """测试完整流程"""
    print("=== 测试完整登录和设备获取流程 ===")
    
    # 1. 直接测试WIFI系统登录
    print("\n[1] 直接测试WIFI系统登录...")
    base_url = "http://192.144.234.153:4000"
    username = "W123456"
    password = "123456"
    
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        # 登录WIFI系统
        login_resp = await client.post(
            "/user/api/login",
            json={"username": username, "password": password}
        )
        
        print(f"WIFI系统登录状态码: {login_resp.status_code}")
        
        if login_resp.status_code == 200:
            login_data = login_resp.json()
            print(f"WIFI系统登录响应: {json.dumps(login_data, indent=2, ensure_ascii=False)[:500]}")
            
            # 提取JWT token
            data_part = login_data.get("data", login_data)
            jwt_token = (
                data_part.get("token") or
                data_part.get("apikey") or
                data_part.get("apiKey") or
                data_part.get("api_key")
            )
            
            if jwt_token:
                print(f"✅ 获取到JWT token: {jwt_token[:8]}... (长度: {len(jwt_token)})")
                print(f"   格式检查: {'是JWT (eyJ开头)' if jwt_token.startswith('eyJ') else '不是标准JWT'}")
            else:
                print("❌ 登录响应中没有找到token字段")
                return
        else:
            print(f"❌ WIFI系统登录失败: {login_resp.status_code}")
            print(f"响应内容: {login_resp.text[:200]}")
            return
    
    # 2. 模拟本地系统登录（调用本地后端）
    print("\n[2] 模拟本地系统登录...")
    local_base_url = "http://127.0.0.1:8001"
    
    try:
        # 创建本地客户端
        local_client = httpx.AsyncClient(base_url=local_base_url, timeout=30.0)
        
        # 登录本地系统
        local_login_resp = await local_client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        
        print(f"本地系统登录状态码: {local_login_resp.status_code}")
        
        if local_login_resp.status_code == 200:
            local_data = local_login_resp.json()
            print(f"本地登录响应: {json.dumps(local_data, ensure_ascii=False)[:300]}")
            
            if local_data.get("code") == 20000:
                local_token = local_data.get("data", {}).get("token")
                if local_token:
                    print(f"✅ 获取到本地JWT token: {local_token[:8]}...")
                    
                    # 3. 使用本地token获取设备列表
                    print("\n[3] 使用本地token获取设备列表...")
                    
                    headers = {
                        "Authorization": f"Bearer {local_token}",
                        "Content-Type": "application/json"
                    }
                    
                    devices_resp = await local_client.get(
                        "/api/v1/devices",
                        headers=headers,
                        params={"page": 1, "page_size": 20}
                    )
                    
                    print(f"设备列表状态码: {devices_resp.status_code}")
                    print(f"设备列表响应头: {dict(devices_resp.headers)}")
                    
                    if devices_resp.status_code == 200:
                        devices_data = devices_resp.json()
                        print(f"设备列表响应: {json.dumps(devices_data, ensure_ascii=False)[:500]}")
                        
                        if devices_data.get("code") == 20000:
                            data = devices_data.get("data", {})
                            total = data.get("total", 0)
                            items = data.get("items", [])
                            print(f"✅ 成功获取设备列表!")
                            print(f"   设备总数: {total}")
                            print(f"   返回设备数: {len(items) if isinstance(items, list) else 'N/A'}")
                            
                            if isinstance(items, list) and len(items) > 0:
                                print(f"   前3个设备:")
                                for i, device in enumerate(items[:3]):
                                    print(f"     [{i+1}] MAC: {device.get('mac', 'N/A')}, IP: {device.get('ip', 'N/A')}")
                        else:
                            print(f"❌ 设备列表API返回错误: {devices_data.get('message')}")
                    else:
                        print(f"❌ 设备列表请求失败: {devices_resp.status_code}")
                        print(f"响应内容: {devices_resp.text[:200]}")
                else:
                    print("❌ 本地登录响应中没有token")
            else:
                print(f"❌ 本地登录失败: {local_data.get('message')}")
        else:
            print(f"❌ 本地系统登录失败: {local_login_resp.status_code}")
            print(f"响应内容: {local_login_resp.text[:200]}")
            
    except httpx.ConnectError as e:
        print(f"❌ 无法连接到本地服务器 (端口8001)")
        print(f"请确保后端服务正在运行: python main.py")
        print(f"错误详情: {e}")
    except Exception as e:
        print(f"❌ 其他错误: {type(e).__name__}: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        # 关闭客户端
        if 'local_client' in locals():
            await local_client.aclose()

if __name__ == "__main__":
    asyncio.run(test_full_flow())