"""Calendar event tools (Pattern 1 — Compositional Design)."""

from mcp.server.fastmcp import Context

from productivity_mcp.db import get_db
from productivity_mcp.errors import ErrorCode, error_response, success_response
from productivity_mcp.tracing import traced


def register_tools(mcp):
    @mcp.tool()
    @traced
    async def create_event(
        title: str,
        date: str,
        ctx: Context,
        description: str = "",
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> dict:
        """Create a calendar event. date: YYYY-MM-DD, times: HH:MM (24h)."""
        db = get_db(ctx)
        cursor = await db.execute(
            "INSERT INTO events (title, description, date, start_time, end_time) VALUES (?, ?, ?, ?, ?)",
            (title, description, date, start_time, end_time),
        )
        await db.commit()
        return success_response({
            "id": cursor.lastrowid,
            "title": title,
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
        })

    @mcp.tool()
    @traced
    async def list_events(
        ctx: Context,
        date: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        """List events. Filter by exact date or date range (YYYY-MM-DD)."""
        db = get_db(ctx)
        query = "SELECT * FROM events WHERE 1=1"
        params: list = []
        if date:
            query += " AND date = ?"
            params.append(date)
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        query += " ORDER BY date, start_time"
        rows = await db.execute_fetchall(query, params)
        return success_response([dict(r) for r in rows])

    @mcp.tool()
    @traced
    async def get_event(event_id: int, ctx: Context) -> dict:
        """Get a single event by ID."""
        db = get_db(ctx)
        row = await db.execute_fetchall("SELECT * FROM events WHERE id = ?", (event_id,))
        if not row:
            return error_response(ErrorCode.NOT_FOUND, f"Event {event_id} not found")
        return success_response(dict(row[0]))

    @mcp.tool()
    @traced
    async def update_event(
        event_id: int,
        ctx: Context,
        title: str | None = None,
        description: str | None = None,
        date: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> dict:
        """Update fields of an existing event."""
        db = get_db(ctx)
        existing = await db.execute_fetchall("SELECT * FROM events WHERE id = ?", (event_id,))
        if not existing:
            return error_response(ErrorCode.NOT_FOUND, f"Event {event_id} not found")

        updates = {}
        if title is not None:
            updates["title"] = title
        if description is not None:
            updates["description"] = description
        if date is not None:
            updates["date"] = date
        if start_time is not None:
            updates["start_time"] = start_time
        if end_time is not None:
            updates["end_time"] = end_time

        if not updates:
            return success_response(dict(existing[0]))

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        set_clause += ", updated_at = datetime('now')"
        values = list(updates.values())
        values.append(event_id)

        await db.execute(f"UPDATE events SET {set_clause} WHERE id = ?", values)
        await db.commit()
        row = await db.execute_fetchall("SELECT * FROM events WHERE id = ?", (event_id,))
        return success_response(dict(row[0]))

    @mcp.tool()
    @traced
    async def delete_event(event_id: int, ctx: Context) -> dict:
        """Delete an event by ID."""
        db = get_db(ctx)
        existing = await db.execute_fetchall("SELECT * FROM events WHERE id = ?", (event_id,))
        if not existing:
            return error_response(ErrorCode.NOT_FOUND, f"Event {event_id} not found")
        await db.execute("DELETE FROM events WHERE id = ?", (event_id,))
        await db.commit()
        return success_response({"deleted": event_id})
