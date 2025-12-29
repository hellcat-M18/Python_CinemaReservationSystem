@echo off
setlocal

@REM プロジェクトルートと仮想環境のPythonパス

set ROOT=%~dp0..
set VENV_PY=%ROOT%\.venv\Scripts\python.exe

@REM 仮想環境がなければセットアップを実行

if not exist "%VENV_PY%" (
    echo venv not found. Running setup...

    python "%ROOT%\scripts\setup.py"
  
)

@REM 仮想環境のPythonがまだなければエラー

if not exist "%VENV_PY%" (
    echo ERROR: venv python still not found: %VENV_PY%
    exit /b 1
)