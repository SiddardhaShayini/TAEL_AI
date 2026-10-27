# TAEL V3 — Build Plan

> [!NOTE]
> This plan covers the initial implementation sprint: scaffolding the project structure, building the core orchestrator, tool system, memory system, and CLI/API — enough to have a working local coding assistant.

## Phase 0 + 1: Foundation & Core Coding Engine

### Step 1: Project Scaffold
- Python project with `pyproject.toml` (uv-managed)
- Package structure: `src/tael/` with subpackages
- Configuration system with YAML defaults
- Logging framework

### Step 2: Configuration & Resource Monitoring
- Hardware detection (RAM, CPU cores, OS)
- Resource profiles (Conservative 8GB, Balanced)
- Runtime resource sampler (memory, CPU)
- Backpressure signals

### Step 3: Local Model Runtime Manager
- Ollama integration for IBM Granite Code 3B
- Model lifecycle (check, pull, start, health, stop)
- Loopback-only binding, request limits
- Fallback behavior and clear error reporting

### Step 4: Tool System (Typed Registry)
- Tool base class with schema, permissions, resource limits
- Tool registry with validation and dispatch
- Built-in tools: file read/write/list, directory tree, search/grep, Git status/diff/log, Python/shell execution (sandboxed), system info
- Approval gates and audit logging

### Step 5: Policy & Approval Service
- Permission levels (read, write, execute, internet, app-launch)
- Per-action confirmation prompts
- Workspace confinement (canonical paths, symlink checks)
- Audit log (action, tool, scope, outcome, approval)

### Step 6: Context & Memory System
- SQLite + FTS5 per-project memory store
- Memory entries: category, tags, verification status, source, supersession
- Task-start retrieval with token budget
- On-demand search, add/update/supersede
- Markdown import/export
- User controls (inspect, edit, disable, clear, delete)

### Step 7: Task Orchestrator
- Request → plan → steps pipeline
- Aider integration for code editing
- Step execution with budget, cancellation, error limits
- Progress reporting and completion summary

### Step 8: Aider Integration
- Configure Aider with local Granite endpoint
- Project-aware context feeding
- Diff review, test/build iteration loop
- Cancellation and timeout handling

### Step 9: CLI Interface
- `tael` command with subcommands: `chat`, `init`, `status`, `memory`, `config`
- Streaming chat with tool execution display
- Task plan display and approval
- Resource status display

### Step 10: Local API Server
- FastAPI service on loopback
- Session management
- Endpoints: chat, tools, memory, status, config
- Client authentication (local token)
- Request size/duration/concurrency limits

## Files to Create

```
d:\TAEL_AI_V3\
├── pyproject.toml
├── README.md
├── PLAN.md (existing)
├── PROJECT_MEMORY.md (existing)
├── src/
│   └── tael/
│       ├── __init__.py
│       ├── __main__.py
│       ├── config/
│       │   ├── __init__.py
│       │   ├── settings.py          # Pydantic settings & YAML loader
│       │   └── defaults.yaml        # Default configuration
│       ├── core/
│       │   ├── __init__.py
│       │   ├── orchestrator.py      # Task orchestrator
│       │   ├── planner.py           # Task planning
│       │   └── session.py           # Session state management
│       ├── models/
│       │   ├── __init__.py
│       │   ├── runtime.py           # Model runtime manager (Ollama)
│       │   └── client.py            # LLM client abstraction
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── registry.py          # Tool registry & dispatch
│       │   ├── base.py              # Base tool class
│       │   ├── workspace.py         # File/directory tools
│       │   ├── git_tools.py         # Git operations
│       │   ├── execution.py         # Python/shell execution
│       │   └── system_info.py       # System information
│       ├── memory/
│       │   ├── __init__.py
│       │   ├── store.py             # SQLite + FTS5 memory store
│       │   ├── retrieval.py         # Task-aware retrieval
│       │   └── models.py            # Memory entry data models
│       ├── policy/
│       │   ├── __init__.py
│       │   ├── permissions.py       # Permission levels & grants
│       │   ├── approval.py          # Approval prompts & gates
│       │   └── audit.py             # Audit logging
│       ├── resources/
│       │   ├── __init__.py
│       │   ├── monitor.py           # Resource monitoring
│       │   └── profiles.py          # Resource profiles
│       ├── coding/
│       │   ├── __init__.py
│       │   └── aider_bridge.py      # Aider integration
│       ├── cli/
│       │   ├── __init__.py
│       │   └── app.py               # CLI application
│       └── api/
│           ├── __init__.py
│           └── server.py            # Local API server
└── tests/
    ├── __init__.py
    ├── test_config.py
    ├── test_tools.py
    ├── test_memory.py
    ├── test_policy.py
    └── test_resources.py
```
