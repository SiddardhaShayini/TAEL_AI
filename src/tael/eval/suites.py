import os
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, Any, List, Optional

from tael.config.settings import TaelConfig, PolicyConfig
from tael.memory.models import MemoryCategory, MemoryEntry
from tael.memory.retrieval import MemoryRetriever
from tael.memory.store import MemoryStore
from tael.policy.approval import ApprovalManager
from tael.policy.audit import AuditLogger, redact_secrets
from tael.policy.permissions import PermissionLevel, WorkspaceConfinementError, validate_workspace_path
from tael.resources.monitor import ResourceMonitor
from tael.tools import create_default_registry


@dataclass
class CaseResult:
    case_id: str
    category: str
    description: str
    passed: bool
    duration_ms: float
    details: str
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationCase:
    case_id: str
    category: str  # "safety", "tool_reliability", "memory_efficiency", "resource_bounds", "software_task"
    description: str
    run_fn: Callable[[TaelConfig], CaseResult]


# --- Safety Suite ---

def run_case_path_traversal(config: TaelConfig) -> CaseResult:
    t0 = time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        ws = str(Path(td).resolve())
        # Attempt 1: relative ../
        blocked_rel = False
        try:
            validate_workspace_path("../outside.txt", ws)
        except WorkspaceConfinementError:
            blocked_rel = True

        # Attempt 2: deeply nested ../../
        blocked_deep = False
        try:
            validate_workspace_path("a/b/../../../../secret.key", ws)
        except WorkspaceConfinementError:
            blocked_deep = True

        passed = blocked_rel and blocked_deep
        dur = (time.perf_counter() - t0) * 1000
        return CaseResult(
            case_id="SAF-01",
            category="safety",
            description="Verify strict prevention of directory traversal attacks (../)",
            passed=passed,
            duration_ms=round(dur, 2),
            details="Directory traversal blocked" if passed else "Path traversal was permitted!",
        )


def run_case_secret_redaction(config: TaelConfig) -> CaseResult:
    t0 = time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        log_file = Path(td) / "audit.log"
        logger = AuditLogger(str(log_file))
        logger.record(
            tool_name="test_tool",
            permission="execute_command",
            arguments={"auth": "bearer ghp_123456789012345678901234567890123456", "token": "secret_key_9999"},
            approved=True,
            success=True,
        )
        content = log_file.read_text(encoding="utf-8")
        has_ghp = "ghp_12345678901234567890" in content
        has_secret = "secret_key_9999" in content
        passed = (not has_ghp) and (not has_secret) and ("***REDACTED***" in content)
        dur = (time.perf_counter() - t0) * 1000
        return CaseResult(
            case_id="SAF-02",
            category="safety",
            description="Verify automatic redaction of API tokens and secrets in audit logs",
            passed=passed,
            duration_ms=round(dur, 2),
            details="Secrets redacted in audit log" if passed else "Plaintext secrets leaked into audit log!",
        )


def run_case_approval_gate(config: TaelConfig) -> CaseResult:
    t0 = time.perf_counter()
    # Ensure write operations cannot self-approve without explicit grant
    p_cfg = PolicyConfig(require_approval_write=True)
    mgr = ApprovalManager(p_cfg, custom_approver=lambda t, p, a: False)
    dec = mgr.request_approval("write_file", PermissionLevel.WRITE_WORKSPACE, {})
    passed = dec.granted is False
    dur = (time.perf_counter() - t0) * 1000
    return CaseResult(
        case_id="SAF-03",
        category="safety",
        description="Verify policy enforcement denies unapproved write actions",
        passed=passed,
        duration_ms=round(dur, 2),
        details="Approval gate correctly blocked unapproved write" if passed else "Write was permitted without approval!",
    )


# --- Tool Reliability Suite ---

def run_case_tool_schema_validation(config: TaelConfig) -> CaseResult:
    t0 = time.perf_counter()
    registry = create_default_registry()
    # Call read_file with missing required parameter 'path'
    res = registry.execute("read_file", {})
    passed = (res.success is False) and ("Missing required parameter" in (res.error or ""))
    dur = (time.perf_counter() - t0) * 1000
    return CaseResult(
        case_id="TOOL-01",
        category="tool_reliability",
        description="Verify tool argument schema validation rejects missing parameters",
        passed=passed,
        duration_ms=round(dur, 2),
        details="Schema validator rejected invalid arguments" if passed else f"Schema check failed: {res.error}",
    )


def run_case_command_timeout(config: TaelConfig) -> CaseResult:
    t0 = time.perf_counter()
    registry = create_default_registry()
    # Call a command that sleeps longer than timeout
    res = registry.execute("execute_command", {"command": "python -c \"import time; time.sleep(5)\"", "timeout_seconds": 1.0})
    passed = (res.success is False) and ("timed out" in (res.error or "").lower())
    dur = (time.perf_counter() - t0) * 1000
    return CaseResult(
        case_id="TOOL-02",
        category="tool_reliability",
        description="Verify subprocess execution timeout enforcement and cleanup",
        passed=passed,
        duration_ms=round(dur, 2),
        details="Timeout enforced" if passed else f"Timeout failed: {res.error}",
    )


# --- Memory Efficiency Suite ---

def run_case_memory_fts_ranking(config: TaelConfig) -> CaseResult:
    t0 = time.perf_counter()
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        store = MemoryStore(td, str(Path(td) / "mem_db"))
        store.add_entry(MemoryCategory.CONVENTION, "Git Commit Conventions", "Use Conventional Commits standard.")
        store.add_entry(MemoryCategory.ARCHITECTURE, "SQLite Architecture", "Use SQLite WAL mode and FTS5 indexing.")
        store.add_entry(MemoryCategory.PITFALL, "Windows Path Delimiters", "Always canonicalize backslashes on Windows.")

        results = store.search_fts("SQLite WAL")
        passed = len(results) >= 1 and results[0].title == "SQLite Architecture"
        dur = (time.perf_counter() - t0) * 1000
        return CaseResult(
            case_id="MEM-01",
            category="memory_efficiency",
            description="Verify SQLite FTS5 full-text search and BM25 relevance ranking",
            passed=passed,
            duration_ms=round(dur, 2),
            details=f"Retrieved {len(results)} matches" if passed else "FTS search failed",
            metrics={"matches_count": len(results)},
        )


def run_case_memory_token_budget(config: TaelConfig) -> CaseResult:
    t0 = time.perf_counter()
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        store = MemoryStore(td, str(Path(td) / "mem_db"))
        for i in range(15):
            store.add_entry(
                MemoryCategory.DECISION,
                f"Design Decision {i}",
                f"Detailed architectural reasoning for decision number {i} with long description text.",
            )

        retriever = MemoryRetriever(store, default_token_budget=100)
        res = retriever.retrieve_for_task("architectural reasoning decision", token_budget=100)
        passed = res.total_tokens <= 100 and res.budget_exhausted is True and len(res.entries) < 15
        dur = (time.perf_counter() - t0) * 1000
        return CaseResult(
            case_id="MEM-02",
            category="memory_efficiency",
            description="Verify hard context token budget prevents prompt bloat",
            passed=passed,
            duration_ms=round(dur, 2),
            details=f"Packed {len(res.entries)} entries within {res.total_tokens}/100 tokens" if passed else "Budget violated",
            metrics={"used_tokens": res.total_tokens, "entries_supplied": len(res.entries)},
        )


# --- Resource Bounds Suite ---

def run_case_resource_sampling(config: TaelConfig) -> CaseResult:
    t0 = time.perf_counter()
    monitor = ResourceMonitor(requested_profile="conservative")
    snapshot = monitor.sample()
    passed = (
        snapshot.total_ram_gb > 0
        and snapshot.available_ram_gb > 0
        and 0 <= snapshot.ram_percent <= 100
        and snapshot.active_profile == "conservative"
    )
    dur = (time.perf_counter() - t0) * 1000
    return CaseResult(
        case_id="RES-01",
        category="resource_bounds",
        description="Verify hardware resource sampler measures RAM and CPU correctly",
        passed=passed,
        duration_ms=round(dur, 2),
        details=f"Available: {snapshot.available_ram_gb}GB / Total: {snapshot.total_ram_gb}GB ({snapshot.ram_percent}%)",
        metrics={"total_ram_gb": snapshot.total_ram_gb, "available_ram_gb": snapshot.available_ram_gb},
    )


ALL_EVALUATION_CASES: List[EvaluationCase] = [
    EvaluationCase("SAF-01", "safety", "Path Traversal Defense", run_case_path_traversal),
    EvaluationCase("SAF-02", "safety", "Secret Redaction in Audit Logs", run_case_secret_redaction),
    EvaluationCase("SAF-03", "safety", "Approval Gate Enforcement", run_case_approval_gate),
    EvaluationCase("TOOL-01", "tool_reliability", "Schema Argument Validation", run_case_tool_schema_validation),
    EvaluationCase("TOOL-02", "tool_reliability", "Subprocess Execution Timeout", run_case_command_timeout),
    EvaluationCase("MEM-01", "memory_efficiency", "SQLite FTS5 Full-Text Retrieval", run_case_memory_fts_ranking),
    EvaluationCase("MEM-02", "memory_efficiency", "Context Token Budget Enforcement", run_case_memory_token_budget),
    EvaluationCase("RES-01", "resource_bounds", "Hardware Telemetry & Profile Sampling", run_case_resource_sampling),
]
