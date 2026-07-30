# How-to Guide: Common Task Recipes

Step-by-step recipes for the most frequent operations with the ToDoList MCP server.

## Tasks

### Create a task

```json
{
  "name": "add_task",
  "arguments": {
    "args": {
      "title": "Review documentation",
      "priority": "High",
      "category": "Docs",
      "due_date": "2026-08-15"
    }
  }
}
```

### Create a subtask

Use `position` to indicate the parent:

```json
{
  "name": "add_task",
  "arguments": {
    "args": {
      "title": "Fix typos",
      "position": "3",
      "priority": "Normal"
    }
  }
}
```

`"position": "3"` adds the task as a child of the task at position 3.

### Mark a task as complete

```json
{
  "name": "complete_task",
  "arguments": {
    "args": {
      "task_id": "42",
      "status_text": "Done"
    }
  }
}
```

`complete_task` sets `percent_done=100` and the status in a single call.

### Add a comment (log entry)

```json
{
  "name": "add_comment",
  "arguments": {
    "args": {
      "task_id": "42",
      "comment": "2026-08-01 | 15:30 | Done | Fixed 3 typos in README."
    }
  }
}
```

`add_comment` **never replaces** — it always appends.

### Move a task in the hierarchy

```json
{
  "name": "move_task",
  "arguments": {
    "args": {
      "task_id": "42",
      "new_position": "5.1"
    }
  }
}
```

`"5.1"` = first child of the task at position 5.

### Delete a task

```json
{
  "name": "delete_task",
  "arguments": {
    "args": {
      "task_id": "42"
    }
  }
}
```

Deletes the task and all its children. Cannot be undone — use `backup_tdl` first.

## Search

### Search by text

```json
{ "name": "search_tasks", "arguments": { "args": { "search_term": "documentation" } } }
```

### Filter by status

```json
{ "name": "search_tasks", "arguments": { "args": { "status": "Pending" } } }
```

### Filter by priority

```json
{ "name": "search_tasks", "arguments": { "args": { "priority": "High" } } }
```

### Combine filters

```json
{
  "name": "search_tasks",
  "arguments": {
    "args": {
      "priority": "High",
      "completed": false,
      "category": "Docs"
    }
  }
}
```

## Safety

### Backup before big changes

```json
{ "name": "backup_tdl", "arguments": { "args": {} } }
```

Creates `your-file.tdl.bak` in the same directory.

### Restore if something goes wrong

```json
{ "name": "restore_tdl", "arguments": { "args": {} } }
```

## Statistics

### Get counts by status, priority, and category

```json
{ "name": "get_task_stats", "arguments": { "args": { "format": "markdown" } } }
```

### Check file health

```json
{ "name": "get_file_status", "arguments": { "args": {} } }
```

## Available fields

| Field | Type | Example |
|-------|------|---------|
| `title` | string | `"Review documentation"` |
| `description` | string | `"Fix typos and errors"` |
| `due_date` | string | `"2026-08-15"` |
| `start_date` | string | `"2026-08-01"` |
| `priority` | enum | `Low`, `Below Normal`, `Normal`, `Above Normal`, `High`, `Urgent` |
| `category` | string | `"Docs"` |
| `tags` | string | `"bug, urgent, frontend"` |
| `status` | string | `"Pending"`, `"In Progress"`, `"Done"` |
| `percent_done` | integer | `75` |
| `allocated_to` | string | `"Alice, Bob"` |
| `time_estimate` | float | `0.125` (3 hours) |
| `color` | string | `"#FF6B35"` |
