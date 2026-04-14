#!/usr/bin/env python3
"""
启动后端服务并进行简单测试
"""
import subprocess
import time
import os
import sys
import threading
import atexit
import signal

def start_backend():
    """启动后端服务"""
    print("=== 启动WIFI标签管理系统后端服务 ===")
    
    # 切换到backend目录
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    print(f"工作目录: {backend_dir}")
    
    # 启动FastAPI服务
    cmd = [sys.executable, "main.py"]
    
    # 设置环境变量，确保加载正确的.env文件
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.dirname(backend_dir) + os.pathsep + env.get("PYTHONPATH", "")
    
    print(f"启动命令: {' '.join(cmd)}")
    print("服务将在后台启动...")
    print("日志将输出到控制台和 wifi_esl_debug.log 文件")
    
    # 启动服务进程
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
        env=env
    )
    
    # 注册退出时清理
    def cleanup():
        print("\n正在停止后端服务...")
        process.terminate()
        process.wait(timeout=5)
        
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, lambda sig, frame: cleanup())
    signal.signal(signal.SIGTERM, lambda sig, frame: cleanup())
    
    # 读取并打印输出
    def read_output():
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                print(f"[BACKEND] {line.rstrip()}")
    
    # 启动输出读取线程
    output_thread = threading.Thread(target=read_output, daemon=True)
    output_thread.start()
    
    # 等待服务启动
    print("等待服务启动...")
    time.sleep(5)
    
    # 检查服务是否运行
    import urllib.request
    try:
        response = urllib.request.urlopen("http://127.0.0.1:8001/health", timeout=5)
        if response.status == 200:
            print("✅ 后端服务启动成功!")
            return process
        else:
            print(f"⚠️  服务返回状态码: {response.status}")
    except Exception as e:
        print(f"❌ 服务可能未启动或无法访问: {e}")
    
    return process

def simple_test():
    """简单的HTTP测试"""
    import urllib.request
    import json
    
    print("\n=== 执行简单测试 ===")
    
    # 测试健康检查
    try:
        req = urllib.request.Request("http://127.0.0.1:8001/health")
        response = urllib.request.urlopen(req, timeout=10)
        data = json.loads(response.read())
        print(f"健康检查: ✅ {data}")
    except Exception as e:
        print(f"健康检查失败: ❌ {e}")
        return False
    
    # 测试根路径
    try:
        req = urllib.request.Request("http://127.0.0.1:8001/")
        response = urllib.request.urlopen(req, timeout=10)
        data = json.loads(response.read())
        print(f"根路径访问: ✅ {data}")
    except Exception as e:
        print(f"根路径访问失败: ❌ {e}")
    
    return True

if __name__ == "__main__":
    print("WIFI标签管理系统 - 诊断工具")
    print("=" * 50)
    
    # 检查配置
    print("\n[1] 检查配置...")
    try:
        import config
        settings = config.settings
        print(f"WIFI_BASE_URL: {settings.wifi_base_url}")
        print(f"WIFI_USERNAME: {settings.wifi_username}")
        print(f"WIFI_APIKEY长度: {len(settings.wifi_apikey)} 字符")
        print(f"BACKEND_PORT: {settings.backend_port}")
    except Exception as e:
        print(f"配置加载失败: {e}")
        sys.exit(1)
    
    # 启动服务
    print("\n[2] 启动后端服务...")
    backend_process = start_backend()
    
    if backend_process:
        # 简单测试
        print("\n[3] 执行简单测试...")
        if simple_test():
            print("\n✅ 服务正常运行!")
            print("现在可以:")
            print("1. 查看日志文件: backend/wifi_esl_debug.log")
            print("2. 打开浏览器访问: http://localhost:8001")
            print("3. 前端连接: http://localhost:3000")
            print("\n按 Ctrl+C 停止服务")
            
            # 等待用户中断
            try:
                backend_process.wait()
            except KeyboardInterrupt:
                print("\n收到中断信号，正在停止服务...")
                backend_process.terminate()
        else:
            print("\n❌ 测试失败，请检查日志")
            backend_process.terminate()
    else:
        print("\n❌ 服务启动失败")