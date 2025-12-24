@echo off
setlocal

set ROOT=%~dp0..
set VENV=%ROOT%\.venv
set PY=%VENV%\Scripts\python.exe

if not exist "%PY%" (
  py -3 -m venv "%VENV%"
)

"%PY%" -m pip install --upgrade pip
"%PY%" -m pip install -r "%ROOT%\requirements.txt"

echo OK: local venv is ready.
endlocal
