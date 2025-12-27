from datetime import datetime

from rich.console import Console
from rich.table import Table

from sqlalchemy import select

from db.db import SessionLocal
from db.models import Movie, Show, Ticket, TicketSeat
from utils.datetimeFormat import format_ymd_hm

console = Console()


def run(session: dict) -> dict:
    """改札(UUID照合/used_at更新)(管理者向け）"""
    console.print("[bold]AdminGateCheck[/bold]")

    def _now_iso_min() -> str:
        return datetime.now().strftime("%Y-%m-%dT%H:%M")

    # チケットUUIDの入力待ち
    while True:
        ticket_uuid = input("チケットUUIDを入力してください (bで戻る): ").strip()
        if ticket_uuid.lower() in {"b", "back"}:
            session["next_page"] = "admin_menu"
            return session
        if not ticket_uuid:
            session["next_page"] = "admin_menu"
            return session

        # DBから該当するチケットを探す
        with SessionLocal() as db_session:
            ticket = (
                db_session.execute(select(Ticket).where(Ticket.uuid == ticket_uuid))
                .scalar_one_or_none()
            )
            if ticket is None:
                console.print("[red]チケットが見つかりません。[/red]")
                continue
                
            # 関連する上映・映画情報も取得
            show = (
                db_session.execute(select(Show).where(Show.id == ticket.show_id))
                .scalar_one_or_none()
            )
            movie = None
            if show is not None:
                movie = (
                    db_session.execute(select(Movie).where(Movie.id == show.movie_id))
                    .scalar_one_or_none()
                )

            seats = (
                db_session.execute(
                    select(TicketSeat.seat)
                    .where(TicketSeat.ticket_id == ticket.id)
                    .order_by(TicketSeat.seat)
                )
                .scalars()
                .all()
            )

            # 結果表示
            t = Table(title="改札結果")
            t.add_column("項目")
            t.add_column("値")
            t.add_row("UUID", ticket.uuid)
            t.add_row("名前", ticket.user_name or "-")
            t.add_row("座席", ", ".join(seats) if seats else "-")
            if show is not None:
                t.add_row("開始", format_ymd_hm(show.start_at))
                t.add_row("ホール", show.hall)
            if movie is not None:
                t.add_row("映画", movie.title)

            if ticket.used_at:
                t.add_row("状態", "[red]使用済み[/red]")
                t.add_row("使用日時", format_ymd_hm(ticket.used_at) if ticket.used_at else "-")
                console.print(t)
                continue

            # 未使用なら使用済みに更新
            ticket.used_at = _now_iso_min()
            try:
                db_session.commit()
            except Exception as exc:
                db_session.rollback()
                console.print(f"[red]更新に失敗しました: {exc}[/red]")
                continue

            t.add_row("状態", "[green]入場OK[/green]")
            t.add_row("使用日時", format_ymd_hm(ticket.used_at) if ticket.used_at else "-")
            console.print(t)

