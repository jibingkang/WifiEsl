#!/usr/bin/env python3
"""
测试Crypto模块是否安装正确
"""
import sys

print("测试Crypto模块...")

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
    print("✅ Crypto模块导入成功")
    
    # 测试加密解密
    key = b'1234567890123456'  # 16字节密钥
    cipher = AES.new(key, AES.MODE_CBC)
    data = b"test data"
    
    ct_bytes = cipher.encrypt(pad(data, AES.block_size))
    iv = cipher.iv
    
    cipher2 = AES.new(key, AES.MODE_CBC, iv)
    pt = unpad(cipher2.decrypt(ct_bytes), AES.block_size)
    
    if pt == data:
        print("✅ AES加密解密测试通过")
    else:
        print("❌ AES加密解密测试失败")
        
except ImportError as e:
    print(f"❌ Crypto模块导入失败: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 测试过程中发生异常: {e}")
    sys.exit(1)

print("所有测试通过！")