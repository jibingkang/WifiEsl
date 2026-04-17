#!/usr/bin/env python3
"""
直接测试WIFI系统API
"""
import asyncio
import httpx
import json
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_wifi_api():
    """直接测试WIFI系统API"""
    base_url = "http://192.144.234.153:4000"
    username = "W123456"
    password = "123456"
    
    print(f"测试WIFI系统API...")
    print(f"目标地址: {base_url}")
    print(f"用户名: {username}")
    print(f"密码: {password}")
    
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        # 1. 登录获取API Key
        print("\n=== 步骤1: 登录获取API Key ===")
        try:
            login_resp = await client.post(
                "/user/api/login",
                json={"username": username, "password": password}
            )
            print(f"登录响应状态码: {login_resp.status_code}")
            print(f"登录响应头: {dict(login_resp.headers)}")
            print(f"登录响应内容: {login_resp.text[:500]}")
            
            if login_resp.status_code != 200:
                print(f"登录失败!")
                return
            
            login_data = login_resp.json()
            print(f"登录返回数据: {json.dumps(login_data, indent=2, ensure_ascii=False)}")
            
            # 提取API Key
            api_key = None
            if isinstance(login_data, dict):
                data_part = login_data.get("data", login_data)
                api_key = (
                    data_part.get("token") or
                    data_part.get("apikey") or
                    data_part.get("apiKey") or
                    data_part.get("api_key")
                )
            
            if not api_key:
                print(f"未找到API Key!")
                return
                
            print(f"获取到的API Key: {api_key[:8]}... (长度: {len(api_key)})")
            
        except Exception as e:
            print(f"登录请求异常: {type(e).__name__}: {e}")
            return
        
        # 2. 使用API Key获取设备列表
        print("\n=== 步骤2: 获取设备列表 ===")
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            devices_resp = await client.get(
                "/user/api/rest/devices",
                headers=headers,
                params={"page": 1, "page_size": 20}
            )
            
            print(f"设备列表响应状态码: {devices_resp.status_code}")
            print(f"设备列表响应头: {dict(devices_resp.headers)}")
            print(f"设备列表响应内容 (前800字符):\n{devices_resp.text[:800]}")
            
            if devices_resp.status_code == 200:
                devices_data = devices_resp.json()
                print(f"\n解析后的设备列表数据:")
                print(f"数据类型: {type(devices_data)}")
                
                if isinstance(devices_data, dict):
                    print(f"数据键: {list(devices_data.keys())}")
                    
                    # 提取设备
                    inner_data = devices_data.get("data", devices_data)
                    if isinstance(inner_data, dict):
                        items = inner_data.get("items", [])
                        total = inner_data.get("total", 0)
                        print(f"设备总数: {total}")
                        print(f"本次返回设备数: {len(items) if isinstance(items, list) else 'N/A'}")
                        
                        # 显示前3个设备
                        if isinstance(items, list) and len(items) > 0:
                            print(f"\n前3个设备信息:")
                            for i, device in enumerate(items[:3]):
                                print(f"  [{i+1}] MAC: {device.get('mac', 'N/A')}, IP: {device.get('ip', 'N/A')}, 状态: {device.get('status', 'N/A')}")
                    
                    # 打印完整响应
                    print(f"\n完整响应结构:")
                    print(json.dumps(devices_data, indent=2, ensure_ascii=False)[:1000])
            
            else:
                print(f"获取设备列表失败!")
                
        except Exception as e:
            print(f"设备列表请求异常: {type(e).__name__}: {e}")
            import traceback
            print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_wifi_api())