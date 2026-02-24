# Productivity MCP Server

A personal productivity MCP server built in Python that demonstrates the 5 compositional architecture patterns from the MCP workshop. Uses SQLite for persistence with three domains: **Tasks**, **Notes**, and **Calendar**.

## Installation

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e .
```

## Usage

### With Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "productivity": {
      "command": "/path/to/productivity-mcp/.venv/bin/productivity-mcp"
    }
  }
}
```

### With MCP Inspector

```bash
mcp dev src/productivity_mcp/server.py
```

### Direct stdio

```bash
productivity-mcp
```

## Tool Reference

### Tasks (6 tools)
| Tool | Description |
|------|-------------|
| `create_task` | Create a task with title, description, priority (low/medium/high), due_date |
| `list_tasks` | List tasks, filter by status or priority |
| `get_task` | Get a single task by ID |
| `update_task` | Update any task field |
| `complete_task` | Mark a task as done |
| `delete_task` | Delete a task |

### Notes (6 tools)
| Tool | Description |
|------|-------------|
| `create_note` | Create a note with title, content, tags (comma-separated) |
| `list_notes` | List notes, filter by tag |
| `get_note` | Get a single note by ID |
| `search_notes` | Search notes by title/content substring |
| `update_note` | Update any note field |
| `delete_note` | Delete a note |

### Calendar (5 tools)
| Tool | Description |
|------|-------------|
| `create_event` | Create event with title, date, start/end time |
| `list_events` | List events, filter by date or date range |
| `get_event` | Get a single event by ID |
| `update_event` | Update any event field |
| `delete_event` | Delete an event |

### Orchestrators (2 tools)
| Tool | Description |
|------|-------------|
| `daily_summary` | Combined view of events + tasks for a date |
| `plan_day` | Generate a time-blocked schedule suggestion |

## Configuration

Set `PRODUCTIVITY_MCP_DB` environment variable to change the database path (default: `productivity.db` in the working directory).

## Architecture

See [docs/learning-journal.md](docs/learning-journal.md) for how this project maps to the 5 MCP workshop patterns.
