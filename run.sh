#!/bin/bash

# A股高股息率工具启动脚本

echo "正在安装依赖..."
pip install -r requirements.txt

echo ""
echo "启动服务..."
echo "后端API: http://localhost:8000"
echo "前端页面: http://localhost:8000/index.html"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

uvicorn app:app --host 0.0.0.0 --port 8000 --reload
