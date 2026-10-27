import json
import subprocess
import time
from typing import Any, Dict, List, Optional

from tael.policy.permissions import PermissionLevel
from tael.tools.base import BaseTool, ToolResult


class MCPClientError(Exception):
    pass


class MCPClient:
    """Lightweight stdio-based MCP (Model Context Protocol) client."""

    def __init__(self, command: List[str], server_name: str = "mcp_server"):
        self.command = command
        self.server_name = server_name
        self._process: Optional[subprocess.Popen] = None
        self._request_id = 0

    def start(self) -> None:
        """Start the MCP server subprocess using stdio communication."""
        try:
            self._process = subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except Exception as e:
            raise MCPClientError(f"Failed to start MCP server '{self.server_name}': {str(e)}")

        # Send initialize request
        init_res = self._send_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "tael", "version": "3.0.0"},
            },
        )
        if "error" in init_res:
            raise MCPClientError(f"MCP server initialization failed: {init_res['error']}")

        # Send initialized notification
        self._send_notification("notifications/initialized", {})

    def stop(self) -> None:
        """Terminate the MCP server subprocess."""
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=3.0)
            except Exception:
                self._process.kill()
            finally:
                self._process = None

    def list_tools(self) -> List[Dict[str, Any]]:
        """Query the MCP server for available tools (tools/list)."""
        res = self._send_request("tools/list", {})
        if "error" in res:
            raise MCPClientError(f"tools/list failed: {res['error']}")
        result = res.get("result", {})
        return result.get("tools", [])

    def call_tool(self, name: str, arguments: Dict[str, Any], timeout_seconds: float = 30.0) -> Dict[str, Any]:
        """Invoke a tool on the MCP server (tools/call)."""
        res = self._send_request("tools/call", {"name": name, "arguments": arguments}, timeout_seconds=timeout_seconds)
        if "error" in res:
            return {"isError": True, "content": [{"type": "text", "text": str(res["error"])}]}
        return res.get("result", {})

    def _send_request(
        self, method: str, params: Dict[str, Any], timeout_seconds: float = 15.0
    ) -> Dict[str, Any]:
        if not self._process or not self._process.stdin or not self._process.stdout:
            raise MCPClientError("MCP server is not running.")

        self._request_id += 1
        req_id = self._request_id
        req_payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params,
        }

        try:
            req_line = json.dumps(req_payload) + "\n"
            self._process.stdin.write(req_line)
            self._process.stdin.flush()

            start_t = time.time()
            while time.time() - start_t < timeout_seconds:
                line = self._process.stdout.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                    if msg.get("id") == req_id:
                        return msg
                except json.JSONDecodeError:
                    continue

            return {"error": {"code": -32000, "message": f"Request {method} timed out after {timeout_seconds}s"}}
        except Exception as e:
            return {"error": {"code": -32603, "message": str(e)}}

    def _send_notification(self, method: str, params: Dict[str, Any]) -> None:
        if not self._process or not self._process.stdin:
            return
        payload = {"jsonrpc": "2.0", "method": method, "params": params}
        try:
            self._process.stdin.write(json.dumps(payload) + "\n")
            self._process.stdin.flush()
        except Exception:
            pass


class MCPToolAdapter(BaseTool):
    """Adapts an MCP remote tool definition into a standard TAEL BaseTool."""

    def __init__(
        self,
        mcp_client: MCPClient,
        tool_def: Dict[str, Any],
        permission: PermissionLevel = PermissionLevel.EXTERNAL_SIDE_EFFECT,
    ):
        self.mcp_client = mcp_client
        self.name = f"{mcp_client.server_name}__{tool_def['name']}"
        self.description = tool_def.get("description", f"MCP Tool from {mcp_client.server_name}")
        self.permission = permission
        self.parameters_schema = tool_def.get("inputSchema", {"type": "object", "properties": {}})
        self.raw_tool_name = tool_def["name"]

    def run(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            res = self.mcp_client.call_tool(self.raw_tool_name, arguments)
            is_error = res.get("isError", False)
            content_list = res.get("content", [])
            text_parts = [c.get("text", "") for c in content_list if c.get("type") == "text"]
            full_text = "\n".join(text_parts) if text_parts else str(res)

            truncated = len(full_text) > 15000
            output_text = full_text[:15000] if truncated else full_text

            if is_error:
                return ToolResult(success=False, data=None, error=output_text, truncated=truncated)
            return ToolResult(success=True, data=output_text, truncated=truncated)
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"MCP execution error: {str(e)}")
