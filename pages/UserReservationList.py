import json

from rich.console import Console
from rich.table import Table

from sqlalchemy import select

from db.db import SessionLocal
from db.models import Movie, Show, Ticket, TicketSeat
from utils.datetimeFormat import format_ymd_hm

console = Console()


def run(session: dict) -> dict:
    # 現在の予約一覧
    # - user_nameで絞り込み（未入力なら入力させる）
    # - キャンセルはTicket削除運用なので、ticketsに残っているものが「現在の予約」

    console.print("[bold]UserReservationList[/bold]")

    # 名前をセッションから取得、なければ入力
    user_name = (session.get("user_name") or "").strip()
    if not user_name:
        user_name = input("名前が未設定です。名前を入力してください (bで戻る): ").strip()
        if user_name.lower() in {"b", "back"}:
            session["next_page"] = "user_menu"
            return session
        if not user_name:
            console.print("[yellow]名前が未入力のため検索できません。[/yellow]")
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

        if not tickets:
            console.print("[yellow]予約が見つかりませんでした。[/yellow]")
            input("Enterでメニューに戻ります... ")
            session["next_page"] = "user_menu"
            return session

        # show/movie をまとめて取得
        show_ids = [t.show_id for t in tickets]
        shows = (
            db_session.execute(select(Show).where(Show.id.in_(show_ids)))
            .scalars()
            .all()
        )
        show_map = {s.id: s for s in shows}

        movie_ids = list({s.movie_id for s in shows})
        movies = (
            db_session.execute(select(Movie).where(Movie.id.in_(movie_ids)))
            .scalars()
            .all()
        )
        movie_map = {m.id: m for m in movies}

        # 座席は ticket_id ごとに集める（小規模想定でN+1でもOKだが、一括で取る）
        ticket_ids = [t.id for t in tickets]
        seat_rows = (
            db_session.execute(
                select(TicketSeat.ticket_id, TicketSeat.seat)
                .where(TicketSeat.ticket_id.in_(ticket_ids))
                .order_by(TicketSeat.ticket_id, TicketSeat.seat)
            )
            .all()
        )

        # 座席情報を ticket_id ごとにまとめる
        seats_by_ticket: dict[int, list[str]] = {}
        for tid, seat in seat_rows:
            seats_by_ticket.setdefault(int(tid), []).append(str(seat))

    # 予約一覧を表示
    table = Table(title=f"予約一覧: {user_name}")
    table.add_column("No", justify="right")
    table.add_column("UUID")
    table.add_column("映画")
    table.add_column("開始")
    table.add_column("hall")
    table.add_column("座席")
    table.add_column("合計", justify="right")
    table.add_column("使用", justify="left")

    # 予約一覧をテーブルに追加
    for i, t in enumerate(tickets, start=1):
        show = show_map.get(t.show_id)
        movie = movie_map.get(show.movie_id) if show is not None else None
        seats = seats_by_ticket.get(t.id, [])

        table.add_row(
            str(i),
            t.uuid,
            movie.title if movie is not None else "(unknown)",
            format_ymd_hm(show.start_at) if show is not None else "-",
            show.hall if show is not None else "-",
            ", ".join(seats) if seats else "-",
            f"{t.sum_price}円",
            "使用済" if t.used_at else "未使用",
        )

    console.print(table)

    # 詳細を見る予約を番号で選択
    console.print("\n詳細を見る場合は番号を入力(bで戻る): ")
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

        ticket = tickets[idx - 1]
        session["ticket_uuid"] = ticket.uuid
        session["next_page"] = "user_ticket_qr"
        return session
