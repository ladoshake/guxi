#!/bin/bash
set -Eeuo pipefail

PORT="${PORT:-5000}"
COZE_WORKSPACE_PATH="${COZE_WORKSPACE_PATH:-$(pwd)}"
DEPLOY_RUN_PORT="${DEPLOY_RUN_PORT:-${PORT}}"

cd "${COZE_WORKSPACE_PATH}"

kill_port_if_listening() {
    local pids
    pids=$(ss -H -lntp 2>/dev/null | awk -v port="${1}" '$4 ~ ":"port"$"' | grep -o 'pid=[0-9]*' | cut -d= -f2 | paste -sd' ' - || true)
    if [[ -z "${pids}" ]]; then
      echo "Port ${1} is free."
      return
    fi
    echo "Port ${1} in use by PIDs: ${pids} (SIGKILL)"
    echo "${pids}" | xargs -I {} kill -9 {}
    sleep 1
}

# 启动 Python 后端（端口 8001）
PYTHON_PORT=8001
echo "Starting Python FastAPI backend on port ${PYTHON_PORT}..."
kill_port_if_listening "${PYTHON_PORT}"
cd "${COZE_WORKSPACE_PATH}/server/python"
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port ${PYTHON_PORT} --log-level info > /Users/green/Desktop/guxi-projects/logs/python-backend.log 2>&1 &
echo "Python backend PID: $!"

cd "${COZE_WORKSPACE_PATH}"

echo "Clearing port ${DEPLOY_RUN_PORT} before start."
kill_port_if_listening "${DEPLOY_RUN_PORT}"
echo "Starting express + Vite dev server on port ${DEPLOY_RUN_PORT}..."

PYTHON_PORT=${PYTHON_PORT} PORT=${DEPLOY_RUN_PORT} pnpm tsx watch server/server.ts
