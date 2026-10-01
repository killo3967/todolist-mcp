import os
import base64
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import List, Optional

from src.domain.models import Task, Priority
from src.lock import FileLock
from src.logger import logger

class XmlTodoRepository:
    """Repository for managing ToDoList XML files."""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

    def _decode_date(self, date_str: str) -> Optional[date]:
        if not date_str:
            return None
        try:
            excel_date = float(date_str)
            excel_epoch = datetime(1899, 12, 30)
            return (excel_epoch + timedelta(days=excel_date)).date()
        except (ValueError, TypeError):
            return None

    def _encode_date(self, dt: datetime) -> str:
        """Encode date to ToDoList Excel serial format"""
        if not dt:
            return ''
        
        try:
            # Ensure dt is a datetime object for subtraction
            if isinstance(dt, date) and not isinstance(dt, datetime):
                dt = datetime.combine(dt, datetime.min.time())
                
            excel_epoch = datetime(1899, 12, 30)
            delta = dt - excel_epoch
            return str(delta.days + (delta.seconds / 86400))
        except (ValueError, TypeError):
            return ''

    def _decode_priority(self, priority_str: str) -> Priority:
        return Priority.from_str(priority_str)

    def _encode_priority(self, priority: Priority) -> str:
        return priority.to_str()

    def _decode_status(self, task_elem: ET.Element) -> str:
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

    def _write_comments(self, task_elem: ET.Element, text: str):
        """Write comments in COMMENTS (plain) and CUSTOMCOMMENTS (base64 UTF-16LE)."""
        text = text.replace('\x00', '')
        ce = task_elem.find('COMMENTS')
        if ce is None:
            ce = ET.SubElement(task_elem, 'COMMENTS')
        ce.text = text
        cc = task_elem.find('CUSTOMCOMMENTS')
        if cc is None:
            cc = ET.SubElement(task_elem, 'CUSTOMCOMMENTS')
        cc.text = base64.b64encode(text.encode('utf-16-le')).decode('ascii')
        task_elem.set('COMMENTSTYPE', 'BAA4E079-268B-4B9B-B7C8-6D15CCF058A2')

    def load_all(self) -> tuple[List[Task], int, dict[str, str]]:
        """Loads all tasks from the XML file, returns (tasks, next_id, root_attributes)."""
        if not self.file_path.exists():
            return [], 1, {}

        try:
            with FileLock(str(self.file_path)):
                tree = ET.parse(self.file_path)
            root = tree.getroot()
            
            next_id = int(root.get('NEXTUNIQUEID', '1'))
            root_attrs = {k: v for k, v in root.attrib.items() if k != 'NEXTUNIQUEID'}
            
            tasks = self._parse_tasks_recursive(root)
            return tasks, next_id, root_attrs
        except Exception as e:
            logger.error(f"Failed to load tasks from {self.file_path}: {e}")
            raise

    def _parse_tasks_recursive(self, parent_element: ET.Element) -> List[Task]:
        tasks = []
        for task_elem in parent_element.findall('./TASK'):
            task = Task(
                id=task_elem.get('ID', ''),
                title=task_elem.get('TITLE', ''),
                priority=self._decode_priority(task_elem.get('PRIORITY', '0')),
                status=self._decode_status(task_elem),
                due_date=self._decode_date(task_elem.get('DUEDATE', '')),
                created_date=self._decode_date(task_elem.get('CREATIONDATE', '')),
                percent_done=int(task_elem.get('PERCENTDONE', '0')),
                pos=task_elem.get('POS', ''),
                pos_string=task_elem.get('POSSTRING', ''),
                time_estimate=float(task_elem.get('TIMEESTIMATE', '0')) if task_elem.get('TIMEESTIMATE') else None,
                start_date=self._decode_date(task_elem.get('STARTDATE', '')),
                comments=task_elem.findtext('COMMENTS', default=task_elem.get('COMMENTS', '')),
                description=task_elem.findtext('COMMENTS', default=task_elem.get('COMMENTS', '')),
            )

            # Tags
            task.tags = [t.text.strip() for t in task_elem.findall('TAG') if t.text]
            # Categories
            task.category = [cat.text.strip() for cat in task_elem.findall('CATEGORY') if cat.text]
            # Allocations
            task.allocated_to = [alloc.text.strip() for alloc in task_elem.findall('ALLOCATEDTO') if alloc.text]
            
            # Color and Icon
            if task_elem.get('COLOR'):
                task.color = task_elem.get('COLOR')
            if task_elem.get('ICONINDEX'):
                task.icon = int(task_elem.get('ICONINDEX'))

            # Recurse
            task.children = self._parse_tasks_recursive(task_elem)
            tasks.append(task)
        return tasks

    def save_all(self, tasks: List[Task], next_id: int, root_attrs: dict[str, str]) -> None:
        """Saves the entire task hierarchy to the XML file."""
        try:
            new_tree = ET.Element('TODOLIST', root_attrs)
            new_tree.set('NEXTUNIQUEID', str(next_id))

            for task in tasks:
                self._append_task_to_element(new_tree, task)

            # Create an ElementTree from the root element to use the .write() method
            output_tree = ET.ElementTree(new_tree)

            with FileLock(str(self.file_path)):
                temp_path = self.file_path.with_suffix(self.file_path.suffix + '.tmp')
                output_tree.write(str(temp_path), encoding='utf-8', xml_declaration=True)
                os.replace(temp_path, self.file_path)
                logger.info(f"Successfully saved all tasks to {self.file_path}")

        except Exception as e:
            logger.error(f"Failed to save tasks to {self.file_path}: {e}")
            raise

    def _append_task_to_element(self, parent_element: ET.Element, task: Task):
        task_elem = ET.SubElement(parent_element, 'TASK')
        task_elem.set('ID', task.id)
        task_elem.set('TITLE', task.title)
        task_elem.set('PRIORITY', self._encode_priority(task.priority))
        task_elem.set('STATUS', task.status)
        
        if task.due_date:
            task_elem.set('DUEDATE', self._encode_date(task.due_date))
            task_elem.set('DUEDATESTRING', task.due_date.strftime('%d/%m/%Y'))
        if task.created_date:
            task_elem.set('CREATIONDATE', self._encode_date(task.created_date))
        if task.start_date:
            task_elem.set('STARTDATE', self._encode_date(task.start_date))
            task_elem.set('STARTDATESTRING', task.start_date.strftime('%d/%m/%Y'))
            
        task_elem.set('PERCENTDONE', str(task.percent_done))
        task_elem.set('POS', task.pos)
        task_elem.set('POSSTRING', task.pos_string)
        
        if task.time_estimate:
            task_elem.set('TIMEESTIMATE', str(task.time_estimate))
        if task.color:
            task_elem.set('COLOR', str(task.color))
        if task.icon is not None:
            task_elem.set('ICONINDEX', str(task.icon))

        # Comments
        if task.description:
            self._write_comments(task_elem, task.description)

        # Tags
        for tag in task.tags:
            t = ET.SubElement(task_elem, 'TAG')
            t.text = tag
        
        # Categories
        for cat in task.category:
            c = ET.SubElement(task_elem, 'CATEGORY')
            c.text = cat
            
        # Allocations
        for alloc in task.allocated_to:
            a = ET.SubElement(task_elem, 'ALLOCATEDTO')
            a.text = alloc

        for child in task.children:
            self._append_task_to_element(task_elem, child)
