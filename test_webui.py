#!/usr/bin/env python3
"""
测试WebUI是否正常工作
"""

import subprocess
import time
import sys
import os
import requests

def main():
    # 切换到项目根目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 使用虚拟环境Python
    python_path = os.path.join('venv', 'bin', 'python')
    if not os.path.isfile(python_path):
        python_path = sys.executable
    
    # 启动服务器
    cmd = [python_path, '-m', 'qtassist_self_evolution.webui.app', '--host', '127.0.0.1', '--port', '5001']
    print(f"启动服务器: {' '.join(cmd)}")
    
    # 在后台启动服务器
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # 等待服务器启动
    print("等待服务器启动...")
    time.sleep(3)
    
    # 检查进程是否仍在运行
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        print(f"服务器启动失败:\n标准输出: {stdout.decode()}\n标准错误: {stderr.decode()}")
        return 1
    
    try:
        # 测试主页
        print("测试主页访问...")
        response = requests.get('http://127.0.0.1:5001/', timeout=5)
        if response.status_code == 200:
            print("✓ 主页访问成功")
        else:
            print(f"✗ 主页访问失败: 状态码 {response.status_code}")
            return 1
        
        # 测试API状态端点
        print("测试API状态端点...")
        response = requests.get('http://127.0.0.1:5001/api/system/status', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ API状态端点成功: {data.get('status', '未知')}")
        else:
            print(f"✗ API状态端点失败: 状态码 {response.status_code}")
            return 1
        
        print("所有测试通过！WebUI工作正常。")
        
    except requests.exceptions.RequestException as e:
        print(f"网络请求失败: {e}")
        return 1
    finally:
        # 停止服务器
        print("停止服务器...")
        process.terminate()
        process.wait(timeout=5)
        print("服务器已停止")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())