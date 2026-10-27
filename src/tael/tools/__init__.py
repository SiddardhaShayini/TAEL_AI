from tael.tools.base import BaseTool, ToolResult
from tael.tools.registry import ToolRegistry
from tael.tools.workspace import ReadFileTool, WriteFileTool, ListDirTool, SearchFilesTool
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
) -> ToolRegistry:
    """Create and populate a ToolRegistry with all standard workspace, git, execution, desktop, profiling, and research tools."""
    # Lazy import to avoid circular dependency with tael.research
    from tael.research.tools import SearchWebTool, FetchPageTool

    registry = ToolRegistry(approval_manager=approval_manager, audit_logger=audit_logger)
    
    # Workspace & inspection tools
    registry.register(ReadFileTool())
    registry.register(WriteFileTool())
    registry.register(ListDirTool())
    registry.register(SearchFilesTool())
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

    # Research tools
    registry.register(SearchWebTool(provider=search_provider))
    registry.register(FetchPageTool(reader=page_reader))

    return registry


__all__ = [
    "BaseTool",
    "ToolResult",
    "ToolRegistry",
    "ReadFileTool",
    "WriteFileTool",
    "ListDirTool",
    "SearchFilesTool",
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
