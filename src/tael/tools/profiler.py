import os
import subprocess
import time
from typing import Any, Dict, List, Optional
import psutil

from tael.policy.permissions import PermissionLevel
from tael.tools.base import BaseTool, ToolResult


class ProfileCommandTool(BaseTool):
    name = "profile_command"
    description = (
        "Execute a test or benchmark command under resource profiling. "
        "Measures execution time, peak memory usage (MB), CPU utilization, and exit status."
    )
    permission = PermissionLevel.EXECUTE_COMMAND
    parameters_schema = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Command or script to benchmark."},
            "timeout_seconds": {"type": "number", "description": "Execution timeout in seconds (default 30, max 120)."},
        },
        "required": ["command"],
    }

    def run(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        cwd = context.get("workspace_root", os.getcwd())
        cmd = arguments["command"]
        timeout = min(120.0, max(1.0, float(arguments.get("timeout_seconds", 30.0))))

        is_windows = os.name == "nt"
        shell_cmd = ["powershell.exe", "-Command", cmd] if is_windows else ["/bin/sh", "-c", cmd]

        start_time = time.perf_counter()
        peak_rss_mb = 0.0

        try:
            proc = subprocess.Popen(
                shell_cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Sample child process tree memory periodically
            try:
                ps_proc = psutil.Process(proc.pid)
                while proc.poll() is None:
                    try:
                        mem_info = ps_proc.memory_info()
                        current_rss = mem_info.rss / (1024 * 1024)
                        # Also check child processes
                        for child in ps_proc.children(recursive=True):
                            try:
                                current_rss += child.memory_info().rss / (1024 * 1024)
                            except Exception:
                                pass
                        if current_rss > peak_rss_mb:
                            peak_rss_mb = current_rss
                    except Exception:
                        pass
                    time.sleep(0.05)
                    if time.perf_counter() - start_time > timeout:
                        proc.kill()
                        return ToolResult(
                            success=False,
                            data={"command": cmd},
                            error=f"Benchmark timed out after {timeout} seconds",
                        )
            except Exception:
                pass

            stdout, stderr = proc.communicate(timeout=5.0)
            duration_ms = (time.perf_counter() - start_time) * 1000

            return ToolResult(
                success=(proc.returncode == 0),
                data={
                    "command": cmd,
                    "duration_ms": round(duration_ms, 2),
                    "peak_memory_mb": round(peak_rss_mb, 2),
                    "exit_code": proc.returncode,
                    "stdout_snippet": stdout.strip()[:1000] if stdout else "",
                    "stderr_snippet": stderr.strip()[:1000] if stderr else "",
                },
                error=None if proc.returncode == 0 else f"Command failed with exit code {proc.returncode}",
            )
        except Exception as e:
            return ToolResult(success=False, data={"command": cmd}, error=f"Profiling failed: {str(e)}")


class CompareBenchmarksTool(BaseTool):
    name = "compare_benchmarks"
    description = (
        "Compare baseline vs optimized benchmark measurements to compute speedup and memory delta."
    )
    permission = PermissionLevel.READ_WORKSPACE
    parameters_schema = {
        "type": "object",
        "properties": {
            "baseline_ms": {"type": "number", "description": "Baseline duration in milliseconds."},
            "optimized_ms": {"type": "number", "description": "Optimized duration in milliseconds."},
            "baseline_memory_mb": {"type": "number", "description": "Baseline peak memory in MB."},
            "optimized_memory_mb": {"type": "number", "description": "Optimized peak memory in MB."},
        },
        "required": ["baseline_ms", "optimized_ms"],
    }

    def run(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        base_ms = float(arguments["baseline_ms"])
        opt_ms = float(arguments["optimized_ms"])

        if base_ms <= 0 or opt_ms <= 0:
            return ToolResult(success=False, data=None, error="Duration measurements must be positive numbers.")

        speedup = base_ms / opt_ms
        time_change_pct = ((opt_ms - base_ms) / base_ms) * 100.0

        mem_delta_mb = None
        mem_change_pct = None
        if "baseline_memory_mb" in arguments and "optimized_memory_mb" in arguments:
            base_mem = float(arguments["baseline_memory_mb"])
            opt_mem = float(arguments["optimized_memory_mb"])
            mem_delta_mb = opt_mem - base_mem
            if base_mem > 0:
                mem_change_pct = (mem_delta_mb / base_mem) * 100.0

        is_improvement = opt_ms < base_ms

        return ToolResult(
            success=True,
            data={
                "is_improvement": is_improvement,
                "speedup_factor": round(speedup, 2),
                "time_change_percent": round(time_change_pct, 1),
                "time_saved_ms": round(base_ms - opt_ms, 2),
                "memory_delta_mb": round(mem_delta_mb, 2) if mem_delta_mb is not None else None,
                "memory_change_percent": round(mem_change_pct, 1) if mem_change_pct is not None else None,
                "summary": (
                    f"{'Speedup' if is_improvement else 'Slowdown'} of {abs(time_change_pct):.1f}% "
                    f"({base_ms:.1f}ms -> {opt_ms:.1f}ms)."
                ),
            },
        )
