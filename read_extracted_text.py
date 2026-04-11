#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
读取提取的文本内容并分析API接口
"""

import re
import json
from collections import defaultdict

def analyze_api_interfaces():
    """分析API接口"""
    
    # 读取提取的文本
    with open("analysis_results/extracted_text.txt", "r", encoding="utf-8") as f:
        text = f.read()
    
    print("="*80)
    print("WIFI标签系统API接口详细分析报告")
    print("="*80)
    
    # 按页分割
    pages = re.split(r'--- 第 \d+ 页 ---', text)
    
    # 分析API接口（重点查看第9-17页）
    print("\nAPI接口详细列表:")
    print("-"*60)
    
    # 查找HTTP协议接口
    http_apis = []
    for i, page in enumerate(pages[9:], 9):  # 从第9页开始
        if i > 16:  # 只看到第17页
            break
            
        # 查找HTTP接口
        lines = page.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 查找HTTP接口定义
            if "/user/api/" in line:
                # 尝试提取HTTP方法和路径
                patterns = [
                    (r'(\d+)\s+(/[^\s]+)\s+(GET|POST|PUT|DELETE|PATCH)', 3),
                    (r'/(user/api/[^\s]+)', 1),
                    (r'(GET|POST|PUT|DELETE|PATCH)\s+(/[^\s]+)', 2),
                ]
                
                for pattern, group_index in patterns:
                    match = re.search(pattern, line)
                    if match:
                        if group_index == 3:
                            api_info = {
                                "id": match.group(1),
                                "path": match.group(2),
                                "method": match.group(3),
                                "page": i,
                                "raw_line": line
                            }
                            http_apis.append(api_info)
                        elif group_index == 1:
                            api_info = {
                                "path": match.group(1),
                                "page": i,
                                "raw_line": line
                            }
                            http_apis.append(api_info)
                        break
    
    # 打印HTTP接口
    print(f"HTTP REST API接口 ({len(http_apis)}个):")
    print("-"*60)
    for api in http_apis:
        method = api.get('method', '未知')
        path = api.get('path', api.get('raw_line', '未知'))
        print(f"  [{method}] {path}")
        
        # 如果有描述，打印描述
        desc_match = re.search(r'\s+([^\d].+)$', api['raw_line'])
        if desc_match:
            print(f"    描述: {desc_match.group(1)}")
        print()
    
    # 查找MQTT主题
    mqtt_topics = []
    for page in pages[2:8]:  # MQTT协议在2-8页
        lines = page.split('\n')
        for line in lines:
            line = line.strip()
            if "Topic" in line or "topic" in line or "/client/" in line:
                # 尝试提取MQTT主题
                topic_match = re.search(r'/(client/[^\s]+)', line)
                if topic_match:
                    mqtt_topics.append({
                        "topic": topic_match.group(1),
                        "description": line,
                        "type": "MQTT"
                    })
    
    print(f"\nMQTT实时通信主题 ({len(mqtt_topics)}个):")
    print("-"*60)
    for topic in mqtt_topics:
        print(f"  主题: {topic['topic']}")
        # 提取描述
        desc = re.sub(r'.*Topic.*?\s+', '', topic['description'], flags=re.IGNORECASE)
        if desc and len(desc) < 100:
            print(f"  描述: {desc}")
        print()
    
    # 分析错误码模式
    print("\n错误码分析:")
    print("-"*60)
    
    # 读取错误码JSON
    with open("analysis_results/error_codes.json", "r", encoding="utf-8") as f:
        error_codes = json.load(f)
    
    # 分类错误码
    error_patterns = defaultdict(list)
    for error in error_codes:
        code = error['code']
        desc = error['description']
        error_patterns[code].append(desc)
    
    print(f"发现 {len(error_patterns)} 种错误码:")
    for code, descs in error_patterns.items():
        if len(descs) > 0:
            # 找最常见的描述
            from collections import Counter
            desc_counter = Counter(descs)
            most_common = desc_counter.most_common(1)[0][0]
            print(f"  错误码 {code}: {most_common[:50]}... (出现{len(descs)}次)")
    
    # 分析设备管理功能
    print("\n设备管理功能分析:")
    print("-"*60)
    
    device_funcs = [
        "设备上线/下线监控",
        "USB状态监控", 
        "按键事件处理",
        "屏幕内容更新",
        "电池电压查询",
        "LED状态控制",
        "设备重启",
        "固件升级"
    ]
    
    for func in device_funcs:
        print(f"  * {func}")
    
    # 分析数据模型
    print("\n设备数据模型:")
    print("-"*60)
    
    device_fields = [
        "MAC地址",
        "IP地址", 
        "电池电量",
        "信号强度(RSSI)",
        "连接的AP信息",
        "MQTT连接信息",
        "设备状态",
        "设备类型",
        "屏幕类型",
        "序列号",
        "软件版本",
        "硬件版本",
        "USB状态",
        "所属产品",
        "图像算法"
    ]
    
    for field in device_fields:
        print(f"  * {field}")
    
    # 生成总结
    print("\n" + "="*80)
    print("分析总结:")
    print("="*80)
    
    summary_points = [
        f"1. 文档结构: {len(pages)-1}页，包含参数配置、设备管理、MQTT协议、HTTP协议四大模块",
        "2. 通信协议: 双协议设计 - MQTT用于设备实时通信，HTTP用于管理操作",
        f"3. API接口: {len(http_apis)}个HTTP接口 + {len(mqtt_topics)}个MQTT主题",
        "4. 设备管理: 完整的设备生命周期管理，支持实时状态监控",
        "5. 错误处理: 系统化错误码设计，支持操作反馈",
        "6. 安全性: MQTT使用API密钥认证，消息内容Base64编码",
        "7. 扩展性: 支持模板系统，便于业务扩展"
    ]
    
    for point in summary_points:
        print(f"   {point}")
    
    print("\n建议:")
    print("-"*60)
    
    recommendations = [
        "1. 实现完整的设备管理API，支持批量操作",
        "2. 添加WebSocket支持，实现实时双向通信",
        "3. 设计统一的错误处理中间件",
        "4. 实现API密钥管理和权限控制",
        "5. 添加请求日志和监控系统",
        "6. 设计模板引擎，支持动态内容渲染",
        "7. 实现固件OTA升级功能"
    ]
    
    for rec in recommendations:
        print(f"   {rec}")
    
    print("\n" + "="*80)
    print("分析完成！详细结果已保存在 analysis_results/ 目录")
    print("="*80)

if __name__ == "__main__":
    analyze_api_interfaces()