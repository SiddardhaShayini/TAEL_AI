# TAEL V3 — Model Context Protocol (MCP) Integration Guide

TAEL V3 includes built-in support for the open **Model Context Protocol (MCP)** specification. This allows TAEL to connect directly to external stdio-based MCP servers and adapt their tools dynamically into TAEL's typed tool registry.

---

## How MCP Works in TAEL

TAEL implements a lightweight, native stdio JSON-RPC client (`MCPClient`) and a tool adapter (`MCPToolAdapter`) in `src/tael/connectors/mcp.py`.

```
┌─────────────┐        JSON-RPC (stdio)        ┌─────────────────────────┐
│   TAEL V3   │ ─────────────────────────────> │ External MCP Server     │
│ Orchestrator│ <───────────────────────────── │ (SQLite, Filesystem...) │
└─────────────┘       tools/list & tools/call  └─────────────────────────┘
```

1. **Auto-Discovery**: On startup, TAEL starts any enabled MCP servers listed in your `.tael/config.yaml`.
2. **Handshake**: TAEL negotiates capabilities via `initialize` and `notifications/initialized`.
3. **Dynamic Registration**: Tools returned by `tools/list` are prefixed (`<server_name>__<tool_name>`) and registered with schema validation.
4. **Sandboxed Execution**: Calls are routed to `tools/call` with timeout enforcement and audit logging.

---

## Configuring MCP Servers

You can configure external MCP servers in your workspace's `.tael/config.yaml`:

```yaml
mcp_servers:
  # Example 1: Local SQLite Explorer
  sqlite:
    command: ["uvx", "mcp-server-sqlite", "--db-path", "inventory.db"]
    enabled: true
    permission: "read_workspace"

  # Example 2: Filesystem Extension Server
  filesystem:
    command: ["npx", "-y", "@modelcontextprotocol/server-filesystem", "D:\\TAEL_AI_V3\\data"]
    enabled: false
    permission: "read_workspace"

  # Example 3: Custom Python Stdio Script
  my_tools:
    command: ["python", "scripts/custom_mcp_server.py"]
    enabled: true
    permission: "external_side_effect"
```

---

## Inspecting and Testing MCP Servers via CLI

TAEL provides the `tael mcp` command to inspect and test external servers:

### 1. List Configured Servers
```bash
tael mcp list
```

Example output:
```
                Configured External MCP Servers                 
┌─────────────┬─────────┬──────────────────────────────────────┐
│ Server Name │ Status  │ Command                              │
├─────────────┼─────────┼──────────────────────────────────────┤
│ sqlite      │ ENABLED │ uvx mcp-server-sqlite --db-path ...  │
└─────────────┴─────────┴──────────────────────────────────────┘
```

### 2. Test Connection and Discover Tools
```bash
tael mcp test sqlite
```

This starts the server, verifies the handshake, queries `tools/list`, displays the discovered tools and their descriptions, and cleanly terminates the process.

---

## Security & Policy Controls

External MCP tools run under TAEL's policy governance:
- **Permission Level**: By default, MCP tools require explicit confirmation (`EXTERNAL_SIDE_EFFECT`) or can be assigned to `READ_WORKSPACE` or `WRITE_WORKSPACE`.
- **Audit Logging**: Every MCP tool execution is recorded in `.tael/audit.log` with secrets automatically scrubbed.
- **Subprocess Isolation**: If an external server hangs or takes too long, TAEL enforces a timeout and cleans up the child process.
