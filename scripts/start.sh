#!/bin/bash
set -Eeuo pipefail

COZE_WORKSPACE_PATH="${COZE_WORKSPACE_PATH:-$(pwd)}"

PORT=5000
DEPLOY_RUN_PORT="${DEPLOY_RUN_PORT:-$PORT}"

# 启动 Python 后端
PYTHON_PORT=8001
cd "${COZE_WORKSPACE_PATH}/server/python"
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port ${PYTHON_PORT} --log-level info > /app/work/logs/bypass/python-backend.log 2>&1 &
echo "Python backend PID: $!"

start_service() {
    cd "${COZE_WORKSPACE_PATH}"
    echo "Starting express production server on port ${DEPLOY_RUN_PORT}..."
    PYTHON_PORT=${PYTHON_PORT} PORT=$DEPLOY_RUN_PORT node dist-server/server.js
}

echo "Starting express production server on port ${DEPLOY_RUN_PORT}..."
start_service
