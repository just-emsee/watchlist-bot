# ─────────────────────────────────────────────
#  database.py  –  All SQLite interactions
# ─────────────────────────────────────────────

import os
import aiosqlite
from typing import Optional


DB_PATH = os.getenv("DB_PATH", "watchlist.db")


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS shows (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id      INTEGER NOT NULL,
                title         TEXT    NOT NULL,
                status        TEXT    NOT NULL DEFAULT 'planned',
                tags          TEXT    NOT NULL DEFAULT '',
                added_by_id   INTEGER NOT NULL,
                added_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


def _tags_to_str(tags: list[str]) -> str:
    return ",".join(t.strip().lower() for t in tags if t.strip())

def tags_str_to_list(tags_str: str) -> list[str]:
    return [t for t in tags_str.split(",") if t] if tags_str else []


async def add_show(guild_id: int, title: str, status: str, tags: list[str], added_by_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO shows (guild_id, title, status, tags, added_by_id) VALUES (?, ?, ?, ?, ?)",
            (guild_id, title, status, _tags_to_str(tags), added_by_id),
        )
        await db.commit()
        return cursor.lastrowid


async def update_show_status(guild_id: int, show_id: int, new_status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE shows SET status = ? WHERE id = ? AND guild_id = ?", (new_status, show_id, guild_id))
        await db.commit()


async def update_show_tags(guild_id: int, show_id: int, tags: list[str]):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE shows SET tags = ? WHERE id = ? AND guild_id = ?", (_tags_to_str(tags), show_id, guild_id))
        await db.commit()


async def delete_show(guild_id: int, show_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM shows WHERE id = ? AND guild_id = ?", (show_id, guild_id))
        await db.commit()


async def clear_all_shows(guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM shows WHERE guild_id = ?", (guild_id,))
        await db.commit()

async def update_show_title(guild_id: int, show_id: int, new_title: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE shows SET title = ? WHERE id = ? AND guild_id = ?", (new_title, show_id, guild_id))
        await db.commit()

async def get_show_by_title(guild_id: int, title: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM shows WHERE guild_id = ? AND LOWER(title) = LOWER(?)", (guild_id, title)
        )
        return await cursor.fetchone()


async def get_shows(guild_id: int, status: str = None, tag: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM shows WHERE guild_id = ?"
        params = [guild_id]
        if status:
            query += " AND status = ?"
            params.append(status)
        if tag:
            query += " AND (',' || tags || ',') LIKE ?"
            params.append(f"%,{tag.lower()},%")
        query += " ORDER BY title COLLATE NOCASE"
        cursor = await db.execute(query, params)
        return await cursor.fetchall()


async def get_all_titles(guild_id: int) -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT title FROM shows WHERE guild_id = ? ORDER BY title COLLATE NOCASE", (guild_id,)
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


