"""Update & search integration test against an isolated temp .tdl file.

Migrated from the legacy script-style test that operated on the real
~/.tdl file. This version is synchronous, uses TodoService, and never
touches user data.
"""

import xml.etree.ElementTree as ET

import pytest

from src.domain.models import Priority
from src.infrastructure.repository import XmlTodoRepository
from src.services.todo_service import TodoService


@pytest.fixture
def service(tmp_path):
    path = tmp_path / "update_search.tdl"
    root = ET.Element("TODOLIST", {"NEXTUNIQUEID": "4"})
    ET.SubElement(root, "TASK", {"ID": "1", "TITLE": "First task", "PRIORITY": "0", "PERCENTDONE": "0"})
    ET.SubElement(root, "TASK", {"ID": "2", "TITLE": "High priority test", "PRIORITY": "2", "PERCENTDONE": "0"})
    ET.SubElement(root, "TASK", {"ID": "3", "TITLE": "Done task", "PRIORITY": "0", "PERCENTDONE": "100"})
    ET.ElementTree(root).write(str(path), encoding="utf-8", xml_declaration=True)
    return TodoService(XmlTodoRepository(str(path)))


def test_update_and_search(service):
    # --- search ---------------------------------------------------------
    assert [t.id for t in service.search_tasks(query="test")] == ["2"]
    assert [t.id for t in service.search_tasks(query="", priority="High")] == ["2"]
    assert [t.id for t in service.search_tasks(query="", completed=False)] == ["1", "2"]

    # --- update then verify --------------------------------------------
    assert service.update_task("1", {"title": "Renamed", "priority": "High", "percent_done": 50}) is True
    updated = service.get_task_by_id("1")
    assert updated.title == "Renamed"
    assert updated.priority is Priority.HIGH
    assert updated.percent_done == 50

    # --- clear a field --------------------------------------------------
    assert service.update_task("1", {"priority": "Normal"}) is True
    assert service.get_task_by_id("1").priority is Priority.NORMAL
