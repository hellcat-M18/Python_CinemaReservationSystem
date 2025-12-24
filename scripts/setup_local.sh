#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
PY="$VENV_DIR/bin/python"

if [ ! -x "$PY" ]; then
  python3 -m venv "$VENV_DIR"
fi

"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r "$ROOT_DIR/requirements.txt"

echo "OK: local venv is ready."
