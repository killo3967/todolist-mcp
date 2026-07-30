"""Hot tests for get_today_tasks MCP tool."""



def test_get_today_tasks_defaults_today(mcp):
    """Without target_date, returns tasks due today (should be empty in test data)."""
    client, _ = mcp
    result = client.call_tool("get_today_tasks", {})
    text = result["result"]["content"][0]["text"]
    # Task Delta has due_date 2026-01-01 — not today, so no tasks unless today is 2026-01-01
    if "No tasks" not in text:
        # If today is 2026-01-01, Delta should appear
        assert "Task Delta" in text


def test_get_today_tasks_specific_date_match(mcp):
    """Task Delta is due 2026-01-01."""
    client, _ = mcp
    result = client.call_tool("get_today_tasks", {"target_date": "2026-01-01"})
    text = result["result"]["content"][0]["text"]
    assert "Task Delta" in text


def test_get_today_tasks_specific_date_no_match(mcp):
    """2020-01-01 has no tasks due."""
    client, _ = mcp
    result = client.call_tool("get_today_tasks", {"target_date": "2020-01-01"})
    text = result["result"]["content"][0]["text"]
    assert "No tasks due" in text


def test_get_today_tasks_invalid_date(mcp):
    """Invalid date should return error message."""
    client, _ = mcp
    result = client.call_tool("get_today_tasks", {"target_date": "not-a-date"})
    text = result["result"]["content"][0]["text"]
    assert "Invalid date" in text


def test_get_today_tasks_json(mcp):
    """JSON format for a specific date."""
    client, _ = mcp
    result = client.call_tool("get_today_tasks", {
        "target_date": "2026-01-01",
        "format": "json",
    })
    import json
    data = json.loads(result["result"]["content"][0]["text"])
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == "6"
    assert data[0]["due_date"] == "2026-01-01"
