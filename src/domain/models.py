from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import List, Optional

class Priority(Enum):
    LOW = "-2"
    BELOW_NORMAL = "-1"
    NORMAL = "0"
    ABOVE_NORMAL = "1"
    HIGH = "2"
    URGENT = "3"

    @classmethod
    def from_str(cls, value: str) -> "Priority":
        try:
            return cls(value)
        except ValueError:
            # Fallback logic for non-standard values
            if value == "Low": return cls.LOW
            if value == "Below Normal": return cls.BELOW_NORMAL
            if value == "Normal": return cls.NORMAL
            if value == "Above Normal": return cls.ABOVE_NORMAL
            if value == "High": return cls.HIGH
            if value == "Urgent": return cls.URGENT
            return cls.NORMAL

    def to_str(self) -> str:
        return self.value

@dataclass
class Task:
    id: str
    title: str
    priority: Priority = Priority.NORMAL
    status: str = "Not Started"
    due_date: Optional[date] = None
    created_date: Optional[date] = None
    percent_done: int = 0
    comments: str = ""
    description: str = ""
    pos: str = ""
    pos_string: str = ""
    time_estimate: Optional[float] = None
    start_date: Optional[date] = None
    tags: List[str] = field(default_factory=list)
    category: List[str] = field(default_factory=list)
    allocated_to: List[str] = field(default_factory=list)
    icon: Optional[int] = None
    color: Optional[str] = None
    children: List["Task"] = field(default_factory=list)

    @property
    def completed(self) -> bool:
        return self.percent_done >= 100

    def to_dict(self) -> dict:
        """Return a dictionary representation for serialization/UI."""
        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority.name,
            "status": self.status,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_date": self.created_date.isoformat() if self.created_date else None,
            "percent_done": self.percent_done,
            "comments": self.comments,
            "description": self.description,
            "pos": self.pos,
            "pos_string": self.pos_string,
            "time_estimate": self.time_estimate,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "tags": ", ".join(self.tags),
            "category": ", ".join(self.category),
            "allocated_to": ", ".join(self.allocated_to),
            "icon": self.icon,
            "color": self.color,
            "completed": self.completed,
            "children": [child.to_dict() for child in self.children]
        }
