import json
from rich.console import Console
from rich.table import Table

from sqlalchemy import select

from db.db import SessionLocal
from db.models import Movie, Show, Ticket, TicketSeat
from utils.datetimeFormat import format_ymd_hm
from utils import QRGenerator
from utils.rich_compat import TABLE_KWARGS

console = Console(highlight=False)


def run(session: dict) -> dict:
    # チケット表示(QR)
    # 事前に session["ticket_uuid"] が入っている想定(UserMenuで手入力 / 購入後)

    console.print("[bold][UserTicketQR][/bold]")

    ticket_uuid = session.get("ticket_uuid")
    if not ticket_uuid:
        console.print("[yellow]ticket_uuid が見つかりません。UserMenuに戻ります。[/yellow]")
        session["next_page"] = "user_menu"
        return session

    # ログイン済みユーザーは「自分のチケットのみ」表示
    user_role = session.get("user_role")
    user_id = session.get("user_id")

    # DB照合してチケット詳細を表示
    with SessionLocal() as db_session:
        ticket = db_session.execute(select(Ticket).where(Ticket.uuid == str(ticket_uuid))).scalar_one_or_none()
        if ticket is None:
            console.print("[red]チケットが見つかりません。UUIDを確認してください。[/red]")
            input("Enterでメニューに戻ります... ")
            session["next_page"] = "user_menu"
            return session

        if user_role == "User" and isinstance(user_id, str) and user_id.strip():
            if str(ticket.user_id) != str(user_id):
                console.print("[yellow]このチケットはあなたのアカウントに紐づいていないため表示できません。[/yellow]")
                input("Enterでメニューに戻ります... ")
                session["next_page"] = "user_menu"
                return session

        # ユーザー側には使用済みチケットを見せない
        if ticket.used_at:
            console.print("[yellow]このチケットは使用済みのため表示できません。[/yellow]")
            input("Enterでメニューに戻ります... ")
            session["next_page"] = "user_menu"
            return session

        # 関連する上映・映画情報を取得
        show = db_session.execute(select(Show).where(Show.id == ticket.show_id)).scalar_one_or_none()
        movie = None
        if show is not None:
            movie = db_session.execute(select(Movie).where(Movie.id == show.movie_id)).scalar_one_or_none()

        seats = (
            db_session.execute(
                select(TicketSeat.seat)
                .where(TicketSeat.ticket_id == ticket.id)
                .order_by(TicketSeat.seat)
            )
            .scalars()
            .all()
        )

    # 表示
    console.print("\n[yellow]UUIDは照合のために保管をお願いします[/yellow]")
    console.print(f"UUID: [bold]{ticket.uuid}[/bold]\n")

    purchaser = Table(title="購入者情報", **TABLE_KWARGS)
    purchaser.add_column("項目")
    purchaser.add_column("値")
    purchaser.add_row("名前", str(ticket.user_name) if ticket.user_name else "-")
    purchaser.add_row("年齢", str(ticket.age) if ticket.age is not None else "-")
    purchaser.add_row("性別", str(ticket.sex) if ticket.sex else "-")
    purchaser.add_row("会員", "はい" if int(ticket.is_member or 0) == 1 else "いいえ")
    console.print(purchaser)
    
    # チケット情報表示
    info = Table(title="チケット情報", **TABLE_KWARGS)
    info.add_column("項目")
    info.add_column("値")

    movie_title = movie.title if movie is not None else "(unknown)"
    info.add_row("映画", movie_title)
    if show is not None:
        info.add_row("上映", f"show_id={show.id}")
        info.add_row("ホール", show.hall)
        info.add_row("開始", format_ymd_hm(show.start_at))
        info.add_row("終了", format_ymd_hm(show.end_at))
        info.add_row("基本料金", f"{show.price} 円")
    else:
        info.add_row("上映", "(showが見つかりません)")

    info.add_row("座席", ", ".join(seats) if seats else "-")
    info.add_row("発行", str(ticket.issued_at) if ticket.issued_at else "-")
    info.add_row("使用", str(ticket.used_at) if ticket.used_at else "未使用")
    info.add_row("合計", f"{ticket.sum_price} 円")
    console.print(info)

    # 内訳表示（あれば）
    try:
        breakdown = json.loads(ticket.breakdown_json or "{}")
    except Exception:
        breakdown = {}

    if isinstance(breakdown, dict) and len(breakdown) > 0:
        labels = {
            "adult": "一般",
            "child": "子供",
            "disabled": "障碍者",
            "other": "その他",
        }
        bd = Table(title="内訳", **TABLE_KWARGS)
        bd.add_column("区分")
        bd.add_column("枚数", justify="right")
        for k, v in breakdown.items():
            try:
                cnt = int(v)
            except Exception:
                continue
            if cnt <= 0:
                continue
            bd.add_row(labels.get(str(k), str(k)), str(cnt))
        if bd.row_count > 0:
            console.print(bd)

    # QRコード表示
    console.print("\n[bold]QRコード[/bold]")
    QRGenerator.print(str(ticket.uuid))

    input("\nEnterでメニューに戻ります... ")
    session["next_page"] = "user_menu"
    return session
