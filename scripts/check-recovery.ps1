param([switch]$Fixture)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
$arguments = @((Join-Path $PSScriptRoot 'recovery_rehearsal.py'))
if ($Fixture) { $arguments += '--fixture-check' }
& $pythonExe @arguments
if ($LASTEXITCODE -ne 0) { throw 'Recovery check blocked; no database restored or security permissions changed.' }
