"""Hot tests for update_task MCP tool — every parameter variant."""

import xml.etree.ElementTree as ET


# ── title ──

def test_update_title(mcp):
    client, tdl_path = mcp
    result = client.call_tool("update_task", {
        "task_id": "4",
        "title": "Renamed Beta",
    })
    assert "Successfully updated" in result["result"]["content"][0]["text"]
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='4']")
    assert task.get("TITLE") == "Renamed Beta"


# ── description ──

def test_update_description(mcp):
    client, tdl_path = mcp
    client.call_tool("update_task", {
        "task_id": "4",
        "description": "Updated desc",
    })
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='4']")
    comments = task.find("COMMENTS")
    assert comments is not None
    assert comments.text == "Updated desc"
    assert "COMMENTSTYPE" not in task.attrib


# ── due_date (set + clear) ──

def test_update_set_due_date(mcp):
    client, tdl_path = mcp
    client.call_tool("update_task", {
        "task_id": "4",
        "due_date": "2025-12-25",
    })
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='4']")
    assert task.get("DUEDATE") is not None


def test_update_clear_due_date(mcp):
    client, tdl_path = mcp
    client.call_tool("update_task", {"task_id": "4", "due_date": "2025-01-01"})
    result = client.call_tool("update_task", {"task_id": "4", "due_date": ""})
    assert "Successfully" in result["result"]["content"][0]["text"]
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='4']")
    assert "DUEDATE" not in task.attrib


# ── priority ──

def test_update_priority_to_urgent(mcp):
    client, tdl_path = mcp
    client.call_tool("update_task", {"task_id": "4", "priority": "Urgent"})
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='4']")
    assert task.get("PRIORITY") == "3"


# ── category (set + clear) ──

def test_update_set_category(mcp):
    client, tdl_path = mcp
    client.call_tool("update_task", {"task_id": "4", "category": "NewCat"})
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='4']")
    cats = [c.text for c in task.findall("CATEGORY")]
    assert "NewCat" in cats


def test_update_clear_category(mcp):
    client, tdl_path = mcp
    client.call_tool("update_task", {"task_id": "4", "category": ""})
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='4']")
    assert len(task.findall("CATEGORY")) == 0


# ── percent_done ──

def test_update_percent_done(mcp):
    client, tdl_path = mcp
    client.call_tool("update_task", {"task_id": "4", "percent_done": 75})
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='4']")
    assert task.get("PERCENTDONE") == "75"


# ── allocated_to (set + clear) ──

def test_update_set_allocated_to(mcp):
    client, tdl_path = mcp
    client.call_tool("update_task", {"task_id": "4", "allocated_to": "Charlie"})
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='4']")
    allocs = [a.text for a in task.findall("ALLOCATEDTO")]
    assert "Charlie" in allocs


def test_update_set_multiple_allocated(mcp):
    client, tdl_path = mcp
    client.call_tool("update_task", {"task_id": "4", "allocated_to": "Alice, Bob"})
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='4']")
    allocs = [a.text for a in task.findall("ALLOCATEDTO")]
    assert "Alice" in allocs
    assert "Bob" in allocs


def test_update_clear_allocated_to(mcp):
    client, tdl_path = mcp
    client.call_tool("update_task", {"task_id": "4", "allocated_to": ""})
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='4']")
    assert len(task.findall("ALLOCATEDTO")) == 0


# ── status ──

def test_update_status(mcp):
    client, tdl_path = mcp
    client.call_tool("update_task", {"task_id": "4", "status": "Bloqueado"})
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='4']")
    assert task.get("STATUS") == "Bloqueado"


# ── status independent of allocated_to (regression) ──

def test_update_status_without_allocated_to(mcp):
    """status must work even when allocated_to is NOT passed."""
    client, tdl_path = mcp
    client.call_tool("update_task", {"task_id": "5", "status": "Verificado"})
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='5']")
    assert task.get("STATUS") == "Verificado"


# ── time_estimate ──

def test_update_time_estimate(mcp):
    client, tdl_path = mcp
    client.call_tool("update_task", {"task_id": "4", "time_estimate": 3.0})
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='4']")
    assert task.get("TIMEESTIMATE") == "3.0"


# ── color (set + clear) ──

def test_update_set_color(mcp):
    client, tdl_path = mcp
    client.call_tool("update_task", {"task_id": "4", "color": "#F44336"})
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='4']")
    assert task.get("COLOR") is not None


def test_update_clear_color(mcp):
    client, tdl_path = mcp
    client.call_tool("update_task", {"task_id": "4", "color": "#F44336"})
    client.call_tool("update_task", {"task_id": "4", "color": ""})
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='4']")
    assert "COLOR" not in task.attrib


# ── multiple fields at once ──

def test_update_multiple_fields(mcp):
    client, tdl_path = mcp
    result = client.call_tool("update_task", {
        "task_id": "4",
        "title": "Multi Update",
        "priority": "High",
        "percent_done": 50,
        "status": "En curso",
    })
    assert "Successfully updated" in result["result"]["content"][0]["text"]
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='4']")
    assert task.get("TITLE") == "Multi Update"
    assert task.get("PRIORITY") == "2"
    assert task.get("PERCENTDONE") == "50"
    assert task.get("STATUS") == "En curso"


# ── error: nonexistent task ──

def test_update_nonexistent_task(mcp):
    client, _ = mcp
    result = client.call_tool("update_task", {
        "task_id": "999",
        "title": "Ghost",
    })
    assert "not found" in result["result"]["content"][0]["text"]


# ── error: no updates ──

def test_update_no_updates_provided(mcp):
    client, _ = mcp
    result = client.call_tool("update_task", {"task_id": "4"})
    assert "No updates" in result["result"]["content"][0]["text"]
