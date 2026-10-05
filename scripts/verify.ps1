param([switch]$Browser)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Verificacion fallida: $Executable $($Arguments -join ' ')" }
}
Push-Location $projectRoot
try {
    Invoke-Checked $pythonExe @('-m', 'pip', 'check')
    Invoke-Checked $pythonExe @('scripts/verify_role_guard.py')
    Invoke-Checked $pythonExe @('-m', 'ruff', 'check', 'backend', 'scripts')
    Invoke-Checked $pythonExe @('backend/manage.py', 'check')
    Invoke-Checked $pythonExe @('backend/manage.py', 'makemigrations', '--check', '--dry-run')
    Invoke-Checked $pythonExe @('backend/manage.py', 'spectacular', '--file', 'docs/api/openapi.yaml', '--validate', '--fail-on-warn')
    Push-Location backend
    try { Invoke-Checked $pythonExe @('-m', 'pytest') } finally { Pop-Location }
    Push-Location frontend
    try {
        Invoke-Checked 'npm.cmd' @('run', 'lint')
        Invoke-Checked 'npm.cmd' @('test')
        Invoke-Checked 'npm.cmd' @('run', 'build')
    } finally { Pop-Location }
    if ($Browser) { Invoke-Checked $pythonExe @('scripts/run_e2e.py') }
} finally { Pop-Location }
