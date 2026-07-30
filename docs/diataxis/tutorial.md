# Tutorial: Getting Started with the ToDoList MCP Server

This tutorial walks you from zero to a working MCP server managing your ToDoList tasks through an AI agent.

## Prerequisites

- Python 3.10 or higher
- [AbstractSpoon ToDoList](https://abstractspoon.com/) installed
- An existing `.tdl` file (created by the ToDoList application)

## 1. Installation

```bash
git clone <repo-url>
cd todolist-mcp
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

Verify it works:

```bash
python main.py
```

The server waits for commands on stdin. Press Ctrl+C to stop for now.

## 2. Configure your task file

The server needs to know where your `.tdl` file is. Three options, by priority:

**Option A — Environment variable (recommended for production)**

Set `TODOLIST_FILE` in your MCP client config:

```json
{
  "mcpServers": {
    "todolist": {
      "command": "python",
      "args": ["path/to/todolist-mcp/main.py"],
      "env": {
        "TODOLIST_FILE": "path/to/your-file.tdl"
      }
    }
  }
}
```

**Option B — Local INI file (recommended for development)**

Create `mcp_server.ini` next to `main.py`:

```ini
[server]
active = yes
tdl_file = test-contract/test_contract.tdl
```

Set `active = no` to disable and fall through to the env var or default.

**Option C — Default**

If no env var or INI is set, the server uses `~/todolist.tdl`.

## 3. Connect your agent

Add the config to your MCP client and restart it. The server starts automatically when the agent needs it.

## 4. First operations

Ask your agent to list your tasks:

> "Show me my ToDoList tasks"

Or use the tools directly:

- `get_my_tasks` — all tasks
- `get_today_tasks` — today's tasks only
- `add_task` — create a new task
- `search_tasks` — search by text, status, priority...

## 5. Next steps

- Read the [How-to Guide](how-to.md) for step-by-step recipes
- Check the [API Reference](reference.md) for all 16 tools and parameters
- Read the [Architecture Explanation](explanation.md) to understand the internal design
