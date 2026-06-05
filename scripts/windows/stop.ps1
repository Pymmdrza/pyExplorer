$ErrorActionPreference = "Stop"

Write-Host "== Stopping pyExplorer local dev ports ==" -ForegroundColor Cyan

$Ports = @(8000, 5173)
foreach ($Port in $Ports) {
    $Connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($ProcessId in $Connections) {
        if ($ProcessId -and $ProcessId -ne 0) {
            Write-Host "Stopping process $ProcessId on port $Port" -ForegroundColor Yellow
            Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
        }
    }
}

Write-Host "Done." -ForegroundColor Green