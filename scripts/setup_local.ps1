$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$venvPath = Join-Path $root '.venv'
$pythonExe = Join-Path $venvPath 'Scripts\python.exe'

if (-not (Test-Path $pythonExe)) {
  py -3 -m venv $venvPath
}

& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install -r (Join-Path $root 'requirements.txt')

Write-Host 'OK: local venv is ready.'
