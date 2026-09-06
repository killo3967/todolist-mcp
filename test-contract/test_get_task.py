"""Hot tests for get_task MCP tool."""


def test_get_task_markdown(mcp):
    """Get a single task in markdown format."""
    client, _ = mcp
    result = client.call_tool("get_task", {"task_id": "1"})
    text = result["result"]["content"][0]["text"]
    assert "Task Alpha" in text
    assert "Subtask Alpha-1" in text
    assert "Subtask Alpha-2" in text


def test_get_task_json(mcp):
    """Get a single task in JSON format."""
    client, _ = mcp
    result = client.call_tool("get_task", {
        "task_id": "1",
        "format": "json",
    })
    import json
    data = json.loads(result["result"]["content"][0]["text"])
    assert isinstance(data, list)
    assert data[0]["id"] == "1"
    assert data[0]["title"] == "Task Alpha"
    assert len(data[0]["children"]) == 2


def test_get_task_with_due_date(mcp):
    """Task Delta has due_date 2026-01-01."""
    client, _ = mcp
    result = client.call_tool("get_task", {
        "task_id": "6",
        "format": "json",
    })
    import json
    data = json.loads(result["result"]["content"][0]["text"])
    assert data[0]["due_date"] == "2026-01-01"


def test_get_task_completed(mcp):
    """Task Gamma is completed."""
    client, _ = mcp
    result = client.call_tool("get_task", {
        "task_id": "5",
        "format": "json",
    })
    import json
    data = json.loads(result["result"]["content"][0]["text"])
    assert data[0]["completed"] is True
    assert data[0]["status"] == "Terminado"


def test_get_task_nonexistent(mcp):
    client, _ = mcp
    result = client.call_tool("get_task", {"task_id": "999"})
    assert "not found" in result["result"]["content"][0]["text"]


def test_get_task_child(mcp):
    """Get a nested subtask directly by ID."""
    client, _ = mcp
    result = client.call_tool("get_task", {
        "task_id": "2",
        "format": "json",
    })
    import json
    data = json.loads(result["result"]["content"][0]["text"])
    assert data[0]["id"] == "2"
    assert data[0]["title"] == "Subtask Alpha-1"


def test_get_task_int_id(mcp):
    """task_id entero debe coercionarse a string automaticamente."""
    client, _ = mcp
    result = client.call_tool("get_task", {"task_id": 1})
    text = result["result"]["content"][0]["text"]
    assert "Task Alpha" in text
