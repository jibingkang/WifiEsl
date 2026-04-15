#!/usr/bin/env python3
"""
测试get_user_wifi_config函数
"""
import asyncio
import sys
sys.path.append("backend")

async def test_get_user_wifi_config():
    """测试get_user_wifi_config函数"""
    try:
        from services.db_service_extended import get_user_wifi_config
        
        print("测试 get_user_wifi_config(1)...")
        config = await get_user_wifi_config(1)
        
        print("返回的配置:")
        print(f"  wifi_username: {config.get('wifi_username')}")
        print(f"  wifi_base_url: {config.get('wifi_base_url')}")
        print(f"  wifi_mqtt_broker: {config.get('wifi_mqtt_broker')}")
        print(f"  wifi_apikey: {config.get('wifi_apikey', '')[:16] if config.get('wifi_apikey') else 'N/A'}")
        print(f"  wifi_token: {config.get('wifi_token', '')[:16] if config.get('wifi_token') else 'N/A'}")
        
        # 检查SQL查询是否正确
        print("\n[DEBUG] 检查SQL查询...")
        import aiosqlite
        
        db_path = "backend/data/wifi_esl.db"
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute('''
                SELECT 
                    wifi_username, wifi_password, wifi_apikey, wifi_base_url, wifi_mqtt_broker,
                    username, role
                FROM users WHERE id = 1
            ''')
            row = await cursor.fetchone()
            
            if row:
                print("SQL查询结果:")
                print(f"  1. wifi_username: {row[0]}")
                print(f"  2. wifi_password: {row[1][:16] if row[1] else 'N/A'}...")
                print(f"  3. wifi_apikey: {row[2][:16] if row[2] else 'N/A'}...")
                print(f"  4. wifi_base_url: {row[3]}")
                print(f"  5. wifi_mqtt_broker: {row[4]}")
                print(f"  6. username: {row[5]}")
                print(f"  7. role: {row[6]}")
                
                # 检查列对应关系
                print("\n[DEBUG] 列对应关系检查:")
                column_names = ['wifi_username', 'wifi_password', 'wifi_apikey', 'wifi_token', 'wifi_base_url', 'wifi_mqtt_broker', 'username', 'role']
                
                for i, col_name in enumerate(column_names):
                    if i < len(row):
                        print(f"  {col_name}: {row[i] if row[i] else 'None'}")
                    else:
                        print(f"  {col_name}: (超出范围)")
                
                # 问题检查：wifi_token列在SQL查询中没有，但函数期望它
                if 'wifi_token' in column_names:
                    print("\n[WARNING] SQL查询中没有wifi_token列，但column_names中有wifi_token")
                    print("这可能导致列对应错位！")
                    
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

async def main():
    print("=" * 60)
    print("测试 get_user_wifi_config 函数")
    print("=" * 60)
    
    await test_get_user_wifi_config()
    
    print("\n" + "=" * 60)
    print("问题分析")
    print("=" * 60)
    print("问题: 在 get_user_wifi_config 函数中，column_names 包含 wifi_token 列")
    print("     但SQL查询中没有 SELECT wifi_token")
    print("     这导致列对应错位，wifi_base_url 可能被赋值为 wifi_mqtt_broker 的值")
    print()
    print("SQL查询列: wifi_username, wifi_password, wifi_apikey, wifi_base_url, wifi_mqtt_broker, username, role")
    print("column_names: wifi_username, wifi_password, wifi_apikey, wifi_token, wifi_base_url, wifi_mqtt_broker, username, role")
    print()
    print("修复方案:")
    print("1. 修改SQL查询，添加 wifi_token 列")
    print("2. 或者修改 column_names，移除 wifi_token 或调整顺序")
    print()
    print("当前错误: wifi_base_url 可能被赋值为 wifi_mqtt_broker 的值")

if __name__ == "__main__":
    asyncio.run(main())