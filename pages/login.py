from rich.console import Console

console = Console()

# ログインページ
# この関数はsessionという名前のdictを受け取って、dictを返すよ、というヒント
def run(session: dict) -> dict:

    # 古いキーが残っていても破綻しないように掃除(安全策)
    session.pop("next_page", None)

    while True:
        user_name = input("Enter your name (or 'exit'): ").strip() # strip(): 前後の空白を削除

        # "exit"が入力されたら終了
        if user_name.lower() == "exit":
            session["user_role"] = None
            session["user_name"] = None
            session["next_page"] = "exit"
            return session

        # 何も入力されなかったら先頭に戻る
        if not user_name:
            console.print("[red]Name is required.[/red]")
            continue

        # Adminとしてログイン
        if user_name == "admin":
            password = input("Enter your password (or 'back'): ")
            if password.lower() == "back":
                continue

            # 認証完了
            if password == "password123":   # あとでenvに移す
                console.print("Access Granted!")
                session["user_role"] = "Admin"
                session["user_name"] = user_name
                session["next_page"] = "admin_menu"
                return session

            # 認証失敗、再試行確認
            console.print("[red]Access Denied![/red] Incorrect password.")
            retry = input("Retry? (y/n): ").strip().lower()
            if retry == "y":
                continue
            
            # noなら終了
            session["user_role"] = None
            session["user_name"] = None
            session["next_page"] = "exit"
            return session

        # Userとしてログイン
        console.print(f"Welcome, [#00ff00]{user_name}[/]!")
        session["user_role"] = "User"
        session["user_name"] = user_name
        session["next_page"] = "user_menu"
        return session
# run({})