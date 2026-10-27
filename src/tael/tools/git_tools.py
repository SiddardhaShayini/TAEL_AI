import subprocess
from pathlib import Path
from typing import Any, Dict
from tael.tools.base import BaseTool, ToolResult
from tael.policy.permissions import PermissionLevel


def _run_git_cmd(args: list[str], cwd: str) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=15.0,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Git command timed out after 15 seconds"
    except FileNotFoundError:
        return -1, "", "Git binary not found on system PATH"
    except Exception as e:
        return -1, "", str(e)


class GitStatusTool(BaseTool):
    name = "git_status"
    description = "Get the current git working tree status (branch, modified, staged, untracked files)."
    permission = PermissionLevel.READ_WORKSPACE
    parameters_schema = {
        "type": "object",
        "properties": {},
    }

    def run(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        cwd = context.get("workspace_root", ".")
        code, stdout, stderr = _run_git_cmd(["status", "--short", "--branch"], cwd)
        if code != 0:
            return ToolResult(success=False, data=None, error=stderr or "Failed to run git status")
        return ToolResult(success=True, data={"status": stdout.strip()})


class GitDiffTool(BaseTool):
    name = "git_diff"
    description = "View uncommitted git diffs in the workspace."
    permission = PermissionLevel.READ_WORKSPACE
    parameters_schema = {
        "type": "object",
        "properties": {
            "staged": {"type": "boolean", "description": "View staged changes if True (default False)."},
            "path": {"type": "string", "description": "Specific file path to diff (optional)."},
        },
    }

    def run(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        cwd = context.get("workspace_root", ".")
        cmd = ["diff"]
        if arguments.get("staged", False):
            cmd.append("--cached")
        if "path" in arguments and arguments["path"]:
            cmd.extend(["--", arguments["path"]])

        code, stdout, stderr = _run_git_cmd(cmd, cwd)
        if code != 0:
            return ToolResult(success=False, data=None, error=stderr or "Failed to run git diff")

        truncated = len(stdout) > 20000
        output_data = stdout[:20000] if truncated else stdout
        return ToolResult(
            success=True,
            data={"diff": output_data, "char_count": len(stdout)},
            truncated=truncated,
        )


class GitLogTool(BaseTool):
    name = "git_log"
    description = "View recent git commit logs."
    permission = PermissionLevel.READ_WORKSPACE
    parameters_schema = {
        "type": "object",
        "properties": {
            "max_count": {"type": "integer", "description": "Number of commits to retrieve (default 5, max 20)."},
        },
    }

    def run(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        cwd = context.get("workspace_root", ".")
        count = min(20, max(1, arguments.get("max_count", 5)))
        cmd = ["log", f"-n{count}", "--oneline", "--decorate"]
        code, stdout, stderr = _run_git_cmd(cmd, cwd)
        if code != 0:
            return ToolResult(success=False, data=None, error=stderr or "Failed to run git log")
        return ToolResult(success=True, data={"commits": stdout.strip().splitlines()})
