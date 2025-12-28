#!/usr/bin/env bash
set -euo pipefail

# プロジェクトルートと仮想環境のPythonパス
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PY="$ROOT_DIR/.venv/bin/python"

# venvのPythonが見つからなければエラー
if [ ! -x "$VENV_PY" ]; then
    cho "ERROR: venv not found. Run bash scripts/run.sh or python3 scripts/setup.py first." >&2
    exit 1
fi

# seed_sample_data.pyを実行
"$VENV_PY" "$ROOT_DIR/scripts/seed_sample_data.py"
