import rich
from rich.console import Console

console = Console()


def run(session: dict) -> dict:
    """映画追加/編集（管理者向け）（WIP）"""
    console.print("[bold]AdminMovieEdit[/bold] (WIP)")
    # TODO: title/description/tags/duration/run_start_date/run_end_date を入力して保存
    # TODO: 生成するShowのデフォルトpriceも入力する運用なら、ここで受け取る
    return session
