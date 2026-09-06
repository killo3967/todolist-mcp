"""Hot tests for search_tasks MCP tool — every filter variant."""


def test_search_by_term(mcp):
    client, _ = mcp
    result = client.call_tool("search_tasks", {"search_term": "Alpha"})
    text = result["result"]["content"][0]["text"]
    assert "Task Alpha" in text
    assert "Subtask Alpha-1" in text
    assert "Subtask Alpha-2" in text


def test_search_by_term_no_match(mcp):
    client, _ = mcp
    result = client.call_tool("search_tasks", {"search_term": "zzz_nonexistent"})
    assert "No tasks found" in result["result"]["content"][0]["text"]


def test_search_by_category(mcp):
    client, _ = mcp
    result = client.call_tool("search_tasks", {"category": "Personal"})
    text = result["result"]["content"][0]["text"]
    assert "Task Beta" in text
    assert "Task Alpha" not in text


def test_search_by_priority_high(mcp):
    client, _ = mcp
    result = client.call_tool("search_tasks", {"priority": "High"})
    text = result["result"]["content"][0]["text"]
    assert "Task Alpha" in text
    assert "Task Delta" in text
    assert "Task Beta" not in text  # Beta is Normal


def test_search_by_priority_low(mcp):
    client, _ = mcp
    result = client.call_tool("search_tasks", {"priority": "Low"})
    text = result["result"]["content"][0]["text"]
    assert "Task Gamma" in text  # Gamma is Low


def test_search_completed(mcp):
    client, _ = mcp
    result = client.call_tool("search_tasks", {"completed": True})
    text = result["result"]["content"][0]["text"]
    # Only top-level tasks are searched — children are NOT included
    assert "Task Gamma" in text
    # Subtask Alpha-1 is a child, not returned by flat search


def test_search_incomplete(mcp):
    client, _ = mcp
    result = client.call_tool("search_tasks", {"completed": False})
    text = result["result"]["content"][0]["text"]
    assert "Task Alpha" in text
    assert "Task Beta" in text
    assert "Task Gamma" not in text


def test_search_by_assigned_to(mcp):
    client, _ = mcp
    result = client.call_tool("search_tasks", {"assigned_to": "Alice"})
    text = result["result"]["content"][0]["text"]
    assert "Task Alpha" in text


def test_search_combined_filters(mcp):
    """High priority + not completed + Work category."""
    client, _ = mcp
    result = client.call_tool("search_tasks", {
        "priority": "High",
        "completed": False,
        "category": "Work",
    })
    text = result["result"]["content"][0]["text"]
    assert "Task Alpha" in text
    assert "Task Delta" not in text  # Delta has category "Urgent"


def test_search_json_format(mcp):
    client, _ = mcp
    result = client.call_tool("search_tasks", {
        "search_term": "Delta",
        "format": "json",
    })
    import json
    data = json.loads(result["result"]["content"][0]["text"])
    assert len(data) == 1
    assert data[0]["id"] == "6"


def test_search_with_description_search(mcp):
    """search_term should match in description/comments too."""
    client, _ = mcp
    result = client.call_tool("search_tasks", {"search_term": "Initial comment"})
    text = result["result"]["content"][0]["text"]
    assert "Task Alpha" in text  # Has "Initial comment for Alpha" in COMMENTS


def test_search_all_filters_no_match(mcp):
    """Filters that conflict should return no results."""
    client, _ = mcp
    result = client.call_tool("search_tasks", {
        "completed": False,
        "priority": "Low",
    })
    text = result["result"]["content"][0]["text"]
    # Gamma is Low but completed, Beta is Normal and incomplete — no match
    assert "No tasks found" in text


def test_search_nested_subtask_by_title(mcp):
    """Buscar por titulo debe encontrar tareas anidadas, no solo raiz."""
    client, _ = mcp
    result = client.call_tool("search_tasks", {"search_term": "Subtask Alpha-1"})
    text = result["result"]["content"][0]["text"]
    assert "Subtask Alpha-1" in text
    assert "Task Alpha" not in text
