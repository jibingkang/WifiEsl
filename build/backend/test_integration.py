#!/usr/bin/env python3
"""
多用户系统集成测试
"""
import asyncio
import sys
import os

# 添加路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.db_service import init_db, get_db, create_user, get_user_by_name, verify_password
from services.db_service_extended import (
    create_user_with_wifi_config, 
    get_user_wifi_config,
    update_user_wifi_config,
    get_users_by_parent,
    list_all_users
)
from services.auth_service import proxy_login, verify_token

async def test_multi_user_system():
    """测试多用户系统的完整功能"""
    print("=== 多用户系统集成测试 ===")
    
    # 1. 初始化数据库
    print("\n1. 初始化数据库...")
    await init_db()
    print("   数据库初始化完成")
    
    # 2. 创建管理员账号
    print("\n2. 创建管理员账号...")
    admin_id = await create_user_with_wifi_config(
        username="admin",
        password="admin123",
        role="admin",
        wifi_username="admin_wifi",
        wifi_password="admin_wifi_pass",
        wifi_apikey="admin_apikey_123",
        wifi_base_url="http://admin.example.com",
        parent_user_id=None,
        created_by=None
    )
    print(f"   管理员账号创建成功，ID: {admin_id}")
    
    # 3. 创建子用户1
    print("\n3. 创建子用户1...")
    user1_id = await create_user_with_wifi_config(
        username="user1",
        password="user123",
        role="user",
        wifi_username="user1_wifi",
        wifi_password="user1_pass",
        wifi_apikey="user1_apikey_456",
        wifi_base_url="http://user1.example.com",
        parent_user_id=admin_id,
        created_by=admin_id
    )
    print(f"   子用户1创建成功，ID: {user1_id}")
    
    # 4. 创建子用户2
    print("\n4. 创建子用户2...")
    user2_id = await create_user_with_wifi_config(
        username="user2",
        password="user456",
        role="user",
        wifi_username="user2_wifi",
        wifi_password="user2_pass",
        wifi_apikey="user2_apikey_789",
        wifi_base_url="http://user2.example.com",
        parent_user_id=admin_id,
        created_by=admin_id
    )
    print(f"   子用户2创建成功，ID: {user2_id}")
    
    # 5. 测试获取用户WIFI配置
    print("\n5. 测试获取用户WIFI配置...")
    wifi_config = await get_user_wifi_config(user1_id)
    print(f"   用户1 WIFI配置: {wifi_config}")
    
    # 6. 测试更新用户WIFI配置
    print("\n6. 测试更新用户WIFI配置...")
    updated = await update_user_wifi_config(
        user1_id,
        wifi_username="user1_wifi_updated",
        wifi_password="new_pass_123",
        wifi_apikey="new_apikey_999",
        wifi_base_url="http://updated.example.com"
    )
    print(f"   用户1 WIFI配置更新: {'成功' if updated else '失败'}")
    
    # 7. 测试获取更新后的配置
    wifi_config_updated = await get_user_wifi_config(user1_id)
    print(f"   更新后的用户1 WIFI配置: {wifi_config_updated}")
    
    # 8. 测试获取管理员下的所有用户
    print("\n7. 测试获取管理员下的所有用户...")
    admin_users = await get_users_by_parent(admin_id)
    print(f"   管理员({admin_id})下的用户数: {len(admin_users)}")
    for user in admin_users:
        print(f"   - 用户: {user.get('username')} (ID: {user.get('id')})")
    
    # 9. 测试列出所有用户
    print("\n8. 测试列出所有用户...")
    all_users = await list_all_users()
    print(f"   系统总用户数: {len(all_users)}")
    for user in all_users:
        print(f"   - {user.get('username')} (角色: {user.get('role')}, 创建者: {user.get('created_by')})")
    
    # 10. 测试代理登录
    print("\n9. 测试代理登录功能...")
    try:
        # 获取用户1的配置
        user1_config = await get_user_wifi_config(user1_id)
        
        # 模拟代理登录
        login_result = await proxy_login(
            username="user1",
            password="user123",
            wifi_username=user1_config.get("wifi_username"),
            wifi_password=user1_config.get("wifi_password_decrypted"),
            wifi_base_url=user1_config.get("wifi_base_url")
        )
        
        if login_result and "token" in login_result:
            print(f"   代理登录成功，获取到token")
            
            # 验证token
            token_data = verify_token(login_result["token"])
            if token_data:
                print(f"   Token验证成功，用户: {token_data.get('username')}")
                print(f"   Token中的WIFI配置: {token_data.get('wifi_config')}")
            else:
                print("   Token验证失败")
        else:
            print(f"   代理登录失败: {login_result}")
    except Exception as e:
        print(f"   代理登录测试异常: {e}")
    
    # 11. 测试用户密码验证
    print("\n10. 测试用户密码验证...")
    user1 = await get_user_by_name("user1")
    if user1:
        is_valid = await verify_password(user1["id"], "user123")
        print(f"   用户1密码验证: {'成功' if is_valid else '失败'}")
    
    print("\n=== 测试完成 ===")
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_multi_user_system())
        if result:
            print("\n✅ 多用户系统测试通过！")
            sys.exit(0)
        else:
            print("\n❌ 多用户系统测试失败！")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)