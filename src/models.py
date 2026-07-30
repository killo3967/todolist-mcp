"""Pydantic argument models for ToDoList MCP tools."""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class GetTasksArgs(BaseModel):
    format: Literal['markdown', 'json'] = Field("markdown", description="Output format")


class GetTodayTasksArgs(BaseModel):
    target_date: Optional[str] = Field(None, description="Target date in YYYY-MM-DD format (defaults to today)")
    format: Literal['markdown', 'json'] = Field("markdown", description="Output format")


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
    start_date: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format")
    tags: Optional[str] = Field(None, description="Comma-separated tags (e.g. 'bug, urgent, frontend')")


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
    start_date: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format (empty string to clear)")
    tags: Optional[str] = Field(None, description="Comma-separated tags (empty string to clear)")


class AddCommentArgs(BaseModel):
    task_id: str = Field(..., description="ID of the task to add a comment to")
    comment: str = Field(..., description="Comment text to append to the task description")


class CompleteTaskArgs(BaseModel):
    task_id: str = Field(..., description="ID of the task to complete")
    status_text: str = Field("Completed", description="Status text to set (e.g. 'Terminado', 'Completed')")


class GetTaskStatsArgs(BaseModel):
    format: Literal['markdown', 'json'] = Field("markdown", description="Output format")


class SearchTasksArgs(BaseModel):
    search_term: Optional[str] = Field(None, description="Search in task titles and descriptions")
    category: Optional[str] = Field(None, description="Filter by category")
    priority: Optional[Literal['Low', 'Below Normal', 'Normal', 'Above Normal', 'High', 'Urgent']] = Field(None, description="Filter by priority")
    status: Optional[str] = Field(None, description="Filter by status text (e.g. 'Pendiente', 'En curso', 'Terminado')")
    completed: Optional[bool] = Field(None, description="Filter by completion status")
    assigned_to: Optional[str] = Field(None, description="Filter by person assigned")
    format: Literal['markdown', 'json'] = Field("markdown", description="Output format")


class MoveTaskArgs(BaseModel):
    task_id: str = Field(..., description="ID of the task to move")
    new_position: str = Field(..., description="New position for the task (e.g., '6.3.4' or parent position '5.3.7')")


class GetTaskArgs(BaseModel):
    task_id: str = Field(..., description="ID of the task to retrieve")
    format: Literal['markdown', 'json'] = Field("markdown", description="Output format")


class ReadAnyTdlArgs(BaseModel):
    file_path: str = Field(..., description="Path to the .tdl file")
    format: Literal['markdown', 'json'] = Field("markdown", description="Output format")
