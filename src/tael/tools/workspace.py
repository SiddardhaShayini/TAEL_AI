from pathlib import Path
from typing import Any, Dict, List
import fnmatch
import os
import re

from tael.tools.base import BaseTool, ToolResult
from tael.policy.permissions import PermissionLevel, validate_workspace_path


IGNORED_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".pytest_cache", ".tael"}


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read lines from a file within the workspace with optional line offset and limit."
    permission = PermissionLevel.READ_WORKSPACE
    parameters_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative path to the file within the workspace."},
            "offset": {"type": "integer", "description": "1-based starting line number (default 1)."},
            "limit": {"type": "integer", "description": "Maximum number of lines to read (default 500)."},
        },
        "required": ["path"],
    }

    def run(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        ws_root = context.get("workspace_root", os.getcwd())
        target_path = validate_workspace_path(arguments["path"], ws_root)

        if not target_path.exists():
            return ToolResult(success=False, data=None, error=f"File not found: {arguments['path']}")
        if not target_path.is_file():
            return ToolResult(success=False, data=None, error=f"Path is not a regular file: {arguments['path']}")

        offset = max(1, arguments.get("offset", 1))
        limit = min(2000, max(1, arguments.get("limit", 500)))

        try:
            with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                all_lines = f.readlines()

            total_lines = len(all_lines)
            start_idx = offset - 1
            end_idx = min(start_idx + limit, total_lines)

            if start_idx >= total_lines:
                return ToolResult(
                    success=True,
                    data={"lines": [], "total_lines": total_lines, "offset": offset, "limit": limit},
                    truncated=False,
                )

            selected_lines = [
                f"{i + 1:4d} | {all_lines[i]}"
                for i in range(start_idx, end_idx)
            ]
            truncated = end_idx < total_lines

            return ToolResult(
                success=True,
                data={
                    "path": str(target_path.relative_to(Path(ws_root))),
                    "content": "".join(selected_lines),
                    "start_line": offset,
                    "end_line": end_idx,
                    "total_lines": total_lines,
                },
                truncated=truncated,
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Failed to read file: {str(e)}")


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Write content to a file within the workspace. Creates parent directories automatically."
    permission = PermissionLevel.WRITE_WORKSPACE
    parameters_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative path to the file within the workspace."},
            "content": {"type": "string", "description": "Text content to write."},
            "overwrite": {"type": "boolean", "description": "Whether to overwrite existing file (default True)."},
        },
        "required": ["path", "content"],
    }

    def run(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        ws_root = context.get("workspace_root", os.getcwd())
        target_path = validate_workspace_path(arguments["path"], ws_root)
        overwrite = arguments.get("overwrite", True)

        if target_path.exists() and not overwrite:
            return ToolResult(
                success=False,
                data=None,
                error=f"File already exists and overwrite is set to False: {arguments['path']}",
            )

        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(arguments["content"])

            rel_path = str(target_path.relative_to(Path(ws_root)))
            bytes_written = len(arguments["content"].encode("utf-8"))
            return ToolResult(
                success=True,
                data={
                    "path": rel_path,
                    "bytes_written": bytes_written,
                    "message": f"Successfully wrote {bytes_written} bytes to {rel_path}",
                },
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Failed to write file: {str(e)}")


class ListDirTool(BaseTool):
    name = "list_dir"
    description = "List files and directories in a workspace directory."
    permission = PermissionLevel.READ_WORKSPACE
    parameters_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative path to directory (default '.')."},
            "max_depth": {"type": "integer", "description": "Max directory depth to traverse (default 2, max 5)."},
        },
    }

    def run(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        ws_root = context.get("workspace_root", os.getcwd())
        subpath = arguments.get("path", ".")
        target_dir = validate_workspace_path(subpath, ws_root)

        if not target_dir.exists():
            return ToolResult(success=False, data=None, error=f"Directory not found: {subpath}")
        if not target_dir.is_dir():
            return ToolResult(success=False, data=None, error=f"Path is not a directory: {subpath}")

        max_depth = min(5, max(1, arguments.get("max_depth", 2)))
        entries = []
        base_depth = len(target_dir.parts)

        for root, dirs, files in os.walk(target_dir):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
            current_depth = len(Path(root).parts) - base_depth
            if current_depth >= max_depth:
                dirs.clear()

            rel_root = Path(root).relative_to(Path(ws_root))
            for f in files:
                if f.startswith("."):
                    continue
                file_path = Path(root) / f
                try:
                    size = file_path.stat().st_size
                    entries.append({
                        "path": str(rel_root / f).replace("\\", "/"),
                        "type": "file",
                        "size_bytes": size,
                    })
                except Exception:
                    pass

            for d in dirs:
                entries.append({
                    "path": str(rel_root / d).replace("\\", "/"),
                    "type": "directory",
                })

            if len(entries) >= 300:
                break

        return ToolResult(
            success=True,
            data={"entries": entries[:300], "total_count": len(entries)},
            truncated=len(entries) > 300,
        )


class SearchFilesTool(BaseTool):
    name = "search_files"
    description = "Search for a regex or text pattern across text files in the workspace."
    permission = PermissionLevel.READ_WORKSPACE
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search string or regex pattern."},
            "file_pattern": {"type": "string", "description": "File glob filter, e.g. '*.py' (default '*')."},
            "max_results": {"type": "integer", "description": "Max matching lines to return (default 50)."},
        },
        "required": ["query"],
    }

    def run(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        ws_root = Path(context.get("workspace_root", os.getcwd()))
        query_str = arguments["query"]
        file_pat = arguments.get("file_pattern", "*")
        max_results = min(200, max(1, arguments.get("max_results", 50)))

        try:
            pattern = re.compile(query_str, re.IGNORECASE)
        except re.error as e:
            return ToolResult(success=False, data=None, error=f"Invalid regex query: {str(e)}")

        results = []
        for root, dirs, files in os.walk(ws_root):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
            for f in files:
                if not fnmatch.fnmatch(f, file_pat):
                    continue
                file_path = Path(root) / f
                try:
                    rel_path = str(file_path.relative_to(ws_root)).replace("\\", "/")
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as fp:
                        for line_no, line in enumerate(fp, start=1):
                            if pattern.search(line):
                                results.append({
                                    "file": rel_path,
                                    "line": line_no,
                                    "text": line.strip()[:200],
                                })
                                if len(results) >= max_results:
                                    break
                except Exception:
                    continue
                if len(results) >= max_results:
                    break
            if len(results) >= max_results:
                break

        return ToolResult(
            success=True,
            data={"matches": results, "count": len(results)},
            truncated=len(results) >= max_results,
        )
