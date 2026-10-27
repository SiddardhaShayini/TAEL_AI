import json
import pytest
from pathlib import Path

from tael.config.settings import PolicyConfig
from tael.policy.approval import ApprovalDecision, ApprovalManager
from tael.policy.audit import AuditLogger, redact_secrets
from tael.policy.permissions import (
    PermissionLevel,
    WorkspaceConfinementError,
    validate_workspace_path,
)


def test_workspace_confinement(tmp_path: Path):
    ws_root = str(tmp_path)

    # Valid in-workspace paths
    p1 = validate_workspace_path("sub/file.txt", ws_root)
    assert str(p1).startswith(str(tmp_path.resolve()))

    # Directory traversal attack
    with pytest.raises(WorkspaceConfinementError):
        validate_workspace_path("../outside.txt", ws_root)

    with pytest.raises(WorkspaceConfinementError):
        validate_workspace_path("sub/../../outside.txt", ws_root)


def test_audit_redaction():
    secret_data = {
        "api_key": "sk-1234567890abcdef1234567890",
        "nested": {"token": "ghp_123456789012345678901234567890123456"},
        "normal": "hello world",
    }
    redacted = redact_secrets(secret_data)
    assert redacted["api_key"] == "***REDACTED***"
    assert redacted["nested"]["token"] == "***REDACTED***"
    assert redacted["normal"] == "hello world"


def test_audit_logging(tmp_path: Path):
    log_file = tmp_path / "audit.log"
    logger = AuditLogger(str(log_file))

    logger.record(
        tool_name="write_file",
        permission="write_workspace",
        arguments={"path": "test.txt", "content": "secret password=my_secret_token_123"},
        approved=True,
        success=True,
        duration_ms=12.5,
    )

    assert log_file.exists()
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["tool"] == "write_file"
    assert entry["approved"] is True
    assert entry["success"] is True
    # Verify redacted in log
    assert "my_secret_token_123" not in entry["arguments"]["content"]


def test_approval_manager():
    cfg = PolicyConfig(require_approval_write=True)

    # Approver that denies everything
    mgr = ApprovalManager(cfg, custom_approver=lambda t, p, a: False)
    dec = mgr.request_approval("write_file", PermissionLevel.WRITE_WORKSPACE, {})
    assert dec.granted is False

    # Read operations should not require approval
    dec_read = mgr.request_approval("read_file", PermissionLevel.READ_WORKSPACE, {})
    assert dec_read.granted is True

    # Approver that approves
    mgr_allow = ApprovalManager(cfg, custom_approver=lambda t, p, a: True)
    dec_write = mgr_allow.request_approval("write_file", PermissionLevel.WRITE_WORKSPACE, {})
    assert dec_write.granted is True


def test_snapshot_manager(tmp_path: Path):
    from tael.policy.rollback import SnapshotManager
    mgr = SnapshotManager(str(tmp_path))

    # Create checkpoint
    chk = mgr.create_checkpoint("Initial state test")
    assert chk.id.startswith("chk_")
    assert chk.description == "Initial state test"

    # List checkpoints
    checkpoints = mgr.list_checkpoints()
    assert len(checkpoints) >= 1
    assert any(c["id"] == chk.id for c in checkpoints)
