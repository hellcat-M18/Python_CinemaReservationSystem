from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    # 通常のインポートパス (例: python router.py)
    from db.models import Base
except ImportError:  # pragma: no cover
    # dbディレクトリ内から実行する場合のパス (例: python db/init_db.py)
    # 初期化時はこちらが動く
    from models import Base

DB_PATH = "cinema.db"                   # SQLiteのDBファイルパス
DATABASE_URL = f"sqlite:///{DB_PATH}"   # SQLiteの接続URL, この場合は相対パスで指定

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