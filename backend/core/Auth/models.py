from sqlalchemy import Column, String, Boolean, DateTime, Date, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import uuid
import os

Base = declarative_base()

# Determine if we're using SQLite or PostgreSQL
FORCE_SQLITE = os.environ.get("FORCE_SQLITE", "").lower() in ("1", "true", "yes")
DATABASE_URL = os.environ.get("MEMORY_DB_URL", "")

USE_SQLITE = True

if not FORCE_SQLITE and DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    try:
        from sqlalchemy import create_engine, text

        test_engine = create_engine(DATABASE_URL)
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        USE_SQLITE = False
    except Exception:
        USE_SQLITE = True

if USE_SQLITE:
    # SQLite-compatible types
    from sqlalchemy import Text

    UUIDType = String(36)
    ArrayType = JSON

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
    # ✅ Added active_repos to store array of repo strings
    active_repos = Column(ArrayType, default=[])

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
