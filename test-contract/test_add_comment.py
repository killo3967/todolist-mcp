"""Hot tests for add_comment MCP tool.

Tests the tool through the MCP protocol, not importing server code.
"""

import xml.etree.ElementTree as ET


def test_add_comment_first_time(mcp):
    """Task 4 (Beta) has no COMMENTS. Adding one should create it."""
    client, tdl_path = mcp

    # Call add_comment via MCP
    result = client.call_tool("add_comment", {
        "task_id": "4",
        "comment": "First hot-test comment",
    })

    assert "Error" not in result["result"]["content"][0]["text"]
    text = result["result"]["content"][0]["text"]
    assert "Comment added" in text

    # Verify on disk: COMMENTS element created
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='4']")
    comments = task.find("COMMENTS")
    assert comments is not None, "COMMENTS element should be created"
    assert "First hot-test comment" in (comments.text or "")

    # COMMENTSTYPE debe apuntar al plugin de texto plano (no RTF)
    assert task.get("COMMENTSTYPE") == "BAA4E079-268B-4B9B-B7C8-6D15CCF058A2"


def test_add_comment_appends(mcp):
    """Adding a second comment must APPEND, not replace."""
    client, tdl_path = mcp

    # First comment
    client.call_tool("add_comment", {
        "task_id": "1",
        "comment": "Line 1",
    })

    # Second comment
    result = client.call_tool("add_comment", {
        "task_id": "1",
        "comment": "Line 2",
    })
    assert "Comment added" in result["result"]["content"][0]["text"]

    # Verify: both comments present, Line 2 after Line 1
    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='1']")
    comments = task.find("COMMENTS")
    text = comments.text or ""

    assert "Line 1" in text
    assert "Line 2" in text
    idx1 = text.index("Line 1")
    idx2 = text.index("Line 2")
    assert idx1 < idx2, "Line 2 must come AFTER Line 1 (append, not replace)"


def test_add_comment_preserves_existing(mcp):
    """Adding a comment to Task 1 (which has 'Initial comment for Alpha')
    must PRESERVE the existing text."""
    client, tdl_path = mcp

    client.call_tool("add_comment", {
        "task_id": "1",
        "comment": "Appended by hot-test",
    })

    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='1']")
    comments = task.find("COMMENTS")
    text = comments.text or ""

    assert "Initial comment for Alpha" in text, "Existing comment was lost!"
    assert "Appended by hot-test" in text


def test_add_comment_nonexistent_task(mcp):
    """Calling add_comment on a non-existent task should fail cleanly."""
    client, tdl_path = mcp

    result = client.call_tool("add_comment", {
        "task_id": "999",
        "comment": "Boom",
    })

    text = result["result"]["content"][0]["text"]
    assert "not found" in text


def test_add_comment_to_completed_task(mcp):
    """Adding a comment to a completed task (ID=5, Gamma) should work."""
    client, tdl_path = mcp

    result = client.call_tool("add_comment", {
        "task_id": "5",
        "comment": "Retrospective note on completed task",
    })

    assert "Comment added" in result["result"]["content"][0]["text"]

    tree = ET.parse(tdl_path)
    task = tree.getroot().find(".//TASK[@ID='5']")
    comments = task.find("COMMENTS")
    assert "Retrospective note on completed task" in (comments.text or "")
