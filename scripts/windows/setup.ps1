$ErrorActionPreference = "Stop"

$Root = Resolve-Path "$PSScriptRoot\..\.."
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$EnvFile = Join-Path $Root ".env"

Write-Host "== pyExplorer Windows setup ==" -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python is not installed or not available in PATH."
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "Node.js/npm is not installed or not available in PATH."
}

if (-not (Test-Path $EnvFile)) {
    Write-Host "Creating root .env with local defaults..." -ForegroundColor Yellow
    @"
PYEXPLORER_ENVIRONMENT=local
PYEXPLORER_LOG_LEVEL=INFO
PYEXPLORER_API_PREFIX=/api/v1
PYEXPLORER_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
PYEXPLORER_REALTIME_ENABLED=true
PYEXPLORER_BLOCKCHAIN_WS_URL=wss://ws.blockchain.info/inv
"@ | Set-Content -Encoding UTF8 $EnvFile
}

Write-Host "Installing backend dependencies..." -ForegroundColor Green
Push-Location $Backend
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
Pop-Location

Write-Host "Installing frontend dependencies..." -ForegroundColor Green
Push-Location $Frontend
npm install
Pop-Location

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Run: powershell -ExecutionPolicy Bypass -File .\scripts\windows\dev.ps1"