# Python_CinemaReservationSystem
大学の課題で作った映画館のチケット購入システムです

## セットアップ
Windowsの場合
1. scripts/setup_local.batを実行
2. scripts/run_router.batで起動(venv)

Linuxの場合
1. scripts/setup_local.shを実行
2. scripts/run_router.shで起動(venv)

Google Colabの場合
1. ! pip install -r requirements.txt を実行
2. ! python Python_CinemaReservationSystem/router.py を実行して起動

## 依存関係
- SQLAlchemy==2.0.45
- rich==14.2.0
- qrcode==8.2
- passlib==1.7.4
- python-dotenv==1.0.1

## 環境変数（管理者アカウント）
管理者ユーザーをDB初期化時に自動作成したい場合は、以下を設定します。

### 方法A: .env（おすすめ・永続化）
1. プロジェクト直下に `.env` を作成（例は `.env.example`）
2. 例:

```
CINEMA_ADMIN_USERNAME=admin
CINEMA_ADMIN_PASSWORD=change_me
```

`.env` は起動時に [db/db.py](db/db.py) が自動で読み込みます。

### 方法B: スクリプトで一時設定（ターミナル限定）
### 方法B: スクリプトで .env を更新
- Windows: `scripts/set_admin_env.bat`
- Linux/macOS/Git Bash: `bash scripts/set_admin_env.sh`

※ どちらも内部では `scripts/set_admin_env.py` を呼び出して `.env` を更新します。

### DBリセットなしで管理者を追加/変更したい場合
既存DBを保持したまま、管理者ユーザーを「追加/パスワード更新」したいときは以下を実行します。

- `python scripts/create_or_update_admin.py`

このスクリプトは `.env`（または環境変数）にある `CINEMA_ADMIN_USERNAME` / `CINEMA_ADMIN_PASSWORD` を読み込んでDBへ反映します。
DB（cinema.db）が未生成の場合は中断します。

## 使い方
wip