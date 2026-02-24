"""SQLite database setup with lifespan management (Pattern 5 — Best Practices)."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import aiosqlite

DB_PATH = os.environ.get("PRODUCTIVITY_MCP_DB", "productivity.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'todo',
    priority TEXT NOT NULL DEFAULT 'medium',
    due_date TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL DEFAULT '',
    tags TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    date TEXT NOT NULL,
    start_time TEXT,
    end_time TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


async def init_schema(db: aiosqlite.Connection) -> None:
    await db.executescript(SCHEMA)
    await db.commit()


@asynccontextmanager
async def app_lifespan(server) -> AsyncIterator[dict]:
    """Async context manager for FastMCP lifespan — opens DB, yields context, closes."""
    db = await aiosqlite.connect(DB_PATH)
    await db.execute("PRAGMA journal_mode=WAL")
    db.row_factory = aiosqlite.Row
    await init_schema(db)
    try:
        yield {"db": db}
    finally:
        await db.close()


def get_db(ctx) -> aiosqlite.Connection:
    """Extract the database connection from the MCP request context."""
    return ctx.request_context.lifespan_context["db"]
