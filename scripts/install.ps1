[CmdletBinding()]
param(
    [switch]$NoStart,
    [switch]$NoLauncher,
    [int]$Port = $(if ($env:PYEXPLORER_PORT) { [int]$env:PYEXPLORER_PORT } else { 8000 }),
    [string]$Source = $env:PYEXPLORER_SOURCE_DIR,
    [switch]$InPlace
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$Repository = "Pymmdrza/pyExplorer"
$Branch = $(if ($env:PYEXPLORER_BRANCH) { $env:PYEXPLORER_BRANCH } else { "main" })
$PythonVersion = $(if ($env:PYEXPLORER_PYTHON_VERSION) { $env:PYEXPLORER_PYTHON_VERSION } else { "3.12" })
$NodeChannel = $(if ($env:PYEXPLORER_NODE_CHANNEL) { $env:PYEXPLORER_NODE_CHANNEL } else { "22" })
$InstallRoot = $(if ($env:PYEXPLORER_HOME) { $env:PYEXPLORER_HOME } else { Join-Path $env:LOCALAPPDATA "pyExplorer" })
$BinDir = $(if ($env:PYEXPLORER_BIN_DIR) { $env:PYEXPLORER_BIN_DIR } else { Join-Path $env:LOCALAPPDATA "pyExplorer\bin" })
$AppDir = Join-Path $InstallRoot "app"
$RuntimeDir = Join-Path $InstallRoot "runtime"
$UvDir = Join-Path $RuntimeDir "uv"
$PythonDir = Join-Path $RuntimeDir "python"
$VenvDir = Join-Path $RuntimeDir "venv"
$NodeDir = Join-Path $RuntimeDir "node"
$CacheDir = Join-Path $RuntimeDir "cache"
$PidFile = Join-Path $RuntimeDir "pyexplorer.pid"
$LogFile = Join-Path $RuntimeDir "pyexplorer.log"
$TempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("pyexplorer-" + [guid]::NewGuid().ToString("N"))

function Write-Step([string]$Message) { Write-Host $Message }
function Fail([string]$Message) { throw "pyExplorer installer: $Message" }
function Invoke-CheckedNative([string]$FilePath, [string[]]$Arguments) {
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) { Fail "$FilePath exited with code $LASTEXITCODE." }
}

function Test-Python([string]$Executable) {
    if (-not (Test-Path $Executable)) { return $false }
    & $Executable -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" *> $null
    return $LASTEXITCODE -eq 0
}

function Test-Node([string]$Executable) {
    if (-not (Test-Path $Executable)) { return $false }
    & $Executable -e 'const [a,b]=process.versions.node.split(".").map(Number); process.exit(((a===20&&b>=19)||(a===22&&b>=12)||a>22)?0:1)' *> $null
    return $LASTEXITCODE -eq 0
}

function Stop-ExistingProcess {
    if (-not (Test-Path $PidFile)) { return }
    $PidValue = (Get-Content $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
    if ($PidValue -match '^\d+$') {
        $Process = Get-Process -Id ([int]$PidValue) -ErrorAction SilentlyContinue
        if ($Process) {
            Write-Step "Stopping the existing pyExplorer process..."
            Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
        }
    }
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

function Install-Source {
    if ($InPlace) {
        if (-not $Source) { Fail "-InPlace requires -Source." }
        $script:AppDir = (Resolve-Path $Source).Path
        if (-not (Test-Path (Join-Path $script:AppDir "run.py"))) { Fail "The source directory is not a pyExplorer checkout." }
        return
    }

    $SourcePath = $null
    if ($Source) {
        $SourcePath = (Resolve-Path $Source).Path
    }
    else {
        Write-Step "Downloading pyExplorer..."
        $ZipPath = Join-Path $TempDir "source.zip"
        $ExtractPath = Join-Path $TempDir "source"
        New-Item -ItemType Directory -Force -Path $ExtractPath | Out-Null
        Invoke-WebRequest -UseBasicParsing -Uri "https://codeload.github.com/$Repository/zip/refs/heads/$Branch" -OutFile $ZipPath
        Expand-Archive -Path $ZipPath -DestinationPath $ExtractPath -Force
        $SourcePath = (Get-ChildItem $ExtractPath -Directory | Select-Object -First 1).FullName
    }

    if (-not (Test-Path (Join-Path $SourcePath "run.py"))) { Fail "The source directory is not a pyExplorer checkout." }
    $SavedEnv = $null
    if (Test-Path (Join-Path $AppDir ".env")) {
        $SavedEnv = Join-Path $TempDir "pyexplorer.env"
        Copy-Item (Join-Path $AppDir ".env") $SavedEnv -Force
    }
    Remove-Item $AppDir -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $AppDir | Out-Null
    Get-ChildItem $SourcePath -Force | Where-Object { $_.Name -notin @('.git', 'node_modules', '.pyexplorer-runtime') } | ForEach-Object {
        Copy-Item $_.FullName -Destination $AppDir -Recurse -Force
    }
    if ($SavedEnv -and (Test-Path $SavedEnv)) { Copy-Item $SavedEnv (Join-Path $AppDir ".env") -Force }
}

function Ensure-Uv {
    $Existing = Get-Command uv -ErrorAction SilentlyContinue
    if ($Existing) { return $Existing.Source }

    New-Item -ItemType Directory -Force -Path $UvDir | Out-Null
    Write-Step "Preparing the Python runtime manager..."
    $UvZip = Join-Path $TempDir "uv.zip"
    $Arch = if ([Environment]::Is64BitOperatingSystem) { "x86_64" } else { Fail "64-bit Windows is required." }
    if ($env:PROCESSOR_ARCHITECTURE -match 'ARM64') { $Arch = "aarch64" }
    $UvUrl = "https://github.com/astral-sh/uv/releases/latest/download/uv-$Arch-pc-windows-msvc.zip"
    Invoke-WebRequest -UseBasicParsing -Uri $UvUrl -OutFile $UvZip
    Expand-Archive -Path $UvZip -DestinationPath $UvDir -Force
    $Uv = Join-Path $UvDir "uv.exe"
    if (-not (Test-Path $Uv)) { Fail "Could not install the Python runtime manager." }
    return $Uv
}

function Ensure-Python([string]$Uv) {
    $env:UV_PYTHON_INSTALL_DIR = $PythonDir
    $env:UV_CACHE_DIR = Join-Path $CacheDir "uv"
    New-Item -ItemType Directory -Force -Path $env:UV_CACHE_DIR | Out-Null

    $PythonSpec = $null
    foreach ($Name in @('python', 'python3')) {
        $Command = Get-Command $Name -ErrorAction SilentlyContinue
        if ($Command -and (Test-Python $Command.Source)) { $PythonSpec = $Command.Source; break }
    }
    if (-not $PythonSpec) {
        Write-Step "Preparing managed Python $PythonVersion..."
        Invoke-CheckedNative $Uv @('python', 'install', $PythonVersion)
        $PythonSpec = $PythonVersion
    }

    $VenvPython = Join-Path $VenvDir "Scripts\python.exe"
    if (-not (Test-Python $VenvPython)) {
        Remove-Item $VenvDir -Recurse -Force -ErrorAction SilentlyContinue
        Invoke-CheckedNative $Uv @('venv', '--python', $PythonSpec, $VenvDir)
    }

    Write-Step "Installing backend dependencies..."
    Invoke-CheckedNative $Uv @('pip', 'install', '--python', $VenvPython, '--upgrade', '-e', (Join-Path $AppDir 'backend'))
    return $VenvPython
}

function Ensure-Node {
    $NodeCommand = Get-Command node -ErrorAction SilentlyContinue
    $NpmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if (-not $NpmCommand) { $NpmCommand = Get-Command npm -ErrorAction SilentlyContinue }
    if ($NodeCommand -and $NpmCommand -and (Test-Node $NodeCommand.Source)) {
        return @{ NodeDir = (Split-Path $NodeCommand.Source); Npm = $NpmCommand.Source }
    }

    $ManagedNode = Join-Path $NodeDir "node.exe"
    if ((Test-Node $ManagedNode) -and (Test-Path (Join-Path $NodeDir "npm.cmd"))) {
        return @{ NodeDir = $NodeDir; Npm = (Join-Path $NodeDir "npm.cmd") }
    }

    Write-Step "Installing a private Node.js runtime..."
    $NodeArch = if ($env:PROCESSOR_ARCHITECTURE -match 'ARM64') { 'arm64' } else { 'x64' }
    $IndexUrl = "https://nodejs.org/dist/latest-v$NodeChannel.x/"
    $Manifest = (Invoke-WebRequest -UseBasicParsing -Uri ($IndexUrl + 'SHASUMS256.txt')).Content
    $Pattern = '(?m)^([a-fA-F0-9]{64})\s+(node-v[0-9.]+-win-' + [regex]::Escape($NodeArch) + '\.zip)$'
    $Match = [regex]::Match($Manifest, $Pattern)
    if (-not $Match.Success) { Fail "Could not resolve a Node.js build for win-$NodeArch." }
    $ExpectedHash = $Match.Groups[1].Value.ToLowerInvariant()
    $NodeFile = $Match.Groups[2].Value
    $NodeZip = Join-Path $TempDir $NodeFile
    Invoke-WebRequest -UseBasicParsing -Uri ($IndexUrl + $NodeFile) -OutFile $NodeZip
    $ActualHash = (Get-FileHash -Algorithm SHA256 $NodeZip).Hash.ToLowerInvariant()
    if ($ActualHash -ne $ExpectedHash) { Fail "Node.js checksum verification failed." }

    $ExtractPath = Join-Path $TempDir "node"
    Expand-Archive -Path $NodeZip -DestinationPath $ExtractPath -Force
    $NodeSource = Get-ChildItem $ExtractPath -Directory | Select-Object -First 1
    if (-not $NodeSource) { Fail "The Node.js archive is invalid." }
    Remove-Item $NodeDir -Recurse -Force -ErrorAction SilentlyContinue
    Move-Item $NodeSource.FullName $NodeDir
    return @{ NodeDir = $NodeDir; Npm = (Join-Path $NodeDir "npm.cmd") }
}

function Build-Frontend($NodeRuntime) {
    $PreviousPath = $env:Path
    $PreviousAudit = $env:NPM_CONFIG_AUDIT
    $PreviousFund = $env:NPM_CONFIG_FUND
    $PreviousNotifier = $env:NPM_CONFIG_UPDATE_NOTIFIER
    try {
        $env:Path = "$($NodeRuntime.NodeDir);$env:Path"
        $env:NPM_CONFIG_AUDIT = "false"
        $env:NPM_CONFIG_FUND = "false"
        $env:NPM_CONFIG_UPDATE_NOTIFIER = "false"
        $Frontend = Join-Path $AppDir "frontend"
        $InstallArgs = @('--prefix', $Frontend, 'install', '--no-audit', '--no-fund', '--package-lock=false', '--progress=false', '--prefer-online', '--fetch-retries=3')
        Write-Step "Installing frontend dependencies..."
        & $NodeRuntime.Npm @InstallArgs
        if ($LASTEXITCODE -ne 0) {
            Write-Step "Retrying frontend dependency installation..."
            & $NodeRuntime.Npm 'cache' 'verify' *> $null
            & $NodeRuntime.Npm @InstallArgs
            if ($LASTEXITCODE -ne 0) { Fail "Frontend dependency installation failed." }
        }
        Write-Step "Building the web interface..."
        Invoke-CheckedNative $NodeRuntime.Npm @('--prefix', $Frontend, 'run', 'build')
    }
    finally {
        $env:Path = $PreviousPath
        $env:NPM_CONFIG_AUDIT = $PreviousAudit
        $env:NPM_CONFIG_FUND = $PreviousFund
        $env:NPM_CONFIG_UPDATE_NOTIFIER = $PreviousNotifier
    }
    if (-not (Test-Path (Join-Path $AppDir "frontend\dist\index.html"))) { Fail "Frontend build did not produce dist/index.html." }
}

function Ensure-Configuration {
    $EnvFile = Join-Path $AppDir ".env"
    $Example = Join-Path $AppDir "backend\.env.example"
    if (-not (Test-Path $EnvFile) -and (Test-Path $Example)) { Copy-Item $Example $EnvFile }
}

function Install-Launcher([string]$Python) {
    if ($NoLauncher) { return }
    New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
    $Launcher = Join-Path $BinDir "pyexplorer.ps1"
    $Cmd = Join-Path $BinDir "pyexplorer.cmd"
    $RawInstaller = "https://raw.githubusercontent.com/$Repository/main/scripts/install.ps1"

    @"
param([Parameter(Position=0)][string]`$Command='start', [Parameter(ValueFromRemainingArguments=`$true)][string[]]`$Rest)
`$ErrorActionPreference='Stop'
`$AppDir='$AppDir'
`$Python='$Python'
`$PidFile='$PidFile'
`$LogFile='$LogFile'
`$Port=if (`$env:PYEXPLORER_PORT) { [int]`$env:PYEXPLORER_PORT } else { $Port }
function Running { if (-not (Test-Path `$PidFile)) { return `$false }; `$p=Get-Content `$PidFile -ErrorAction SilentlyContinue | Select-Object -First 1; return (`$p -match '^\d+$' -and (Get-Process -Id ([int]`$p) -ErrorAction SilentlyContinue)) }
switch (`$Command.ToLowerInvariant()) {
  'start' { if (Running) { Write-Host "pyExplorer is already running at http://127.0.0.1:`$Port"; break }; `$p=Start-Process -FilePath `$Python -ArgumentList @('run.py','--host','127.0.0.1','--port',`$Port)+`$Rest -WorkingDirectory `$AppDir -RedirectStandardOutput `$LogFile -RedirectStandardError (`$LogFile+'.err') -PassThru -WindowStyle Hidden; Set-Content `$PidFile `$p.Id; Write-Host "pyExplorer is running at http://127.0.0.1:`$Port" }
  'serve' { Push-Location `$AppDir; try { & `$Python run.py --host 127.0.0.1 --port `$Port @Rest } finally { Pop-Location } }
  'stop' { if (Running) { `$p=[int](Get-Content `$PidFile | Select-Object -First 1); Stop-Process -Id `$p -Force -ErrorAction SilentlyContinue }; Remove-Item `$PidFile -Force -ErrorAction SilentlyContinue; Write-Host 'pyExplorer stopped.' }
  'restart' { & `$PSCommandPath stop; & `$PSCommandPath start @Rest }
  'status' { if (Running) { Write-Host "pyExplorer is running at http://127.0.0.1:`$Port" } else { Write-Host 'pyExplorer is not running.'; exit 1 } }
  'logs' { if (Test-Path `$LogFile) { Get-Content `$LogFile -Wait -Tail 120 } else { Write-Host 'No log file exists yet.' } }
  'open' { Start-Process "http://127.0.0.1:`$Port" }
  'update' { irm '$RawInstaller' | iex }
  default { Write-Error 'Usage: pyexplorer {start|serve|stop|restart|status|logs|open|update}'; exit 2 }
}
"@ | Set-Content -Encoding UTF8 $Launcher

    "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$Launcher`" %*`r`n" | Set-Content -Encoding ASCII $Cmd

    $UserPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $PathParts = @($UserPath -split ';' | Where-Object { $_ })
    if ($PathParts -notcontains $BinDir) {
        [Environment]::SetEnvironmentVariable('Path', (($PathParts + $BinDir) -join ';'), 'User')
    }
}

New-Item -ItemType Directory -Force -Path $InstallRoot, $RuntimeDir, $CacheDir, $TempDir | Out-Null
try {
    Stop-ExistingProcess
    Install-Source
    Ensure-Configuration
    $Uv = Ensure-Uv
    $Python = Ensure-Python $Uv
    $NodeRuntime = Ensure-Node
    Build-Frontend $NodeRuntime
    Install-Launcher $Python

    Write-Host ""
    Write-Host "pyExplorer installation completed successfully."
    Write-Host "Application: $AppDir"
    if (-not $NoLauncher) { Write-Host "Launcher:    $BinDir\pyexplorer.cmd" }

    if (-not $NoStart) {
        if (-not $NoLauncher) {
            & (Join-Path $BinDir "pyexplorer.ps1") start
        }
        else {
            Push-Location $AppDir
            try { & $Python run.py --host 127.0.0.1 --port $Port }
            finally { Pop-Location }
        }
    }
}
finally {
    Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue
}
