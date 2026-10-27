from dataclasses import dataclass
from typing import Optional, Tuple
import os
import psutil

from tael.resources.profiles import ResourceProfile, select_profile


@dataclass
class ResourceSnapshot:
    total_ram_gb: float
    available_ram_gb: float
    ram_percent: float
    process_rss_mb: float
    cpu_percent: float
    cpu_count_logical: int
    cpu_count_physical: int
    is_under_pressure: bool
    pressure_reason: Optional[str]
    active_profile: str


class ResourceMonitor:
    def __init__(self, requested_profile: str = "auto"):
        self.requested_profile = requested_profile
        self._process = psutil.Process(os.getpid())
        # Initial hardware check
        vm = psutil.virtual_memory()
        total_ram_gb = vm.total / (1024 ** 3)
        self.profile: ResourceProfile = select_profile(requested_profile, total_ram_gb)

    def check_pressure(self) -> Tuple[bool, Optional[str]]:
        """Check if system is currently under memory or CPU pressure."""
        vm = psutil.virtual_memory()
        available_gb = vm.available / (1024 ** 3)
        percent = vm.percent

        if available_gb < self.profile.min_free_ram_gb:
            return (
                True,
                f"Available RAM ({available_gb:.2f} GB) is below safe minimum ({self.profile.min_free_ram_gb:.2f} GB)",
            )
        if percent > self.profile.max_ram_percent:
            return (
                True,
                f"RAM usage ({percent:.1f}%) exceeds safety ceiling ({self.profile.max_ram_percent:.1f}%)",
            )
        return False, None

    def sample(self) -> ResourceSnapshot:
        """Sample current hardware and process resource utilization."""
        vm = psutil.virtual_memory()
        total_ram_gb = vm.total / (1024 ** 3)
        available_ram_gb = vm.available / (1024 ** 3)
        ram_percent = vm.percent

        rss_mb = 0.0
        try:
            mem_info = self._process.memory_info()
            rss_mb = mem_info.rss / (1024 ** 2)
        except Exception:
            pass

        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_logical = psutil.cpu_count(logical=True) or 1
        cpu_physical = psutil.cpu_count(logical=False) or 1

        under_pressure, reason = self.check_pressure()

        return ResourceSnapshot(
            total_ram_gb=round(total_ram_gb, 2),
            available_ram_gb=round(available_ram_gb, 2),
            ram_percent=round(ram_percent, 1),
            process_rss_mb=round(rss_mb, 2),
            cpu_percent=round(cpu_percent, 1),
            cpu_count_logical=cpu_logical,
            cpu_count_physical=cpu_physical,
            is_under_pressure=under_pressure,
            pressure_reason=reason,
            active_profile=self.profile.name,
        )
