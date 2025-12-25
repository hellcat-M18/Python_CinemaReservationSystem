from rich.console import Console
from rich.table import Table

from sqlalchemy import select

from db.db import SessionLocal
from db.models import Movie, Show
from utils.datetimeFormat import format_ymd_hm

console = Console()


def run(session: dict) -> dict:
    # 上映回選択
    # - session["movie_id"] のshowsを表示し、番号選択で show_id をセットして座席へ

    console.print("[bold]UserShowSelect[/bold]")

    # movie_idを遷移元から引き継ぎ
    movie_id = session.get("movie_id")
    if movie_id is None:
        console.print("[red]movie_idが未設定です。[/red]")
        input("Enterで映画一覧に戻ります... ")
        session["next_page"] = "user_movie_browse"
        return session

    # DBから上映回一覧を取得
    with SessionLocal() as db_session:
        movie = db_session.execute(select(Movie).where(Movie.id == movie_id)).scalar_one_or_none()
        shows = (
            db_session.execute(
                select(Show)
                .where(Show.movie_id == movie_id)
                .order_by(Show.start_at, Show.hall, Show.id)
            )
            .scalars()
            .all()
        )

    movie_title = movie.title if movie is not None else "(unknown)"
    console.print(f"映画: {movie_title} (movie_id={movie_id})")

    # 上映回がなければ戻る
    if not shows:
        console.print("[yellow]上映回がありません。管理者がスケジュールを作成してください。[/yellow]")
        input("Enterで映画一覧に戻ります... ")
        session["next_page"] = "user_movie_browse"
        return session

    # richでテーブル作成
    table = Table(title="上映回一覧")
    table.add_column("No", justify="right")
    table.add_column("show_id", justify="right")
    table.add_column("start_at")
    table.add_column("end_at")
    table.add_column("hall")
    table.add_column("price", justify="right")

    # 上映回一覧をテーブルに追加
    for i, s in enumerate(shows, start=1):
        table.add_row(
            str(i),
            str(s.id),
            format_ymd_hm(s.start_at),
            format_ymd_hm(s.end_at),
            s.hall,
            str(s.price),
        )

    console.print(table)

    # 上映回選択
    while True:
        raw = input("選択してください (番号 / bで戻る): ").strip().lower()
        # bなら戻る
        if raw in {"b", "back"}:
            session["next_page"] = "user_movie_browse"
            return session
        # 数値チェック
        if not raw.isdigit():
            console.print("[red]番号を入力してください。[/red]")
            continue
        # 範囲チェック
        idx = int(raw)
        if idx < 1 or idx > len(shows):
            console.print("[red]範囲外です。[/red]")
            continue
        
        # show_idをセットして座席選択へ
        show = shows[idx - 1]
        session["show_id"] = show.id
        session["next_page"] = "user_seat_select"
        return session
