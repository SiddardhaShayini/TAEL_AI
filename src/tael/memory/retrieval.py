from typing import List, Optional
from tael.memory.models import MemoryCategory, MemoryEntry, MemorySearchResult
from tael.memory.store import MemoryStore


class MemoryRetriever:
    def __init__(self, store: MemoryStore, default_token_budget: int = 1000):
        self.store = store
        self.default_token_budget = default_token_budget

    def retrieve_for_task(
        self,
        task_prompt: str,
        token_budget: Optional[int] = None,
        max_entries: int = 8,
    ) -> MemorySearchResult:
        """
        Retrieve a bounded, prioritized subset of project memory for a task prompt.
        Enforces a hard token budget to prevent context window bloat on 8GB machines.
        """
        budget = token_budget or self.default_token_budget
        profile = self.store.get_or_create_project_profile()

        # Step 1: Search using FTS5 on task prompt
        candidates = self.store.search_fts(task_prompt, limit=max_entries * 2, active_only=True)

        # Step 2: Also fetch high-priority conventions and architecture if not already found
        priority_categories = [MemoryCategory.CONVENTION, MemoryCategory.ARCHITECTURE, MemoryCategory.PITFALL]
        for cat in priority_categories:
            cat_entries = self.store.list_entries(category=cat, active_only=True, limit=3)
            for e in cat_entries:
                if not any(c.id == e.id for c in candidates):
                    candidates.append(e)

        # Step 3: Greedily pack entries within token budget
        selected: List[MemoryEntry] = []
        used_tokens = 0
        budget_exhausted = False

        for entry in candidates:
            cost = entry.estimate_tokens()
            if used_tokens + cost <= budget:
                selected.append(entry)
                used_tokens += cost
            else:
                budget_exhausted = True
                break

        return MemorySearchResult(
            entries=selected,
            total_found=len(candidates),
            total_tokens=used_tokens,
            budget_exhausted=budget_exhausted,
        )

    def format_context_prompt(self, result: MemorySearchResult) -> str:
        """Format retrieved memories into a clear, structured prompt section."""
        if not result.entries:
            return ""

        profile = self.store.get_or_create_project_profile()
        lines = [
            f"=== PERSISTENT PROJECT MEMORY (Supplied {len(result.entries)} entries, ~{result.total_tokens} tokens) ===",
            f"Project: {profile.project_name} ({profile.primary_language})",
            "Note: Memory is contextual guidance; always verify facts against live files and test execution.",
            "",
        ]

        for entry in result.entries:
            status = "Verified" if entry.verified else "Assumption"
            lines.append(f"• [{entry.category.value.upper()}] {entry.title} ({status})")
            lines.append(f"  {entry.content}")
            if entry.source_paths:
                lines.append(f"  Sources: {', '.join(entry.source_paths)}")
            lines.append("")

        lines.append("=" * 65)
        return "\n".join(lines)
