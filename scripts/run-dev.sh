#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
HOST="${SERVER_HOST:-127.0.0.1}"
PORT="${SERVER_PORT:-8080}"
export AI_PROVIDER="${AI_PROVIDER:-ollama}"
export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
export OLLAMA_MODEL="${OLLAMA_MODEL:-mindbridge-qwen2.5-7b-ft:latest}"
exec uvicorn app.main:app --host "$HOST" --port "$PORT"

# app.main: 模块位置
# app： 模块里的变量名冒号后的 app 是该模块中的变量，指向一个 FastAPI 应用对象。
# 这段命令告诉 Uvicorn 去哪里取得对象；创建对象的是 Python 代码。
