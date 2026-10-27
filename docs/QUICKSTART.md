<p align="center">
  <img src="../assets/tael-logo-v3.svg" width="100" height="100" alt="TAEL AI Logo" />
</p>

# TAEL V3 — Beginner's Quickstart Guide

**TAEL V3** (Task-Adaptive Efficient Language AI) is a local-first AI software creation and research assistant designed for everyday hardware, including CPU-only laptops with 8GB RAM.

---

## 1. Quick Installation (One-Command)

### Windows (PowerShell)
```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

### Linux / macOS
```bash
bash setup.sh
```

The setup script checks your Python installation, sets up a fast virtual environment via `uv`, installs TAEL, and runs a diagnostic self-check.

---

## 2. Setting Up Local Inference (IBM Granite Code 3B)

TAEL is optimized to run **IBM Granite Code 3B** locally through **Ollama**:

1. Download and run Ollama from [https://ollama.com](https://ollama.com).
2. Pull the Granite Code 3B model (approx 2.0 GB):
   ```bash
   ollama pull granite-code:3b
   ```
3. Run the TAEL doctor to verify the connection:
   ```bash
   tael doctor
   ```

*Note: If Ollama is offline, TAEL automatically operates with built-in mock/deterministic mode for testing.*

---

## 3. CLI Commands Reference

| Command | Description |
| :--- | :--- |
| `tael chat [PROMPT]` | Start an interactive coding session or run a single prompt |
| `tael server [--port 7860]` | Launch local HTTP service and interactive Web Studio dashboard |
| `tael status` | Show current RAM, CPU, active profile, and model backend status |
| `tael doctor` | Run full system security and diagnostic checks |
| `tael eval [--category ...]` | Run automated evaluation benchmark suite |
| `tael init` | Run the first-run hardware onboarding wizard |
| `tael memory list` | View active project memory entries |
| `tael memory search <query>` | Full-text search (FTS5) across project memory |
| `tael memory export` | Export project memory to Markdown |
| `tael memory clear` | Clear stored memories for current project |
| `tael research <query>` | Search the web for technical documentation and libraries |
| `tael profile <cmd>` | Benchmark execution time and peak RAM usage of a command |

---

## 4. Common Tasks

### Starting an Interactive Coding Session
```bash
tael chat "Create a small inventory app with offline storage and tests"
```

### Launching the Web Studio Dashboard
```bash
tael server
```
Open `http://127.0.0.1:7860` in your web browser.

### Running System Health Diagnostics
```bash
tael doctor
```

### Running the Evaluation Benchmark Suite
```bash
tael eval --export BENCHMARK_REPORT.md
```

### Researching Technical Libraries
```bash
tael research "Pydantic V2 migration best practices"
```

### Profiling an Algorithm
```bash
tael profile "python -c 'sum(x**2 for x in range(1000000))'"
```

---

## 5. VS Code Extension Installation

1. Package the extension:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\package_vscode.ps1
   ```
2. In VS Code, open Extensions (`Ctrl+Shift+X`), click `...` -> **Install from VSIX...**, and choose `extensions/vscode/tael-ai-3.0.0.vsix`.
3. Press `Ctrl+Shift+P` -> **TAEL AI: Open Web Studio** to open the assistant beside your editor.

---

## 6. Standalone Executable Packaging

To build a standalone Windows binary (`dist/tael.exe`) that runs on computers without Python:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_standalone.ps1
```

---

## 7. Security & Privacy

- **Local Inference:** Your code and prompts stay on your machine.
- **Approval Gates:** File writes, shell commands, and application launches require explicit user confirmation.
- **Confinement:** File tools cannot read or modify files outside your project workspace.
- **Audit Logging:** Every tool call is recorded to `.tael/audit.log` with secrets automatically redacted.
