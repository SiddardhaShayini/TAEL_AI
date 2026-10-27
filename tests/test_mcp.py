from typing import Any, Dict
from tael.connectors.mcp import MCPToolAdapter, MCPClient
from tael.policy.permissions import PermissionLevel


class DummyMCPClient:
    def __init__(self, server_name: str = "mock_server"):
        self.server_name = server_name
        self.calls = []

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        self.calls.append({"name": name, "arguments": arguments})
        if name == "echo":
            return {"content": [{"type": "text", "text": f"Echo: {arguments.get('message')}"}]}
        return {"isError": True, "content": [{"type": "text", "text": f"Unknown tool {name}"}]}


def test_mcp_tool_adapter():
    client = DummyMCPClient(server_name="test_service")
    tool_def = {
        "name": "echo",
        "description": "Echo back a message",
        "inputSchema": {
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        },
    }

    adapter = MCPToolAdapter(client, tool_def, permission=PermissionLevel.EXTERNAL_SIDE_EFFECT)
    assert adapter.name == "test_service__echo"
    assert adapter.description == "Echo back a message"
    assert adapter.permission == PermissionLevel.EXTERNAL_SIDE_EFFECT

    # Execute
    res = adapter.run({"message": "Hello from TAEL!"}, {})
    assert res.success is True
    assert res.data == "Echo: Hello from TAEL!"
    assert len(client.calls) == 1
    assert client.calls[0]["arguments"]["message"] == "Hello from TAEL!"
