from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# プロジェクトルートのパス
def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent

# 仮想環境内のPython実行ファイルのパス
# Windows系なら Scripts/python.exe, Unix系なら bin/python
def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"

# コマンド実行ユーティリティ
# 引数にコマンド(スペースで区切ったリスト形式)とカレントディレクトリを入れるとそれに沿って実行してくれる
def _run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=str(cwd), check=True)

# メイン処理
def main() -> int:
    # ディレクトリ設定
    root_dir = _project_root()
    venv_dir = root_dir / ".venv"
    venv_py = _venv_python(venv_dir)

    # venvがなければ作成
    if not venv_py.exists():
        print("Creating venv: .venv")
        _run([sys.executable, "-m", "venv", str(venv_dir)], cwd=root_dir)

    # pipをアップグレードしてからrequirements.txtをインストール
    print("Upgrading pip")
    _run([str(venv_py), "-m", "pip", "install", "--upgrade", "pip"], cwd=root_dir)

    req = root_dir / "requirements.txt"
    if not req.exists():
        print("ERROR: requirements.txt not found")
        return 1

    print("Installing requirements")
    _run([str(venv_py), "-m", "pip", "install", "-r", str(req)], cwd=root_dir)

    # 完了メッセージ
    print("OK: local venv is ready.")
    print(f"Python: {venv_py}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
