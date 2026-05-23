# ─────────────────────────────────────────────
#  database.py  –  All SQLite interactions
# ─────────────────────────────────────────────

import aiosqlite
from typing import Optional

DB_PATH = "watchlist.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS shows (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                title         TEXT    NOT NULL,
                status        TEXT    NOT NULL DEFAULT 'planned',
                tags          TEXT    NOT NULL DEFAULT 'anime',
                added_by_id   INTEGER NOT NULL,
                added_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


def _tags_to_str(tags: list[str]) -> str:
    return ",".join(t.strip().lower() for t in tags if t.strip())

def tags_str_to_list(tags_str: str) -> list[str]:
    return [t for t in tags_str.split(",") if t] if tags_str else []


async def add_show(title: str, status: str, tags: list[str], added_by_id: int, added_by_name: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO shows (title, status, tags, added_by_id, added_by_name) VALUES (?, ?, ?, ?, ?)",
            (title, status, _tags_to_str(tags), added_by_id, added_by_name),
        )
        await db.commit()
        return cursor.lastrowid


async def update_show_status(show_id: int, new_status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE shows SET status = ? WHERE id = ?", (new_status, show_id))
        await db.commit()


async def update_show_tags(show_id: int, tags: list[str]):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE shows SET tags = ? WHERE id = ?", (_tags_to_str(tags), show_id))
        await db.commit()


async def delete_show(show_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM shows WHERE id = ?", (show_id,))
        await db.commit()


async def get_show_by_title(title: str) -> Optional[aiosqlite.Row]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM shows WHERE LOWER(title) = LOWER(?)", (title,))
        return await cursor.fetchone()


async def get_shows(status: Optional[str] = None, tag: Optional[str] = None) -> list[aiosqlite.Row]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM shows WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if tag:
            query += " AND (',' || tags || ',') LIKE ?"
            params.append(f"%,{tag.lower()},%")
        query += " ORDER BY title COLLATE NOCASE"
        cursor = await db.execute(query, params)
        return await cursor.fetchall()


async def get_all_titles() -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT title FROM shows ORDER BY title COLLATE NOCASE")
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

async def clear_all_shows():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM shows")
        await db.commit()
