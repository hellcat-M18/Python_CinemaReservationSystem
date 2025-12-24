from rich.console import Console

from sqlalchemy import select

from db.db import SessionLocal
from db.models import Movie, Show, TicketSeat
from utils.hallLayout import render_vacancy_table

console = Console()


def run(session: dict) -> dict:
    # 座席表示（空席/予約済み）
    # 予約作成はまだ未実装なので、まず「見える化」だけ行う

    console.print("[bold]UserSeatSelect[/bold]")

    show_id = session.get("show_id")
    if show_id is None:
        raw = input("show_idを入力してください: ").strip()
        if raw == "":
            session["next_page"] = "user_menu"
            return session
        if not raw.isdigit():
            console.print("[red]show_idは数字で入力してください。[/red]")
            session["next_page"] = "user_menu"
            return session
        show_id = int(raw)
        session["show_id"] = show_id

    with SessionLocal() as db_session:
        show = db_session.execute(select(Show).where(Show.id == show_id)).scalar_one_or_none()
        if show is None:
            console.print("[red]指定されたshow_idが見つかりません。[/red]")
            input("Enterでメニューに戻ります... ")
            session["next_page"] = "user_menu"
            return session

        movie = db_session.execute(select(Movie).where(Movie.id == show.movie_id)).scalar_one_or_none()
        movie_title = movie.title if movie is not None else "(unknown)"

        reserved = (
            db_session.execute(select(TicketSeat.seat).where(TicketSeat.show_id == show.id))
            .scalars()
            .all()
        )

    console.print(f"\n映画: {movie_title}")
    console.print(f"上映: show_id={show.id} hall={show.hall} start_at={show.start_at}")
    render_vacancy_table(console, hall=show.hall, reserved=reserved)

    input("Enterでメニューに戻ります... ")
    session["next_page"] = "user_menu"
    return session
