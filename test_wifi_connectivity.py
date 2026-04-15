#!/usr/bin/env python3
"""
测试WIFI系统连通性
"""
import asyncio
import httpx
import sys
from typing import Dict, Any

async def test_connectivity(url: str, timeout: int = 10) -> Dict[str, Any]:
    """测试指定URL的连通性"""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # 尝试连接
            print(f"正在测试连接: {url}")
            response = await client.get(f"{url}/user/api/login", follow_redirects=True)
            
            return {
                "url": url,
                "status_code": response.status_code,
                "reachable": response.status_code < 500,
                "headers": dict(response.headers),
                "text_preview": response.text[:200] if response.text else ""
            }
    except httpx.ConnectTimeout:
        return {"url": url, "error": "连接超时", "reachable": False}
    except httpx.ConnectError:
        return {"url": url, "error": "连接错误", "reachable": False}
    except Exception as e:
        return {"url": url, "error": str(e), "reachable": False}

async def test_wifi_systems():
    """测试所有已知的WIFI系统"""
    wifi_systems = [
        "http://192.144.234.153:4000",  # 用户1的WIFI系统
        "http://192.168.1.172:4000",    # 用户5的WIFI系统
    ]
    
    print("=" * 60)
    print("WIFI系统连通性测试")
    print("=" * 60)
    
    results = []
    for url in wifi_systems:
        result = await test_connectivity(url)
        results.append(result)
    
    # 打印结果
    print("\n测试结果:")
    print("-" * 60)
    
    for result in results:
        if result.get("reachable"):
            print(f"[OK] {result['url']} - 可连接 (状态码: {result.get('status_code', 'N/A')})")
        else:
            print(f"[ERROR] {result['url']} - 不可连接")
            if "error" in result:
                print(f"   错误: {result['error']}")
    
    # 建议
    print("\n建议:")
    print("-" * 60)
    working_systems = [r for r in results if r.get("reachable")]
    if working_systems:
        print(f"发现 {len(working_systems)} 个可用的WIFI系统:")
        for system in working_systems:
            print(f"  - {system['url']}")
    else:
        print("[ERROR] 没有可用的WIFI系统，请检查网络连接和WIFI系统服务")
    
    return results

async def test_user_configs():
    """测试用户配置"""
    print("\n" + "=" * 60)
    print("用户配置检查")
    print("=" * 60)
    
    # 从.env文件读取配置
    import os
    from dotenv import load_dotenv
    
    load_dotenv("backend/.env")
    
    config = {
        "WIFI_BASE_URL": os.getenv("WIFI_BASE_URL"),
        "WIFI_USERNAME": os.getenv("WIFI_USERNAME"),
        "WIFI_APIKEY": os.getenv("WIFI_APIKEY"),
    }
    
    print("后端配置:")
    for key, value in config.items():
        if value:
            masked = value[:8] + "..." if len(value) > 10 else value
            print(f"  {key}: {masked}")
        else:
            print(f"  {key}: [ERROR] 未设置")
    
    # 检查数据库中的用户配置
    try:
        sys.path.append("backend")
        from services.db_service_extended import get_user_wifi_config
        
        print("\n数据库用户配置:")
        for user_id in [1, 5]:  # 测试用户1和5
            try:
                config = await get_user_wifi_config(user_id)
                print(f"\n用户 {user_id}:")
                print(f"  wifi_username: {config.get('wifi_username', 'N/A')}")
                print(f"  wifi_base_url: {config.get('wifi_base_url', 'N/A')}")
                print(f"  wifi_apikey: {config.get('wifi_apikey', 'N/A')[:8]}..." if config.get('wifi_apikey') else "  wifi_apikey: N/A")
            except Exception as e:
                print(f"用户 {user_id}: [ERROR] 获取配置失败 - {e}")
    except ImportError as e:
        print(f"无法导入数据库模块: {e}")

if __name__ == "__main__":
    print("正在启动WIFI系统测试...")
    
    try:
        # 测试连通性
        results = asyncio.run(test_wifi_systems())
        
        # 测试用户配置
        asyncio.run(test_user_configs())
        
        # 总结
        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)
        
        reachable_count = sum(1 for r in results if r.get("reachable"))
        if reachable_count > 0:
            print(f"[OK] 发现 {reachable_count} 个可用的WIFI系统")
        else:
            print("[ERROR] 没有可用的WIFI系统，请检查:")
            print("   1. 网络连接")
            print("   2. WIFI系统服务是否运行")
            print("   3. 防火墙设置")
            print("   4. 配置的URL是否正确")
            
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()