from __future__ import annotations

from dataclasses import dataclass # dataclass: クラスの定義を簡潔に書くためのモジュール。__init__などを自動で生成してくれる。
from pathlib import Path          # ファイルパス操作用モジュール
from typing import Iterable       # 型ヒント用モジュール

from rich.console import Console  # richライブラリのConsoleクラスをインポート
from rich.table import Table      # richライブラリのTableクラスをインポート

# 映画館のホールレイアウトを扱うユーティリティ
@dataclass(frozen=True)
class HallLayout:
    hall: str
    lines: list[str]

    def seat_ids(self) -> list[str]:
        # レイアウトの'#'だけを座席として扱う
        # 座席IDは "A-1" 形式（行=英字、列=その行の座席番号）
        seat_ids: list[str] = []
        row_letter_ord = ord("A")

        # 行ごとに処理 | enumerate: リストをインデックス付きでループするための組み込み関数
        for row_index, raw in enumerate(self.lines):
            line = raw.rstrip("\n")
            if line.strip() == "":
                continue

            row_letter = chr(row_letter_ord + row_index)
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

    table = Table(title=f"Hall {hall} 座席状況")
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
