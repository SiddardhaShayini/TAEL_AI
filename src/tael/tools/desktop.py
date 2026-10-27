import os
import shutil
import subprocess
import webbrowser
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from tael.tools.base import BaseTool, ToolResult
from tael.policy.permissions import PermissionLevel


APPROVED_APPLICATIONS = {
    "notepad": {
        "display_name": "Notepad",
        "command_windows": ["notepad.exe"],
        "command_posix": ["nano"],
    },
    "vscode": {
        "display_name": "Visual Studio Code",
        "command_windows": ["code"],
        "command_posix": ["code"],
    },
    "terminal": {
        "display_name": "Terminal",
        "command_windows": ["powershell.exe"],
        "command_posix": ["x-terminal-emulator", "bash"],
    },
    "calc": {
        "display_name": "Calculator",
        "command_windows": ["calc.exe"],
        "command_posix": ["gnome-calculator"],
    },
}


class LaunchAppTool(BaseTool):
    name = "launch_application"
    description = (
        "Launch an approved desktop application (e.g. 'notepad', 'vscode', 'terminal', 'calc') "
        "with optional file argument. Requires explicit user approval."
    )
    permission = PermissionLevel.APP_LAUNCH
    parameters_schema = {
        "type": "object",
        "properties": {
            "app_name": {
                "type": "string",
                "description": f"Name of the approved application to launch. Allowed: {list(APPROVED_APPLICATIONS.keys())}",
            },
            "file_path": {
                "type": "string",
                "description": "Optional file path to open in the target application.",
            },
        },
        "required": ["app_name"],
    }

    def run(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        app_key = arguments["app_name"].lower().strip()
        if app_key not in APPROVED_APPLICATIONS:
            return ToolResult(
                success=False,
                data=None,
                error=(
                    f"Application '{app_key}' is not in the approved applications allowlist. "
                    f"Allowed applications: {list(APPROVED_APPLICATIONS.keys())}."
                ),
            )

        app_info = APPROVED_APPLICATIONS[app_key]
        cmd_candidates = (
            app_info["command_windows"] if os.name == "nt" else app_info["command_posix"]
        )

        target_bin = cmd_candidates[0]
        # Resolve path if file argument provided
        target_file = arguments.get("file_path")
        cmd = [target_bin]
        if target_file:
            ws_root = context.get("workspace_root", os.getcwd())
            from tael.policy.permissions import validate_workspace_path
            resolved_file = str(validate_workspace_path(target_file, ws_root))
            cmd.append(resolved_file)

        try:
            # Spawn non-blocking background process
            subprocess.Popen(
                cmd,
                shell=(os.name == "nt" and target_bin.endswith(".exe")),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return ToolResult(
                success=True,
                data={
                    "app": app_info["display_name"],
                    "launched": True,
                    "target_file": target_file,
                    "message": f"Successfully launched {app_info['display_name']}.",
                },
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to launch application '{app_info['display_name']}': {str(e)}",
            )


class OpenUrlTool(BaseTool):
    name = "open_url"
    description = "Open an approved http/https web link in the system's default browser."
    permission = PermissionLevel.APP_LAUNCH
    parameters_schema = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Web URL starting with http:// or https://."},
        },
        "required": ["url"],
    }

    def run(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        url = arguments["url"].strip()
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return ToolResult(
                success=False,
                data=None,
                error=f"Invalid URL '{url}'. Must start with http:// or https://.",
            )

        try:
            # Open URL in browser
            opened = webbrowser.open(url)
            return ToolResult(
                success=True,
                data={
                    "url": url,
                    "opened": opened,
                    "message": f"Requested system browser to open {url}",
                },
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Failed to open URL: {str(e)}")
