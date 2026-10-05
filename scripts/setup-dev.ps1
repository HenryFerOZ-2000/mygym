param()
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
        & py -3.13 -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Se necesita Python 3.13.' }
    }
    $pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
    & $pythonExe -m pip install -r backend\requirements.lock
    if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar dependencias Python.' }
    & $pythonExe scripts\download_postgres.py
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo preparar PostgreSQL.' }
    & $pythonExe scripts\provision_local.py
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo provisionar la base.' }
    foreach ($databaseName in @('mygym_dev', 'mygym_test', 'mygym_e2e')) {
        & $pythonExe scripts\migrate_local.py $databaseName
        if ($LASTEXITCODE -ne 0) { throw "Fallo migracion: $databaseName" }
    }
    foreach ($databaseName in @('mygym_dev', 'mygym_e2e')) {
        & $pythonExe scripts\seed_local.py $databaseName
        if ($LASTEXITCODE -ne 0) { throw "Fallo demo: $databaseName" }
    }
    Push-Location frontend
    try {
        & npm.cmd ci --no-fund
        if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar dependencias frontend.' }
        & npx.cmd playwright install chromium
        if ($LASTEXITCODE -ne 0) { throw 'No se pudo instalar Chromium para pruebas.' }
    } finally { Pop-Location }
} finally { Pop-Location }
Write-Output 'Entorno preparado. Ejecuta .\scripts\start-dev.ps1.'
