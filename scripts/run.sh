#!/usr/bin/env bash
set -euo pipefail

# プロジェクトルートと仮想環境のPythonパス
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PY="$ROOT_DIR/.venv/bin/python"

# venvがなければセットアップを実行
if [ ! -x "$VENV_PY" ]; then
    echo "venv not found. Running setup..."
    if command -v python3 >/dev/null 2>&1; then
        python3 "$ROOT_DIR/scripts/setup.py"
    else
        python "$ROOT_DIR/scripts/setup.py"
    fi
fi

# venvのPythonが見つからなければエラー
if [ ! -x "$VENV_PY" ]; then
    echo "ERROR: venv python still not found: $VENV_PY" >&2
    exit 1
fi

# router.pyを実行
"$VENV_PY" "$ROOT_DIR/router.py"
