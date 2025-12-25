from __future__ import annotations

from datetime import datetime

# ユーティリティ関数: 日付時刻の表示用フォーマット変換
def format_ymd_hm(value: str | None) -> str:
    # DB保存のISO文字列(YYYY-MM-DDTHH:MM)を、表示用(YYYY/MM/DD HH:MM)に整形する
    # 失敗したらそのまま返す
    if value is None:
        return "-"

    v = str(value).strip()
    if v == "":
        return "-"

    try:
        # YYYY-MM-DDTHH:MM / YYYY-MM-DD HH:MM を許容
        dt = datetime.strptime(v.replace(" ", "T"), "%Y-%m-%dT%H:%M")
        return dt.strftime("%Y/%m/%d %H:%M")
    except Exception:
        return v
