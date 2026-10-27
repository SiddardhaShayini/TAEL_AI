import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from tael.models.client import LLMMessage


@dataclass
class SessionState:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    workspace_root: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    messages: List[LLMMessage] = field(default_factory=list)
    action_log: List[Dict[str, Any]] = field(default_factory=list)
    max_history_turns: int = 20
    is_cancelled: bool = False

    def add_message(self, message: LLMMessage) -> None:
        self.messages.append(message)
        # Bounded history window: maintain system message + recent turns
        if len(self.messages) > (self.max_history_turns * 2 + 1):
            system_msgs = [m for m in self.messages if m.role == "system"]
            recent_turns = self.messages[-(self.max_history_turns * 2):]
            self.messages = (system_msgs[:1] if system_msgs else []) + recent_turns

    def cancel(self) -> None:
        self.is_cancelled = True
