import os
import subprocess
import time
from typing import Any, Dict
from tael.tools.base import BaseTool, ToolResult
from tael.policy.permissions import PermissionLevel


MAX_OUTPUT_CHARS = 30000


class ExecuteCommandTool(BaseTool):
    name = "execute_command"
    description = "Run a shell command within the workspace directory with timeout and output bounds."
    permission = PermissionLevel.EXECUTE_COMMAND
    parameters_schema = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Shell command to execute."},
            "timeout_seconds": {"type": "number", "description": "Execution timeout in seconds (default 30, max 180)."},
        },
        "required": ["command"],
    }

    def run(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        cwd = context.get("workspace_root", os.getcwd())
        cmd = arguments["command"]
        timeout = min(180.0, max(1.0, float(arguments.get("timeout_seconds", 30.0))))

        start_time = time.time()
        try:
            # Use powershell on Windows, /bin/sh or bash on Linux/macOS
            is_windows = os.name == "nt"
            shell_cmd = ["powershell.exe", "-Command", cmd] if is_windows else ["/bin/sh", "-c", cmd]

            proc = subprocess.run(
                shell_cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            duration = time.time() - start_time
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""

            truncated = (len(stdout) + len(stderr)) > MAX_OUTPUT_CHARS
            if truncated:
                stdout = stdout[:MAX_OUTPUT_CHARS]
                stderr = stderr[:10000]

            return ToolResult(
                success=(proc.returncode == 0),
                data={
                    "command": cmd,
                    "exit_code": proc.returncode,
                    "stdout": stdout,
                    "stderr": stderr,
                    "duration_seconds": round(duration, 2),
                },
                error=None if proc.returncode == 0 else f"Command exited with code {proc.returncode}",
                truncated=truncated,
            )
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return ToolResult(
                success=False,
                data={"command": cmd, "duration_seconds": round(duration, 2)},
                error=f"Command timed out after {timeout} seconds",
            )
        except Exception as e:
            return ToolResult(success=False, data={"command": cmd}, error=f"Command execution failed: {str(e)}")
