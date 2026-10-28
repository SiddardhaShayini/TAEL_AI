@echo off
title TAEL AI Studio Launcher
echo ===================================================
echo           TAEL AI Studio Launcher
echo ===================================================
echo Starting TAEL AI Local Service...

start "" http://127.0.0.1:7860

if exist "dist\tael.exe" (
    echo [OK] Launching Standalone Binary (dist\tael.exe)...
    dist\tael.exe server
) else if exist "release\tael-v3.0.0-windows-x64.exe" (
    echo [OK] Launching Release Binary...
    release\tael-v3.0.0-windows-x64.exe server
) else if exist ".venv\Scripts\tael.exe" (
    echo [OK] Launching from Python Virtual Environment...
    .venv\Scripts\tael.exe server
) else (
    echo [ERROR] Neither standalone executable nor virtual environment found.
    echo Please run setup.ps1 or build_standalone.ps1 first.
    pause
)
