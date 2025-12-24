$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$pythonExe = Join-Path $root '.venv\Scripts\python.exe'

if (-not (Test-Path $pythonExe)) {
  Write-Host 'venv not found. Run scripts\setup_local.ps1 first.'
  exit 1
}

& $pythonExe (Join-Path $root 'router.py')
