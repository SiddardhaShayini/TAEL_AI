from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class SearchResultItem:
    title: str
    url: str
    snippet: str
    source_domain: str = ""
    published_date: Optional[str] = None


@dataclass
class ResearchSource:
    url: str
    title: str
    excerpt: str
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_primary: bool = False


@dataclass
class ResearchFinding:
    claim: str
    citation_urls: List[str] = field(default_factory=list)
    confidence: str = "medium"  # "high", "medium", "uncertain"
    uncertainty_notes: Optional[str] = None


@dataclass
class ResearchReport:
    topic: str
    summary: str
    findings: List[ResearchFinding] = field(default_factory=list)
    sources: List[ResearchSource] = field(default_factory=list)
    unresolved_questions: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_markdown(self) -> str:
        lines = [
            f"# Research Report: {self.topic}",
            f"- **Date:** {self.created_at}",
            f"- **Sources Consulted:** {len(self.sources)}\n",
            "## Summary",
            self.summary,
            "\n## Key Findings",
        ]
        for f in self.findings:
            conf_badge = f"[{f.confidence.upper()}]"
            cites = ", ".join(f"[Source]({u})" for u in f.citation_urls)
            lines.append(f"- **{conf_badge}** {f.claim}")
            if cites:
                lines.append(f"  *Citations:* {cites}")
            if f.uncertainty_notes:
                lines.append(f"  *Uncertainty:* {f.uncertainty_notes}")

        if self.unresolved_questions:
            lines.append("\n## Missing Evidence / Open Questions")
            for q in self.unresolved_questions:
                lines.append(f"- {q}")

        lines.append("\n## Sources")
        for s in self.sources:
            lines.append(f"- [{s.title}]({s.url}) (Retrieved {s.fetched_at})")

        return "\n".join(lines)
