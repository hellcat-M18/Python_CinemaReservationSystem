from __future__ import annotations

import os
from datetime import datetime

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    # 通常のインポートパス (例: python router.py)
    from db.models import Base
except ImportError:  # pragma: no cover
    # dbディレクトリ内から実行する場合のパス (例: python db/init_db.py)
    # 初期化時はこちらが動く
    from models import Base

# DBファイルのパスと接続URLの設定
_ROOT_DIR = Path(__file__).resolve().parent.parent  # プロジェクトルート
DB_PATH = str((_ROOT_DIR / "cinema.db").resolve())  # DBファイルの絶対パス
DATABASE_URL = f"sqlite:///{Path(DB_PATH).as_posix()}" # SQLiteの接続URL


def _load_dotenv_if_exists() -> None:
    """プロジェクトルートの .env を（あれば）読み込む。

    - .env はローカル設定用（管理者アカウントなど）
    - python-dotenv が未インストールでも動作は継続する（単に読み込めないだけ）
    """

    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    if not os.path.exists(env_path):
        return

    try:
        from dotenv import load_dotenv

        load_dotenv(env_path, override=False)
    except Exception:
        return


_load_dotenv_if_exists()

# engine: DBへの接続口みたいなもの, SQLAlchemyのコア部分
engine = create_engine(
    DATABASE_URL,
    echo=False,    # SQLログ見たいなら True
    future=True,   # 2.0スタイルを有効にするオプション
)
# DB操作用のセッションを作るためのクラス
# セッション: DB操作の単位, やり取りを管理する
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# DB初期化関数: テーブルを作成する
def init_db() -> None:
    Base.metadata.create_all(engine)


def reset_db(remove_file: bool = True) -> None:
    # DBの作り直し

    if remove_file and os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    # テーブル作成
    Base.metadata.create_all(engine)

    # 環境変数から管理者ユーザーを作成
    admin_username = (os.environ.get("CINEMA_ADMIN_USERNAME") or "").strip()
    admin_password = (os.environ.get("CINEMA_ADMIN_PASSWORD") or "").strip()
    if not admin_username or not admin_password:
        return

    # 初期化時のみ必要な依存なので遅延import（依存を最小化・将来の循環/重依存対策）
    from sqlalchemy import select

    from db.models import User
    from utils.auth import hash_password

    # 管理者ユーザーの作成
    with SessionLocal() as db_session:
        existing = db_session.execute(select(User).where(User.username == admin_username)).scalar_one_or_none()
        if existing is not None:
            return

        user = User(
            username=admin_username,
            password_hash=hash_password(admin_password),
            role="Admin",
            created_at=datetime.now().strftime("%Y-%m-%dT%H:%M"),
        )
        db_session.add(user)
        db_session.commit()