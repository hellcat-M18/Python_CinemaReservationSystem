@echo off
setlocal

REM ------------------------------------------------------------
REM 管理者アカウント用の設定を「プロジェクト直下の .env」に書き込む
REM - 実体は scripts/set_admin_env.py
REM - .env は gitignore 済み（秘密情報をコミットしない）
REM
REM 使い方:
REM   scripts\set_admin_env.bat
REM   scripts\set_admin_env.bat admin mypass
REM ------------------------------------------------------------

set ROOT=%~dp0..
set PY=%ROOT%\.venv\Scripts\python.exe

if not exist "%PY%" (
echo venv not found. Run scripts\setup_local.bat first.
exit /b 1
)

"%PY%" "%ROOT%\scripts\set_admin_env.py" %1 %2

endlocal
