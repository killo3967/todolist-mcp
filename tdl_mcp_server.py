#!/usr/bin/env python3
r"""
MCP Server for ToDoList (.tdl) XML files
Provides tools to read, create, update, search, and manage tasks in ToDoList application format.
Monitors C:\Users\tomas\OneDrive\Documentos\TodoList\Mis proyectos.tdl by default.

Features:
- Read all tasks or filter by date
- Create new tasks with full metadata (title, description, priority, due date, category, status, time estimate)
- Update existing tasks (title, description, priority, due date, category, assignment, progress, status, time estimate)
- Search and filter tasks by various criteria
- Full ToDoList XML format compatibility
"""

import json
import xml.etree.ElementTree as ET
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Literal, Tuple

from pydantic import BaseModel, Field

from mcp.server import MCPServer

# Initialize MCP server with MCPServer
mcp = MCPServer("todolist-mcp-server", version="0.5.0")

# Default file path
DEFAULT_TDL_FILE = r"C:\Users\tomas\OneDrive\Documentos\TodoList\Mis proyectos.tdl"

class ToDoListManager:
    """Manages ToDoList application XML-based .tdl files"""
    
    def __init__(self, base_path: str = None, default_file: str = DEFAULT_TDL_FILE):
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.default_file = default_file
    
    def parse_tdl_file(self, file_path: str = None) -> ET.ElementTree:
        """Parse a .tdl XML file"""
        if file_path is None:
            file_path = self.default_file
            
        try:
            tree = ET.parse(file_path)
            return tree
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML format in {file_path}: {e}")
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
    
    def extract_tasks(self, tree: ET.ElementTree) -> List[Dict[str, Any]]:
        """Extract tasks from ToDoList XML format in a hierarchical structure"""
        root = tree.getroot()
        return self._extract_tasks_recursive(root)

    def _extract_tasks_recursive(self, parent_element: ET.Element) -> List[Dict[str, Any]]:
        """Recursively extract tasks from a parent element."""
        tasks = []
        for task_elem in parent_element.findall('./TASK'):
            task = {}
            
            # Extract from attributes
            task['id'] = task_elem.get('ID', '')
            task['title'] = task_elem.get('TITLE', '')
            task['priority'] = self._decode_priority(task_elem.get('PRIORITY', ''))
            task['status'] = self._decode_status(task_elem)
            task['due_date'] = self._decode_date(task_elem.get('DUEDATE', ''))
            task['created_date'] = self._decode_date(task_elem.get('CREATIONDATE', ''))
            task['percent_done'] = task_elem.get('PERCENTDONE', '0')
            # Leer de elemento hijo <COMMENTS>; si no existe o está vacío, fallback al atributo
            ce = task_elem.find('COMMENTS')
            comments_text = ce.text if ce is not None and ce.text else ''
            if not comments_text:
                comments_text = task_elem.get('COMMENTS', '')
            task['comments'] = comments_text
            task['description'] = comments_text
            task['pos'] = task_elem.get('POS', '')
            task['pos_string'] = task_elem.get('POSSTRING', '')
            task['time_estimate'] = task_elem.get('TIMEESTIMATE', '')

            # Extract categories
            categories = [cat.text.strip() for cat in task_elem.findall('CATEGORY') if cat.text]
            task['category'] = ', '.join(categories)

            # Extract allocations
            allocations = [alloc.text.strip() for alloc in task_elem.findall('ALLOCATEDTO') if alloc.text]
            task['allocated_to'] = ', '.join(allocations)

            # Calculate completion status
            percent = int(task['percent_done']) if task['percent_done'].isdigit() else 0
            task['completed'] = percent >= 100
            
            # Recursively extract children
            task['children'] = self._extract_tasks_recursive(task_elem)
            
            tasks.append(task)
        
        return tasks
    
    def _decode_priority(self, priority_str: str) -> str:
        """Decode ToDoList priority values"""
        if not priority_str or priority_str == '0':
            return 'Normal'
        try:
            priority_val = int(priority_str)
            if priority_val <= -2:
                return 'Low'
            elif priority_val == -1:
                return 'Below Normal'
            elif priority_val == 0:
                return 'Normal'
            elif priority_val == 1:
                return 'Above Normal'
            else:
                return 'High'
        except ValueError:
            return 'Normal'
    
    def _encode_priority(self, priority_str: str) -> str:
        """Encode priority to ToDoList format"""
        priority_map = {
            'Low': '-2',
            'Below Normal': '-1', 
            'Normal': '0',
            'Above Normal': '1',
            'High': '2',
            'Urgent': '3'
        }
        return priority_map.get(priority_str, '0')
    
    def _decode_status(self, task_elem: ET.Element) -> str:
        """Decode task status from STATUS attribute, falling back to PERCENTDONE"""
        status = task_elem.get('STATUS', '')
        if status:
            return status
        percent_done = task_elem.get('PERCENTDONE', '0')
        if percent_done == '100':
            return 'Completed'
        elif percent_done == '0':
            return 'Not Started'
        else:
            return f'{percent_done}% Complete'
    
    def _decode_date(self, date_str: str) -> str:
        """Decode ToDoList date format (Excel serial date)"""
        if not date_str:
            return ''
        
        try:
            # ToDoList uses Excel date serial format
            excel_date = float(date_str)
            # Excel epoch starts 1900-01-01, but has a bug counting 1900 as leap year
            excel_epoch = datetime(1899, 12, 30)  # Adjusted for Excel bug
            python_date = excel_epoch + timedelta(days=excel_date)
            return python_date.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            return date_str
    
    def _encode_date(self, date_str: str) -> str:
        """Encode date to ToDoList Excel serial format"""
        if not date_str:
            return ''
        
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            excel_epoch = datetime(1899, 12, 30)
            delta = date_obj - excel_epoch
            return str(delta.days + (delta.seconds / 86400))
        except ValueError:
            return ''

    @staticmethod
    def _hex_to_rgb_int(hex_color: str) -> str:
        """Convert hex color like '#E65100' to decimal BGR int for ToDoList.
        ToDoList stores COLOR as BGR (not RGB), so we swap R<->B."""
        hex_color = hex_color.lstrip('#')
        # RGB -> BGR: swap first and last byte pair
        bgr = hex_color[4:6] + hex_color[2:4] + hex_color[0:2]
        return str(int(bgr, 16))
    
    def _find_task_by_pos_string(self, root: ET.Element, pos_string: str) -> Optional[ET.Element]:
        """Find a task element by its POSSTRING."""
        if not pos_string:
            return root
        
        parts = pos_string.split('.')
        current_element = root
        
        for i, part in enumerate(parts):
            pos = int(part) - 1
            children = sorted(current_element.findall('./TASK'), key=lambda t: int(t.get('POS', 0)))
            if pos < len(children):
                current_element = children[pos]
                # Final part of the path, we found our element
                if i == len(parts) - 1:
                    return current_element
            else:
                return None
        return None

    def _update_positions(self, parent_element: ET.Element):
        """Update the POS and POSSTRING of all child tasks of a given element."""
        parent_pos_string = parent_element.get('POSSTRING', '')
        
        for i, task_elem in enumerate(parent_element.findall('./TASK')):
            new_pos = str(i)
            if parent_pos_string:
                new_pos_string = f"{parent_pos_string}.{i + 1}"
            else:
                new_pos_string = str(i + 1)
                
            task_elem.set('POS', new_pos)
            task_elem.set('POSSTRING', new_pos_string)
            
            # Recursively update positions for children
            self._update_positions(task_elem)

    def get_next_unique_id(self, root: ET.Element) -> str:
        """Get the next unique ID from ToDoList structure"""
        next_id_str = root.get('NEXTUNIQUEID', '1')
        try:
            next_id = int(next_id_str)
            # Update the NEXTUNIQUEID attribute
            root.set('NEXTUNIQUEID', str(next_id + 1))
            return str(next_id)
        except ValueError:
            return '1'
    
    
    
    def _save_tdl_file(self, tree: ET.ElementTree, file_path: str):
        """Save ToDoList file preserving format"""
        # Write with XML declaration
        tree.write(file_path, encoding='utf-8', xml_declaration=True)
    
    def update_task(self, task_id: str, file_path: str = None, **updates) -> Tuple[bool, str]:
        """Update an existing task in ToDoList format"""
        if file_path is None:
            file_path = self.default_file
            
        try:
            if not Path(file_path).exists():
                return False, f"File not found: {file_path}"
            
            tree = self.parse_tdl_file(file_path)
            root = tree.getroot()
            
            # Find the task by ID
            task_elem = None
            for task in root.findall('.//TASK'):
                if task.get('ID') == task_id:
                    task_elem = task
                    break
            
            if task_elem is None:
                return False, f"Task with ID '{task_id}' not found"
            
            # Track what was updated
            updated_fields = []
            
            # Update basic attributes
            if 'title' in updates and updates['title'] is not None:
                task_elem.set('TITLE', updates['title'])
                updated_fields.append('title')
            
            if 'description' in updates and updates['description'] is not None and updates['description'] != '':
                # Usar elemento hijo <COMMENTS>, no el atributo
                comments_elem = task_elem.find('COMMENTS')
                if comments_elem is None:
                    comments_elem = ET.SubElement(task_elem, 'COMMENTS')
                comments_elem.text = updates['description']
                # Eliminar COMMENTSTYPE para que ToDoList muestre texto plano
                if 'COMMENTSTYPE' in task_elem.attrib:
                    del task_elem.attrib['COMMENTSTYPE']
                if 'COMMENTS' in task_elem.attrib:
                    del task_elem.attrib['COMMENTS']
                updated_fields.append('description')
            
            if 'priority' in updates and updates['priority'] is not None:
                priority_encoded = self._encode_priority(updates['priority'])
                task_elem.set('PRIORITY', priority_encoded)
                task_elem.set('RISK', priority_encoded)  # ToDoList uses same value
                updated_fields.append('priority')
            
            if 'percent_done' in updates and updates['percent_done'] is not None:
                task_elem.set('PERCENTDONE', str(updates['percent_done']))
                updated_fields.append('percent_done')
            
            # Handle due date (support clearing with empty string)
            if 'due_date' in updates:
                if updates['due_date'] == '':
                    # Clear due date
                    if 'DUEDATE' in task_elem.attrib:
                        del task_elem.attrib['DUEDATE']
                    if 'DUEDATESTRING' in task_elem.attrib:
                        del task_elem.attrib['DUEDATESTRING']
                    updated_fields.append('due_date (cleared)')
                elif updates['due_date'] is not None:
                    # Set new due date
                    due_date_encoded = self._encode_date(updates['due_date'])
                    if due_date_encoded:
                        task_elem.set('DUEDATE', due_date_encoded)
                        due_date_obj = datetime.strptime(updates['due_date'], '%Y-%m-%d')
                        task_elem.set('DUEDATESTRING', due_date_obj.strftime('%d/%m/%Y'))
                        updated_fields.append('due_date')
            
            # Handle category (support clearing with empty string)
            if 'category' in updates:
                # Remove existing category elements
                for cat_elem in task_elem.findall('CATEGORY'):
                    task_elem.remove(cat_elem)
                
                if updates['category'] == '':
                    updated_fields.append('category (cleared)')
                elif updates['category'] is not None:
                    # Add new category
                    category_elem = ET.SubElement(task_elem, 'CATEGORY')
                    category_elem.text = updates['category']
                    updated_fields.append('category')
            
            # Handle allocated_to (support clearing with empty string)
            if 'allocated_to' in updates:
                # Remove existing allocation elements
                for alloc_elem in task_elem.findall('ALLOCATEDTO'):
                    task_elem.remove(alloc_elem)
                
                if updates['allocated_to'] == '':
                    updated_fields.append('allocated_to (cleared)')
                elif updates['allocated_to'] is not None:
                    # Add new allocation
                    # Split by comma if multiple people
                    allocations = [a.strip() for a in updates['allocated_to'].split(',') if a.strip()]
                    for allocation in allocations:
                        alloc_elem = ET.SubElement(task_elem, 'ALLOCATEDTO')
                        alloc_elem.text = allocation
                    updated_fields.append('allocated_to')

            # Handle status
            if 'status' in updates and updates['status'] is not None:
                task_elem.set('STATUS', updates['status'])
                updated_fields.append('status')

            # Handle time estimate (in days, float)
            if 'time_estimate' in updates and updates['time_estimate'] is not None:
                task_elem.set('TIMEESTIMATE', str(updates['time_estimate']))
                updated_fields.append('time_estimate')

            # Handle color (hex RGB string)
            if 'color' in updates:
                if updates['color'] == '':
                    # Clear color
                    if 'COLOR' in task_elem.attrib:
                        del task_elem.attrib['COLOR']
                    updated_fields.append('color (cleared)')
                elif updates['color'] is not None:
                    task_elem.set('COLOR', self._hex_to_rgb_int(updates['color']))
                    updated_fields.append('color')

            # Update modification info if any changes were made
            if updated_fields:
                now = datetime.now()
                mod_date = self._encode_date(now.strftime('%Y-%m-%d'))
                task_elem.set('LASTMOD', mod_date)
                task_elem.set('LASTMODSTRING', now.strftime('%d/%m/%Y %I:%M %p'))
                task_elem.set('LASTMODBY', 'PI-AGENT')
                
                # Update root modification time too
                root.set('LASTMOD', mod_date)
                root.set('LASTMODSTRING', now.strftime('%d/%m/%Y %I:%M %p'))
                
                # Save the file
                self._save_tdl_file(tree, file_path)
                
                return True, f"Successfully updated task '{task_id}': {', '.join(updated_fields)}"
            else:
                return False, "No updates specified or all values were None"
                
        except Exception as e:
            return False, f"Error updating task: {str(e)}"

    def add_comment(self, task_id: str, comment: str, file_path: str = None) -> tuple:
        """Append a comment to a task description. Never replaces — always appends."""
        if file_path is None:
            file_path = self.default_file
        try:
            tree = self.parse_tdl_file(file_path)
            root = tree.getroot()
            for task in root.findall('.//TASK'):
                if task.get('ID') == task_id:
                    # Usar elemento hijo <COMMENTS>, no el atributo
                    comments_elem = task.find('COMMENTS')
                    current = comments_elem.text if comments_elem is not None and comments_elem.text else ''
                    # Fallback al atributo si el elemento hijo no existe
                    if not current:
                        current = task.get('COMMENTS', '')
                    new_comment = comment if not current else current + '\n' + comment
                    if comments_elem is None:
                        comments_elem = ET.SubElement(task, 'COMMENTS')
                    comments_elem.text = new_comment
                    # Eliminar COMMENTSTYPE para que ToDoList muestre texto plano
                    if 'COMMENTSTYPE' in task.attrib:
                        del task.attrib['COMMENTSTYPE']
                    if 'COMMENTS' in task.attrib:
                        del task.attrib['COMMENTS']
                    # Update modification timestamp
                    from datetime import datetime
                    now = datetime.now()
                    root.set('LASTMOD', now.strftime('%Y%m%d') + '.' + now.strftime('%H%M%S'))
                    root.set('LASTMODSTRING', now.strftime('%d/%m/%Y %I:%M %p'))
                    self._save_tdl_file(tree, file_path)
                    return True, f"Comment added to task '{task_id}'"
            return False, f"Task with ID '{task_id}' not found"
        except Exception as e:
            return False, f"Error adding comment: {str(e)}"
    
    def filter_tasks_by_date(self, tasks: List[Dict], target_date: date = None) -> List[Dict]:
        """Filter tasks by due date (defaults to today)"""
        if target_date is None:
            target_date = date.today()
        
        today_tasks = []
        
        for task in tasks:
            due_date_str = task.get('due_date', '')
            if not due_date_str:
                continue
                
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                if due_date == target_date:
                    today_tasks.append(task)
            except ValueError:
                continue
        
        return today_tasks
    
    def search_tasks(self, tasks: List[Dict], **filters) -> List[Dict]:
        """Search and filter tasks based on various criteria"""
        filtered_tasks = tasks.copy()
        
        # Filter by search term (title and description)
        if filters.get('search_term'):
            search_term = filters['search_term'].lower()
            filtered_tasks = [
                task for task in filtered_tasks 
                if search_term in task.get('title', '').lower() or 
                   search_term in task.get('description', '').lower()
            ]
        
        # Filter by category
        if filters.get('category'):
            category = filters['category'].lower()
            filtered_tasks = [
                task for task in filtered_tasks 
                if category in task.get('category', '').lower()
            ]
        
        # Filter by priority
        if filters.get('priority'):
            priority = filters['priority']
            filtered_tasks = [
                task for task in filtered_tasks 
                if task.get('priority') == priority
            ]
        
        # Filter by completion status
        if filters.get('completed') is not None:
            completed = filters['completed']
            filtered_tasks = [
                task for task in filtered_tasks 
                if task.get('completed', False) == completed
            ]
        
        # Filter by assigned person
        if filters.get('assigned_to'):
            assigned = filters['assigned_to'].lower()
            filtered_tasks = [
                task for task in filtered_tasks 
                if assigned in task.get('allocated_to', '').lower()
            ]
        
        return filtered_tasks
    
    def format_tasks_as_markdown(self, tasks: List[Dict]) -> str:
        """Convert tasks to Markdown format, preserving hierarchy."""
        if not tasks:
            return "No tasks found."
        
        md_lines = ["# Tasks\n"]
        self._format_tasks_recursive(tasks, md_lines, level=0)
        return "\n".join(md_lines)

    def _format_tasks_recursive(self, tasks: List[Dict], md_lines: List[str], level: int):
        """Recursively format tasks with indentation."""
        indent = "  " * level
        
        for task in sorted(tasks, key=lambda t: int(t.get('pos', 0))):
            title = task.get('title', 'Untitled Task')
            completed = task.get('completed', False)
            pos_string = task.get('pos_string', '')
            task_id = task.get('id', '')
            
            checkbox = "- [x]" if completed else "- [ ]"
            
            md_lines.append(f"{indent}{checkbox} {pos_string} (ID: {task_id}) **{title}**")
            
            details_indent = indent + "  "
            if task.get('description'):
                md_lines.append(f"{details_indent}- Description: {task['description']}")
            if task.get('due_date'):
                md_lines.append(f"{details_indent}- Due: {task['due_date']}")
            if task.get('priority') and task.get('priority') != 'Normal':
                md_lines.append(f"{details_indent}- Priority: {task['priority']}")
            if task.get('category'):
                md_lines.append(f"{details_indent}- Category: {task['category']}")
            if task.get('allocated_to'):
                md_lines.append(f"{details_indent}- Assigned to: {task['allocated_to']}")
            if task.get('percent_done', '0') != '0':
                md_lines.append(f"{details_indent}- Progress: {task['percent_done']}%")
            
            md_lines.append("")

            if task.get('children'):
                self._format_tasks_recursive(task['children'], md_lines, level + 1)

todo_manager = ToDoListManager()

class GetTasksArgs(BaseModel):
    format: Literal['markdown', 'json'] = Field("markdown", description="Output format")

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

class GetTodayTasksArgs(BaseModel):
    target_date: Optional[str] = Field(None, description="Target date in YYYY-MM-DD format (defaults to today)")
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

class AddTaskArgs(BaseModel):
    title: str = Field(..., description="Task title")
    position: Optional[str] = Field(None, description="Position to add the task (e.g., '6.3.4' or parent position '5.3.7')")
    description: Optional[str] = Field(None, description="Task description")
    due_date: Optional[str] = Field(None, description="Due date in YYYY-MM-DD format")
    priority: Literal['Low', 'Below Normal', 'Normal', 'Above Normal', 'High', 'Urgent'] = Field("Normal", description="Task priority")
    category: Optional[str] = Field(None, description="Task category or project")
    status: Optional[str] = Field(None, description="Task status text (e.g. 'Pendiente', 'In Progress', 'Completed')")
    time_estimate: Optional[float] = Field(None, description="Time estimate in days (e.g. 0.125 for 3 hours)")
    color: Optional[str] = Field(None, description="Task color as hex RGB (e.g. '#FF6B35')")

class UpdateTaskArgs(BaseModel):
    task_id: str = Field(..., description="ID of the task to update")
    title: Optional[str] = Field(None, description="New task title")
    description: Optional[str] = Field(None, description="New task description")
    due_date: Optional[str] = Field(None, description="New due date in YYYY-MM-DD format (empty string to clear)")
    priority: Optional[Literal['Low', 'Below Normal', 'Normal', 'Above Normal', 'High', 'Urgent']] = Field(None, description="New task priority")
    category: Optional[str] = Field(None, description="New task category or project (empty string to clear)")
    percent_done: Optional[int] = Field(None, description="Completion percentage (0-100)", ge=0, le=100)
    allocated_to: Optional[str] = Field(None, description="Person(s) assigned to task (empty string to clear)")
    status: Optional[str] = Field(None, description="Task status text (e.g. 'Pendiente', 'In Progress', 'Completed')")
    time_estimate: Optional[float] = Field(None, description="Time estimate in days (e.g. 0.125 for 3 hours)")
    color: Optional[str] = Field(None, description="Task color as hex RGB (e.g. '#FF6B35'). Empty string to clear.")

class AddCommentArgs(BaseModel):
    task_id: str = Field(..., description="ID of the task to add a comment to")
    comment: str = Field(..., description="Comment text to append to the task description")

class SearchTasksArgs(BaseModel):
    search_term: Optional[str] = Field(None, description="Search in task titles and descriptions")
    category: Optional[str] = Field(None, description="Filter by category")
    priority: Optional[Literal['Low', 'Below Normal', 'Normal', 'Above Normal', 'High', 'Urgent']] = Field(None, description="Filter by priority")
    completed: Optional[bool] = Field(None, description="Filter by completion status")
    assigned_to: Optional[str] = Field(None, description="Filter by person assigned")
    format: Literal['markdown', 'json'] = Field("markdown", description="Output format")

class MoveTaskArgs(BaseModel):
    task_id: str = Field(..., description="ID of the task to move")
    new_position: str = Field(..., description="New position for the task (e.g., '6.3.4' or parent position '5.3.7')")

class GetTaskArgs(BaseModel):
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
            # Usar elemento hijo <COMMENTS>, no el atributo
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
        old_parent = root.find(f".//TASK/TASK[@ID='{args.task_id}']/..")
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

        # Fix: stdlib xml.etree.ElementTree no soporta XPath ".." (parent axis).
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

class ReadAnyTdlArgs(BaseModel):
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

if __name__ == "__main__":
    mcp.run()