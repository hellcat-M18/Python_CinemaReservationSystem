from __future__ import annotations

import os
import sys
from getpass import getpass

KEY_USERNAME = "CINEMA_ADMIN_USERNAME"
KEY_PASSWORD = "CINEMA_ADMIN_PASSWORD"


def _project_root() -> str:
    # scripts/ の1つ上をプロジェクトルートとみなす
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# .env(あれば)のパス
def _env_path() -> str:
    return os.path.join(_project_root(), ".env")

# ファイルの読み書きユーティリティ
def _read_lines(path: str) -> list[str]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f]

# ファイルへ書き込み
def _write_lines(path: str, lines: list[str]) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for line in lines:
            f.write(line + "\n")

# key=value 行の追加・更新ユーティリティ
def _upsert_kv(lines: list[str], key: str, value: str) -> list[str]:
    # 既存の key= 行は削除し、末尾に追記（他の行は保持）
    kept = [ln for ln in lines if not ln.startswith(key + "=")]
    kept.append(f"{key}={value}")
    return kept

# メイン処理
def main(argv: list[str]) -> int:

    #環境変数はbat/shから渡す想定
    username = argv[1].strip() if len(argv) >= 2 else ""
    password = argv[2].strip() if len(argv) >= 3 else ""

    # 万一環境変数なしで呼ばれた場合はinputで取得する
    if not username:
        username = input("Admin username: ").strip()
    if not username:
        print("ERROR: username is required", file=sys.stderr)
        return 2

    if not password:
        password = getpass("Admin password: ").strip()
    if not password:
        print("ERROR: password is required", file=sys.stderr)
        return 2

    # .env ファイルを読み込み、更新して書き戻す
    env_file = _env_path()
    lines = _read_lines(env_file)
    
    # key=value 行の追加・更新
    lines = _upsert_kv(lines, KEY_USERNAME, username)
    lines = _upsert_kv(lines, KEY_PASSWORD, password)

    # 書き込み
    _write_lines(env_file, lines)

    # 完了メッセージ
    print(f"OK: updated {env_file}")
    print(f"  {KEY_USERNAME}={username}")
    print(f"  {KEY_PASSWORD}=********")
    return 0

# シェルから呼んだ時に終了コードを明示的に返す書き方
if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
