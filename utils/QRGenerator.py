import qrcode
from rich.console import Console

console = Console(highlight=False)

def generate_qr_ascii(data: str, border: int = 4) -> str:
    """
    半ブロック(█▀▄)でQRを生成し、崩れにくい文字列を返す。
    - border: Quiet Zone。読み取りなら 4 推奨。
    """
    WHITE = "\u00A0"  # NBSP: 見た目は空白だが幅が潰れにくい

    qr = qrcode.QRCode(
        border=border,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
    )
    qr.add_data(data)
    qr.make(fit=True)

    m = qr.get_matrix()
    h = len(m)
    w = len(m[0])

    lines = []
    for y in range(0, h, 2):
        row = []
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
                ch = WHITE

            row.append(ch)
        lines.append("".join(row))

    return "\n".join(lines)


def print(data: str, border: int = 4) -> None:
    qr_text = generate_qr_ascii(data=data, border=border)
    # QRは「折り返し」されると崩れるので、markup無効＋wrap無効で出す
    console.print(qr_text, markup=False, highlight=False, overflow="ignore", soft_wrap=False)
