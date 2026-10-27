# TAEL AI (V3)
**Task-Adaptive Efficient Language AI**  
*"Capable local AI, built for everyday hardware."*

TAEL V3 is a local-first AI software creation and research assistant designed for everyday laptops, specifically engineered to operate reliably on CPU-only systems with 8GB RAM.

---

## Key Features

- **Local Inference Baseline:** Designed around IBM Granite Code 3B served locally via Ollama or llama.cpp over loopback.
- **Coding Engine Integration:** Integrates with Aider for focused, reviewable code modifications and test/diff loops.
- **Built-in Persistent Project Memory:** SQLite + FTS5 indexed memory store per user project with bounded token-budget retrieval and Markdown export/import.
- **Hardware-Aware Resource Supervisor:** Monitors RAM and CPU, dynamically applying backpressure and resource profiles (Conservative 8GB and Balanced).
- **Typed Tool Registry & Policy System:** Schema-validated tools with explicit capability grants, approval gates, sandboxing, and auditable action logs.
- **Deep Internet Research:** Search and web page reader connectors with untrusted external content isolation.
- **Permissioned Desktop Assistance:** Approved application launch allowlist (`notepad`, `vscode`, `terminal`, `calc`) and URL opener.
- **Hardware Optimization Profiler:** Subprocess execution benchmarking measuring execution time, peak memory (MB), and before/after comparisons.
- **Extensible Connectors:** Stdio-based MCP (Model Context Protocol) client and tool adapter.
- **Unified Interfaces:** Rich CLI application and local HTTP API server for editor/extension integrations.

---

## Quickstart

### 1. One-Command Setup

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

**Linux / macOS:**
```bash
bash setup.sh
```

### 2. Run Diagnostics
```bash
tael doctor
```

### 3. Interactive Coding Session
```bash
tael chat "Create a small inventory app with offline storage and tests"
```

### 4. CLI Subcommands
```bash
# Check hardware status & active profile
tael status

# Search and synthesize web research
tael research "Pydantic V2 migration patterns"

# Profile command execution time and peak memory
tael profile "python -c 'sum(range(500000))'"

# Manage persistent project memory
tael memory list
tael memory search "conventions"
tael memory export
```

---

## Documentation

- [Quickstart Guide](docs/QUICKSTART.md) — Beginner installation and configuration
- [Technical Architecture](docs/ARCHITECTURE.md) — Subsystem designs and security model
- [Full Plan](PLAN.md) — Product vision and specification
- [Development Memory](PROJECT_MEMORY.md) — Engineering work log and project continuity
