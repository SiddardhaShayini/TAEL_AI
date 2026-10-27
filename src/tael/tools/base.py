from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
from tael.policy.permissions import PermissionLevel


@dataclass
class ToolResult:
    success: bool
    data: Any
    error: Optional[str] = None
    truncated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "truncated": self.truncated,
        }


class BaseTool(ABC):
    name: str
    description: str
    permission: PermissionLevel
    parameters_schema: Dict[str, Any]
    default_timeout_seconds: float = 30.0

    @abstractmethod
    def run(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute the tool with given validated arguments and context."""
        pass
