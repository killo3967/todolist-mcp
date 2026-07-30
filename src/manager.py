"""ToDoList XML file manager."""

import os
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


def _resolve_tdl_file() -> str:
    env_value = os.environ.get('TODOLIST_FILE')
    if env_value:
        return env_value
    ini_path = Path(__file__).resolve().parent / 'mcp_server.ini'
    if ini_path.exists():
        from configparser import ConfigParser
        cfg = ConfigParser()
        cfg.read(ini_path)
        if cfg.getboolean('server', 'active', fallback=True):
            ini_value = cfg.get('server', 'tdl_file', fallback='')
            if ini_value:
                return ini_value
    # No env var, no INI — use a sensible default
    return os.path.expanduser("~/todolist.tdl")

DEFAULT_TDL_FILE = _resolve_tdl_file()

class ToDoListManager:
    """Manages ToDoList application XML-based .tdl files"""
    
    def __init__(self, base_path: str | None = None, default_file: str = DEFAULT_TDL_FILE):
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.default_file = default_file
    
    def parse_tdl_file(self, file_path: str | None = None) -> ET.ElementTree:
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
    
    def extract_tasks(self, tree: ET.ElementTree) -> list[dict[str, Any]]:
        """Extract tasks from ToDoList XML format in a hierarchical structure"""
        root = tree.getroot()
        return self._extract_tasks_recursive(root)

    def _extract_tasks_recursive(self, parent_element: ET.Element) -> list[dict[str, Any]]:
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
            task['start_date'] = self._decode_date(task_elem.get('STARTDATE', ''))
            tags_list = [t.text.strip() for t in task_elem.findall('TAG') if t.text]
            task['tags'] = ', '.join(tags_list)

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
    
    @staticmethod
    def _escape_xpath_value(value: str) -> str:
        if "'" not in value:
            return f"'{value}'"
        parts = value.split("'")
        quoted = []
        for i, part in enumerate(parts):
            quoted.append(f"'{part}'")
            if i < len(parts) - 1:
                quoted.append("\"'\"")
        return "concat(" + ", ".join(quoted) + ")"

    def _find_task_element(self, root, task_id: str):
        safe_id = self._escape_xpath_value(task_id)
        return root.find(f".//TASK[@ID={safe_id}]")

    @staticmethod
    def _validate_safe_path(file_path: str) -> str:
        from pathlib import Path
        resolved = str(Path(file_path).resolve())
        original = str(Path(file_path))
        if ".." in Path(original).parts:
            raise ValueError(f"Path traversal blocked: {file_path}")
        return resolved

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
    
    def _find_task_by_pos_string(self, root: ET.Element, pos_string: str) -> ET.Element | None:
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

    def _find_parent(self, root, task_id: str):
        for parent in root.iter():
            for child in parent.findall('./TASK'):
                if child.get('ID') == task_id:
                    return parent
        return None

    def _find_task_in_tree(self, tasks: list, target_id: str):
        for t in tasks:
            if t['id'] == target_id:
                return t
            if t.get('children'):
                found = self._find_task_in_tree(t['children'], target_id)
                if found:
                    return found
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
    
    def update_task(self, task_id: str, file_path: str | None = None, **updates) -> tuple[bool, str]:
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
                # Use <COMMENTS> child element, not the attribute
                comments_elem = task_elem.find('COMMENTS')
                if comments_elem is None:
                    comments_elem = ET.SubElement(task_elem, 'COMMENTS')
                comments_elem.text = updates['description']
                # Remove COMMENTSTYPE so ToDoList displays plain text
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

            # Handle start_date
            if 'start_date' in updates:
                if updates['start_date'] == '':
                    if 'STARTDATE' in task_elem.attrib:
                        del task_elem.attrib['STARTDATE']
                    if 'STARTDATESTRING' in task_elem.attrib:
                        del task_elem.attrib['STARTDATESTRING']
                    updated_fields.append('start_date (cleared)')
                elif updates['start_date'] is not None:
                    sd = self._encode_date(updates['start_date'])
                    if sd:
                        task_elem.set('STARTDATE', sd)
                        task_elem.set('STARTDATESTRING', datetime.strptime(updates['start_date'], '%Y-%m-%d').strftime('%d/%m/%Y'))
                        updated_fields.append('start_date')

            # Handle tags
            if 'tags' in updates:
                for tag_elem in task_elem.findall('TAG'):
                    task_elem.remove(tag_elem)
                if updates['tags'] == '':
                    updated_fields.append('tags (cleared)')
                elif updates['tags'] is not None:
                    for tag in updates['tags'].split(','):
                        tag = tag.strip()
                        if tag:
                            t = ET.SubElement(task_elem, 'TAG')
                            t.text = tag
                    updated_fields.append('tags')

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

    def add_comment(self, task_id: str, comment: str, file_path: str | None = None) -> tuple:
        """Append a comment to a task description. Never replaces — always appends."""
        if file_path is None:
            file_path = self.default_file
        try:
            tree = self.parse_tdl_file(file_path)
            root = tree.getroot()
            for task in root.findall('.//TASK'):
                if task.get('ID') == task_id:
                    # Use <COMMENTS> child element, not the attribute
                    comments_elem = task.find('COMMENTS')
                    current = comments_elem.text if comments_elem is not None and comments_elem.text else ''
                    # Fallback to attribute if child element does not exist
                    if not current:
                        current = task.get('COMMENTS', '')
                    new_comment = comment if not current else current + '\n' + comment
                    if comments_elem is None:
                        comments_elem = ET.SubElement(task, 'COMMENTS')
                    comments_elem.text = new_comment
                    # Remove COMMENTSTYPE so ToDoList displays plain text
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
    
    def get_stats(self, tasks):
        by_status = {}
        by_priority = {}
        by_category = {}
        completed = 0
        def _count(task):
            nonlocal completed
            s = task.get('status') or 'Unknown'
            p = task.get('priority') or 'Normal'
            c = task.get('category') or 'None'
            by_status[s] = by_status.get(s, 0) + 1
            by_priority[p] = by_priority.get(p, 0) + 1
            for cat in c.split(', '):
                cat = cat.strip() or 'None'
                by_category[cat] = by_category.get(cat, 0) + 1
            if task.get('completed'):
                completed += 1
            for child in task.get('children', []):
                _count(child)
        for task in tasks:
            _count(task)
        return {
            'total': sum(by_status.values()),
            'completed': completed,
            'by_status': by_status,
            'by_priority': by_priority,
            'by_category': by_category,
        }

    def filter_tasks_by_date(self, tasks: list[dict], target_date: date | None = None) -> list[dict]:
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
    
    def search_tasks(self, tasks: list[dict], **filters) -> list[dict]:
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
        
            
        # Filter by status text
        if filters.get('status'):
            status_filter = filters['status'].lower()
            filtered_tasks = [
                task for task in filtered_tasks
                if status_filter in task.get('status', '').lower()
            ]
        return filtered_tasks
    
    def format_tasks_as_markdown(self, tasks: list[dict]) -> str:
        """Convert tasks to Markdown format, preserving hierarchy."""
        if not tasks:
            return "No tasks found."
        
        md_lines = ["# Tasks\n"]
        self._format_tasks_recursive(tasks, md_lines, level=0)
        return "\n".join(md_lines)

    def _format_tasks_recursive(self, tasks: list[dict], md_lines: list[str], level: int):
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
