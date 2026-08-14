$ErrorActionPreference = "Stop"

$Root = Resolve-Path "$PSScriptRoot\..\.."
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$EnvFile = Join-Path $Root ".env"

Write-Host "== pyExplorer setup ==" -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python 3.11 or newer is required."
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "Node.js and npm are required to build the web interface."
}

if (-not (Test-Path $EnvFile)) {
    Copy-Item (Join-Path $Backend ".env.example") $EnvFile
}

Write-Host "Installing backend dependencies..." -ForegroundColor Green
python -m pip install -e $Backend

Write-Host "Installing frontend dependencies..." -ForegroundColor Green
Push-Location $Frontend
npm ci
Write-Host "Building frontend..." -ForegroundColor Green
npm run build
Pop-Location

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Start pyExplorer with: python run.py"
