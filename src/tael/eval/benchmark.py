import json
import platform
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from tael import __version__
from tael.config.settings import TaelConfig
from tael.eval.suites import ALL_EVALUATION_CASES, CaseResult, EvaluationCase
from tael.resources.monitor import ResourceMonitor


@dataclass
class BenchmarkReport:
    version: str
    timestamp: str
    machine_os: str
    machine_arch: str
    total_ram_gb: float
    cpu_cores_logical: int
    active_profile: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    total_duration_ms: float
    results: List[CaseResult] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        if self.total_cases == 0:
            return 0.0
        return (self.passed_cases / self.total_cases) * 100.0

    def to_markdown(self) -> str:
        lines = [
            f"# TAEL V3 — Evaluation Benchmark Report",
            f"- **Version:** `v{self.version}`",
            f"- **Execution Timestamp:** `{self.timestamp}`",
            f"- **Operating System:** `{self.machine_os} ({self.machine_arch})`",
            f"- **Hardware Target:** `{self.total_ram_gb} GB RAM, {self.cpu_cores_logical} CPU Cores (Profile: {self.active_profile.upper()})`",
            f"- **Summary:** **{self.passed_cases}/{self.total_cases} Passed** ({self.pass_rate:.1f}%) in `{self.total_duration_ms:.1f} ms`\n",
            "---",
            "## Case Results",
            "",
            "| Case ID | Category | Description | Status | Duration (ms) | Details |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]

        for r in self.results:
            status_badge = "**PASS**" if r.passed else "**FAIL**"
            lines.append(f"| `{r.case_id}` | `{r.category}` | {r.description} | {status_badge} | {r.duration_ms:.1f} | {r.details} |")

        lines.append("")
        return "\n".join(lines)

    def to_json(self) -> str:
        data = {
            "version": self.version,
            "timestamp": self.timestamp,
            "system": {
                "os": self.machine_os,
                "arch": self.machine_arch,
                "total_ram_gb": self.total_ram_gb,
                "cpu_cores_logical": self.cpu_cores_logical,
                "active_profile": self.active_profile,
            },
            "summary": {
                "total_cases": self.total_cases,
                "passed_cases": self.passed_cases,
                "failed_cases": self.failed_cases,
                "pass_rate_percent": round(self.pass_rate, 2),
                "total_duration_ms": round(self.total_duration_ms, 2),
            },
            "results": [
                {
                    "case_id": r.case_id,
                    "category": r.category,
                    "description": r.description,
                    "passed": r.passed,
                    "duration_ms": r.duration_ms,
                    "details": r.details,
                    "metrics": r.metrics,
                }
                for r in self.results
            ],
        }
        return json.dumps(data, indent=2)


class BenchmarkRunner:
    def __init__(self, config: Optional[TaelConfig] = None):
        self.config = config or TaelConfig.load()
        self.monitor = ResourceMonitor(self.config.resource.profile)

    def run_suite(self, category: Optional[str] = None) -> BenchmarkReport:
        snapshot = self.monitor.sample()
        cases = ALL_EVALUATION_CASES
        if category:
            cases = [c for c in cases if c.category.lower() == category.lower()]

        t0 = time.perf_counter()
        results: List[CaseResult] = []

        for case in cases:
            res = case.run_fn(self.config)
            results.append(res)

        total_dur = (time.perf_counter() - t0) * 1000
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed

        return BenchmarkReport(
            version=__version__,
            timestamp=datetime.now(timezone.utc).isoformat(),
            machine_os=platform.system(),
            machine_arch=platform.machine(),
            total_ram_gb=snapshot.total_ram_gb,
            cpu_cores_logical=snapshot.cpu_count_logical,
            active_profile=snapshot.active_profile,
            total_cases=len(results),
            passed_cases=passed,
            failed_cases=failed,
            total_duration_ms=round(total_dur, 2),
            results=results,
        )
