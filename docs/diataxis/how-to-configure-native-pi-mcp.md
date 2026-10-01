# How-to: Configure Native Pi MCP

This guide explains how to register the ToDoList MCP server using Pi's native MCP configuration system.

## Overview

Instead of using the legacy `pi-mcp-adapter`, modern Pi environments use a centralized `mcp.json` file located in your Pi agent directory. This allows for better control, observability, and native integration with tools like `codemode` and `context-mode`.

## Step 1: Locate your configuration file

The configuration file is typically located at:
`C:\Users\<YourUsername>\.pi\agent\mcp.json`

## Step 2: Add the ToDoList Server

Open `mcp.json` in your preferred editor and add the `todolist` entry to the `mcpServers` object.

**Important:** You must provide the absolute path to your `main.py` and your `.tdl` file.

```json
{
  "mcpServers": {
    "todolist": {
      "command": "python",
      "args": ["C:/path/to/todolist-mcp/main.py"],
      "env": {
        "TODOLIST_FILE": "C:/path/to/your-tasks.tdl"
      },
      "exposure": "codemode"
    }
  }
}
```

### Configuration Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `command` | string | The executable to run (e.g., `python` or the full path to `python.exe`). |
| `args` | array | List of arguments passed to the command. Must include the path to `main.py`. |
| `env` | object | Environment variables. Use `TODOLIST_FILE` to specify your task file. |
| `exposure` | string | Controls how tools are visible. `codemode` is recommended for development. |

## Step 3: Verify the Connection

After saving the file, restart your Pi session or reload the agent. You can verify that the server is running correctly by using the following command in your terminal:

```bash
pi mcp list
```

You should see `todolist` listed with its connected tools (e.g., `add_task`, `complete_task`, etc.).

## Troubleshooting

### Server not appearing in `pi mcp list`

1. **Check the path**: Ensure the paths in `command` and `args` are absolute and correct.
2. **Check the JSON syntax**: A single missing comma or quote will cause the entire `mcp.json` to fail to load.
3. **Check environment variables**: Ensure `TODOLIST_FILE` points to a valid, existing `.tdl` file.
4. **Check Python environment**: If using a virtual environment, use the full path to the python executable inside the `venv` folder (e.g., `K:/todolist_mcp/venv/Scripts/python.exe`).

## Transitioning from `pi-mcp-adapter`

If you are migrating from the legacy adapter:
1. Copy your server configurations from `mcp-adapter.json` to `mcp.json`.
2. Remove the `pi-mcp-adapter` entry from your `mcp.json` or delete the adapter configuration entirely.
3. Note that the `exposure` parameter is a new requirement for native MCP.
