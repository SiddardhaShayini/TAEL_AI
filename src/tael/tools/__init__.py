from typing import Any, Dict, Optional
from tael.tools.base import BaseTool, ToolResult
from tael.tools.registry import ToolRegistry
from tael.tools.workspace import (
    ReadFileTool,
    WriteFileTool,
    ListDirTool,
    SearchFilesTool,
    CreateCheckpointTool,
    RollbackWorkspaceTool,
)
from tael.tools.git_tools import GitStatusTool, GitDiffTool, GitLogTool
from tael.tools.execution import ExecuteCommandTool
from tael.tools.system_info import SystemInfoTool
from tael.tools.desktop import LaunchAppTool, OpenUrlTool
from tael.tools.profiler import ProfileCommandTool, CompareBenchmarksTool
from tael.policy.approval import ApprovalManager
from tael.policy.audit import AuditLogger


def create_default_registry(
    approval_manager: ApprovalManager = None,
    audit_logger: AuditLogger = None,
    search_provider=None,
    page_reader=None,
    mcp_servers: Optional[Dict[str, Any]] = None,
) -> ToolRegistry:
    """Create and populate a ToolRegistry with all standard workspace, git, execution, desktop, profiling, research, and configured MCP tools."""
    # Lazy import to avoid circular dependency with tael.research
    from tael.research.tools import SearchWebTool, FetchPageTool

    registry = ToolRegistry(approval_manager=approval_manager, audit_logger=audit_logger)
    
    # Workspace & inspection tools
    registry.register(ReadFileTool())
    registry.register(WriteFileTool())
    registry.register(ListDirTool())
    registry.register(SearchFilesTool())
    registry.register(CreateCheckpointTool())
    registry.register(RollbackWorkspaceTool())
    registry.register(GitStatusTool())
    registry.register(GitDiffTool())
    registry.register(GitLogTool())
    registry.register(ExecuteCommandTool())
    registry.register(SystemInfoTool())

    # Desktop assistance tools
    registry.register(LaunchAppTool())
    registry.register(OpenUrlTool())

    # Profiling & optimization tools
    registry.register(ProfileCommandTool())
    registry.register(CompareBenchmarksTool())

    # Coding & refactoring tools
    from tael.coding.tool import AiderCodingTool
    registry.register(AiderCodingTool())

    # Research tools
    registry.register(SearchWebTool(provider=search_provider))
    registry.register(FetchPageTool(reader=page_reader))

    # Configured external stdio MCP servers
    if mcp_servers:
        from tael.connectors.mcp import MCPClient, MCPToolAdapter
        for s_name, s_cfg in mcp_servers.items():
            is_enabled = getattr(s_cfg, "enabled", True) if hasattr(s_cfg, "enabled") else s_cfg.get("enabled", True)
            cmd = getattr(s_cfg, "command", None) if hasattr(s_cfg, "command") else s_cfg.get("command")
            if is_enabled and cmd:
                try:
                    client = MCPClient(command=cmd, server_name=s_name)
                    client.start()
                    for t_def in client.list_tools():
                        adapter = MCPToolAdapter(client, t_def)
                        registry.register(adapter)
                except Exception as e:
                    if audit_logger:
                        audit_logger.log_event("mcp_server_connect_error", {"server": s_name, "error": str(e)})

    return registry


__all__ = [
    "BaseTool",
    "ToolResult",
    "ToolRegistry",
    "ReadFileTool",
    "WriteFileTool",
    "ListDirTool",
    "SearchFilesTool",
    "CreateCheckpointTool",
    "RollbackWorkspaceTool",
    "GitStatusTool",
    "GitDiffTool",
    "GitLogTool",
    "ExecuteCommandTool",
    "SystemInfoTool",
    "LaunchAppTool",
    "OpenUrlTool",
    "ProfileCommandTool",
    "CompareBenchmarksTool",
    "create_default_registry",
]
