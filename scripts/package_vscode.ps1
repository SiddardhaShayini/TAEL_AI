<#
.SYNOPSIS
Packages the TAEL AI VS Code companion extension into a .vsix file.
#>
$ErrorActionPreference = "Stop"
Write-Host "=== TAEL AI VS Code Companion Packager ===" -ForegroundColor Cyan

$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$ExtensionDir = Join-Path $WorkspaceRoot "extensions\vscode"
Set-Location $ExtensionDir

Write-Host "Packaging extension from $ExtensionDir..." -ForegroundColor Green
& npx --yes @vscode/vsce package --no-git-tag-version --allow-missing-repository

$VsixFiles = Get-ChildItem -Filter "*.vsix"
if ($VsixFiles) {
    Write-Host "`n[SUCCESS] Packaged VSIX: $($VsixFiles[0].Name)" -ForegroundColor Green
    Write-Host "Install in VS Code via: Extensions -> ... -> Install from VSIX..." -ForegroundColor Cyan
} else {
    Write-Error "Packaging completed but no .vsix file was found."
}
