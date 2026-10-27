# TAEL V3 One-Command Setup & Launch Script for Windows
# Run via: powershell -ExecutionPolicy Bypass -File .\setup.ps1

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host " TAEL V3: Task-Adaptive Efficient Language AI Setup   " -ForegroundColor Green
Write-Host " 'Capable local AI, built for everyday hardware.'     " -ForegroundColor DarkCyan
Write-Host "======================================================" -ForegroundColor Cyan

# 1. Check Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[!] Error: Python 3.11+ is required but was not found on PATH." -ForegroundColor Red
    Write-Host "    Download Python from https://www.python.org/downloads/" -ForegroundColor Yellow
    Exit 1
}

$pyVer = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "[+] Found Python $pyVer" -ForegroundColor Green

# 2. Check or Install uv
$uvCmd = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvCmd) {
    Write-Host "[*] uv package manager not found. Installing uv..." -ForegroundColor Yellow
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","User") + ";" + [System.Environment]::GetEnvironmentVariable("Path","Machine")
}

# 3. Create Virtual Environment
if (-not (Test-Path ".venv")) {
    Write-Host "[*] Creating virtual environment (.venv)..." -ForegroundColor Yellow
    uv venv
}

# 4. Install Dependencies
Write-Host "[*] Installing TAEL V3 and dependencies..." -ForegroundColor Yellow
uv pip install -e ".[dev]"

# 5. Run Onboarding Diagnostics
Write-Host "`n[*] Running First-Run System Check..." -ForegroundColor Green
& .venv\Scripts\tael.exe doctor

Write-Host "`n======================================================" -ForegroundColor Cyan
Write-Host " TAEL V3 Setup Successfully Completed!                " -ForegroundColor Green
Write-Host " Start coding:  .venv\Scripts\tael.exe chat           " -ForegroundColor Yellow
Write-Host " System status: .venv\Scripts\tael.exe status         " -ForegroundColor Yellow
Write-Host "======================================================" -ForegroundColor Cyan
