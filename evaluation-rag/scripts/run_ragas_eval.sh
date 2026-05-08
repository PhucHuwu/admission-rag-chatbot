#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

if [ -f "$ROOT_DIR/evaluation-rag/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/evaluation-rag/.env"
  set +a
fi

BASE_URL="${EVAL_BASE_URL:-http://localhost:8000}"
SEARCH_ENDPOINT="${EVAL_SEARCH_ENDPOINT:-/api/v1/search}"
CHAT_ENDPOINT="${EVAL_CHAT_ENDPOINT:-/api/v1/chat}"
DATASET_PATH="${EVAL_DATASET_PATH:-evaluation-rag/dataset/query_set.v1.json}"
TOP_K_CONTEXT="${EVAL_TOP_K_CONTEXT:-5}"
TIMEOUT_SEC="${EVAL_TIMEOUT_SEC:-30}"
JUDGE_MODEL="${JUDGE_MODEL:-gpt-4o-mini}"

if [ -z "${OPENAI_API_KEY:-}" ]; then
  echo "Missing OPENAI_API_KEY. Set it in evaluation-rag/.env" >&2
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python executable '$PYTHON_BIN' not found. Set PYTHON_BIN or install python3." >&2
  exit 1
fi

"$PYTHON_BIN" "$ROOT_DIR/evaluation-rag/scripts/ragas_eval.py" \
  --base-url "$BASE_URL" \
  --search-endpoint "$SEARCH_ENDPOINT" \
  --chat-endpoint "$CHAT_ENDPOINT" \
  --input "$DATASET_PATH" \
  --top-k "$TOP_K_CONTEXT" \
  --timeout "$TIMEOUT_SEC" \
  --judge-model "$JUDGE_MODEL"
