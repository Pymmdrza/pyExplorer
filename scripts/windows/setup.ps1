$ErrorActionPreference = "Stop"
$Root = (Resolve-Path "$PSScriptRoot\..\..").Path
$Runtime = Join-Path $Root ".pyexplorer-runtime"
$env:PYEXPLORER_SOURCE_DIR = $Root
$env:PYEXPLORER_HOME = $Runtime
$env:PYEXPLORER_BIN_DIR = Join-Path $Runtime "bin"
& (Join-Path $Root "scripts\install.ps1") -Source $Root -InPlace -NoStart -NoLauncher
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Start pyExplorer with: .\scripts\windows\run.ps1"
