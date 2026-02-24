"""Task management tools (Pattern 1 — Compositional Design)."""

from mcp.server.fastmcp import Context

from productivity_mcp.db import get_db
from productivity_mcp.errors import ErrorCode, ToolError, error_response, success_response
from productivity_mcp.tracing import traced


def register_tools(mcp):
    @mcp.tool()
    @traced
    async def create_task(
        title: str,
        ctx: Context,
        description: str = "",
        priority: str = "medium",
        due_date: str | None = None,
    ) -> dict:
        """Create a new task. Priority: low/medium/high. due_date: YYYY-MM-DD."""
        if priority not in ("low", "medium", "high"):
            return error_response(ErrorCode.VALIDATION_ERROR, "Priority must be low, medium, or high")
        db = get_db(ctx)
        cursor = await db.execute(
            "INSERT INTO tasks (title, description, priority, due_date) VALUES (?, ?, ?, ?)",
            (title, description, priority, due_date),
        )
        await db.commit()
        return success_response({"id": cursor.lastrowid, "title": title, "status": "todo", "priority": priority})

    @mcp.tool()
    @traced
    async def list_tasks(
        ctx: Context,
        status: str | None = None,
        priority: str | None = None,
    ) -> dict:
        """List tasks, optionally filtered by status (todo/in_progress/done) or priority."""
        db = get_db(ctx)
        query = "SELECT * FROM tasks WHERE 1=1"
        params: list = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if priority:
            query += " AND priority = ?"
            params.append(priority)
        query += " ORDER BY created_at DESC"
        rows = await db.execute_fetchall(query, params)
        return success_response([dict(r) for r in rows])

    @mcp.tool()
    @traced
    async def get_task(task_id: int, ctx: Context) -> dict:
        """Get a single task by ID."""
        db = get_db(ctx)
        row = await db.execute_fetchall("SELECT * FROM tasks WHERE id = ?", (task_id,))
        if not row:
            return error_response(ErrorCode.NOT_FOUND, f"Task {task_id} not found")
        return success_response(dict(row[0]))

    @mcp.tool()
    @traced
    async def update_task(
        task_id: int,
        ctx: Context,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        due_date: str | None = None,
    ) -> dict:
        """Update fields of an existing task."""
        db = get_db(ctx)
        existing = await db.execute_fetchall("SELECT * FROM tasks WHERE id = ?", (task_id,))
        if not existing:
            return error_response(ErrorCode.NOT_FOUND, f"Task {task_id} not found")
        if status and status not in ("todo", "in_progress", "done"):
            return error_response(ErrorCode.VALIDATION_ERROR, "Status must be todo, in_progress, or done")
        if priority and priority not in ("low", "medium", "high"):
            return error_response(ErrorCode.VALIDATION_ERROR, "Priority must be low, medium, or high")

        updates = {}
        if title is not None:
            updates["title"] = title
        if description is not None:
            updates["description"] = description
        if status is not None:
            updates["status"] = status
        if priority is not None:
            updates["priority"] = priority
        if due_date is not None:
            updates["due_date"] = due_date

        if not updates:
            return success_response(dict(existing[0]))

        updates["updated_at"] = "datetime('now')"
        set_clause = ", ".join(f"{k} = ?" for k in updates if k != "updated_at")
        set_clause += ", updated_at = datetime('now')"
        values = [v for k, v in updates.items() if k != "updated_at"]
        values.append(task_id)

        await db.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
        await db.commit()
        row = await db.execute_fetchall("SELECT * FROM tasks WHERE id = ?", (task_id,))
        return success_response(dict(row[0]))

    @mcp.tool()
    @traced
    async def complete_task(task_id: int, ctx: Context) -> dict:
        """Mark a task as done."""
        db = get_db(ctx)
        existing = await db.execute_fetchall("SELECT * FROM tasks WHERE id = ?", (task_id,))
        if not existing:
            return error_response(ErrorCode.NOT_FOUND, f"Task {task_id} not found")
        await db.execute(
            "UPDATE tasks SET status = 'done', updated_at = datetime('now') WHERE id = ?",
            (task_id,),
        )
        await db.commit()
        row = await db.execute_fetchall("SELECT * FROM tasks WHERE id = ?", (task_id,))
        return success_response(dict(row[0]))

    @mcp.tool()
    @traced
    async def delete_task(task_id: int, ctx: Context) -> dict:
        """Delete a task by ID."""
        db = get_db(ctx)
        existing = await db.execute_fetchall("SELECT * FROM tasks WHERE id = ?", (task_id,))
        if not existing:
            return error_response(ErrorCode.NOT_FOUND, f"Task {task_id} not found")
        await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        await db.commit()
        return success_response({"deleted": task_id})
