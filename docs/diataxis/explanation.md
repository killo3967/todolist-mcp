# Explanation: Architecture and Design Decisions

## What is this?

An [MCP](https://modelcontextprotocol.io) server that exposes ToDoList `.tdl` files as tools for AI agents. The agent can read, create, modify, search, and delete tasks as if using the desktop app, but via JSON-RPC over stdio.

## Project structure

```
src/
├── models.py    # Pydantic models (argument validation)
├── manager.py   # ToDoListManager (XML, CRUD, search, stats)
└── tools.py     # 16 @mcp.tool() functions (MCP handlers)
main.py          # Entry point
```

**Separation of concerns**:

| Module | Responsibility | Depends on |
|--------|---------------|------------|
| `models.py` | Define argument shapes (Pydantic) | — |
| `manager.py` | All business logic: XML parsing, CRUD, search, encode/decode | `models` |
| `tools.py` | Expose logic as MCP tools via `@mcp.tool()` | `manager`, `models` |

## How the .tdl file is resolved

The server decides which file to use with this priority:

1. `$TODOLIST_FILE` — environment variable (set by the MCP client)
2. `mcp_server.ini` — local file next to the script (if `active = yes`)
3. `~/todolist.tdl` — default fallback

This allows local development with an INI file without touching the MCP client config.

## How tests work

### Unit tests (`test/`)

Import `ToDoListManager` directly. Use in-memory XML (`ElementTree`), no real files. 80 tests.

### Contract tests (`test-contract/`)

Spawn the server as a subprocess and talk JSON-RPC over stdio. Verify the MCP contract from the outside, without knowing the implementation. 112 tests.

The `test_contract.tdl` file is a test `.tdl` with 6 tasks of known structure. Each test copies this file to a temp directory, starts the server pointing to the copy, and verifies mutations.

## Design decisions

### Why POSSTRING and not parent_id?

ToDoList uses `POSSTRING` (paths like `"1.2.3"`) to identify position in the hierarchy. We keep this native format rather than `parent_id` because:

- It is ToDoList's real format
- Agents can get the `pos_string` of a task via `get_task`
- Adding `parent_id` as an alternative would add complexity without real benefit

### Why is `add_comment` separate from `update_task`?

`update_task` replaces the entire description field. `add_comment` always appends. This separation prevents the data loss bug where an agent writes `description` without reading the existing one first.

### Why `backup_tdl` / `restore_tdl`?

Safety tools for big changes. The user (or agent) can backup before a destructive operation and restore if something goes wrong. The backup is saved as `file.tdl.bak` in the same directory.

### Why escape values in XPath queries?

`ElementTree` has no parameterized queries. If a `task_id` contains a single quote (`"it's"`), it breaks the XPath. We use `concat()` to safely escape the value.

## .tdl file format

ToDoList uses XML with nested `<TASK>` elements. Key fields:

```xml
<TASK ID="1" TITLE="My task" PRIORITY="2" PERCENTDONE="50" STATUS="In Progress">
  <CATEGORY>Work</CATEGORY>
  <ALLOCATEDTO>Alice</ALLOCATEDTO>
  <COMMENTS>Task notes</COMMENTS>
  <TAG>urgent</TAG>
</TASK>
```

Dates are stored as Excel serial numbers (days since 1899-12-30). Colors are stored as BGR integers (not RGB).
