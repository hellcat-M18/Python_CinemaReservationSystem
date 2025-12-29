import importlib
import os

import qrcode
from rich.console import Console
from rich.text import Text


def _is_colab() -> bool:
    return any(
        os.environ.get(k)
        for k in (
            "COLAB_RELEASE_TAG",
            "COLAB_GPU",
            "COLAB_BACKEND_VERSION",
            "COLAB_JUPYTER_IP",
        )
    )


console = Console(highlight=False)


def print(data: str, border: int = 4) -> None:
    """QRを表示する。

    - 通常: コンソール向けに文字で表示
    - Colab: ブロック文字(█▀▄)や罫線がフォント混在で崩れやすいので、画像表示を優先
    """

    if _is_colab():
        try:
            ipy_display = importlib.import_module("IPython.display")
            display = getattr(ipy_display, "display")

            img = qrcode.make(data)
            display(img)
            return
        except Exception:
            # 画像表示ができない環境ではASCIIにフォールバック
            pass

    qr = qrcode.QRCode(
        border=border,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
    )
    qr.add_data(data)
    qr.make(fit=True)

    m = qr.get_matrix()
    h = len(m)
    w = len(m[0])

    # Colabはブロック文字が崩れやすいのでASCIIのみで表示。
    if _is_colab():
        BLACK = "##"
        WHITE = "  "
        lines: list[str] = []
        for row in m:
            lines.append("".join(BLACK if cell else WHITE for cell in row))
        res = Text("\n".join(lines), overflow="ignore", no_wrap=True)
        console.print(res)
        return

    # 通常環境: 半ブロックで高さを1/2にしてコンパクトに表示
    SPACE = " "
    lines: list[str] = []
    for y in range(0, h, 2):
        row_chars: list[str] = []
        for x in range(w):
            top = m[y][x]
            bottom = m[y + 1][x] if y + 1 < h else False

            if top and bottom:
                ch = "█"
            elif top and not bottom:
                ch = "▀"
            elif (not top) and bottom:
                ch = "▄"
            else:
                ch = SPACE

            row_chars.append(ch)
        lines.append("".join(row_chars))

    res = Text("\n".join(lines), overflow="ignore", no_wrap=True)
    console.print(res)
