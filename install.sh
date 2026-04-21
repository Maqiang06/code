#!/bin/bash
# 量化交易助手自我进化系统 - 安装脚本

set -e

echo "========================================"
echo "量化交易助手自我进化系统 安装程序"
echo "版本: 1.0.0"
echo "========================================"

# 检查Python版本
echo "检查Python版本..."
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "检测到 Python $python_version"

if [[ $(python3 -c "import sys; print(sys.version_info < (3, 8))") == "True" ]]; then
    echo "错误: 需要 Python 3.8 或更高版本"
    exit 1
fi

# 检查pip
echo "检查pip..."
if ! command -v pip3 &> /dev/null; then
    echo "错误: pip3 未找到，请先安装 pip"
    exit 1
fi

# 安装选项
echo ""
echo "安装选项:"
echo "1. 基础安装 (仅核心功能)"
echo "2. 完全安装 (包含Web界面和机器学习功能)"
echo "3. 开发环境安装 (包含所有开发工具)"
read -p "请选择安装选项 (1/2/3, 默认:2): " install_option
install_option=${install_option:-2}

# 创建虚拟环境（可选）
read -p "是否创建虚拟环境? (y/n, 默认:y): " create_venv
create_venv=${create_venv:-y}

if [[ $create_venv == "y" ]]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    echo "虚拟环境已激活"
fi

# 安装包
echo "安装qtassist-self-evolution包..."

case $install_option in
    1)
        echo "执行基础安装..."
        pip3 install -e .
        ;;
    2)
        echo "执行完全安装..."
        pip3 install -e .[all]
        ;;
    3)
        echo "执行开发环境安装..."
        pip3 install -e .[all,dev]
        ;;
    *)
        echo "无效选项，使用完全安装..."
        pip3 install -e .[all]
        ;;
esac

# 验证安装
echo ""
echo "验证安装..."
if python3 -c "import qtassist_self_evolution; print('✓ qtassist_self_evolution 导入成功')"; then
    echo "✓ 包安装成功"
else
    echo "✗ 包安装失败"
    exit 1
fi

# 检查命令行工具
echo ""
echo "检查命令行工具..."
if command -v qtassist-evolution &> /dev/null; then
    echo "✓ 命令行工具已安装"
    echo "使用方法: qtassist-evolution --help"
else
    echo "命令行工具未找到，请检查PATH"
fi

# 创建数据目录
echo ""
echo "创建数据目录..."
mkdir -p data logs

# 显示后续步骤
echo ""
echo "========================================"
echo "安装完成!"
echo "========================================"
echo ""
echo "下一步:"
echo "1. 初始化系统: qtassist-evolution init"
echo "2. 启动Web控制面板: qtassist-evolution web"
echo "3. 查看帮助: qtassist-evolution --help"
echo ""
echo "文档:"
echo "- 用户指南: 查看 docs/USAGE.md"
echo "- API文档: 查看 docs/API.md"
echo ""
if [[ $create_venv == "y" ]]; then
    echo "注意: 虚拟环境已激活，退出后使用以下命令激活:"
    echo "source venv/bin/activate"
fi
echo "========================================"