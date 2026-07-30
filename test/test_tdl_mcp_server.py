"""Unit tests for ToDoListManager core methods.

Tests use in-memory XML trees — no real .tdl file required.
"""

import xml.etree.ElementTree as ET
from datetime import date, datetime

import pytest

from src.manager import ToDoListManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def manager():
    """Fresh ToDoListManager with no real file dependency."""
    return ToDoListManager(default_file="nonexistent.tdl")


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
    def test_decode_valid_excel_date(self, manager):
        """Excel serial date 44927 = 2023-01-01."""
        assert manager._decode_date("44927") == "2023-01-01"

    def test_decode_empty_string(self, manager):
        assert manager._decode_date("") == ""

    def test_decode_non_numeric(self, manager):
        """Non-numeric returns original string unchanged."""
        assert manager._decode_date("hello") == "hello"

    def test_encode_valid_date(self, manager):
        result = manager._encode_date("2025-09-08")
        assert float(result) > 40000  # days since 1899-12-30

    def test_encode_empty_string(self, manager):
        assert manager._encode_date("") == ""

    def test_encode_invalid_date(self, manager):
        assert manager._encode_date("not-a-date") == ""

    def test_roundtrip(self, manager):
        """encode → decode should return original date."""
        for d in ["2025-01-01", "2024-12-31", "2023-06-15"]:
            encoded = manager._encode_date(d)
            decoded = manager._decode_date(encoded)
            assert decoded == d, f"Roundtrip failed for {d}"


# ---------------------------------------------------------------------------
# _decode_priority / _encode_priority
# ---------------------------------------------------------------------------

class TestPriorityCodec:
    def test_decode_all_levels(self, manager):
        assert manager._decode_priority("-2") == "Low"
        assert manager._decode_priority("-1") == "Below Normal"
        assert manager._decode_priority("0") == "Normal"
        assert manager._decode_priority("1") == "Above Normal"
        assert manager._decode_priority("2") == "High"
        assert manager._decode_priority("3") == "High"  # >=2 all map to High

    def test_decode_empty(self, manager):
        assert manager._decode_priority("") == "Normal"

    def test_decode_invalid(self, manager):
        assert manager._decode_priority("abc") == "Normal"

    def test_encode_all_levels(self, manager):
        assert manager._encode_priority("Low") == "-2"
        assert manager._encode_priority("Below Normal") == "-1"
        assert manager._encode_priority("Normal") == "0"
        assert manager._encode_priority("Above Normal") == "1"
        assert manager._encode_priority("High") == "2"
        assert manager._encode_priority("Urgent") == "3"

    def test_encode_unknown(self, manager):
        assert manager._encode_priority("Unknown") == "0"


# ---------------------------------------------------------------------------
# _hex_to_rgb_int
# ---------------------------------------------------------------------------

class TestHexToRGBInt:
    def test_standard_color(self, manager):
        """#FF6B35 (orange) → BGR."""
        result = manager._hex_to_rgb_int("#FF6B35")
        # R=FF, G=6B, B=35 → BGR = 35 6B FF = 3496959
        # R=FF(255), G=6B(107), B=35(53) → BGR=35 6B FF = 0x356BFF = 3501055
        assert result == "3501055"

    def test_without_hash(self, manager):
        assert manager._hex_to_rgb_int("FF0000") == manager._hex_to_rgb_int("#FF0000")

    def test_black_white(self, manager):
        assert manager._hex_to_rgb_int("#000000") == "0"
        assert manager._hex_to_rgb_int("#FFFFFF") == "16777215"

    def test_bgr_swap(self, manager):
        """Red (#FF0000) becomes blue via BGR swap."""
        result = manager._hex_to_rgb_int("#FF0000")
        # R=FF, G=00, B=00 → BGR = 00 00 FF = 255
        assert result == "255"


# ---------------------------------------------------------------------------
# _decode_status
# ---------------------------------------------------------------------------

class TestDecodeStatus:
    def test_explicit_status(self):
        manager = ToDoListManager()
        elem = ET.Element("TASK", {"STATUS": "In Progress", "PERCENTDONE": "30"})
        assert manager._decode_status(elem) == "In Progress"

    def test_fallback_percent_100(self):
        manager = ToDoListManager()
        elem = ET.Element("TASK", {"PERCENTDONE": "100"})
        assert manager._decode_status(elem) == "Completed"

    def test_fallback_percent_0(self):
        manager = ToDoListManager()
        elem = ET.Element("TASK", {"PERCENTDONE": "0"})
        assert manager._decode_status(elem) == "Not Started"

    def test_fallback_percent_partial(self):
        manager = ToDoListManager()
        elem = ET.Element("TASK", {"PERCENTDONE": "75"})
        assert manager._decode_status(elem) == "75% Complete"

    def test_no_status_no_percent(self):
        manager = ToDoListManager()
        elem = ET.Element("TASK", {})
        assert manager._decode_status(elem) == "Not Started"


# ---------------------------------------------------------------------------
# _find_task_by_pos_string
# ---------------------------------------------------------------------------

class TestFindTaskByPosString:
    @pytest.fixture
    def root(self):
        root = ET.Element("TODOLIST")
        for i in range(3):
            t = ET.SubElement(root, "TASK", {
                "ID": str(i + 1), "POS": str(i), "POSSTRING": str(i + 1),
            })
        # Add child to task 2 (index 1)
        parent = root.findall("./TASK")[1]
        ET.SubElement(parent, "TASK", {
            "ID": "4", "POS": "0", "POSSTRING": "2.1",
        })
        return root

    def test_top_level_first(self, manager, root):
        found = manager._find_task_by_pos_string(root, "1")
        assert found is not None
        assert found.get("ID") == "1"

    def test_top_level_second(self, manager, root):
        found = manager._find_task_by_pos_string(root, "2")
        assert found.get("ID") == "2"

    def test_nested_child(self, manager, root):
        found = manager._find_task_by_pos_string(root, "2.1")
        assert found.get("ID") == "4"

    def test_empty_string_returns_root(self, manager, root):
        found = manager._find_task_by_pos_string(root, "")
        assert found is root

    def test_nonexistent_level(self, manager, root):
        found = manager._find_task_by_pos_string(root, "5")
        assert found is None

    def test_nonexistent_nested(self, manager, root):
        found = manager._find_task_by_pos_string(root, "1.99")
        assert found is None


# ---------------------------------------------------------------------------
# _find_parent
# ---------------------------------------------------------------------------

class TestFindParent:
    @pytest.fixture
    def root(self):
        root = ET.Element("TODOLIST")
        parent = ET.SubElement(root, "TASK", {"ID": "1", "TITLE": "Parent"})
        ET.SubElement(parent, "TASK", {"ID": "2", "TITLE": "Child"})
        ET.SubElement(root, "TASK", {"ID": "3", "TITLE": "Sibling"})
        return root

    def test_find_parent_of_child(self, manager, root):
        found = manager._find_parent(root, "2")
        assert found is not None
        assert found.get("ID") == "1"

    def test_find_parent_of_top_level(self, manager, root):
        found = manager._find_parent(root, "1")
        assert found is root

    def test_nonexistent_task(self, manager, root):
        found = manager._find_parent(root, "99")
        assert found is None


# ---------------------------------------------------------------------------
# _update_positions
# ---------------------------------------------------------------------------

class TestUpdatePositions:
    def test_top_level_positions(self, manager):
        root = ET.Element("TODOLIST")
        ET.SubElement(root, "TASK", {"ID": "1"})
        ET.SubElement(root, "TASK", {"ID": "2"})
        ET.SubElement(root, "TASK", {"ID": "3"})

        manager._update_positions(root)

        tasks = root.findall("./TASK")
        assert tasks[0].get("POS") == "0"
        assert tasks[0].get("POSSTRING") == "1"
        assert tasks[1].get("POS") == "1"
        assert tasks[1].get("POSSTRING") == "2"
        assert tasks[2].get("POS") == "2"
        assert tasks[2].get("POSSTRING") == "3"

    def test_nested_positions(self, manager):
        root = ET.Element("TODOLIST")
        parent = ET.SubElement(root, "TASK", {"ID": "1"})
        ET.SubElement(parent, "TASK", {"ID": "1.1"})
        ET.SubElement(parent, "TASK", {"ID": "1.2"})

        manager._update_positions(root)

        children = parent.findall("./TASK")
        assert children[0].get("POSSTRING") == "1.1"
        assert children[1].get("POSSTRING") == "1.2"


# ---------------------------------------------------------------------------
# get_next_unique_id
# ---------------------------------------------------------------------------

class TestNextUniqueId:
    def test_gets_and_increments(self, manager, empty_root):
        first = manager.get_next_unique_id(empty_root)
        assert first == "10"
        assert empty_root.get("NEXTUNIQUEID") == "11"

    def test_no_nextuniqueid_defaults_1(self, manager):
        root = ET.Element("TODOLIST")
        assert manager.get_next_unique_id(root) == "1"


# ---------------------------------------------------------------------------
# search_tasks
# ---------------------------------------------------------------------------

class TestSearchTasks:
    @pytest.fixture
    def tasks(self):
        return [
            {"id": "1", "title": "Buy milk", "description": "Low-fat",
             "category": "Shopping", "priority": "Normal", "completed": False,
             "allocated_to": "John", "pos": "0"},
            {"id": "2", "title": "Write code", "description": "Python API",
             "category": "Work", "priority": "High", "completed": False,
             "allocated_to": "Jane", "pos": "1"},
            {"id": "3", "title": "Read book", "description": "Sci-fi novel",
             "category": "Leisure", "priority": "Low", "completed": True,
             "allocated_to": "", "pos": "2"},
        ]

    def test_search_by_term_title(self, manager, tasks):
        result = manager.search_tasks(tasks, search_term="code")
        assert len(result) == 1
        assert result[0]["id"] == "2"

    def test_search_by_term_description(self, manager, tasks):
        result = manager.search_tasks(tasks, search_term="sci-fi")
        assert len(result) == 1
        assert result[0]["id"] == "3"

    def test_search_case_insensitive(self, manager, tasks):
        result = manager.search_tasks(tasks, search_term="BUY")
        assert len(result) == 1
        assert result[0]["id"] == "1"

    def test_filter_by_priority(self, manager, tasks):
        result = manager.search_tasks(tasks, priority="High")
        assert len(result) == 1
        assert result[0]["id"] == "2"

    def test_filter_by_completed(self, manager, tasks):
        result = manager.search_tasks(tasks, completed=True)
        assert len(result) == 1
        assert result[0]["id"] == "3"

    def test_filter_by_category(self, manager, tasks):
        result = manager.search_tasks(tasks, category="Shopping")
        assert len(result) == 1
        assert result[0]["id"] == "1"

    def test_filter_by_assigned_to(self, manager, tasks):
        result = manager.search_tasks(tasks, assigned_to="Jane")
        assert len(result) == 1
        assert result[0]["id"] == "2"

    def test_combined_filters(self, manager, tasks):
        result = manager.search_tasks(tasks, completed=False, priority="High")
        assert len(result) == 1
        assert result[0]["id"] == "2"

    def test_no_results(self, manager, tasks):
        result = manager.search_tasks(tasks, search_term="nonexistent")
        assert result == []


# ---------------------------------------------------------------------------
# filter_tasks_by_date
# ---------------------------------------------------------------------------

class TestFilterTasksByDate:
    @pytest.fixture
    def tasks(self):
        return [
            {"id": "1", "title": "Today", "due_date": date.today().strftime("%Y-%m-%d"), "pos": "0"},
            {"id": "2", "title": "Yesterday", "due_date": "2020-01-15", "pos": "1"},
            {"id": "3", "title": "No date", "due_date": "", "pos": "2"},
            {"id": "4", "title": "Invalid date", "due_date": "not-a-date", "pos": "3"},
        ]

    def test_defaults_today(self, manager, tasks):
        result = manager.filter_tasks_by_date(tasks)
        assert len(result) == 1
        assert result[0]["id"] == "1"

    def test_specific_date(self, manager, tasks):
        target = date(2020, 1, 15)
        result = manager.filter_tasks_by_date(tasks, target)
        assert len(result) == 1
        assert result[0]["id"] == "2"

    def test_no_due_date_skipped(self, manager, tasks):
        target = date.today()
        result = manager.filter_tasks_by_date(tasks, target)
        assert all(t["due_date"] != "" for t in result)


# ---------------------------------------------------------------------------
# extract_tasks
# ---------------------------------------------------------------------------

class TestExtractTasks:
    def test_extracts_flat_tasks(self, manager, sample_tree):
        tasks = manager.extract_tasks(sample_tree)
        assert len(tasks) == 1  # "Parent" at top level
        assert tasks[0]["id"] == "1"
        assert tasks[0]["title"] == "Parent"
        assert tasks[0]["priority"] == "High"
        assert tasks[0]["percent_done"] == "50"
        assert tasks[0]["completed"] is False
        assert tasks[0]["category"] == "Work"

    def test_extracts_nested_children(self, manager, sample_tree):
        tasks = manager.extract_tasks(sample_tree)
        children = tasks[0]["children"]
        assert len(children) == 1
        assert children[0]["id"] == "2"
        assert children[0]["title"] == "Child"
        assert children[0]["completed"] is True
        assert children[0]["status"] == "Completed"

    def test_extracts_due_date(self, manager, sample_tree):
        tasks = manager.extract_tasks(sample_tree)
        assert tasks[0]["due_date"] != ""

    def test_extracts_comments(self, manager):
        """COMMENTS element child should be read correctly."""
        root = ET.Element("TODOLIST")
        task = ET.SubElement(root, "TASK", {"ID": "1", "TITLE": "With Comment"})
        comments = ET.SubElement(task, "COMMENTS")
        comments.text = "Hello world"
        tree = ET.ElementTree(root)
        tasks = manager.extract_tasks(tree)
        assert tasks[0]["comments"] == "Hello world"
        assert tasks[0]["description"] == "Hello world"

    def test_comments_fallback_to_attribute(self, manager):
        """If no COMMENTS element, fall back to attribute."""
        root = ET.Element("TODOLIST")
        ET.SubElement(root, "TASK", {"ID": "1", "TITLE": "Attr", "COMMENTS": "legacy"})
        tree = ET.ElementTree(root)
        tasks = manager.extract_tasks(tree)
        assert tasks[0]["comments"] == "legacy"

    def test_comments_element_wins_over_attribute(self, manager):
        """When BOTH exist, element child wins."""
        root = ET.Element("TODOLIST")
        task = ET.SubElement(root, "TASK", {
            "ID": "1", "TITLE": "Both", "COMMENTS": "attribute_val",
        })
        comments = ET.SubElement(task, "COMMENTS")
        comments.text = "element_val"
        tree = ET.ElementTree(root)
        tasks = manager.extract_tasks(tree)
        assert tasks[0]["comments"] == "element_val"


# ---------------------------------------------------------------------------
# add_comment (append behavior)
# ---------------------------------------------------------------------------

class TestAddComment:
    @pytest.fixture
    def tmp_tdl(self, tmp_path):
        """Create a temporary .tdl file with one task."""
        root = ET.Element("TODOLIST", {"NEXTUNIQUEID": "2"})
        task = ET.SubElement(root, "TASK", {
            "ID": "1", "TITLE": "Test Task",
        })
        tree = ET.ElementTree(root)
        path = tmp_path / "test.tdl"
        tree.write(str(path), encoding="utf-8", xml_declaration=True)
        return str(path)

    def test_add_comment_first_time(self, manager, tmp_tdl):
        success, msg = manager.add_comment("1", "First comment", tmp_tdl)
        assert success
        # Verify file was updated
        tree = manager.parse_tdl_file(tmp_tdl)
        tasks = manager.extract_tasks(tree)
        assert "First comment" in tasks[0]["description"]

    def test_add_comment_appends(self, manager, tmp_tdl):
        manager.add_comment("1", "Line 1", tmp_tdl)
        manager.add_comment("1", "Line 2", tmp_tdl)
        tree = manager.parse_tdl_file(tmp_tdl)
        tasks = manager.extract_tasks(tree)
        desc = tasks[0]["description"]
        assert "Line 1" in desc
        assert "Line 2" in desc
        assert desc.index("Line 1") < desc.index("Line 2"), "Line 2 should come after Line 1"

    def test_add_comment_nonexistent_task(self, manager, tmp_tdl):
        success, msg = manager.add_comment("99", "Oops", tmp_tdl)
        assert not success
        assert "not found" in msg


# ---------------------------------------------------------------------------
# update_task
# ---------------------------------------------------------------------------

class TestUpdateTask:
    @pytest.fixture
    def tmp_tdl(self, tmp_path):
        root = ET.Element("TODOLIST", {"NEXTUNIQUEID": "3"})
        ET.SubElement(root, "TASK", {
            "ID": "1", "TITLE": "Original", "PRIORITY": "0",
        })
        tree = ET.ElementTree(root)
        path = tmp_path / "test.tdl"
        tree.write(str(path), encoding="utf-8", xml_declaration=True)
        return str(path)

    def test_update_title(self, manager, tmp_tdl):
        success, msg = manager.update_task("1", title="New Title", file_path=tmp_tdl)
        assert success
        tree = manager.parse_tdl_file(tmp_tdl)
        tasks = manager.extract_tasks(tree)
        assert tasks[0]["title"] == "New Title"

    def test_update_priority(self, manager, tmp_tdl):
        success, msg = manager.update_task("1", priority="High", file_path=tmp_tdl)
        assert success
        tree = manager.parse_tdl_file(tmp_tdl)
        tasks = manager.extract_tasks(tree)
        assert tasks[0]["priority"] == "High"

    def test_update_percent_done(self, manager, tmp_tdl):
        success, msg = manager.update_task("1", percent_done=75, file_path=tmp_tdl)
        assert success
        tree = manager.parse_tdl_file(tmp_tdl)
        tasks = manager.extract_tasks(tree)
        assert tasks[0]["percent_done"] == "75"

    def test_update_status_independent_of_allocated_to(self, manager, tmp_tdl):
        """Regression: status was wrongly nested inside allocated_to block."""
        success, msg = manager.update_task("1", status="Pendiente", file_path=tmp_tdl)
        assert success
        tree = manager.parse_tdl_file(tmp_tdl)
        tasks = manager.extract_tasks(tree)
        assert tasks[0]["status"] == "Pendiente"

    def test_update_description_as_element_child(self, manager, tmp_tdl):
        """Description must go to <COMMENTS> element, not attribute."""
        success, msg = manager.update_task("1", description="New desc", file_path=tmp_tdl)
        assert success
        tree = manager.parse_tdl_file(tmp_tdl)
        root = tree.getroot()
        task = root.find(".//TASK[@ID='1']")
        comments = task.find("COMMENTS")
        assert comments is not None
        assert comments.text == "New desc"
        # Should NOT have COMMENTSTYPE (forces RTF)
        assert "COMMENTSTYPE" not in task.attrib

    def test_update_due_date(self, manager, tmp_tdl):
        success, msg = manager.update_task("1", due_date="2025-12-25", file_path=tmp_tdl)
        assert success
        tree = manager.parse_tdl_file(tmp_tdl)
        root = tree.getroot()
        task = root.find(".//TASK[@ID='1']")
        assert task.get("DUEDATE") != ""

    def test_clear_due_date(self, manager, tmp_tdl):
        manager.update_task("1", due_date="2025-01-01", file_path=tmp_tdl)
        success, msg = manager.update_task("1", due_date="", file_path=tmp_tdl)
        assert success
        tree = manager.parse_tdl_file(tmp_tdl)
        tasks = manager.extract_tasks(tree)
        assert tasks[0]["due_date"] == ""

    def test_update_category(self, manager, tmp_tdl):
        success, msg = manager.update_task("1", category="Urgent", file_path=tmp_tdl)
        assert success
        tree = manager.parse_tdl_file(tmp_tdl)
        tasks = manager.extract_tasks(tree)
        assert tasks[0]["category"] == "Urgent"

    def test_update_time_estimate(self, manager, tmp_tdl):
        success, msg = manager.update_task("1", time_estimate=2.5, file_path=tmp_tdl)
        assert success
        tree = manager.parse_tdl_file(tmp_tdl)
        root = tree.getroot()
        task = root.find(".//TASK[@ID='1']")
        assert task.get("TIMEESTIMATE") == "2.5"

    def test_update_color(self, manager, tmp_tdl):
        success, msg = manager.update_task("1", color="#4CAF50", file_path=tmp_tdl)
        assert success
        tree = manager.parse_tdl_file(tmp_tdl)
        root = tree.getroot()
        task = root.find(".//TASK[@ID='1']")
        assert task.get("COLOR") is not None

    def test_clear_color(self, manager, tmp_tdl):
        manager.update_task("1", color="#4CAF50", file_path=tmp_tdl)
        success, msg = manager.update_task("1", color="", file_path=tmp_tdl)
        assert success
        tree = manager.parse_tdl_file(tmp_tdl)
        root = tree.getroot()
        task = root.find(".//TASK[@ID='1']")
        assert "COLOR" not in task.attrib

    def test_nonexistent_task(self, manager, tmp_tdl):
        success, msg = manager.update_task("99", title="Boom", file_path=tmp_tdl)
        assert not success
        assert "not found" in msg

    def test_all_none_updates(self, manager, tmp_tdl):
        success, msg = manager.update_task("1", title=None, priority=None, file_path=tmp_tdl)
        assert not success
        assert "No updates" in msg


# ---------------------------------------------------------------------------
# format_tasks_as_markdown
# ---------------------------------------------------------------------------

class TestFormatTasksAsMarkdown:
    def test_empty_tasks(self, manager):
        assert manager.format_tasks_as_markdown([]) == "No tasks found."

    def test_single_task(self, manager):
        tasks = [{"id": "1", "title": "Hello", "completed": False, "pos": "0",
                   "pos_string": "1"}]
        result = manager.format_tasks_as_markdown(tasks)
        assert "- [ ]" in result
        assert "**Hello**" in result

    def test_completed_task(self, manager):
        tasks = [{"id": "1", "title": "Done", "completed": True, "pos": "0",
                   "pos_string": "1"}]
        result = manager.format_tasks_as_markdown(tasks)
        assert "- [x]" in result

    def test_nested_children(self, manager):
        tasks = [{
            "id": "1", "title": "Parent", "completed": False, "pos": "0",
            "pos_string": "1",
            "children": [{
                "id": "2", "title": "Child", "completed": True, "pos": "0",
                "pos_string": "1.1", "children": [],
            }],
        }]
        result = manager.format_tasks_as_markdown(tasks)
        assert "- [ ]" in result  # Parent (root level, no indent)
        assert "  - [x]" in result  # Child (one level indented)


# ---------------------------------------------------------------------------
# parse_tdl_file
# ---------------------------------------------------------------------------

class TestParseTdlFile:
    def test_file_not_found(self, manager):
        with pytest.raises(FileNotFoundError):
            manager.parse_tdl_file("nonexistent.tdl")

    def test_invalid_xml(self, manager, tmp_path):
        path = tmp_path / "bad.tdl"
        path.write_text("not xml", encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid XML"):
            manager.parse_tdl_file(str(path))

    def test_valid_xml(self, manager, tmp_path):
        path = tmp_path / "valid.tdl"
        root = ET.Element("TODOLIST")
        tree = ET.ElementTree(root)
        tree.write(str(path), encoding="utf-8", xml_declaration=True)
        result = manager.parse_tdl_file(str(path))
        assert result.getroot().tag == "TODOLIST"


