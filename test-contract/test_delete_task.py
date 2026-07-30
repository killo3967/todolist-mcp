"""Hot tests for delete_task MCP tool."""

import xml.etree.ElementTree as ET


def test_delete_existing_task(mcp):
    """Delete an existing task by ID."""
    client, tdl_path = mcp

    result = client.call_tool("delete_task", {"task_id": "4"})
    text = result["result"]["content"][0]["text"]
    assert "Successfully deleted" in text or "deleted" in text.lower()

    tree = ET.parse(tdl_path)
    assert tree.getroot().find(".//TASK[@ID='4']") is None


def test_delete_task_with_children(mcp):
    """Deleting a parent task also removes its children."""
    client, tdl_path = mcp

    result = client.call_tool("delete_task", {"task_id": "1"})
    assert "Successfully deleted" in result["result"]["content"][0]["text"] or \
           "deleted" in result["result"]["content"][0]["text"].lower()

    tree = ET.parse(tdl_path)
    assert tree.getroot().find(".//TASK[@ID='1']") is None
    assert tree.getroot().find(".//TASK[@ID='2']") is None  # child
    assert tree.getroot().find(".//TASK[@ID='3']") is None  # child


def test_delete_nonexistent_task(mcp):
    """Deleting a non-existent task should fail cleanly."""
    client, _ = mcp

    result = client.call_tool("delete_task", {"task_id": "999"})
    text = result["result"]["content"][0]["text"]
    assert "not found" in text.lower()


def test_delete_twice_fails(mcp):
    """Deleting the same task twice should fail on second attempt."""
    client, tdl_path = mcp

    client.call_tool("delete_task", {"task_id": "4"})
    result = client.call_tool("delete_task", {"task_id": "4"})
    assert "not found" in result["result"]["content"][0]["text"].lower()
