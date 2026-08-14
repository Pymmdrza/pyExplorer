@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1" %*
if errorlevel 1 exit /b %errorlevel%
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run.ps1"
exit /b %errorlevel%
