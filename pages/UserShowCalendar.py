from __future__ import annotations

import re  #正規表現モジュール
import calendar
from datetime import date, datetime, timedelta

from rich.console import Console    # 印字用
from rich.table import Table    # テーブル表示用

from sqlalchemy import select

from db.db import SessionLocal
from db.models import Movie, Show

console = Console(highlight=False)


_MONTH_RE = re.compile(r"^(\d{4})[-/](\d{1,2})$") #YYYY-MM形式の正規表現

# 月初と月末のISOフォーマット(YYYY-MM-DDTHH:MM)を取得
def _month_bounds(year: int, month: int) -> tuple[str, str]:
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
    return start.strftime("%Y-%m-%dT%H:%M"), end.strftime("%Y-%m-%dT%H:%M")

# カレンダー表示
def _render_calendar(year: int, month: int, show_days: set[int]) -> None:
    cal = calendar.Calendar(firstweekday=6)  # Sunday start

    # テーブル作成
    title = f"{year}/{month:02d}"
    table = Table(title=f"上映カレンダー ({title})", show_header=True, header_style="bold")

    # 曜日ヘッダー追加
    for name in ["日", "月", "火", "水", "木", "金", "土"]:
        table.add_column(name, justify="center", no_wrap=True)
    
    # 日付行を追加
    for week in cal.monthdayscalendar(year, month):
        row: list[str] = []
        for d in week:
            if d == 0:
                row.append(" ")
                continue
            
            # 上映がある日なら緑で表示
            if d in show_days:
                row.append(f"[#00ff00]{d:2d}[/]")
            else:
                row.append(f"{d:2d}")

        table.add_row(*row)

    # コンソールに印字
    console.print(table)
    console.print("[#00ff00]緑[/] = 上映あり")

# ページ本体
def run(session: dict) -> dict:
    console.print("[bold][UserShowCalendar][/bold]")

    # movie_idを遷移元から引き継ぎ
    movie_id = session.get("movie_id")
    if movie_id is None:
        console.print("[red]movie_idが未設定です。[/red]")
        input("Enterで映画一覧に戻ります... ")
        session["next_page"] = "user_movie_browse"
        return session

    # 初期表示月（前回の表示を保持しつつ、なければ今月を表示）
    today = date.today()
    year = session.get("calendar_year")
    month = session.get("calendar_month")
    if not isinstance(year, int) or not isinstance(month, int):# isinstanceで型チェック
        year, month = today.year, today.month

    # 入力を受け付けるメインループ
    while True:
        # movie名 + 指定された月の上映日セットを取得
        with SessionLocal() as db_session:
            # 対象の映画の情報を取得
            movie = db_session.execute(select(Movie).where(Movie.id == movie_id)).scalar_one_or_none()

            # 範囲の定義
            month_start, month_end = _month_bounds(year, month)

            # 指定月の上映回を取得
            # 指定された映画ID && 開始日時が月初以降 && 開始日時が月末前
            shows = (
                db_session.execute(
                    select(Show)
                    .where(Show.movie_id == movie_id)
                    .where(Show.start_at >= month_start)
                    .where(Show.start_at < month_end)
                )

                # 結果から余分な情報を取り除き、リストとして返却
                .scalars()
                .all()
            )

        movie_title = movie.title if movie is not None else "(unknown)"
        console.print(f"映画: {movie_title} (movie_id={movie_id})")

        # 上映がある日だけを抽出
        show_days: set[int] = set()
        for s in shows:
            # ISO: YYYY-MM-DDTHH:MM の想定
            try:
                # スライスで日付部分だけを取りだし、セットに追加
                show_days.add(int(str(s.start_at)[8:10]))
            
            # 例外はゴミ箱にぶん投げる
            except Exception:
                continue
        
        # カレンダーを表示
        _render_calendar(year, month, show_days)

        # ユーザー入力受付
        raw = input("日付を選択 (1-31) / n次月 p前月 / YYYY-MMで月指定 / bで戻る: ").strip().lower()

        # bなら映画一覧に戻る
        if raw in {"b", "back"}:
            session.pop("selected_date", None)
            session["next_page"] = "user_movie_browse"
            return session

        # nで次月、pで前月
        if raw in {"n", ">"}:
            if month == 12:
                year += 1
                month = 1
            else:
                month += 1
            session["calendar_year"], session["calendar_month"] = year, month
            continue

        if raw in {"p", "<"}:
            if month == 1:
                year -= 1
                month = 12
            else:
                month -= 1
            session["calendar_year"], session["calendar_month"] = year, month
            continue
        
        # YYYY-MM形式でのダイレクト指定
        m = _MONTH_RE.match(raw)
        if m:
            y = int(m.group(1))
            mo = int(m.group(2))
            if 1 <= mo <= 12:
                year, month = y, mo
                session["calendar_year"], session["calendar_month"] = year, month
                continue
            console.print("[red]月は1〜12で指定してください。[/red]")
            continue
        
        # 日付指定の際に数値かどうかチェック
        if not raw.isdigit():
            console.print("[red]入力が不正です。[/red]")
            continue

        # 範囲チェックと存在チェック
        day = int(raw)
        try:
            selected = date(year, month, day)
        except ValueError:
            console.print("[red]その日付は存在しません。[/red]")
            continue

        if day not in show_days:
            console.print("[yellow]その日は上映がありません。[/yellow]")
            continue
        
        # 日付を保存して上映回選択へ
        session["selected_date"] = selected.strftime("%Y-%m-%d")
        session["calendar_year"], session["calendar_month"] = year, month
        session["next_page"] = "user_show_select"
        return session
