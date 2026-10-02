---
name: todolist-mcp
description: "Trigger: MCP todolist, tdl, ToDoList, tasks, add_task, update_task, complete_task, search_tasks, get_task_stats, todolist tool. MCP server for ToDoList (.tdl) files. Load before calling any todolist_* tool — flat argument shape, exact parameter formats."
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "2.1"
---

## Activation Contract

Load this skill before ANY call to the `todolist` MCP server (`todolist_*` or `mcp__todolist__*`). The server manages ToDoList `.tdl` XML files over stdio JSON-RPC and exposes 17 tools. Every mutation is written to the `.tdl` file immediately; ToDoList Desktop does not need to be running.

## Which server are you calling?

Both entry points in this repository run the same server, so the argument shape is flat either way:

| Entry point | What it is |
|---|---|
| `main.py` | Canonical entry point — `src/tools.py`, 17 tools |
| `tdl_mcp_server.py` (repo root) | 9-line compatibility shim that imports the same `src.tools.mcp` |

The nested `{"args": {...}}` shape belongs to the **old upstream monolith**, which this fork no longer ships. You meet it only when an MCP client points at a stale copy of that file kept outside the repository, such as a local `.local/todolist-mcp/tdl_mcp_server_patched.py`.

If a call fails with an unknown-parameter error or `Field required: args`, check the path your client actually runs:

```bash
grep "from src.tools import mcp" <configured-file>
```

A match means the flat contract in this skill applies. No match means you are running the legacy monolith, which needs the extra `args` wrapper.

## Hard Rules

1. **Flat arguments.** Pass parameters directly, one level deep: `mcp({tool: "todolist_get_task", args: {task_id: "42"}})`. Do not nest a second `args` object — the tool receives it as an unexpected parameter and validation fails.
2. **`task_id` accepts a string or an integer.** Use `"42"` for consistency with the `.tdl` XML, where IDs are strings.
3. **`position` and `new_position` are PARENT paths**, not insert-before targets. `"5"` appends as a child of task at position 5; `"2.3"` targets the third child of task 2.
4. **Dates are `YYYY-MM-DD`** — for `due_date`, `start_date` and `target_date`. An invalid format is silently dropped, not rejected. ToDoList *displays* `DD/MM/YYYY`, but the API never accepts that form.
5. **`priority` is a closed set:** `Low`, `Below Normal`, `Normal`, `Above Normal`, `High`, `Urgent`.
6. **`percent_done` is an int 0–100**; `time_estimate` is a float in days (`0.125` = 3h, `0.25` = 6h, `1.0` = 1 day).
7. **`add_comment` always appends.** `update_task` with `description` **replaces** the entire body — use `add_comment` for logs.

## Decision Gates

| Situation | Action |
|-----------|--------|
| Need all tasks | `get_my_tasks` |
| Need tasks due on a date | `get_today_tasks` (`target_date`) |
| Read one task + children | `get_task` (`task_id`) |
| Find tasks by text or filter | `search_tasks` |
| Create a task | `add_task` (`title` required) |
| Modify a task | `update_task` (`task_id` required) |
| Mark a task done | `complete_task` (`task_id`, optional `status_text`) |
| Append a log entry | `add_comment` (`task_id`, `comment`) |
| Delete a task | `delete_task` (`task_id`) |
| Rearrange hierarchy | `move_task` (`task_id`, `new_position`) |
| Counts by status/priority | `get_task_stats` |
| Check the .tdl file | `get_file_status` |
| Read another .tdl | `read_any_tdl_file` (`file_path`) |
| Inspect XML structure | `analyze_structure` |
| Back up / restore | `backup_tdl` / `restore_tdl` |
| Diagnose the server | `get_server_logs` (`lines`, default 100) |
| Tool rejects an unknown parameter | Check for a nested `args` wrapper (Rule 1) |
| A date is ignored with no error | Use `YYYY-MM-DD` (Rule 4) |

## Execution Steps

### Tool signatures

`*` marks a required parameter. Every `format` parameter accepts `markdown` or `json` and defaults to `json` — set it explicitly when you need to parse the output.

| Tool | Parameters |
|---|---|
| `get_my_tasks` | `format` |
| `get_today_tasks` | `target_date`, `format` |
| `get_task` | `task_id*`, `format` |
| `search_tasks` | `search_term`, `category`, `priority`, `completed`, `status`, `allocated_to`, `format` |
| `get_task_stats` | `format` |
| `get_file_status` | — |
| `analyze_structure` | — |
| `read_any_tdl_file` | `file_path*`, `format` |
| `add_task` | `title*`, `position`, `description`, `due_date`, `start_date`, `priority`, `category`, `status`, `time_estimate`, `color`, `tags`, `icon` |
| `update_task` | `task_id*`, plus every `add_task` field and `percent_done`, `allocated_to` |
| `complete_task` | `task_id*`, `status_text` (default `Completed`) |
| `add_comment` | `task_id*`, `comment*` |
| `delete_task` | `task_id*` |
| `move_task` | `task_id*`, `new_position*` |
| `backup_tdl` / `restore_tdl` | — |
| `get_server_logs` | `lines` |

### Call format

```js
mcp({tool: "todolist_get_task", args: {task_id: "42"}})
mcp({tool: "todolist_add_task", args: {title: "Fix cover", priority: "High", due_date: "2026-08-15"}})
```

The wire-level JSON-RPC request still carries `params.arguments`, but your client builds that from `args`. One level only.

### Creating a task

```json
{"title": "Task title (required)",
 "position": "2.3",
 "description": "Long description",
 "due_date": "2026-08-15",
 "start_date": "2026-08-01",
 "priority": "High",
 "category": "work",
 "status": "In Progress",
 "time_estimate": 0.125,
 "color": "#FF6B35",
 "tags": "invoice",
 "icon": 1}
```

- `color` is hex RGB; the server converts it to ToDoList's BGR integer.
- `status` is free text and is stored verbatim.
- Clear a field by passing `""` (`due_date`, `category`, `allocated_to`, `color`, `tags`).

### Updating a task

```json
{"task_id": "42",
 "percent_done": 50,
 "status": "In Progress",
 "due_date": "2026-08-15"}
```

Only the fields you send change. `description` is the exception: it replaces the whole body.

### Appending a comment

```json
{"task_id": "42", "comment": "### 2026-10-02 | 11:30 | Note | what happened"}
```

## Output Contract

All tools return a plain string in `content[0].text`. For `format: "json"` the text is a JSON document to parse; otherwise it is hierarchical markdown. Write tools return a success or `Error` message string. Failures arrive as text with an `Error` prefix rather than as a JSON-RPC error, so always inspect the payload before assuming success. `get_task` on a missing id returns `Error: Task with ID 'X' not found.`

## Install

Copy this folder into a skills directory so the agent loads it automatically:

- Global: `~/.agents/skills/todolist-mcp/`
- Per project: `<project>/.agent/skills/todolist-mcp/`

## References

- `references/tool-schemas.json` — full JSON input schemas for all 17 tools, captured from the running server.
- `src/tools.py` — authoritative tool signatures; check here when a parameter is unclear.
- `../../../docs/diataxis/reference.md` — human-facing tool reference and JSON-RPC call format.
- `../../../docs/diataxis/how-to-configure-native-pi-mcp.md` — register the server with Pi.
