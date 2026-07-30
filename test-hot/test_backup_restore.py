"""Hot tests for backup_tdl and restore_tdl tools."""

import xml.etree.ElementTree as ET
from pathlib import Path


def test_backup_creates_file(mcp):
    """backup_tdl creates a .bak file alongside the .tdl file."""
    client, tdl_path = mcp
    result = client.call_tool("backup_tdl", {})
    text = result["result"]["content"][0]["text"]
    assert "Backup created" in text or "backup" in text.lower()

    # Check .bak file exists
    backup_path = Path(str(tdl_path) + ".bak")
    assert backup_path.exists(), f"Backup file not found: {backup_path}"
    assert backup_path.stat().st_size > 0


def test_backup_preserves_content(mcp):
    """Backup should be a byte-identical copy of the original."""
    client, tdl_path = mcp

    client.call_tool("backup_tdl", {})
    backup_path = Path(str(tdl_path) + ".bak")

    original = tdl_path.read_bytes()
    backup = backup_path.read_bytes()
    assert original == backup, "Backup content differs from original"


def test_restore_from_backup(mcp):
    """After modifying the .tdl and backing up, restore should revert changes."""
    client, tdl_path = mcp

    # 1. Take backup of original
    client.call_tool("backup_tdl", {})

    # 2. Modify the .tdl (add a task)
    client.call_tool("add_task", {"title": "Temporary Task"})
    tree = ET.parse(tdl_path)
    assert tree.getroot().find(".//TASK[@TITLE='Temporary Task']") is not None

    # 3. Restore
    result = client.call_tool("restore_tdl", {})
    text = result["result"]["content"][0]["text"]
    assert "Restored" in text or "restore" in text.lower()

    # 4. Verify the temporary task is gone
    tree = ET.parse(tdl_path)
    assert tree.getroot().find(".//TASK[@TITLE='Temporary Task']") is None


def test_restore_without_backup_fails(mcp):
    """Calling restore when no .bak exists should fail cleanly."""
    client, tdl_path = mcp

    # Ensure no .bak exists
    backup_path = Path(str(tdl_path) + ".bak")
    if backup_path.exists():
        backup_path.unlink()

    result = client.call_tool("restore_tdl", {})
    text = result["result"]["content"][0]["text"]
    assert "No backup" in text or "not found" in text.lower() or "Error" in text


def test_backup_overwrites_previous(mcp):
    """Second backup should overwrite the first."""
    client, tdl_path = mcp

    client.call_tool("backup_tdl", {})
    first_stat = Path(str(tdl_path) + ".bak").stat()

    # Modify
    client.call_tool("add_task", {"title": "Another Task"})

    # Backup again
    client.call_tool("backup_tdl", {})
    second_stat = Path(str(tdl_path) + ".bak").stat()

    # Second backup should have different content (includes new task)
    assert second_stat.st_size != first_stat.st_size
