$ErrorActionPreference = "Stop"

$Root = (Resolve-Path "$PSScriptRoot\..\..").Path
$Runtime = Join-Path $Root ".pyexplorer-runtime"
$Python = Join-Path $Runtime "runtime\venv\Scripts\python.exe"
$ManagedNpm = Join-Path $Runtime "runtime\node\npm.cmd"
$Frontend = Join-Path $Root "frontend"
$Backend = Join-Path $Root "backend"

if (-not (Test-Path $Python) -or -not (Test-Path (Join-Path $Frontend "node_modules"))) {
    & (Join-Path $Root "scripts\windows\setup.ps1")
}

if (Test-Path $ManagedNpm) {
    $Npm = $ManagedNpm
    $env:Path = "$(Split-Path $ManagedNpm);$env:Path"
}
else {
    $NpmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if (-not $NpmCommand) { $NpmCommand = Get-Command npm -ErrorAction SilentlyContinue }
    if (-not $NpmCommand) { throw "npm runtime is unavailable. Run scripts\windows\setup.ps1." }
    $Npm = $NpmCommand.Source
}

Push-Location $Frontend
try {
    & $Npm install --prefer-offline --fetch-retries=3
    if ($LASTEXITCODE -ne 0) { throw "Frontend dependency installation failed." }
}
finally { Pop-Location }

$BackendProcess = Start-Process -FilePath $Python -ArgumentList @('-m', 'uvicorn', 'pyexplorer_api.asgi:app', '--reload', '--host', '0.0.0.0', '--port', '8000') -WorkingDirectory $Backend -PassThru
$FrontendProcess = Start-Process -FilePath $Npm -ArgumentList @('run', 'dev', '--', '--host', '0.0.0.0', '--port', '5173') -WorkingDirectory $Frontend -PassThru

Write-Host "Backend:  http://localhost:8000/api/v1/health"
Write-Host "Frontend: http://localhost:5173"
Write-Host "Backend PID: $($BackendProcess.Id)"
Write-Host "Frontend PID: $($FrontendProcess.Id)"
Write-Host "Use scripts\windows\stop.ps1 to stop the development servers."
