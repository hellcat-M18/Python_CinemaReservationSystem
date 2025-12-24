import rich
from rich.console import Console

from utils import QRGenerator

console = Console()


def run(session: dict) -> dict:
    # チケット表示(QR)
    # 事前に session["ticket_uuid"] が入っている想定(UserMenuで手入力)

    console.print("[bold]UserTicketQR[/bold]")

    ticket_uuid = session.get("ticket_uuid")
    if not ticket_uuid:
        console.print("[yellow]ticket_uuid が見つかりません。UserMenuに戻ります。[/yellow]")
        session["next_page"] = "user_menu"
        return session
    
    # 後でDBとの照合を入れる

    console.print(f"UUID: [bold]{ticket_uuid}[/bold]")
    QRGenerator.print(ticket_uuid)

    input("\nEnterでメニューに戻ります... ")
    session["next_page"] = "user_menu"
    return session
