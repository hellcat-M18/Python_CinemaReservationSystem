import rich
from rich.console import Console

from utils import QRGenerator

console = Console()


def run(session: dict) -> dict:
    """チケット表示（QR）(WIP)"""
    console.print("[bold]UserTicketQR[/bold] (WIP)")
    # TODO: sessionからticket_uuidを取り出してQRを表示
    # QRGenerator.print(ticket_uuid)
    return session
