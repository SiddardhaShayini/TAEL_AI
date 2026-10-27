from typing import Any, Dict, List, Optional
from tael.policy.permissions import PermissionLevel
from tael.tools.base import BaseTool, ToolResult
from tael.coding.aider_bridge import AiderBridge


class AiderCodingTool(BaseTool):
    """Tool allowing TAEL orchestrator to delegate multi-file editing to Aider."""

    name = "aider_edit"
    description = "Delegate focused multi-file coding, editing, or refactoring tasks to Aider with local model guidance."
    permission = PermissionLevel.WRITE_WORKSPACE
    parameters_schema = {
        "type": "object",
        "properties": {
            "instruction": {
                "type": "string",
                "description": "Natural-language coding instruction or refactoring prompt.",
            },
            "files": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional list of target workspace file paths to modify.",
            },
        },
        "required": ["instruction"],
    }

    def __init__(self, model_name: str = "granite-code:3b", endpoint: str = "http://127.0.0.1:11434"):
        self.model_name = model_name
        self.endpoint = endpoint

    def run(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        workspace_root = context.get("workspace_root", ".")
        instruction = arguments.get("instruction", "")
        files = arguments.get("files") or []

        bridge = AiderBridge(
            workspace_root=workspace_root,
            model_name=self.model_name,
            endpoint=self.endpoint,
        )

        res = bridge.run_coding_task(
            instruction=instruction,
            files=files,
            auto_commit=False,
        )

        if not res.get("success"):
            return ToolResult(success=False, error=res.get("error", "Aider execution failed"), data=res)
        return ToolResult(success=True, data=res)
