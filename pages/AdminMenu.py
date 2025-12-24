from rich.console import Console

console = Console()


def run(session: dict) -> dict:
    # 管理者メインメニュー
    # 数字入力で遷移先を決め、session["next_page"] にセットしてrouterへ返す

    user_name = session.get("user_name")
    if user_name:
        console.print(f"[bold]AdminMenu[/bold] こんにちは、{user_name} さん")
    else:
        console.print("[bold]AdminMenu[/bold]")

    # 操作候補の表示と入力待ち
    while True:
        console.print("\n[bold]操作を選んでください[/bold]")
        console.print("  1) 映画の管理(一覧/追加/編集/削除)")
        console.print("  2) 上映スケジュールの設定・編集(差分反映含む)")
        console.print("  3) 改札(チケットUUID照合)")
        console.print("  9) ログアウト")
        console.print("  0) 終了")

        choice = input("> ").strip()

        # 1なら映画管理へ
        if choice == "1":
            session["next_page"] = "admin_movie_list"
            return session

        # 2なら上映スケジュール設定へ
        if choice == "2":
            session["next_page"] = "admin_schedule_edit"
            return session

        # 3なら改札用ページへ、外部のスキャナーか何かでUUIDを読み取る想定
        if choice == "3":
            session["next_page"] = "admin_gate_check"
            return session

        # 9ならログアウト
        if choice == "9":
            session["user_role"] = None
            session["user_name"] = None
            session.pop("ticket_uuid", None)
            session["next_page"] = "login"
            return session

        # 0なら終了
        if choice == "0":
            session["next_page"] = "exit"
            return session

        console.print("[red]無効な入力です。[/red]")
