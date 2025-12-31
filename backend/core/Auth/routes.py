from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import List
from pydantic import BaseModel
import os

from . import models, schemas, utils

# --- FIX START ---
# 1. Changed env var name to MEMORY_DB_URL to match docker-compose
# 2. Updated default fallback to match container name (chatbot_postgres) and DB name (super_employee_memory)
DATABASE_URL = os.environ.get(
    "MEMORY_DB_URL", 
    "postgresql://postgres:postgres@chatbot_postgres:5432/super_employee_memory"
)
# --- FIX END ---

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

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