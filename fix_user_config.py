#!/usr/bin/env python3
"""
修复用户配置
"""
import sqlite3

def check_and_fix_config():
    """检查并修复用户配置"""
    conn = sqlite3.connect('backend/data/wifi_esl.db')
    cursor = conn.cursor()
    
    # 查询当前配置
    cursor.execute('SELECT id, username, wifi_base_url, wifi_mqtt_broker, wifi_apikey FROM users WHERE id = 1')
    user = cursor.fetchone()
    
    print('=== 用户1 (admin) 配置检查 ===')
    print(f'  用户ID: {user[0]}')
    print(f'  用户名: {user[1]}')
    print(f'  wifi_base_url: {user[2]}')
    print(f'  wifi_mqtt_broker: {user[3]}')
    print(f'  wifi_apikey: {user[4][:16] if user[4] else "N/A"}...')
    
    # 检查配置
    issues = []
    fix_needed = False
    
    # 检查 wifi_base_url 是否正确
    if user[2] == 'mqtt://192.144.234.153:8883':
        issues.append('[ERROR] wifi_base_url 被错误设置为 MQTT broker 地址')
        issues.append('   当前: mqtt://192.144.234.153:8883')
        issues.append('   应为: http://192.144.234.153:4000')
        fix_needed = True
    elif user[2] != 'http://192.144.234.153:4000':
        issues.append(f'[WARNING] wifi_base_url 可能不正确: {user[2]}')
        issues.append('   应为: http://192.144.234.153:4000')
    
    # 检查 wifi_mqtt_broker 是否正确
    if user[3] != 'mqtt://192.144.234.153:8883':
        issues.append(f'[WARNING] wifi_mqtt_broker 可能不正确: {user[3]}')
        issues.append('   应为: mqtt://192.144.234.153:8883')
    
    if issues:
        print('\n[WARNING] 发现问题:')
        for issue in issues:
            print(f'  {issue}')
        
        if fix_needed:
            print('\n[FIXING] 正在修复配置...')
            
            # 更新配置
            cursor.execute('''
                UPDATE users 
                SET wifi_base_url = 'http://192.144.234.153:4000',
                    wifi_mqtt_broker = 'mqtt://192.144.234.153:8883'
                WHERE id = 1
            ''')
            conn.commit()
            print('[OK] 配置已修复！')
            
            # 再次查询验证
            cursor.execute('SELECT wifi_base_url, wifi_mqtt_broker FROM users WHERE id = 1')
            updated = cursor.fetchone()
            print(f'\n  更新后配置:')
            print(f'    wifi_base_url: {updated[0]}')
            print(f'    wifi_mqtt_broker: {updated[1]}')
        else:
            print('\n[INFO] 配置基本正确，不需要修复')
    else:
        print('\n[OK] 配置正确')
    
    conn.close()
    
    return fix_needed

def test_config_fix():
    """测试配置修复后是否正常工作"""
    import asyncio
    import sys
    sys.path.append("backend")
    
    print('\n' + '='*60)
    print('测试配置修复结果')
    print('='*60)
    
    try:
        from services.db_service_extended import get_user_wifi_config
        
        async def test():
            config = await get_user_wifi_config(1)
            print('修复后用户配置:')
            print(f'  wifi_base_url: {config.get("wifi_base_url")}')
            print(f'  wifi_mqtt_broker: {config.get("wifi_mqtt_broker")}')
            print(f'  wifi_apikey: {config.get("wifi_apikey", "")[:16] if config.get("wifi_apikey") else "N/A"}...')
            
            # 检查配置
            base_url = config.get('wifi_base_url', '')
            if base_url.startswith('http://') or base_url.startswith('https://'):
                print('  [OK] wifi_base_url 格式正确')
            else:
                print(f'  [ERROR] wifi_base_url 格式不正确: {base_url}')
                
            mqtt_broker = config.get('wifi_mqtt_broker', '')
            if mqtt_broker.startswith('mqtt://') or mqtt_broker.startswith('ws://') or mqtt_broker.startswith('wss://'):
                print('  [OK] wifi_mqtt_broker 格式正确')
            else:
                print(f'  [ERROR] wifi_mqtt_broker 格式不正确: {mqtt_broker}')
        
        asyncio.run(test())
    except Exception as e:
        print(f'测试失败: {e}')

if __name__ == "__main__":
    print('开始检查并修复用户配置...')
    fixed = check_and_fix_config()
    
    if fixed:
        test_config_fix()
        print('\n[OK] 配置修复完成！')
        print('请重新测试WIFI系统连接和模板推送功能。')
    else:
        print('\n[INFO] 配置检查完成，无需修复。')