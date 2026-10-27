from tael.tools.base import BaseTool, ToolResult
from tael.tools.registry import ToolRegistry
from tael.tools.workspace import ReadFileTool, WriteFileTool, ListDirTool, SearchFilesTool
from tael.tools.git_tools import GitStatusTool, GitDiffTool, GitLogTool
from tael.tools.execution import ExecuteCommandTool
from tael.tools.system_info import SystemInfoTool
from tael.policy.approval import ApprovalManager
from tael.policy.audit import AuditLogger


def create_default_registry(
    approval_manager: ApprovalManager = None,
    audit_logger: AuditLogger = None,
) -> ToolRegistry:
    """Create and populate a ToolRegistry with all standard workspace, git, execution, and system tools."""
    registry = ToolRegistry(approval_manager=approval_manager, audit_logger=audit_logger)
    registry.register(ReadFileTool())
    registry.register(WriteFileTool())
    registry.register(ListDirTool())
    registry.register(SearchFilesTool())
    registry.register(GitStatusTool())
    registry.register(GitDiffTool())
    registry.register(GitLogTool())
    registry.register(ExecuteCommandTool())
    registry.register(SystemInfoTool())
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
    "create_default_registry",
]
