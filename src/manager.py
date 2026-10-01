"""ToDoList Manager - thin wiring for the service layer.

Owns only the .tdl path resolution and the repository/service composition.
All business logic lives in TodoService and XmlTodoRepository.
"""

import os
from pathlib import Path

from src.infrastructure.repository import XmlTodoRepository
from src.services.todo_service import TodoService


def _resolve_tdl_file() -> str:
    """Resolve the .tdl path: TODOLIST_FILE env > mcp_server.ini > fallback."""
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
    return os.path.expanduser("~/todolist.tdl")


DEFAULT_TDL_FILE = _resolve_tdl_file()


class ToDoListManager:
    """Wiring only: composes a repository and a service over one .tdl file."""

    def __init__(self, base_path: str | None = None, default_file: str = DEFAULT_TDL_FILE):
        self.file_path = default_file if default_file else DEFAULT_TDL_FILE
        self.repository = XmlTodoRepository(self.file_path)
        self.service = TodoService(self.repository)


todo_manager = ToDoListManager()
