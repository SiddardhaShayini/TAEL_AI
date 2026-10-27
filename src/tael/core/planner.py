from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class StepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    id: int
    description: str
    status: StepStatus = StepStatus.PENDING
    tool_hint: Optional[str] = None
    result_summary: Optional[str] = None

    def to_markdown(self) -> str:
        icons = {
            StepStatus.PENDING: "[ ]",
            StepStatus.IN_PROGRESS: "[>]",
            StepStatus.COMPLETED: "[x]",
            StepStatus.FAILED: "[!]",
            StepStatus.SKIPPED: "[-]",
        }
        res = f"  {icons[self.status]} Step {self.id}: {self.description}"
        if self.result_summary:
            res += f" -> {self.result_summary}"
        return res


@dataclass
class TaskPlan:
    goal: str
    steps: List[PlanStep] = field(default_factory=list)
    verification_strategy: str = ""

    def to_markdown(self) -> str:
        lines = [f"### Task Plan: {self.goal}"]
        for s in self.steps:
            lines.append(s.to_markdown())
        if self.verification_strategy:
            lines.append(f"\n**Verification:** {self.verification_strategy}")
        return "\n".join(lines)

    def is_finished(self) -> bool:
        return all(s.status in (StepStatus.COMPLETED, StepStatus.SKIPPED, StepStatus.FAILED) for s in self.steps)
