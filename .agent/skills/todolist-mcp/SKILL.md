---
name: todolist-mcp
description: "Trigger: MCP todolist, tdl, tasks, ToDoList, add_task, update_task, complete_task, search_tasks, get_my_tasks, get_task_stats, todolist tool. MCP server for ToDoList (.tdl) files. Load before calling any todolist_* tool."
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## Activation Contract

Load this skill before ANY call to the `todolist` MCP server. The server manages ToDoList (.tdl) XML files via 13 tools over stdio JSON-RPC. All mutations persist to the `.tdl` file immediately. Do not assume ToDoList Desktop is running — changes are direct to the XML file.

## Hard Rules

1. **Always wrap args**: every tool call must pass `{"args": {"param": "value", ...}}`, never flat arguments.
2. **`task_id` is always a string**, never an integer (e.g. `"42"`, not `42`).
3. **`position` is always the PARENT path**, not an insert-before target. `"5"` appends as child of task 5.
4. **`add_comment` never replaces** — it always appends to the existing description.
5. **Date format**: always `YYYY-MM-DD` for `due_date` and `start_date`.
6. **Priority values**: `Low`, `Below Normal`, `Normal`, `Above Normal`, `High`, `Urgent`.
7. **Clear a field**: pass an empty string `""` for `due_date`, `category`, `allocated_to`, `color`, `start_date`, `tags`. Pass `"0"` for `priority` (Normal).

## Decision Gates

| Situation | Action |
|-----------|--------|
| Need all tasks | `get_my_tasks` (markdown default, or `json`) |
| Need tasks due today | `get_today_tasks` |
| Create a new task | `add_task` (title required, rest optional) |
| Modify existing task | `update_task` (task_id required) |
| Mark task done | `complete_task` (sets progress=100, status) |
| Add text to task | `add_comment` (appends, never replaces) |
| Find tasks | `search_tasks` (term, category, priority, status, completed, assigned_to) |
| Rearrange hierarchy | `move_task` |
| Inspect one task | `get_task` |
| File health check | `get_file_status` |
| Read any .tdl file | `read_any_tdl_file` |
| Inspect XML structure | `analyze_structure` |
| Counts by status/priority | `get_task_stats` |

## Execution Steps

## Execution Steps

### Configuration

#### Standard Configuration (via `mcp_server.ini`)
The server resolves the `.tdl` file path with priority:
1. `$TODOLIST_FILE` environment variable (set by MCP client config)
2. `mcp_server.ini` next to the server script (if `active = yes`)
3. Hardcoded fallback

For local dev, create `mcp_server.ini`:
```ini
[server]
active = yes
tdl_file = test-contract/test_contract.tdl
```

#### Native Pi MCP Configuration
To register the server natively in Pi, add it to your `~/.pi/agent/mcp.json`:

```json
{
  "mcpServers": {
    "todolist": {
      "command": "python",
      "args": ["path/to/todolist-mcp/main.py"],
      "env": {
        "TODOLIST_FILE": "path/to/your-file.tdl"
      },
      "exposure": "codemode"
    }
  }
}
```


### Tool Reference

#### Read tools

**get_my_tasks** — all tasks, hierarchical
- `format`: `"markdown"` (default) | `"json"`

**get_today_tasks** — tasks due on a date
- `target_date`: `"YYYY-MM-DD"` (optional, defaults to today)
- `format`: `"markdown"` (default) | `"json"`

**get_task** — one task + its children
- `task_id` *required*: task ID string
- `format`: `"markdown"` (default) | `"json"`

**search_tasks** — filter tasks
- `search_term`: free text (matches title + description)
- `category`: filter by category name
- `priority`: `Low` | `Below Normal` | `Normal` | `Above Normal` | `High` | `Urgent`
- `status`: filter by status text (e.g. `"Pendiente"`, `"En curso"`)
- `completed`: `true` | `false`
- `assigned_to`: filter by person name
- `format`: `"markdown"` (default) | `"json"`

**get_file_status** — file statistics (no parameters)

**read_any_tdl_file** — read any .tdl file
- `file_path` *required*: absolute path to .tdl file
- `format`: `"markdown"` (default) | `"json"`

**analyze_structure** — XML structure diagnostic (no parameters)

**get_task_stats** — counts by status, priority, category
- `format`: `"markdown"` (default) | `"json"`

#### Write tools

**add_task** — create a task
- `title` *required*: task title string
- `position`: parent path (e.g. `"3"` = child of task at position 3)
- `description`: task description text
- `due_date`: `"YYYY-MM-DD"`
- `priority`: one of the 6 priority values (default: `Normal`)
- `category`: category/project name
- `status`: status text (e.g. `"Pendiente"`, `"En curso"`)
- `time_estimate`: days as float (e.g. `0.125` = 3 hours)
- `color`: hex RGB string (e.g. `"#FF6B35"`)

**update_task** — modify any field
- `task_id` *required*: task ID to update
- All optional fields from `add_task` plus:
- `percent_done`: 0–100 integer
- `allocated_to`: person name(s), comma-separated
- `tags`: comma-separated tags (e.g. `"bug, urgent"`)

**complete_task** — mark task done
- `task_id` *required*: task ID
- `status_text`: status to set (default: `"Completed"`)

**add_comment** — append text to description
- `task_id` *required*: task ID
- `comment` *required*: text to append

**move_task** — reposition in hierarchy
- `task_id` *required*: task ID to move
- `new_position` *required*: target position (e.g. `"2.1"` = child of pos 2, index 1)

### MCP Call Format

All tools use this JSON-RPC shape:
```json
{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "tool_name", "arguments": {"args": {"param": "value"}}}}
```

## Output Contract

All tools return a string in the `content[0].text` field of the response. For `json` format tools, parse the text with `JSON.parse()` or `json.loads()`. Write tools return a success/error message string. Read errors return the error text directly.

## References

- `references/tool-schemas.json` — full JSON schemas for all 13 tools (generated from server)
- Server source: `K:/todolist_mcp/tdl_mcp_server.py`
- Test data: `K:/todolist_mcp/test-contract/test_contract.tdl`
