from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import List
from pydantic import BaseModel
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import re

from . import models, schemas, utils

# Database configuration - use SQLite for local development, PostgreSQL for production
# Set FORCE_SQLITE=1 to force SQLite even if MEMORY_DB_URL is set
FORCE_SQLITE = os.environ.get("FORCE_SQLITE", "").lower() in ("1", "true", "yes")
MEMORY_DB_URL = os.environ.get("MEMORY_DB_URL", "")

# Determine which database to use
use_postgres = not FORCE_SQLITE and MEMORY_DB_URL and MEMORY_DB_URL.startswith("postgresql://")

if use_postgres:
    # Try PostgreSQL first
    DATABASE_URL = MEMORY_DB_URL
    connect_args = {}
    print(f"Attempting to use PostgreSQL database from MEMORY_DB_URL")
    
    # Test PostgreSQL connection, fallback to SQLite if it fails
    try:
        from sqlalchemy import text
        test_engine = create_engine(DATABASE_URL, connect_args=connect_args)
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✓ PostgreSQL connection successful")
    except Exception as e:
        print(f"⚠ PostgreSQL connection failed: {e}")
        print("   Falling back to SQLite...")
        use_postgres = False

if not use_postgres:
    # Use SQLite for local development (no PostgreSQL required)
    db_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "local_db.sqlite")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    DATABASE_URL = f"sqlite:///{db_path}"
    print(f"✓ Using SQLite database: {db_path}")

# SQLite-specific configuration
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}  # Required for SQLite with FastAPI
    # Ensure models use SQLite-compatible types
    os.environ["FORCE_SQLITE"] = "1"
    # Reload models to pick up SQLite types
    import importlib
    importlib.reload(models)

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ========================================
# NEW: Schema Management Functions
# ========================================

def get_user_schema_name(username: str) -> str:
    """Generate safe schema name from username"""
    # logic must match what is used in chat api
    sanitized = re.sub(r"[^a-z0-9_]", "_", username.lower())
    return f"user_{sanitized}"


def create_user_schema_postgres(username: str, schema_name: str):
    """
    Create a new schema for a user in PostgreSQL by cloning templates.
    Properly handles BIGSERIAL sequences for messages.id
    """
    if not use_postgres: 
        return

    try:
        conn = psycopg2.connect(MEMORY_DB_URL)
        conn.autocommit = True
        with conn.cursor() as cur:
            # 1. Check if user schema already exists
            schema_exists = False
            cur.execute("SELECT 1 FROM information_schema.schemata WHERE schema_name = %s", (schema_name,))
            if cur.fetchone():
                schema_exists = True
                # Check if tables exist in the schema
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = %s AND table_name IN ('conversations', 'messages', 'tasks')
                """, (schema_name,))
                existing_tables = {row[0] for row in cur.fetchall()}
                required_tables = {'conversations', 'messages', 'tasks'}

                # If all tables exist, verify sequence for messages
                if existing_tables == required_tables:
                    # Check if messages.id has proper sequence
                    cur.execute("""
                        SELECT column_default 
                        FROM information_schema.columns 
                        WHERE table_schema = %s 
                        AND table_name = 'messages' 
                        AND column_name = 'id'
                    """, (schema_name,))
                    default_val = cur.fetchone()

                    if default_val and default_val[0] and 'nextval' in str(default_val[0]):
                        # Everything is good
                        return
                    else:
                        # Need to fix the sequence
                        print(f"⚠ Fixing sequence for {schema_name}.messages")
                        _fix_messages_sequence(cur, schema_name)
                        return

            # 2. Ensure template_schema exists
            cur.execute("SELECT 1 FROM information_schema.schemata WHERE schema_name = 'template_schema'")
            if not cur.fetchone():
                # Create template_schema and its tables
                cur.execute("CREATE SCHEMA IF NOT EXISTS template_schema")

                # Create template conversations table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS template_schema.conversations (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        session_id VARCHAR(255) UNIQUE NOT NULL,
                        user_id VARCHAR(255),
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW(),
                        title TEXT,
                        metadata JSONB DEFAULT '{}'::jsonb
                    )
                """)

                # Create template messages table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS template_schema.messages (
                        id BIGSERIAL PRIMARY KEY,
                        conversation_id UUID NOT NULL,
                        role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                        content TEXT NOT NULL,
                        tokens_used INTEGER DEFAULT 0,
                        response_time_ms INTEGER,
                        created_at TIMESTAMP DEFAULT NOW(),
                        metadata JSONB DEFAULT '{}'::jsonb,
                        CONSTRAINT fk_conversation 
                            FOREIGN KEY (conversation_id) 
                            REFERENCES template_schema.conversations(id) 
                            ON DELETE CASCADE
                    )
                """)

                # Create template tasks table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS template_schema.tasks (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        title TEXT NOT NULL,
                        description TEXT,
                        category VARCHAR(50) DEFAULT 'day-to-day',
                        priority VARCHAR(20) DEFAULT 'medium',
                        status VARCHAR(20) DEFAULT 'pending',
                        deadline DATE,
                        assigned_to_username VARCHAR(50),
                        assigned_by VARCHAR(50) DEFAULT 'Self',
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)

                # Add indexes to template
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
                    ON template_schema.messages(conversation_id)
                """)

                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_messages_created_at 
                    ON template_schema.messages(created_at)
                """)

                print("✓ Created template_schema with template tables")

            # 3. Check if clone_schema_for_user function exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM pg_proc p
                    JOIN pg_namespace n ON p.pronamespace = n.oid
                    WHERE n.nspname = 'public' 
                    AND p.proname = 'clone_schema_for_user'
                )
            """)

            has_clone_function = cur.fetchone()[0]

            if has_clone_function:
                # Use the PostgreSQL function for proper cloning
                print(f"✓ Using clone_schema_for_user function for {schema_name}")
                cur.execute("SELECT clone_schema_for_user('template_schema', %s)", (schema_name,))
                print(f"✓ Created schema {schema_name} for {username}")
                return

            # 4. Fallback: Manual schema creation (if function doesn't exist)
            print(f"⚠ clone_schema_for_user function not found, using manual creation")

            # Create user schema (if it doesn't exist)
            if not schema_exists:
                cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")

            # Clone conversations table
            if 'conversations' not in existing_tables if schema_exists else True:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {schema_name}.conversations 
                    (LIKE template_schema.conversations INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING INDEXES)
                """)

            # Clone messages table structure
            if 'messages' not in existing_tables if schema_exists else True:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {schema_name}.messages 
                    (LIKE template_schema.messages INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING INDEXES)
                """)

                # Fix the sequence for messages.id
                _fix_messages_sequence(cur, schema_name)

            # Clone tasks table
            if 'tasks' not in existing_tables if schema_exists else True:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {schema_name}.tasks 
                    (LIKE template_schema.tasks INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING INDEXES)
                """)

            # Add foreign key constraint
            try:
                cur.execute(f"""
                    ALTER TABLE {schema_name}.messages
                    DROP CONSTRAINT IF EXISTS fk_conversation
                """)
                cur.execute(f"""
                    ALTER TABLE {schema_name}.messages
                    ADD CONSTRAINT fk_conversation 
                    FOREIGN KEY (conversation_id) 
                    REFERENCES {schema_name}.conversations(id) 
                    ON DELETE CASCADE
                """)
            except Exception as fk_error:
                print(f"⚠ Foreign key creation warning: {fk_error}")

            # Create indexes
            try:
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
                    ON {schema_name}.messages(conversation_id)
                """)
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_messages_created_at 
                    ON {schema_name}.messages(created_at)
                """)
            except Exception:
                pass

            print(f"✓ Created schema {schema_name} for {username}")

        conn.close()

    except Exception as e:
        print(f"⚠ Error creating schema {schema_name}: {e}")
        import traceback
        traceback.print_exc()


def _fix_messages_sequence(cur, schema_name: str):
    """
    Helper function to create and configure sequence for messages.id column.
    This fixes the BIGSERIAL sequence issue.
    """
    try:
        # Create sequence
        cur.execute(f"CREATE SEQUENCE IF NOT EXISTS {schema_name}.messages_id_seq")

        # Set the sequence as default for messages.id
        cur.execute(f"""
            ALTER TABLE {schema_name}.messages 
            ALTER COLUMN id SET DEFAULT nextval('{schema_name}.messages_id_seq'::regclass)
        """)

        # Set sequence ownership
        cur.execute(f"""
            ALTER SEQUENCE {schema_name}.messages_id_seq 
            OWNED BY {schema_name}.messages.id
        """)

        # Set sequence value to max(id) + 1
        cur.execute(f"""
            SELECT setval('{schema_name}.messages_id_seq', 
                COALESCE((SELECT MAX(id) FROM {schema_name}.messages), 0) + 1, 
                false)
        """)

        print(f"✓ Fixed messages sequence for {schema_name}")

    except Exception as e:
        print(f"⚠ Error fixing sequence for {schema_name}: {e}")


router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def sync_users_from_json(db: Session):
    """Sync users from users.json file to database"""
    try:
        import json
        from datetime import datetime
        from pathlib import Path
        
        # Find users.json file
        # routes.py is at backend/core/Auth/routes.py
        # So we need: backend/data/Admin/users.json
        backend_dir = Path(__file__).resolve().parent.parent.parent
        users_file = backend_dir / "data" / "Admin" / "users.json"
        
        if not users_file.exists():
            print(f"⚠ users.json not found at {users_file}")
            return
        
        with open(users_file, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
        
        users_list = users_data.get('users', [])
        if not users_list:
            print("⚠ No users found in users.json")
            return
        
        synced_count = 0
        skipped_count = 0
        
        for user_data in users_list:
            username = user_data.get('username')
            if not username:
                continue
            
            # Check if user already exists
            existing_user = db.query(models.User).filter(models.User.username == username).first()
            
            # Parse lastDay if it exists
            last_day = None
            if user_data.get('lastDay'):
                try:
                    from datetime import datetime
                    last_day = datetime.strptime(user_data['lastDay'], '%Y-%m-%d').date()
                except:
                    pass

            schema_name = get_user_schema_name(username)
            
            if existing_user:
                # Update existing user with data from JSON file
                existing_user.role = user_data.get('role', existing_user.role)
                existing_user.status = user_data.get('status', existing_user.status)
                existing_user.name = user_data.get('name', existing_user.name)
                existing_user.designation = user_data.get('designation', existing_user.designation)
                existing_user.employee_id = user_data.get('employeeId') or user_data.get('employee_id') or existing_user.employee_id
                existing_user.last_day = last_day if last_day else existing_user.last_day
                existing_user.managers = user_data.get('managers', []) if isinstance(user_data.get('managers'), list) else []
                
                if use_postgres:
                    if not existing_user.schema_name:
                        existing_user.schema_name = schema_name
                    create_user_schema_postgres(username, schema_name)

                skipped_count += 1
            else:
                # Create new user
                hashed_pwd = utils.get_password_hash(user_data.get('password', username))
                
                new_user = models.User(
                    username=username,
                    password_hash=hashed_pwd,
                    role=user_data.get('role', 'employee'),
                    status=user_data.get('status', 'general'),
                    name=user_data.get('name'),
                    designation=user_data.get('designation'),
                    employee_id=user_data.get('employeeId') or user_data.get('employee_id'),
                    last_day=last_day,
                    managers=user_data.get('managers', []) if isinstance(user_data.get('managers'), list) else [],
                    schema_name=(schema_name if use_postgres else None)
                )
                
                db.add(new_user)
                synced_count += 1
        
        db.commit()
        print(f"✓ Synced {synced_count} user(s) from users.json to database")
        if skipped_count > 0:
            print(f"  (Skipped {skipped_count} existing user(s))")
    except Exception as e:
        db.rollback()
        print(f"⚠ Warning: Could not sync users from users.json: {e}")
        import traceback
        traceback.print_exc()

# Create tables if they don't exist (for SQLite, this creates the file)
try:
    models.Base.metadata.create_all(bind=engine)
    print("✓ Database tables created/verified")
    
    # Sync users from users.json to database (always sync to keep data in sync)
    db = SessionLocal()
    try:
        user_count = db.query(models.User).count()
        if user_count == 0:
            print("📥 Database is empty, syncing users from users.json...")
        else:
            print(f"✓ Database has {user_count} user(s), syncing/updating from users.json...")
        sync_users_from_json(db)
    finally:
        db.close()
except Exception as e:
    print(f"⚠ Warning: Could not create database tables: {e}")
    import traceback
    traceback.print_exc()
    # If table creation fails, try to continue anyway (tables might already exist)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_postgres_connection(schema_name: str = None):
    """
    Get a raw connection for schema operations.
    Needed because ORM is hard to switch schemas dynamically per request.
    """
    if not use_postgres:
         raise HTTPException(status_code=501, detail="Schema operations require PostgreSQL")
    
    conn = psycopg2.connect(MEMORY_DB_URL)
    if schema_name:
        with conn.cursor() as cur:
            cur.execute(f"SET search_path TO {schema_name}, public")
        conn.commit()
    return conn

@router.post("/signup", response_model=schemas.UserResponse)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_pwd = utils.get_password_hash(user.password)
    
    new_user = models.User(
        username=user.username,
        password_hash=hashed_pwd,
        role=user.role,
        status=user.status,
        name=user.name,
        designation=user.designation,
        employee_id=user.employee_id,
        managers=user.managers,
        last_day=user.last_day
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    
    if not user or not utils.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = utils.create_access_token(
        data={
            "sub": user.username, 
            "role": user.role,
            "status": user.status,          
            "employeeId": user.employee_id,
            "name": user.name
        }
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = utils.jwt.decode(token, utils.SECRET_KEY, algorithms=[utils.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except utils.jwt.JWTError:
        raise credentials_exception
        
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

@router.get("/users", response_model=List[schemas.UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    users = db.query(models.User).all()
    return users

class StatusUpdate(BaseModel):
    status: str

@router.put("/users/{username}/status")
def update_user_status(
    username: str, 
    status_update: StatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role not in ['admin', 'manager']:
        raise HTTPException(status_code=403, detail="Not authorized")

    user_to_update = db.query(models.User).filter(models.User.username == username).first()
    if not user_to_update:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_to_update.status = status_update.status
    db.commit()
    return {"message": "Status updated successfully"}

@router.get("/tasks", response_model=List[schemas.TaskResponse])
def get_my_tasks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Fetch all tasks assigned TO the logged-in user.
    """
    return db.query(models.Task).filter(models.Task.assigned_to_username == current_user.username).all()


@router.post("/tasks", response_model=schemas.TaskResponse)
def create_task(
    task: schemas.TaskCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """
    Create a new task.
    If 'assigned_to_username' is missing, it assigns to Self.
    If 'assigned_to_username' is someone else, 'assigned_by' becomes the current user.
    """
    target_user = task.assigned_to_username if task.assigned_to_username else current_user.username
    assigned_by = "Self" if target_user == current_user.username else current_user.name or current_user.username

    new_task = models.Task(
        title=task.title,
        description=task.description,
        category=task.category,
        priority=task.priority,
        deadline=task.deadline,
        status=task.status,
        assigned_to_username=target_user,
        assigned_by=assigned_by
    )
    
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


@router.put("/tasks/{task_id}", response_model=schemas.TaskResponse)
def update_task(
    task_id: str, 
    task_update: schemas.TaskUpdate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """
    Update a task (status, priority, deadline, etc.)
    """
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.assigned_to_username != current_user.username and task.assigned_by != current_user.username:
         if current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Not authorized to update this task")

    if task_update.title: task.title = task_update.title
    if task_update.description: task.description = task_update.description
    if task_update.priority: task.priority = task_update.priority
    if task_update.status: task.status = task_update.status
    if task_update.deadline: task.deadline = task_update.deadline

    db.commit()
    db.refresh(task)
    return task