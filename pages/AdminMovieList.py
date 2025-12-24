import rich
from rich.console import Console

console = Console()


def run(session: dict) -> dict:
    """映画一覧（管理者向け）（WIP）"""
    console.print("[bold]AdminMovieList[/bold] (WIP)")
    # TODO: DBからmoviesを一覧表示
    # TODO: 追加/編集/削除/スケジュール編集へ遷移
    return session
