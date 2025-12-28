import rich
from rich.console import Console

console = Console(highlight=False)


def run(session: dict) -> dict:
    """上映スケジュール確定（差分反映/削除警告）（管理者向け）（WIP）"""
    console.print("[bold][AdminScheduleConfirm][/bold] (WIP)")
    # TODO: 既存Showとの差分を表示
    # TODO: Ticket付きShowの削除が発生するなら警告→y/n→yならTicket抹消してShow削除
    # TODO: 追加/更新/削除を反映
    return session
