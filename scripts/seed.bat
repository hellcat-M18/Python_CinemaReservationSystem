@echo off
setlocal

@REM プロジェクトルートと仮想環境のPythonパス
set ROOT=%~dp0..
set VENV_PY=%ROOT%\.venv\Scripts\python.exe

@REM 仮想環境がなければエラー
if not exist "%VENV_PY%" (
    echo ERROR: venv not found. Run scripts\run.bat or python scripts\setup.py first.
    exit /b 1
)

@REM seed_sample_data.pyを起動
"%VENV_PY%" "%ROOT%\scripts\seed_sample_data.py"
endlocal
