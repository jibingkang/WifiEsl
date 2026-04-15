#!/usr/bin/env python3
"""
直接检查用户配置
"""
import sqlite3
import sys
import os

def check_db_config():
    """直接查询数据库"""
    db_path = "backend/data/wifi_esl.db"
    print(f"检查数据库: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. 检查users表结构
    print("\n1. users表结构:")
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # 2. 检查用户数据
    print("\n2. 用户配置数据:")
    cursor.execute("SELECT id, username, wifi_username, wifi_base_url, wifi_mqtt_broker, wifi_apikey, wifi_token FROM users")
    users = cursor.fetchall()
    
    for user in users:
        user_id, username, wifi_username, wifi_base_url, wifi_mqtt_broker, wifi_apikey, wifi_token = user
        print(f"\n用户 {user_id} ({username}):")
        print(f"  wifi_username: {wifi_username}")
        print(f"  wifi_base_url: {wifi_base_url}")
        print(f"  wifi_mqtt_broker: {wifi_mqtt_broker}")
        print(f"  wifi_apikey: {wifi_apikey[:16] if wifi_apikey else 'N/A'}")
        print(f"  wifi_token: {wifi_token[:16] if wifi_token else 'N/A'}")
        
        # 检查URL格式
        if wifi_base_url and wifi_base_url.startswith('mqtt://'):
            print(f"  ⚠️  ERROR: wifi_base_url 应该是HTTP协议: {wifi_base_url}")
        
        if wifi_mqtt_broker and (wifi_mqtt_broker.startswith('http://') or wifi_mqtt_broker.startswith('https://')):
            print(f"  ⚠️  ERROR: wifi_mqtt_broker 应该是MQTT/WS协议: {wifi_mqtt_broker}")
    
    conn.close()
    
    # 3. 检查 .env 配置
    print("\n" + "="*60)
    print("3. 后端 .env 文件配置:")
    env_file = "backend/.env"
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    print(f"  {line.strip()}")
    else:
        print(f"  .env 文件不存在: {env_file}")

if __name__ == "__main__":
    print("=" * 60)
    print("用户配置调试工具")
    print("=" * 60)
    
    try:
        check_db_config()
    except Exception as e:
        print(f"检查过程中出错: {e}")
        import traceback
        traceback.print_exc()