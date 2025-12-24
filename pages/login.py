import rich
from rich.console import Console

console = Console()


def run(session: dict) -> dict:
    """ログイン画面。

    - router.py が画面クリアを担当する前提
    - session["next_page"] をセットするとルーターが遷移する
    """

    # 古いキーが残っていても破綻しないように掃除
    session.pop("nextPage", None)

    while True:
        user_name = input("Enter your name (or 'exit'): ").strip()

        if user_name.lower() == "exit":
            session["userRole"] = None
            session["userName"] = None
            session["next_page"] = "exit"
            return session

        if not user_name:
            console.print("[red]Name is required.[/red]")
            continue

        # Admin login
        if user_name == "admin":
            password = input("Enter your password (or 'back'): ")
            if password.lower() == "back":
                continue

            if password == "password123":
                console.print("Access Granted!")
                session["userRole"] = "Admin"
                session["userName"] = user_name
                session["next_page"] = "admin_menu"
                return session

            console.print("[red]Access Denied![/red] Incorrect password.")
            retry = input("Retry? (y/n): ").strip().lower()
            if retry == "y":
                continue

            session["userRole"] = None
            session["userName"] = None
            session["next_page"] = "exit"
            return session

        # User login (simple)
        console.print(f"Welcome, [#00ff00]{user_name}[/]!")
        session["userRole"] = "User"
        session["userName"] = user_name
        session["next_page"] = "user_menu"
        return session
# run({})