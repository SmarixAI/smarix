from sqlalchemy import Column, String, Boolean, DateTime, Date, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import uuid
import os

Base = declarative_base()

# Determine if we're using SQLite or PostgreSQL
# Default to SQLite for safety - only use PostgreSQL if explicitly set and verified
FORCE_SQLITE = os.environ.get("FORCE_SQLITE", "").lower() in ("1", "true", "yes")
DATABASE_URL = os.environ.get("MEMORY_DB_URL", "")

# Default to SQLite unless PostgreSQL is explicitly set AND verified to be available
USE_SQLITE = True  # Default to SQLite

# Only use PostgreSQL if:
# 1. Not forcing SQLite
# 2. PostgreSQL URL is explicitly set
# 3. PostgreSQL connection is actually available
if not FORCE_SQLITE and DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    try:
        from sqlalchemy import create_engine, text
        test_engine = create_engine(DATABASE_URL)
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        # PostgreSQL is available, use it
        USE_SQLITE = False
    except Exception:
        # PostgreSQL not available, use SQLite
        USE_SQLITE = True

if USE_SQLITE:
    # SQLite-compatible types
    from sqlalchemy import Text
    UUIDType = String(36)  # Use String(36) for UUIDs in SQLite (UUID string length)
    ArrayType = JSON  # Use JSON for arrays in SQLite
    def uuid_default():
        return str(uuid.uuid4())
else:
    # PostgreSQL-specific types
    from sqlalchemy.dialects.postgresql import UUID, ARRAY
    UUIDType = UUID(as_uuid=True)
    ArrayType = ARRAY(String)
    def uuid_default():
        return uuid.uuid4()

class User(Base):
    __tablename__ = "users"
    id = Column(UUIDType, primary_key=True, default=uuid_default)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="employee")
    status = Column(String, default="general")
    name = Column(String, nullable=True)
    designation = Column(String, nullable=True)
    employee_id = Column(String, unique=True, index=True, nullable=True)
    last_day = Column(Date, nullable=True)
    managers = Column(ArrayType, default=[])
    schema_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUIDType, primary_key=True, default=uuid_default)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, default="day-to-day") 
    priority = Column(String, default="medium") 
    status = Column(String, default="pending") 
    deadline = Column(Date, nullable=True)
    
    assigned_to_username = Column(String, ForeignKey("users.username"))
    assigned_by = Column(String, default="Self")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())