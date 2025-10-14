import os
import sqlite3
from typing import List, Optional, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "stage_inventory.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the items table if it doesn't exist and run lightweight migrations."""
    with get_connection() as conn:
        # Items table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'General',
                crew_tag TEXT NOT NULL,
                location TEXT NOT NULL,
                in_use INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        # Locations table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );
            """
        )
        # Lightweight migration: ensure 'category' column exists for older DBs
        info = conn.execute("PRAGMA table_info(items)").fetchall()
        cols = {row[1] for row in info}  # second field is name
        if "category" not in cols:
            conn.execute("ALTER TABLE items ADD COLUMN category TEXT NOT NULL DEFAULT 'General'")

        # Simple trigger to keep updated_at fresh
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS trg_items_updated
            AFTER UPDATE ON items
            FOR EACH ROW
            BEGIN
                UPDATE items SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
            END;
            """
        )

        # Seed default locations if table is empty
        cur = conn.execute("SELECT COUNT(*) FROM locations")
        if cur.fetchone()[0] == 0:
            defaults = [
                ("West Campus Basement Storage",),
                ("East Campus Basement Storage",),
                ("East Campus Theatre Closet",),
            ]
            conn.executemany("INSERT OR IGNORE INTO locations(name) VALUES (?)", defaults)


def add_item(name: str, category: str, crew_tag: str, location: str, in_use: bool = False) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO items (name, category, crew_tag, location, in_use) VALUES (?, ?, ?, ?, ?)",
            (name, category, crew_tag, location, 1 if in_use else 0),
        )
        return cur.lastrowid


def update_item(item_id: int, name: str, category: str, crew_tag: str, location: str, in_use: bool) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE items SET name = ?, category = ?, crew_tag = ?, location = ?, in_use = ? WHERE id = ?",
            (name, category, crew_tag, location, 1 if in_use else 0, item_id),
        )


def set_in_use(item_id: int, in_use: bool) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE items SET in_use = ? WHERE id = ?", (1 if in_use else 0, item_id))


def delete_item(item_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM items WHERE id = ?", (item_id,))


def get_item(item_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def list_items(
    name_query: Optional[str] = None,
    categories: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    locations: Optional[List[str]] = None,
    in_use: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    """Return items matching optional filters."""
    where = []
    params: List[Any] = []

    if name_query:
        where.append("LOWER(name) LIKE ?")
        params.append(f"%{name_query.lower()}%")

    if categories:
        where.append(f"category IN ({','.join(['?'] * len(categories))})")
        params.extend(categories)

    if tags:
        where.append(f"crew_tag IN ({','.join(['?'] * len(tags))})")
        params.extend(tags)

    if locations:
        where.append(f"location IN ({','.join(['?'] * len(locations))})")
        params.extend(locations)

    if in_use is not None:
        where.append("in_use = ?")
        params.append(1 if in_use else 0)

    sql = "SELECT id, name, category, crew_tag, location, in_use, created_at, updated_at FROM items"
    if where:
        sql += " WHERE " + " AND ".join(where)

    sql += " ORDER BY name COLLATE NOCASE"

    with get_connection() as conn:
        cur = conn.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        # Normalize SQLite ints to Python bools for in_use
        for r in rows:
            r["in_use"] = bool(r["in_use"])
        return rows


def get_locations() -> List[str]:
    with get_connection() as conn:
        # Prefer managed locations table, fall back to distinct from items for legacy
        cur = conn.execute("SELECT name FROM locations ORDER BY name COLLATE NOCASE")
        rows = [r[0] for r in cur.fetchall()]
        if rows:
            return rows
        cur = conn.execute("SELECT DISTINCT location FROM items ORDER BY location COLLATE NOCASE")
        return [r[0] for r in cur.fetchall()]


def get_tags() -> List[str]:
    with get_connection() as conn:
        cur = conn.execute("SELECT DISTINCT crew_tag FROM items ORDER BY crew_tag COLLATE NOCASE")
        return [r[0] for r in cur.fetchall()]

def get_categories() -> List[str]:
    with get_connection() as conn:
        cur = conn.execute("SELECT DISTINCT category FROM items ORDER BY category COLLATE NOCASE")
        return [r[0] for r in cur.fetchall()]


def add_location(name: str) -> None:
    name = name.strip()
    if not name:
        return
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO locations(name) VALUES (?)", (name,))
