import pytest
from pathlib import Path
from tael.coding.aider_bridge import AiderBridge
from tael.coding.tool import AiderCodingTool
from tael.policy.permissions import PermissionLevel


def test_aider_bridge_availability(tmp_path: Path):
    bridge = AiderBridge(workspace_root=str(tmp_path))
    available = bridge.is_aider_available()
    assert isinstance(available, bool)


def test_aider_coding_tool_schema():
    tool = AiderCodingTool()
    assert tool.name == "aider_edit"
    assert tool.permission == PermissionLevel.WRITE_WORKSPACE
    assert "instruction" in tool.parameters_schema["required"]


def test_aider_tool_execution_graceful_fallback(tmp_path: Path):
    tool = AiderCodingTool()
    res = tool.run({"instruction": "Refactor helper.py"}, {"workspace_root": str(tmp_path)})
    if not tool.run({"instruction": "test"}, {"workspace_root": str(tmp_path)}).success:
        assert res.success is False
        assert "Aider is not installed" in res.error or "Failed to execute" in res.error
