#!/usr/bin/env python3
"""
MQTT 订阅测试程序
用于测试是否能正常接收 MQTT 消息
"""
import paho.mqtt.client as mqtt
import time
import json
import base64

# MQTT 配置
#BROKER_HOST = "192.168.1.172"
BROKER_HOST = "192.144.234.153"
BROKER_PORT = 8883
USERNAME = "W123456"
PASSWORD = "123456"
API_KEY = "cef24a6d1fffaf23d2eb72ff"
#API_KEY = "1429f05c2785912a6941a1e7"

# 订阅的主题列表
topics = [
    f"/client/{API_KEY}/action/online",
    f"/client/{API_KEY}/action/offline",
    f"/client/{API_KEY}/action/usb_state",
    f"/client/{API_KEY}/action/button",
    f"/client/{API_KEY}/action/battery_reply",
    f"/client/{API_KEY}/action/led_reply",
    f"/client/{API_KEY}/action/reboot_reply",
    f"/client/{API_KEY}/action/display_reply",
    f"/device/D43D3966B84C/10/button",
]

def on_connect(client, userdata, flags, reason_code, properties=None):
    """连接成功回调"""
    print(f"\n[连接状态] reason_code: {reason_code}")
    if reason_code == 0:
        print("[连接状态] ✅ MQTT 连接成功!")
        print(f"[连接状态] 正在订阅 {len(topics)} 个主题...")
        for topic in topics:
            result = client.subscribe(topic, qos=1)
            action_type = topic.split('/')[-1] if '/' in topic else topic
            print(f"[订阅] {action_type} -> {topic}")
    else:
        print(f"[连接状态] ❌ MQTT 连接失败，错误码: {reason_code}")

def on_message(client, userdata, msg):
    """消息到达回调"""
    topic = msg.topic
    payload = msg.payload
    
    # 解析主题
    prefix = f"/client/{API_KEY}/action/"
    if topic.startswith(prefix):
        action_type = topic[len(prefix):]
    else:
        action_type = topic
    
    # 解析消息内容
    print(f"\n{'='*60}")
    print(f"[收到消息] 主题: {topic}")
    print(f"[收到消息] 类型: {action_type}")
    print(f"[收到消息] 原始payload (hex): {payload.hex()[:100]}")
    print(f"[收到消息] 原始payload (str): {payload.decode('utf-8', errors='ignore')[:200]}")
    
    # 尝试 base64 解码
    try:
        decoded = base64.b64decode(payload).decode("utf-8")
        print(f"[收到消息] base64解码后: {decoded}")
        data = json.loads(decoded)
        print(f"[收到消息] JSON解析: {json.dumps(data, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"[收到消息] base64解码失败: {e}")
        # 尝试直接 JSON 解析
        try:
            data = json.loads(payload.decode("utf-8"))
            print(f"[收到消息] 直接JSON解析: {json.dumps(data, ensure_ascii=False, indent=2)}")
        except Exception as e2:
            print(f"[收到消息] JSON解析也失败: {e2}")
    print(f"{'='*60}")

def on_disconnect(client, userdata, flags, reason_code, properties=None):
    """断开连接回调"""
    print(f"\n[连接状态] ⚠️ MQTT 断开连接，原因码: {reason_code}")

def on_subscribe(client, userdata, mid, reason_codes, properties=None):
    """订阅成功回调"""
    print(f"[订阅确认] 订阅请求 mid={mid} 已确认, reason_codes={reason_codes}")

def main():
    print("="*60)
    print("MQTT 订阅测试程序")
    print("="*60)
    print(f"Broker: {BROKER_HOST}:{BROKER_PORT}")
    print(f"用户名: {USERNAME}")
    print(f"密码: {'*' * len(PASSWORD)}")
    print(f"API Key: {API_KEY}")
    print(f"订阅主题数: {len(topics)}")
    print("="*60)
    
    # 创建客户端
    client_id = f"test-mqtt-client-{int(time.time())}"
    print(f"\n[初始化] Client ID: {client_id}")
    
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=client_id,
        transport="tcp",
        protocol=mqtt.MQTTv311,
    )
    
    # 设置回调
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.on_subscribe = on_subscribe
    
    # 设置用户名密码
    client.username_pw_set(USERNAME, PASSWORD)
    print(f"[初始化] 用户名密码已设置 (用户名: {USERNAME})")
    
    # 连接 Broker
    print(f"\n[连接] 正在连接 {BROKER_HOST}:{BROKER_PORT} ...")
    try:
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
        print("[连接] connect() 调用成功")
    except Exception as e:
        print(f"[连接] ❌ 连接失败: {e}")
        return
    
    # 启动网络循环
    print("[连接] 启动网络循环，等待消息...")
    print("\n提示: 按 Ctrl+C 退出程序\n")
    
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n\n[退出] 收到中断信号，正在断开连接...")
        client.disconnect()
        print("[退出] 已断开连接")

if __name__ == "__main__":
    main()
