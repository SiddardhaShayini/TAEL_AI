import platform
import sys
from typing import Any, Dict
from tael.tools.base import BaseTool, ToolResult
from tael.policy.permissions import PermissionLevel
from tael.resources.monitor import ResourceMonitor


class SystemInfoTool(BaseTool):
    name = "get_system_info"
    description = "Retrieve current system hardware, OS, Python environment, and resource utilization."
    permission = PermissionLevel.READ_WORKSPACE
    parameters_schema = {
        "type": "object",
        "properties": {},
    }

    def __init__(self, monitor: ResourceMonitor = None):
        self.monitor = monitor or ResourceMonitor()

    def run(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            snapshot = self.monitor.sample()
            info = {
                "os": platform.system(),
                "os_release": platform.release(),
                "machine": platform.machine(),
                "python_version": sys.version.split()[0],
                "total_ram_gb": snapshot.total_ram_gb,
                "available_ram_gb": snapshot.available_ram_gb,
                "ram_usage_percent": snapshot.ram_percent,
                "process_rss_mb": snapshot.process_rss_mb,
                "cpu_percent": snapshot.cpu_percent,
                "cpu_cores_physical": snapshot.cpu_count_physical,
                "cpu_cores_logical": snapshot.cpu_count_logical,
                "active_profile": snapshot.active_profile,
                "is_under_pressure": snapshot.is_under_pressure,
                "pressure_reason": snapshot.pressure_reason,
            }
            return ToolResult(success=True, data=info)
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Failed to sample system info: {str(e)}")
