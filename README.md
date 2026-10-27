# TAEL AI (V3)
**Task-Adaptive Efficient Language AI**
*"Capable local AI, built for everyday hardware."*

TAEL V3 is a local-first AI software creation and research assistant designed for everyday laptops (including 8GB RAM CPU-only systems).

## Key Features

- **Local Inference Baseline:** Designed around IBM Granite Code 3B using local backends (Ollama / llama.cpp).
- **Coding Engine Integration:** Integrates with Aider for focused, reviewable code modifications and test/diff loops.
- **Built-in Persistent Project Memory:** SQLite + FTS5 indexed memory store per user project with bounded token-budget retrieval and Markdown export/import.
- **Hardware-Aware Resource Supervisor:** Monitors RAM and CPU, dynamically applying backpressure and resource profiles (Conservative 8GB and Balanced).
- **Typed Tool Registry & Policy System:** Schema-validated tools with explicit capability grants, approval gates, sandboxing, and auditable action logs.
- **Unified Interfaces:** CLI application and local HTTP API server for editor/extension integrations.

## Architecture

See [PLAN.md](PLAN.md) for full architectural specifications and [PROJECT_MEMORY.md](PROJECT_MEMORY.md) for project development continuity.

## Getting Started

```bash
# Setup with uv
uv venv
uv pip install -e ".[dev]"

# Run TAEL CLI
tael --help
tael status
```
