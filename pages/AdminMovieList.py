from rich.console import Console

from sqlalchemy import select   # db操作用、Select文

from db.db import SessionLocal  # DB操作のセッションを生成するクラス
from db.models import Movie     # テーブル"Movie"のモデルをインポート

console = Console(highlight=False)


def run(session: dict) -> dict:
    # 映画の管理(一覧/追加/編集/削除)
    # - 一覧を表示
    # - 数字入力で遷移先を決め、session["next_page"] にセットしてrouterへ返す
    # - 編集/削除は対象movie_idを session["movie_id"] に入れて次ページへ渡す

    console.print("[bold][AdminMovieList][/bold]")

    # DBへの接続を試行
    try:
        with SessionLocal() as db_session:
            movies = db_session.execute(select(Movie).order_by(Movie.id)).scalars().all()
            # Movieテーブルの全行をソートし、それをmoviesにセット、scalars()で余分なデータをカットしall()でリスト化

    except Exception as exc:
        console.print(f"[red]DBアクセスに失敗しました: {exc}[/red]")
        input("EnterでAdminMenuに戻ります... ")
        session["next_page"] = "admin_menu"
        return session

    # 映画一覧を表示
    if not movies:
        console.print("[yellow]映画が登録されていません。[/yellow]")
    else:
        console.print("\n[bold]映画一覧[/bold]")
        for movie in movies:
            run_range = ""
            if movie.run_start_date or movie.run_end_date:
                run_range = f" ({movie.run_start_date or ''} - {movie.run_end_date or ''})"
            console.print(
                f"  id={movie.id} | {movie.title} | {movie.duration_min}min | price={movie.default_price}{run_range}"
            )
            # id, タイトル, 上映時間, 上映期間(あれば)を表示

    # 操作候補の表示と入力待ち
    while True:
        console.print("\n[bold]操作を選んでください[/bold]")
        console.print("  1) 追加")
        console.print("  2) 編集")
        console.print("  3) 削除")
        console.print("  0) 戻る")

        choice = input("> ").strip()

        # 1なら追加へ
        if choice == "1":
            session["movie_id"] = None
            session["next_page"] = "admin_movie_edit"
            return session

        # 2なら既存の映画の編集へ
        if choice == "2":
            movie_id_str = input("編集するmovie_idを入力してください(空白で戻る): ").strip()
            if not movie_id_str:
                continue
            if not movie_id_str.isdigit():
                console.print("[red]数字を入力してください。[/red]")
                continue
            session["movie_id"] = int(movie_id_str)
            session["next_page"] = "admin_movie_edit"
            return session

        # 3なら既存の映画の削除へ
        if choice == "3":
            movie_id_str = input("削除するmovie_idを入力してください(空白で戻る): ").strip()
            if not movie_id_str:
                continue
            if not movie_id_str.isdigit():
                console.print("[red]数字を入力してください。[/red]")
                continue
            session["movie_id"] = int(movie_id_str)
            session["next_page"] = "admin_movie_delete"
            return session

        # 0なら戻る
        if choice == "0":
            session["next_page"] = "admin_menu"
            return session

        console.print("[red]無効な入力です。[/red]")
