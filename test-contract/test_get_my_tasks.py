"""Hot tests for get_my_tasks MCP tool."""


def test_get_my_tasks_default_markdown(mcp):
    """Default format (markdown) returns all tasks."""
    client, _ = mcp
    result = client.call_tool("get_my_tasks", {})
    text = result["result"]["content"][0]["text"]
    assert "Task Alpha" in text
    assert "Task Beta" in text
    assert "Task Gamma" in text


def test_get_my_tasks_json(mcp):
    """JSON format returns parseable JSON with all tasks."""
    client, _ = mcp
    result = client.call_tool("get_my_tasks", {"format": "json"})
    text = result["result"]["content"][0]["text"]
    import json
    data = json.loads(text)
    ids = [t["id"] for t in data]
    assert "1" in ids
    assert "4" in ids
    assert "5" in ids


def test_get_my_tasks_has_children(mcp):
    """Task 1 should have nested children (2 and 3)."""
    client, _ = mcp
    result = client.call_tool("get_my_tasks", {"format": "json"})
    import json
    data = json.loads(result["result"]["content"][0]["text"])
    task1 = next(t for t in data if t["id"] == "1")
    child_ids = [c["id"] for c in task1.get("children", [])]
    assert "2" in child_ids
    assert "3" in child_ids
