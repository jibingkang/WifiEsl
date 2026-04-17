#!/usr/bin/env python3
"""
直接测试登录流程，看是否调用WIFI系统登录
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_login():
    print("=== 测试完整的登录流程 ===")
    
    # 导入必要的模块
    from services.auth_service import proxy_login
    from config import settings
    
    print(f"\n[1] 当前配置:")
    print(f"   WIFI_BASE_URL: {settings.wifi_base_url}")
    print(f"   WIFI_USERNAME: {settings.wifi_username}")
    print(f"   WIFI_PASSWORD: {'*' * len(settings.wifi_password)}")
    print(f"   WIFI_APIKEY: {settings.wifi_apikey[:8]}... (长度: {len(settings.wifi_apikey)})")
    
    print(f"\n[2] 调用 proxy_login()...")
    try:
        # 使用本地系统用户登录
        result = await proxy_login("admin", "admin123", "127.0.0.1")
        
        print(f"\n[3] 登录结果:")
        print(f"   状态: ✅ 成功")
        print(f"   返回的JWT token: {result.get('token', '')[:8]}...")
        
        # 检查token格式
        token = result.get('token', '')
        if token.startswith('eyJ'):
            print(f"   JWT格式: ✅ 标准JWT")
        else:
            print(f"   JWT格式: ⚠️  非标准格式 (开头不是'eyJ')")
        
        print(f"   token长度: {len(token)} 字符")
        
        return result
        
    except Exception as e:
        print(f"\n[3] 登录结果:")
        print(f"   状态: ❌ 失败")
        print(f"   错误: {type(e).__name__}: {e}")
        import traceback
        print(f"   堆栈: {traceback.format_exc()}")
        return None

async def test_device_list(token):
    print(f"\n[4] 测试使用token获取设备列表...")
    
    import httpx
    
    if not token:
        print("   没有token，跳过")
        return
    
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8001", timeout=30.0) as client:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            resp = await client.get(
                "/api/v1/devices",
                headers=headers,
                params={"page": 1, "page_size": 20}
            )
            
            print(f"   状态码: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"   ✅ 成功获取设备列表")
                print(f"   响应code: {data.get('code', 'N/A')}")
                
                data_part = data.get('data', {})
                if isinstance(data_part, dict):
                    total = data_part.get('total', 0)
                    items = data_part.get('items', [])
                    print(f"   设备总数: {total}")
                    print(f"   返回设备数: {len(items) if isinstance(items, list) else 'N/A'}")
                    
                    if isinstance(items, list) and len(items) > 0:
                        print(f"   前3个设备:")
                        for i, device in enumerate(items[:3]):
                            print(f"     [{i+1}] MAC: {device.get('mac', 'N/A')}, IP: {device.get('ip', 'N/A')}")
            else:
                print(f"   ❌ 失败: {resp.status_code}")
                print(f"   响应: {resp.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ 异常: {type(e).__name__}: {e}")

async def main():
    print("WIFI标签管理系统 - 登录流程诊断")
    print("=" * 50)
    
    # 测试登录
    result = await test_login()
    
    if result:
        token = result.get('token')
        await test_device_list(token)
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("请查看日志文件: backend/wifi_esl_debug.log")
    print("查看是否有 [登录WIFI系统] 和 [AUTH] 相关的日志")

if __name__ == "__main__":
    asyncio.run(main())