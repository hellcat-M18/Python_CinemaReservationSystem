from __future__ import annotations

from dataclasses import dataclass # dataclass: クラスの定義を簡潔に書くためのモジュール。__init__などを自動で生成してくれる。
from pathlib import Path          # ファイルパス操作用モジュール
from typing import Iterable       # 型ヒント用モジュール

from rich.console import Console  # richライブラリのConsoleクラスをインポート
from rich.table import Table      # richライブラリのTableクラスをインポート

from utils.rich_compat import TABLE_KWARGS

# 映画館のホールレイアウトを扱うユーティリティ
@dataclass(frozen=True)
class HallLayout:
    hall: str
    lines: list[str]

    def seat_ids(self) -> list[str]:
        # レイアウトの'#'だけを座席として扱う
        # 座席IDは "A-1" 形式（行=英字、列=その行の座席番号）
        seat_ids: list[str] = []

        # 行ラベルは「空行を除いた行番号」で連番にする
        row_no = 0
        for raw in self.lines:
            line = raw.rstrip("\n")
            if line.strip() == "":
                continue

            row_letter = chr(ord("A") + row_no)
            row_no += 1

            col_no = 0
            for ch in line:
                if ch == "#":
                    col_no += 1
                    seat_ids.append(f"{row_letter}-{col_no}")

        return seat_ids

# レイアウトファイルの格納ディレクトリを取得
def _layouts_dir() -> Path:
    # utils/ の1つ上がプロジェクトルート想定
    return Path(__file__).resolve().parent.parent / "layouts"

# ホールのレイアウトをファイルから読み込む
def load_layout(hall: str) -> HallLayout:
    path = _layouts_dir() / f"{hall}.txt"
    if not path.exists():
        raise FileNotFoundError(f"レイアウトが見つかりません: {path}")

    lines = path.read_text(encoding="utf-8").splitlines()
    return HallLayout(hall=hall, lines=lines)

# ホール内の全座席IDを取得
def get_all_seats(hall: str) -> set[str]:
    layout = load_layout(hall)
    return set(layout.seat_ids())

# ホールの空席/予約済み席を表形式で表示
def render_vacancy_table(
    console: Console,
    hall: str,
    reserved: Iterable[str],
) -> None:
    # 最小: 空席/予約席を一覧表示（後でマップ表示にも拡張しやすい）
    all_seats = sorted(get_all_seats(hall))
    reserved_set = set(reserved)
    available = [s for s in all_seats if s not in reserved_set]

    table = Table(title=f"Hall {hall} 座席状況", **TABLE_KWARGS)
    table.add_column("区分", justify="left")
    table.add_column("席数", justify="right")
    table.add_column("席一覧（先頭のみ）", justify="left")

    # 座席一覧のプレビュー表示用関数
    def _preview(items: list[str], n: int = 20) -> str:
        if len(items) <= n:
            return ", ".join(items)
        return ", ".join(items[:n]) + f" ...(+{len(items) - n})"

    table.add_row("空席", str(len(available)), _preview(available))
    table.add_row("予約済", str(len(reserved_set)), _preview(sorted(reserved_set)))

    console.print(table)


def render_seat_map(
    console: Console,
    hall: str,
    reserved: Iterable[str],
) -> None:
    # レイアウトを「席の配置っぽく」表形式で表示する
    # - # : 座席
    # - . : 通路
    # 表示は seat_id を色分け（空席=緑、予約済=赤）

    layout = load_layout(hall)
    reserved_set = {str(s).strip().upper() for s in reserved}

    # 表示対象行（空行は除外）
    rows = [ln for ln in layout.lines if ln.strip() != ""]
    if not rows:
        console.print("[yellow]レイアウトが空です。[/yellow]")
        return

    max_cols = max(len(r) for r in rows)

    # 表形式で表示
    table = Table(title=f"Hall {hall} 座席表", show_header=True, **TABLE_KWARGS)
    table.add_column("列")
    for i in range(1, max_cols + 1):
        table.add_column(str(i), justify="center")

    for row_no, line in enumerate(rows):
        row_letter = chr(ord("A") + row_no)
        col_no = 0
        
        # 予約の有無で色分けして表示
        cells: list[str] = [row_letter]
        for x in range(max_cols):
            ch = line[x] if x < len(line) else " "
            if ch == "#":
                col_no += 1
                seat_id = f"{row_letter}-{col_no}"
                if seat_id.upper() in reserved_set:
                    cells.append(f"[red]{seat_id}[/red]")
                else:
                    cells.append(f"[green]{seat_id}[/green]")
            elif ch == ".":
                cells.append(" ")
            else:
                cells.append(" ")

        table.add_row(*cells)

    console.print("[green]緑=空席[/green]  [red]赤=予約済[/red]")
    console.print(table)
