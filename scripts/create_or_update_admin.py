from __future__ import annotations

"""管理者ユーザーの追加/更新(DBリセットなし)。

役割の分離(シンプル版):
- scripts/set_admin_env.py: .env に値を書くだけ
- このスクリプト: .env(または環境変数)を読み、DB(users)へ反映するだけ

注意:
- DBファイルが未生成の場合は中断(abort)する
"""

import os
import sys
from datetime import datetime

# プロジェクトルートのパス
def _project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# DBファイルのパス
def _db_path() -> str:
    return os.path.join(_project_root(), "cinema.db")

# .env(あれば)のパス
def _env_path() -> str:
    return os.path.join(_project_root(), ".env")

# .env(あれば)を読み込む
def _load_dotenv_if_exists() -> None:
    env_file = _env_path()
    if not os.path.exists(env_file):
        return
    try:
        from dotenv import load_dotenv

        load_dotenv(env_file, override=False)
    except Exception:
        return


def main() -> int:
    # 1) DB未生成なら中断
    if not os.path.exists(_db_path()):
        print("ERROR: cinema.db が見つかりません(DB未生成)。")
        print("  先に `python db/init_db.py` を実行してDBを作成してください。")
        return 1

    # 2) .env(あれば)を読み込んでから環境変数を参照
    _load_dotenv_if_exists()

    # 環境変数から管理者ユーザー名/パスワードを取得
    username = (os.environ.get("CINEMA_ADMIN_USERNAME") or "").strip()
    password = (os.environ.get("CINEMA_ADMIN_PASSWORD") or "").strip()
    if not username or not password:
        print("ERROR: CINEMA_ADMIN_USERNAME / CINEMA_ADMIN_PASSWORD が未設定です。")
        print("  先に `scripts/set_admin_env.(bat|sh)` か `python scripts/set_admin_env.py` で .env を更新してください。")
        return 2

    # 3) DBへ反映(upsert)
    from sqlalchemy import select

    from db.db import SessionLocal
    from db.models import User
    from utils.auth import hash_password

    now = datetime.now().strftime("%Y-%m-%dT%H:%M")

    # 管理者ユーザーの作成または更新
    try:
        with SessionLocal() as db_session:
            user = db_session.execute(select(User).where(User.username == username)).scalar_one_or_none()
            if user is None:
                user = User(
                    username=username,
                    password_hash=hash_password(password),
                    role="Admin",
                    created_at=now,
                )
                db_session.add(user)
            else:
                user.password_hash = hash_password(password)
                user.role = "Admin"

            db_session.commit()
    
    # DBが古い/未初期化の場合の例外対策
    except Exception as exc:
        print(f"ERROR: DB更新に失敗しました: {exc}")
        print("  DBが古い/未初期化の可能性があります。`python db/init_db.py` を実行してください。")
        return 3

    print("OK: admin user upserted")
    print(f"  username={username}")
    return 0

# シェルから呼んだ時に終了コードを明示的に返す書き方
if __name__ == "__main__":
    raise SystemExit(main())
