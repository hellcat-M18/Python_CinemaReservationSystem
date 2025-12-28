from rich.console import Console

from sqlalchemy import select

from db.db import SessionLocal
from db.models import Movie, Show, TicketSeat  # movie, Show, TicketSeatモデルをインポート
from utils.hallLayout import get_all_seats, render_seat_map  # ホールレイアウト表示ユーティリティ
from utils.datetimeFormat import format_ymd_hm

console = Console(highlight=False)


def run(session: dict) -> dict:
    # 座席表示（空席/予約済み）
    # 予約作成はまだ未実装なので、まず「見える化」だけ行う

    console.print("[bold][UserSeatSelect][/bold]")

    # 上映回の選択画面からshow_idを受け取る
    show_id = session.get("show_id")
    if show_id is None:
        raw = input("show_idを入力してください: ").strip()# 通常のパスではここには来ないはず
        if raw == "":
            session["next_page"] = "user_menu"
            return session
        if not raw.isdigit():
            console.print("[red]show_idは数字で入力してください。[/red]")
            session["next_page"] = "user_menu"
            return session
        show_id = int(raw)
        session["show_id"] = show_id

    # DBから上映回情報と予約済み座席を取得
    with SessionLocal() as db_session:
        # showの情報を取得
        show = db_session.execute(select(Show).where(Show.id == show_id)).scalar_one_or_none()
        if show is None:
            console.print("[red]指定されたshow_idが見つかりません。[/red]")
            input("Enterでメニューに戻ります... ")
            session["next_page"] = "user_menu"
            return session

        # 上映タイトルの情報を取得
        movie = db_session.execute(select(Movie).where(Movie.id == show.movie_id)).scalar_one_or_none()
        movie_title = movie.title if movie is not None else "(unknown)"

        # 予約済み座席のリストを取得
        reserved = (
            db_session.execute(select(TicketSeat.seat).where(TicketSeat.show_id == show.id))
            .scalars()
            .all()
        )

    console.print(f"\n映画: {movie_title}")
    console.print(f"上映: show_id={show.id} hall={show.hall} start_at={format_ymd_hm(show.start_at)}")
    render_seat_map(console, hall=show.hall, reserved=reserved)

    # ホールのレイアウトを取得
    try:
        all_seats = get_all_seats(show.hall)
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        input("Enterでメニューに戻ります... ")
        session["next_page"] = "user_menu"
        return session

    reserved_set = {s.strip().upper() for s in reserved}

    # 購入枚数（座席数）を入力
    while True:
        raw_cnt = input("購入枚数(座席数) [1] (bで戻る): ").strip().lower()
        if raw_cnt in {"b", "back"}:
            session.pop("selected_seats", None)
            session["next_page"] = "user_show_select"
            return session
        if raw_cnt == "":
            seat_count = 1
            break
        if not raw_cnt.isdigit():
            console.print("[red]数字を入力してください。[/red]")
            continue
        seat_count = int(raw_cnt)
        if seat_count <= 0:
            console.print("[red]1以上で入力してください。[/red]")
            continue
        break

    session["seat_count"] = seat_count

    # 座席入力（カンマ区切り）
    while True:
        raw = input(
            f"座席を{seat_count}個入力してください（例: A-1,A-2 / bで戻る）: "
        ).strip()
        if raw.lower() in {"b", "back"}:
            session.pop("selected_seats", None)
            session["next_page"] = "user_show_select"
            return session

        tokens = [t.strip().upper() for t in raw.split(",") if t.strip() != ""]
        if not tokens:
            console.print("[red]座席を1つ以上入力してください。[/red]")
            continue

        # 重複排除しつつ順序を保つ
        normalized: list[str] = []
        seen: set[str] = set()
        for t in tokens:
            if t not in seen:
                normalized.append(t)
                seen.add(t)

        # 存在チェックと予約済みチェック
        if len(normalized) != seat_count:
            console.print(
                f"[red]座席数が一致しません（入力={len(normalized)} / 必要={seat_count}）。[/red]"
            )
            continue

        invalid = [t for t in normalized if t not in all_seats]
        if invalid:
            console.print(f"[red]存在しない座席があります: {', '.join(invalid)}[/red]")
            continue

        taken = [t for t in normalized if t in reserved_set]
        if taken:
            console.print(f"[red]すでに予約済みの座席があります: {', '.join(taken)}[/red]")
            continue
        
        # 決済へ進む
        session["selected_seats"] = normalized
        session["next_page"] = "user_checkout"
        return session
