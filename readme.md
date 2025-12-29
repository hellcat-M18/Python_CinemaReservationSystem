# Python_CinemaReservationSystem
大学の課題で作った映画館のチケット購入システムです

## セットアップ
Windowsの場合
1. `scripts/run.bat`
2. 必要なら`python scripts/seed_sample_data.py`でサンプルデータ投入

Linuxの場合
1. `bash scripts/run.sh`
2. 必要なら`python scripts/seed_sample_data.py`でサンプルデータ投入

Google Colabの場合
1. `!pip install -r requirements.txt`
2. `!python router.py`
3. 必要なら`!python scripts/seed_sample_data.py`でサンプルデータ投入

## 依存関係
- SQLAlchemy==2.0.45
- rich==14.2.0
- qrcode==8.2
- passlib==1.7.4
- python-dotenv==1.0.1

## 環境変数（管理者アカウント）
管理者ユーザーをDB初期化時に自動作成したい場合は、以下を設定します。

### 方法A: .env（DB初期化時）
1. プロジェクト直下に `.env` を作成（例は `.env.example`）
2. 例:

```
CINEMA_ADMIN_USERNAME=admin
CINEMA_ADMIN_PASSWORD=change_me
```

`.env` はDB初期化時に [db/db.py](db/db.py) が自動で読み込みます。

### 方法B: DBリセットなしで管理者を追加/変更
既存DBを保持したまま、管理者ユーザーを「追加/パスワード更新」したいときは以下を実行します。

- `python scripts/create_or_update_admin.py`

このスクリプトは `.env`（または環境変数）にある `CINEMA_ADMIN_USERNAME` / `CINEMA_ADMIN_PASSWORD` を読み込んでDBへ反映します。
DB（cinema.db）が未生成の場合は中断します。

## 使い方
`scripts/run.(bat|sh)` で起動するとログイン画面から開始します。

## サンプルデータ投入
映画5本と、2か月分の平日（月〜金）上映スケジュール（週ごとに繰り返し）を登録します。

- `python scripts/seed_sample_data.py`

※ cinema.db が未生成の場合は中断します（先に `python db/init_db.py`）。