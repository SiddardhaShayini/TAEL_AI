# TAEL AI Companion for VS Code

The official VS Code companion extension for **TAEL V3** (Task-Adaptive Efficient Language AI).

## Overview

TAEL is a local-first AI creation and research assistant engineered for everyday hardware (8GB RAM laptops). This lightweight extension connects VS Code directly to your local TAEL AI service (`http://127.0.0.1:7860`).

## Features

- **Interactive Web Studio Beside Code**: Open the full TAEL AI Web Studio tab in an editor split pane right beside your active files (`Ctrl+Shift+P` -> `Open TAEL Web Studio`).
- **Quick Natural-Language Tasks**: Dispatch instructions, bug fixes, or architecture queries without leaving your current editor (`Ctrl+Shift+P` -> `Ask TAEL / Run Task`).
- **Workspace Safety Checkpoints**: Create instant snapshot checkpoints before major refactors (`tael.checkpoint`).
- **One-Click Rollback**: Inspect and restore prior snapshots if an experimental modification went wrong (`tael.rollback`).
- **Integrated Diagnostics**: Run the system doctor directly in your integrated terminal (`tael.doctor`).

## Prerequisites

1. Ensure the TAEL local service is running in your workspace:
   ```bash
   tael-server
   # or via python:
   uv run python -m tael.cli.app server
   ```
2. By default, the extension connects to `http://127.0.0.1:7860`. You can customize this in VS Code Settings under `tael.serviceUrl`.

## Installation

To load this extension in VS Code for development or everyday use:
1. Open this folder in VS Code (`d:\TAEL_AI_V3\extensions\vscode`).
2. Press `F5` to open an **Extension Development Host** window.
3. Or package as `.vsix` using `npx vsce package` and install via `Extensions -> Install from VSIX...`.
