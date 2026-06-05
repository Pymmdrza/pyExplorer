$ErrorActionPreference = "Stop"

$Root = Resolve-Path "$PSScriptRoot\..\.."
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"

Write-Host "== Running backend checks ==" -ForegroundColor Cyan
Push-Location $Backend
python -m ruff check .
python -m pytest
python -m compileall src tests
Pop-Location

Write-Host "== Running frontend checks ==" -ForegroundColor Cyan
Push-Location $Frontend
npm run lint
npm run build
Pop-Location

Write-Host ""
Write-Host "All checks passed." -ForegroundColor Green