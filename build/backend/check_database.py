#!/usr/bin/env python3
"""
检查数据库配置
"""
import sys
import os
import hashlib

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def check_database():
    print("=== 检查数据库配置 ===")
    
    try:
        from services.db_service import init_db, get_db, get_user_by_name
        
        # 初始化数据库
        await init_db()
        
        # 获取数据库连接
        db = await get_db()
        
        print(f"\n[1] 数据库连接状态: ✅ 成功")
        
        # 检查users表
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = await cursor.fetchall()
        table_names = [row['name'] for row in tables]
        
        print(f"[2] 数据库中的表:")
        for table in table_names:
            print(f"   - {table}")
        
        if 'users' in table_names:
            print(f"\n[3] 检查users表数据...")
            cursor = await db.execute("SELECT * FROM users")
            users = await cursor.fetchall()
            
            print(f"   用户数量: {len(users)}")
            
            for i, user in enumerate(users):
                print(f"\n   用户 {i+1}:")
                print(f"     id: {user['id']}")
                print(f"     username: {user['username']}")
                print(f"     password哈希: {user['password'][:16]}...")
                print(f"     role: {user['role']}")
                print(f"     status: {user['status']}")
                
                # 测试admin用户的密码
                if user['username'] == 'admin':
                    password_to_test = "admin123"
                    hashed_test = hashlib.sha256(password_to_test.encode("utf-8")).hexdigest()
                    print(f"     测试admin123密码: {hashed_test[:16]}...")
                    print(f"     与存储的哈希匹配: {hashed_test == user['password']}")
        
        # 测试get_user_by_name函数
        print(f"\n[4] 测试get_user_by_name('admin'):")
        user = await get_user_by_name("admin")
        if user:
            print(f"   ✅ 找到用户: {user['username']}")
            print(f"   密码哈希: {user['password'][:16]}...")
        else:
            print(f"   ❌ 未找到admin用户")
            
        # 检查默认密码
        print(f"\n[5] 默认密码检查:")
        default_password = "admin123"
        hashed_default = hashlib.sha256(default_password.encode("utf-8")).hexdigest()
        print(f"   admin123的SHA256哈希: {hashed_default[:16]}...")
        
    except Exception as e:
        print(f"❌ 数据库检查失败: {type(e).__name__}: {e}")
        import traceback
        print(f"堆栈: {traceback.format_exc()}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(check_database())