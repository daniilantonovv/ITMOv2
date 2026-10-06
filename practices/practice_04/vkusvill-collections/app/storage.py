import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from app.models import CategoryCount, Collection, CollectionIn, Product, Totals

MAX_COLLECTIONS = 100


class DuplicateCartUrlError(Exception):
    """Raised when trying to store a collection with a cart_url that already exists."""


class StorageUnavailableError(Exception):
    """Raised when the database cannot be read or written."""

SCHEMA = """
CREATE TABLE IF NOT EXISTS collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    cart_url TEXT NOT NULL,
    products TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_collections_cart_url ON collections(cart_url);
"""


class CollectionStore:
    """SQLite storage. Keeps only the newest MAX_COLLECTIONS rows."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self._schema_ready = False

    @contextmanager
    def _db(self) -> Iterator[sqlite3.Connection]:
        """One transaction. Storage failures become StorageUnavailableError.

        The schema is created lazily, so a database that was broken at startup
        works again once it is repaired, without a restart.
        """
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            db = sqlite3.connect(self.db_path)
            try:
                db.row_factory = sqlite3.Row
                with db:
                    if not self._schema_ready:
                        db.executescript(SCHEMA)
                        self._schema_ready = True
                    yield db
            finally:
                db.close()
        except sqlite3.IntegrityError:
            raise
        except (sqlite3.DatabaseError, OSError) as error:
            self._schema_ready = False
            raise StorageUnavailableError("storage unavailable") from error

    def create(self, data: CollectionIn) -> Collection:
        created_at = datetime.now(UTC).isoformat(timespec="seconds")
        try:
            with self._db() as db:
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
        except sqlite3.IntegrityError as error:
            raise _duplicate_or(error, data) from error
        return self.get(new_id)

    def get(self, collection_id: int) -> Collection | None:
        with self._db() as db:
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
        with self._db() as db:
            rows = db.execute(query, params).fetchall()
        return [_to_collection(row) for row in rows]

    def update(self, collection_id: int, data: CollectionIn) -> Collection | None:
        try:
            with self._db() as db:
                cursor = db.execute(
                    "UPDATE collections SET title = ?, category = ?, cart_url = ?, products = ?"
                    " WHERE id = ?",
                    (data.title, data.category, data.cart_url, _dump(data.products), collection_id),
                )
        except sqlite3.IntegrityError as error:
            raise _duplicate_or(error, data) from error
        return self.get(collection_id) if cursor.rowcount else None

    def delete(self, collection_id: int) -> bool:
        with self._db() as db:
            cursor = db.execute("DELETE FROM collections WHERE id = ?", (collection_id,))
        return cursor.rowcount > 0

    def categories(self) -> list[CategoryCount]:
        with self._db() as db:
            rows = db.execute(
                "SELECT category, COUNT(*) AS count FROM collections"
                " GROUP BY category ORDER BY category"
            ).fetchall()
        return [CategoryCount(category=row["category"], count=row["count"]) for row in rows]


def _duplicate_or(error: sqlite3.IntegrityError, data: CollectionIn) -> Exception:
    if "cart_url" in str(error):
        return DuplicateCartUrlError(f"cart_url {data.cart_url} already exists")
    return StorageUnavailableError("storage unavailable")


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
