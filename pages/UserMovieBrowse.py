from rich.console import Console
from rich.table import Table

from sqlalchemy import select

from db.db import SessionLocal
from db.models import Movie

console = Console()


def run(session: dict) -> dict:
    # 映画一覧（ユーザー向け）
    # - moviesを一覧表示し、番号選択でmovie_idをsessionに入れて次へ

    console.print("[bold]UserMovieBrowse[/bold]")

    # DBから映画一覧を取得
    with SessionLocal() as db_session:
        movies = db_session.execute(select(Movie).order_by(Movie.id)).scalars().all()

    if not movies:
        console.print("[yellow]映画が登録されていません。[/yellow]")
        input("Enterでメニューに戻ります... ")
        session["next_page"] = "user_menu"
        return session

    # テーブル作成
    table = Table(title="映画一覧")
    table.add_column("No", justify="right")
    table.add_column("movie_id", justify="right")
    table.add_column("title")
    table.add_column("duration", justify="right")
    table.add_column("price", justify="right")

    # 映画一覧をテーブルに追加
    for i, m in enumerate(movies, start=1):
        table.add_row(str(i), str(m.id), m.title, f"{m.duration_min}min", str(m.default_price))

    console.print(table)

    while True:
        # 予約する映画を選択
        raw = input("選択してください (番号 / bで戻る): ").strip().lower()
        # bなら戻る
        if raw in {"b", "back"}:
            session["next_page"] = "user_menu"
            return session
        # 数値チェック
        if not raw.isdigit():
            console.print("[red]番号を入力してください。[/red]")
            continue
        # 範囲チェック
        idx = int(raw)
        if idx < 1 or idx > len(movies):
            console.print("[red]範囲外です。[/red]")
            continue
        
        # movie_idをセットして上映回選択へ
        movie = movies[idx - 1]
        session["movie_id"] = movie.id
        session["next_page"] = "user_show_select"
        return session
