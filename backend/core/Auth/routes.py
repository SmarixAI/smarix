import boto3
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

# Database configuration - PostgreSQL only
MEMORY_DB_URL = os.environ.get("MEMORY_DB_URL", "")

if not MEMORY_DB_URL or not MEMORY_DB_URL.startswith("postgresql://"):
    raise RuntimeError("MEMORY_DB_URL must be set to a valid PostgreSQL connection string")

DATABASE_URL = MEMORY_DB_URL
print(f"Using PostgreSQL database from MEMORY_DB_URL")

try:
    from sqlalchemy import text

    test_engine = create_engine(DATABASE_URL)
    with test_engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✓ PostgreSQL connection successful")
except Exception as e:
    print(f"❌ PostgreSQL connection failed: {e}")
    raise

# Create engine and session (no connect_args needed for PostgreSQL)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ========================================
# Schema Management Functions
# ========================================

def get_user_schema_name(username: str) -> str:
    """Generate safe schema name from username"""
    sanitized = re.sub(r"[^a-z0-9_]", "_", username.lower())
    return f"user_{sanitized}"


def create_user_schema_postgres(username: str, schema_name: str):
    """
    Create a new schema for a user in PostgreSQL by cloning templates.
    """
    try:
        conn = psycopg2.connect(MEMORY_DB_URL)
        conn.autocommit = True
        with conn.cursor() as cur:
            # 1. Check if user schema already exists
            schema_exists = False
            cur.execute(
                "SELECT 1 FROM information_schema.schemata WHERE schema_name = %s",
                (schema_name,),
            )
            if cur.fetchone():
                schema_exists = True

                # Check tables and sequences...
                cur.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = %s
                      AND table_name IN ('conversations', 'messages', 'tasks')
                    """,
                    (schema_name,),
                )
                existing_tables = {row[0] for row in cur.fetchall()}
                required_tables = {"conversations", "messages", "tasks"}

                if existing_tables == required_tables:
                    # Check sequence
                    cur.execute(
                        """
                        SELECT column_default
                        FROM information_schema.columns
                        WHERE table_schema = %s
                          AND table_name = 'messages'
                          AND column_name = 'id'
                        """,
                        (schema_name,),
                    )
                    default_val = cur.fetchone()

                    if (
                            default_val
                            and default_val[0]
                            and "nextval" in str(default_val[0])
                    ):
                        return
                    else:
                        print(f"⚠ Fixing sequence for {schema_name}.messages")
                        _fix_messages_sequence(cur, schema_name)
                        return

            # 2. Ensure template_schema exists
            cur.execute(
                "SELECT 1 FROM information_schema.schemata WHERE schema_name = 'template_schema'"
            )
            if not cur.fetchone():
                cur.execute("CREATE SCHEMA IF NOT EXISTS template_schema")
                # Create template tables (Conversations, Messages, Tasks)
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS template_schema.conversations
                    (
                        id
                        UUID
                        PRIMARY
                        KEY
                        DEFAULT
                        gen_random_uuid
                    (
                    ),
                        session_id VARCHAR
                    (
                        255
                    ) UNIQUE NOT NULL,
                        user_id VARCHAR
                    (
                        255
                    ),
                        created_at TIMESTAMP DEFAULT NOW
                    (
                    ),
                        updated_at TIMESTAMP DEFAULT NOW
                    (
                    ),
                        title TEXT,
                        metadata JSONB DEFAULT '{}'::jsonb
                        )
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS template_schema.messages
                    (
                        id
                        BIGSERIAL
                        PRIMARY
                        KEY,
                        conversation_id
                        UUID
                        NOT
                        NULL,
                        role
                        VARCHAR
                    (
                        20
                    ) NOT NULL CHECK
                    (
                        role
                        IN
                    (
                        'user',
                        'assistant',
                        'system'
                    )),
                        content TEXT NOT NULL,
                        tokens_used INTEGER DEFAULT 0,
                        response_time_ms INTEGER,
                        created_at TIMESTAMP DEFAULT NOW
                    (
                    ),
                        metadata JSONB DEFAULT '{}'::jsonb,
                        CONSTRAINT fk_conversation
                        FOREIGN KEY
                    (
                        conversation_id
                    )
                        REFERENCES template_schema.conversations
                    (
                        id
                    )
                        ON DELETE CASCADE
                        )
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS template_schema.tasks
                    (
                        id
                        UUID
                        PRIMARY
                        KEY
                        DEFAULT
                        gen_random_uuid
                    (
                    ),
                        title TEXT NOT NULL,
                        description TEXT,
                        category VARCHAR
                    (
                        50
                    ) DEFAULT 'day-to-day',
                        priority VARCHAR
                    (
                        20
                    ) DEFAULT 'medium',
                        status VARCHAR
                    (
                        20
                    ) DEFAULT 'pending',
                        deadline DATE,
                        assigned_to_username VARCHAR
                    (
                        50
                    ),
                        assigned_by VARCHAR
                    (
                        50
                    ) DEFAULT 'Self',
                        created_at TIMESTAMP DEFAULT NOW
                    (
                    )
                        )
                    """
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON template_schema.messages(conversation_id)"
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_messages_created_at ON template_schema.messages(created_at)"
                )
                print("✓ Created template_schema with template tables")

            # 3. Use clone function if available
            cur.execute(
                """
                SELECT EXISTS (SELECT 1
                               FROM pg_proc p
                                        JOIN pg_namespace n ON p.pronamespace = n.oid
                               WHERE n.nspname = 'public'
                                 AND p.proname = 'clone_schema_for_user')
                """
            )
            if cur.fetchone()[0]:
                cur.execute(
                    "SELECT clone_schema_for_user('template_schema', %s)",
                    (schema_name,),
                )
                print(
                    f"✓ Created schema {schema_name} for {username} via clone function"
                )
                return

            # 4. Fallback manual creation
            print(f"⚠ clone_schema_for_user function not found, using manual creation")
            if not schema_exists:
                cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")

            # Manual table cloning logic...
            existing_tables_set = existing_tables if schema_exists else set()

            if "conversations" not in existing_tables_set:
                cur.execute(
                    f"CREATE TABLE IF NOT EXISTS {schema_name}.conversations (LIKE template_schema.conversations INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING INDEXES)"
                )

            if "messages" not in existing_tables_set:
                cur.execute(
                    f"CREATE TABLE IF NOT EXISTS {schema_name}.messages (LIKE template_schema.messages INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING INDEXES)"
                )
                _fix_messages_sequence(cur, schema_name)

            if "tasks" not in existing_tables_set:
                cur.execute(
                    f"CREATE TABLE IF NOT EXISTS {schema_name}.tasks (LIKE template_schema.tasks INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING INDEXES)"
                )

            try:
                cur.execute(
                    f"ALTER TABLE {schema_name}.messages DROP CONSTRAINT IF EXISTS fk_conversation"
                )
                cur.execute(
                    f"ALTER TABLE {schema_name}.messages ADD CONSTRAINT fk_conversation FOREIGN KEY (conversation_id) REFERENCES {schema_name}.conversations(id) ON DELETE CASCADE"
                )
            except Exception:
                pass

            print(f"✓ Created schema {schema_name} for {username}")
        conn.close()
    except Exception as e:
        print(f"⚠ Error creating schema {schema_name}: {e}")
        import traceback
        traceback.print_exc()


def _fix_messages_sequence(cur, schema_name: str):
    """Helper function to fix sequences"""
    try:
        cur.execute(f"CREATE SEQUENCE IF NOT EXISTS {schema_name}.messages_id_seq")
        cur.execute(
            f"ALTER TABLE {schema_name}.messages ALTER COLUMN id SET DEFAULT nextval('{schema_name}.messages_id_seq'::regclass)"
        )
        cur.execute(
            f"ALTER SEQUENCE {schema_name}.messages_id_seq OWNED BY {schema_name}.messages.id"
        )
        cur.execute(
            f"SELECT setval('{schema_name}.messages_id_seq', COALESCE((SELECT MAX(id) FROM {schema_name}.messages), 0) + 1, false)"
        )
    except Exception as e:
        print(f"⚠ Error fixing sequence for {schema_name}: {e}")


router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Create tables if they don't exist
try:
    models.Base.metadata.create_all(bind=engine)
    print("✓ Database tables created/verified")
except Exception as e:
    print(f"⚠ Warning: Could not create database tables: {e}")
    import traceback

    traceback.print_exc()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/signup", response_model=schemas.UserResponse)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. Check if user exists
    db_user = (
        db.query(models.User).filter(models.User.username == user.username).first()
    )
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_pwd = utils.get_password_hash(user.password)

    # 2. Determine Schema Name
    schema_name = get_user_schema_name(user.username)

    # 3. Create User in DB
    new_user = models.User(
        username=user.username,
        password_hash=hashed_pwd,
        role=user.role,
        status=user.status,
        name=user.name,
        designation=user.designation,
        employee_id=user.employee_id,
        managers=user.managers,
        last_day=user.last_day,
        schema_name=schema_name,  # Always use schema_name since we're PostgreSQL only
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # 4. Create User Schema
        create_user_schema_postgres(user.username, schema_name)

        return new_user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/token", response_model=schemas.Token)
def login(
        form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = (
        db.query(models.User).filter(models.User.username == form_data.username).first()
    )

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
            "name": user.name,
            "activeRepos": user.active_repos or []
        }
    )

    return {"access_token": access_token, "token_type": "bearer"}


def get_current_user(
        token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = utils.jwt.decode(
            token, utils.SECRET_KEY, algorithms=[utils.ALGORITHM]
        )
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
        db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    users = db.query(models.User).all()
    return users


@router.put("/users/{username}", response_model=schemas.UserResponse)
def update_user(
        username: str,
        user_update: schemas.UserUpdate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    if current_user.role not in ['admin', 'manager']:
        raise HTTPException(status_code=403, detail="Not authorized to update users")

    db_user = db.query(models.User).filter(models.User.username == username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_update.name is not None: db_user.name = user_update.name
    if user_update.role is not None: db_user.role = user_update.role
    if user_update.status is not None: db_user.status = user_update.status
    if user_update.designation is not None: db_user.designation = user_update.designation
    if user_update.employee_id is not None: db_user.employee_id = user_update.employee_id
    if user_update.last_day is not None: db_user.last_day = user_update.last_day

    if user_update.active_repos is not None:
        db_user.active_repos = user_update.active_repos
    elif user_update.active_repo is not None:
        db_user.active_repos = [user_update.active_repo] if user_update.active_repo else []

    if user_update.managers is not None:
        db_user.managers = user_update.managers

    try:
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repositories")
def get_s3_repositories(current_user: models.User = Depends(get_current_user)):
    """
    Scans S3 bucket 'smarix-data-apsouth1' under 'DataCollectionFromGit/'
    to find available Orgs and Repos.
    Returns: ["org/repo1", "org/repo2", ...]
    """
    if current_user.role not in ['admin', 'manager']:
        raise HTTPException(status_code=403, detail="Not authorized")

    s3 = boto3.client("s3", region_name="ap-south-1")
    bucket_name = "smarix-data-apsouth1"
    base_prefix = "DataCollectionFromGit/"

    repos = []

    try:
        org_response = s3.list_objects_v2(
            Bucket=bucket_name,
            Prefix=base_prefix,
            Delimiter='/'
        )

        org_prefixes = [p.get('Prefix') for p in org_response.get('CommonPrefixes', [])]

        for org_path in org_prefixes:
            org_name = org_path.replace(base_prefix, "").strip("/")

            repo_response = s3.list_objects_v2(
                Bucket=bucket_name,
                Prefix=org_path,
                Delimiter='/'
            )

            repo_prefixes = [r.get('Prefix') for r in repo_response.get('CommonPrefixes', [])]

            for repo_path in repo_prefixes:
                repo_name = repo_path.replace(org_path, "").strip("/")

                repos.append(f"{org_name}/{repo_name}")

        return {"repositories": repos}

    except Exception as e:
        print(f"Error scanning S3: {e}")
        return {"repositories": [], "error": str(e)}


class StatusUpdate(BaseModel):
    status: str


@router.put("/users/{username}/status")
def update_user_status(
        username: str,
        status_update: StatusUpdate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user),
):
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    user_to_update = (
        db.query(models.User).filter(models.User.username == username).first()
    )
    if not user_to_update:
        raise HTTPException(status_code=404, detail="User not found")

    user_to_update.status = status_update.status
    db.commit()
    return {"message": "Status updated successfully"}


@router.get("/tasks", response_model=List[schemas.TaskResponse])
def get_my_tasks(
        db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    return (
        db.query(models.Task)
        .filter(models.Task.assigned_to_username == current_user.username)
        .all()
    )


@router.post("/tasks", response_model=schemas.TaskResponse)
def create_task(
        task: schemas.TaskCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user),
):
    target_user = (
        task.assigned_to_username
        if task.assigned_to_username
        else current_user.username
    )
    assigned_by = (
        "Self"
        if target_user == current_user.username
        else current_user.name or current_user.username
    )

    new_task = models.Task(
        title=task.title,
        description=task.description,
        category=task.category,
        priority=task.priority,
        deadline=task.deadline,
        status=task.status,
        assigned_to_username=target_user,
        assigned_by=assigned_by,
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
        current_user: models.User = Depends(get_current_user),
):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if (
            task.assigned_to_username != current_user.username
            and task.assigned_by != current_user.username
    ):
        if current_user.role != "admin":
            raise HTTPException(
                status_code=403, detail="Not authorized to update this task"
            )

    if task_update.title:
        task.title = task_update.title
    if task_update.description:
        task.description = task_update.description
    if task_update.priority:
        task.priority = task_update.priority
    if task_update.status:
        task.status = task_update.status
    if task_update.deadline:
        task.deadline = task_update.deadline

    db.commit()
    db.refresh(task)
    return task
