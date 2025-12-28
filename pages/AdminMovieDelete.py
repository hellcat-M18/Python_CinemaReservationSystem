from rich.console import Console

from sqlalchemy import select

from db.db import SessionLocal
from db.models import Movie

console = Console(highlight=False)


def run(session: dict) -> dict:
    # 映画削除
    # - session["movie_id"] を参照して削除対象を決める
    # - Movie->Show->Ticket まで ORM cascade で消える設計
    # - 削除後は admin_movie_list に戻る

    movie_id = session.get("movie_id")
    console.print("[bold][AdminMovieDelete][/bold]")

    # 想定外のアクセス
    if movie_id is None:
        console.print("[yellow]movie_id が指定されていません。[/yellow]")
        input("Enterで一覧に戻ります... ")
        session["next_page"] = "admin_movie_list"
        return session

    # DBへの接続セッションを確立
    with SessionLocal() as db_session:
        try:
            movie = db_session.execute(select(Movie).where(Movie.id == movie_id)).scalar_one_or_none()
        except Exception as exc:
            console.print(f"[red]DBアクセスに失敗しました: {exc}[/red]")
            input("Enterで一覧に戻ります... ")
            session["next_page"] = "admin_movie_list"
            return session

        # 見つからなければ戻る
        if movie is None:
            console.print("[yellow]指定されたmovie_idが見つかりません。[/yellow]")
            input("Enterで一覧に戻ります... ")
            session["next_page"] = "admin_movie_list"
            return session

        # 確認表示
        console.print("\n[bold]削除対象[/bold]")
        console.print(f"  id={movie.id}")
        console.print(f"  title={movie.title}")
        console.print(f"  duration_min={movie.duration_min}")

        # 確認入力
        confirm = input("この映画を削除しますか? (y/n): ").strip().lower()
        if confirm != "y":
            console.print("[yellow]キャンセルしました。[/yellow]")
            session["next_page"] = "admin_movie_list"
            return session

        # 削除実行
        try:
            db_session.delete(movie)
            db_session.commit()
            console.print("[green]削除しました。[/green]")
        except Exception as exc:
            db_session.rollback()
            console.print(f"[red]削除に失敗しました: {exc}[/red]")
            input("Enterで一覧に戻ります... ")

        # メニューに戻る
        session["next_page"] = "admin_movie_list"
        return session
