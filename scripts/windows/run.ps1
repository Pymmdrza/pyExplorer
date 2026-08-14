$ErrorActionPreference = "Stop"
$Root = Resolve-Path "$PSScriptRoot\..\.."
Push-Location $Root
python run.py @args
Pop-Location
