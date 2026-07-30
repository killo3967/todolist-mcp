"""Feature 1: search_tasks now supports status filter."""


def test_search_by_status_pendiente(mcp):
    client, _ = mcp
    result = client.call_tool("search_tasks", {"status": "Pendiente"})
    text = result["result"]["content"][0]["text"]
    assert "Task Alpha" in text  # STATUS="Pendiente"


def test_search_by_status_completed(mcp):
    client, _ = mcp
    result = client.call_tool("search_tasks", {"status": "Terminado"})
    text = result["result"]["content"][0]["text"]
    assert "Task Gamma" in text  # STATUS="Terminado"


def test_search_status_combined(mcp):
    """Above Normal + En curso should find Subtask Alpha-2.
    Note: search_tasks only matches top-level tasks, not children."""
    client, _ = mcp
    result = client.call_tool("search_tasks", {
        "status": "En curso",
        "priority": "Above Normal",
    })
    text = result["result"]["content"][0]["text"]
    # Subtask Alpha-2 is a child of Task Alpha, not top-level
    assert "No tasks found" in text


def test_search_status_no_match(mcp):
    """No task has status 'Inexistente'."""
    client, _ = mcp
    result = client.call_tool("search_tasks", {"status": "Inexistente"})
    assert "No tasks found" in result["result"]["content"][0]["text"]
