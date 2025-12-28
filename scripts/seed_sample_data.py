from __future__ import annotations

"""サンプルデータ投入スクリプト(DBを消さない)。

- 映画を5本作成(同名があれば再利用)
- 2か月分の上映スケジュールを作成
  - 平日(月〜金)のみ
  - 月曜→映画1、火曜→映画2、... 金曜→映画5(週ごとに繰り返し)
  - 1日1回、固定時刻で1ホールのみ(衝突しにくい最小構成)

使い方:
  python scripts/seed_sample_data.py

注意:
- cinema.db が無い場合は abort(先に python db/init_db.py)
"""

import calendar
import os
import sys
from datetime import date, datetime, time, timedelta

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from sqlalchemy import select

from db.db import SessionLocal
from db.models import Movie, Show

DB_PATH = os.path.join(ROOT_DIR, "cinema.db")


def _add_months(d: date, months: int) -> date:
    """dateutil無しで月を足す(同日が無ければ月末に丸める)。"""
    year = d.year + (d.month - 1 + months) // 12
    month = (d.month - 1 + months) % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(d.day, last_day))


def main() -> int:
    if not os.path.exists(DB_PATH):
        print("ERROR: cinema.db が見つかりません(DB未生成)。")
        print("  先に `python db/init_db.py` を実行してDBを作成してください。")
        return 1

    # 5本のサンプル映画
    sample_movies: list[dict[str, object]] = [
        {
            "title": "サンプル映画1: 月曜アクション",
            "duration_min": 110,
            "default_price": 1800,
            "tags_json": '["action"]',
            "description": "月曜日の定番アクション。",
        },
        {
            "title": "サンプル映画2: 火曜ミステリー",
            "duration_min": 105,
            "default_price": 1700,
            "tags_json": '["mystery"]',
            "description": "火曜日は推理で頭を使う。",
        },
        {
            "title": "サンプル映画3: 水曜コメディ",
            "duration_min": 95,
            "default_price": 1600,
            "tags_json": '["comedy"]',
            "description": "水曜日は気軽に笑える。",
        },
        {
            "title": "サンプル映画4: 木曜ドラマ",
            "duration_min": 120,
            "default_price": 1800,
            "tags_json": '["drama"]',
            "description": "木曜はしっとりドラマ。",
        },
        {
            "title": "サンプル映画5: 金曜ファンタジー",
            "duration_min": 130,
            "default_price": 1900,
            "tags_json": '["fantasy"]',
            "description": "金曜は非日常へ。",
        },
    ]

    # 期間: 今日〜2か月後(同日)まで
    start_d = date.today()
    end_d = _add_months(start_d, 2)

    # 19:00開始、ホールA固定
    start_t = time(19, 0)
    hall = "A"

    # 処理用のカウンタ変数
    created_movies = 0
    reused_movies = 0
    created_shows = 0
    skipped_shows = 0

    with SessionLocal() as db_session:
        # 既存映画は「必要なタイトルだけ」取る
        titles = [str(m["title"]) for m in sample_movies]
        existing = db_session.execute(select(Movie).where(Movie.title.in_(titles))).scalars().all()
        movie_by_title = {m.title: m for m in existing}

        # 月〜金(0..4)に対応する movie_id を作る
        weekday_movie_ids: dict[int, int] = {}
        for weekday, mdef in enumerate(sample_movies):
            title = str(mdef["title"])
            movie = movie_by_title.get(title)
        
            if movie is None:
                movie = Movie(
                    title=title,
                    duration_min=int(mdef["duration_min"]),
                    default_price=int(mdef["default_price"]),
                    tags_json=str(mdef["tags_json"]),
                    description=str(mdef["description"]),
                    run_start_date=start_d.isoformat(),
                    run_end_date=end_d.isoformat(),
                )
                db_session.add(movie)
                db_session.flush()  # movie.id 確定
                created_movies += 1
            else:
                reused_movies += 1

            weekday_movie_ids[weekday] = int(movie.id)

        # ここから上映スケジュール作成
        d = start_d
        while d <= end_d:
            wd = d.weekday()  # 0=Mon ... 6=Sun
            if 0 <= wd <= 4:
                movie_id = weekday_movie_ids[wd]
                start_dt = datetime.combine(d, start_t)
                start_at = start_dt.strftime("%Y-%m-%dT%H:%M")

                # 既に同一(hall, start_at)があればスキップ
                exists = db_session.execute(
                    select(Show.id).where(Show.hall == hall, Show.start_at == start_at)
                ).first()
                if exists is not None:
                    skipped_shows += 1
                else:
                    movie = db_session.execute(select(Movie).where(Movie.id == movie_id)).scalar_one()
                    end_dt = start_dt + timedelta(minutes=int(movie.duration_min))
                    end_at = end_dt.strftime("%Y-%m-%dT%H:%M")

                    # 上映回の登録
                    show = Show(
                        movie_id=movie_id,
                        hall=hall,
                        start_at=start_at,
                        end_at=end_at,
                        price=int(movie.default_price or 0),
                    )
                    db_session.add(show)
                    created_shows += 1

            d += timedelta(days=1)

        db_session.commit()

    print("OK: seeded sample data")
    print(f"  movies: created={created_movies}, reused={reused_movies}")
    print(f"  shows:  created={created_shows}, skipped(existing)={skipped_shows}")
    print(f"  range:  {start_d.isoformat()} .. {end_d.isoformat()} (weekdays only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
