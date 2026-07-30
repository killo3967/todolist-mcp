"""Feature 2: complete_task convenience tool."""

import xml.etree.ElementTree as ET


def test_complete_task_defaults(mcp):
    """Default: sets percent_done=100, status='Completed'."""
    client, tdl_path = mcp
    result = client.call_tool("complete_task", {"task_id": "4"})
    assert "Successfully completed" in result["result"]["content"][0]["text"]

    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='4']")
    assert task.get("PERCENTDONE") == "100"
    assert task.get("STATUS") == "Completed"


def test_complete_task_custom_status(mcp):
    """Custom status text like 'Terminado'."""
    client, tdl_path = mcp
    result = client.call_tool("complete_task", {
        "task_id": "4",
        "status_text": "Terminado",
    })
    assert "Successfully completed" in result["result"]["content"][0]["text"]

    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='4']")
    assert task.get("PERCENTDONE") == "100"
    assert task.get("STATUS") == "Terminado"


def test_complete_task_nonexistent(mcp):
    client, _ = mcp
    result = client.call_tool("complete_task", {"task_id": "999"})
    assert "not found" in result["result"]["content"][0]["text"]


def test_complete_task_already_completed(mcp):
    """Completing an already-completed task should still work (idempotent)."""
    client, tdl_path = mcp
    result = client.call_tool("complete_task", {"task_id": "5"})
    assert "Successfully completed" in result["result"]["content"][0]["text"]

    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='5']")
    assert task.get("PERCENTDONE") == "100"
