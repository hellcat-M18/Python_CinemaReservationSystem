from rich.console import Console

from datetime import date, datetime, timedelta # 日付・時間操作用

from sqlalchemy import func, select  # DB操作用、集約関数func、Select文 

from db.db import SessionLocal # DB操作のセッションを生成するクラス
from db.models import Movie, Show, Ticket   # テーブル"Movie", "Show", "Ticket"のモデルをインポート

console = Console()


def run(session: dict) -> dict:
    # 上映スケジュールの設定・編集(差分反映含む)
    # - show は「単一の上映回」を表す
    # - ここで入力されたルールから start_at/end_at を生成し、DBのshowsに差分反映する
    # - 既存showの削除が発生する場合は警告して y/n を取る(yなら該当ticketも抹消される)

    console.print("[bold]AdminScheduleEdit[/bold]")

    # 入力補助
    # MovieEditなどにあるのと同じ
    def _prompt_int(label: str, default: int | None = None, required: bool = False) -> int | None:
        while True:
            cur = "" if default is None else str(default)
            value = input(f"{label} [{cur}]: ").strip()
            if value == "":
                if required and default is None:
                    console.print("[red]必須です。[/red]")
                    continue
                return default
            if not value.isdigit():
                console.print("[red]数字を入力してください。[/red]")
                continue
            return int(value)

    def _prompt_str(label: str, default: str | None = None, required: bool = False) -> str | None:
        while True:
            cur = "" if default is None else default
            value = input(f"{label} [{cur}]: ").strip()
            if value == "":
                if required and default is None:
                    console.print("[red]必須です。[/red]")
                    continue
                return default
            return value

    def _prompt_date(label: str, default: str | None = None, required: bool = False) -> str | None:
        while True:
            value = _prompt_str(label, default, required)
            if value is None:
                return None
            try:
                date.fromisoformat(value)
            except ValueError:
                console.print("[red]YYYY-MM-DD形式で入力してください。[/red]")
                continue
            return value

    def _prompt_time(label: str, default: str | None = None, required: bool = False) -> str | None:
        while True:
            value = _prompt_str(label, default, required)
            if value is None:
                return None
            try:
                datetime.strptime(value, "%H:%M")
            except ValueError:
                console.print("[red]HH:MM形式で入力してください(例: 19:30)。[/red]")
                continue
            return value
        
    # DBのデータ(文字列)をdatetimeに変換
    def _parse_start_at(value: str) -> datetime:
        # YYYY-MM-DDTHH:MM または YYYY-MM-DD HH:MM を受け付ける
        v = value.strip().replace(" ", "T")
        return datetime.strptime(v, "%Y-%m-%dT%H:%M")

    def _to_iso_min(dt: datetime) -> str:
        return dt.strftime("%Y-%m-%dT%H:%M")

    # 入力: movie_id
    # sessionのデータを読み取り
    movie_id = session.get("movie_id")
    if movie_id is None:
        movie_id = _prompt_int("対象movie_id", None, required=True)
        session["movie_id"] = movie_id

    # 対象movie取得
    # DBへの接続セッションを確立
    with SessionLocal() as db_session:
        # idにマッチするmovieを取得
        movie = db_session.execute(select(Movie).where(Movie.id == movie_id)).scalar_one_or_none()
        if movie is None:
            console.print("[red]指定されたmovie_idが見つかりません。[/red]")
            input("EnterでAdminMenuに戻ります... ")
            session["next_page"] = "admin_menu"
            return session

        console.print(f"\n映画: id={movie.id} | {movie.title} | {movie.duration_min}min | default_price={movie.default_price}")

        # 上映の基本的な設定
        hall = _prompt_str("hall(レイアウトキー/ファイル名)", None, required=True)
        price = _prompt_int("price(空Enterでdefault_price)", movie.default_price, required=True)

        # 定期上映か否か
        repeat = input("繰り返しにしますか? (y/n): ").strip().lower()

        # スケジュール変更後の上映回一覧を持つリスト
        desired: dict[tuple[str, str], dict[str, object]] = {}

        # 繰り返し設定
        if repeat == "y":
            console.print("\n繰り返し種別")
            console.print("  1) weekly(毎週/n週ごと)")
            console.print("  2) monthly(毎月/nか月ごと)")
            repeat_type = input("> ").strip()

            start_date_str = _prompt_date("開始日(start_date, YYYY-MM-DD)", None, required=True)
            end_date_str = _prompt_date("終了日(end_date, YYYY-MM-DD)", None, required=True)
            start_time_str = _prompt_time("開始時刻(start_time, HH:MM)", None, required=True)
            start_d = date.fromisoformat(start_date_str)
            end_d = date.fromisoformat(end_date_str)

            # 日付の大小チェック
            # 再入力させられるならそっちの方が嬉しいが...
            if start_d > end_d:
                console.print("[red]開始日 <= 終了日 になるように入力してください。[/red]")
                input("EnterでAdminMenuに戻ります... ")
                session["next_page"] = "admin_menu"
                return session

            # n週ごとリピート
            # 放映する曜日を選択
            if repeat_type == "1":
                interval_weeks = _prompt_int("繰り返し間隔(interval_weeks)", 1, required=True) or 1
                console.print("曜日をカンマ区切りで入力してください(0=Mon,1=Tue,2=Wed,3=Thu,4=Fri,5=Sat,6=Sun)")
                dow_raw = _prompt_str("days_of_week", None, required=True) or ""

                # 入力チェック
                try:
                    days_of_week = {int(x.strip()) for x in dow_raw.split(",") if x.strip() != ""}
                except ValueError:
                    console.print("[red]曜日は0-6の数字で入力してください。[/red]")
                    input("EnterでAdminMenuに戻ります... ")
                    session["next_page"] = "admin_menu"
                    return session
                if any(d < 0 or d > 6 for d in days_of_week) or len(days_of_week) == 0:
                    console.print("[red]曜日は0-6の範囲で指定してください。[/red]")
                    input("EnterでAdminMenuに戻ります... ")
                    session["next_page"] = "admin_menu"
                    return session

                # start_dからend_dまで走査し、該当曜日かつinterval_weeksごとに上映を追加
                start_time = datetime.strptime(start_time_str, "%H:%M").time()
                day = start_d
                while day <= end_d:
                    week_index = (day - start_d).days // 7
                    if week_index % interval_weeks == 0 and day.weekday() in days_of_week:
                        # 条件にマッチ
                        start_at_dt = datetime.combine(day, start_time)
                        end_at_dt = start_at_dt + timedelta(minutes=movie.duration_min)
                        key = (_to_iso_min(start_at_dt), hall)
                        
                        # 追加
                        desired[key] = {"start_at": _to_iso_min(start_at_dt), "end_at": _to_iso_min(end_at_dt), "price": price}
                    day = day + timedelta(days=1)

            # n月ごとリピート(これいる？)
            elif repeat_type == "2":
                interval_months = _prompt_int("繰り返し間隔(interval_months)", 1, required=True) or 1
                day_of_month = start_d.day
                start_time = datetime.strptime(start_time_str, "%H:%M").time()

                # start_dの月からend_dの月まで、interval_monthsごとに走査
                year = start_d.year
                month = start_d.month

                def _add_months(y: int, m: int, add: int) -> tuple[int, int]:
                    nm = m + add
                    y += (nm - 1) // 12
                    m = ((nm - 1) % 12) + 1
                    return y, m

                while True:
                    try:
                        candidate = date(year, month, day_of_month)
                    except ValueError:
                        # その月に存在しない日(例: 31日)はスキップ
                        candidate = None

                    if candidate is not None and start_d <= candidate <= end_d:
                        start_at_dt = datetime.combine(candidate, start_time)
                        end_at_dt = start_at_dt + timedelta(minutes=movie.duration_min)
                        key = (_to_iso_min(start_at_dt), hall)
                        desired[key] = {"start_at": _to_iso_min(start_at_dt), "end_at": _to_iso_min(end_at_dt), "price": price}

                    # 次の月へ
                    year, month = _add_months(year, month, interval_months)
                    if date(year, month, 1) > end_d.replace(day=1):
                        break

            else:
                console.print("[red]無効な選択です。[/red]")
                input("EnterでAdminMenuに戻ります... ")
                session["next_page"] = "admin_menu"
                return session

        else:
            # 単発
            start_at_input = _prompt_str("開始日時(start_at, YYYY-MM-DDTHH:MM)", None, required=True)
            try:
                start_at_dt = _parse_start_at(start_at_input or "")
            except ValueError:
                console.print("[red]日時形式が不正です(例: 2025-12-24T19:30)。[/red]")
                input("EnterでAdminMenuに戻ります... ")
                session["next_page"] = "admin_menu"
                return session

            end_at_dt = start_at_dt + timedelta(minutes=movie.duration_min)
            key = (_to_iso_min(start_at_dt), hall)
            desired[key] = {"start_at": _to_iso_min(start_at_dt), "end_at": _to_iso_min(end_at_dt), "price": price}

        # 既存showを取得(対象movie_id + hallのみを管理範囲にする)
        existing_shows = db_session.execute(
            select(Show).where(Show.movie_id == movie.id, Show.hall == hall).order_by(Show.start_at)
        ).scalars().all()

        # 既存showをキー付きで辞書化
        existing_by_key: dict[tuple[str, str], Show] = {(s.start_at, s.hall): s for s in existing_shows}

        to_add: list[Show] = []
        to_update: list[Show] = []
        to_delete: list[Show] = []

        # desiredを走査し、追加・更新候補を選定
        for key, info in desired.items():
            if key in existing_by_key:
                s = existing_by_key[key]
                new_end_at = str(info["end_at"])
                new_price = int(info["price"])  # type: ignore[arg-type]
                changed = False
                if s.end_at != new_end_at:
                    s.end_at = new_end_at
                    changed = True
                if s.price != new_price:
                    s.price = new_price
                    changed = True
                if changed:
                    to_update.append(s)
            else:
                to_add.append(
                    Show(
                        movie_id=movie.id,
                        hall=hall,
                        start_at=str(info["start_at"]),
                        end_at=str(info["end_at"]),
                        price=int(info["price"]),  # type: ignore[arg-type]
                    )
                )

        # 削除候補(既存にあって desiredにない)
        desired_keys = set(desired.keys())
        for key, s in existing_by_key.items():
            if key not in desired_keys:
                to_delete.append(s)

        # 変更内容の表示
        console.print("\n[bold]差分[/bold]")
        console.print(f"  add: {len(to_add)}")
        console.print(f"  update: {len(to_update)}")
        console.print(f"  delete: {len(to_delete)}")

        # deleteにticketが付いているか確認
        delete_with_tickets: list[tuple[Show, int]] = []
        if to_delete:
            show_ids = [s.id for s in to_delete]
            counts = db_session.execute(
                #
                select(Ticket.show_id, func.count(Ticket.id)).where(Ticket.show_id.in_(show_ids)).group_by(Ticket.show_id)
            ).all()
            # 該当するチケットの情報のリストが返ってくる
            count_map = {sid: int(cnt) for sid, cnt in counts}
            for s in to_delete:
                cnt = count_map.get(s.id, 0)
                if cnt > 0:
                    delete_with_tickets.append((s, cnt))

        # 操作対象の上映回にticketがある場合は警告
        if delete_with_tickets:
            console.print("\n[yellow]注意: 以下の上映回を削除するとチケットも抹消されます[/yellow]")
            for s, cnt in delete_with_tickets:
                console.print(f"  show_id={s.id} start_at={s.start_at} tickets={cnt}")

        # 確認入力
        confirm = input("この差分を反映しますか? (y/n): ").strip().lower()
        if confirm != "y":
            console.print("[yellow]キャンセルしました。[/yellow]")
            session["next_page"] = "admin_menu"
            return session

        # 反映
        try:
            if to_add:
                db_session.add_all(to_add)

            # deleteはShowを消す(ORM cascadeでTicketも消える)
            for s in to_delete:
                db_session.delete(s)

            # updateはオブジェクトに値を入れているのでcommitで反映
            db_session.commit()

        except Exception as exc:
            db_session.rollback()
            console.print(f"[red]反映に失敗しました: {exc}[/red]")
            input("EnterでAdminMenuに戻ります... ")
            session["next_page"] = "admin_menu"
            return session

    # メニューに戻る
    console.print("[green]スケジュールを更新しました。[/green]")
    input("EnterでAdminMenuに戻ります... ")
    session["next_page"] = "admin_menu"
    return session
