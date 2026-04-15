#!/usr/bin/env python3
"""
启动WIFI标签管理系统服务器
"""
import sys
import os
import subprocess
import time

def main():
    print("启动WIFI标签管理系统后端服务...")
    print("=" * 50)
    
    # 切换到backend目录
    backend_dir = os.path.join(os.path.dirname(__file__), "backend")
    os.chdir(backend_dir)
    
    # 使用虚拟环境中的Python
    venv_python = os.path.join(os.path.dirname(os.path.dirname(backend_dir)), "venv", "Scripts", "python.exe")
    
    if os.path.exists(venv_python):
        print(f"使用虚拟环境Python: {venv_python}")
        python_executable = venv_python
    else:
        print("使用系统Python")
        python_executable = sys.executable
    
    # 启动服务器
    print("启动服务器...")
    try:
        process = subprocess.Popen(
            [python_executable, "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            bufsize=1
        )
        
        # 读取前几行输出
        print("服务器输出:")
        for i in range(10):
            line = process.stdout.readline()
            if line:
                print(f"  {line.strip()}")
            else:
                break
        
        # 检查是否还在运行
        time.sleep(2)
        if process.poll() is None:
            print("\n[OK] 服务器已成功启动并运行")
            print("按Ctrl+C停止服务器")
            
            # 等待用户中断
            try:
                process.wait()
            except KeyboardInterrupt:
                print("\n停止服务器...")
                process.terminate()
                process.wait()
                print("服务器已停止")
        else:
            print("\n[ERROR] 服务器启动失败")
            stdout, stderr = process.communicate()
            print("标准错误输出:")
            print(stderr)
            
    except Exception as e:
        print(f"[ERROR] 启动服务器时发生异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()