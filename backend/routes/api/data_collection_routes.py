"""
Data Collection API Routes - FULLY DYNAMIC
No static runtime_state.json needed for repo selection
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime
import asyncio
from dotenv import load_dotenv
import sys, os
from pathlib import Path

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))


from core.DataCollection.DataCollectionFromGithub.github_installation_manager import GitHubInstallationManager
from core.DataCollection.DataCollectionFromGithub.private_repository_processor import AsyncPrivateRepositoryProcessor
from utils.s3 import s3_manager

router = APIRouter(prefix="/api/data-collection", tags=["Data Collection"])

# ============================================
# Request/Response Models
# ============================================

class ProcessRepoRequest(BaseModel):
    """Request to process a GitHub repository"""
    owner: str       # DYNAMIC: Passed in each request
    repo: str        # DYNAMIC: Passed in each request
    user_id: Optional[int] = None
    team_id: Optional[str] = None
    channel_id: Optional[str] = None


class JobResponse(BaseModel):
    """Job creation response"""
    job_id: str
    status: str
    owner: str
    repo: str
    installation_id: int
    created_at: str
    message: str


class JobStatus(BaseModel):
    """Job status response"""
    job_id: str
    status: str  # 'queued', 'processing', 'completed', 'failed'
    owner: str
    repo: str
    installation_id: int
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    output_s3_key: Optional[str] = None
    progress: Optional[dict] = None


# ============================================
# In-Memory Job Store (Replace with Redis in production)
# ============================================

jobs_store = {}  # job_id -> JobStatus dict


# ============================================
# Background Task
# ============================================

async def process_repo_background(
    job_id: str,
    owner: str,
    repo: str,
    installation_id: int,
    team_id: Optional[str] = None,
    channel_id: Optional[str] = None
):
    """
    Background task to process a repository
    """
    try:
        # Update status
        jobs_store[job_id]["status"] = "processing"
        jobs_store[job_id]["started_at"] = datetime.now().isoformat()
        
        print(f"\n🚀 Job {job_id}: Processing {owner}/{repo}")
        print(f"   Installation ID: {installation_id}\n")
        
        # Process repository
        processor = AsyncPrivateRepositoryProcessor()
        
        repo_data = await processor.process_repository(
            owner=owner,
            repo=repo,
            installation_id=installation_id,
            team_id=team_id,
            channel_id=channel_id
        )
        
        # Save to S3
        output_s3_key = processor.save_repository_data(repo_data, owner, repo)
        
        # Update job status
        jobs_store[job_id]["status"] = "completed"
        jobs_store[job_id]["completed_at"] = datetime.now().isoformat()
        jobs_store[job_id]["output_s3_key"] = output_s3_key
        
        print(f"✅ Job {job_id} completed: {output_s3_key}\n")
    
    except Exception as e:
        print(f"❌ Job {job_id} failed: {e}\n")
        
        jobs_store[job_id]["status"] = "failed"
        jobs_store[job_id]["completed_at"] = datetime.now().isoformat()
        jobs_store[job_id]["error"] = str(e)


# ============================================
# API Endpoints
# ============================================

@router.post("/process-repo", response_model=JobResponse)
async def process_repository(
    request: ProcessRepoRequest,
    background_tasks: BackgroundTasks
):
    """
    Process any GitHub repository dynamically
    
    Args:
        request: Contains owner, repo (both DYNAMIC per request)
    
    Flow:
        1. Resolve installation_id from S3 (based on owner)
        2. Create background job
        3. Return job_id immediately
        4. Process in background
    
    Example:
        POST /api/data-collection/process-repo
        {
            "owner": "oops-shlok",
            "repo": "my-private-repo"
        }
    """
    owner = request.owner
    repo = request.repo
    
    print(f"\n📥 New request: {owner}/{repo}")
    
    # Step 1: Resolve installation_id dynamically from S3
    manager = GitHubInstallationManager()
    
    try:
        installation_id = await manager.get_installation_id(owner, repo)
        print(f"   ✅ Found installation_id: {installation_id}")
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resolve installation: {str(e)}"
        )
    
    # Step 2: Create job
    job_id = str(uuid.uuid4())
    
    job_data = {
        "job_id": job_id,
        "status": "queued",
        "owner": owner,
        "repo": repo,
        "installation_id": installation_id,
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None,
        "error": None,
        "output_s3_key": None
    }
    
    jobs_store[job_id] = job_data
    
    # Step 3: Start background processing
    background_tasks.add_task(
        process_repo_background,
        job_id=job_id,
        owner=owner,
        repo=repo,
        installation_id=installation_id,
        team_id=request.team_id,
        channel_id=request.channel_id
    )
    
    return JobResponse(
        job_id=job_id,
        status="queued",
        owner=owner,
        repo=repo,
        installation_id=installation_id,
        created_at=job_data["created_at"],
        message=f"Job created. Processing {owner}/{repo} in background."
    )


@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """
    Get status of a data collection job
    
    Args:
        job_id: Job ID from /process-repo response
    
    Returns:
        Current job status
    """
    if job_id not in jobs_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatus(**jobs_store[job_id])


@router.get("/installations")
async def list_installations():
    """
    List all GitHub App installations from S3
    
    Returns:
        All installations with their repositories
    """
    manager = GitHubInstallationManager()
    installations = manager.list_all_installations()
    
    return {
        "total": len(installations),
        "installations": installations
    }


@router.get("/installations/{owner}")
async def get_installation(owner: str):
    """
    Get installation details for a specific owner
    
    Args:
        owner: GitHub username or organization name
    
    Returns:
        Installation details and available repositories
    """
    manager = GitHubInstallationManager()
    installation_id = manager.get_installation_id_from_s3(owner)
    
    if not installation_id:
        raise HTTPException(
            status_code=404,
            detail=f"No installation found for {owner}"
        )
    
    installations = manager.list_all_installations()
    installation_data = installations.get(owner, {})
    
    return {
        "owner": owner,
        "installation_id": installation_id,
        "account_type": installation_data.get("account_type"),
        "repositories": installation_data.get("repositories", []),
        "installed_at": installation_data.get("installed_at"),
        "updated_at": installation_data.get("updated_at")
    }


@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a job (marks as cancelled, actual cancellation not implemented)"""
    if job_id not in jobs_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_store[job_id]
    
    if job["status"] in ["completed", "failed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job with status: {job['status']}"
        )
    
    jobs_store[job_id]["status"] = "cancelled"
    jobs_store[job_id]["completed_at"] = datetime.now().isoformat()
    
    return {"message": "Job cancelled", "job_id": job_id}
