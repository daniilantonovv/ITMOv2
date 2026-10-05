import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from app.models import CategoryCount, Collection, CollectionIn, Product, Totals

MAX_COLLECTIONS = 100

SCHEMA = """
CREATE TABLE IF NOT EXISTS collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    cart_url TEXT NOT NULL,
    products TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""


class CollectionStore:
    """SQLite storage. Keeps only the newest MAX_COLLECTIONS rows."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.db_path)
        db.row_factory = sqlite3.Row
        return db

    def create(self, data: CollectionIn) -> Collection:
        created_at = datetime.now(UTC).isoformat(timespec="seconds")
        with self._connect() as db:
            cursor = db.execute(
                "INSERT INTO collections (title, category, cart_url, products, created_at)"
                " VALUES (?, ?, ?, ?, ?)",
                (data.title, data.category, data.cart_url, _dump(data.products), created_at),
            )
            db.execute(
                "DELETE FROM collections WHERE id NOT IN"
                " (SELECT id FROM collections ORDER BY id DESC LIMIT ?)",
                (MAX_COLLECTIONS,),
            )
            new_id = cursor.lastrowid
        return self.get(new_id)

    def get(self, collection_id: int) -> Collection | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM collections WHERE id = ?", (collection_id,)
            ).fetchone()
        return _to_collection(row) if row else None

    def list(self, limit: int, category: str | None = None) -> list[Collection]:
        query = "SELECT * FROM collections"
        params: list = []
        if category is not None:
            query += " WHERE category = ?"
            params.append(category)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        with self._connect() as db:
            rows = db.execute(query, params).fetchall()
        return [_to_collection(row) for row in rows]

    def update(self, collection_id: int, data: CollectionIn) -> Collection | None:
        with self._connect() as db:
            cursor = db.execute(
                "UPDATE collections SET title = ?, category = ?, cart_url = ?, products = ?"
                " WHERE id = ?",
                (data.title, data.category, data.cart_url, _dump(data.products), collection_id),
            )
        return self.get(collection_id) if cursor.rowcount else None

    def delete(self, collection_id: int) -> bool:
        with self._connect() as db:
            cursor = db.execute("DELETE FROM collections WHERE id = ?", (collection_id,))
        return cursor.rowcount > 0

    def categories(self) -> list[CategoryCount]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT category, COUNT(*) AS count FROM collections"
                " GROUP BY category ORDER BY category"
            ).fetchall()
        return [CategoryCount(category=row["category"], count=row["count"]) for row in rows]


def _dump(products: list[Product]) -> str:
    return json.dumps([p.model_dump() for p in products], ensure_ascii=False)


def _to_collection(row: sqlite3.Row) -> Collection:
    products = [Product(**p) for p in json.loads(row["products"])]
    return Collection(
        id=row["id"],
        title=row["title"],
        category=row["category"],
        cart_url=row["cart_url"],
        created_at=row["created_at"],
        products=products,
        totals=Totals.of(products),
    )
