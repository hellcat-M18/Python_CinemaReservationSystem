#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------
# 管理者アカウント用の設定を「プロジェクト直下の .env」に書き込む
# - .env は gitignore 済み（秘密情報をコミットしない）
# - db/db.py が起動時に .env を自動で読み込みます
#
# 使い方（推奨: 対話）:
#   bash scripts/set_admin_env.sh
#
# 引数も可:
#   bash scripts/set_admin_env.sh admin mypass
# ------------------------------------------------------------

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$PY" ]; then
  echo "venv not found. Run scripts/setup_local.sh first."
  exit 1
fi

"$PY" "$ROOT_DIR/scripts/set_admin_env.py" "${1:-}" "${2:-}"
