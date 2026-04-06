#!/bin/bash

# 颜色输出辅助函数
info() { echo -e "\033[32m[INFO]\033[0m $1"; }
warn() { echo -e "\033[33m[WARN]\033[0m $1"; }
error() { echo -e "\033[31m[ERROR]\033[0m $1"; }

# 1. 查找可用的 Python 命令
if command -v python3 &> /dev/null; then
    python_cmd="python3"
elif command -v python &> /dev/null; then
    python_cmd="python"
else
    error "此计算机不存在 Python，请先安装。"
    echo "Debian/Ubuntu: sudo apt install python3"
    echo "CentOS: sudo yum install python3"
    echo "macOS: brew install python3"
    exit 1
fi

# 2. 检查是否已处于虚拟环境中
if [[ -z "$VIRTUAL_ENV" ]]; then
    warn "未检测到虚拟环境。"
    
    # 尝试使用 uv 创建虚拟环境（如果 uv 已安装）
    if command -v uv &> /dev/null; then
        info "检测到 uv，正在创建虚拟环境..."
        uv venv
        source .venv/bin/activate
    # 否则使用 python -m venv 创建
    elif $python_cmd -m venv .venv &> /dev/null; then
        info "正在使用 venv 创建虚拟环境..."
        source .venv/bin/activate
    else
        error "无法创建虚拟环境 (缺少 venv 模块)。"
        error "尝试安装到系统环境 (不推荐，可能会触发 PEP 668 错误)。"
        
        # 查找 pip
        if command -v pip3 &> /dev/null; then
            pip_cmd="pip3"
        elif command -v pip &> /dev/null; then
            pip_cmd="pip"
        else
            pip_cmd="$python_cmd -m pip"
        fi

        # 强制安装参数
        pip_args="--break-system-packages"
    fi
fi

# 3. 确定使用的 pip 命令
# 如果已经在虚拟环境中，直接使用 pip 即可，不需要指定 python3 -m pip
if [[ -n "$VIRTUAL_ENV" ]]; then
    pip_cmd="pip"
    pip_args=""
fi

# 4. 检查并安装 uv
if ! command -v uv &> /dev/null; then
    info "未检测到 uv，正在安装..."
    if ! $pip_cmd install uv $pip_args; then
        error "uv 安装失败。"
        exit 1
    fi
fi

# 5. 运行主程序
info "正在运行 main.py..."
$python_cmd -m uv run main.py