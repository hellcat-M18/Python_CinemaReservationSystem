from rich.console import Console

console = Console()


def run(session: dict) -> dict:
    # ユーザー用メニュー
    # 数字入力で遷移先を決め、session["next_page"] にセットしてrouterへ返す

    user_name = session.get("user_name")
    if user_name:
        console.print(f"[bold]UserMenu[/bold] こんにちは、{user_name} さん")
    else:
        console.print("[bold]UserMenu[/bold]")

    # 操作候補を表示し、対応する数値の入力を待つ
    while True:
        console.print("\n[bold]操作を選んでください[/bold]")
        console.print("  1) 映画一覧を見る / 予約する")
        console.print("  2) チケットQRを表示(本来ならQRコードリーダーで読み取る)")
        console.print("  3) チケットをキャンセル(予約一覧から番号指定)")
        console.print("  4) 予約一覧を見る(ログイン名から自動表示)")
        console.print("  9) ログアウト")
        console.print("  0) 終了")

        choice = input("> ").strip()

        # 1なら映画一覧へ
        if choice == "1":
            session["next_page"] = "user_movie_browse"
            return session

        # 2ならチケットQR表示へ
        if choice == "2":
            ticket_uuid = input("チケットUUIDを入力してください(空白で戻る): ").strip()
            if not ticket_uuid:
                continue

            session["ticket_uuid"] = ticket_uuid
            session["next_page"] = "user_ticket_qr"
            return session

        # 3ならチケットキャンセルへ
        if choice == "3":
            session["next_page"] = "user_cancel_ticket"
            return session

        # 4なら予約一覧へ
        if choice == "4":
            session["next_page"] = "user_reservation_list"
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
