import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class InventoryItem:
    id: Optional[int]
    sku: str
    name: str
    quantity: int
    price_cents: int
    updated_at: str


class InventoryDB:
    """Local SQLite-backed inventory store engineered for offline, lightweight desktop apps."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sku TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    quantity INTEGER NOT NULL DEFAULT 0,
                    price_cents INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL
                );
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_items_sku ON items(sku);")
            conn.commit()

    def add_or_update_item(self, sku: str, name: str, quantity: int, price_cents: int) -> InventoryItem:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO items (sku, name, quantity, price_cents, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(sku) DO UPDATE SET
                    name=excluded.name,
                    quantity=excluded.quantity,
                    price_cents=excluded.price_cents,
                    updated_at=excluded.updated_at;
                """,
                (sku, name, quantity, price_cents, now),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM items WHERE sku = ?", (sku,)).fetchone()
            return InventoryItem(
                id=row["id"],
                sku=row["sku"],
                name=row["name"],
                quantity=row["quantity"],
                price_cents=row["price_cents"],
                updated_at=row["updated_at"],
            )

    def get_item_by_sku(self, sku: str) -> Optional[InventoryItem]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM items WHERE sku = ?", (sku,)).fetchone()
            if not row:
                return None
            return InventoryItem(
                id=row["id"],
                sku=row["sku"],
                name=row["name"],
                quantity=row["quantity"],
                price_cents=row["price_cents"],
                updated_at=row["updated_at"],
            )

    def list_low_stock(self, threshold: int = 5) -> List[InventoryItem]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM items WHERE quantity <= ? ORDER BY quantity ASC",
                (threshold,),
            ).fetchall()
            return [
                InventoryItem(
                    id=r["id"],
                    sku=r["sku"],
                    name=r["name"],
                    quantity=r["quantity"],
                    price_cents=r["price_cents"],
                    updated_at=r["updated_at"],
                )
                for r in rows
            ]

    def delete_item(self, sku: str) -> bool:
        with self._get_connection() as conn:
            cur = conn.execute("DELETE FROM items WHERE sku = ?", (sku,))
            conn.commit()
            return cur.rowcount > 0
