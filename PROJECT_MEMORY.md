# TAEL V3 Development Memory

## Project Summary

TAEL V3 (Task-Adaptive Efficient Language AI) is planned as an easy-to-use, local-first AI assistant for software creation, technical research, and permissioned desktop assistance. Its initial coding stack is Aider with IBM Granite Code 3B, designed for CPU-only laptops with 8GB RAM. The plan emphasizes reliable natural-language coding workflows, deep internet research with traceable sources, hardware-aware engineering, measured resource use, privacy, safety, and clear user approval for sensitive actions.

This file is development continuity for the people and agents building TAEL V3. It records TAEL's project context and work history; the authoritative product vision, scope, architecture, and roadmap are in `PLAN.md`.

**Important distinction:** This repository's `PROJECT_MEMORY.md` is not the persistent memory feature being built into TAEL. TAEL's product must provide a separate, local, per-user-project memory store for the projects TAEL's users work on. Do not treat this development log as that runtime store or assume that user project memories belong in this repository. See the built-in memory specification in `PLAN.md` section 6.1.

## Required Reading and Working Rules

1. Start with this file as the concise project briefing. Read only the `PLAN.md` sections relevant to the task rather than rereading the whole plan by default. Use `PLAN.md` for intended behavior and scope; use this file for recent project state, decisions, work performed, and known issues.
2. Do not assume an item in the plan or memory has been implemented. Inspect the relevant project files and tests before relying on remembered claims or describing current behavior.
3. Keep changes aligned with the plan. If requirements conflict or a significant decision is unclear, document the uncertainty and ask the user rather than silently choosing a risky direction.
4. After creating, editing, deleting, or moving project files, update this file in the same work session. Record what changed, why, relevant paths, and validation performed (or why validation was not run).
5. Add a dated and timed entry to the Work Log for each meaningful work session. Include the local time and timezone when known. Keep entries factual and concise; do not claim tests or builds succeeded unless they were actually run.
6. Record mistakes, failed approaches, discovered defects, and corrections honestly. Note their impact and resolution or current status; do not erase earlier history to make the record look clean.
7. Record assumptions and decisions separately from verified facts. Mark unverified assumptions clearly and update them when checked.
8. Note outstanding work, blockers, risks, and next steps so a future agent can continue without repeating investigation.
9. Never put credentials, access tokens, private keys, or other secrets in this file. Summarize sensitive details without reproducing them.
10. Keep this memory consistent with the project. When an entry becomes outdated, add a correction or status update instead of silently rewriting history.

## Efficient Agent Context

- Treat this file as a concise index and continuity briefing, not a complete copy of the codebase or conversation history.
- For a task, read the current state and only the relevant memory entries; inspect source files, tests, and runtime state that directly bear on the requested change.
- Record durable, reusable facts, decisions, assumptions, completed changes, pitfalls, and open work. Mark assumptions and unverified claims clearly, and include relevant paths and verification dates where practical.
- Keep summaries short. Do not copy full source files, credentials, or long chat transcripts into memory. Keep detailed history available only when needed and update stale summaries transparently.
- Memory can guide where to look, but it is not proof of current behavior and must not override user instructions, project policy, or verified source.

## Current Project State

- Planning phase: TAEL V3 architecture defined in PLAN.md.
- Implementation phase: Core architecture and foundations built and verified (Phase 0 and Phase 1-2 core foundations):
  - Project scaffolded with pyproject.toml, uv virtualenv management, and Python 3.12 compatibility.
  - Configuration engine in src/tael/config/ with YAML defaults, environment overrides, and graceful .tael directory fallback.
  - Hardware-aware resource supervisor in src/tael/resources/ with dynamic profiling (Conservative 8GB vs Balanced), memory sampling, and backpressure detection.
  - Policy & approval system in src/tael/policy/ enforcing canonical workspace path confinement, user approval gates, and JSONL audit logging with secret redaction.
  - Typed tool registry in src/tael/tools/ with schema validation, execution bounds, workspace file tools (`read_file`, write_file, list_dir, search_files), git inspection tools, command execution, and system info.
  - In-product persistent project memory in src/tael/memory/ implemented with local SQLite + FTS5 full-text indexing, token-budgeted task retrieval, supersession linking, and Markdown export/import.
  - Agent orchestrator and session engine in src/tael/core/ with multi-turn tool loops, mock LLM client for deterministic testing, and cancellation handling.
  - Local model runtime abstraction in src/tael/models/ for Ollama/Granite with loopback safety validation.
  - Aider bridge in src/tael/coding/ providing configuration and command invocation for local Granite-powered editing.
  - Local API service in src/tael/api/ built with FastAPI providing session management, memory inspection, and resource status.
  - Interactive CLI in src/tael/cli/ with status, chat, memory commands and Windows CP1252/UTF-8 terminal compatibility.
  - 15 unit and integration tests passing in tests/.

## Assumptions and Open Questions

- Real-world Ollama / IBM Granite Code 3B model execution requires local installation of Ollama with granite-code:3b; system includes MockLLMClient and runtime fallbacks for offline development.
- Windows console encoding: legacy Windows terminals default to CP1252; CLI now reconfigures standard I/O to UTF-8 and uses safe ASCII fallback indicators for checkmarks and progress icons.
- Local socket / async execution on Windows sandbox: standard sandbox environment isolates network, which blocks asyncio socketpair creation unless bypass is granted for async tests; synchronous agent loop and CLI run cleanly in standard sandbox.
- Future phases remaining: Phase 3 (expanded desktop app integrations and MCP connector adapters), Phase 4 (internet search & deep research connectors), Phase 5 (hardware-aware optimization benchmark loops), Phase 6 (single-command/installer packaging).

## Work Log

### 2026-10-26 18:01 (+05:30)

- Created `PROJECT_MEMORY.md` with the TAEL V3 summary, current planning status, assumptions, open questions, and instructions for future agents.
- No software, build, or implementation work was performed.
- Validation: documentation content only; no build or tests were run.
- Mistakes or failed approaches: none known.
- Assumptions: the current `PLAN.md` is the authoritative V3 plan and this file is intended to be maintained as the project's continuity log.
- Next step: any agent starting project work must read both `PLAN.md` and `PROJECT_MEMORY.md`, inspect the actual project state, and update this log after making changes.

### 2026-10-27 10:57 (+05:30)

- Updated `PLAN.md` to specify a task-scoped project-memory feature: a compact project briefing, categorized durable entries, bounded task-relevant retrieval, verification against current source, and user controls.
- Updated the Phase 2 roadmap, memory evaluation criteria, and definition of done to include memory efficiency and quality.
- Updated this file's agent workflow to use the concise memory briefing and relevant plan sections rather than requiring full-document rereads for every task.
- This entry supersedes the earlier work-log note that told agents to read both planning documents in full.
- No software, build, or implementation work was performed.
- Validation: documentation-only changes; no build or tests were run.
- Mistakes or failed approaches: none known.
- Assumptions: the product feature should reduce repeated broad discovery while still requiring agents to verify relevant source and tests.
- Next step: evaluate storage and retrieval options during Phase 2; retain the local-first, bounded-retrieval behavior regardless of implementation choice.

### 2026-10-27 11:06 (+05:30)

- Clarified the requirement: TAEL needs an in-product persistent project-memory system for agents working on users' projects. This repository's `PROJECT_MEMORY.md` is only development continuity for building TAEL and is not that feature.
- Specified a concrete product approach in `PLAN.md` section 6.1 and Phase 2: project-isolated local SQLite/FTS5 storage, bounded task-based retrieval, on-demand search, focused updates, Markdown import/export, and user controls.
- Updated this file's title and project state to make the separation explicit and corrected the earlier entry's underspecified description.
- No software, build, or implementation work was performed.
- Validation: documentation-only changes; no build or tests were run.
- Mistakes or failed approaches: the previous documentation update described task-scoped memory at a high level but did not clearly distinguish TAEL's in-product feature from this repository's development memory or define a concrete storage/retrieval/update design.
- Next step: implement and evaluate the built-in memory system in Phase 2; do not store user project memories in this repository file.

### 2026-10-27 11:29 (+05:30)

- Read-only reviewed `D:\Optimizing Local AI Agents` (FastAgent and its OlaiEdge successor) and `D:\ThimbleLoom` (a TAEL V2 planning proposal). No files in either source project were changed.
- Added only missing V3 planning requirements: a single owner for orchestration/session/model lifecycle; explicit cross-boundary tool hand-off; bounded transient session archives; local API authentication and request limits; explicit supported-schema validation; distinction between resource monitoring and enforceable limits; model artifact integrity checks; and native-engine/platform end-to-end release tests.
- No TAEL V3 software was built or implemented.
- Validation: documentation review only; no build or tests were run.
- Mistakes or failed approaches: none known.
- Next step: resolve the remaining service/API, session-retention, platform enforcement, and model-artifact questions during the relevant feasibility and implementation phases.

### 2026-10-27 12:20 (+05:30)

- Built and validated TAEL V3 core foundation components according to `PLAN.md` and `build-plan.md`:
  - Project scaffold: `pyproject.toml`, uv configuration, `.gitignore`, `README.md`.
  - Configuration: `src/tael/config/` (`settings.py`, `defaults.yaml`) with probe-based `.tael` directory fallback.
  - Resource supervisor: `src/tael/resources/` (`profiles.py`, `monitor.py`) implementing Conservative 8GB vs Balanced profiles, live sampling of memory/CPU, and backpressure detection.
  - Policy & safety: `src/tael/policy/` (`permissions.py`, `approval.py`, `audit.py`) with canonical path validation, confinement error guards, approval handlers, and secret-redacted JSONL audit logging.
  - Typed tool registry: `src/tael/tools/` (`base.py`, `registry.py`, `workspace.py`, `git_tools.py`, `execution.py`, `system_info.py`) supporting bounded file reads, writes, directory listing, content searching, git diff/status/log, and subprocess execution.
  - In-product persistent project memory: `src/tael/memory/` (`models.py`, `store.py`, `retrieval.py`) using SQLite + FTS5 full-text search, BM25 ranking, token-budgeted prompt injection, superseding updates, and Markdown export/import.
  - Agent orchestrator: `src/tael/core/` (`orchestrator.py`, `planner.py`, `session.py`) multi-turn ReAct tool execution loop, cancellation, and progress streaming.
  - Local model runtime: `src/tael/models/` (`runtime.py`, `client.py`) with Ollama endpoint management, loopback enforcement, and MockLLMClient for testing.
  - Aider bridge: `src/tael/coding/` (`aider_bridge.py`) configuring local Granite model endpoints and Aider invocations.
  - Local API server: `src/tael/api/` (`server.py`) with FastAPI endpoints for health, status, sessions, chat, and memory search/export.
  - CLI: `src/tael/cli/` (`app.py`, `__main__.py`) supporting `tael status`, `tael chat`, `tael memory list/search/export/clear`.
- Tests created and verified: 15 tests across `test_config.py`, `test_resources.py`, `test_policy.py`, `test_tools.py`, `test_memory.py`, `test_orchestrator.py`, and `test_api.py`.
- Validation: all 15 tests passed (`15 passed in 0.67s`). CLI commands `tael status`, `tael memory list`, `tael memory search`, `tael memory export`, `tael memory clear` tested and verified working.
- Mistakes and corrections:
  1. `TaelConfig.get_default_config_path` and `get_user_tael_dir` were missing `cls` argument on `@classmethod`. Corrected.
  2. `redact_secrets` in `audit.py` had regex with `\1` on patterns without capture groups causing `re.error`. Refactored into pattern replacements.
  3. Default user home `.tael` directory had restricted permissions in Windows sandbox environment. Added probe-based write check falling back to workspace `.tael`.
  4. Windows console default CP1252 encoding threw `UnicodeEncodeError` on checkmark in `tael memory list`. Reconfigured stdout to UTF-8 and replaced non-ASCII icons with clean ASCII indicators.
- Next step: proceed to Phase 3 (MCP connectors and desktop app launch integrations) and Phase 4 (internet search & research connectors).

### 2026-10-27 12:32 (+05:30)

- Implemented Phase 3 (Desktop Assistance & MCP Connector Layer), Phase 4 (Internet Search & Deep Research), and Phase 5 (Hardware-Aware Profiling & Optimization):
  - Desktop integrations in `src/tael/tools/desktop.py`:
    - `LaunchAppTool` (`launch_application`) with approved applications allowlist (`notepad`, `vscode`, `terminal`, `calc`) and scope confirmation.
    - `OpenUrlTool` (`open_url`) opening verified http/https links in system default browser.
  - MCP connector architecture in `src/tael/connectors/mcp.py`:
    - `MCPClient` implementing JSON-RPC 2.0 over stdio for external MCP tool discovery (`tools/list`) and invocation (`tools/call`).
    - `MCPToolAdapter` converting arbitrary MCP tool definitions into schema-validated, permissioned `BaseTool` instances for TAEL's registry.
  - Internet search & research connector in `src/tael/research/`:
    - `DuckDuckGoSearchProvider` and `MockSearchProvider` for query search with structured results (`title`, `url`, `snippet`, `domain`).
    - `PageReader` fetching web pages with a 60KB payload ceiling, HTML sanitization, script/style removal, and untrusted external content banner tagging.
    - `SearchWebTool` and `FetchPageTool` registered under `PermissionLevel.INTERNET_ACCESS`.
  - Hardware-aware optimization & profiling tools in `src/tael/tools/profiler.py`:
    - `ProfileCommandTool` executing commands under child process tree memory (RSS) and duration monitoring.
    - `CompareBenchmarksTool` calculating speedup factors, percentage deltas, and memory usage differences.
  - Updated CLI in `src/tael/cli/app.py` with `tael research <query>` and `tael profile <command>`.
- Tests created and verified: 8 new tests across `test_desktop.py`, `test_mcp.py`, `test_research.py`, and `test_profiler.py` (total 23 tests).
- Validation: all 23 tests passed in 1.27s. Live search and page retrieval tested and verified. Profiler benchmark command tested on live subshell.
- Mistakes and corrections:
  1. Circular import detected between `tael.research.tools` and `tael.tools.__init__`. Resolved by making research tool registration in `create_default_registry` lazy-imported.
- Next step: Phase 6 (Packaging, beginner onboarding/first-run verification, and documentation).

### 2026-10-27 12:48 (+05:30)

- Implemented Phase 6 (Hardening, Packaging, Beginner Onboarding, and Diagnostics):
  - First-run onboarding wizard in `src/tael/cli/onboarding.py`:
    - Checks hardware memory, CPU cores, OS, and auto-selects Conservative (8GB) vs Balanced profile.
    - Inspects Ollama and Granite Code 3B installation, displaying model download sizes (~2.0 GB) and recovery steps.
    - Generates user-customized `.tael/config.yaml` automatically without requiring manual configuration file editing.
  - Automated system diagnostics doctor in `src/tael/eval/doctor.py`:
    - Runs 6 automated verification checks: workspace confinement security, SQLite FTS5 integrity, hardware supervisor sampling, audit log & secret redaction, typed tool registry coverage (15+ tools), and model backend reachability.
  - One-command setup and launch scripts:
    - Windows PowerShell bootstrap script in `setup.ps1`: handles Python checks, installs `uv`, creates `.venv`, installs TAEL, and runs doctor.
    - POSIX bootstrap script in `setup.sh` for Linux and macOS.
  - Documentation:
    - `docs/QUICKSTART.md`: Step-by-step guide for beginners, local model setup, and CLI reference.
    - `docs/ARCHITECTURE.md`: Subsystem architectures, security model, and resource supervisor documentation.
    - Updated `README.md` with full feature overview and setup commands.
  - CLI commands registered and verified: `tael init` (onboarding wizard) and `tael doctor` (diagnostic check scorecard).
- Tests created and verified: 2 new test modules in `test_onboarding.py` and `test_doctor.py` (total 25 tests).
- Validation: all 25 tests passed in 1.66s. `tael doctor` executed on live system and cleanly passed all 5 integrity checks with warning for offline Ollama. `tael init` executed and generated valid `.tael/config.yaml`.
- Definition of Done status: all 9 criteria from `PLAN.md` Section 15 are fulfilled.
- Next step: ready for end-user interaction and natural-language coding tasks.

### 2026-10-27 13:03 (+05:30)

- Integrated TAEL official vector brand identity (`assets/tael-logo-v3.svg`):
  - Explored logo asset: 512x514 scalable SVG featuring teal microchip circuitry, memory banks, reasoning tree nodes, and off-white/gold accents.
  - Embedded logo into `README.md`, `docs/QUICKSTART.md`, and `docs/ARCHITECTURE.md`.
  - Added `/logo.svg` endpoint in `src/tael/api/server.py` serving SVG with `image/svg+xml`.
  - Built an interactive HTML dashboard at the root endpoint `GET /` on the local API server featuring live telemetry cards (RAM, CPU, Pressure, Profile), model status, and direct links to documentation and Swagger UI.
  - Added unit and integration tests in `tests/test_api.py` validating `GET /` and `GET /logo.svg`.
- Validation: all 25 tests passed in 2.11s. API dashboard verified serving HTML and SVG logo.
- Next step: deployable and ready for natural-language code creation workflows.

### 2026-10-27 14:46 (+05:30)

- Built and verified Workspace Safety Checkpoint/Rollback Recovery and Interactive Web Agent Studio:
  - Workspace Snapshot & Rollback system in `src/tael/policy/rollback.py`:
    - `SnapshotManager`: automatically creates git-staged checkpoint commits or directory snapshots before destructive changes.
    - Bound snapshot history to 20 checkpoints.
    - Added `CreateCheckpointTool` (`create_checkpoint`) and `RollbackWorkspaceTool` (`rollback_workspace`) to `src/tael/tools/workspace.py`.
    - Total tools in registry increased to 17 tools.
  - Interactive Web Studio in `src/tael/api/server.py`:
    - Tabbed UI for `GET /`: Interactive Agent Chat Studio with streaming-ready response and tool card pills, Live System Hardware Telemetry, and Registered Tools browser.
    - Added API endpoints: `GET /tools` (full schema export), `GET /checkpoints`, `POST /checkpoints`, and `POST /rollback`.
  - Tests updated and verified: added `test_snapshot_manager` in `tests/test_policy.py` and API checkpoint/tools tests in `tests/test_api.py` (total 26 tests).
- Validation: all 26 tests passed in 1.65s. `tael doctor` confirms all 17 registered tools are schema-validated.
- Next step: system is comprehensive, hardened, and ready for full end-user workflows.

### 2026-10-27 14:58 (+05:30)

- Configured GitHub remote and published codebase:
  - Added remote `origin`: `https://github.com/SiddardhaShayini/TAEL_AI.git`.
  - Renamed local branch from `master` to standard `main`.
  - Pushed all 5 commits, source modules, tests, documentation, setup scripts, and logo assets to GitHub `origin/main`.
- Validation: `git push -u origin main` succeeded with branch tracking established.
- Next step: maintain repository sync as new features and evaluations are developed.


### 2026-10-27 15:11 (+05:30)

- Implemented versioned evaluation benchmark harness and automated multi-OS CI pipeline:
  - Evaluation benchmark suite in `src/tael/eval/suites.py` and `src/tael/eval/benchmark.py`:
    - 8 benchmark cases across four critical categories:
      - `safety`: Path traversal prevention (`SAF-01`), secret & token redaction (`SAF-02`), policy approval gates (`SAF-03`).
      - `tool_reliability`: Schema validation reject missing arguments (`TOOL-01`), subprocess timeout enforcement and cleanup (`TOOL-02`).
      - `memory_efficiency`: SQLite FTS5 search & BM25 ranking (`MEM-01`), context token budget bounds (`MEM-02`).
      - `resource_bounds`: Hardware sampler accuracy under memory limits (`RES-01`).
    - Markdown and JSON report generator with millisecond-precision timing and hardware profile attribution.
  - CLI integration: added `tael eval` command supporting `--category` filtering and `--export` to Markdown/JSON files.
  - Exported benchmark results to `BENCHMARK_REPORT.md` (8/8 passed, 100.0% pass rate in 6.35s).
  - Multi-OS GitHub Actions CI workflow in `.github/workflows/ci.yml`:
    - Tests against matrix: `ubuntu-latest` and `windows-latest` across Python `3.11` and `3.12`.
    - Automatically executes `pytest` and `tael eval` benchmarks on all pull requests and pushes to `main`.
  - Refactored `MemoryStore._get_connection()` to a contextmanager with deterministic `finally: conn.close()` to prevent WinError 32 file-locking issues during test teardown.
  - Added unit test `tests/test_benchmark.py` testing the benchmark suite runner.
- Validation: 27/27 unit tests passed in 2.11s. `tael eval` passed 8/8 benchmark cases.
- Next step: commit and push evaluation suite and CI, then implement real-time streaming progress updates (SSE).


### 2026-10-27 15:16 (+05:30)

- Implemented real-time Server-Sent Events (SSE) streaming, `tael server` command, and official VS Code companion extension:
  - SSE Streaming Endpoint in `src/tael/api/server.py`:
    - Added `StreamingProgress` hook forwarding orchestrator progress events (`thought`, `tool_start`, `tool_end`, `pressure`, `done`) into a thread-safe queue.
    - Added `POST /session/{session_id}/chat/stream` yielding `text/event-stream` SSE chunks.
    - Upgraded root Web Studio (`GET /`) to consume the streaming endpoint via `ReadableStream` and render live interactive status pills for tool calls and thoughts in real time, with graceful fallback to standard JSON endpoint.
  - CLI Server Command in `src/tael/cli/app.py`:
    - Added `tael server` subcommand with `--host` and `--port` flags to spin up the local service and Web Studio with a single command.
  - Official VS Code Extension in `extensions/vscode/`:
    - `package.json`: Contributes 5 commands (`tael.openStudio`, `tael.chat`, `tael.doctor`, `tael.checkpoint`, `tael.rollback`), configuration options (`tael.serviceUrl`, `tael.authToken`), and editor title bar shortcuts.
    - `extension.js`: Implements side-by-side webview embedding of Web Studio, modal checkpoint and rollback picker, and progress notifications.
    - `README.md` and `.vscodeignore`: Clear setup and testing instructions.
  - Tests updated in `tests/test_api.py`: verified both standard `/session/{id}/chat` and SSE streaming `/session/{id}/chat/stream`.
- Validation: 27/27 tests pass in 1.79s. `tael doctor` passes all 5 system checks with mock runtime warning. `tael eval` passes 8/8 benchmark cases (100.0%) in 1.15s.
- Next step: stage, commit, and push these enhancements to GitHub `origin/main`.


### 2026-10-27 15:41 (+05:30)

- Verified live local IBM Granite Code 3B model execution and completed coding subsystem tool integration:
  - Discovered local Ollama instance on `127.0.0.1:11434` with `granite-code:3b` (3.5B parameters, Q4_0 quantization) pre-installed.
  - Executed live `tael doctor`: all 6/6 system diagnostic checks passed (`PASS`), including Model Inference Backend online.
  - Integrated `AiderCodingTool` in `src/tael/coding/tool.py` and registered it in `src/tael/tools/__init__.py`:
    - Enables the agent orchestrator to delegate multi-file code editing and refactoring tasks directly to Aider with local model guidance.
    - Provides graceful error handling and clear guidance when Aider is not yet installed on PATH.
    - Total registered tools increased to 18 tools.
  - Added unit test suite in `tests/test_aider.py` (3 tests verifying bridge availability, schema validation, and graceful fallback).
  - Configured standalone packaging and distribution assets (Phase 6):
    - PyInstaller specification in `packaging/tael.spec` bundling CLI, FastAPI service, defaults, and logo into a single Windows `.exe`.
    - Automated packaging scripts: `scripts/build_standalone.ps1` and `scripts/package_vscode.ps1`.
    - Localized extension logo and added Git repository metadata in `extensions/vscode/package.json`.
- Validation: 30/30 unit & integration tests passed in 2.78s. `tael doctor` passed all 6 checks with live local model.
- Next step: stage, commit, and push these updates to GitHub `origin/main`.


### 2026-10-27 17:49 (+05:30)

- Completed Phase 6 single-command packaging, standalone Windows compilation, and documentation refresh:
  - VS Code Companion Extension packaging:
    - Generated a pure-Python standard library 128x128 RGBA PNG icon in `extensions/vscode/assets/tael-logo.png` adhering to VS Code marketplace specifications.
    - Updated `scripts/package_vscode.ps1` to target `@vscode/vsce@3.2.1` for Node 20 LTS compatibility.
    - Added Apache 2.0 `LICENSE` to root repository and `extensions/vscode/LICENSE`.
    - Successfully built `extensions/vscode/tael-ai-3.0.0.vsix` (8 files, 11.48 KB) with zero warnings.
  - Standalone Windows Executable Compilation:
    - Installed PyInstaller in `.venv` via `uv pip install pyinstaller`.
    - Added CLI module entrypoint in `src/tael/cli/__main__.py`.
    - Compiled standalone binary `dist/tael.exe` (19.06 MB) using `scripts/build_standalone.ps1`.
    - Validated binary in isolated execution: `.\dist\tael.exe doctor` and `.\dist\tael.exe eval` ran natively and passed 8/8 evaluation cases (100.0%) in 6.37s.
  - Documentation & Tracking Updates:
    - Added `.vsix` to `.gitignore`.
    - Extensively updated `README.md` and `docs/QUICKSTART.md` covering `tael eval`, `tael server` Web Studio, VS Code `.vsix` installation, and standalone compilation.
- Validation: 30/30 unit & integration tests passing (`pytest`). `tael eval` 8/8 passing both in Python environment and compiled `dist/tael.exe`.
- Next step: stage, commit, and push changes to GitHub `origin/main`.


### 2026-10-27 17:57 (+05:30)

- Completed MCP server catalog configuration and automated multi-artifact release pipeline:
  - MCP Server Configuration & Lifecycle:
    - Added `MCPServerConfig` in `src/tael/config/settings.py` supporting `command`, `enabled`, and `permission` fields.
    - Updated `create_default_registry()` in `src/tael/tools/__init__.py` and `TaskOrchestrator` in `src/tael/core/orchestrator.py` to auto-discover and attach configured stdio MCP servers.
    - Added `tael mcp` CLI command in `src/tael/cli/app.py` with `list` and `test <server_name>` subcommands.
  - Automated Release Packaging Pipeline in `scripts/release.ps1`:
    - Executes pytest suite (30/30 passed in 2.50s).
    - Packages VS Code extension into `release/tael-ai-3.0.0.vsix` (11.5 KB).
    - Compiles clean standalone Windows binary into `release/tael-v3.0.0-windows-x64.exe` (19.07 MB).
    - Computes SHA256 hashes and writes `release/SHA256SUMS.txt`.
  - Added `release/` to `.gitignore`.
- Validation: 30/30 tests passed (`pytest`). Release binary verified: `.\release\tael-v3.0.0-windows-x64.exe --version` returns `tael 3.0.0a1`.
- Next step: stage, commit, and push updates to GitHub `origin/main`.


### 2026-10-27 18:03 (+05:30)

- Added automated GitHub Release workflow, MCP defaults, and technical documentation:
  - Configuration & Guide:
    - Updated `src/tael/config/defaults.yaml` with `mcp_servers: {}` block.
    - Created `docs/MCP_GUIDE.md` covering stdio JSON-RPC handshake, configuration examples, `tael mcp test` diagnostics, and permission confinement.
    - Added MCP documentation link in `README.md`.
  - Automated Release CI Workflow (`.github/workflows/release.yml`):
    - Triggers on git tags `v*` (or manual dispatch).
    - Compiles the standalone Windows executable on `windows-latest`.
    - Packages the VS Code extension on `ubuntu-latest`.
    - Generates SHA256 checksums and automatically publishes a official GitHub Release via `softprops/action-gh-release@v2`.
- Validation: 30/30 unit tests passed in 1.90s.
- Next step: stage, commit, tag `v3.0.0a1`, and push to GitHub `origin/main`.


### 2026-10-27 18:22 (+05:30)

- Completed end-to-end live task workflow, non-native tool fallback, and reference application suite:
  - Reference Inventory Application in `examples/inventory_app/`:
    - SQLite-backed offline storage with automatic schema migrations, SKU upsert, low-stock threshold queries, and deletion.
    - Full pytest suite in `examples/inventory_app/test_inventory.py` (4 tests passing).
  - Non-Native Tool Calling Fallback in `src/tael/models/client.py`:
    - Detected and handled Ollama HTTP 400 error when models like `granite-code:3b` lack native tool calling metadata.
    - Implemented automatic retry without `tools` payload parameter and added text-based tool extraction fallback.
  - End-to-End Programmatic Demo in `examples/demo_workflow.py`:
    - Exercises all 5 core subsystems: resource profiling, SQLite FTS5 BM25 memory retrieval, Git snapshot checkpoints, live Granite local inference, and subprocess profiling via `ProfileCommandTool`.
  - Added unit test `tests/test_examples.py` (total 31 unit tests passing in 2.0s).
- Validation: all 31 tests passing (`pytest`). Live `examples/demo_workflow.py` ran end-to-end on real hardware and completed with exit code 0.
- Next step: stage, commit, and push changes to GitHub `origin/main`.


### 2026-10-28 11:20 (+05:30)

- Hardened local memory reclamation, model eviction, and terminal demo workflow:
  - Diagnosed and resolved terminal demo issues in `examples/demo_workflow.py`:
    - Resolved `KeyError: 'status'` by returning `"status": "completed"` in `TaskOrchestrator.execute_task` and using safe `.get("status", "completed")` in caller scripts.
    - Added comprehensive tool aliases in `ToolRegistry` (`list_files` -> `list_dir`, `run_command` -> `execute_command`, `exec` -> `execute_command`, `search` -> `search_files`) so local models invoking common alternate tool names execute reliably without failures.
    - Prevented duplicate memory entries on repeated runs of `demo_workflow.py` by checking existing titles before insertion.
    - Scoped `SnapshotManager` in the demo to `examples/inventory_app` to keep root repository git commit history clean.
  - Eliminated lingering background `llama.cpp` runner (`llama-server.exe`) to reclaim RAM on 8GB/16GB machines:
    - Added `unload_model()` and `list_loaded_models()` to `ModelRuntimeManager` in `src/tael/models/runtime.py` leveraging Ollama's `keep_alive: 0` eviction protocol.
    - Integrated automatic model eviction on server shutdown via FastAPI `lifespan` context manager in `src/tael/api/server.py`.
    - Added `POST /model/unload` and `GET /model/loaded` API endpoints with interactive "Free RAM (Unload Model)" button in the Web Studio header.
    - Added `tael unload` CLI command for instant one-line RAM reclamation.
    - Wrapped `cmd_server()`, `cmd_chat()`, and `demo_workflow.py` in `finally:` blocks that automatically call `runtime.unload_model()`.
    - Verified via Windows `Win32_Process` query that `llama-server.exe` is cleanly terminated with zero lingering background memory footprint.
  - Test suite enhancements in `tests/test_api.py`:
    - Added test assertions for `/model/loaded` and `/model/unload`.
    - Optimized SSE streaming generator to use non-blocking `event_queue.get_nowait()` and `asyncio.sleep(0.05)` yielding prompt responses.
- Validation: 31/31 unit & integration tests passed in 1.86s. `tael doctor` passed all 6/6 diagnostics (`PASS`). Live `examples/demo_workflow.py` ran to completion with exit code 0 and confirmed zero lingering `llama.cpp` runner.
- Next step: stage, commit, and push updates to GitHub remote `origin/main`.


### 2026-10-28 12:30 (+05:30)

- Addressed standalone binary test feedback, Granite 3B tool calling, release packaging, and documentation:
  - Fixed Standalone Executable File Creation in CLI & Web Studio:
    - Root cause 1: `format_tools_prompt()` lacked few-shot demonstrations for small local models like IBM Granite 3B, causing it to respond conversationally rather than generating `<tool_call>` JSON.
    - Root cause 2: `json.loads()` failed with `JSONDecodeError: Invalid control character` when models produced multiline text without strict JSON escaping. Added `strict=False` and regex whitespace sanitization in `src/tael/models/client.py`.
    - Root cause 3: Added automatic fallback `_extract_implicit_file_action()` in `src/tael/core/orchestrator.py` that parses markdown/code blocks when user prompt requests file creation, synthesizing a `write_file` tool invocation if model omits the `<tool_call>` wrapper.
    - Root cause 4: Added tool call deduplication in `execute_task()` to prevent repetitive execution loops.
    - Verified in external test folder `D:\zzz`: `tael-windows-x64.exe chat "create a .md file and write about Agentic AI"` successfully created `D:\zzz\agentic_ai.md` (1,087 bytes) and `D:\zzz\quantum_computing.md` (505 bytes).
  - Enhanced Release Packaging & GitHub Workflow:
    - Updated `scripts/release.ps1` and `.github/workflows/release.yml` to package and publish both `tael.exe` and `tael-windows-x64.exe` aliases alongside `tael-ai-3.0.0.vsix` and `SHA256SUMS.txt`.
    - Added `launch_studio.bat` in the repository root for one-click double-click launch on Windows.
  - Documentation and Attribution Updates:
    - Added comprehensive `CONTRIBUTING.md` covering architecture, setup, testing, code style, and step-by-step instructions for adding custom tools.
    - Updated `README.md` and `docs/QUICKSTART.md` correcting commands to `.\tael-windows-x64.exe server` (or rename to `tael.exe`), documenting `tael unload`, and adding developer attribution:
      ```markdown
      ## Developer
      **Siddardha Shayini**
      GitHub: https://github.com/SiddardhaShayini
      ```
  - Validation: 31/31 unit & integration tests passing (`pytest`). Recompiled standalone binary `dist/tael.exe` (19.07 MB) and release package tested successfully in `D:\zzz`.
  - Next step: commit, tag `v3.0.0`, and push to GitHub `origin/main`.
