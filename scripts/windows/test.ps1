$ErrorActionPreference = "Stop"

$Root = (Resolve-Path "$PSScriptRoot\..\..").Path
$Runtime = Join-Path $Root ".pyexplorer-runtime"
$Python = Join-Path $Runtime "runtime\venv\Scripts\python.exe"
$LocalUv = Join-Path $Runtime "runtime\uv\uv.exe"
$ManagedNpm = Join-Path $Runtime "runtime\node\npm.cmd"
$Frontend = Join-Path $Root "frontend"

if (-not (Test-Path $Python) -or -not (Test-Path (Join-Path $Frontend "node_modules"))) {
    & (Join-Path $Root "scripts\windows\setup.ps1")
}

if (Test-Path $LocalUv) {
    $Uv = $LocalUv
}
else {
    $UvCommand = Get-Command uv -ErrorAction SilentlyContinue
    if (-not $UvCommand) { throw "uv is unavailable. Run scripts\windows\setup.ps1." }
    $Uv = $UvCommand.Source
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

& $Uv pip install --python $Python --upgrade -e "$Root\backend[dev]"
if ($LASTEXITCODE -ne 0) { throw "Development dependency installation failed." }
& $Python -m ruff check "$Root\backend\src" "$Root\backend\tests"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $Python -m pytest "$Root\backend"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $Python -m compileall "$Root\backend\src" "$Root\backend\tests"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Push-Location $Frontend
try {
    & $Npm install --prefer-offline --fetch-retries=3
    if ($LASTEXITCODE -ne 0) { throw "Frontend dependency installation failed." }
    & $Npm run lint
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $Npm run build
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally { Pop-Location }

Write-Host "All checks passed."
