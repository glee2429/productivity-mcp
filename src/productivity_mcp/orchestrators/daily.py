"""Daily orchestrators that combine multiple domains (Pattern 2 — Orchestrator Patterns)."""

from datetime import date

from mcp.server.fastmcp import Context

from productivity_mcp.db import get_db
from productivity_mcp.errors import success_response
from productivity_mcp.tracing import traced


def register_tools(mcp):
    @mcp.tool()
    @traced
    async def daily_summary(ctx: Context, date_str: str | None = None) -> dict:
        """Get a combined summary of tasks and events for a date (default: today).

        This is an orchestrator that reads from both the tasks and events tables
        to give a unified view of your day. date_str format: YYYY-MM-DD.
        """
        if date_str is None:
            date_str = date.today().isoformat()

        db = get_db(ctx)

        # Fetch events for the day
        events = await db.execute_fetchall(
            "SELECT * FROM events WHERE date = ? ORDER BY start_time",
            (date_str,),
        )

        # Fetch tasks due on this day
        due_tasks = await db.execute_fetchall(
            "SELECT * FROM tasks WHERE due_date = ? ORDER BY priority DESC",
            (date_str,),
        )

        # Fetch incomplete tasks (not tied to a specific date)
        open_tasks = await db.execute_fetchall(
            "SELECT * FROM tasks WHERE status != 'done' AND (due_date IS NULL OR due_date = '') ORDER BY priority DESC",
        )

        return success_response({
            "date": date_str,
            "events": [dict(r) for r in events],
            "due_tasks": [dict(r) for r in due_tasks],
            "open_tasks": [dict(r) for r in open_tasks],
            "summary": {
                "event_count": len(events),
                "due_task_count": len(due_tasks),
                "open_task_count": len(open_tasks),
            },
        })

    @mcp.tool()
    @traced
    async def plan_day(ctx: Context, date_str: str | None = None) -> dict:
        """Generate a time-blocked schedule from tasks and events for a date.

        This orchestrator reads events (fixed commitments) and open tasks,
        then suggests a schedule that fits tasks around existing events.
        date_str format: YYYY-MM-DD.
        """
        if date_str is None:
            date_str = date.today().isoformat()

        db = get_db(ctx)

        events = await db.execute_fetchall(
            "SELECT * FROM events WHERE date = ? ORDER BY start_time",
            (date_str,),
        )

        # Get tasks to schedule: due today or undated, not yet done
        tasks = await db.execute_fetchall(
            "SELECT * FROM tasks WHERE status != 'done' AND (due_date = ? OR due_date IS NULL OR due_date = '') ORDER BY priority DESC",
            (date_str,),
        )

        # Build time blocks: events are fixed, tasks fill the gaps
        schedule = []

        for event in events:
            schedule.append({
                "type": "event",
                "title": event["title"],
                "start_time": event["start_time"],
                "end_time": event["end_time"],
                "fixed": True,
            })

        # Priority order mapping for display
        priority_order = {"high": 1, "medium": 2, "low": 3}
        sorted_tasks = sorted(tasks, key=lambda t: priority_order.get(t["priority"], 2))

        task_blocks = []
        for task in sorted_tasks:
            task_blocks.append({
                "type": "task",
                "title": task["title"],
                "priority": task["priority"],
                "status": task["status"],
                "task_id": task["id"],
                "fixed": False,
            })

        return success_response({
            "date": date_str,
            "fixed_events": schedule,
            "tasks_to_schedule": task_blocks,
            "suggestion": (
                f"You have {len(schedule)} fixed event(s) and {len(task_blocks)} task(s) to work on. "
                f"Schedule high-priority tasks in your largest free blocks between events."
            ),
        })
