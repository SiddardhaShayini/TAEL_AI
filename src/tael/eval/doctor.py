import os
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from tael.config.settings import TaelConfig
from tael.memory.store import MemoryStore
from tael.models.runtime import ModelRuntimeManager
from tael.policy.audit import AuditLogger, redact_secrets
from tael.policy.permissions import WorkspaceConfinementError, validate_workspace_path
from tael.resources.monitor import ResourceMonitor
from tael.tools import create_default_registry


@dataclass
class DiagnosticCheck:
    name: str
    status: str  # "PASS", "WARN", "FAIL"
    message: str


class SystemDoctor:
    def __init__(self, config: TaelConfig):
        self.config = config

    def run_all_checks(self) -> List[DiagnosticCheck]:
        checks = []
        checks.append(self._check_workspace_security())
        checks.append(self._check_sqlite_fts5())
        checks.append(self._check_resource_supervisor())
        checks.append(self._check_audit_logging())
        checks.append(self._check_tool_registry())
        checks.append(self._check_model_runtime())
        return checks

    def _check_workspace_security(self) -> DiagnosticCheck:
        try:
            # 1. Valid workspace resolve
            validate_workspace_path(".", self.config.workspace_root)
            # 2. Traversal protection
            traversal_caught = False
            try:
                validate_workspace_path("../outside_test_path.txt", self.config.workspace_root)
            except WorkspaceConfinementError:
                traversal_caught = True

            if traversal_caught:
                return DiagnosticCheck("Workspace Confinement", "PASS", "Strict path traversal confinement active.")
            return DiagnosticCheck("Workspace Confinement", "FAIL", "Path traversal was not properly blocked.")
        except Exception as e:
            return DiagnosticCheck("Workspace Confinement", "FAIL", str(e))

    def _check_sqlite_fts5(self) -> DiagnosticCheck:
        try:
            with sqlite3.connect(":memory:") as conn:
                conn.execute("CREATE VIRTUAL TABLE fts_test USING fts5(title, content);")
                conn.execute("INSERT INTO fts_test(title, content) VALUES ('TAEL', 'Local AI Assistant');")
                cur = conn.execute("SELECT * FROM fts_test WHERE fts_test MATCH 'Local';")
                row = cur.fetchone()
                if row:
                    return DiagnosticCheck("SQLite FTS5 Full-Text Search", "PASS", "FTS5 module enabled and functional.")
            return DiagnosticCheck("SQLite FTS5 Full-Text Search", "FAIL", "FTS5 query returned no results.")
        except Exception as e:
            return DiagnosticCheck("SQLite FTS5 Full-Text Search", "FAIL", f"SQLite FTS5 unavailable: {str(e)}")

    def _check_resource_supervisor(self) -> DiagnosticCheck:
        try:
            monitor = ResourceMonitor(self.config.resource.profile)
            snapshot = monitor.sample()
            if snapshot.total_ram_gb > 0 and snapshot.available_ram_gb > 0:
                msg = f"Profile: {snapshot.active_profile.upper()} | RAM: {snapshot.available_ram_gb}GB free / {snapshot.total_ram_gb}GB total"
                return DiagnosticCheck("Hardware Resource Supervisor", "PASS", msg)
            return DiagnosticCheck("Hardware Resource Supervisor", "WARN", "Could not sample system memory.")
        except Exception as e:
            return DiagnosticCheck("Hardware Resource Supervisor", "FAIL", str(e))

    def _check_audit_logging(self) -> DiagnosticCheck:
        try:
            with tempfile.TemporaryDirectory() as td:
                test_log = Path(td) / "test_audit.log"
                logger = AuditLogger(str(test_log))
                logger.record(
                    tool_name="test_tool",
                    permission="read_workspace",
                    arguments={"api_key": "sk-1234567890abcdef1234567890"},
                    approved=True,
                    success=True,
                )
                content = test_log.read_text(encoding="utf-8")
                if "***REDACTED***" in content and "sk-1234567890abcdef" not in content:
                    return DiagnosticCheck("Audit & Redaction Service", "PASS", "Audit log and secret redaction verified.")
            return DiagnosticCheck("Audit & Redaction Service", "FAIL", "Secret redaction failed.")
        except Exception as e:
            return DiagnosticCheck("Audit & Redaction Service", "FAIL", str(e))

    def _check_tool_registry(self) -> DiagnosticCheck:
        try:
            registry = create_default_registry()
            tools = registry.list_tools()
            if len(tools) >= 12:
                return DiagnosticCheck("Typed Tool Registry", "PASS", f"{len(tools)} tools registered and schema-validated.")
            return DiagnosticCheck("Typed Tool Registry", "WARN", f"Only {len(tools)} tools registered.")
        except Exception as e:
            return DiagnosticCheck("Typed Tool Registry", "FAIL", str(e))

    def _check_model_runtime(self) -> DiagnosticCheck:
        runtime = ModelRuntimeManager(self.config.model)
        online = runtime.check_health()
        if online:
            models = runtime.list_installed_models()
            return DiagnosticCheck("Model Inference Backend", "PASS", f"Online ({len(models)} models found: {', '.join(models[:3])})")
        return DiagnosticCheck(
            "Model Inference Backend",
            "WARN",
            f"Ollama offline at {self.config.model.endpoint}. TAEL is operating with mock runtime.",
        )
