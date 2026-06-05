$ErrorActionPreference = "Stop"

$Root = Resolve-Path "$PSScriptRoot\..\.."

Write-Host "== Starting pyExplorer Docker demo ==" -ForegroundColor Cyan

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker is not installed or not available in PATH."
}

Push-Location $Root
docker compose up --build
Pop-Location