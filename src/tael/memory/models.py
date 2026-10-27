from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
import json


class MemoryCategory(str, Enum):
    ARCHITECTURE = "architecture"
    CONVENTION = "convention"
    DECISION = "decision"
    PITFALL = "pitfall"
    DEPENDENCY = "dependency"
    WORK_COMPLETED = "work_completed"
    OPEN_WORK = "open_work"
    ENVIRONMENT = "environment"


@dataclass
class MemoryEntry:
    id: Optional[int] = None
    project_id: str = ""
    category: MemoryCategory = MemoryCategory.DECISION
    title: str = ""
    content: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    verified: bool = True
    source_paths: List[str] = field(default_factory=list)
    supersedes_id: Optional[int] = None
    active: bool = True

    def estimate_tokens(self) -> int:
        """Rough token estimate (~4 chars per token) for context budgeting."""
        text = f"{self.title} {self.content} {' '.join(self.tags)} {self.category.value}"
        return max(1, len(text) // 4)

    def to_markdown(self) -> str:
        tags_str = ", ".join(self.tags) if self.tags else "none"
        sources_str = ", ".join(self.source_paths) if self.source_paths else "none"
        verified_str = "Verified" if self.verified else "Unverified/Assumption"
        return (
            f"### [{self.category.value.upper()}] {self.title}\n"
            f"- **Status:** {verified_str} | **Tags:** {tags_str} | **Sources:** {sources_str}\n"
            f"- **Content:** {self.content}\n"
        )


@dataclass
class ProjectProfile:
    project_id: str
    workspace_path: str
    project_name: str
    primary_language: str = "Unknown"
    framework: str = "Unknown"
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class MemorySearchResult:
    entries: List[MemoryEntry]
    total_found: int
    total_tokens: int
    budget_exhausted: bool = False
