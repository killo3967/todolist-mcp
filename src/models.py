"""Pydantic argument models for ToDoList MCP tools."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class _TaskIdArgs(BaseModel):
    """Base para modelos que referencian tareas por ID.

    coerce_numbers_to_str permite que task_id se envie como entero (p. ej. 246)
    y se normalice a string automaticamente, evitando errores de validacion.
    """
    model_config = ConfigDict(coerce_numbers_to_str=True)


class GetTasksArgs(BaseModel):
    format: Literal['markdown', 'json'] = Field("markdown", description="Output format")


class GetTodayTasksArgs(BaseModel):
    target_date: str | None = Field(None, description="Target date in YYYY-MM-DD format (defaults to today)")
    format: Literal['markdown', 'json'] = Field("markdown", description="Output format")


class AddTaskArgs(BaseModel):
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
    icon: int | None = Field(None, description="Task icon index (ToDoList ICONINDEX, e.g. 85 for the standard project/folder icon)")


class UpdateTaskArgs(_TaskIdArgs):
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
    start_date: str | None = Field(None, description="Start date in YYYY-MM-DD format (empty string to clear)")
    tags: str | None = Field(None, description="Comma-separated tags (empty string to clear)")
    icon: int | None = Field(None, description="New task icon index (ToDoList ICONINDEX, e.g. 85). Set to 0 to clear.")


class AddCommentArgs(_TaskIdArgs):
    task_id: str = Field(..., description="ID of the task to add a comment to")
    comment: str = Field(..., description="Comment text to append to the task description")


class CompleteTaskArgs(_TaskIdArgs):
    task_id: str = Field(..., description="ID of the task to complete")
    status_text: str = Field("Completed", description="Status text to set (e.g. 'Terminado', 'Completed')")


class GetTaskStatsArgs(BaseModel):
    format: Literal['markdown', 'json'] = Field("markdown", description="Output format")


class SearchTasksArgs(BaseModel):
    search_term: str | None = Field(None, description="Search in task titles and descriptions")
    category: str | None = Field(None, description="Filter by category")
    priority: Literal['Low', 'Below Normal', 'Normal', 'Above Normal', 'High', 'Urgent'] | None = Field(None, description="Filter by priority")
    status: str | None = Field(None, description="Filter by status text (e.g. 'Pendiente', 'En curso', 'Terminado')")
    completed: bool | None = Field(None, description="Filter by completion status")
    assigned_to: str | None = Field(None, description="Filter by person assigned")
    format: Literal['markdown', 'json'] = Field("markdown", description="Output format")


class MoveTaskArgs(_TaskIdArgs):
    task_id: str = Field(..., description="ID of the task to move")
    new_position: str = Field(..., description="New position for the task (e.g., '6.3.4' or parent position '5.3.7')")


class GetTaskArgs(_TaskIdArgs):
    task_id: str = Field(..., description="ID of the task to retrieve")
    format: Literal['markdown', 'json'] = Field("markdown", description="Output format")

class DeleteTaskArgs(_TaskIdArgs):
    task_id: str = Field(..., description="ID of the task to delete")


class ReadAnyTdlArgs(BaseModel):
    file_path: str = Field(..., description="Path to the .tdl file")
    format: Literal['markdown', 'json'] = Field("markdown", description="Output format")
