from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict

class Status(Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"  # 已超时

class ProjectStatus(Enum):
    """项目状态"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"  # 已完成
    ARCHIVED = "archived"  # 已归档（失败的项目）

@dataclass
class Project:
    id: str
    name: str
    description: str
    status: str  # 使用字符串，可以是 planned, in_progress, completed, archived
    local_path: str  # 本地文件夹路径
    created_at: str
    updated_at: str
    is_pinned: bool = False
    local_path_map: Dict[str, str] = field(default_factory=dict)

@dataclass
class Task:
    id: str
    project_id: str
    name: str
    description: str
    notes: str
    start_date: str
    end_date: str
    status: Status
    local_path: str  # 本地文件夹路径
    local_path_map: Dict[str, str] = field(default_factory=dict)
    is_important: bool = False  # 是否重要（默认不重要）
    is_urgent: bool = False  # 是否紧急（默认不紧急）
    created_at: str = ""
    updated_at: str = ""