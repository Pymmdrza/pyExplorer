[CmdletBinding()]
param(
    [switch]$NoStart,
    [switch]$NoLauncher,
    [switch]$InPlace,
    [int]$Port = $(if ($env:PYEXPLORER_PORT) { [int]$env:PYEXPLORER_PORT } else { 8000 }),
    [string]$Source = $env:PYEXPLORER_SOURCE_DIR
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$Repository = "Pymmdrza/pyExplorer"
$Branch = if ($env:PYEXPLORER_BRANCH) { $env:PYEXPLORER_BRANCH } else { "main" }
$PythonVersion = if ($env:PYEXPLORER_PYTHON_VERSION) { $env:PYEXPLORER_PYTHON_VERSION } else { "3.12" }
$NodeChannel = if ($env:PYEXPLORER_NODE_CHANNEL) { $env:PYEXPLORER_NODE_CHANNEL } else { "22" }
$InstallRoot = if ($env:PYEXPLORER_HOME) { $env:PYEXPLORER_HOME } else { Join-Path $env:LOCALAPPDATA "pyExplorer" }
$BinDir = if ($env:PYEXPLORER_BIN_DIR) { $env:PYEXPLORER_BIN_DIR } else { Join-Path $InstallRoot "bin" }
$AppDir = Join-Path $InstallRoot "app"
if ($InPlace) {
    if (-not $Source) { throw "-InPlace requires -Source PATH." }
    $AppDir = (Resolve-Path $Source).Path
}
$RuntimeDir = Join-Path $InstallRoot "runtime"
$UvDir = Join-Path $RuntimeDir "uv"
$PythonDir = Join-Path $RuntimeDir "python"
$VenvDir = Join-Path $RuntimeDir "venv"
$NodeDir = Join-Path $RuntimeDir "node"
$CacheDir = Join-Path $RuntimeDir "cache"
$PidFile = Join-Path $RuntimeDir "pyexplorer.pid"
$LogFile = Join-Path $RuntimeDir "pyexplorer.log"
$ErrorLogFile = Join-Path $RuntimeDir "pyexplorer.error.log"

function Write-Step([string]$Message) {
    Write-Host $Message -ForegroundColor Cyan
}

function Invoke-CheckedNative {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )
    & $FilePath @Arguments | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
    }
}

function Stop-ExistingProcess {
    if (-not (Test-Path $PidFile)) { return }
    $PidValue = (Get-Content $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
    if ($PidValue -and ($PidValue -as [int])) {
        $Process = Get-Process -Id ([int]$PidValue) -ErrorAction SilentlyContinue
        if ($Process) {
            Write-Step "Stopping the existing pyExplorer process..."
            Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
            $Process.WaitForExit(5000) | Out-Null
        }
    }
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

function Copy-SourceTree([string]$SourcePath, [string]$TempDir) {
    $ResolvedSource = (Resolve-Path $SourcePath).Path
    if (-not (Test-Path (Join-Path $ResolvedSource "run.py"))) { throw "The source directory does not contain run.py." }
    if (-not (Test-Path (Join-Path $ResolvedSource "backend"))) { throw "The source directory does not contain backend/." }
    if (-not (Test-Path (Join-Path $ResolvedSource "frontend"))) { throw "The source directory does not contain frontend/." }

    $ExistingApp = if (Test-Path $AppDir) { (Resolve-Path $AppDir).Path } else { $null }
    if ($ExistingApp -and $ResolvedSource -eq $ExistingApp) { return }

    $SavedEnv = $null
    if (Test-Path (Join-Path $AppDir ".env")) {
        $SavedEnv = Join-Path $TempDir "pyexplorer.env"
        Copy-Item (Join-Path $AppDir ".env") $SavedEnv -Force
    }

    Remove-Item $AppDir -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Path $AppDir -Force | Out-Null
    Get-ChildItem -LiteralPath $ResolvedSource -Force | Where-Object {
        $_.Name -notin @(".git", "node_modules", ".venv")
    } | ForEach-Object {
        Copy-Item $_.FullName -Destination $AppDir -Recurse -Force
    }

    if ($SavedEnv -and (Test-Path $SavedEnv)) {
        Copy-Item $SavedEnv (Join-Path $AppDir ".env") -Force
    }
}

function Get-RepositorySource([string]$TempDir) {
    $Archive = Join-Path $TempDir "source.zip"
    $ExtractDir = Join-Path $TempDir "source"
    New-Item -ItemType Directory -Path $ExtractDir -Force | Out-Null
    Write-Step "Downloading pyExplorer..."
    Invoke-WebRequest -UseBasicParsing -Uri "https://codeload.github.com/$Repository/zip/refs/heads/$Branch" -OutFile $Archive
    Expand-Archive -Path $Archive -DestinationPath $ExtractDir -Force
    $SourceDir = Get-ChildItem $ExtractDir -Directory | Select-Object -First 1
    if (-not $SourceDir) { throw "Downloaded archive did not contain the application source." }
    return $SourceDir.FullName
}

function Get-Uv {
    $Existing = Get-Command uv -ErrorAction SilentlyContinue
    if ($Existing) { return $Existing.Source }

    New-Item -ItemType Directory -Path $UvDir -Force | Out-Null
    Write-Step "Installing the private Python runtime manager..."
    $PreviousInstallDir = $env:UV_INSTALL_DIR
    $PreviousNoModify = $env:UV_NO_MODIFY_PATH
    try {
        $env:UV_INSTALL_DIR = $UvDir
        $env:UV_NO_MODIFY_PATH = "1"
        $UvInstaller = Invoke-RestMethod https://astral.sh/uv/install.ps1
        Invoke-Expression $UvInstaller | Out-Host
    }
    finally {
        $env:UV_INSTALL_DIR = $PreviousInstallDir
        $env:UV_NO_MODIFY_PATH = $PreviousNoModify
    }

    $Uv = Join-Path $UvDir "uv.exe"
    if (-not (Test-Path $Uv)) { throw "uv installation did not produce an executable." }
    return $Uv
}

function Test-PythonSupported([string]$PythonCommand) {
    try {
        & $PythonCommand -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" 2>$null
        return $LASTEXITCODE -eq 0
    }
    catch { return $false }
}

function Install-Python([string]$Uv) {
    $env:UV_PYTHON_INSTALL_DIR = $PythonDir
    $env:UV_CACHE_DIR = Join-Path $CacheDir "uv"
    New-Item -ItemType Directory -Path $env:UV_PYTHON_INSTALL_DIR -Force | Out-Null
    New-Item -ItemType Directory -Path $env:UV_CACHE_DIR -Force | Out-Null

    $PythonSpec = $null
    $SystemPython = Get-Command python.exe -ErrorAction SilentlyContinue
    if (-not $SystemPython) { $SystemPython = Get-Command python -ErrorAction SilentlyContinue }
    if ($SystemPython -and (Test-PythonSupported $SystemPython.Source)) {
        $PythonSpec = $SystemPython.Source
    }
    else {
        Write-Step "Preparing managed Python $PythonVersion..."
        Invoke-CheckedNative -FilePath $Uv -Arguments @("python", "install", $PythonVersion)
        $PythonSpec = $PythonVersion
    }

    $Python = Join-Path $VenvDir "Scripts\python.exe"
    if (-not (Test-Path $Python) -or -not (Test-PythonSupported $Python)) {
        Remove-Item $VenvDir -Recurse -Force -ErrorAction SilentlyContinue
        Invoke-CheckedNative -FilePath $Uv -Arguments @("venv", "--python", $PythonSpec, $VenvDir)
    }

    Write-Step "Installing backend dependencies..."
    Invoke-CheckedNative -FilePath $Uv -Arguments @("pip", "install", "--python", $Python, "--upgrade", "-e", (Join-Path $AppDir "backend"))
    return $Python
}

function Test-NodeSupported([string]$Node) {
    try {
        $Version = & $Node -p "process.versions.node"
        if (-not $Version) { return $false }
        $Parts = $Version.Split('.')
        $Major = [int]$Parts[0]
        $Minor = [int]$Parts[1]
        if ($Major -gt 22) { return $true }
        if ($Major -eq 22 -and $Minor -ge 12) { return $true }
        if ($Major -eq 20 -and $Minor -ge 19) { return $true }
        return $false
    }
    catch { return $false }
}

function Install-Node([string]$TempDir) {
    $SystemNode = Get-Command node -ErrorAction SilentlyContinue
    $SystemNpm = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if (-not $SystemNpm) { $SystemNpm = Get-Command npm -ErrorAction SilentlyContinue }
    if ($SystemNode -and $SystemNpm -and (Test-NodeSupported $SystemNode.Source)) {
        return @{ NodeDir = (Split-Path $SystemNode.Source); Npm = $SystemNpm.Source }
    }

    $ManagedNode = Join-Path $NodeDir "node.exe"
    $ManagedNpm = Join-Path $NodeDir "npm.cmd"
    if ((Test-Path $ManagedNode) -and (Test-Path $ManagedNpm) -and (Test-NodeSupported $ManagedNode)) {
        return @{ NodeDir = $NodeDir; Npm = $ManagedNpm }
    }

    Write-Step "Installing a private Node.js runtime..."
    $Arch = if ($env:PROCESSOR_ARCHITECTURE -eq "ARM64") { "arm64" } else { "x64" }
    $IndexUrl = "https://nodejs.org/download/release/latest-v$NodeChannel.x/"
    $Index = (Invoke-WebRequest -UseBasicParsing -Uri $IndexUrl).Content
    $Pattern = "node-v[0-9.]+-win-$Arch\.zip"
    $Match = [regex]::Match($Index, $Pattern)
    if (-not $Match.Success) { throw "Could not resolve a Node.js build for Windows $Arch." }

    $NodeFile = $Match.Value
    $Archive = Join-Path $TempDir $NodeFile
    $ExtractDir = Join-Path $TempDir "node"
    Invoke-WebRequest -UseBasicParsing -Uri "$IndexUrl$NodeFile" -OutFile $Archive

    $Checksums = (Invoke-WebRequest -UseBasicParsing -Uri "${IndexUrl}SHASUMS256.txt").Content
    $ChecksumPattern = '(?m)^([a-fA-F0-9]{64})\s+' + [regex]::Escape($NodeFile) + '$'
    $ChecksumMatch = [regex]::Match($Checksums, $ChecksumPattern)
    if (-not $ChecksumMatch.Success) { throw "Could not resolve the Node.js archive checksum." }
    $ExpectedHash = $ChecksumMatch.Groups[1].Value.ToLowerInvariant()
    $ActualHash = (Get-FileHash -Path $Archive -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($ExpectedHash -ne $ActualHash) { throw "Node.js archive checksum verification failed." }

    Expand-Archive -Path $Archive -DestinationPath $ExtractDir -Force
    $NodeSource = Get-ChildItem $ExtractDir -Directory | Select-Object -First 1
    if (-not $NodeSource) { throw "Node.js archive did not contain an executable runtime." }

    Remove-Item $NodeDir -Recurse -Force -ErrorAction SilentlyContinue
    Move-Item $NodeSource.FullName $NodeDir
    return @{ NodeDir = $NodeDir; Npm = (Join-Path $NodeDir "npm.cmd") }
}

function Build-Frontend($NodeRuntime) {
    $PreviousPath = $env:Path
    try {
        $env:Path = "$($NodeRuntime.NodeDir);$env:Path"
        Write-Step "Installing locked frontend dependencies..."
        Invoke-CheckedNative -FilePath $NodeRuntime.Npm -Arguments @("--prefix", (Join-Path $AppDir "frontend"), "ci", "--no-audit", "--no-fund")
        Write-Step "Building the web interface..."
        Invoke-CheckedNative -FilePath $NodeRuntime.Npm -Arguments @("--prefix", (Join-Path $AppDir "frontend"), "run", "build")
    }
    finally {
        $env:Path = $PreviousPath
    }

    if (-not (Test-Path (Join-Path $AppDir "frontend\dist\index.html"))) {
        throw "Frontend build did not produce dist/index.html."
    }
}

function Install-Launcher([string]$Python) {
    if ($NoLauncher) { return $null }
    New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
    $LauncherPs1 = Join-Path $BinDir "pyexplorer.ps1"
    $LauncherCmd = Join-Path $BinDir "pyexplorer.cmd"

    $LauncherContent = @'
param(
    [Parameter(Position = 0)][string]$Command = "start",
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$ExtraArgs
)
$ErrorActionPreference = "Stop"
$AppDir = "__APP_DIR__"
$Python = "__PYTHON__"
$RuntimeDir = "__RUNTIME_DIR__"
$PidFile = "__PID_FILE__"
$LogFile = "__LOG_FILE__"
$ErrorLogFile = "__ERROR_LOG_FILE__"
$DefaultPort = __PORT__
$Port = if ($env:PYEXPLORER_PORT) { [int]$env:PYEXPLORER_PORT } else { $DefaultPort }

function Get-RunningProcess {
    if (-not (Test-Path $PidFile)) { return $null }
    $PidValue = Get-Content $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not ($PidValue -as [int])) { return $null }
    return Get-Process -Id ([int]$PidValue) -ErrorAction SilentlyContinue
}

function Start-Server {
    $Existing = Get-RunningProcess
    if ($Existing) {
        Write-Host "pyExplorer is already running at http://127.0.0.1:$Port"
        return
    }

    New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null
    $Arguments = @("run.py", "--host", "127.0.0.1", "--port", [string]$Port) + $ExtraArgs
    $Process = Start-Process -FilePath $Python -ArgumentList $Arguments -WorkingDirectory $AppDir -WindowStyle Hidden -RedirectStandardOutput $LogFile -RedirectStandardError $ErrorLogFile -PassThru
    Set-Content -Path $PidFile -Value $Process.Id -Encoding ascii

    for ($Attempt = 0; $Attempt -lt 50; $Attempt++) {
        Start-Sleep -Milliseconds 200
        if ($Process.HasExited) {
            Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
            throw "pyExplorer failed to start. See $ErrorLogFile"
        }
        try {
            Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/api/v1/health" -TimeoutSec 1 | Out-Null
            Write-Host "pyExplorer is running at http://127.0.0.1:$Port"
            return
        }
        catch { }
    }
    Write-Host "pyExplorer is starting. Check status with: pyexplorer status"
}

switch ($Command.ToLowerInvariant()) {
    "start" { Start-Server }
    "serve" {
        Push-Location $AppDir
        try { & $Python run.py --host 127.0.0.1 --port $Port @ExtraArgs }
        finally { Pop-Location }
    }
    "stop" {
        $Process = Get-RunningProcess
        if (-not $Process) {
            Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
            Write-Host "pyExplorer is not running."
            break
        }
        Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        Write-Host "pyExplorer stopped."
    }
    "restart" {
        & $PSCommandPath stop
        & $PSCommandPath start @ExtraArgs
    }
    "status" {
        if (Get-RunningProcess) { Write-Host "pyExplorer is running at http://127.0.0.1:$Port" }
        else { Write-Host "pyExplorer is not running."; exit 1 }
    }
    "logs" {
        if (Test-Path $LogFile) { Get-Content $LogFile -Tail 120 -Wait }
        elseif (Test-Path $ErrorLogFile) { Get-Content $ErrorLogFile -Tail 120 -Wait }
        else { Write-Host "No log file exists yet." }
    }
    "open" { Start-Process "http://127.0.0.1:$Port" }
    "update" {
        $env:PYEXPLORER_HOME = "__INSTALL_ROOT__"
        $env:PYEXPLORER_BIN_DIR = "__BIN_DIR__"
        $env:PYEXPLORER_PORT = [string]$Port
        & (Join-Path $AppDir "scripts\install.ps1")
    }
    default { throw "Usage: pyexplorer {start|serve|stop|restart|status|logs|open|update}" }
}
'@

    $LauncherContent = $LauncherContent.Replace("__APP_DIR__", $AppDir)
    $LauncherContent = $LauncherContent.Replace("__PYTHON__", $Python)
    $LauncherContent = $LauncherContent.Replace("__RUNTIME_DIR__", $RuntimeDir)
    $LauncherContent = $LauncherContent.Replace("__PID_FILE__", $PidFile)
    $LauncherContent = $LauncherContent.Replace("__LOG_FILE__", $LogFile)
    $LauncherContent = $LauncherContent.Replace("__ERROR_LOG_FILE__", $ErrorLogFile)
    $LauncherContent = $LauncherContent.Replace("__INSTALL_ROOT__", $InstallRoot)
    $LauncherContent = $LauncherContent.Replace("__BIN_DIR__", $BinDir)
    $LauncherContent = $LauncherContent.Replace("__PORT__", [string]$Port)
    Set-Content -Path $LauncherPs1 -Value $LauncherContent -Encoding utf8
    Set-Content -Path $LauncherCmd -Value "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$LauncherPs1`" %*`r`n" -Encoding ascii

    $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $PathParts = if ($UserPath) { $UserPath.Split(';') } else { @() }
    if ($PathParts -notcontains $BinDir) {
        $NewPath = if ($UserPath) { "$UserPath;$BinDir" } else { $BinDir }
        [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
    }

    return $LauncherPs1
}

New-Item -ItemType Directory -Path $InstallRoot -Force | Out-Null
New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null
New-Item -ItemType Directory -Path $CacheDir -Force | Out-Null
$TempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("pyexplorer-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

try {
    Stop-ExistingProcess
    if ($Source) {
        Copy-SourceTree $Source $TempDir
    }
    else {
        $DownloadedSource = Get-RepositorySource $TempDir
        Copy-SourceTree $DownloadedSource $TempDir
    }

    if (-not (Test-Path (Join-Path $AppDir ".env")) -and (Test-Path (Join-Path $AppDir "backend\.env.example"))) {
        Copy-Item (Join-Path $AppDir "backend\.env.example") (Join-Path $AppDir ".env")
    }

    $Uv = Get-Uv
    $Python = Install-Python $Uv
    $NodeRuntime = Install-Node $TempDir
    Build-Frontend $NodeRuntime
    $Launcher = Install-Launcher $Python

    Write-Host ""
    Write-Host "pyExplorer installation completed successfully." -ForegroundColor Green
    Write-Host "Application: $AppDir"
    if ($Launcher) {
        Write-Host "Launcher:    $BinDir\pyexplorer.cmd"
        Write-Host "A new terminal can use: pyexplorer start"
    }

    if (-not $NoStart) {
        if ($Launcher) {
            & $Launcher start
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
