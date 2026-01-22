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
    last_day: Optional[date] = None

class UserCreate(UserBase):
    password: str

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