<p align="center">
  <img src="../assets/tael-logo-v3.svg" width="100" height="100" alt="TAEL AI Logo" />
</p>

# TAEL V3 — Technical Architecture

This document outlines the architecture, security model, and resource management strategies implemented in **TAEL V3** based on [PLAN.md](../PLAN.md).

---

## 1. High-Level Architecture

```text
               +-------------------------------------------+
               |        User Interfaces (CLI / API)        |
               +---------------------+---------------------+
                                     |
                                     v
               +-------------------------------------------+
               |             Task Orchestrator             |
               |   (Multi-turn loop, budgets, session)     |
               +---------+-------------------+-------------+
                         |                   |
            +------------v-----------+       |
            | Persistent Proj Memory |       |
            | (SQLite + FTS5 / BM25) |       |
            +------------------------+       |
                                             v
               +-------------------------------------------+
               |          Policy & Approval Service        |
               | (Confinement check, approval, redaction)  |
               +---------------------+---------------------+
                                     |
                                     v
               +-------------------------------------------+
               |            Typed Tool Registry            |
               |                                           |
               | • Workspace Tools (read, write, search)   |
               | • Git Tools (status, diff, log)           |
               | • Subprocess Execution (bounded, timeout) |
               | • Desktop Tools (launch_app, open_url)    |
               | • Research Tools (search_web, fetch_page) |
               | • Profiler (profile_command, compare)     |
               | • MCP Connector (stdio JSON-RPC adapter)  |
               +---------------------+---------------------+
                                     |
                        +------------+------------+
                        |                         |
                        v                         v
               +-----------------+       +-----------------+
               |   Aider Bridge  |       |  Model Runtime  |
               |  (Code Editing) |       | (Granite / 3B)  |
               +-----------------+       +-----------------+
```

---

## 2. Core Subsystems

### 2.1 Hardware-Aware Resource Supervisor (`src/tael/resources/`)
- Dynamically selects **Conservative Profile** (for laptops with <= 10GB RAM) or **Balanced Profile** (16GB+).
- Samples live RAM and CPU utilization before every agent turn.
- Emits backpressure warnings and throttling pauses if free memory drops below safe thresholds (1.5GB on 8GB machines).

### 2.2 In-Product Persistent Project Memory (`src/tael/memory/`)
- Isolates project memories per workspace in local SQLite databases (`.tael/memory/<project_id>.db`).
- SQLite FTS5 full-text indexing with BM25 ranking for sub-millisecond retrieval.
- Enforces hard token budgets (e.g. 1000 tokens) at task start to prevent context window exhaustion on 8GB laptops.
- Supports superseding outdated entries, categorizing facts/decisions/pitfalls, and Markdown export/import.

### 2.3 Policy & Approval Engine (`src/tael/policy/`)
- **Workspace Confinement:** All file paths are strictly canonicalized against `workspace_root`. Traversal attacks (`../`) and out-of-workspace symlinks are caught with `WorkspaceConfinementError`.
- **Capability Approval:** The model cannot grant itself permissions. Actions requiring writes, execution, network, or desktop launches trigger interactive confirmation.
- **Audit Logging:** Continuous JSONL logging with regex-based credential and bearer token redaction.

### 2.4 Research & Untrusted Content Isolation (`src/tael/research/`)
- Fetches web pages under a 60KB ceiling and converts HTML to plain text.
- Strips `<script>`, `<style>`, and `<svg>`.
- Wraps retrieved external content with `=== [UNTRUSTED EXTERNAL WEB CONTENT] ===` security banners so LLMs never execute instructions contained inside web pages.

### 2.5 Extensible MCP Connector (`src/tael/connectors/mcp.py`)
- Communicates with external MCP servers via JSON-RPC 2.0 stdio protocol.
- Automatically maps discovered tools into typed `BaseTool` schemas with safety boundaries.
