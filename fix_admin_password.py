#!/usr/bin/env python3
"""
修复 admin 用户的 WIFI 密码
"""
import asyncio
import sys
import os

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from services.db_service import init_db, get_db
from services.db_service_extended import update_user_wifi_config

async def fix_admin_wifi_password():
    """修复 admin 的 WIFI 密码为 123456"""
    print("=" * 60)
    print("修复 admin 用户 WIFI 密码")
    print("=" * 60)
    
    # 初始化数据库
    await init_db()
    
    # 查找 admin 用户
    db = await get_db()
    cursor = await db.execute("SELECT id, username, wifi_username, wifi_password FROM users WHERE username = 'admin'")
    admin = await cursor.fetchone()
    
    if not admin:
        print("❌ 未找到 admin 用户")
        return
    
    user_id = admin[0]
    print(f"找到用户: ID={user_id}, 用户名={admin[1]}")
    print(f"当前 WIFI 用户名: {admin[2]}")
    print(f"当前 WIFI 密码: {admin[3][:20]}..." if admin[3] else "当前 WIFI 密码: 未设置")
    
    # 更新 WIFI 配置
    print("\n正在更新 WIFI 配置...")
    print("  - WIFI 用户名: W123456")
    print("  - WIFI 密码: 123456")
    
    success = await update_user_wifi_config(
        user_id=user_id,
        wifi_username="W123456",
        wifi_password="123456"
    )
    
    if success:
        print("\n✅ admin 用户的 WIFI 配置已更新")
        print("\n现在可以使用以下配置登录:")
        print("  本系统用户名: admin")
        print("  本系统密码: <你的admin密码>")
        print("  WIFI 系统用户名: W123456")
        print("  WIFI 系统密码: 123456")
    else:
        print("\n❌ 更新失败")

if __name__ == "__main__":
    asyncio.run(fix_admin_wifi_password())
