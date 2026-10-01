from typing import List, Optional, Dict, Any
from datetime import date, datetime

from src.domain.models import Task, Priority
from src.infrastructure.repository import XmlTodoRepository
from src.logger import logger

class TodoService:
    """Service layer for managing ToDoList business logic."""

    def __init__(self, repository: XmlTodoRepository):
        self.repository = repository

    def _get_all_with_root(self) -> tuple[List[Task], int, Dict[str, str]]:
        """Helper to get current state."""
        return self.repository.load_all()

    def get_all_tasks(self) -> List[Task]:
        tasks, _, _ = self._get_all_with_root()
        return tasks

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        tasks, _, _ = self._get_all_with_root()
        return self._find_task_recursive(tasks, task_id)

    def _find_task_recursive(self, tasks: List[Task], task_id: str) -> Optional[Task]:
        for task in tasks:
            if task.id == task_id:
                return task
            if task.children:
                found = self._find_task_recursive(task.children, task_id)
                if found:
                    return found
        return None

    def add_task(self, parent_pos: Optional[str], task_data: Dict[str, Any]) -> Task:
        tasks, next_id, root_attrs = self._get_all_with_root()
        
        # We need to find the parent element to insert the new task
        # Since we are working with objects, we'll find the parent Task object
        new_task = Task(
            id=str(next_id),
            title=task_data['title'],
            priority=Priority.from_str(task_data.get('priority', 'Normal')),
            status=task_data.get('status', 'Not Started'),
            description=task_data.get('description', ''),
            due_date=datetime.strptime(task_data['due_date'], '%Y-%m-%d').date() if task_data.get('due_date') else None,
            created_date=datetime.now().date(),
            percent_done=0,
            pos="", # To be calculated
            pos_string="",
            time_estimate=task_data.get('time_estimate'),
            start_date=datetime.strptime(task_data['start_date'], '%Y-%m-%d').date() if task_data.get('start_date') else None,
            tags=task_data.get('tags', '').split(',') if task_data.get('tags') else [],
            category=task_data.get('category', '').split(',') if task_data.get('category') else [],
            allocated_to=task_data.get('allocated_to', '').split(',') if task_data.get('allocated_to') else [],
            icon=task_data.get('icon'),
            color=task_data.get('color'),
        )
        
        # Clean up empty strings from splits
        new_task.tags = [t.strip() for t in new_task.tags if t.strip()]
        new_task.category = [c.strip() for c in new_task.category if c.strip()]
        new_task.allocated_to = [a.strip() for a in new_task.allocated_to if a.strip()]

        # Find parent and insert
        if not parent_pos:
            tasks.append(new_task)
        else:
            parent = self._find_task_by_pos(tasks, parent_pos)
            if not parent:
                raise ValueError(f"Parent task at position {parent_pos} not found")
            parent.children.append(new_task)

        # Recalculate all positions
        self._recalculate_positions(tasks)
        
        self._save_with_root(tasks, next_id + 1, root_attrs)
        return new_task

    def _find_task_by_pos(self, tasks: List[Task], pos_string: str) -> Optional[Task]:
        if not pos_string:
            return None
        parts = pos_string.split('.')
        
        current_list = tasks
        target_parent = None
        
        for i, part in enumerate(parts):
            try:
                pos = int(part) - 1
            except ValueError:
                return None
                
            if pos < len(current_list):
                target_parent = current_list[pos]
                if i == len(parts) - 1:
                    return target_parent
                current_list = target_parent.children
            else:
                return None
        return None

    def _recalculate_positions(self, tasks: List[Task], parent_pos_string: str = ""):
        for i, task in enumerate(tasks):
            task.pos = str(i)
            task.pos_string = f"{parent_pos_string}.{i+1}" if parent_pos_string else str(i+1)
            if task.children:
                self._recalculate_positions(task.children, task.pos_string)

    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        tasks, next_id, root_attrs = self._get_all_with_root()
        task = self._find_task_recursive(tasks, task_id)
        if not task:
            return False
        
        for key, value in updates.items():
            if value is None:
                continue
            if key == 'due_date' and value == '':
                setattr(task, 'due_date', None)
            elif key == 'start_date' and value == '':
                setattr(task, 'start_date', None)
            elif key == 'description' and value == '':
                task.description = ""
                task.comments = ""
            elif key == 'category' and value == '':
                task.category = []
            elif key == 'allocated_to' and value == '':
                task.allocated_to = []
            elif key == 'tags' and value == '':
                task.tags = []
            elif key == 'priority':
                task.priority = Priority.from_str(value)
            elif key == 'percent_done':
                task.percent_done = int(value)
            elif key == 'due_date':
                task.due_date = datetime.strptime(value, '%Y-%m-%d').date()
            elif key == 'start_date':
                task.start_date = datetime.strptime(value, '%Y-%m-%d').date()
            elif key == 'tags':
                task.tags = [t.strip() for t in value.split(',') if t.strip()]
            elif key == 'category':
                task.category = [c.strip() for c in value.split(',') if c.strip()]
            elif key == 'allocated_to':
                task.allocated_to = [a.strip() for a in value.split(',') if a.strip()]
            else:
                setattr(task, key, value)

        self._recalculate_positions(tasks)
        self._save_with_root(tasks, next_id, root_attrs)
        return True

    def add_comment(self, task_id: str, comment: str) -> bool:
        tasks, next_id, root_attrs = self._get_all_with_root()
        task = self._find_task_recursive(tasks, task_id)
        if not task:
            return False
        
        if task.description:
            task.description += "\n" + comment
        else:
            task.description = comment
        task.comments = task.description
        
        self._save_with_root(tasks, next_id, root_attrs)
        return True

    def move_task(self, task_id: str, new_position: str) -> bool:
        tasks, next_id, root_attrs = self._get_all_with_root()
        
        # 1. Find the task and its old parent
        task_to_move = self._find_task_recursive(tasks, task_id)
        if not task_to_move:
            return False
        
        # 2. Find the old parent to remove it
        old_parent = self._find_parent_of_task(tasks, task_to_move)
        if old_parent:
            old_parent.children.remove(task_to_move)
        else:
            # It's at the root level
            tasks = [t for t in tasks if t.id != task_id]
        
        # 3. Find the new parent
        parts = new_position.split('.')
        parent_pos_string = ".".join(parts[:-1])
        if not parent_pos_string:
            target_container = tasks
        else:
            target_container = self._find_task_by_pos(tasks, parent_pos_string)
            if not target_container:
                raise ValueError(f"New parent at {parent_pos_string} not found")
        
        # 4. Insert
        index = int(parts[-1]) - 1
        if isinstance(target_container, list):
            target_container.insert(max(0, index), task_to_move)
        else:
            target_container.children.insert(max(0, index), task_to_move)
        
        # 5. Recalculate
        self._recalculate_positions(tasks)
        self._save_with_root(tasks, next_id, root_attrs)
        return True

    def _find_parent_of_task(self, tasks: List[Task], target_task: Task) -> Optional[Task]:
        for task in tasks:
            if target_task in task.children:
                return task
            if task.children:
                found = self._find_parent_of_task(task.children, target_task)
                if found:
                    return found
        return None

    def delete_task(self, task_id: str) -> bool:
        tasks, next_id, root_attrs = self._get_all_with_root()
        task = self._find_task_recursive(tasks, task_id)
        if not task:
            return False
        
        parent = self._find_parent_of_task(tasks, task)
        if parent:
            parent.children.remove(task)
        else:
            tasks = [t for t in tasks if t.id != task_id]
            
        self._recalculate_positions(tasks)
        self._save_with_root(tasks, next_id, root_attrs)
        return True

    def get_stats(self) -> Dict[str, Any]:
        tasks = self.get_all_tasks()
        stats = {
            "total": 0,
            "completed": 0,
            "by_status": {},
            "by_priority": {},
            "by_category": {}
        }

        def _traverse(t_list: List[Task]):
            for t in t_list:
                stats["total"] += 1
                if t.completed:
                    stats["completed"] += 1
                
                stats["by_status"][t.status] = stats["by_status"].get(t.status, 0) + 1
                stats["by_priority"][t.priority.name] = stats["by_priority"].get(t.priority.name, 0) + 1
                for cat in t.category:
                    stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1
                
                if t.children:
                    _traverse(t.children)

        _traverse(tasks)
        return stats

    def search_tasks(self, query: str, category: Optional[str] = None, priority: Optional[str] = None, completed: Optional[bool] = None, status: Optional[str] = None, allocated_to: Optional[str] = None) -> List[Task]:
        all_tasks = self.get_all_tasks()
        
        def _flatten(t_list: List[Task]) -> List[Task]:
            flat = []
            for t in t_list:
                flat.append(t)
                if t.children:
                    flat.extend(_flatten(t.children))
            return flat

        flat_tasks = _flatten(all_tasks)
        results = []
        
        for t in flat_tasks:
            if query and query.lower() not in t.title.lower() and query.lower() not in t.description.lower():
                continue
            if category and category.lower() not in [c.lower() for c in t.category]:
                continue
            if priority and t.priority.name != priority.replace(' ', '_').upper():
                continue
            if completed is not None and t.completed != completed:
                continue
            if status and t.status != status:
                continue
            if allocated_to and allocated_to.lower() not in [a.lower() for a in t.allocated_to]:
                continue
            results.append(t)
        return results

    def get_today_tasks(self, target_date: date) -> List[Task]:
        all_tasks = self.get_all_tasks()
        today_tasks = []
        
        def _traverse(t_list: List[Task]):
            for t in t_list:
                if t.due_date == target_date:
                    today_tasks.append(t)
                if t.children:
                    _traverse(t.children)
        
        _traverse(all_tasks)
        return today_tasks

    def _save_with_root(self, tasks: List[Task], next_id: int, root_attrs: Dict[str, str]) -> None:
        """Helper to save current state."""
        self.repository.save_all(tasks, next_id, root_attrs)
