import rich
from rich.console import Console

console = Console()


def run(session: dict) -> dict:
    """改札（UUID照合/used_at更新）（管理者向け）（WIP）"""
    console.print("[bold]AdminGateCheck[/bold] (WIP)")
    # TODO: uuid入力→Ticket検索→used_atを確認し、未使用なら使用済みに更新
    return session
