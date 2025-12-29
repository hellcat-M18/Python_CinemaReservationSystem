from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ADMIN_USERNAME_KEY = "CINEMA_ADMIN_USERNAME"
ADMIN_PASSWORD_KEY = "CINEMA_ADMIN_PASSWORD"

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


def _env_has_admin_keys(env_path: Path) -> bool:
    if not env_path.exists():
        return False
    try:
        text = env_path.read_text(encoding="utf-8")
    except Exception:
        return False
    return (f"{ADMIN_USERNAME_KEY}=" in text) and (f"{ADMIN_PASSWORD_KEY}=" in text)


def _db_path(root_dir: Path) -> Path:
    return root_dir / "cinema.db"


def _is_colab() -> bool:
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

# メイン処理
def main() -> int:
    # ディレクトリ設定
    root_dir = _project_root()
    req = root_dir / "requirements.txt"
    if not req.exists():
        print("ERROR: requirements.txt not found")
        return 1

    # Colab は venv を作らず、その場の環境に install する
    if _is_colab():
        runner_py = sys.executable # 現在実行中のPythonのパスを取得
        print("Colab detected: installing requirements into current environment (no venv)")
        print("Upgrading pip")
        # colabのpythonを使ってアップグレード・インストール
        _run([runner_py, "-m", "pip", "install", "--upgrade", "pip"], cwd=root_dir)
        print("Installing requirements")
        _run([runner_py, "-m", "pip", "install", "-r", str(req)], cwd=root_dir)
    else:
        venv_dir = root_dir / ".venv"
        venv_py = _venv_python(venv_dir)
        runner_py = str(venv_py)

        # venvがなければ作成
        if not venv_py.exists():
            print("Creating venv: .venv")
            _run([sys.executable, "-m", "venv", str(venv_dir)], cwd=root_dir)

        # pipをアップグレードしてからrequirements.txtをインストール
        print("Upgrading pip")
        _run([runner_py, "-m", "pip", "install", "--upgrade", "pip"], cwd=root_dir)
        print("Installing requirements")
        _run([runner_py, "-m", "pip", "install", "-r", str(req)], cwd=root_dir)

    # pip installの後にDBテーブルを作成
    print("Creating DB tables")
    _run(
        # init_db関数をdb/db.pyから読み込み、実行
        [runner_py, "-c", "from db.db import init_db; init_db(); print('OK: created tables')"],
        cwd=root_dir,
    )


    # 依存導入後、必要なら管理者アカウント(.env)もセットアップ
    env_path = root_dir / ".env"
    if not _env_has_admin_keys(env_path):
        if sys.stdin.isatty():
            ans = input("Admin (.env) を設定しますか? [y/N]: ").strip().lower()
            if ans in {"y", "yes"}:
                _run([runner_py, str(root_dir / "scripts" / "set_admin_env.py")], cwd=root_dir)
        else:
            print("NOTE: .env admin keys are not set. Skipping set_admin_env (non-interactive).")

    # 管理者設定の後、必要ならサンプルデータ投入
    if sys.stdin.isatty():
        ans = input("サンプルデータを投入しますか? [y/N]: ").strip().lower()
        if ans in {"y", "yes"}:

            _run([runner_py, str(root_dir / "scripts" / "seed_sample_data.py")], cwd=root_dir)
            
    else:
        print("NOTE: skipping sample data seed (non-interactive).")

    # 完了メッセージ
    print("OK: setup completed.")
    print(f"Python: {runner_py}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
