# TodoList MCP Server

> **Enhanced fork** of the original MCP by [ispyridis/todolist-mcp](https://github.com/ispyridis/todolist-mcp). Extended with 16 tools, backup/restore, stats, contract tests, and Diataxis documentation.

MCP server for managing [ToDoList](https://abstractspoon.com/) `.tdl` files. Tested with **ToDoList 9.2.4**.

## Differences from the original

| Original | This fork |
|----------|-----------|
| 10 tools | **16 tools** (complete_task, get_task_stats, backup_tdl, restore_tdl, delete_task, add_comment) |
| No tests | **192 tests** (80 unit + 112 contract MCP) |
| No type checking | **mypy + ruff + pyright** clean |
| Monolith | **src/ modular** (models, manager, tools) |
| No docs | **Diataxis** (tutorial, how-to, explanation, reference) |

## Quick start

```bash
git clone <repo-url>
cd todolist-mcp
python -m venv venv
venv\Scripts\pip install -r requirements.txt
python main.py
```

## Configuration

The server resolves the `.tdl` file with this priority:

1. `$TODOLIST_FILE` — environment variable (set by the MCP client)
2. `mcp_server.ini` — local file with `active = yes/no` toggle
3. `~/todolist.tdl` — default fallback

### MCP client

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

### Local development

```ini
# mcp_server.ini
[server]
active = yes
tdl_file = test-contract/test_contract.tdl
```

## Documentation

| Document | Type | Contents |
|----------|------|----------|
| [Tutorial](docs/diataxis/tutorial.md) | Tutorial | From zero to first command in 5 steps |
| [How-to Guide](docs/diataxis/how-to.md) | How-to | Recipes: create, search, comment, backup... |
| [Explanation](docs/diataxis/explanation.md) | Explanation | Architecture, design decisions, .tdl format |
| [API Reference](docs/diataxis/reference.md) | Reference | Complete 16-tool API with all parameters |

## Project structure

```
todolist-mcp/
├── main.py                     # Entry point
├── config.json.example         # MCP config template
├── mcp_server.ini.example      # Local override template
├── pyproject.toml              # mypy + ruff + pyright
├── requirements.txt
├── src/
│   ├── models.py               # Pydantic models
│   ├── manager.py              # ToDoListManager (XML, CRUD, stats)
│   └── tools.py                # 16 @mcp.tool() handlers
├── test/                       # 80 unit tests
├── test-contract/              # 112 MCP contract tests
├── docs/
│   └── diataxis/               # Diataxis documentation
├── .agent/skills/
│   └── todolist-mcp/           # Agent skill
└── README.md
```

## Tests

```bash
pytest test/ test-contract/ -q              # 192 tests
mypy src/ main.py test/ test-contract/      # Type checking
ruff check src/ main.py test/ test-contract/ # Linting
```

## License

Apache License 2.0 — see [LICENSE](LICENSE).
