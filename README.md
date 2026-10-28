<p align="center">
  <img src="assets/tael-logo-v3.svg" width="140" height="140" alt="TAEL AI Logo" />
</p>

<h1 align="center">TAEL AI (V3)</h1>
<p align="center">
  <strong>Task-Adaptive Efficient Language AI</strong><br>
  <em>"Capable local AI, built for everyday hardware."</em>
</p>

[![CI](https://github.com/SiddardhaShayini/TAEL_AI/actions/workflows/ci.yml/badge.svg)](https://github.com/SiddardhaShayini/TAEL_AI/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-green.svg)](pyproject.toml)
[![Evaluation Benchmark](https://img.shields.io/badge/Evaluation-8%2F8%20Passed%20(100%25)-brightgreen.svg)](BENCHMARK_REPORT.md)

TAEL V3 is a local-first AI software creation and research assistant designed for everyday laptops, specifically engineered to operate reliably on CPU-only systems with 8GB RAM.

---

## Key Features

- **Local Inference Baseline:** Powered by IBM Granite Code 3B running locally via Ollama or llama.cpp over loopback (`127.0.0.1:11434`).
- **Coding Engine Integration:** Integrates with Aider for focused, reviewable code modifications and test/diff loops (`AiderCodingTool`).
- **Built-in Persistent Project Memory:** SQLite + FTS5 indexed memory store per user project with bounded token-budget retrieval and Markdown export/import.
- **Hardware-Aware Resource Supervisor:** Monitors RAM and CPU in real time, dynamically applying backpressure and resource profiles (Conservative 8GB and Balanced).
- **Typed Tool Registry (18 Tools):** Schema-validated tools with explicit capability grants, approval gates, sandboxing, and auditable action logs.
- **Deep Internet Research:** Search and web page reader connectors with untrusted external content isolation.
- **Permissioned Desktop Assistance:** Approved application launch allowlist (`notepad`, `vscode`, `terminal`, `calc`) and URL opener.
- **Interactive Web Studio & Real-time SSE Streaming:** Local web dashboard at `http://127.0.0.1:7860` with live telemetry, tool schema explorer, and token streaming.
- **VS Code Companion Extension:** Side-by-side webview studio, quick prompt triggers, and one-click workspace snapshot checkpoints and rollback.
- **Hardware Optimization Profiler:** Subprocess execution benchmarking measuring execution time, peak memory (MB), and before/after comparisons.
- **Extensible Connectors:** Stdio-based MCP (Model Context Protocol) client and tool adapter.

---

## Quickstart

### Option A: Zero-Install Standalone Executable (Recommended)

No Python, Node.js, or virtual environment is required!

1. Download `tael-windows-x64.exe` from [GitHub Releases](https://github.com/SiddardhaShayini/TAEL_AI/releases) (or find it in [`dist/tael.exe`](dist/tael.exe)).
2. Start the interactive Web Studio:
   ```powershell
   .\tael.exe server
   ```
   Open `http://127.0.0.1:7860` in your browser.
3. Or chat directly from your terminal:
   ```powershell
   .\tael.exe chat "Analyze the files in examples/inventory_app"
   ```

---

### Option B: From Source (Developers)

#### 1. One-Command Setup

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

**Linux / macOS:**
```bash
bash setup.sh
```

#### 2. Verify System Health (Doctor)
```bash
tael doctor
```

#### 3. Run Evaluation Benchmarks
```bash
tael eval
```

#### 4. Launch Local Web Studio
```bash
tael server
```
Navigate to `http://127.0.0.1:7860` to access the interactive agent chat, live hardware telemetry, and registered tools.

#### 5. Interactive Coding Session via CLI
```bash
tael chat "Create a small inventory app with offline storage and tests"
```

---

## CLI Reference

| Command | Description |
| :--- | :--- |
| `tael chat [PROMPT]` | Start an interactive coding session or run a single prompt |
| `tael server [--port 7860]` | Launch the local API service and interactive Web Studio dashboard |
| `tael unload` | Evict model from RAM and terminate background `llama-server.exe` to free memory |
| `tael status` | Show current RAM, CPU, active profile, and model backend status |
| `tael doctor` | Run full system security and diagnostic checks |
| `tael eval [--category ...]` | Run versioned evaluation benchmark suite and view results |
| `tael init` | Run the first-run hardware onboarding wizard |
| `tael memory list` | View active project memory entries |
| `tael memory search <query>` | Full-text search (FTS5) across project memory |
| `tael memory export` | Export project memory to Markdown |
| `tael memory clear` | Clear stored memories for current project |
| `tael research <query>` | Search the web for technical documentation and libraries |
| `tael profile <cmd>` | Benchmark execution time and peak RAM usage of a command |
| `tael mcp [list\|test]` | Manage and inspect external Model Context Protocol (MCP) servers |

---

## Reference Examples

- [`examples/demo_workflow.py`](examples/demo_workflow.py) — End-to-end programmatic workflow testing hardware detection, SQLite FTS5 BM25 memory, git snapshots, multi-turn local Granite code orchestration, and pytest profiling.
- [`examples/inventory_app/`](examples/inventory_app/) — Complete reference application with SQLite offline storage, migrations, and unit tests.

---

## VS Code Companion Extension

The official companion extension bridges your VS Code editor directly to the local TAEL AI service:

1. Package the extension (or grab `release/tael-ai-3.0.0.vsix`):
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\package_vscode.ps1
   ```
2. Install the generated `.vsix` in VS Code:
   ```powershell
   code --install-extension release\tael-ai-3.0.0.vsix
   ```
   *Or in VS Code: Extensions (`Ctrl+Shift+X`) -> `...` -> **Install from VSIX...***
3. Open the studio beside your code using `Ctrl+Shift+P` -> **TAEL AI: Open Web Studio**.

---

## Standalone Windows Executable Build

To compile a portable standalone Windows executable (`dist/tael.exe`) from source using PyInstaller:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_standalone.ps1
```

Or generate a full release bundle with SHA256 checksums:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\release.ps1
```

---

## Documentation

- [Quickstart Guide](docs/QUICKSTART.md) — Beginner installation and configuration
- [Technical Architecture](docs/ARCHITECTURE.md) — Subsystem designs and security model
- [Contributing Guide](CONTRIBUTING.md) — Development setup, guidelines, and tool creation
- [MCP Integration Guide](docs/MCP_GUIDE.md) — Connecting external stdio MCP tools
- [Evaluation Report](BENCHMARK_REPORT.md) — Verified benchmark suite results
- [Full Plan](PLAN.md) — Authoritative product vision and specification
- [Development Memory](PROJECT_MEMORY.md) — Engineering work log and project continuity

---

## Developer

**Siddardha Shayini**  
GitHub: [https://github.com/SiddardhaShayini](https://github.com/SiddardhaShayini)
