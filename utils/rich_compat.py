from __future__ import annotations

import os

from rich import box


def is_colab() -> bool:
    # Google Colab sets one or more of these env vars.
    return any(
        os.environ.get(k)
        for k in (
            "COLAB_RELEASE_TAG",
            "COLAB_GPU",
            "COLAB_BACKEND_VERSION",
            "COLAB_JUPYTER_IP",
        )
    )


# Colabは罫線文字(│─など)やブロック文字(█▀▄)が別フォント扱いになり、
# 列幅がズレて表示が崩れることがあるため、ASCII枠に寄せる。
TABLE_KWARGS = {"box": box.ASCII} if is_colab() else {}
