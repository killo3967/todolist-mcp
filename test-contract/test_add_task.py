"""Hot tests for add_task MCP tool — every parameter variant."""

import xml.etree.ElementTree as ET

# ── title (only required field) ──

def test_add_task_minimal(mcp):
    """Only title — all other fields get defaults."""
    client, tdl_path = mcp
    result = client.call_tool("add_task", {"title": "Minimal Task"})
    text = result["result"]["content"][0]["text"]
    assert "Successfully added" in text

    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@TITLE='Minimal Task']")
    assert task is not None
    assert task.get("PRIORITY") == "0"  # Normal
    # PERCENTDONE is not set by add_task (only set explicitly via update_task)


# ── position ──

def test_add_task_top_level(mcp):
    """No position = top-level append."""
    client, tdl_path = mcp
    client.call_tool("add_task", {"title": "Top Level"})
    tree = ET.parse(tdl_path)
    tasks = tree.getroot().findall("./TASK")
    assert any(t.get("TITLE") == "Top Level" for t in tasks)


def test_add_task_as_child(mcp):
    """Position='1' appends as child of Task Alpha."""
    client, tdl_path = mcp
    client.call_tool("add_task", {
        "title": "New Child",
        "position": "1",
    })
    tree = ET.parse(tdl_path)
    parent = tree.getroot().find(".//TASK[@ID='1']")
    children = parent.findall("./TASK")
    assert any(t.get("TITLE") == "New Child" for t in children)


# ── description ──

def test_add_task_with_description(mcp):
    """Description should become <COMMENTS> element child."""
    client, tdl_path = mcp
    client.call_tool("add_task", {
        "title": "With Desc",
        "description": "Hello from hot-test",
    })
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@TITLE='With Desc']")
    comments = task.find("COMMENTS")
    assert comments is not None
    assert comments.text == "Hello from hot-test"
    assert task.get("COMMENTSTYPE") == "BAA4E079-268B-4B9B-B7C8-6D15CCF058A2"


# ── due_date ──

def test_add_task_with_due_date(mcp):
    """Due date should set DUEDATE + DUEDATESTRING."""
    client, tdl_path = mcp
    client.call_tool("add_task", {
        "title": "Dated Task",
        "due_date": "2025-12-25",
    })
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@TITLE='Dated Task']")
    assert task.get("DUEDATE") is not None
    assert "25/12/2025" in task.get("DUEDATESTRING", "")


# ── priority (all 6 levels) ──

def test_add_task_priority_low(mcp):
    _add_and_check_priority(mcp, "Low Priority", "Low", "-2")

def test_add_task_priority_below_normal(mcp):
    _add_and_check_priority(mcp, "BN Priority", "Below Normal", "-1")

def test_add_task_priority_normal(mcp):
    _add_and_check_priority(mcp, "Normal Priority", "Normal", "0")

def test_add_task_priority_above_normal(mcp):
    _add_and_check_priority(mcp, "AN Priority", "Above Normal", "1")

def test_add_task_priority_high(mcp):
    _add_and_check_priority(mcp, "High Priority", "High", "2")

def test_add_task_priority_urgent(mcp):
    _add_and_check_priority(mcp, "Urgent Priority", "Urgent", "3")


def _add_and_check_priority(mcp, title, priority_label, expected_code):
    client, tdl_path = mcp
    client.call_tool("add_task", {"title": title, "priority": priority_label})
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(f".//TASK[@TITLE='{title}']")
    assert task is not None, f"Task '{title}' not found"
    assert task.get("PRIORITY") == expected_code, f"Expected PRIORITY={expected_code}, got {task.get('PRIORITY')}"


# ── category ──

def test_add_task_with_category(mcp):
    client, tdl_path = mcp
    client.call_tool("add_task", {
        "title": "Categorized",
        "category": "Testing",
    })
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@TITLE='Categorized']")
    categories = [c.text for c in task.findall("CATEGORY")]
    assert "Testing" in categories


# ── status ──

def test_add_task_with_status(mcp):
    client, tdl_path = mcp
    client.call_tool("add_task", {
        "title": "Status Task",
        "status": "En curso",
    })
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@TITLE='Status Task']")
    assert task.get("STATUS") == "En curso"


# ── time_estimate ──

def test_add_task_with_time_estimate(mcp):
    client, tdl_path = mcp
    client.call_tool("add_task", {
        "title": "Timed Task",
        "time_estimate": 0.125,
    })
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@TITLE='Timed Task']")
    assert task.get("TIMEESTIMATE") == "0.125"


# ── color ──

def test_add_task_with_color(mcp):
    client, tdl_path = mcp
    client.call_tool("add_task", {
        "title": "Colored Task",
        "color": "#4CAF50",
    })
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@TITLE='Colored Task']")
    assert task.get("COLOR") is not None
    # #4CAF50 → BGR = 50 AF 4C decimal
    assert task.get("COLOR") == "5287756"


# ── combined fields ──

def test_add_task_all_fields(mcp):
    """All fields combined should work."""
    client, tdl_path = mcp
    client.call_tool("add_task", {
        "title": "Full Task",
        "description": "Full description",
        "due_date": "2025-06-15",
        "priority": "High",
        "category": "Integration",
        "status": "Pendiente",
        "time_estimate": 1.5,
        "color": "#FF6B35",
        "position": "1",
    })
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@TITLE='Full Task']")
    assert task is not None
    assert task.find("COMMENTS").text == "Full description"
    assert task.get("STATUS") == "Pendiente"
    assert task.get("TIMEESTIMATE") == "1.5"
