import rich
from rich.console import Console

console = Console()


def run(session: dict) -> dict:
    """購入/入力（ユーザー情報・枚数内訳など）（WIP）"""
    console.print("[bold]UserCheckout[/bold] (WIP)")
    # TODO: user_name/age/sex/is_member, breakdown, sum_price を確定
    # TODO: Ticket + TicketSeat を作成
    return session
