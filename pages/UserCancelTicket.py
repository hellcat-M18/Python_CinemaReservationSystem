from rich.console import Console
from rich.table import Table

from sqlalchemy import select

from db.db import SessionLocal
from db.models import Movie, Show, Ticket, TicketSeat
from utils.datetimeFormat import format_ymd_hm

console = Console()


def run(session: dict) -> dict:
    # チケットキャンセル（最小）
    # - sessionのuser_nameで現在の予約一覧を表示
    # - 番号選択でキャンセル
    # - used_at が入っている場合はキャンセル不可
    # - y/n確認後、Ticketを削除（cascadeでticket_seatsも削除）

    console.print("[bold]UserCancelTicket[/bold]")

    # 名前をセッションから取得、なければ入力
    user_name = (session.get("user_name") or "").strip()
    if not user_name:
        user_name = input("名前が未設定です。名前を入力してください (bで戻る): ").strip()
        if user_name.lower() in {"b", "back"}:
            session["next_page"] = "user_menu"
            return session
        if not user_name:
            console.print("[yellow]名前が未入力のためキャンセル対象を表示できません。[/yellow]")
            input("Enterでメニューに戻ります... ")
            session["next_page"] = "user_menu"
            return session
        session["user_name"] = user_name

    # DBからチケット一覧を取得
    with SessionLocal() as db_session:
        tickets = (
            db_session.execute(
                select(Ticket)
                .where(Ticket.user_name == user_name)
                .order_by(Ticket.issued_at.desc().nullslast(), Ticket.id.desc())
            )
            .scalars()
            .all()
        )

        # チケットが見つからなければメニューに戻る
        if not tickets:
            console.print("[yellow]現在の予約が見つかりませんでした。[/yellow]")
            input("Enterでメニューに戻ります... ")
            session["next_page"] = "user_menu"
            return session

        # チケットに関連する上映情報
        show_ids = [t.show_id for t in tickets]
        shows = (
            db_session.execute(select(Show).where(Show.id.in_(show_ids)))
            .scalars()
            .all()
        )
        show_map = {s.id: s for s in shows}

        # チケットに関連する映画情報
        movie_ids = list({s.movie_id for s in shows})
        movies = (
            db_session.execute(select(Movie).where(Movie.id.in_(movie_ids)))
            .scalars()
            .all()
        )
        movie_map = {m.id: m for m in movies}

        # チケットに関連する座席情報
        ticket_ids = [t.id for t in tickets]
        seat_rows = (
            db_session.execute(
                select(TicketSeat.ticket_id, TicketSeat.seat)
                .where(TicketSeat.ticket_id.in_(ticket_ids))
                .order_by(TicketSeat.ticket_id, TicketSeat.seat)
            )
            .all()
        )
        seats_by_ticket: dict[int, list[str]] = {}
        for tid, seat in seat_rows:
            seats_by_ticket.setdefault(int(tid), []).append(str(seat))

    # 予約一覧を表示
    table = Table(title=f"キャンセル対象一覧: {user_name}")
    table.add_column("No", justify="right")
    table.add_column("映画")
    table.add_column("開始")
    table.add_column("hall")
    table.add_column("座席")
    table.add_column("合計", justify="right")
    table.add_column("使用")

    # 予約一覧をテーブルに追加
    for i, ticket in enumerate(tickets, start=1):
        show = show_map.get(ticket.show_id)
        movie = movie_map.get(show.movie_id) if show is not None else None
        seats = seats_by_ticket.get(ticket.id, [])
        table.add_row(
            str(i),
            movie.title if movie is not None else "(unknown)",
            format_ymd_hm(show.start_at) if show is not None else "-",
            show.hall if show is not None else "-",
            ", ".join(seats) if seats else "-",
            f"{ticket.sum_price}円",
            "使用済" if ticket.used_at else "未使用",
        )

    console.print(table)

    # キャンセルする予約を番号で選択
    console.print("\nキャンセルする予約の番号を入力(bで戻る): ")
    while True:
        raw = input("> ").strip().lower()
        if raw in {"b", "back", ""}:
            session["next_page"] = "user_menu"
            return session
        if not raw.isdigit():
            console.print("[red]番号を入力してください。[/red]")
            continue

        idx = int(raw)
        if idx < 1 or idx > len(tickets):
            console.print("[red]範囲外です。[/red]")
            continue

        selected = tickets[idx - 1]
        if selected.used_at:
            console.print("[yellow]このチケットは使用済みのためキャンセルできません。[/yellow]")
            continue

        show = show_map.get(selected.show_id)
        movie = movie_map.get(show.movie_id) if show is not None else None
        seats = seats_by_ticket.get(selected.id, [])

        # 確認表示
        t = Table(title="キャンセル確認")
        t.add_column("項目")
        t.add_column("値")
        t.add_row("UUID", selected.uuid)
        t.add_row("名前", selected.user_name or "-")
        t.add_row("映画", movie.title if movie is not None else "(unknown)")
        t.add_row("開始", format_ymd_hm(show.start_at) if show is not None else "-")
        t.add_row("ホール", show.hall if show is not None else "-")
        t.add_row("座席", ", ".join(seats) if seats else "-")
        t.add_row("合計", f"{selected.sum_price} 円")
        console.print(t)

        confirm = input("このチケットをキャンセルしますか? (y/n): ").strip().lower()
        if confirm != "y":
            console.print("[yellow]キャンセルを中止しました。[/yellow]")
            session["next_page"] = "user_menu"
            return session

        # キャンセル実行
        with SessionLocal() as db_session:
            ticket = db_session.execute(select(Ticket).where(Ticket.uuid == selected.uuid)).scalar_one_or_none()
            if ticket is None:
                console.print("[red]チケットが見つかりません（既に消された可能性）。[/red]")
                input("Enterでメニューに戻ります... ")
                session["next_page"] = "user_menu"
                return session
            if ticket.used_at:
                console.print("[yellow]このチケットは使用済みのためキャンセルできません。[/yellow]")
                input("Enterでメニューに戻ります... ")
                session["next_page"] = "user_menu"
                return session

            try:
                db_session.delete(ticket)
                db_session.commit()
            except Exception as exc:
                db_session.rollback()
                console.print(f"[red]キャンセルに失敗しました: {exc}[/red]")
                input("Enterでメニューに戻ります... ")
                session["next_page"] = "user_menu"
                return session

        console.print("[green]キャンセルしました。[/green]")
        input("Enterでメニューに戻ります... ")
        session["next_page"] = "user_menu"
        return session
