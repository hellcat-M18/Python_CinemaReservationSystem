import rich
from rich.console import Console

console = Console()


def run(session: dict) -> dict:
    """映画削除（管理者向け）（WIP）"""
    console.print("[bold]AdminMovieDelete[/bold] (WIP)")
    # TODO: 対象映画の確認→y/n→削除
    # NOTE: Movie->Show->Ticket まで ORM cascade で消える設計
    return session
