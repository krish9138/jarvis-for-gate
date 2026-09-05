# GATE JARVIS PowerShell Launcher
Set-Location -Path $PSScriptRoot
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "🚀 Launching GATE JARVIS (Mechanical Engineering Stage 2)" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan
py -m streamlit run "$PSScriptRoot\app.py" --server.port 8503
