"""Unit tests for ToDoListManager core methods.

Tests use in-memory XML trees — no real .tdl file required.
"""

import xml.etree.ElementTree as ET
from datetime import date, datetime

import pytest

from src.domain.models import Priority, Task
from src.infrastructure.repository import XmlTodoRepository
from src.services.todo_service import TodoService
from src.tools import _format_tasks_markdown, _hex_to_bgr

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def repo():
    """Repository bound to a non-existent file (pure codec/parse tests)."""
    return XmlTodoRepository("nonexistent.tdl")

@pytest.fixture
def service():
    """TodoService bound to a non-existent file (pure logic tests)."""
    return TodoService(XmlTodoRepository("nonexistent.tdl"))

def _service_with_tasks(tmp_path, tasks):
    """Persist Task objects to a temp .tdl and return a TodoService bound to it."""
    path = tmp_path / "service.tdl"
    XmlTodoRepository(str(path)).save_all(tasks, 100, {"PROJECTNAME": "unit-tests"})
    return TodoService(XmlTodoRepository(str(path)))


@pytest.fixture
def empty_root():
    """Minimal ToDoList XML root (TODOLIST element)."""
    return ET.Element("TODOLIST", {
        "PROJECTNAME": "Test Project",
        "NEXTUNIQUEID": "10",
    })


@pytest.fixture
def sample_tree():
    """Two-level task tree:
    TODOLIST
    └─ TASK ID=1 'Parent'
       └─ TASK ID=2 'Child'
    """
    root = ET.Element("TODOLIST", {"NEXTUNIQUEID": "3"})
    parent = ET.SubElement(root, "TASK", {
        "ID": "1", "TITLE": "Parent", "PRIORITY": "2",
        "DUEDATE": "45900", "PERCENTDONE": "50",
    })
    ET.SubElement(parent, "CATEGORY").text = "Work"
    child = ET.SubElement(parent, "TASK", {
        "ID": "2", "TITLE": "Child", "PRIORITY": "0",
        "PERCENTDONE": "100", "STATUS": "Completed",
    })
    # Set positions
    for i, t in enumerate(root.findall("./TASK")):
        t.set("POS", str(i))
        t.set("POSSTRING", str(i + 1))
    for i, t in enumerate(parent.findall("./TASK")):
        t.set("POS", str(i))
        t.set("POSSTRING", f"1.{i + 1}")
    tree = ET.ElementTree(root)
    return tree


# ---------------------------------------------------------------------------
# _decode_date / _encode_date
# ---------------------------------------------------------------------------

class TestDateCodec:
    def test_decode_valid_excel_date(self, repo):
        """Excel serial date 44927 = 2023-01-01."""
        assert repo._decode_date("44927") == date(2023, 1, 1)

    def test_decode_empty_string(self, repo):
        assert repo._decode_date("") is None

    def test_decode_non_numeric(self, repo):
        """Non-numeric input is not a valid date."""
        assert repo._decode_date("hello") is None

    def test_encode_valid_date(self, repo):
        result = repo._encode_date(datetime(2025, 9, 8))
        assert float(result) > 40000  # days since 1899-12-30

    def test_encode_empty_string(self, repo):
        assert repo._encode_date(None) == ""

    def test_encode_invalid_date(self, repo):
        assert repo._encode_date("not-a-date") == ""

    def test_roundtrip(self, repo):
        """encode -> decode should return the original date."""
        for d in (date(2025, 1, 1), date(2024, 12, 31), date(2023, 6, 15)):
            encoded = repo._encode_date(d)
            decoded = repo._decode_date(encoded)
            assert decoded == d, f"Roundtrip failed for {d}"


# ---------------------------------------------------------------------------
# _decode_priority / _encode_priority
# ---------------------------------------------------------------------------

class TestPriorityCodec:
    def test_from_str_numeric_codes(self):
        assert Priority.from_str("-2") is Priority.LOW
        assert Priority.from_str("-1") is Priority.BELOW_NORMAL
        assert Priority.from_str("0") is Priority.NORMAL
        assert Priority.from_str("1") is Priority.ABOVE_NORMAL
        assert Priority.from_str("2") is Priority.HIGH
        assert Priority.from_str("3") is Priority.URGENT

    def test_from_str_human_labels(self):
        assert Priority.from_str("Low") is Priority.LOW
        assert Priority.from_str("Below Normal") is Priority.BELOW_NORMAL
        assert Priority.from_str("Normal") is Priority.NORMAL
        assert Priority.from_str("Above Normal") is Priority.ABOVE_NORMAL
        assert Priority.from_str("High") is Priority.HIGH
        assert Priority.from_str("Urgent") is Priority.URGENT

    def test_from_str_empty_and_invalid_fall_back_to_normal(self):
        assert Priority.from_str("") is Priority.NORMAL
        assert Priority.from_str("abc") is Priority.NORMAL

    def test_to_str_all_levels(self):
        assert Priority.LOW.to_str() == "-2"
        assert Priority.BELOW_NORMAL.to_str() == "-1"
        assert Priority.NORMAL.to_str() == "0"
        assert Priority.ABOVE_NORMAL.to_str() == "1"
        assert Priority.HIGH.to_str() == "2"
        assert Priority.URGENT.to_str() == "3"


# ---------------------------------------------------------------------------
# _hex_to_rgb_int
# ---------------------------------------------------------------------------

class TestHexToBgr:
    def test_standard_color(self):
        """#FF6B35 (orange) -> BGR integer."""
        # R=FF G=6B B=35 -> BGR = 0x35 0x6B 0xFF
        assert _hex_to_bgr("#FF6B35") == 3501055

    def test_without_hash(self):
        assert _hex_to_bgr("FF0000") == _hex_to_bgr("#FF0000")

    def test_black_white(self):
        assert _hex_to_bgr("#000000") == 0
        assert _hex_to_bgr("#FFFFFF") == 16777215

    def test_bgr_swap(self):
        """Red (#FF0000) lands in the low byte after the BGR swap."""
        assert _hex_to_bgr("#FF0000") == 255


# ---------------------------------------------------------------------------
# _decode_status
# ---------------------------------------------------------------------------

class TestDecodeStatus:
    def test_explicit_status(self, repo):
        elem = ET.Element("TASK", {"STATUS": "In Progress", "PERCENTDONE": "30"})
        assert repo._decode_status(elem) == "In Progress"

    def test_fallback_percent_100(self, repo):
        elem = ET.Element("TASK", {"PERCENTDONE": "100"})
        assert repo._decode_status(elem) == "Completed"

    def test_fallback_percent_0(self, repo):
        elem = ET.Element("TASK", {"PERCENTDONE": "0"})
        assert repo._decode_status(elem) == "Not Started"

    def test_fallback_percent_partial(self, repo):
        elem = ET.Element("TASK", {"PERCENTDONE": "75"})
        assert repo._decode_status(elem) == "75% Complete"

    def test_no_status_no_percent(self, repo):
        elem = ET.Element("TASK", {})
        assert repo._decode_status(elem) == "Not Started"


# ---------------------------------------------------------------------------
# _find_task_by_pos_string
# ---------------------------------------------------------------------------

class TestFindTaskByPosString:
    @pytest.fixture
    def tasks(self):
        t1 = Task(id="1", title="One")
        t2 = Task(id="2", title="Two")
        t3 = Task(id="3", title="Three")
        t2.children.append(Task(id="4", title="Child"))
        return [t1, t2, t3]

    def test_top_level_first(self, service, tasks):
        found = service._find_task_by_pos(tasks, "1")
        assert found is not None
        assert found.id == "1"

    def test_top_level_second(self, service, tasks):
        assert service._find_task_by_pos(tasks, "2").id == "2"

    def test_nested_child(self, service, tasks):
        assert service._find_task_by_pos(tasks, "2.1").id == "4"

    def test_empty_string_returns_none(self, service, tasks):
        assert service._find_task_by_pos(tasks, "") is None

    def test_nonexistent_level(self, service, tasks):
        assert service._find_task_by_pos(tasks, "5") is None

    def test_nonexistent_nested(self, service, tasks):
        assert service._find_task_by_pos(tasks, "1.99") is None


# ---------------------------------------------------------------------------
# _find_parent
# ---------------------------------------------------------------------------

class TestFindParent:
    @pytest.fixture
    def tree(self):
        parent = Task(id="1", title="Parent")
        child = Task(id="2", title="Child")
        parent.children.append(child)
        sibling = Task(id="3", title="Sibling")
        return [parent, sibling], parent, child

    def test_find_parent_of_child(self, service, tree):
        tasks, parent, child = tree
        assert service._find_parent_of_task(tasks, child) is parent

    def test_find_parent_of_top_level(self, service, tree):
        tasks, parent, child = tree
        assert service._find_parent_of_task(tasks, parent) is None

    def test_nonexistent_task(self, service, tree):
        tasks, parent, child = tree
        assert service._find_task_recursive(tasks, "99") is None


# ---------------------------------------------------------------------------
# _update_positions
# ---------------------------------------------------------------------------

class TestUpdatePositions:
    def test_top_level_positions(self, service):
        tasks = [Task(id="1", title="a"), Task(id="2", title="b"), Task(id="3", title="c")]

        service._recalculate_positions(tasks)

        assert tasks[0].pos == "0"
        assert tasks[0].pos_string == "1"
        assert tasks[1].pos == "1"
        assert tasks[1].pos_string == "2"
        assert tasks[2].pos == "2"
        assert tasks[2].pos_string == "3"

    def test_nested_positions(self, service):
        parent = Task(id="1", title="p")
        parent.children = [Task(id="1.1", title="c1"), Task(id="1.2", title="c2")]

        service._recalculate_positions([parent])

        assert parent.children[0].pos_string == "1.1"
        assert parent.children[1].pos_string == "1.2"


# ---------------------------------------------------------------------------
# get_next_unique_id
# ---------------------------------------------------------------------------

class TestNextUniqueId:
    def test_load_reports_next_id(self, tmp_path):
        path = tmp_path / "next.tdl"
        ET.ElementTree(ET.Element("TODOLIST", {"NEXTUNIQUEID": "10"})).write(
            str(path), encoding="utf-8", xml_declaration=True
        )
        _, next_id, _ = XmlTodoRepository(str(path)).load_all()
        assert next_id == 10

    def test_missing_nextuniqueid_defaults_to_1(self, tmp_path):
        path = tmp_path / "none.tdl"
        ET.ElementTree(ET.Element("TODOLIST")).write(
            str(path), encoding="utf-8", xml_declaration=True
        )
        _, next_id, _ = XmlTodoRepository(str(path)).load_all()
        assert next_id == 1

    def test_add_task_increments_next_id(self, tmp_path):
        path = tmp_path / "inc.tdl"
        ET.ElementTree(ET.Element("TODOLIST", {"NEXTUNIQUEID": "10"})).write(
            str(path), encoding="utf-8", xml_declaration=True
        )
        service = TodoService(XmlTodoRepository(str(path)))
        service.add_task(None, {"title": "New"})
        _, next_id, _ = XmlTodoRepository(str(path)).load_all()
        assert next_id == 11


# ---------------------------------------------------------------------------
# search_tasks
# ---------------------------------------------------------------------------

class TestSearchTasks:
    @pytest.fixture
    def service(self, tmp_path):
        tasks = [
            Task(id="1", title="Buy milk", description="Low-fat", category=["Shopping"],
                 priority=Priority.NORMAL, allocated_to=["John"]),
            Task(id="2", title="Write code", description="Python API", category=["Work"],
                 priority=Priority.HIGH, allocated_to=["Jane"]),
            Task(id="3", title="Read book", description="Sci-fi novel", category=["Leisure"],
                 priority=Priority.LOW, percent_done=100),
        ]
        return _service_with_tasks(tmp_path, tasks)

    def test_search_by_term_title(self, service):
        result = service.search_tasks(query="code")
        assert [t.id for t in result] == ["2"]

    def test_search_by_term_description(self, service):
        result = service.search_tasks(query="sci-fi")
        assert [t.id for t in result] == ["3"]

    def test_search_case_insensitive(self, service):
        result = service.search_tasks(query="BUY")
        assert [t.id for t in result] == ["1"]

    def test_filter_by_priority(self, service):
        result = service.search_tasks(query="", priority="High")
        assert [t.id for t in result] == ["2"]

    def test_filter_by_completed(self, service):
        result = service.search_tasks(query="", completed=True)
        assert [t.id for t in result] == ["3"]

    def test_filter_by_category(self, service):
        result = service.search_tasks(query="", category="Shopping")
        assert [t.id for t in result] == ["1"]

    def test_filter_by_assigned_to(self, service):
        result = service.search_tasks(query="", allocated_to="Jane")
        assert [t.id for t in result] == ["2"]

    def test_combined_filters(self, service):
        result = service.search_tasks(query="", completed=False, priority="High")
        assert [t.id for t in result] == ["2"]

    def test_no_results(self, service):
        assert service.search_tasks(query="zzz-no-match") == []


# ---------------------------------------------------------------------------
# filter_tasks_by_date
# ---------------------------------------------------------------------------

class TestFilterTasksByDate:
    @pytest.fixture
    def service(self, tmp_path):
        tasks = [
            Task(id="1", title="Today", due_date=date.today()),
            Task(id="2", title="Yesterday", due_date=date(2020, 1, 15)),
            Task(id="3", title="No date"),
        ]
        return _service_with_tasks(tmp_path, tasks)

    def test_defaults_today(self, service):
        result = service.get_today_tasks(date.today())
        assert [t.id for t in result] == ["1"]

    def test_specific_date(self, service):
        result = service.get_today_tasks(date(2020, 1, 15))
        assert [t.id for t in result] == ["2"]

    def test_no_due_date_skipped(self, service):
        result = service.get_today_tasks(date.today())
        assert all(t.due_date is not None for t in result)


# ---------------------------------------------------------------------------
# extract_tasks
# ---------------------------------------------------------------------------

class TestExtractTasks:
    @pytest.fixture
    def sample_path(self, tmp_path):
        root = ET.Element("TODOLIST", {"NEXTUNIQUEID": "3"})
        parent = ET.SubElement(root, "TASK", {
            "ID": "1", "TITLE": "Parent", "PRIORITY": "2",
            "DUEDATE": "45900", "PERCENTDONE": "50",
        })
        ET.SubElement(parent, "CATEGORY").text = "Work"
        ET.SubElement(parent, "TASK", {
            "ID": "2", "TITLE": "Child", "PRIORITY": "0",
            "PERCENTDONE": "100", "STATUS": "Completed",
        })
        path = tmp_path / "sample.tdl"
        ET.ElementTree(root).write(str(path), encoding="utf-8", xml_declaration=True)
        return str(path)

    def test_extracts_flat_tasks(self, sample_path):
        tasks, _, _ = XmlTodoRepository(sample_path).load_all()
        assert len(tasks) == 1  # "Parent" at top level
        assert tasks[0].id == "1"
        assert tasks[0].title == "Parent"
        assert tasks[0].priority is Priority.HIGH
        assert tasks[0].percent_done == 50
        assert tasks[0].completed is False
        assert tasks[0].category == ["Work"]

    def test_extracts_nested_children(self, sample_path):
        tasks, _, _ = XmlTodoRepository(sample_path).load_all()
        children = tasks[0].children
        assert len(children) == 1
        assert children[0].id == "2"
        assert children[0].title == "Child"
        assert children[0].completed is True
        assert children[0].status == "Completed"

    def test_extracts_due_date(self, sample_path):
        tasks, _, _ = XmlTodoRepository(sample_path).load_all()
        assert tasks[0].due_date is not None
        assert isinstance(tasks[0].due_date, date)

    def test_extracts_comments(self, tmp_path):
        """COMMENTS element child should be read correctly."""
        root = ET.Element("TODOLIST")
        task = ET.SubElement(root, "TASK", {"ID": "1", "TITLE": "With Comment"})
        ET.SubElement(task, "COMMENTS").text = "Hello world"
        path = tmp_path / "comments.tdl"
        ET.ElementTree(root).write(str(path), encoding="utf-8", xml_declaration=True)
        tasks, _, _ = XmlTodoRepository(str(path)).load_all()
        assert tasks[0].comments == "Hello world"
        assert tasks[0].description == "Hello world"

    def test_comments_fallback_to_attribute(self, tmp_path):
        """If no COMMENTS element, fall back to the attribute."""
        root = ET.Element("TODOLIST")
        ET.SubElement(root, "TASK", {"ID": "1", "TITLE": "Attr", "COMMENTS": "legacy"})
        path = tmp_path / "attr.tdl"
        ET.ElementTree(root).write(str(path), encoding="utf-8", xml_declaration=True)
        tasks, _, _ = XmlTodoRepository(str(path)).load_all()
        assert tasks[0].comments == "legacy"


# ---------------------------------------------------------------------------
# add_comment (append behavior)
# ---------------------------------------------------------------------------

class TestAddComment:
    @pytest.fixture
    def tdl_path(self, tmp_path):
        path = tmp_path / "test.tdl"
        root = ET.Element("TODOLIST", {"NEXTUNIQUEID": "2"})
        ET.SubElement(root, "TASK", {"ID": "1", "TITLE": "Test Task"})
        ET.ElementTree(root).write(str(path), encoding="utf-8", xml_declaration=True)
        return str(path)

    @pytest.fixture
    def service(self, tdl_path):
        return TodoService(XmlTodoRepository(tdl_path))

    def test_add_comment_first_time(self, service, tdl_path):
        assert service.add_comment("1", "First comment") is True
        tasks, _, _ = XmlTodoRepository(tdl_path).load_all()
        assert "First comment" in tasks[0].description

    def test_add_comment_appends(self, service, tdl_path):
        service.add_comment("1", "Line 1")
        service.add_comment("1", "Line 2")
        tasks, _, _ = XmlTodoRepository(tdl_path).load_all()
        desc = tasks[0].description
        assert "Line 1" in desc
        assert "Line 2" in desc
        assert desc.index("Line 1") < desc.index("Line 2"), "Line 2 should come after Line 1"

    def test_add_comment_nonexistent_task(self, service):
        assert service.add_comment("99", "Oops") is False


# ---------------------------------------------------------------------------
# update_task
# ---------------------------------------------------------------------------

class TestUpdateTask:
    @pytest.fixture
    def tdl_path(self, tmp_path):
        path = tmp_path / "test.tdl"
        root = ET.Element("TODOLIST", {"NEXTUNIQUEID": "3"})
        ET.SubElement(root, "TASK", {"ID": "1", "TITLE": "Original", "PRIORITY": "0"})
        ET.ElementTree(root).write(str(path), encoding="utf-8", xml_declaration=True)
        return str(path)

    @pytest.fixture
    def service(self, tdl_path):
        return TodoService(XmlTodoRepository(tdl_path))

    @staticmethod
    def _reload(tdl_path):
        tasks, _, _ = XmlTodoRepository(tdl_path).load_all()
        return tasks[0]

    def test_update_title(self, service, tdl_path):
        assert service.update_task("1", {"title": "New"}) is True
        assert self._reload(tdl_path).title == "New"

    def test_update_priority(self, service, tdl_path):
        assert service.update_task("1", {"priority": "High"}) is True
        assert self._reload(tdl_path).priority is Priority.HIGH

    def test_update_percent_done(self, service, tdl_path):
        assert service.update_task("1", {"percent_done": 100}) is True
        assert self._reload(tdl_path).percent_done == 100

    def test_update_status_independent_of_allocated_to(self, service, tdl_path):
        assert service.update_task("1", {"status": "En curso"}) is True
        assert self._reload(tdl_path).status == "En curso"

    def test_update_description_as_element_child(self, service, tdl_path):
        assert service.update_task("1", {"description": "Desc"}) is True
        assert self._reload(tdl_path).description == "Desc"

    def test_update_due_date(self, service, tdl_path):
        assert service.update_task("1", {"due_date": "2025-06-15"}) is True
        assert self._reload(tdl_path).due_date == date(2025, 6, 15)

    def test_clear_due_date(self, service, tdl_path):
        assert service.update_task("1", {"due_date": ""}) is True
        assert self._reload(tdl_path).due_date is None

    def test_update_category(self, service, tdl_path):
        assert service.update_task("1", {"category": "Work"}) is True
        assert self._reload(tdl_path).category == ["Work"]

    def test_update_time_estimate(self, service, tdl_path):
        assert service.update_task("1", {"time_estimate": 2.5}) is True
        assert self._reload(tdl_path).time_estimate == 2.5

    def test_update_color(self, service, tdl_path):
        assert service.update_task("1", {"color": "3501055"}) is True
        assert self._reload(tdl_path).color == "3501055"

    def test_clear_color(self, service, tdl_path):
        assert service.update_task("1", {"color": ""}) is True
        assert self._reload(tdl_path).color is None

    def test_nonexistent_task(self, service):
        assert service.update_task("99", {"title": "X"}) is False

    def test_all_none_updates(self, service, tdl_path):
        assert service.update_task("1", {}) is True
        assert self._reload(tdl_path).title == "Original"


# ---------------------------------------------------------------------------
# format_tasks_as_markdown
# ---------------------------------------------------------------------------

class TestFormatTasksAsMarkdown:
    def test_empty_tasks(self):
        assert _format_tasks_markdown([]) == ""

    def test_single_task(self):
        tasks = [Task(id="1", title="Hello", pos_string="1")]
        result = _format_tasks_markdown(tasks)
        assert "- [ ]" in result
        assert "**Hello**" in result

    def test_completed_task(self):
        tasks = [Task(id="1", title="Done", pos_string="1", percent_done=100)]
        result = _format_tasks_markdown(tasks)
        assert "- [x]" in result

    def test_nested_children(self):
        parent = Task(id="1", title="Parent", pos_string="1")
        parent.children.append(Task(id="2", title="Child", pos_string="1.1", percent_done=100))
        result = _format_tasks_markdown([parent])
        assert "- [ ]" in result      # Parent (root level, no indent)
        assert "  - [x]" in result    # Child indented by two spaces


# ---------------------------------------------------------------------------
# parse_tdl_file
# ---------------------------------------------------------------------------

class TestParseTdlFile:
    def test_file_not_found_returns_empty(self, tmp_path):
        tasks, next_id, attrs = XmlTodoRepository(str(tmp_path / "nonexistent.tdl")).load_all()
        assert tasks == []
        assert next_id == 1
        assert attrs == {}

    def test_invalid_xml_raises(self, tmp_path):
        path = tmp_path / "bad.tdl"
        path.write_text("not xml", encoding="utf-8")
        with pytest.raises(ET.ParseError):
            XmlTodoRepository(str(path)).load_all()

    def test_valid_empty_xml(self, tmp_path):
        path = tmp_path / "valid.tdl"
        ET.ElementTree(ET.Element("TODOLIST")).write(
            str(path), encoding="utf-8", xml_declaration=True
        )
        tasks, _, _ = XmlTodoRepository(str(path)).load_all()
        assert tasks == []

    def test_save_roundtrip_preserves_root_tag(self, tmp_path):
        """Regression: save_all must write <TODOLIST>, never <TODO>."""
        path = tmp_path / "roundtrip.tdl"
        repo = XmlTodoRepository(str(path))
        repo.save_all([Task(id="1", title="Keep")], 2, {"PROJECTNAME": "p"})
        assert ET.parse(str(path)).getroot().tag == "TODOLIST"
        tasks, next_id, _ = XmlTodoRepository(str(path)).load_all()
        assert [t.title for t in tasks] == ["Keep"]
        assert next_id == 2


