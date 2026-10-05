param()
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
$pgCtl = Join-Path $projectRoot '.local\pg17\pgsql\bin\pg_ctl.exe'
$pgData = Join-Path $projectRoot '.local\pgdata'
$processFile = Join-Path $projectRoot '.local\dev-processes.json'
foreach ($port in @(8000, 5173)) {
    $listener = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue
    if ($listener) { throw "El puerto $port ya esta en uso. Revisa el proceso antes de iniciar MyGym." }
}
& $pgCtl -D $pgData status *> $null
if ($LASTEXITCODE -ne 0) {
    & $pgCtl -D $pgData -l (Join-Path $projectRoot '.local\postgres.log') -w start
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo iniciar PostgreSQL.' }
}
& $pythonExe (Join-Path $projectRoot 'backend\manage.py') check
if ($LASTEXITCODE -ne 0) { throw 'Django check fallo.' }
& $pythonExe (Join-Path $projectRoot 'scripts\check_runtime.py')
if ($LASTEXITCODE -ne 0) { throw 'Los privilegios runtime no cumplen RLS.' }
$backend = Start-Process -FilePath $pythonExe -ArgumentList @(('"' + (Join-Path $projectRoot 'backend\manage.py') + '"'), 'runserver', '127.0.0.1:8000', '--noreload') -WorkingDirectory (Join-Path $projectRoot 'backend') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $projectRoot '.local\backend.stdout.log') -RedirectStandardError (Join-Path $projectRoot '.local\backend.stderr.log')
try {
    $nodeExe = (Get-Command node.exe).Source
    $vitePath = Join-Path $projectRoot 'frontend\node_modules\vite\bin\vite.js'
    $frontend = Start-Process -FilePath $nodeExe -ArgumentList @(('"' + $vitePath + '"'), '--host', '127.0.0.1', '--port', '5173', '--strictPort') -WorkingDirectory (Join-Path $projectRoot 'frontend') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $projectRoot '.local\frontend.stdout.log') -RedirectStandardError (Join-Path $projectRoot '.local\frontend.stderr.log')
    @{ backend = $backend.Id; frontend = $frontend.Id } | ConvertTo-Json | Set-Content -Encoding UTF8 -LiteralPath $processFile
    $ready = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        try {
            $api = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8000/api/v1/health/' -TimeoutSec 1
            $ui = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:5173' -TimeoutSec 1
            if ($api.StatusCode -eq 200 -and $ui.StatusCode -eq 200) { $ready = $true; break }
        } catch { Start-Sleep -Milliseconds 250 }
    }
    if (-not $ready) { throw 'Arranque incompleto. Revisa los logs de .local.' }
    Write-Output 'MyGym desarrollo: http://127.0.0.1:5173'
    Write-Output 'Cuenta demo.owner; contrasena privada en .local\mygym_dev-demo.json.'
} catch {
    & (Join-Path $PSScriptRoot 'stop-dev.ps1')
    throw
}
