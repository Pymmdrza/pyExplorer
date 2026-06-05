$ErrorActionPreference = "Stop"

$Root = Resolve-Path "$PSScriptRoot\..\.."
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"

Write-Host "== Starting pyExplorer dev stack ==" -ForegroundColor Cyan

if (-not (Test-Path (Join-Path $Frontend "node_modules"))) {
    Write-Host "frontend/node_modules not found. Run scripts\windows\setup.ps1 first." -ForegroundColor Yellow
}

$BackendCommand = "cd /d `"$Backend`" && set PYTHONPATH=src && python -m uvicorn pyexplorer_api.asgi:app --reload --host 0.0.0.0 --port 8000"
$FrontendCommand = "cd /d `"$Frontend`" && npm run dev -- --host 0.0.0.0 --port 5173"

Start-Process cmd.exe -ArgumentList "/k", $BackendCommand -WindowStyle Normal
Start-Sleep -Seconds 2
Start-Process cmd.exe -ArgumentList "/k", $FrontendCommand -WindowStyle Normal

Start-Sleep -Seconds 5
try {
    $Health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health" -TimeoutSec 5
    Write-Host "Backend health: $($Health.status)" -ForegroundColor Green
} catch {
    Write-Host "Backend health check is not ready yet. Check the backend terminal window." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Backend:  http://localhost:8000/api/v1/health" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host ""
Write-Host "Two terminal windows were opened. Close them, or run scripts\windows\stop.ps1, to stop the servers."