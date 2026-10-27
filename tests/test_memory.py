from pathlib import Path
from tael.memory.models import MemoryCategory, MemoryEntry
from tael.memory.store import MemoryStore
from tael.memory.retrieval import MemoryRetriever


def test_memory_store_crud_and_fts(tmp_path: Path):
    store = MemoryStore(workspace_path=str(tmp_path), store_dir=str(tmp_path / "memory_db"))

    # Add convention entry
    e1 = store.add_entry(
        category=MemoryCategory.CONVENTION,
        title="Code Formatting Rules",
        content="Use 4 spaces for indentation. Never use raw SQL concatenation.",
        tags=["python", "style", "security"],
        source_paths=["CONTRIBUTING.md"],
    )
    assert e1.id is not None
    assert e1.active is True

    # Add architecture entry
    e2 = store.add_entry(
        category=MemoryCategory.ARCHITECTURE,
        title="Local-First Storage",
        content="Use SQLite for local relational data storage and FTS5 for indexing.",
        tags=["database", "sqlite"],
    )

    # Search via FTS5
    res = store.search_fts("formatting")
    assert len(res) == 1
    assert res[0].title == "Code Formatting Rules"

    res_sql = store.search_fts("SQLite")
    assert len(res_sql) >= 1
    assert any("SQLite" in r.content for r in res_sql)

    # Supersede e1 with updated entry
    e3 = store.supersede_entry(
        old_entry_id=e1.id,
        new_entry=MemoryEntry(
            category=MemoryCategory.CONVENTION,
            title="Updated Code Formatting Rules",
            content="Use black formatter with 88 chars max line length.",
            tags=["python", "black"],
        ),
    )
    assert e3.supersedes_id == e1.id

    # e1 should now be inactive
    old_e1 = store.get_entry(e1.id)
    assert old_e1.active is False

    # Active list should only return e2 and e3
    active_entries = store.list_entries(active_only=True)
    assert len(active_entries) == 2

    # Export to markdown
    md = store.export_to_markdown()
    assert "# TAEL Project Memory Export" in md
    assert "Updated Code Formatting Rules" in md


def test_memory_retriever_token_budget(tmp_path: Path):
    store = MemoryStore(workspace_path=str(tmp_path), store_dir=str(tmp_path / "memory_db"))
    retriever = MemoryRetriever(store, default_token_budget=50)

    # Add multiple entries
    for i in range(10):
        store.add_entry(
            category=MemoryCategory.DECISION,
            title=f"Architectural Decision {i}",
            content=f"Detailed rationale explaining why choice {i} was selected for module {i} with long descriptions.",
            tags=["decision", "arch"],
        )

    # Retrieve with small token budget (50 tokens)
    result = retriever.retrieve_for_task("module architectural decision", token_budget=50)
    assert result.budget_exhausted is True
    assert result.total_tokens <= 50
    assert len(result.entries) < 10

    # Formatted prompt includes header and boundary
    prompt = retriever.format_context_prompt(result)
    assert "=== PERSISTENT PROJECT MEMORY" in prompt
