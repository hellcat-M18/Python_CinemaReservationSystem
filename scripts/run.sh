#!/usr/bin/env bash
set -euo pipefail

# プロジェクトルートと仮想環境のPythonパス
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PY="$ROOT_DIR/.venv/bin/python"

PY="python3"

# venvがなければセットアップを実行
if [ ! -x "$VENV_PY" ]; then
    echo "venv not found. Running setup..."
    "$PY" "$ROOT_DIR/scripts/setup.py"
fi

# venvがあればvenvで実行、なければ通常Pythonで実行（Colabなど）
if [ -x "$VENV_PY" ]; then
    exec "$VENV_PY" "$ROOT_DIR/router.py"
else
    echo "NOTE: venv python not found. Running with: $PY" >&2
    exec "$PY" "$ROOT_DIR/router.py"
fi
