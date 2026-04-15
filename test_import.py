#!/usr/bin/env python3
"""
测试db_service的导入
"""
import sys
import os

# 添加backend到路径
backend_dir = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, backend_dir)

print("测试db_service导入...")

try:
    from services.db_service import encrypt_wifi_password, decrypt_wifi_password
    print("✅ db_service导入成功")
    
    # 测试加密解密
    test_password = "test_password_123"
    encrypted = encrypt_wifi_password(test_password)
    print(f"加密结果: {encrypted}")
    
    decrypted = decrypt_wifi_password(encrypted)
    print(f"解密结果: {decrypted}")
    
    if decrypted == test_password:
        print("✅ 加密解密功能正常")
    else:
        print(f"❌ 加密解密不匹配: 原始='{test_password}', 解密='{decrypted}'")
        
except ImportError as e:
    print(f"❌ 导入失败: {e}")
except Exception as e:
    print(f"❌ 测试过程中发生异常: {e}")
    import traceback
    traceback.print_exc()