<#
.SYNOPSIS
Builds, tests, and bundles complete TAEL V3 release distributions (Windows x64 executable and VS Code .vsix) into a release/ folder with SHA256 checksums.
#>
$ErrorActionPreference = "Stop"
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   TAEL V3 Automated Release Packager        " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
Set-Location $WorkspaceRoot

$ReleaseDir = Join-Path $WorkspaceRoot "release"
if (Test-Path $ReleaseDir) {
    Remove-Item -Recurse -Force $ReleaseDir
}
New-Item -ItemType Directory -Path $ReleaseDir | Out-Null

# 1. Run Automated Tests
Write-Host "`n[Step 1/4] Running unit and integration tests..." -ForegroundColor Green
& ".\.venv\Scripts\pytest.exe" -q
if ($LASTEXITCODE -ne 0) {
    Write-Error "Tests failed! Aborting release packaging."
}

# 2. Package VS Code Extension
Write-Host "`n[Step 2/4] Packaging VS Code companion extension (.vsix)..." -ForegroundColor Green
& powershell -ExecutionPolicy Bypass -File ".\scripts\package_vscode.ps1"
$VsixFile = Get-ChildItem -Path "extensions\vscode" -Filter "*.vsix" | Select-Object -First 1
if ($VsixFile) {
    Copy-Item $VsixFile.FullName (Join-Path $ReleaseDir $VsixFile.Name)
    Write-Host "Copied $($VsixFile.Name) to release\" -ForegroundColor Green
}

# 3. Build Standalone Windows Executable
Write-Host "`n[Step 3/4] Building standalone Windows executable..." -ForegroundColor Green
& powershell -ExecutionPolicy Bypass -File ".\scripts\build_standalone.ps1" -Clean
$ExeFile = Join-Path $WorkspaceRoot "dist\tael.exe"
if (Test-Path $ExeFile) {
    $TargetExe = Join-Path $ReleaseDir "tael-v3.0.0-windows-x64.exe"
    Copy-Item $ExeFile $TargetExe
    Write-Host "Copied to $TargetExe" -ForegroundColor Green
}

# 4. Generate SHA256 Checksums
Write-Host "`n[Step 4/4] Generating SHA256 release checksums..." -ForegroundColor Green
$ChecksumFile = Join-Path $ReleaseDir "SHA256SUMS.txt"
$Artifacts = Get-ChildItem -Path $ReleaseDir -File | Where-Object { $_.Name -ne "SHA256SUMS.txt" }

$ChecksumLines = foreach ($item in $Artifacts) {
    $hash = (Get-FileHash -Path $item.FullName -Algorithm SHA256).Hash.ToLower()
    "$hash  $($item.Name)"
}
$ChecksumLines | Out-File -FilePath $ChecksumFile -Encoding utf8

Write-Host "`n=============================================" -ForegroundColor Cyan
Write-Host "   Release Packaging Complete!               " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Get-ChildItem -Path $ReleaseDir | ForEach-Object {
    $SizeKb = [math]::Round($_.Length / 1KB, 1)
    Write-Host "  - $($_.Name) ($SizeKb KB)" -ForegroundColor Yellow
}
Write-Host "`nArtifacts are ready in release\" -ForegroundColor Green
