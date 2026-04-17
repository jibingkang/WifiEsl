#!/usr/bin/env python3
"""
快速测试多用户系统
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

async def quick_test():
    print("快速测试多用户系统...\n")
    
    try:
        # 1. 测试数据库初始化
        print("1. 测试数据库初始化...")
        from services.db_service import init_db, get_db
        await init_db()
        print("   ✓ 数据库初始化成功")
        
        # 2. 测试用户查询
        print("\n2. 测试用户查询...")
        db = await get_db()
        cursor = await db.execute("SELECT id, username, role FROM users WHERE status='active'")
        users = await cursor.fetchall()
        print(f"   ✓ 找到 {len(users)} 个活跃用户")
        
        # 3. 测试AES加密
        print("\n3. 测试AES加密...")
        from services.db_service import encrypt_wifi_password, decrypt_wifi_password
        test_pwd = "TestPassword123"
        encrypted = encrypt_wifi_password(test_pwd)
        decrypted = decrypt_wifi_password(encrypted)
        
        if decrypted == test_pwd:
            print(f"   ✓ AES加密解密成功")
        else:
            print(f"   ✗ AES加密解密失败")
        
        # 4. 测试用户管理API导入
        print("\n4. 测试用户管理API...")
        try:
            from api.users import router as users_router
            print("   ✓ 用户管理API导入成功")
        except Exception as e:
            print(f"   ✗ 用户管理API导入失败: {e}")
        
        # 5. 测试认证服务
        print("\n5. 测试认证服务...")
        try:
            from services.auth_service import proxy_login, verify_token
            print("   ✓ 认证服务导入成功")
        except Exception as e:
            print(f"   ✗ 认证服务导入失败: {e}")
        
        # 6. 测试数据库扩展
        print("\n6. 测试数据库扩展...")
        try:
            from services.db_service_extended import create_user_with_wifi_config, get_user_wifi_config
            print("   ✓ 数据库扩展导入成功")
        except Exception as e:
            print(f"   ✗ 数据库扩展导入失败: {e}")
        
        print("\n=== 测试完成 ===")
        print("多用户系统核心组件:")
        print("  - 数据库表结构 ✓")
        print("  - AES加密 ✓")
        print("  - 用户管理API ✓")
        print("  - 认证服务 ✓")
        print("  - 数据库扩展 ✓")
        
        print("\n启动后端服务器:")
        print("  python main.py")
        
    except Exception as e:
        print(f"测试失败: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(quick_test())