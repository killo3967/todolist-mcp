"""MCP tool handlers for ToDoList server."""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Literal, Any

try:
    from mcp.server import MCPServer as Server
    mcp = Server("todolist-mcp-server", version="1.0.0")
except ImportError:  # mcp 1.x: MCPServer no existe, se usa FastMCP
    from mcp.server import FastMCP as Server
    mcp = Server("todolist-mcp-server")

from src.manager import todo_manager, DEFAULT_TDL_FILE
from src.infrastructure.repository import XmlTodoRepository
from src.logger import logger

def _hex_to_bgr(hex_str: str) -> int:
    """Convert hex RGB string to BGR integer."""
    hex_str = hex_str.lstrip('#')
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    return (b << 16) | (g << 8) | r

def _format_tasks_markdown(tasks, indent: int = 0) -> str:
    """Render tasks as a markdown list, indenting nested subtasks by two spaces."""
    prefix = "  " * indent
    lines = []
    for task in tasks:
        status = "[x]" if task.completed else "[ ]"
        lines.append(f"{prefix}- {status} {task.pos_string} (ID: {task.id}) **{task.title}**")
        if task.children:
            nested = _format_tasks_markdown(task.children, indent + 1)
            if nested:
                lines.append(nested)
    return "\n".join(lines)

@mcp.tool()
def get_my_tasks(format: Literal['markdown', 'json'] = 'json') -> str:
    """Get all tasks from your main ToDoList file"""
    logger.info(f"get_my_tasks called with format: {format}")
    try:
        tasks = todo_manager.service.get_all_tasks()
        
        if format == "json":
            json_tasks = [task.to_dict() for task in tasks]
            return json.dumps(json_tasks, indent=2)
        else:
            md = "# Your Tasks\n\n"
            body = _format_tasks_markdown(tasks)
            if body:
                md += body + "\n"
            return md
    except Exception as e:
        logger.exception("get_my_tasks error")
        return f"Error reading tasks: {str(e)}"


@mcp.tool()
def get_today_tasks(target_date: str | None = None, format: Literal['markdown', 'json'] = 'json') -> str:
    """Get today's tasks from your main ToDoList file"""
    logger.info(f"get_today_tasks called with target_date: {target_date}, format: {format}")
    target_d = date.today()
    if target_date:
        try:
            target_d = datetime.strptime(target_date, '%Y-%m-%d').date()
        except ValueError:
            return f"Invalid date format: {target_date}. Use YYYY-MM-DD"

    try:
        today_tasks = todo_manager.service.get_today_tasks(target_d)
        
        if format == "json":
            json_tasks = [task.to_dict() for task in today_tasks]
            return json.dumps(json_tasks, indent=2)
        else:
            md = f"# Tasks due on {target_d.strftime('%Y-%m-%d')}\n\n"
            body = _format_tasks_markdown(today_tasks)
            if body:
                md += body + "\n"
            return md
    except Exception as e:
        logger.exception("get_today_tasks error")
        return f"Error reading tasks: {str(e)}"

@mcp.tool()
def add_task(
    title: str,
    position: str | None = None,
    description: str | None = None,
    due_date: str | None = None,
    priority: Literal['Low', 'Below Normal', 'Normal', 'Above Normal', 'High', 'Urgent'] = 'Normal',
    category: str | None = None,
    status: str | None = None,
    time_estimate: float | None = None,
    color: str | None = None,
    start_date: str | None = None,
    tags: str | None = None,
    icon: int | None = None
) -> str:
    """Add a new task to your main ToDoList file"""
    logger.info(f"add_task called with params: title={title}, position={position}, category={category}")
    try:
        update_params = {
            "title": title,
            "position": position,
            "description": description,
            "due_date": due_date,
            "priority": priority,
            "category": category,
            "status": status,
            "time_estimate": time_estimate,
            "color": color,
            "start_date": start_date,
            "tags": tags,
            "icon": icon
        }
        update_params = {k: v for k, v in update_params.items() if v is not None}
        
        if 'color' in update_params and isinstance(update_params['color'], str) and update_params['color'].startswith('#'):
            update_params['color'] = _hex_to_bgr(update_params['color'])
        
        new_task = todo_manager.service.add_task(position, update_params)
        return f"Successfully added task '{new_task.title}' at position {new_task.pos_string}"
    except Exception as e:
        logger.exception("add_task error")
        return f"Error adding task: {str(e)} (Check if ToDoList or another app is locking the file)"

@mcp.tool()
def update_task(
    task_id: str | int,
    title: str | None = None,
    description: str | None = None,
    due_date: str | None = None,
    priority: Literal['Low', 'Below Normal', 'Normal', 'Above Normal', 'High', 'Urgent'] | None = None,
    category: str | None = None,
    percent_done: int | None = None,
    allocated_to: str | None = None,
    status: str | None = None,
    time_estimate: float | None = None,
    color: str | None = None,
    start_date: str | None = None,
    tags: str | None = None,
    icon: int | None = None
) -> str:
    """Update an existing task in your main ToDoList file"""
    task_id = str(task_id)
    logger.info(f"update_task called for task {task_id}")
    try:
        update_data = {
            "title": title,
            "description": description,
            "due_date": due_date,
            "priority": priority,
            "category": category,
            "percent_done": percent_done,
            "allocated_to": allocated_to,
            "status": status,
            "time_estimate": time_estimate,
            "color": color,
            "start_date": start_date,
            "tags": tags,
            "icon": icon
        }
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        if not update_data:
            return "No updates"

        if 'color' in update_data and isinstance(update_data['color'], str) and update_data['color'].startswith('#'):
            update_data['color'] = _hex_to_bgr(update_data['color'])
        
        success = todo_manager.service.update_task(task_id, update_data)
        return "Successfully updated task" if success else "Task not found"
    except Exception as e:
        logger.exception("update_task error")
        return f"Error updating task: {str(e)} (Check if ToDoList or another app is locking the file)"

@mcp.tool()
def add_comment(task_id: str | int, comment: str) -> str:
    """Append a comment to a task description."""
    task_id = str(task_id)
    logger.info(f"add_comment called for task {task_id}")
    try:
        success = todo_manager.service.add_comment(task_id, comment)
        return "Comment added" if success else "Comment not found"
    except Exception as e:
        logger.exception("add_comment error")
        return f"Error adding comment: {str(e)}"

@mcp.tool()
def search_tasks(
    search_term: str | None = None,
    category: str | None = None,
    priority: Literal['Low', 'Below Normal', 'Normal', 'Above Normal', 'High', 'Urgent'] | None = None,
    completed: bool | None = None,
    status: str | None = None,
    allocated_to: str | None = None,
    format: Literal['markdown', 'json'] = 'json'
) -> str:
    """Search and filter tasks in your main ToDoList file"""
    logger.info(f"search_tasks called with term={search_term}, category={category}, status={status}")
    try:
        tasks = todo_manager.service.search_tasks(
            query=search_term or "",
            category=category,
            priority=priority,
            completed=completed,
            status=status,
            allocated_to=allocated_to
        )
        
        if not tasks:
            return "No tasks found"

        if format == "json":
            json_tasks = [task.to_dict() for task in tasks]
            return json.dumps(json_tasks, indent=2)
        else:
            md = f"# Search Results ({len(tasks)} tasks found)\n\n"
            body = _format_tasks_markdown(tasks)
            if body:
                md += body + "\n"
            return md
    except Exception as e:
        logger.exception("search_tasks error")
        return f"Error searching tasks: {str(e)}"

@mcp.tool()
def move_task(task_id: str | int, new_position: str) -> str:
    """Move a task to a new position in the hierarchy."""
    task_id = str(task_id)
    logger.info(f"move_task called for task {task_id} to {new_position}")
    try:
        success = todo_manager.service.move_task(task_id, new_position)
        if not success:
            return "Task not found"
        return "Successfully moved task"
    except ValueError as e:
        if "New parent at" in str(e):
             return "Could not find new parent"
        return f"Error moving task: {str(e)} (Check if ToDoList or another app is locking the file)"
    except Exception as e:
        logger.exception("move_task error")
        return f"Error moving task: {str(e)} (Check if ToDoList or another app is locking the file)"

@mcp.tool()
def get_task(task_id: str | int, format: Literal['markdown', 'json'] = 'json') -> str:
    """Get a specific task and its children from your main ToDoList file"""
    task_id = str(task_id)
    logger.info(f"get_task called for task {task_id}")
    try:
        task = todo_manager.service.get_task_by_id(task_id)
        if not task:
            return f"Error: Task with ID '{task_id}' not found."
        
        if format == "json":
            d = task.to_dict()
            if d.get("due_date"):
                d["due_date"] = d["due_date"][:10]
            if d.get("start_date"):
                d["start_date"] = d["start_date"][:10]
            if d.get("created_date"):
                d["created_date"] = d["created_date"][:10]
            return json.dumps([d], indent=2)
        else:
            md = f"# Task Details\n\n"
            md += f"- **Title**: {task.title}\n"
            md += f"- **Status**: {task.status}\n"
            md += f"- **Priority**: {task.priority.name}\n"
            md += f"- **Due**: {task.due_date}\n"
            md += f"- **Description**: {task.description}\n"
            return md
    except Exception as e:
        logger.exception("get_task error")
        return f"Error getting task: {str(e)}"

@mcp.tool()
def get_file_status() -> str:
    """Check the status of your main ToDoList file"""
    logger.info("get_file_status called")
    try:
        stats = todo_manager.service.get_stats()
        repo = XmlTodoRepository(DEFAULT_TDL_FILE)
        _, _, root_attrs = repo.load_all()
        project_name = root_attrs.get('PROJECTNAME', 'ToDoList')
        
        return (f"ToDoList File Status\n\n"
                f"Project: {project_name}\n\n"
                f"Total Tasks: {stats['total']} | Completed: {stats['completed']}\n"
                f"Remaining: {stats['total'] - stats['completed']}")
    except Exception as e:
        logger.exception("get_file_status error")
        return f"Error getting status: {str(e)}"

@mcp.tool()
def read_any_tdl_file(file_path: str, format: Literal['markdown', 'json'] = 'json') -> str:
    """Read tasks from any ToDoList .tdl file"""
    logger.info(f"read_any_tdl_file called for {file_path}")
    try:
        repo = XmlTodoRepository(file_path)
        if '..' in Path(file_path).parts:
            return "Error: Path traversal is blocked."
        if not repo.file_path.exists():
            return f"Error: File {file_path} not found."
        tasks = repo.load_all()[0]
        
        if not tasks:
            return "[]"

        if format == "json":
            json_tasks = [task.to_dict() for task in tasks]
            return json.dumps(json_tasks, indent=2)
        else:
            md = f"# Tasks from {file_path}\n\n"
            body = _format_tasks_markdown(tasks)
            if body:
                md += body + "\n"
            return md
    except Exception as e:
        logger.exception("read_any_tdl_file error")
        err_msg = str(e).lower()
        if "not found" in err_msg or "no such file" in err_msg:
            return f"Error: File {file_path} not found."
        return f"Error reading file {file_path}: {str(e)}"

@mcp.tool()
def analyze_structure() -> str:
    """Analyze the XML structure of your main ToDoList file"""
    logger.info("analyze_structure called")
    try:
        repo = XmlTodoRepository(DEFAULT_TDL_FILE)
        tasks, next_id, root_attrs = repo.load_all()
        
        info = []
        info.append(f"Root Element: TODOLIST")
        info.append(f"Project Name: {root_attrs.get('PROJECTNAME', 'Unknown')}")
        info.append(f"File Version: {root_attrs.get('FILEVERSION', 'Unknown')}")
        info.append(f"App Version: {root_attrs.get('APPVER', 'Unknown')}")
        info.append(f"Next Unique ID: {root_attrs.get('NEXTUNIQUEID', 'Unknown')}")
        info.append(f"Tasks: {len(tasks)}")
        
        categories = set()
        for task in tasks:
            for cat in task.category:
                categories.add(cat)
        info.append(f"Categories: {', '.join(sorted(list(categories))) if categories else 'None'}")
        
        info.append(f"Sample Task Attributes: ID, TITLE, PRIORITY, STATUS, COLOR")
        
        return "\n".join(info)
    except Exception as e:
        logger.exception("analyze_structure error")
        return f"Error analyzing {DEFAULT_TDL_FILE}: {str(e)}"

@mcp.tool()
def complete_task(task_id: str | int, status_text: str = "Completed") -> str:
    """Complete a task."""
    task_id = str(task_id)
    logger.info(f"complete_task called for task {task_id}")
    try:
        updates = {'percent_done': 100, 'status': status_text}
        success = todo_manager.service.update_task(task_id, updates)
        return "Successfully completed task" if success else "Task not found"
    except Exception as e:
        logger.exception("complete_task error")
        return f"Error completing task: {str(e)}"

@mcp.tool()
def delete_task(task_id: str | int) -> str:
    """Delete a task."""
    task_id = str(task_id)
    logger.info(f"delete_task called for task {task_id}")
    try:
        success = todo_manager.service.delete_task(task_id)
        return "Successfully deleted task" if success else "Task not found"
    except Exception as e:
        logger.exception("delete_task error")
        return f"Error deleting task: {str(e)}"

@mcp.tool()
def get_task_stats(format: Literal['markdown', 'json'] = 'json') -> str:
    """Get task statistics."""
    logger.info(f"get_task_stats called")
    try:
        stats = todo_manager.service.get_stats()
        if format == "json":
            return json.dumps(stats, indent=2)
        else:
            md = "# Task Statistics\n\n"
            md += f"- Total Tasks: {stats['total']}\n"
            md += f"- Completed: {stats['completed']}\n\n"
            md += "## By Status\n"
            for status, count in stats['by_status'].items():
                md += f"- {status}: {count}\n"
            md += "\n## By Priority\n"
            for priority, count in stats['by_priority'].items():
                md += f"- {priority}: {count}\n"
            md += "\n## By Category\n"
            for category, count in stats['by_category'].items():
                md += f"- {category}: {count}\n"
            return md
    except Exception as e:
        logger.exception("get_task_stats error")
        return f"Error getting stats: {str(e)}"

@mcp.tool()
def backup_tdl() -> str:
    """Backup the ToDoList file."""
    logger.info("backup_tdl called")
    try:
        import shutil
        src = Path(DEFAULT_TDL_FILE)
        dst = src.with_suffix(src.suffix + ".bak")
        shutil.copy2(src, dst)
        return f"Backup created: {dst}"
    except Exception as e:
        logger.exception("backup_tdl error")
        return f"Error creating backup: {str(e)}"

@mcp.tool()
def restore_tdl() -> str:
    """Restore the ToDoList file from backup."""
    logger.info("restore_tdl called")
    try:
        bak = Path(DEFAULT_TDL_FILE).with_suffix(Path(DEFAULT_TDL_FILE).suffix + ".bak")
        if not bak.exists():
            return "No backup found."
        import shutil
        shutil.copy2(bak, DEFAULT_TDL_FILE)
        return "Restored from backup"
    except Exception as e:
        logger.exception("restore_tdl error")
        return f"Error restoring backup: {str(e)}"

@mcp.tool()
def get_server_logs(lines: int = 100) -> str:
    """Retrieve the recent server logs to diagnose issues"""
    logger.info(f"get_server_logs called with lines: {lines}")
    try:
        from pathlib import Path
        import os
        base_dir = Path(__file__).resolve().parent.parent
        log_path = base_dir / "todolist_mcp.log"
        
        if not log_path.exists():
            return f"No log file found at {log_path}"
            
        with open(log_path, 'r', encoding='utf-8') as f:
            lines_content = f.readlines()
            last_lines = lines_content[-lines:]
            return "".join(last_lines)
    except Exception as e:
        logger.exception("get_server_logs error")
        return f"Error reading logs: {str(e)}"
