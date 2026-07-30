"""Feature 4: STARTDATE and TAGS support in add_task / update_task."""

import xml.etree.ElementTree as ET

# ── add_task with start_date ──

def test_add_task_with_start_date(mcp):
    client, tdl_path = mcp
    client.call_tool("add_task", {
        "title": "Started Task",
        "start_date": "2025-06-01",
    })
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@TITLE='Started Task']")
    assert task.get("STARTDATE") is not None
    assert task.get("STARTDATESTRING") == "01/06/2025"


# ── add_task with tags ──

def test_add_task_with_single_tag(mcp):
    client, tdl_path = mcp
    client.call_tool("add_task", {
        "title": "Tagged Task",
        "tags": "important",
    })
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@TITLE='Tagged Task']")
    tags = [t.text for t in task.findall("TAG")]
    assert "important" in tags


def test_add_task_with_multiple_tags(mcp):
    client, tdl_path = mcp
    client.call_tool("add_task", {
        "title": "Multi Tagged",
        "tags": "urgent, bug, frontend",
    })
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@TITLE='Multi Tagged']")
    tags = [t.text for t in task.findall("TAG")]
    assert "urgent" in tags
    assert "bug" in tags
    assert "frontend" in tags


# ── update_task with start_date ──

def test_update_set_start_date(mcp):
    client, tdl_path = mcp
    client.call_tool("update_task", {
        "task_id": "4",
        "start_date": "2025-03-15",
    })
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='4']")
    assert task.get("STARTDATESTRING") == "15/03/2025"


def test_update_clear_start_date(mcp):
    client, tdl_path = mcp
    client.call_tool("update_task", {"task_id": "4", "start_date": "2025-01-01"})
    client.call_tool("update_task", {"task_id": "4", "start_date": ""})
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='4']")
    assert "STARTDATE" not in task.attrib


# ── update_task with tags ──

def test_update_set_tags(mcp):
    client, tdl_path = mcp
    client.call_tool("update_task", {
        "task_id": "4",
        "tags": "refactor, critical",
    })
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='4']")
    tags = [t.text for t in task.findall("TAG")]
    assert "refactor" in tags
    assert "critical" in tags


def test_update_clear_tags(mcp):
    client, tdl_path = mcp
    client.call_tool("update_task", {"task_id": "4", "tags": "test"})
    client.call_tool("update_task", {"task_id": "4", "tags": ""})
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='4']")
    assert len(task.findall("TAG")) == 0


# ── extract_tasks reads start_date and tags ──

def test_extract_tasks_reads_start_date(mcp):
    client, _ = mcp
    result = client.call_tool("get_task", {"task_id": "1", "format": "json"})
    import json
    data = json.loads(result["result"]["content"][0]["text"])
    # Existing tasks may have STARTDATE from ToDoList
    assert "start_date" in data[0]
