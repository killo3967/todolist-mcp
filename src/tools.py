"""MCP tool handlers for ToDoList server."""

import json
import xml.etree.ElementTree as ET
from datetime import date, datetime
from pathlib import Path
from typing import Literal

from mcp.server import MCPServer

from src.manager import DEFAULT_TDL_FILE, todo_manager
from src.models import *

mcp = MCPServer("todolist-mcp-server", version="1.0.0")

@mcp.tool()
def get_my_tasks(args: GetTasksArgs) -> str:
    """Get all tasks from your main ToDoList file"""
    if not Path(DEFAULT_TDL_FILE).exists():
        return f"Your main todolist file doesn't exist: {DEFAULT_TDL_FILE}"
    
    try:
        tree = todo_manager.parse_tdl_file()
        tasks = todo_manager.extract_tasks(tree)
        
        if args.format == "json":
            json_tasks = [{k: v for k, v in task.items() if k != 'xml_element'} for task in tasks]
            return json.dumps(json_tasks, indent=2)
        else:
            return f"# Your Tasks ({DEFAULT_TDL_FILE})\n\n" + todo_manager.format_tasks_as_markdown(tasks)
    except Exception as e:
        return f"Error reading tasks: {str(e)}"

    target_date: str | None = Field(None, description="Target date in YYYY-MM-DD format (defaults to today)")
    format: Literal['markdown', 'json'] = Field("markdown", description="Output format")

@mcp.tool()
def get_today_tasks(args: GetTodayTasksArgs) -> str:
    """Get today's tasks from your main ToDoList file"""
    target_d = date.today()
    if args.target_date:
        try:
            target_d = datetime.strptime(args.target_date, '%Y-%m-%d').date()
        except ValueError:
            return f"Invalid date format: {args.target_date}. Use YYYY-MM-DD"

    if not Path(DEFAULT_TDL_FILE).exists():
        return f"Your main todolist file doesn't exist: {DEFAULT_TDL_FILE}"

    try:
        tree = todo_manager.parse_tdl_file()
        all_tasks = todo_manager.extract_tasks(tree)
        today_tasks = todo_manager.filter_tasks_by_date(all_tasks, target_d)

        if args.format == "json":
            json_tasks = [{k: v for k, v in task.items() if k != 'xml_element'} for task in today_tasks]
            return json.dumps(json_tasks, indent=2)
        else:
            date_str = target_d.strftime('%Y-%m-%d')
            if today_tasks:
                return f"# Tasks due on {date_str}\n\n" + todo_manager.format_tasks_as_markdown(today_tasks)
            else:
                return f"No tasks due on {date_str}"
    except Exception as e:
        return f"Error reading tasks: {str(e)}"

    title: str = Field(..., description="Task title")
    position: str | None = Field(None, description="Position to add the task (e.g., '6.3.4' or parent position '5.3.7')")
    description: str | None = Field(None, description="Task description")
    due_date: str | None = Field(None, description="Due date in YYYY-MM-DD format")
    priority: Literal['Low', 'Below Normal', 'Normal', 'Above Normal', 'High', 'Urgent'] = Field("Normal", description="Task priority")
    category: str | None = Field(None, description="Task category or project")
    status: str | None = Field(None, description="Task status text (e.g. 'Pendiente', 'In Progress', 'Completed')")
    time_estimate: float | None = Field(None, description="Time estimate in days (e.g. 0.125 for 3 hours)")
    color: str | None = Field(None, description="Task color as hex RGB (e.g. '#FF6B35')")
    start_date: str | None = Field(None, description="Start date in YYYY-MM-DD format")
    tags: str | None = Field(None, description="Comma-separated tags (e.g. 'bug, urgent, frontend')")

    task_id: str = Field(..., description="ID of the task to update")
    title: str | None = Field(None, description="New task title")
    description: str | None = Field(None, description="New task description")
    due_date: str | None = Field(None, description="New due date in YYYY-MM-DD format (empty string to clear)")
    priority: Literal['Low', 'Below Normal', 'Normal', 'Above Normal', 'High', 'Urgent'] | None = Field(None, description="New task priority")
    category: str | None = Field(None, description="New task category or project (empty string to clear)")
    percent_done: int | None = Field(None, description="Completion percentage (0-100)", ge=0, le=100)
    allocated_to: str | None = Field(None, description="Person(s) assigned to task (empty string to clear)")
    status: str | None = Field(None, description="Task status text (e.g. 'Pendiente', 'In Progress', 'Completed')")
    time_estimate: float | None = Field(None, description="Time estimate in days (e.g. 0.125 for 3 hours)")
    color: str | None = Field(None, description="Task color as hex RGB (e.g. '#FF6B35'). Empty string to clear.")

    task_id: str = Field(..., description="ID of the task to add a comment to")
    comment: str = Field(..., description="Comment text to append to the task description")

    task_id: str = Field(..., description="ID of the task to complete")
    status_text: str = Field("Completed", description="Status text to set (e.g. 'Terminado', 'Completed')")

    format: Literal['markdown', 'json'] = Field("markdown", description="Output format")

    search_term: str | None = Field(None, description="Search in task titles and descriptions")
    category: str | None = Field(None, description="Filter by category")
    priority: Literal['Low', 'Below Normal', 'Normal', 'Above Normal', 'High', 'Urgent'] | None = Field(None, description="Filter by priority")
    status: str | None = Field(None, description="Filter by status text (e.g. 'Pendiente', 'En curso', 'Terminado')")
    completed: bool | None = Field(None, description="Filter by completion status")
    assigned_to: str | None = Field(None, description="Filter by person assigned")
    format: Literal['markdown', 'json'] = Field("markdown", description="Output format")

    task_id: str = Field(..., description="ID of the task to move")
    new_position: str = Field(..., description="New position for the task (e.g., '6.3.4' or parent position '5.3.7')")

    task_id: str = Field(..., description="ID of the task to retrieve")
    format: Literal['markdown', 'json'] = Field("markdown", description="Output format")


@mcp.tool()
def add_task(args: AddTaskArgs) -> str:
    """Add a new task to your main ToDoList file"""
    if not Path(DEFAULT_TDL_FILE).exists():
        return f"Error: ToDoList file doesn't exist: {DEFAULT_TDL_FILE}. Please open ToDoList first to create the file."
    
    try:
        tree = todo_manager.parse_tdl_file()
        root = tree.getroot()
        
        task_data = args.dict()
        
        # Find parent and insertion index
        parent_pos_string = ""
        insert_index = -1

        if args.position:
            # Position is always treated as the parent path to append to.
            # This avoids the ambiguity where a single-part position like "5"
            # could be misread as "insert before task 5" instead of "append to task 5".
            parent_pos_string = args.position

        parent_element = todo_manager._find_task_by_pos_string(root, parent_pos_string)
        if parent_element is None:
            if not parent_pos_string: # Top-level
                parent_element = root
            else:
                return f"Error: Could not find parent task at position {parent_pos_string}"

        # Get next unique ID
        task_id = todo_manager.get_next_unique_id(root)
        
        # Create new TASK element
        new_task = ET.Element('TASK')
        new_task.set('ID', task_id)
        new_task.set('TITLE', task_data.get('title', ''))
        
        # Set other attributes...
        now = datetime.now()
        creation_date = todo_manager._encode_date(now.strftime('%Y-%m-%d'))
        new_task.set('CREATIONDATE', creation_date)
        new_task.set('CREATIONDATESTRING', now.strftime('%d/%m/%Y %I:%M %p'))
        new_task.set('LASTMOD', creation_date)
        new_task.set('LASTMODSTRING', now.strftime('%d/%m/%Y %I:%M %p'))
        new_task.set('LASTMODBY', 'PI-AGENT')
        if task_data.get('description'):
            # Use <COMMENTS> child element, not the attribute
            comments_elem = ET.SubElement(new_task, 'COMMENTS')
            comments_elem.text = task_data['description']
        priority_encoded = todo_manager._encode_priority(task_data.get('priority', 'Normal'))
        new_task.set('PRIORITY', priority_encoded)
        if task_data.get('due_date'):
            due_date_encoded = todo_manager._encode_date(task_data['due_date'])
            if due_date_encoded:
                new_task.set('DUEDATE', due_date_encoded)
                due_date_obj = datetime.strptime(task_data['due_date'], '%Y-%m-%d')
                new_task.set('DUEDATESTRING', due_date_obj.strftime('%d/%m/%Y'))
        if task_data.get('category'):
            category_elem = ET.SubElement(new_task, 'CATEGORY')
            category_elem.text = task_data['category']
        if task_data.get('status'):
            new_task.set('STATUS', task_data['status'])
        if task_data.get('time_estimate'):
            new_task.set('TIMEESTIMATE', str(task_data['time_estimate']))
        if task_data.get('color'):
            new_task.set('COLOR', todo_manager._hex_to_rgb_int(task_data['color']))
        if task_data.get('start_date'):
            sd = todo_manager._encode_date(task_data['start_date'])
            if sd:
                new_task.set('STARTDATE', sd)
                new_task.set('STARTDATESTRING', datetime.strptime(task_data['start_date'], '%Y-%m-%d').strftime('%d/%m/%Y'))
        if task_data.get('tags'):
            for tag in task_data['tags'].split(','):
                tag = tag.strip()
                if tag:
                    t = ET.SubElement(new_task, 'TAG')
                    t.text = tag

        # Insert and update positions
        if insert_index != -1:
            parent_element.insert(insert_index, new_task)
        else:
            parent_element.append(new_task)
            
        todo_manager._update_positions(parent_element if parent_element is not root else root)

        # Save the file
        todo_manager._save_tdl_file(tree, DEFAULT_TDL_FILE)
        
        return f"Successfully added task '{task_data['title']}' at position {new_task.get('POSSTRING')}"

    except Exception as e:
        return f"Error adding task: {str(e)}"

@mcp.tool()
def update_task(args: UpdateTaskArgs) -> str:
    """Update an existing task in your main ToDoList file"""
    if not Path(DEFAULT_TDL_FILE).exists():
        return f"Error: ToDoList file doesn't exist: {DEFAULT_TDL_FILE}. Please open ToDoList first to create the file."
    
    try:
        # Convert args to dict and filter out None values for optional parameters
        update_data = {k: v for k, v in args.dict().items() if k != 'task_id' and v is not None}
        
        # Call the update method
        success, message = todo_manager.update_task(args.task_id, **update_data)
        
        return message
        
    except Exception as e:
        return f"Error updating task: {str(e)}"


@mcp.tool()
def add_comment(args: AddCommentArgs) -> str:
    """Append a comment to a task description. Unlike update_task, this NEVER replaces — it always appends."""
    if not Path(DEFAULT_TDL_FILE).exists():
        return f"Error: ToDoList file doesn't exist: {DEFAULT_TDL_FILE}"
    try:
        success, message = todo_manager.add_comment(args.task_id, args.comment)
        return message
    except Exception as e:
        return f"Error adding comment: {str(e)}"
@mcp.tool()
def search_tasks(args: SearchTasksArgs) -> str:
    """Search and filter tasks in your main ToDoList file"""
    if not Path(DEFAULT_TDL_FILE).exists():
        return f"Your main todolist file doesn't exist: {DEFAULT_TDL_FILE}"
    
    try:
        tree = todo_manager.parse_tdl_file()
        all_tasks = todo_manager.extract_tasks(tree)
        
        # Create filter dict from args, excluding format and None values
        filters = {k: v for k, v in args.dict().items() if k != 'format' and v is not None}
        
        # Search tasks
        filtered_tasks = todo_manager.search_tasks(all_tasks, **filters)
        
        if not filtered_tasks:
            return "No tasks found matching the search criteria."
        
        if args.format == "json":
            json_tasks = [{k: v for k, v in task.items() if k != 'xml_element'} for task in filtered_tasks]
            return json.dumps(json_tasks, indent=2)
        else:
            result = f"# Search Results ({len(filtered_tasks)} tasks found)\n\n"
            if filters:
                filter_desc = []
                for key, value in filters.items():
                    filter_desc.append(f"{key.replace('_', ' ')}: {value}")
                result += f"**Filters:** {', '.join(filter_desc)}\n\n"
            
            result += todo_manager.format_tasks_as_markdown(filtered_tasks)
            return result
            
    except Exception as e:
        return f"Error searching tasks: {str(e)}"

@mcp.tool()
def move_task(args: MoveTaskArgs) -> str:
    """Move a task to a new position in the hierarchy."""
    if not Path(DEFAULT_TDL_FILE).exists():
        return f"Error: ToDoList file doesn't exist: {DEFAULT_TDL_FILE}."

    try:
        tree = todo_manager.parse_tdl_file()
        root = tree.getroot()

        # Find the task to move
        task_to_move = root.find(f".//TASK[@ID='{args.task_id}']")
        if task_to_move is None:
            return f"Error: Task with ID '{args.task_id}' not found."

        # Find the new parent element
        parts = args.new_position.split('.')
        parent_pos_string = ".".join(parts[:-1])
        insert_index = int(parts[-1]) - 1

        new_parent = todo_manager._find_task_by_pos_string(root, parent_pos_string)
        if new_parent is None:
            if not parent_pos_string: # Top-level
                new_parent = root
            else:
                return f"Error: Could not find new parent task at position {parent_pos_string}"

        # Detach from old parent
        old_parent = todo_manager._find_parent(root, args.task_id)
        if old_parent is None:
            old_parent = root
        
        old_parent.remove(task_to_move)
        todo_manager._update_positions(old_parent)

        # Attach to new parent
        new_parent.insert(insert_index, task_to_move)
        todo_manager._update_positions(new_parent)

        todo_manager._save_tdl_file(tree, DEFAULT_TDL_FILE)
        return f"Successfully moved task {args.task_id} to position {task_to_move.get('POSSTRING')}"

    except Exception as e:
        return f"Error moving task: {str(e)}"

@mcp.tool()
def get_task(args: GetTaskArgs) -> str:
    """Get a specific task and its children from your main ToDoList file"""
    if not Path(DEFAULT_TDL_FILE).exists():
        return f"Your main todolist file doesn't exist: {DEFAULT_TDL_FILE}"
    
    try:
        tree = todo_manager.parse_tdl_file()
        root = tree.getroot()

        task_elem = root.find(f".//TASK[@ID='{args.task_id}']")
        if task_elem is None:
            return f"Error: Task with ID '{args.task_id}' not found."

        # stdlib ElementTree does not support XPath ".." (parent axis).
        # Extraemos todas las tareas y buscamos recursivamente para preservar la jerarquía.
        all_tasks = todo_manager.extract_tasks(tree)

        def _find_task(tasks, target_id):
            for t in tasks:
                if t['id'] == target_id:
                    return t
                if t.get('children'):
                    found = _find_task(t['children'], target_id)
                    if found:
                        return found
            return None

        task = _find_task(all_tasks, args.task_id)
        if task is None:
            return f"Error: Task with ID '{args.task_id}' not found."
        task = [task]


        if args.format == "json":
            return json.dumps(task, indent=2)
        else:
            return "# Task Details\n\n" + todo_manager.format_tasks_as_markdown(task)
            
    except Exception as e:
        return f"Error getting task: {str(e)}"

@mcp.tool()
def get_file_status() -> str:
    """Check the status of your main ToDoList file"""
    file_path = Path(DEFAULT_TDL_FILE)
    
    if not file_path.exists():
        return f"Your main todolist file doesn't exist: {DEFAULT_TDL_FILE}"

    stat = file_path.stat()
    modified = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    size = stat.st_size
    
    try:
        tree = todo_manager.parse_tdl_file()
        root = tree.getroot()
        tasks = todo_manager.extract_tasks(tree)
        
        # Get ToDoList file info
        project_name = root.get('PROJECTNAME', 'Unknown')
        file_version = root.get('FILEVERSION', 'Unknown')
        app_version = root.get('APPVER', 'Unknown')
        
        task_count = len(tasks)
        completed = len([t for t in tasks if t.get('completed', False)])
        
        return f"""ToDoList File Status
File: {DEFAULT_TDL_FILE}
Project: {project_name}
Size: {size} bytes
Last Modified: {modified}
File Version: {file_version}
App Version: {app_version}
Total Tasks: {task_count}
Completed: {completed}
Remaining: {task_count - completed}"""
    
    except Exception as e:
        return f"""ToDoList File Status
File: {DEFAULT_TDL_FILE}
Size: {size} bytes  
Last Modified: {modified}
Warning: Error reading tasks: {str(e)}"""

    file_path: str = Field(..., description="Path to the .tdl file")
    format: Literal['markdown', 'json'] = Field("markdown", description="Output format")

@mcp.tool()
def read_any_tdl_file(args: ReadAnyTdlArgs) -> str:
    """Read tasks from any ToDoList .tdl file"""
    try:
        tree = todo_manager.parse_tdl_file(args.file_path)
        tasks = todo_manager.extract_tasks(tree)
        
        if args.format == "json":
            json_tasks = [{k: v for k, v in task.items() if k != 'xml_element'} for task in tasks]
            return json.dumps(json_tasks, indent=2)
        else:
            return f"# Tasks from {args.file_path}\n\n" + todo_manager.format_tasks_as_markdown(tasks)
    except Exception as e:
        return f"Error reading file {args.file_path}: {str(e)}"

@mcp.tool()
def analyze_structure() -> str:
    """Analyze the XML structure of your main ToDoList file"""
    if not Path(DEFAULT_TDL_FILE).exists():
        return f"Your main todolist file doesn't exist yet: {DEFAULT_TDL_FILE}"
    
    try:
        tree = todo_manager.parse_tdl_file()
        root = tree.getroot()
        
        # Show ToDoList specific structure
        info = []
        info.append(f"Root Element: {root.tag}")
        info.append(f"Project Name: {root.get('PROJECTNAME', 'Unknown')}")
        info.append(f"File Version: {root.get('FILEVERSION', 'Unknown')}")
        info.append(f"App Version: {root.get('APPVER', 'Unknown')}")
        info.append(f"Next Unique ID: {root.get('NEXTUNIQUEID', 'Unknown')}")
        
        # Count different elements
        tasks = root.findall('.//TASK')
        categories = root.findall('.//CATEGORY')
        statuses = root.findall('.//STATUS')
        
        info.append("\nElement Counts:")
        info.append(f"Tasks: {len(tasks)}")
        info.append(f"Categories: {len(set(cat.text for cat in categories if cat.text))}")
        info.append(f"Statuses: {len(set(stat.text for stat in statuses if stat.text))}")
        
        # Show task attributes structure
        if tasks:
            sample_task = tasks[0]
            info.append("\nSample Task Attributes:")
            for attr, value in sample_task.attrib.items():
                info.append(f"  {attr}: {value[:50]}..." if len(value) > 50 else f"  {attr}: {value}")
        
        return "\n".join(info)
        
    except Exception as e:
        return f"Error analyzing {DEFAULT_TDL_FILE}: {str(e)}"

@mcp.tool()
def complete_task(args: CompleteTaskArgs) -> str:
    if not Path(DEFAULT_TDL_FILE).exists():
        return f"Error: ToDoList file doesn't exist: {DEFAULT_TDL_FILE}."
    try:
        success, message = todo_manager.update_task(
            args.task_id, percent_done=100, status=args.status_text)
        if success:
            return f"Successfully completed task '{args.task_id}' with status '{args.status_text}'."
        return message
    except Exception as e:
        return f"Error completing task: {str(e)}"

@mcp.tool()
def delete_task(args: DeleteTaskArgs) -> str:
    if not Path(DEFAULT_TDL_FILE).exists():
        return f"Error: ToDoList file doesn't exist: {DEFAULT_TDL_FILE}."
    try:
        tree = todo_manager.parse_tdl_file()
        root = tree.getroot()
        task = todo_manager._find_task_element(root, args.task_id)
        if task is None:
            return f"Error: Task with ID '{args.task_id}' not found."
        parent = todo_manager._find_parent(root, args.task_id)
        if parent is None:
            parent = root
        parent.remove(task)
        todo_manager._update_positions(parent)
        todo_manager._save_tdl_file(tree, DEFAULT_TDL_FILE)
        return f"Successfully deleted task '{args.task_id}'."
    except Exception as e:
        return f"Error deleting task: {str(e)}"


@mcp.tool()
def get_task_stats(args: GetTaskStatsArgs) -> str:
    if not Path(DEFAULT_TDL_FILE).exists():
        return f"Your main todolist file doesn't exist: {DEFAULT_TDL_FILE}"
    try:
        tree = todo_manager.parse_tdl_file()
        tasks = todo_manager.extract_tasks(tree)
        stats = todo_manager.get_stats(tasks)
        if args.format == "json":
            return json.dumps(stats, indent=2)
        NL = chr(10)
        lines = ["# Task Statistics", ""]
        rem = stats["total"] - stats["completed"]
        lines.append(f"**Total**: {stats['total']} | **Completed**: {stats['completed']} | **Remaining**: {rem}")
        for title, data in [("By Status", stats["by_status"]), ("By Priority", stats["by_priority"]), ("By Category", stats["by_category"])]:
            lines.append(NL + "## " + title)
            for key, count in sorted(data.items(), key=lambda x: -x[1]):
                lines.append(f"- **{key}**: {count}")
        return NL.join(lines)
    except Exception as e:
        return f"Error getting stats: {str(e)}"


@mcp.tool()
def backup_tdl() -> str:
    """Create a backup of the current .tdl file in the same directory."""
    if not Path(DEFAULT_TDL_FILE).exists():
        return f"Error: ToDoList file doesn't exist: {DEFAULT_TDL_FILE}"
    try:
        src = Path(DEFAULT_TDL_FILE)
        dst = Path(str(src) + ".bak")
        dst.write_bytes(src.read_bytes())
        return f"Backup created: {dst} ({dst.stat().st_size} bytes)"
    except Exception as e:
        return f"Error creating backup: {str(e)}"


@mcp.tool()
def restore_tdl() -> str:
    """Restore the .tdl file from the last backup."""
    try:
        bak = Path(str(DEFAULT_TDL_FILE) + ".bak")
        if not bak.exists():
            return "Error: No backup found. Run backup_tdl first."
        dst = Path(DEFAULT_TDL_FILE)
        dst.write_bytes(bak.read_bytes())
        return f"Restored from backup: {bak} ({bak.stat().st_size} bytes)"
    except Exception as e:
        return f"Error restoring backup: {str(e)}"


