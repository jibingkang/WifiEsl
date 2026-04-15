#!/usr/bin/env python3
"""
快速测试WIFI系统连接
"""
import httpx
import asyncio

async def test_wifi_login():
    """测试WIFI系统登录"""
    url = "http://192.144.234.153:4000"
    username = "W123456"
    password = "123456"
    
    print(f"测试WIFI系统登录:")
    print(f"  URL: {url}")
    print(f"  用户名: {username}")
    print(f"  密码: ******")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 尝试连接
            print(f"\n1. 尝试连接...")
            response = await client.post(
                f"{url}/user/api/login",
                json={"username": username, "password": password}
            )
            
            print(f"  响应状态码: {response.status_code}")
            print(f"  响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n2. 登录成功，返回数据:")
                print(f"  完整响应: {data}")
                
                # 检查token
                token = data.get('token')
                if token:
                    print(f"\n3. 找到token:")
                    print(f"  token: {token[:16]}...")
                    print(f"  token长度: {len(token)}")
                else:
                    print(f"\n3. 没有找到token字段")
                    print(f"  所有字段: {list(data.keys())}")
                    
                    # 检查是否有apiKey
                    apiKey = data.get('apiKey')
                    if apiKey:
                        print(f"\n4. 找到apiKey:")
                        print(f"  apiKey: {apiKey[:16]}...")
                        print(f"  apiKey长度: {len(apiKey)}")
                        
                    # 检查是否有data字段
                    if 'data' in data and isinstance(data['data'], dict):
                        print(f"\n5. 检查data字段:")
                        data_content = data['data']
                        print(f"  data字段内容: {data_content}")
                        
                        if 'token' in data_content:
                            print(f"  在data中找到token: {data_content['token'][:16]}...")
            else:
                print(f"\n[ERROR] 登录失败: {response.status_code}")
                print(f"  响应内容: {response.text[:200]}")
                
    except httpx.ConnectTimeout:
        print(f"\n[ERROR] 连接超时")
    except httpx.ConnectError:
        print(f"\n[ERROR] 连接错误")
    except Exception as e:
        print(f"\n[ERROR] 其他错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("开始测试WIFI系统登录...")
    asyncio.run(test_wifi_login())