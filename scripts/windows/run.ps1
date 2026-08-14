$ErrorActionPreference = "Stop"
$Root = (Resolve-Path "$PSScriptRoot\..\..").Path
$Python = Join-Path $Root ".pyexplorer-runtime\runtime\venv\Scripts\python.exe"
$Frontend = Join-Path $Root "frontend\dist\index.html"
if (-not (Test-Path $Python) -or -not (Test-Path $Frontend)) {
    & (Join-Path $Root "scripts\windows\setup.ps1")
}
Push-Location $Root
try { & $Python run.py @args }
finally { Pop-Location }
