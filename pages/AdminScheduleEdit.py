from rich.console import Console
from rich.table import Table

from utils.rich_compat import TABLE_KWARGS

from datetime import date, datetime, timedelta # 日付・時間操作用

from sqlalchemy import func, select  # DB操作用、集約関数func、Select文 

from db.db import SessionLocal # DB操作のセッションを生成するクラス
from db.models import Movie, Show, Ticket   # テーブル"Movie", "Show", "Ticket"のモデルをインポート

console = Console(highlight=False)


def run(session: dict) -> dict:
    # 上映スケジュールの設定・編集(差分反映含む)
    # - show は「単一の上映回」を表す
    # - ここで入力されたルールから start_at/end_at を生成し、DBのshowsに差分反映する
    # - 既存showの削除が発生する場合は警告して y/n を取る(yなら該当ticketも抹消される)

    console.print("[bold][AdminScheduleEdit][/bold]")

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

    # ISO文字列(YYYY-MM-DDTHH:MM)をdatetime型に変換する関数
    def _parse_iso_min(value: str) -> datetime:
        v = str(value).strip().replace(" ", "T")
        return datetime.strptime(v, "%Y-%m-%dT%H:%M")

    def _to_iso_min(dt: datetime) -> str:
        return dt.strftime("%Y-%m-%dT%H:%M")

    # 最初に映画一覧を表示（movie_id入力の助け）
    with SessionLocal() as db_session:
        movies = db_session.execute(select(Movie).order_by(Movie.id)).scalars().all()

    if movies:
        table = Table(title="映画一覧", **TABLE_KWARGS)
        table.add_column("id", justify="right")
        table.add_column("title")
        table.add_column("上映期間")
        table.add_column("duration", justify="right")
        table.add_column("default_price", justify="right")
        for m in movies:
            run_range = f"{m.run_start_date or '-'} ~ {m.run_end_date or '-'}"
            table.add_row(
                str(m.id),
                m.title,
                run_range,
                f"{m.duration_min}min",
                str(m.default_price),
            )
        console.print(table)
    else:
        console.print("[yellow]映画が未登録です。先に映画を追加してください。[/yellow]")

    # 入力: movie_id
    # sessionのデータを読み取り
    movie_id = session.get("movie_id")
    movie_id = _prompt_int("対象movie_id", movie_id, required=True)
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

            # 繰り返しの開始日と終了日は映画そのものの上映期間を既定値として使う
            start_date_str = _prompt_date(
                "開始日(start_date, YYYY-MM-DD)",
                movie.run_start_date,
                required=True,
            )
            end_date_str = _prompt_date(
                "終了日(end_date, YYYY-MM-DD)",
                movie.run_end_date,
                required=True,
            )
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

                # 曜日ごとに開始時刻(複数)を入力
                console.print("\n各曜日の開始時刻をカンマ区切りで入力してください(例: 10:00, 13:30, 19:00)")
                times_by_dow: dict[int, list[datetime.time]] = {}
                for dow in sorted(days_of_week):
                    while True:
                        raw = _prompt_str(f"start_times for {dow} (HH:MM,HH:MM...)", None, required=True) or ""
                        parts = [p.strip() for p in raw.split(",") if p.strip()]
                        if not parts:
                            console.print("[red]少なくとも1つは開始時刻を入力してください。[/red]")
                            continue
                        parsed: list[datetime.time] = []
                        ok = True
                        for p in parts:
                            try:
                                parsed.append(datetime.strptime(p, "%H:%M").time())
                            except ValueError:
                                console.print(f"[red]HH:MM形式で入力してください: {p}[/red]")
                                ok = False
                                break
                        if not ok:
                            continue
                        # 重複を落としてソート（同じ曜日に同じ時刻を入れても1回にする）
                        unique_sorted = sorted(set(parsed))
                        times_by_dow[dow] = unique_sorted
                        break

                # start_dからend_dまで走査し、該当曜日かつinterval_weeksごとに上映を追加
                # 上映はここで一括生成
                day = start_d
                while day <= end_d:
                    week_index = (day - start_d).days // 7
                    if week_index % interval_weeks == 0 and day.weekday() in days_of_week:
                        for start_time in times_by_dow.get(day.weekday(), []):
                            start_at_dt = datetime.combine(day, start_time)
                            end_at_dt = start_at_dt + timedelta(minutes=movie.duration_min)
                            key = (_to_iso_min(start_at_dt), hall)
                            desired[key] = {
                                "start_at": _to_iso_min(start_at_dt),
                                "end_at": _to_iso_min(end_at_dt),
                                "price": price,
                            }
                    day = day + timedelta(days=1)

            # n月ごとリピート(これいる？)
            elif repeat_type == "2":
                start_time_str = _prompt_time("開始時刻(start_time, HH:MM)", None, required=True)
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
            # 単発上映
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

        # ---- スケジュール衝突チェック（同一hallで時間帯が被る） ----
        # まず自分自身との衝突チェック
        desired_intervals: list[tuple[str, str]] = []
        for info in desired.values():
            desired_intervals.append((str(info["start_at"]), str(info["end_at"])))
        desired_intervals.sort(key=lambda x: x[0])

        # 設定した上映会について、前回の終了時刻と次の開始時刻を比較して衝突を検知
        internal_conflicts: list[tuple[str, str, str, str]] = []
        prev_start: str | None = None
        prev_end: str | None = None
        for start_s, end_s in desired_intervals:
            if prev_start is not None and prev_end is not None:
                # ISO文字列は辞書順で時系列になる前提（YYYY-MM-DDTHH:MM）
                if start_s < prev_end:
                    internal_conflicts.append((prev_start, prev_end, start_s, end_s))
            prev_start, prev_end = start_s, end_s

        # 衝突する箇所が見つかれば警告
        if internal_conflicts:
            console.print("\n[red]エラー: 同一ホール内で上映時間が重複しています（入力したスケジュール同士の衝突）。[/red]")
            ctbl = Table(title=f"衝突(入力内) hall={hall}", **TABLE_KWARGS)
            ctbl.add_column("枠A")
            ctbl.add_column("枠B")
            for a_start, a_end, b_start, b_end in internal_conflicts:
                ctbl.add_row(f"{a_start} ~ {a_end}", f"{b_start} ~ {b_end}")
            console.print(ctbl)
            input("EnterでAdminMenuに戻ります... ")
            session["next_page"] = "admin_menu"
            return session

        # 既存show（他movie含む）との衝突
        if desired_intervals:
            # 入力範囲のうち一番最初の上映回の開始時刻
            min_start = desired_intervals[0][0]

            # 入力範囲のうち一番最後の上映回の終了時刻
            max_end = max(e for _, e in desired_intervals)

            # ↑これらはおおまかな範囲指定用

            # 管理対象(movie+hall)の既存showは除外（自分自身との衝突は上で検知済み）
            ignore_ids = {s.id for s in existing_shows}

            # 同一のhallで、今回の入力範囲内に存在する上映回を取得
            hall_candidates = (
                db_session.execute(
                    select(Show)
                    .where(
                        Show.hall == hall,
                        Show.start_at < max_end,
                        Show.end_at > min_start,
                    )
                    .order_by(Show.start_at)
                )
                .scalars()
                .all()
            )

            other_shows = [s for s in hall_candidates if s.id not in ignore_ids]

            # 個別に時間を比較して実際に衝突しているものを抽出
            external_conflicts: list[tuple[str, str, Show]] = []
            for start_s, end_s in desired_intervals:
                ds = _parse_iso_min(start_s)
                de = _parse_iso_min(end_s)
                for s in other_shows:
                    ss = _parse_iso_min(s.start_at)
                    se = _parse_iso_min(s.end_at)
                    if ds < se and de > ss:
                        external_conflicts.append((start_s, end_s, s))

            if external_conflicts:
                movie_ids = list({c[2].movie_id for c in external_conflicts})
                movies2 = (
                    db_session.execute(select(Movie).where(Movie.id.in_(movie_ids)))
                    .scalars()
                    .all()
                )
                movie_map2 = {m.id: m for m in movies2}

                console.print("\n[yellow]警告: 同一ホールで他の上映と時間帯が重複しています。[/yellow]")
                etbl = Table(title=f"衝突(既存) hall={hall}", **TABLE_KWARGS)
                etbl.add_column("入力した枠")
                etbl.add_column("既存show")
                etbl.add_column("映画")
                for d_start, d_end, s in external_conflicts:
                    m = movie_map2.get(s.movie_id)
                    etbl.add_row(
                        f"{d_start} ~ {d_end}",
                        f"show_id={s.id} {s.start_at} ~ {s.end_at}",
                        m.title if m is not None else f"movie_id={s.movie_id}",
                    )
                console.print(etbl)

                proceed = input("衝突があります。このまま反映しますか? (y/n): ").strip().lower()
                if proceed != "y":
                    console.print("[yellow]キャンセルしました。[/yellow]")
                    session["next_page"] = "admin_menu"
                    return session

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
