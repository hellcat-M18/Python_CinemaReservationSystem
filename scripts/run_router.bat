@echo off
setlocal

set ROOT=%~dp0..
set PY=%ROOT%\.venv\Scripts\python.exe

if not exist "%PY%" (
echo venv not found. Run scripts\setup_local.bat first.
exit /b 1
)

"%PY%" "%ROOT%\router.py"
endlocal
