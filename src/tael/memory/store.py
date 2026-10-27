import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from tael.memory.models import MemoryCategory, MemoryEntry, ProjectProfile


def generate_project_id(workspace_path: str) -> str:
    """Generate a clean, deterministic project ID from canonical workspace path."""
    canonical = str(Path(workspace_path).resolve()).lower()
    folder_name = Path(canonical).name or "root"
    h = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:8]
    # Clean folder name for safe filename
    clean_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in folder_name)
    return f"{clean_name}_{h}"


class MemoryStore:
    def __init__(self, workspace_path: str, store_dir: Optional[str] = None):
        self.workspace_path = str(Path(workspace_path).resolve())
        self.project_id = generate_project_id(self.workspace_path)
        
        if store_dir:
            self.base_dir = Path(store_dir)
        else:
            from tael.config.settings import TaelConfig
            self.base_dir = TaelConfig.get_user_tael_dir(self.workspace_path) / "memory"
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        
        self.db_path = self.base_dir / f"{self.project_id}.db"
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    workspace_path TEXT NOT NULL,
                    project_name TEXT NOT NULL,
                    primary_language TEXT,
                    framework TEXT,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT NOT NULL, -- JSON array
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    verified INTEGER NOT NULL DEFAULT 1,
                    source_paths TEXT NOT NULL, -- JSON array
                    supersedes_id INTEGER,
                    active INTEGER NOT NULL DEFAULT 1
                );
            """)

            # SQLite FTS5 Table
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
                    title,
                    content,
                    tags,
                    category,
                    content='memory_entries',
                    content_rowid='id'
                );
            """)

            # FTS Triggers
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memory_entries_ai AFTER INSERT ON memory_entries BEGIN
                    INSERT INTO memory_fts(rowid, title, content, tags, category)
                    VALUES (new.id, new.title, new.content, new.tags, new.category);
                END;
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memory_entries_ad AFTER DELETE ON memory_entries BEGIN
                    INSERT INTO memory_fts(memory_fts, rowid, title, content, tags, category)
                    VALUES ('delete', old.id, old.title, old.content, old.tags, old.category);
                END;
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memory_entries_au AFTER UPDATE ON memory_entries BEGIN
                    INSERT INTO memory_fts(memory_fts, rowid, title, content, tags, category)
                    VALUES ('delete', old.id, old.title, old.content, old.tags, old.category);
                    INSERT INTO memory_fts(rowid, title, content, tags, category)
                    VALUES (new.id, new.title, new.content, new.tags, new.category);
                END;
            """)
            conn.commit()

        # Ensure project record exists
        self.get_or_create_project_profile()

    def get_or_create_project_profile(self) -> ProjectProfile:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM projects WHERE project_id = ?", (self.project_id,)
            ).fetchone()
            if row:
                return ProjectProfile(
                    project_id=row["project_id"],
                    workspace_path=row["workspace_path"],
                    project_name=row["project_name"],
                    primary_language=row["primary_language"] or "Unknown",
                    framework=row["framework"] or "Unknown",
                    description=row["description"] or "",
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            folder_name = Path(self.workspace_path).name or "Workspace"
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                """
                INSERT INTO projects (project_id, workspace_path, project_name, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (self.project_id, self.workspace_path, folder_name, now, now),
            )
            conn.commit()
            return ProjectProfile(
                project_id=self.project_id,
                workspace_path=self.workspace_path,
                project_name=folder_name,
                created_at=now,
                updated_at=now,
            )

    def add_entry(
        self,
        category: MemoryCategory,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        verified: bool = True,
        source_paths: Optional[List[str]] = None,
        supersedes_id: Optional[int] = None,
    ) -> MemoryEntry:
        now = datetime.now(timezone.utc).isoformat()
        tags_json = json.dumps(tags or [])
        sources_json = json.dumps(source_paths or [])

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO memory_entries (
                    project_id, category, title, content, tags,
                    created_at, updated_at, verified, source_paths,
                    supersedes_id, active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    self.project_id,
                    category.value,
                    title,
                    content,
                    tags_json,
                    now,
                    now,
                    1 if verified else 0,
                    sources_json,
                    supersedes_id,
                ),
            )
            entry_id = cursor.lastrowid
            conn.commit()

        return MemoryEntry(
            id=entry_id,
            project_id=self.project_id,
            category=category,
            title=title,
            content=content,
            tags=tags or [],
            created_at=now,
            updated_at=now,
            verified=verified,
            source_paths=source_paths or [],
            supersedes_id=supersedes_id,
            active=True,
        )

    def supersede_entry(self, old_entry_id: int, new_entry: MemoryEntry) -> MemoryEntry:
        """Mark old entry as inactive and link new entry as superseding it."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE memory_entries SET active = 0, updated_at = ? WHERE id = ?",
                (datetime.now(timezone.utc).isoformat(), old_entry_id),
            )
            conn.commit()

        new_entry.supersedes_id = old_entry_id
        return self.add_entry(
            category=new_entry.category,
            title=new_entry.title,
            content=new_entry.content,
            tags=new_entry.tags,
            verified=new_entry.verified,
            source_paths=new_entry.source_paths,
            supersedes_id=old_entry_id,
        )

    def get_entry(self, entry_id: int) -> Optional[MemoryEntry]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM memory_entries WHERE id = ?", (entry_id,)).fetchone()
            if not row:
                return None
            return self._row_to_entry(row)

    def list_entries(
        self,
        category: Optional[MemoryCategory] = None,
        active_only: bool = True,
        limit: int = 100,
    ) -> List[MemoryEntry]:
        query = "SELECT * FROM memory_entries WHERE project_id = ?"
        params: List[Any] = [self.project_id]

        if active_only:
            query += " AND active = 1"
        if category:
            query += " AND category = ?"
            params.append(category.value)

        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_entry(r) for r in rows]

    def search_fts(
        self,
        query: str,
        category: Optional[MemoryCategory] = None,
        limit: int = 10,
        active_only: bool = True,
    ) -> List[MemoryEntry]:
        """Full-text search using SQLite FTS5 with BM25 ranking."""
        # Sanitize query for FTS5 (escape quotes, tokens)
        clean_tokens = [t for t in "".join(c if c.isalnum() else " " for c in query).split() if len(t) > 1]
        if not clean_tokens:
            return self.list_entries(category=category, active_only=active_only, limit=limit)

        fts_query = " OR ".join(f'"{t}"*' for t in clean_tokens)

        sql = """
            SELECT m.*, rank FROM memory_entries m
            JOIN memory_fts f ON m.id = f.rowid
            WHERE memory_fts MATCH ? AND m.project_id = ?
        """
        params: List[Any] = [fts_query, self.project_id]

        if active_only:
            sql += " AND m.active = 1"
        if category:
            sql += " AND m.category = ?"
            params.append(category.value)

        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            try:
                rows = conn.execute(sql, params).fetchall()
                return [self._row_to_entry(r) for r in rows]
            except sqlite3.OperationalError:
                # Fallback to simple title/content LIKE search if FTS syntax error
                return self.list_entries(category=category, active_only=active_only, limit=limit)

    def delete_entry(self, entry_id: int, hard: bool = False) -> bool:
        with self._get_connection() as conn:
            if hard:
                cursor = conn.execute("DELETE FROM memory_entries WHERE id = ?", (entry_id,))
            else:
                cursor = conn.execute("UPDATE memory_entries SET active = 0 WHERE id = ?", (entry_id,))
            conn.commit()
            return cursor.rowcount > 0

    def clear_project_memory(self) -> int:
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM memory_entries WHERE project_id = ?", (self.project_id,))
            conn.commit()
            return cursor.rowcount

    def export_to_markdown(self) -> str:
        profile = self.get_or_create_project_profile()
        entries = self.list_entries(active_only=True, limit=500)
        
        md_lines = [
            f"# TAEL Project Memory Export: {profile.project_name}",
            f"- **Workspace Path:** `{profile.workspace_path}`",
            f"- **Exported At:** {datetime.now(timezone.utc).isoformat()}",
            f"- **Active Entries:** {len(entries)}\n",
            "---",
            "## Stored Project Knowledge\n",
        ]

        if not entries:
            md_lines.append("*No entries stored yet.*")
        else:
            for entry in entries:
                md_lines.append(entry.to_markdown())

        return "\n".join(md_lines)

    def _row_to_entry(self, row: sqlite3.Row) -> MemoryEntry:
        return MemoryEntry(
            id=row["id"],
            project_id=row["project_id"],
            category=MemoryCategory(row["category"]),
            title=row["title"],
            content=row["content"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            verified=bool(row["verified"]),
            source_paths=json.loads(row["source_paths"]) if row["source_paths"] else [],
            supersedes_id=row["supersedes_id"],
            active=bool(row["active"]),
        )
