"""Note management tools (Pattern 1 — Compositional Design)."""

from mcp.server.fastmcp import Context

from productivity_mcp.db import get_db
from productivity_mcp.errors import ErrorCode, error_response, success_response
from productivity_mcp.tracing import traced


def register_tools(mcp):
    @mcp.tool()
    @traced
    async def create_note(
        title: str,
        ctx: Context,
        content: str = "",
        tags: str = "",
    ) -> dict:
        """Create a new note. Tags are comma-separated strings."""
        db = get_db(ctx)
        cursor = await db.execute(
            "INSERT INTO notes (title, content, tags) VALUES (?, ?, ?)",
            (title, content, tags),
        )
        await db.commit()
        return success_response({"id": cursor.lastrowid, "title": title, "tags": tags})

    @mcp.tool()
    @traced
    async def list_notes(ctx: Context, tag: str | None = None) -> dict:
        """List all notes, optionally filtered by tag."""
        db = get_db(ctx)
        if tag:
            rows = await db.execute_fetchall(
                "SELECT * FROM notes WHERE ',' || tags || ',' LIKE ? ORDER BY created_at DESC",
                (f"%,{tag},%",),
            )
        else:
            rows = await db.execute_fetchall("SELECT * FROM notes ORDER BY created_at DESC")
        return success_response([dict(r) for r in rows])

    @mcp.tool()
    @traced
    async def get_note(note_id: int, ctx: Context) -> dict:
        """Get a single note by ID."""
        db = get_db(ctx)
        row = await db.execute_fetchall("SELECT * FROM notes WHERE id = ?", (note_id,))
        if not row:
            return error_response(ErrorCode.NOT_FOUND, f"Note {note_id} not found")
        return success_response(dict(row[0]))

    @mcp.tool()
    @traced
    async def search_notes(query: str, ctx: Context) -> dict:
        """Search notes by title or content (case-insensitive substring match)."""
        db = get_db(ctx)
        pattern = f"%{query}%"
        rows = await db.execute_fetchall(
            "SELECT * FROM notes WHERE title LIKE ? OR content LIKE ? ORDER BY created_at DESC",
            (pattern, pattern),
        )
        return success_response([dict(r) for r in rows])

    @mcp.tool()
    @traced
    async def update_note(
        note_id: int,
        ctx: Context,
        title: str | None = None,
        content: str | None = None,
        tags: str | None = None,
    ) -> dict:
        """Update fields of an existing note."""
        db = get_db(ctx)
        existing = await db.execute_fetchall("SELECT * FROM notes WHERE id = ?", (note_id,))
        if not existing:
            return error_response(ErrorCode.NOT_FOUND, f"Note {note_id} not found")

        updates = {}
        if title is not None:
            updates["title"] = title
        if content is not None:
            updates["content"] = content
        if tags is not None:
            updates["tags"] = tags

        if not updates:
            return success_response(dict(existing[0]))

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        set_clause += ", updated_at = datetime('now')"
        values = list(updates.values())
        values.append(note_id)

        await db.execute(f"UPDATE notes SET {set_clause} WHERE id = ?", values)
        await db.commit()
        row = await db.execute_fetchall("SELECT * FROM notes WHERE id = ?", (note_id,))
        return success_response(dict(row[0]))

    @mcp.tool()
    @traced
    async def delete_note(note_id: int, ctx: Context) -> dict:
        """Delete a note by ID."""
        db = get_db(ctx)
        existing = await db.execute_fetchall("SELECT * FROM notes WHERE id = ?", (note_id,))
        if not existing:
            return error_response(ErrorCode.NOT_FOUND, f"Note {note_id} not found")
        await db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        await db.commit()
        return success_response({"deleted": note_id})
