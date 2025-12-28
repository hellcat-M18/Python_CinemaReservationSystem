from __future__ import annotations

from passlib.context import CryptContext

# パスワードハッシュ化と検証用ユーティリティ関数
# NOTE:
# - bcrypt は passlib と bcrypt 本体のバージョン組み合わせによって
#   互換性問題が出ることがある（Python 3.13 + bcrypt最新版など）。
# - pbkdf2_sha256 は Python 標準の hashlib を使うため追加依存がなく安定。
_pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# パスワードをハッシュ化して返す
def hash_password(password: str) -> str:
    return _pwd_context.hash(password)

# パスワードとハッシュを比較して検証する
def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)
