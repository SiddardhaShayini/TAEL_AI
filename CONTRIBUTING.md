# Contributing to TAEL AI (V3)

Thank you for your interest in contributing to **TAEL AI** (*Task-Adaptive Efficient Language AI*)!

TAEL V3 is a local-first, privacy-respecting AI pair programmer engineered specifically for everyday hardware (such as 8GB RAM CPU-only laptops). We welcome contributions from the community—whether it's reporting bugs, improving documentation, adding new tools, or optimizing system resource efficiency.

---

## Table of Contents

1. [Core Design Constraints & Philosophy](#core-design-constraints--philosophy)
2. [Prerequisites & Development Setup](#prerequisites--development-setup)
3. [Repository Structure](#repository-structure)
4. [Development Workflow](#development-workflow)
5. [Testing & Diagnostics](#testing--diagnostics)
6. [How to Add a New Tool to the Registry](#how-to-add-a-new-tool-to-the-registry)
7. [Building Standalone Binaries & Packaging](#building-standalone-binaries--packaging)
8. [Commit & Pull Request Guidelines](#commit--pull-request-guidelines)
9. [Developer & Maintainer](#developer--maintainer)

---

## 1. Core Design Constraints & Philosophy

When contributing code to TAEL V3, keep these fundamental principles in mind:

- **Local Inference First:** The primary baseline model is **IBM Granite Code 3B** served locally over loopback (`127.0.0.1:11434`) via Ollama. Cloud APIs must never be mandatory for core functionality.
- **Strict Hardware Governance:** The system must run smoothly on everyday laptops with $\le$ 8GB RAM without freezing the OS. Always use the `ResourceMonitor` and never leak memory.
- **Model Eviction Protocol:** When an interactive session terminates, the model runner must be evicted using `keep_alive: 0` so `llama-server.exe` does not linger in RAM.
- **Path Confinement:** Every file operation MUST pass through `validate_workspace_path` to prevent path traversal outside the user's workspace.
- **Zero In-Memory Loops:** Background tasks and subagents communicate reactively via async notifications; avoid CPU-busy polling loops.

---

## 2. Prerequisites & Development Setup

### System Requirements
- **OS:** Windows 10/11, macOS, or Linux (Ubuntu 22.04+)
- **Python:** Python 3.11 or 3.12 (managed with [uv](https://docs.astral.sh/uv/))
- **Node.js:** Node.js 20 LTS (required only if modifying the VS Code extension)
- **Local LLM Engine:** [Ollama](https://ollama.com) with `granite-code:3b`

### Step-by-Step Setup

1. **Fork and Clone the Repository:**
   ```bash
   git clone https://github.com/SiddardhaShayini/TAEL_AI.git
   cd TAEL_AI
   ```

2. **Automated Setup (Recommended):**
   - **Windows:**
     ```powershell
     powershell -ExecutionPolicy Bypass -File .\setup.ps1
     ```
   - **Linux / macOS:**
     ```bash
     bash setup.sh
     ```

3. **Manual Setup using `uv`:**
   ```bash
   uv venv
   # On Windows:
   .venv\Scripts\activate
   # On Linux/macOS:
   source .venv/bin/activate

   uv pip install -e ".[dev]"
   ```

4. **Pull Local Model:**
   ```bash
   ollama pull granite-code:3b
   ```

5. **Verify Installation:**
   ```bash
   tael doctor
   ```

---

## 3. Repository Structure

```
TAEL_AI/
├── .github/workflows/          # CI and Release automated pipelines
├── assets/                     # Logos, branding icons, and graphics
├── docs/                       # Technical architecture, MCP, and quickstart docs
├── examples/                   # Reference apps and programmatic workflow demos
│   ├── inventory_app/          # Reference SQLite offline inventory app
│   └── demo_workflow.py        # End-to-end 5-step subsystem demo
├── extensions/vscode/          # Official TAEL AI VS Code companion extension
├── packaging/                  # PyInstaller standalone build specifications
├── scripts/                    # Automation scripts (standalone build, release, vsix)
├── src/tael/                   # Core Python package
│   ├── api/                    # FastAPI server & SSE streaming studio
│   ├── cli/                    # Rich terminal CLI commands & onboarding
│   ├── coding/                 # Aider bridge and autonomous editing tool
│   ├── config/                 # Settings, Pydantic validation, defaults.yaml
│   ├── connectors/             # External MCP client & protocol bridge
│   ├── core/                   # Task orchestrator, planner, and session state
│   ├── eval/                   # Doctor diagnostics and benchmark suites
│   ├── memory/                 # SQLite + FTS5 BM25 persistent memory engine
│   ├── models/                 # Ollama client, model runtime manager & eviction
│   ├── policy/                 # Approval gates, audit logging & git checkpoints
│   ├── research/               # Search engine and web page reader connectors
│   ├── resources/              # Hardware sampler, profiles, and backpressure
│   └── tools/                  # Typed sandboxed tool registry & implementations
├── tests/                      # Comprehensive pytest unit and integration suite
├── launch_studio.bat           # 1-click Windows Web Studio launcher
├── pyproject.toml              # Build metadata and dependencies
└── README.md                   # Project overview and quickstart
```

---

## 4. Development Workflow

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. Maintain clean code style and type annotations:
   - Follow standard PEP 8 conventions.
   - Use type hints (`typing.Optional`, `typing.List`, `typing.Dict`).
   - Prefer standard library solutions where possible to keep the standalone binary lightweight.
3. Test thoroughly before staging:
   ```bash
   pytest -v
   tael doctor
   ```

---

## 5. Testing & Diagnostics

Every contribution must maintain **100% test pass rate** across all platforms.

### Running Unit & Integration Tests
```bash
pytest -v
```

### Running the Evaluation Benchmark Suite
```bash
tael eval
```
The benchmark suite validates:
- `SAF-01` to `SAF-03`: Safety, path traversal prevention, secret redaction, approval gates.
- `TOOL-01` to `TOOL-02`: Schema validation and subprocess timeout bounds.
- `MEM-01` to `MEM-02`: SQLite FTS5 search ranking and context budget compliance.
- `RES-01`: Hardware resource sampler accuracy.

### Running System Diagnostics
```bash
tael doctor
```

---

## 6. How to Add a New Tool to the Registry

Adding a new capability to TAEL's agent is straightforward and declarative:

1. **Subclass `BaseTool`** in `src/tael/tools/`:
   ```python
   from typing import Any, Dict
   from tael.tools.base import BaseTool, ToolResult
   from tael.policy.permissions import PermissionLevel

   class CalculateHashTool(BaseTool):
       name = "calculate_hash"
       description = "Compute SHA256 checksum of a file in the workspace."
       permission = PermissionLevel.READ_WORKSPACE
       parameters_schema = {
           "type": "object",
           "properties": {
               "path": {
                   "type": "string",
                   "description": "Relative workspace file path."
               }
           },
           "required": ["path"]
       }

       def run(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
           import hashlib
           from tael.policy.permissions import validate_workspace_path
           ws_root = context.get("workspace_root", ".")
           target = validate_workspace_path(arguments["path"], ws_root)
           if not target.exists():
               return ToolResult(success=False, data=None, error=f"File not found: {arguments['path']}")
           
           sha256 = hashlib.sha256(target.read_bytes()).hexdigest()
           return ToolResult(success=True, data={"path": arguments["path"], "sha256": sha256})
   ```

2. **Register the tool** in `src/tael/tools/__init__.py`:
   ```python
   registry.register(CalculateHashTool())
   ```

3. **Add aliases if common synonyms exist** in `ToolRegistry.ALIASES` in `src/tael/tools/registry.py`.

4. **Add a unit test** in `tests/test_tools.py`.

---

## 7. Building Standalone Binaries & Packaging

To compile and verify the zero-dependency Windows executable:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_standalone.ps1
```

To build a full release bundle (`.exe`, `.vsix`, and `SHA256SUMS.txt`):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\release.ps1
```

---

## 8. Commit & Pull Request Guidelines

### Commit Messages
We follow the [Conventional Commits](https://www.conventionalcommits.org/) format:
- `feat(tool): add calculate_hash tool`
- `fix(memory): prevent duplicate FTS entries on re-indexing`
- `docs(readme): add troubleshooting section for Ollama loopback`
- `perf(resources): optimize hardware sampler interval`

### Submitting a Pull Request
1. Ensure `pytest` passes with 0 failures.
2. Update `PROJECT_MEMORY.md` with a summary of changes if modifying architecture or adding significant capabilities.
3. Push your branch and open a PR against `main`.
4. Our multi-OS GitHub Actions workflow (`ubuntu-latest` and `windows-latest`) will automatically run `pytest` and `tael eval`.

---

## 9. Developer & Maintainer

**Siddardha Shayini**  
GitHub: [https://github.com/SiddardhaShayini](https://github.com/SiddardhaShayini)  
Project Repository: [https://github.com/SiddardhaShayini/TAEL_AI](https://github.com/SiddardhaShayini/TAEL_AI)
