from rich.console import Console
from rich.table import Table

from utils.rich_compat import TABLE_KWARGS

from sqlalchemy import select   # DB操作用、Select文

from datetime import date       # 日付を扱うためのモジュール

from db.db import SessionLocal  # DB操作のセッションを生成するクラス
from db.models import Movie     # テーブル"Movie"のモデルをインポート

console = Console(highlight=False)


def run(session: dict) -> dict:
    # 映画の追加/編集
    # - session["movie_id"] が None/未設定: 追加
    # - session["movie_id"] が int: その映画を編集
    # - 保存後は admin_movie_list に戻る

    movie_id = session.get("movie_id")

    # セッションがmovie_idを持たない->追加モード　持つ->編集モード
    if movie_id is None:
        console.print("[bold][AdminMovieEdit][/bold]")
        console.print("追加モード")
    else:
        console.print(f"[bold][AdminMovieEdit][/bold]")
        console.print(f"編集モード movie_id={movie_id}")

    # DBへの接続セッションを作る
    # with: ファイルやDB接続などのリソースを自動的に解放するための構文。処理が終わったら自動的に閉じてくれる。
    with SessionLocal() as db_session:
        movie: Movie | None = None  # ややこしいけど型ヒント。初期値NoneでMovieが入る可能性があるよ、という表現。
        if movie_id is not None:
            try:
                movie = db_session.execute(select(Movie).where(Movie.id == movie_id)).scalar_one_or_none()
                # 該当するmovie_idの映画を取得。なければNoneが返る。
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

            # 編集モード: 現在の登録情報を一覧表示
            info = Table(title="現在の登録情報", **TABLE_KWARGS)
            info.add_column("項目")
            info.add_column("値")
            info.add_row("id", str(movie.id))
            info.add_row("title", movie.title)
            info.add_row("duration_min", str(movie.duration_min))
            info.add_row("default_price", str(movie.default_price))
            info.add_row("description", movie.description or "-")
            info.add_row("tags_json", movie.tags_json)
            info.add_row("run_start_date", movie.run_start_date or "-")
            info.add_row("run_end_date", movie.run_end_date or "-")
            console.print(info)

        # 入力補助
        # 入力ラベルを表示し、ユーザーからの入力を待つ。
        # 空白Enter時、それが新規追加なら再入力を促し、編集なら現在値を保持。入力があった場合はそれを返す。
        # returnでwhileを抜け次に進む。
        def _prompt_str(label: str, current: str | None, required: bool = False) -> str | None:
            while True:
                cur = "" if current is None else current
                value = input(f"{label} [{cur}]: ").strip()
                if value == "":
                    if required and current is None:
                        console.print("[red]必須です。[/red]")
                        continue
                    return current
                return value

        # 上のやつに数値チェックを追加したバージョン
        def _prompt_int(label: str, current: int | None, required: bool = False) -> int | None:
            while True:
                cur = "" if current is None else str(current)
                value = input(f"{label} [{cur}]: ").strip()
                if value == "":
                    if required and current is None:
                        console.print("[red]必須です。[/red]")
                        continue
                    return current
                if not value.isdigit():
                    console.print("[red]数字を入力してください。[/red]")
                    continue
                return int(value)

        # 日付の形式チェック付き(YYYY-MM-DD)
        def _prompt_date(label: str, current: str | None, required: bool = False) -> str | None:
            while True:
                cur = "" if current is None else current
                value = input(f"{label} [{cur}]: ").strip()
                if value == "":
                    if required and current is None:
                        console.print("[red]必須です。[/red]")
                        continue
                    return current

                # YYYY-MM-DD 形式かどうかを判定
                try:
                    date.fromisoformat(value)
                except ValueError:
                    console.print("[red]YYYY-MM-DD形式で入力してください。[/red]")
                    continue
                return value
            
        # 各フィールドの入力待ち
        # あるなら現在の登録内容を表示
        title = _prompt_str("映画名(title)", movie.title if movie else None, required=True)
        duration_min = _prompt_int("上映時間(duration_min)", movie.duration_min if movie else None, required=True)
        default_price = _prompt_int("基本料金(default_price)", movie.default_price if movie else 0, required=True)
        description = _prompt_str("説明(description)", movie.description if movie else None, required=False)
        tags_json = _prompt_str("タグ(tags_json, JSON文字列)", movie.tags_json if movie else "[]", required=True)
        # 上映期間の入力(大小チェック付き)
        while True:
            run_start_date = _prompt_date(
                "上映開始日(run_start_date, YYYY-MM-DD)",
                movie.run_start_date if movie else None,
            )
            run_end_date = _prompt_date(
                "上映終了日(run_end_date, YYYY-MM-DD)",
                movie.run_end_date if movie else None,
            )

            if run_start_date and run_end_date:
                start_d = date.fromisoformat(run_start_date)
                end_d = date.fromisoformat(run_end_date)
                if start_d > end_d:
                    console.print("[red]上映開始日 <= 上映終了日 になるように入力してください。[/red]")
                    continue

            break

        # 確認画面
        console.print("\n[bold]確認[/bold]")
        console.print(f"  title: {title}")
        console.print(f"  duration_min: {duration_min}")
        console.print(f"  default_price: {default_price}")
        console.print(f"  description: {description}")
        console.print(f"  tags_json: {tags_json}")
        console.print(f"  run_start_date: {run_start_date}")
        console.print(f"  run_end_date: {run_end_date}")

        # yで保存、他でキャンセル
        confirm = input("保存しますか? (y/n): ").strip().lower()
        if confirm != "y":
            console.print("[yellow]キャンセルしました。[/yellow]")
            session["next_page"] = "admin_movie_list"
            return session

        # DBへの書き込みを実行
        try:
            # 追加モードなら新規作成、編集モードなら既存オブジェクトを更新
            if movie is None:
                movie = Movie(
                    title=title or "",
                    duration_min=duration_min or 0,
                    default_price=default_price or 0,
                    tags_json=tags_json or "[]",
                    description=description,
                    run_start_date=run_start_date,
                    run_end_date=run_end_date,
                )
                db_session.add(movie)
            else:
                movie.title = title or movie.title
                movie.duration_min = int(duration_min or movie.duration_min)
                movie.default_price = int(default_price or movie.default_price)
                movie.description = description
                movie.tags_json = tags_json or movie.tags_json
                movie.run_start_date = run_start_date
                movie.run_end_date = run_end_date

            db_session.commit()
        except Exception as exc:

            # エラー時はキャンセル
            db_session.rollback()
            console.print(f"[red]保存に失敗しました: {exc}[/red]")
            input("Enterで一覧に戻ります... ")

        # 正常終了, メニューに戻る
        session["next_page"] = "admin_movie_list"
        return session
