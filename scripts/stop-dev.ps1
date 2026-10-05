param([switch]$Database)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$processFile = Join-Path $projectRoot '.local\dev-processes.json'
if (Test-Path -LiteralPath $processFile) {
    $record = Get-Content -Raw -LiteralPath $processFile | ConvertFrom-Json
    foreach ($processId in @($record.frontend, $record.backend)) {
        $process = Get-CimInstance Win32_Process -Filter "ProcessId=$processId" -ErrorAction SilentlyContinue
        if ($process) {
            if (-not $process.CommandLine -or -not $process.CommandLine.Contains($projectRoot)) { throw "PID $processId no pertenece al proyecto; no se detuvo." }
            Stop-Process -Id $processId -ErrorAction Stop
        }
    }
    Remove-Item -LiteralPath $processFile
}
if ($Database) {
    & (Join-Path $projectRoot '.local\pg17\pgsql\bin\pg_ctl.exe') -D (Join-Path $projectRoot '.local\pgdata') -m fast -w stop
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo detener PostgreSQL.' }
}
Write-Output 'Procesos de desarrollo detenidos.'
