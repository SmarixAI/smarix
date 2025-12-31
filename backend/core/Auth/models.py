from sqlalchemy import Column, String, Boolean, DateTime, ARRAY, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="employee")
    status = Column(String, default="general")
    name = Column(String, nullable=True)
    designation = Column(String, nullable=True)
    employee_id = Column(String, unique=True, index=True, nullable=True)
    last_day = Column(Date, nullable=True)
    managers = Column(ARRAY(String), default=[])
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, default="day-to-day") 
    priority = Column(String, default="medium") 
    status = Column(String, default="pending") 
    deadline = Column(Date, nullable=True)
    
    assigned_to_username = Column(String, ForeignKey("users.username"))
    assigned_by = Column(String, default="Self")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())