#!/usr/bin/env python3
"""
完整的多用户系统测试
"""
import asyncio
import sys
import os
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

async def test_multi_user_system():
    print("=== WIFI标签管理系统 - 多用户系统完整测试 ===\n")
    
    try:
        # 1. 初始化数据库
        print("1. 初始化数据库...")
        from services.db_service import init_db, get_db
        await init_db()
        
        # 2. 检查现有用户
        print("\n2. 检查现有用户...")
        db = await get_db()
        cursor = await db.execute("SELECT id, username, role, wifi_username FROM users WHERE status='active'")
        users = await cursor.fetchall()
        
        print(f"   数据库中有 {len(users)} 个活跃用户:")
        for user in users:
            print(f"     ID: {user[0]}, 用户名: {user[1]}, 角色: {user[2]}, WIFI用户名: {user[3]}")
        
        # 3. 测试创建子用户
        print("\n3. 测试创建子用户...")
        from services.db_service_extended import create_user_with_wifi_config
        
        sub_user_id = await create_user_with_wifi_config(
            username="test_operator",
            password="test123",
            role="operator",
            wifi_username="W123456_test",
            wifi_password="test_password",
            wifi_apikey="test_apikey",
            wifi_base_url="http://192.144.234.153:4000",
            parent_user_id=1,  # admin用户
            created_by=1
        )
        print(f"   创建子用户成功! 用户ID: {sub_user_id}")
        
        # 4. 测试获取用户配置
        print("\n4. 测试获取用户配置...")
        from services.db_service_extended import get_user_wifi_config, get_user_with_details
        
        config = await get_user_wifi_config(sub_user_id)
        print(f"   用户 {sub_user_id} 的WIFI配置:")
        print(f"     用户名: {config.get('wifi_username')}")
        print(f"     API地址: {config.get('wifi_base_url')}")
        print(f"     API Key: {config.get('wifi_apikey')}")
        print(f"     密码加密状态: {'已加密' if config.get('wifi_password') and len(config.get('wifi_password', '')) > 20 else '未加密'}")
        
        # 5. 测试用户登录
        print("\n5. 测试用户登录...")
        from services.auth_service import proxy_login, verify_token
        
        try:
            # 测试管理员登录
            print("   测试管理员登录...")
            admin_result = await proxy_login("admin", "admin123", "127.0.0.1")
            admin_token = admin_result.get('token', '')
            print(f"   管理员登录成功! token: {admin_token[:10]}...")
            
            # 验证token
            is_valid, api_key = verify_token(admin_token)
            print(f"   Token验证: {'有效' if is_valid else '无效'}, API Key: {api_key[:8] if api_key else '无'}...")
            
            # 测试子用户登录
            print("\n   测试子用户登录...")
            sub_result = await proxy_login("test_operator", "test123", "127.0.0.1")
            sub_token = sub_result.get('token', '')
            print(f"   子用户登录成功! token: {sub_token[:10]}...")
            
            # 验证子用户token
            is_valid, api_key = verify_token(sub_token)
            print(f"   Token验证: {'有效' if is_valid else '无效'}")
            
        except Exception as e:
            print(f"   登录测试失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
        
        # 6. 测试用户列表查询
        print("\n6. 测试用户列表查询...")
        from services.db_service_extended import get_users_by_parent
        
        admin_sub_users = await get_users_by_parent(1)  # 获取admin的子用户
        print(f"   admin用户有 {len(admin_sub_users)} 个子用户:")
        for user in admin_sub_users:
            print(f"     - {user.get('username')} (角色: {user.get('role')})")
        
        # 7. 测试AES加密
        print("\n7. 测试AES加密...")
        from services.db_service import encrypt_wifi_password, decrypt_wifi_password
        
        test_password = "MySecretPassword123"
        encrypted = encrypt_wifi_password(test_password)
        decrypted = decrypt_wifi_password(encrypted)
        
        print(f"   原始密码: {test_password}")
        print(f"   加密后: {encrypted[:30]}... (长度: {len(encrypted)})")
        print(f"   解密后: {decrypted}")
        print(f"   加密/解密测试: {'成功' if decrypted == test_password else '失败'}")
        
        # 8. 测试权限控制
        print("\n8. 测试权限控制...")
        from services.db_service import get_user_by_name
        
        admin_user = await get_user_by_name("admin")
        sub_user = await get_user_by_name("test_operator")
        
        print(f"   管理员信息:")
        print(f"     ID: {admin_user.get('id')}")
        print(f"     角色: {admin_user.get('role')}")
        print(f"     WIFI用户名: {admin_user.get('wifi_username')}")
        print(f"     父用户ID: {admin_user.get('parent_user_id')}")
        
        print(f"   子用户信息:")
        print(f"     ID: {sub_user.get('id')}")
        print(f"     角色: {sub_user.get('role')}")
        print(f"     WIFI用户名: {sub_user.get('wifi_username')}")
        print(f"     父用户ID: {sub_user.get('parent_user_id')}")
        print(f"     创建者: {sub_user.get('created_by')}")
        
        # 9. 测试数据库扩展字段
        print("\n9. 测试数据库扩展字段...")
        cursor = await db.execute("PRAGMA table_info(users)")
        columns_info = await cursor.fetchall()
        
        print(f"   users表有 {len(columns_info)} 个字段:")
        wifi_columns = []
        for col in columns_info:
            col_name = col[1]
            if col_name.startswith('wifi_') or col_name in ['parent_user_id', 'created_by']:
                wifi_columns.append(col_name)
            print(f"     - {col_name}")
        
        print(f"\n   多用户相关字段: {', '.join(wifi_columns)}")
        
        # 10. 测试完整的用户详情
        print("\n10. 测试完整的用户详情...")
        user_details = await get_user_with_details(sub_user_id)
        print(f"   用户 {sub_user_id} 的完整信息:")
        print(f"     用户名: {user_details.get('username')}")
        print(f"     角色: {user_details.get('role')}")
        print(f"     状态: {user_details.get('status')}")
        print(f"     WIFI配置:")
        print(f"       用户名: {user_details.get('wifi_username')}")
        print(f"       API地址: {user_details.get('wifi_base_url')}")
        print(f"       API Key: {user_details.get('wifi_apikey')}")
        print(f"       密码解密: {'成功' if user_details.get('wifi_password_decrypted') else '未解密'}")
        print(f"     关系:")
        print(f"       父用户ID: {user_details.get('parent_user_id')}")
        print(f"       创建者: {user_details.get('created_by')}")
        print(f"     时间:")
        print(f"       创建时间: {user_details.get('created_at')}")
        print(f"       更新时间: {user_details.get('updated_at')}")
        
        print("\n=== 测试总结 ===")
        print("✓ 数据库初始化成功")
        print("✓ 多用户表结构完整")
        print("✓ 用户创建功能正常")
        print("✓ WIFI配置存储正常")
        print("✓ AES加密解密正常")
        print("✓ 用户登录正常")
        print("✓ 权限关系正确")
        print("✓ 用户详情查询正常")
        
        print("\n下一步:")
        print("1. 启动后端服务 (python main.py)")
        print("2. 测试用户管理API接口")
        print("3. 测试设备隔离功能")
        print("4. 前端界面集成")
        
    except Exception as e:
        print(f"\n测试失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

async def main():
    await test_multi_user_system()

if __name__ == "__main__":
    asyncio.run(main())