from __future__ import annotations

import json                                     # JSON操作用
import uuid                                     # UUID生成用
from decimal import Decimal, ROUND_HALF_UP      # 料金計算用, ROUND_HALF_UPは四捨五入用
from datetime import datetime                   # 発行日時用 

from rich.console import Console

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError # DB操作用、例外処理

from db.db import SessionLocal
from db.models import Movie, Show, Ticket, TicketSeat # DBのmovie, Show, Ticket, TicketSeatモデルをインポート

console = Console(highlight=False)


# 料金ルール（必要ならここだけ触ればOK）
# - base_price (= show.price) に倍率を掛ける
# - Decimal文字列で書くと丸めが安定する
PRICE_RULES: dict[str, dict[str, str]] = {
    "adult": {"label": "一般", "mult": "1.0"},
    "college": {"label": "大学生", "mult": "0.8"},
    "highschool": {"label": "高校生", "mult": "0.7"},
    "junior": {"label": "小中学生", "mult": "0.6"},
    "child": {"label": "幼児(3歳以上)", "mult": "0.5"},
    "senior": {"label": "シニア(60歳以上)", "mult": "0.7"},
    "disabled": {"label": "障がい者割引", "mult": "0.7"},
    "other": {"label": "その他", "mult": "1.0"},
}

# 会員割引（合計に対して倍率を掛ける）
MEMBER_DISCOUNT_MULT = Decimal("0.8")


def run(session: dict) -> dict:
    # 購入/確定（最小）
    # - SeatSelectで選ばれた座席を使って Ticket + TicketSeat を作成する

    console.print("[bold][UserCheckout][/bold]")

    user_id = session.get("user_id")
    user_name = (session.get("user_name") or "").strip()
    if not isinstance(user_id, str) or not user_id.strip() or not user_name:
        console.print("[yellow]ログインが必要です。ログイン画面に戻ります。[/yellow]")
        session["next_page"] = "login"
        return session

    show_id = session.get("show_id")
    selected_seats = session.get("selected_seats")

    # 例外処理(普通はここ通らないはず)
    if show_id is None or not isinstance(show_id, int):
        console.print("[red]show_idが未設定です。[/red]")
        input("Enterで上映回選択に戻ります... ")
        session["next_page"] = "user_show_select"
        return session

    if not isinstance(selected_seats, list) or len(selected_seats) == 0:
        console.print("[red]座席が未選択です。[/red]")
        input("Enterで座席選択に戻ります... ")
        session["next_page"] = "user_seat_select"
        return session

    # 入力補助用、他のファイルにあるのと同じ
    def _prompt_int(label: str, default: int | None = None, required: bool = False) -> int | None:
        while True:
            cur = "" if default is None else str(default)
            raw = input(f"{label} [{cur}]: ").strip()
            if raw == "":
                if required and default is None:
                    console.print("[red]必須です。[/red]")
                    continue
                return default
            if not raw.isdigit():
                console.print("[red]数字で入力してください。[/red]")
                continue
            return int(raw)

    def _prompt_str(label: str, default: str | None = None, required: bool = False) -> str | None:
        while True:
            cur = "" if default is None else default
            raw = input(f"{label} [{cur}]: ").strip()
            if raw == "":
                if required and default is None:
                    console.print("[red]必須です。[/red]")
                    continue
                return default
            return raw

    # 名前はログインユーザーIDを使用（Ticket表示用に保存）
    # ※ 認証導入後は、購入者の識別は user_id で行う

    # 追加のユーザー情報
    age = session.get("age")
    if not isinstance(age, int):
        age = _prompt_int("年齢(空Enterで省略)", None, required=False)
        session["age"] = age

    sex = session.get("sex")
    if not isinstance(sex, str) or sex.strip() == "":
        sex = _prompt_str("性別(例: M/F/Other, 空Enterで省略)", None, required=False)
        session["sex"] = sex

    is_member = session.get("is_member")
    if not isinstance(is_member, int):
        raw_member = input("会員ですか? (y/n, 空Enterでn): ").strip().lower()
        is_member = 1 if raw_member == "y" else 0
        session["is_member"] = is_member
    
    # 予約情報登録
    with SessionLocal() as db_session:
        # 該当するshowの情報を取得
        show = db_session.execute(select(Show).where(Show.id == show_id)).scalar_one_or_none()
        if show is None:
            console.print("[red]上映回が見つかりません。[/red]")
            input("Enterで上映回選択に戻ります... ")
            session["next_page"] = "user_show_select"
            return session
        
        # 上映タイトルの情報を取得
        movie = db_session.execute(select(Movie).where(Movie.id == show.movie_id)).scalar_one_or_none()
        movie_title = movie.title if movie is not None else "(unknown)"

        # 内訳(breakdown)入力
        seat_count = len(selected_seats)
        console.print(f"\n枚数(座席数): {seat_count}")
        console.print("内訳を入力してください（合計が座席数になる必要があります）")
        console.print("料金ルール: base_price (= show.price) x mult")

        # 予約種別ごとに枚数を入力
        # 例：child: 2, adult: 1 みたいに
        while True:
            breakdown: dict[str, int] = {}
            total = 0
            for key, rule in PRICE_RULES.items():
                label = rule["label"]
                cnt = _prompt_int(f"{label}({key}) 枚数", 0, required=True) or 0
                if cnt < 0:
                    console.print("[red]0以上で入力してください。[/red]")
                    break
                breakdown[key] = cnt
                total += cnt

            if total != seat_count:
                console.print(f"[red]内訳の合計({total})が座席数({seat_count})と一致しません。[/red]")
                retry = input("再入力しますか? (y/n): ").strip().lower()
                if retry == "y":
                    continue
                session["next_page"] = "user_seat_select"
                return session

            break

        # 合計金額計算（内訳×倍率）
        base_price = Decimal(str(show.price))
        sum_price_dec = Decimal("0")
        unit_prices: dict[str, int] = {}

        # 単価計算、種別ごとに倍率適用
        for key, cnt in breakdown.items():
            mult = Decimal(PRICE_RULES[key]["mult"])
            unit = (base_price * mult).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            unit_prices[key] = int(unit)
            sum_price_dec += unit * Decimal(cnt)

        # 会員割引適用
        pre_discount = sum_price_dec
        if int(is_member) == 1:
            sum_price_dec = (sum_price_dec * MEMBER_DISCOUNT_MULT).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        sum_price = int(sum_price_dec)

        # 保存用に内訳データをJSON化
        breakdown_json = json.dumps(breakdown, ensure_ascii=False)

        # 確認表示
        console.print(f"\n映画: {movie_title}")
        console.print(f"上映: show_id={show.id} hall={show.hall} start_at={show.start_at}")
        console.print(f"座席: {', '.join(selected_seats)}")
        console.print("\n[bold]内訳[/bold]")
        for key, cnt in breakdown.items():
            if cnt <= 0:
                continue
            label = PRICE_RULES[key]["label"]
            console.print(f"  {label}: {cnt} × {unit_prices[key]}円")

        if int(is_member) == 1:
            console.print(f"\n会員割引: ×{MEMBER_DISCOUNT_MULT}（{int(pre_discount)}円 → {sum_price}円）")
        console.print(f"\n合計: {sum_price} 円")

        confirm = input("購入を確定しますか? (y/n): ").strip().lower()
        if confirm != "y":
            console.print("[yellow]キャンセルしました。[/yellow]")
            session["next_page"] = "user_seat_select"
            return session

        # Ticket + TicketSeat情報確定
        issued_at = datetime.now().strftime("%Y-%m-%dT%H:%M")
        ticket = Ticket(
            uuid=str(uuid.uuid4()),
            show_id=show.id,
            user_id=str(user_id),
            user_name=user_name,
            age=age,
            sex=sex,
            is_member=int(is_member),
            breakdown_json=breakdown_json,
            sum_price=sum_price,
            issued_at=issued_at,
        )

        ticket_uuid = str(ticket.uuid)

        # 登録実行
        try:
            # DBへの書き込みをリクエスト
            db_session.add(ticket)
            db_session.flush()  # ticket.id を確定させる

            for seat in selected_seats:
                db_session.add(
                    TicketSeat(
                        ticket_id=ticket.id,
                        show_id=show.id,
                        seat=str(seat),
                    )
                )

            db_session.commit()
        except IntegrityError:
            # 弾かれた場合のパス(重複予約時)
            db_session.rollback()
            console.print("[red]購入に失敗しました（他の人が先に予約した可能性があります）。[/red]")
            input("Enterで座席選択に戻ります... ")
            session["next_page"] = "user_seat_select"
            return session
        except Exception as exc:
            # その他のエラー時
            db_session.rollback()
            console.print(f"[red]購入に失敗しました: {exc}[/red]")
            input("Enterで座席選択に戻ります... ")
            session["next_page"] = "user_seat_select"
            return session

    # チケット表示へ遷移
    session["ticket_uuid"] = ticket_uuid
    session["next_page"] = "user_ticket_qr"
    return session
