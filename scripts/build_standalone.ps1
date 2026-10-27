<#
.SYNOPSIS
Builds a standalone portable Windows executable for TAEL V3 using PyInstaller.
#>
param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
Write-Host "=== TAEL V3 Standalone Executable Builder ===" -ForegroundColor Cyan

$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
Set-Location $WorkspaceRoot

if ($Clean) {
    Write-Host "Cleaning previous build artifacts..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "build", "dist"
}

# Ensure PyInstaller is installed in virtualenv
Write-Host "Checking for pyinstaller in virtual environment..." -ForegroundColor Green
& ".\.venv\Scripts\python.exe" -m pip install --quiet pyinstaller

Write-Host "Compiling standalone binary via packaging\tael.spec..." -ForegroundColor Green
& ".\.venv\Scripts\pyinstaller.exe" "packaging\tael.spec" --noconfirm

if (Test-Path "dist\tael.exe") {
    $SizeMb = [math]::Round((Get-Item "dist\tael.exe").Length / 1MB, 2)
    Write-Host "`n[SUCCESS] Standalone binary created at dist\tael.exe ($SizeMb MB)" -ForegroundColor Green
    Write-Host "You can now distribute dist\tael.exe or test via: .\dist\tael.exe doctor" -ForegroundColor Cyan
} else {
    Write-Error "Build completed but dist\tael.exe was not found."
}
