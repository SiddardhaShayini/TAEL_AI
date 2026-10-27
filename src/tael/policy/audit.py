import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|secret|password|bearer|auth|authorization)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?"),
    re.compile(r"ghp_[a-zA-Z0-9]{36}"),
    re.compile(r"sk-[a-zA-Z0-9]{32,}"),
]


def redact_secrets(data: Any) -> Any:
    """Recursively redact obvious API keys, tokens, and passwords from logged structures."""
    if isinstance(data, str):
        redacted = data
        redacted = re.sub(r"ghp_[a-zA-Z0-9]{36}", "ghp_***REDACTED***", redacted)
        redacted = re.sub(r"sk-[a-zA-Z0-9]{32,}", "sk-***REDACTED***", redacted)
        redacted = re.sub(
            r"(?i)(api[_-]?key|token|secret|password|bearer|auth|authorization)(\s*[:=]\s*['\"]?)([a-zA-Z0-9_\-\.]{8,})(['\"]?)",
            r"\1\2***REDACTED***\4",
            redacted,
        )
        return redacted
    elif isinstance(data, dict):
        out = {}
        for k, v in data.items():
            if any(s in k.lower() for s in ["token", "secret", "password", "api_key", "authorization"]):
                out[k] = "***REDACTED***"
            else:
                out[k] = redact_secrets(v)
        return out
    elif isinstance(data, list):
        return [redact_secrets(item) for item in data]
    return data


class AuditLogger:
    def __init__(self, log_path: Optional[str] = None):
        if log_path:
            self.log_file = Path(log_path)
        else:
            from tael.config.settings import TaelConfig
            self.log_file = TaelConfig.get_user_tael_dir() / "audit.log"
        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

    def record(
        self,
        tool_name: str,
        permission: str,
        arguments: Dict[str, Any],
        approved: bool,
        success: bool,
        error_message: Optional[str] = None,
        duration_ms: float = 0.0,
    ) -> None:
        """Write an audit entry in JSONL format."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool": tool_name,
            "permission": permission,
            "arguments": redact_secrets(arguments),
            "approved": approved,
            "success": success,
            "error": error_message,
            "duration_ms": round(duration_ms, 2),
        }
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            # Audit logging failure must not crash the entire orchestrator, but log to stderr
            pass
