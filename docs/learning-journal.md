# Learning Journal: MCP Workshop Patterns

This document maps the 5 compositional architecture patterns from the MCP workshop to their implementations in this project.

## Pattern 1: Compositional Design

**Files:** `tools/tasks.py`, `tools/notes.py`, `tools/calendar.py`

Each tool is a small, atomic operation that does one thing well. Rather than building monolithic "manage tasks" tools, we decompose into `create_task`, `list_tasks`, `get_task`, `update_task`, `complete_task`, and `delete_task`. This allows an LLM to compose them freely — e.g., calling `list_tasks` then `complete_task` — without us having to predict every workflow.

**Key decisions:**
- Each tool module exports a `register_tools(mcp)` function for clean composition
- Tools return structured dicts so the LLM can reason about the data
- Optional parameters with sensible defaults keep each tool simple

## Pattern 2: Orchestrator Patterns

**File:** `orchestrators/daily.py`

Orchestrators combine multiple atomic tools into higher-level operations. `daily_summary` reads from both tasks and events to give a unified day view. `plan_day` goes further by organizing tasks around fixed events into a schedule suggestion.

**Key decisions:**
- Orchestrators query the database directly (same `get_db()` helper) rather than calling tools through MCP — this avoids unnecessary round-trips
- They still use `@traced` and return `success_response()` for consistency
- The `plan_day` tool provides a suggestion string alongside structured data, giving the LLM both raw data and a starting point for conversation

## Pattern 3: Structured Errors

**File:** `errors.py`

Every tool returns a consistent envelope: `{"success": true, "data": ...}` or `{"success": false, "error": {"code": "NOT_FOUND", "message": "..."}}`. The `ErrorCode` enum provides a fixed vocabulary (NOT_FOUND, VALIDATION_ERROR, CONFLICT, INTERNAL) that LLMs can pattern-match on.

**Key decisions:**
- Errors are returned as data (not exceptions) so the LLM always gets a structured response
- `ToolError` exception class exists for cases where you want to raise-and-catch internally
- The error code enum prevents typos and makes error handling consistent across all tools

## Pattern 4: Observability

**File:** `tracing.py`

The `@traced` decorator logs tool entry, exit, timing, and errors to stderr. Since MCP communicates over stdio, stderr is the correct channel for diagnostics — it won't interfere with the JSON-RPC protocol.

**Key decisions:**
- Logging goes to stderr via `logging.StreamHandler(sys.stderr)`
- The decorator measures wall-clock time with `time.perf_counter()`
- Every tool uses `@traced` — it's applied consistently below `@mcp.tool()` so the function signature is preserved for FastMCP's introspection

## Pattern 5: Best Practices (Lifespan + Composition Root)

**Files:** `db.py`, `server.py`

The `app_lifespan()` async context manager in `db.py` handles the database lifecycle: connect, enable WAL mode, initialize schema, yield the connection via context, and close on shutdown. The `server.py` composition root wires everything together — FastMCP instance, lifespan, and all tool registrations.

**Key decisions:**
- SQLite WAL mode for better concurrent read performance
- `get_db(ctx)` helper extracts the DB connection from MCP's request context, keeping tools decoupled from connection management
- The composition root (`server.py`) is intentionally thin — it's just wiring, not logic
- Schema initialization is idempotent (`CREATE TABLE IF NOT EXISTS`)

## Summary Table

| Pattern | What it teaches | Where to look |
|---------|----------------|---------------|
| 1. Compositional Design | Small, composable tools | `tools/*.py` |
| 2. Orchestrator Patterns | Multi-domain workflows | `orchestrators/daily.py` |
| 3. Structured Errors | Consistent error envelopes | `errors.py` |
| 4. Observability | Tracing + stderr logging | `tracing.py` |
| 5. Best Practices | Lifespan, composition root | `db.py`, `server.py` |
