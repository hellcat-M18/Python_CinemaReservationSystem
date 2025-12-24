import rich
from rich.console import Console

console = Console()


def run(session: dict) -> dict:
	"""映画一覧（旧ファイル名／用途未確定）（WIP）"""
	console.print("[bold]movieList[/bold] (WIP)")
	# TODO: 役割が管理者/ユーザーどちらか決めて、適切なページへ統合 or リネーム
	return session

