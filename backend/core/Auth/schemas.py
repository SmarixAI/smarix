from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date, datetime
import uuid


class UserBase(BaseModel):
    username: str
    role: Optional[str] = "employee"
    status: Optional[str] = "general"
    name: Optional[str] = None
    designation: Optional[str] = None
    employee_id: Optional[str] = None
    managers: Optional[List[str]] = []
    # ✅ Added active_repos to Base so it returns in GET requests
    active_repos: Optional[List[str]] = []
    last_day: Optional[date] = None


class UserCreate(UserBase):
    password: str
    # Allow creating with a single repo string (convenience)
    active_repo: Optional[str] = None


class UserUpdate(BaseModel):
    role: Optional[str] = None
    status: Optional[str] = None
    name: Optional[str] = None
    designation: Optional[str] = None
    employee_id: Optional[str] = None
    managers: Optional[List[str]] = None
    last_day: Optional[date] = None

    # ✅ Added active_repo (singular) to match Frontend JSON payload
    active_repo: Optional[str] = None
    # ✅ Added active_repos (plural) for direct list updates
    active_repos: Optional[List[str]] = None


class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: Optional[Dict[str, Any]] = None


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = "day-to-day"
    priority: Optional[str] = "medium"
    deadline: Optional[date] = None
    status: Optional[str] = "pending"


class TaskCreate(TaskBase):
    assigned_to_username: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    deadline: Optional[date] = None


class TaskResponse(TaskBase):
    id: uuid.UUID
    assigned_to_username: Optional[str] = None
    assigned_by: Optional[str] = "Self"
    created_at: datetime

    class Config:
        from_attributes = True
