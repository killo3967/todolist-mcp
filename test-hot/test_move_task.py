"""Hot tests for move_task MCP tool."""

import xml.etree.ElementTree as ET


def test_move_task_within_same_parent(mcp):
    """Move ID=3 (Subtask Alpha-2, pos 1.2) before ID=2 (Subtask Alpha-1, pos 1.1)."""
    client, tdl_path = mcp
    result = client.call_tool("move_task", {
        "task_id": "3",
        "new_position": "1.1",
    })
    assert "Successfully moved" in result["result"]["content"][0]["text"]

    tree = ET.parse(tdl_path)
    parent = tree.getroot().find(".//TASK[@ID='1']")
    children = parent.findall("./TASK")
    assert children[0].get("ID") == "3"
    assert children[1].get("ID") == "2"


def test_move_task_to_top_level(mcp):
    """Move ID=3 (child of 1) to top level, position 2."""
    client, tdl_path = mcp
    result = client.call_tool("move_task", {
        "task_id": "3",
        "new_position": "2",
    })
    assert "Successfully moved" in result["result"]["content"][0]["text"]

    tree = ET.parse(tdl_path)
    root = tree.getroot()
    top = root.findall("./TASK")
    assert len([t for t in top if t.get("ID") == "3"]) == 1
    assert top[1].get("ID") == "3"


def test_move_task_to_child_position(mcp):
    """Move top-level ID=4 to become child of ID=1 at position 1.1."""
    client, tdl_path = mcp
    result = client.call_tool("move_task", {
        "task_id": "4",
        "new_position": "1.1",
    })
    assert "Successfully moved" in result["result"]["content"][0]["text"]

    tree = ET.parse(tdl_path)
    parent = tree.getroot().find(".//TASK[@ID='1']")
    children = parent.findall("./TASK")
    assert children[0].get("ID") == "4"


def test_move_task_positions_updated(mcp):
    """After move, POSSTRING values must be consistent."""
    client, tdl_path = mcp
    client.call_tool("move_task", {"task_id": "3", "new_position": "1.1"})

    tree = ET.parse(tdl_path)
    all_tasks = tree.getroot().findall(".//TASK")
    pos_strings = [t.get("POSSTRING") for t in all_tasks]
    assert all(ps for ps in pos_strings), f"Some tasks have empty POSSTRING"


def test_move_task_nonexistent(mcp):
    client, _ = mcp
    result = client.call_tool("move_task", {
        "task_id": "999",
        "new_position": "1",
    })
    assert "not found" in result["result"]["content"][0]["text"]


def test_move_task_nonexistent_parent(mcp):
    client, _ = mcp
    result = client.call_tool("move_task", {
        "task_id": "2",
        "new_position": "999.1",
    })
    assert "Could not find new parent" in result["result"]["content"][0]["text"]
