import rich
from rich.console import Console

console = Console()


def run(session: dict) -> dict:
    """上映スケジュール設定/編集（管理者向け）（WIP）"""
    console.print("[bold]AdminScheduleEdit[/bold] (WIP)")
    # TODO: hall(レイアウトキー/ファイル名), price, start/end, 繰り返し(weekly/monthly/interval)等を入力
    # TODO: 入力ルールをsessionに保持し、確定ページへ
    return session
