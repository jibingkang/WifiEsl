import sqlite3

def fix_user_config():
    """直接修复用户1的配置"""
    conn = sqlite3.connect('backend/data/wifi_esl.db')
    cursor = conn.cursor()
    
    # 检查当前配置
    cursor.execute('SELECT id, username, wifi_base_url, wifi_mqtt_broker FROM users WHERE id = 1')
    user = cursor.fetchone()
    
    print('[DEBUG] 当前配置:')
    print(f'  wifi_base_url: {user[2]}')
    print(f'  wifi_mqtt_broker: {user[3]}')
    
    # 修复配置
    if user[2] == 'mqtt://192.144.234.153:8883':
        print('[INFO] 发现错误配置，正在修复...')
        cursor.execute('''
            UPDATE users 
            SET wifi_base_url = 'http://192.144.234.153:4000',
                wifi_mqtt_broker = 'mqtt://192.144.234.153:8883'
            WHERE id = 1
        ''')
        conn.commit()
        print('[OK] 配置已修复')
        
        # 验证修复
        cursor.execute('SELECT wifi_base_url, wifi_mqtt_broker FROM users WHERE id = 1')
        updated = cursor.fetchone()
        print('[DEBUG] 修复后配置:')
        print(f'  wifi_base_url: {updated[0]}')
        print(f'  wifi_mqtt_broker: {updated[1]}')
    else:
        print('[INFO] 配置正确，无需修复')
    
    conn.close()
    return True

if __name__ == "__main__":
    print("开始修复用户配置...")
    fix_user_config()
    print("完成。")