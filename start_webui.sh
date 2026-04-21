#!/bin/bash
# 启动量化交易助手自我进化系统Web控制面板

set -e

cd "$(dirname "$0")"

# 检查虚拟环境
if [ -d "venv" ]; then
    echo "使用虚拟环境..."
    source venv/bin/activate
elif [ -f "pyproject.toml" ]; then
    echo "使用当前Python环境..."
else
    echo "错误: 未找到虚拟环境，请先运行 ./install.sh"
    exit 1
fi

# 检查Flask是否安装
if ! python -c "import flask" 2>/dev/null; then
    echo "Flask未安装，正在安装..."
    pip install flask
fi

# 启动Web控制面板
echo "正在启动Web控制面板..."
echo "访问地址: http://localhost:5001"
echo "按Ctrl+C停止服务器"

# 运行模块
python -m qtassist_self_evolution.webui.app --host 0.0.0.0 --port 5001