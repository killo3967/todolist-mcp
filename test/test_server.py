"""Smoke tests for ToDoList MCP Server.

These require a real .tdl file configured via TODOLIST_FILE env var
or the default path. They run only when the file exists.
"""

import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

import pytest

from src.domain.models import Priority
from src.infrastructure.repository import XmlTodoRepository


@pytest.fixture
def tdl_path():
    """Resolve the .tdl file path the same way the server does."""
    from src.manager import DEFAULT_TDL_FILE
    path = Path(DEFAULT_TDL_FILE)
    if not path.exists():
        pytest.skip(f"ToDoList file not found: {DEFAULT_TDL_FILE}")
    return str(path)


def test_file_reading(tdl_path):
    """The .tdl file can be parsed as valid XML."""
    root = ET.parse(tdl_path).getroot()
    assert root.tag == "TODOLIST"
    assert root.get("PROJECTNAME")


def test_task_extraction(tdl_path):
    """Tasks can be loaded from the .tdl file."""
    tasks, _, _ = XmlTodoRepository(tdl_path).load_all()
    assert len(tasks) > 0


def test_date_handling():
    """Date encode/decode round-trips correctly."""
    repo = XmlTodoRepository("nonexistent.tdl")
    target = date(2025, 9, 8)
    encoded = repo._encode_date(target)
    assert encoded, "Date encoding returned empty"
    assert repo._decode_date(encoded) == target


def test_priority_handling():
    """All priority levels round-trip through code and back."""
    for label in ["Low", "Normal", "High", "Urgent"]:
        p = Priority.from_str(label)
        assert Priority.from_str(p.to_str()) is p
