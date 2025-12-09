#!/bin/bash

# 文件处理转换系统启动脚本

echo "================================"
echo "文件处理转换系统"
echo "================================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: Python3 未安装"
    echo "请先安装Python 3.8或更高版本"
    exit 1
fi

# 检查配置文件
if [ ! -f "config.yaml" ]; then
    echo "错误: config.yaml 配置文件不存在"
    echo "请先创建配置文件并填入Unstructured API密钥"
    exit 1
fi

# 检查并创建虚拟环境
if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python3 -m venv venv
    echo "✓ 虚拟环境创建完成"
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装依赖包..."
pip install -r requirements.txt > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✓ 依赖安装完成"
else
    echo "✗ 依赖安装失败,尝试升级pip后重试..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

echo ""
echo "================================"
echo "启动服务..."
echo "================================"
echo ""

# 启动应用
python main.py
