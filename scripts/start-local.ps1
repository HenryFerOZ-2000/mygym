param([ValidateRange(1024,65535)][int]$Port = 8765, [switch]$Check)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not $Check) {
    $listener = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    if ($listener) { throw "El puerto $Port ya esta en uso. No se detuvo ningun proceso." }
}
$launchArgs = @((Join-Path $PSScriptRoot 'serve_local.py'), '--port', "$Port")
if ($Check) { $launchArgs += '--check' }
& $pythonExe @launchArgs
if ($LASTEXITCODE -ne 0) { throw 'No se pudo iniciar o verificar MyGym Local.' }
