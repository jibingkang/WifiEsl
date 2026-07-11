#!/usr/bin/env python3
"""
测试数据库连接
"""
import asyncio
import aiosqlite
import os

DB_PATH = "f:/pick/AI项目/CodeBuddy/WifiEsl/backend/data/wifi_esl.db"

async def test_db():
    print(f"测试数据库: {DB_PATH}")
    print(f"文件存在: {os.path.exists(DB_PATH)}")
    
    try:
        print("\n尝试连接数据库...")
        db = await aiosqlite.connect(DB_PATH)
        print("✅ 数据库连接成功")
        
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        print("✅ 外键约束已启用")
        
        # 检查表是否存在
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = await cursor.fetchall()
        print(f"\n数据库中的表 ({len(tables)}个):")
        for table in tables:
            print(f"  - {table[0]}")
        
        # 检查 users 表
        if any(t[0] == 'users' for t in tables):
            cursor = await db.execute("SELECT COUNT(*) FROM users")
            count = await cursor.fetchone()
            print(f"\nusers 表中的用户数量: {count[0]}")
            
            # 查看 admin 用户
            cursor = await db.execute("SELECT id, username, wifi_username, mqtt_username FROM users WHERE username='admin'")
            admin = await cursor.fetchone()
            if admin:
                print(f"\nadmin 用户信息:")
                print(f"  ID: {admin[0]}")
                print(f"  用户名: {admin[1]}")
                print(f"  WIFI用户名: {admin[2]}")
                print(f"  MQTT用户名: {admin[3]}")
        
        await db.close()
        print("\n✅ 数据库测试完成")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_db())
