# Reference: Complete MCP Tools API

Server `todolist-mcp-server` v0.5.0 — 16 tools over JSON-RPC 2.0 / stdio.

## Call format

All tools use this wrapper:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "tool_name",
    "arguments": {
      "args": {
        "param1": "value1"
      }
    }
  }
}
```

Arguments go inside `{"args": {...}}`.

## Read tools

### get_my_tasks

Returns all tasks from the main file, with full hierarchy.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `format` | `"markdown"` \| `"json"` | `"markdown"` | Output format |

### get_today_tasks

Tasks due on a specific date.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `target_date` | string \| null | `null` (today) | Date in `YYYY-MM-DD` |
| `format` | `"markdown"` \| `"json"` | `"markdown"` | Output format |

### get_task

A specific task with its children.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | string | ✅ | Task ID |
| `format` | `"markdown"` \| `"json"` | No | Output format |

### search_tasks

Search and filter tasks (top-level only, not recursive into children).

| Parameter | Type | Description |
|-----------|------|-------------|
| `search_term` | string | Searches title and description |
| `category` | string | Filter by category |
| `priority` | enum | `Low`, `Below Normal`, `Normal`, `Above Normal`, `High`, `Urgent` |
| `status` | string | Filter by status text |
| `completed` | boolean | `true` = completed, `false` = pending |
| `assigned_to` | string | Filter by assigned person |
| `format` | `"markdown"` \| `"json"` | Output format |

### get_file_status

File statistics: project, version, task counts. No parameters.

### read_any_tdl_file

Read any `.tdl` file (with path traversal protection).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_path` | string | ✅ | Absolute path to `.tdl` |
| `format` | `"markdown"` \| `"json"` | No | Output format |

### analyze_structure

XML structure diagnostic: metadata, counts, sample attributes. No parameters.

### get_task_stats

Aggregated counts by status, priority, and category.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `format` | `"markdown"` \| `"json"` | `"markdown"` | Output format |

## Write tools

### add_task

Create a new task.

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `title` | string | ✅ | — |
| `position` | string | No | Top-level |
| `description` | string | No | — |
| `due_date` | string | No | — |
| `start_date` | string | No | — |
| `priority` | enum | No | `"Normal"` |
| `category` | string | No | — |
| `status` | string | No | — |
| `time_estimate` | float | No | — |
| `color` | string | No | — |
| `tags` | string | No | — |

### update_task

Modify fields of an existing task. Pass `""` to clear a field.

| Parameter | Type | Required |
|-----------|------|----------|
| `task_id` | string | ✅ |
| `title` | string | No |
| `description` | string | No |
| `due_date` | string | No |
| `start_date` | string | No |
| `priority` | enum | No |
| `category` | string | No |
| `tags` | string | No |
| `status` | string | No |
| `percent_done` | integer | No |
| `allocated_to` | string | No |
| `time_estimate` | float | No |
| `color` | string | No |

### complete_task

Mark a task as done (shortcut: `percent_done=100` + status).

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `task_id` | string | ✅ | — |
| `status_text` | string | No | `"Completed"` |

### add_comment

Append text to the description. **Never replaces**.

| Parameter | Type | Required |
|-----------|------|----------|
| `task_id` | string | ✅ |
| `comment` | string | ✅ |

### move_task

Move a task to a different position in the hierarchy.

| Parameter | Type | Required |
|-----------|------|----------|
| `task_id` | string | ✅ |
| `new_position` | string | ✅ |

### delete_task

Delete a task and all its children.

| Parameter | Type | Required |
|-----------|------|----------|
| `task_id` | string | ✅ |

### backup_tdl

Create a backup of the current `.tdl` as `.tdl.bak`. No parameters.

### restore_tdl

Restore the `.tdl` from the last backup. No parameters.

## Priority values

`Low`, `Below Normal`, `Normal`, `Above Normal`, `High`, `Urgent`

## Date format

All dates use `YYYY-MM-DD`. To clear a date, pass an empty string `""`.

## Colors

Hex RGB format: `"#FF6B35"`. ToDoList internally stores BGR — the server converts automatically.

## Common errors

| Error | Cause |
|-------|-------|
| `"Unknown tool"` | The tool name does not exist |
| `"Task with ID 'X' not found"` | The `task_id` does not exist |
| `"No backup found"` | `restore_tdl` without prior `backup_tdl` |
| `"Path traversal blocked"` | `read_any_tdl_file` with `..` in the path |
