from dataclasses import dataclass
from typing import Literal


@dataclass
class ResourceProfile:
    name: Literal["conservative", "balanced"]
    description: str
    max_context_tokens: int
    max_output_tokens: int
    max_cpu_threads: int
    allow_parallel_tools: bool
    max_subprocess_memory_mb: int
    max_tool_timeout_seconds: float
    min_free_ram_gb: float
    max_ram_percent: float


CONSERVATIVE_PROFILE = ResourceProfile(
    name="conservative",
    description="Conservative profile optimized for 8GB RAM CPU-only laptops.",
    max_context_tokens=4096,
    max_output_tokens=1024,
    max_cpu_threads=4,
    allow_parallel_tools=False,
    max_subprocess_memory_mb=1024,
    max_tool_timeout_seconds=60.0,
    min_free_ram_gb=1.5,
    max_ram_percent=85.0,
)

BALANCED_PROFILE = ResourceProfile(
    name="balanced",
    description="Balanced profile for 16GB+ RAM workstations and laptops.",
    max_context_tokens=8192,
    max_output_tokens=2048,
    max_cpu_threads=8,
    allow_parallel_tools=True,
    max_subprocess_memory_mb=2048,
    max_tool_timeout_seconds=120.0,
    min_free_ram_gb=2.5,
    max_ram_percent=90.0,
)


def select_profile(requested_profile: str, total_ram_gb: float) -> ResourceProfile:
    """Select appropriate resource profile based on configuration or detected hardware."""
    if requested_profile == "conservative":
        return CONSERVATIVE_PROFILE
    elif requested_profile == "balanced":
        return BALANCED_PROFILE
    else:  # auto
        if total_ram_gb <= 10.0:
            return CONSERVATIVE_PROFILE
        return BALANCED_PROFILE
