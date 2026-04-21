#!/usr/bin/env python3
"""
启动量化交易助手自我进化系统Web控制面板

使用方法:
    python start_webui.py [--port PORT] [--host HOST]

参数:
    --port PORT  服务器端口 (默认: 5001)
    --host HOST  服务器主机 (默认: 0.0.0.0)
"""

import sys
import os
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description='启动量化交易助手自我进化系统Web控制面板')
    parser.add_argument('--port', type=int, default=5001, help='服务器端口 (默认: 5001)')
    parser.add_argument('--host', default='0.0.0.0', help='服务器主机 (默认: 0.0.0.0)')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    args = parser.parse_args()
    
    # 切换到脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 检查虚拟环境
    venv_path = os.path.join(script_dir, 'venv')
    python_path = sys.executable
    
    if os.path.isdir(venv_path):
        print("检测到虚拟环境，使用虚拟环境Python...")
        # 尝试激活虚拟环境（通过使用虚拟环境的Python）
        venv_python = os.path.join(venv_path, 'bin', 'python')
        if os.path.isfile(venv_python):
            python_path = venv_python
        else:
            # Windows虚拟环境
            venv_python = os.path.join(venv_path, 'Scripts', 'python.exe')
            if os.path.isfile(venv_python):
                python_path = venv_python
    
    # 检查Flask是否安装
    try:
        subprocess.run([python_path, '-c', 'import flask'], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("Flask未安装，正在安装...")
        subprocess.run([python_path, '-m', 'pip', 'install', 'flask'], check=True)
    
    # 启动Web控制面板
    print(f"正在启动Web控制面板...")
    print(f"访问地址: http://{args.host}:{args.port}")
    print("按Ctrl+C停止服务器")
    
    # 运行模块
    cmd = [
        python_path,
        '-m', 'qtassist_self_evolution.webui.app',
        '--host', args.host,
        '--port', str(args.port)
    ]
    if args.debug:
        cmd.append('--debug')
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except subprocess.CalledProcessError as e:
        print(f"启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()