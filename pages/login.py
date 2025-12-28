from datetime import datetime

from rich.console import Console
from sqlalchemy import select

from db.db import SessionLocal
from db.models import User
from utils.auth import hash_password, verify_password

console = Console(highlight=False)


def _prompt_username() -> str:
    while True:
        raw = input("ユーザーID: ").strip()
        if raw:
            return raw
        console.print("[red]ユーザーIDは必須です。[/red]")


def _prompt_password(label: str = "パスワード") -> str:
    while True:
        raw = input(f"{label}: ").strip()
        if raw:
            return raw
        console.print("[red]パスワードは必須です。[/red]")


def run(session: dict) -> dict:
    # ログイン/新規登録ページ
    # - DB(User)でユーザーID+パスワード認証
    # - 成功時: session['user_id','user_name','user_role'] をセット

    session.pop("next_page", None)

    while True:
        console.print("[bold][login][/bold]")
        console.print("  1) ログイン")
        console.print("  2) 新規登録")
        console.print("  0) 終了")
        choice = input("> ").strip()

        if choice == "0":
            session["user_role"] = None
            session["user_name"] = None
            session["user_id"] = None
            session["next_page"] = "exit"
            return session

        if choice not in {"1", "2"}:
            console.print("[red]無効な入力です。[/red]")
            continue

        username = _prompt_username()
        password = _prompt_password()

        with SessionLocal() as db_session:
            user = db_session.execute(select(User).where(User.username == username)).scalar_one_or_none()

            if choice == "1":
                # ログイン
                if user is None or not verify_password(password, user.password_hash):
                    console.print("[red]ユーザーIDまたはパスワードが違います。[/red]")
                    continue

                session["user_id"] = user.id
                session["user_name"] = user.username
                session["user_role"] = user.role
                session.pop("ticket_uuid", None)

                if user.role == "Admin":
                    session["next_page"] = "admin_menu"
                else:
                    session["next_page"] = "user_menu"
                return session

            # 新規登録
            if user is not None:
                console.print("[yellow]そのユーザーIDは既に使われています。[/yellow]")
                continue

            created = User(
                username=username,
                password_hash=hash_password(password),
                role="User",
                created_at=datetime.now().strftime("%Y-%m-%dT%H:%M"),
            )
            db_session.add(created)
            db_session.commit()

            session["user_id"] = created.id
            session["user_name"] = created.username
            session["user_role"] = created.role
            session.pop("ticket_uuid", None)
            session["next_page"] = "user_menu"
            return session