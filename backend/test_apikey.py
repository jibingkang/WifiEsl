#!/usr/bin/env python3
"""
测试不同的API Key格式
"""
import asyncio
import httpx
import json

async def test_api_key(api_key, description):
    """测试API Key是否有效"""
    base_url = "http://192.144.234.153:4000"
    
    print(f"\n=== 测试: {description} ===")
    print(f"API Key: {api_key[:8]}... (长度: {len(api_key)})")
    
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            resp = await client.get(
                "/user/api/rest/devices",
                headers=headers,
                params={"page": 1, "page_size": 20}
            )
            
            print(f"响应状态码: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"[SUCCESS] 获取设备列表成功!")
                if isinstance(data, dict):
                    inner = data.get("data", data)
                    if isinstance(inner, dict):
                        total = inner.get("total", 0)
                        print(f"设备总数: {total}")
                    else:
                        print(f"返回数据: {json.dumps(data, ensure_ascii=False)[:200]}")
                return True
            else:
                print(f"[FAILED] 失败: {resp.status_code}")
                print(f"响应内容: {resp.text[:200]}")
                return False
                
        except Exception as e:
            print(f"[ERROR] 异常: {type(e).__name__}: {e}")
            return False

async def main():
    # 测试1: 使用项目中的API Key
    project_key = "cef24a6d1fffaf23d2eb72ff"
    await test_api_key(project_key, "项目配置中的API Key (24字符)")
    
    # 测试2: 使用登录获取的JWT token
    # 先登录获取JWT
    base_url = "http://192.144.234.153:4000"
    username = "W123456"
    password = "123456"
    
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        login_resp = await client.post(
            "/user/api/login",
            json={"username": username, "password": password}
        )
        
        if login_resp.status_code == 200:
            login_data = login_resp.json()
            jwt_token = login_data.get("data", {}).get("token")
            if jwt_token:
                await test_api_key(jwt_token, "登录获取的JWT token")
            else:
                print("登录响应中没有找到token")
        else:
            print(f"登录失败: {login_resp.status_code}")

if __name__ == "__main__":
    asyncio.run(main())