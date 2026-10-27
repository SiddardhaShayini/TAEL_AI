import time
import traceback
from typing import Any, Dict, List, Optional
from tael.tools.base import BaseTool, ToolResult
from tael.policy.approval import ApprovalManager
from tael.policy.audit import AuditLogger
from tael.policy.permissions import WorkspaceConfinementError


def validate_schema(schema: Dict[str, Any], data: Dict[str, Any]) -> Optional[str]:
    """Validate data dictionary against a simplified JSON schema."""
    if not isinstance(data, dict):
        return f"Arguments must be a JSON object, got {type(data).__name__}"

    required = schema.get("required", [])
    for field in required:
        if field not in data:
            return f"Missing required parameter '{field}'"

    properties = schema.get("properties", {})
    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
    }

    for key, val in data.items():
        if key in properties:
            expected_type = properties[key].get("type")
            if expected_type and expected_type in type_map:
                valid_types = type_map[expected_type]
                # Special case: bool is subclass of int in Python
                if expected_type in ("integer", "number") and isinstance(val, bool):
                    return f"Parameter '{key}' expected {expected_type}, got boolean"
                if not isinstance(val, valid_types):
                    return f"Parameter '{key}' expected {expected_type}, got {type(val).__name__}"

    return None


class ToolRegistry:
    def __init__(
        self,
        approval_manager: Optional[ApprovalManager] = None,
        audit_logger: Optional[AuditLogger] = None,
    ):
        self._tools: Dict[str, BaseTool] = {}
        self.approval_manager = approval_manager
        self.audit_logger = audit_logger

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        return list(self._tools.values())

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Return list of tool descriptions and schemas for LLM prompts or function calling."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "permission": tool.permission.value,
                "parameters": tool.parameters_schema,
            }
            for tool in self._tools.values()
        ]

    def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        """Validate, check approval, execute tool, record audit, and return result."""
        tool = self._tools.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool '{tool_name}' is not registered.",
            )

        context = context or {}
        start_time = time.time()

        # 1. Schema validation
        schema_err = validate_schema(tool.parameters_schema, arguments)
        if schema_err:
            if self.audit_logger:
                self.audit_logger.record(
                    tool_name=tool.name,
                    permission=tool.permission.value,
                    arguments=arguments,
                    approved=False,
                    success=False,
                    error_message=schema_err,
                )
            return ToolResult(success=False, data=None, error=f"Invalid arguments: {schema_err}")

        # 2. Permission / Approval check
        approved = True
        if self.approval_manager:
            decision = self.approval_manager.request_approval(
                tool_name=tool.name,
                permission=tool.permission,
                arguments=arguments,
            )
            if not decision.granted:
                duration_ms = (time.time() - start_time) * 1000
                if self.audit_logger:
                    self.audit_logger.record(
                        tool_name=tool.name,
                        permission=tool.permission.value,
                        arguments=arguments,
                        approved=False,
                        success=False,
                        error_message=decision.reason,
                        duration_ms=duration_ms,
                    )
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Permission denied: {decision.reason}",
                )

        # 3. Tool Execution
        try:
            result = tool.run(arguments, context)
            duration_ms = (time.time() - start_time) * 1000
            if self.audit_logger:
                self.audit_logger.record(
                    tool_name=tool.name,
                    permission=tool.permission.value,
                    arguments=arguments,
                    approved=True,
                    success=result.success,
                    error_message=result.error,
                    duration_ms=duration_ms,
                )
            return result
        except WorkspaceConfinementError as e:
            duration_ms = (time.time() - start_time) * 1000
            err_msg = str(e)
            if self.audit_logger:
                self.audit_logger.record(
                    tool_name=tool.name,
                    permission=tool.permission.value,
                    arguments=arguments,
                    approved=True,
                    success=False,
                    error_message=err_msg,
                    duration_ms=duration_ms,
                )
            return ToolResult(success=False, data=None, error=f"Security violation: {err_msg}")
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            err_msg = f"Execution error in '{tool_name}': {str(e)}"
            if self.audit_logger:
                self.audit_logger.record(
                    tool_name=tool.name,
                    permission=tool.permission.value,
                    arguments=arguments,
                    approved=True,
                    success=False,
                    error_message=err_msg,
                    duration_ms=duration_ms,
                )
            return ToolResult(success=False, data=None, error=err_msg)
