# Boot the AULA backend + frontend (one server). Usage: .\run.ps1
# Serves the app at http://localhost:8000
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv .venv
}

& ".venv\Scripts\Activate.ps1"
python -m pip install -q -r requirements.txt

Write-Host ""
Write-Host "AULA is starting -> http://localhost:8000" -ForegroundColor Green
Write-Host ""
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
