$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
Push-Location $projectRoot
try {
    & $pythonExe -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'Dependencias Python inconsistentes.' }
    Push-Location (Join-Path $projectRoot 'frontend')
    try {
        & npm.cmd run build -- --manifest
        if ($LASTEXITCODE -ne 0) { throw 'No se pudo compilar el frontend Local.' }
    } finally { Pop-Location }
} finally { Pop-Location }
