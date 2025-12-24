#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$PY" ]; then
  echo "venv not found. Run scripts/setup_local.sh first."
  exit 1
fi

"$PY" "$ROOT_DIR/router.py"
