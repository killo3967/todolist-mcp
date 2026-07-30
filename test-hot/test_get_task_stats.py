"""Feature 3: get_task_stats aggregation tool."""


def test_get_task_stats(mcp):
    client, _ = mcp
    result = client.call_tool("get_task_stats", {})
    text = result["result"]["content"][0]["text"]
    assert "Task Statistics" in text
    assert "By Status" in text
    assert "By Priority" in text
    assert "By Category" in text


def test_get_task_stats_json(mcp):
    client, _ = mcp
    result = client.call_tool("get_task_stats", {"format": "json"})
    import json
    data = json.loads(result["result"]["content"][0]["text"])
    assert "by_status" in data
    assert "by_priority" in data
    assert "by_category" in data
    assert "total" in data
    assert "completed" in data
    assert data["total"] >= 4
    assert isinstance(data["by_status"], dict)
