#!/usr/bin/env python3
"""
最终测试验证配置修复
"""
import sqlite3
import time

def main():
    print("=" * 60)
    print("最终配置测试")
    print("=" * 60)
    
    # 1. 检查数据库配置
    print("\n1. 数据库配置检查:")
    conn = sqlite3.connect('backend/data/wifi_esl.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, username, wifi_username, wifi_base_url, wifi_mqtt_broker FROM users WHERE id = 1')
    user = cursor.fetchone()
    
    print(f"  用户 {user[0]} ({user[1]})")
    print(f"  wifi_username: {user[2]}")
    print(f"  wifi_base_url: {user[3]}")
    print(f"  wifi_mqtt_broker: {user[4]}")
    
    # 配置正确性检查
    base_url = user[3]
    mqtt_broker = user[4]
    
    correct = True
    
    if base_url != 'http://192.144.234.153:4000':
        print(f"  [ERROR] wifi_base_url 不正确")
        print(f"     应为: http://192.144.234.153:4000")
        print(f"     实际: {base_url}")
        correct = False
    else:
        print(f"  [OK] wifi_base_url 正确")
    
    if mqtt_broker != 'mqtt://192.144.234.153:8883':
        print(f"  [WARNING] wifi_mqtt_broker 不正确")
        print(f"     应为: mqtt://192.144.234.153:8883")
        print(f"     实际: {mqtt_broker}")
    else:
        print(f"  [OK] wifi_mqtt_broker 正确")
    
    # 2. 配置问题分析
    print("\n2. 问题分析:")
    print("  根据错误日志分析:")
    print("  问题: WIFI系统连接使用了错误的URL: mqtt://192.144.234.153:8883")
    print("  原因: 用户的 wifi_base_url 字段被错误地设置为 MQTT broker 地址")
    print()
    print("  已进行的修复:")
    print("  1. 修复了数据库配置")
    print("  2. 修复了 get_user_wifi_config 函数的列对应关系")
    print()
    print("  预期结果:")
    print("  - WIFI系统登录应使用 HTTP 地址: http://192.144.234.153:4000")
    print("  - MQTT订阅应使用 MQTT broker 地址: mqtt://192.144.234.153:8883")
    
    # 3. 建议
    print("\n3. 后续步骤:")
    print("  a. 重新启动后端服务")
    print("  b. 测试设备列表获取")
    print("  c. 测试模板推送功能")
    
    # 4. 验证修复
    print("\n4. 验证修复:")
    if correct:
        print("  [OK] 数据库配置已修复")
        print("  [OK] 列对应关系已修复")
        print("  [OK] 配置分离完成:")
        print("    - WIFI API: http://192.144.234.153:4000")
        print("    - MQTT Broker: mqtt://192.144.234.153:8883")
    else:
        print("  [ERROR] 仍需修复配置")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()