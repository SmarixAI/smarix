"""
Admin-related API routes for the RAG Chatbot
Contains all admin endpoints and WebSocket handlers
"""

from datetime import datetime
from fastapi import APIRouter, Body, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from pathlib import Path
import os
import json
import asyncio
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from core.DataCollection.DataCollectionFromGithub.repository_processor import AsyncRepositoryProcessor
from core.DataCollection.DataCollectionFromGithub.github_client import AsyncGitHubClient
from utils.s3 import s3_manager

STATE_S3_KEY = "Admin/state/runtime_state.json"


router = APIRouter()


# ==================== PYDANTIC MODELS ====================

class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    username: str
    old_password: str
    new_password: str


class OffboardingLoginRequest(BaseModel):
    username: str
    password: str
    role: str  # "manager" or "employee"


class ValidateRepositoryRequest(BaseModel):
    organization: str
    repo_name: str


class SetupRequest(BaseModel):
    organization: str
    repo_name: str


class SetupResponse(BaseModel):
    status: str
    message: str
    step: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class OnboardingRequest(BaseModel):
    generators: Optional[List[str]] = None


class OffboardingRequest(BaseModel):
    steps: Optional[List[str]] = None  # Ignored: pipeline runs all steps for single user
    employee_name: Optional[str] = None  # Ignored: user is derived from GitHub data (top contributor)


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str  # "admin", "manager", or "employee"
    name: Optional[str] = None
    employeeId: Optional[str] = None
    designation: Optional[str] = None
    status: Optional[str] = "general"
    lastDay: Optional[str] = None


class UpdateUserRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    name: Optional[str] = None
    employeeId: Optional[str] = None
    designation: Optional[str] = None
    status: Optional[str] = None
    lastDay: Optional[str] = None


# ==================== ADMIN AUTHENTICATION ENDPOINTS ====================

@router.post("/admin/auth/login")
async def admin_login(request: LoginRequest):
    """Authenticate admin user"""
    from .chatbot_api import get_users_file_path
    
    try:
        users_file = get_users_file_path()
        
        # Create file if it doesn't exist
        if not users_file.exists():
            users_file.parent.mkdir(parents=True, exist_ok=True)
            default_users = {
                "users": [
                    {
                        "username": "admin",
                        "password": "admin",
                        "role": "admin",
                        "employeeId": None
                    }
                ]
            }
            with open(users_file, 'w') as f:
                json.dump(default_users, f, indent=2)
        
        # Read users
        with open(users_file, 'r') as f:
            data = json.load(f)
        
        users = data.get("users", [])
        
        # Find user
        user = next((u for u in users if u.get("username") == request.username), None)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        if user.get("password") != request.password:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Verify user has admin role - strict check
        user_role = user.get("role")
        if not user_role or str(user_role).lower() != "admin":
            raise HTTPException(status_code=403, detail="Access denied. Admin role required.")
        
        # Return user info (without password)
        return {
            "status": "success",
            "user": {
                "username": user.get("username"),
                "role": user.get("role", "admin"),
                "employeeId": user.get("employeeId")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during login: {str(e)}")


@router.post("/admin/auth/change-password")
async def admin_change_password(request: ChangePasswordRequest):
    """Change user password (dummy implementation for now)"""
    from .chatbot_api import get_users_file_path
    
    try:
        users_file = get_users_file_path()
        
        if not users_file.exists():
            raise HTTPException(status_code=404, detail="Users file not found")
        
        # Read users
        with open(users_file, 'r') as f:
            data = json.load(f)
        
        users = data.get("users", [])
        
        # Find user
        user = next((u for u in users if u.get("username") == request.username), None)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify old password
        if user.get("password") != request.old_password:
            raise HTTPException(status_code=401, detail="Invalid old password")
        
        # Update password (dummy - not actually saving for now as requested)
        # user["password"] = request.new_password
        
        # Save (commented out for dummy implementation)
        # with open(users_file, 'w') as f:
        #     json.dump(data, f, indent=2)
        
        return {
            "status": "success",
            "message": "Password change requested (dummy implementation)"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error changing password: {str(e)}")


@router.post("/admin/auth/offboarding/login")
async def offboarding_login(request: OffboardingLoginRequest):
    """Authenticate offboarding user (manager or employee)"""
    from .chatbot_api import get_users_file_path
    
    try:
        users_file = get_users_file_path()
        
        # Create file if it doesn't exist
        if not users_file.exists():
            users_file.parent.mkdir(parents=True, exist_ok=True)
            default_users = {
                "users": [
                    {
                        "username": "admin",
                        "password": "admin",
                        "role": "admin",
                        "employeeId": None
                    },
                    {
                        "username": "manager1",
                        "password": "manager1",
                        "role": "manager",
                        "employeeId": None,
                        "name": "Rajesh Kumar"
                    }
                ]
            }
            with open(users_file, 'w') as f:
                json.dump(default_users, f, indent=2)
        
        # Read users
        with open(users_file, 'r') as f:
            data = json.load(f)
        
        users = data.get("users", [])
        
        # Find user by username (case-insensitive for username)
        user = next((u for u in users if u.get("username", "").lower() == request.username.lower()), None)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Verify password
        if user.get("password") != request.password:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Verify role matches - strict check
        user_role = user.get("role", "").lower()
        requested_role = request.role.lower()
        
        # Only allow manager or employee roles for offboarding login
        if requested_role not in ["manager", "employee"]:
            raise HTTPException(status_code=403, detail="Invalid role for offboarding login. Only manager or employee allowed.")
        
        # Verify user's role matches requested role
        if user_role != requested_role:
            raise HTTPException(status_code=403, detail=f"Access denied. User has '{user_role}' role, but '{requested_role}' role is required.")
        
        # Return user info (without password)
        user_data = {
            "username": user.get("username"),
            "role": user.get("role", requested_role),
            "employeeId": user.get("employeeId"),
            "name": user.get("name", user.get("username"))
        }
        
        # Add status field for employees and managers
        if user_role in ["employee", "manager"]:
            user_data["status"] = user.get("status", "general")
        
        return {
            "status": "success",
            "user": user_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during login: {str(e)}")


# ==================== ADMIN UTILITY ENDPOINTS ====================

@router.get("/admin/test")
async def admin_test():
    """Test endpoint to verify admin routes are working"""
    return {"status": "ok", "message": "Admin endpoints are accessible"}


@router.get("/admin/routes")
async def list_admin_routes():
    """List all admin routes for debugging"""
    from fastapi import FastAPI
    from .chatbot_api import app
    
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and route.path.startswith('/admin'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if hasattr(route, 'methods') else []
            })
    return {"status": "ok", "routes": routes}


@router.post("/admin/validate-repository")
async def validate_repository(request: ValidateRepositoryRequest):
    """
    Validate if a GitHub repository exists and is accessible.
    Returns validation result with detailed error messages.
    """
    import requests
    import re
    from config.DataCollection.settings import Config
    
    config = Config()
    organization = request.organization.strip()
    repo_name = request.repo_name.strip()
    
    # Basic validation
    if not organization:
        return {
            "is_valid": False,
            "error": "Organization name cannot be empty",
            "field": "organization"
        }
    
    if not repo_name:
        return {
            "is_valid": False,
            "error": "Repository name cannot be empty",
            "field": "repo_name"
        }
    
    # Check GitHub API format (alphanumeric and hyphens only)
    if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$', organization):
        return {
            "is_valid": False,
            "error": "Organization name contains invalid characters. Only letters, numbers, and hyphens are allowed.",
            "field": "organization"
        }
    
    if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$', repo_name):
        return {
            "is_valid": False,
            "error": "Repository name contains invalid characters. Only letters, numbers, and hyphens are allowed.",
            "field": "repo_name"
        }
    
    # Check repository existence via GitHub API
    try:
        headers = {'Accept': 'application/vnd.github.v3+json'}
        if config.GITHUB_TOKEN:
            headers['Authorization'] = f'token {config.GITHUB_TOKEN}'
        
        api_url = f"{config.GITHUB_API_BASE_URL}/repos/{organization}/{repo_name}"
        response = requests.get(api_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            repo_data = response.json()
            # Check if repository is accessible (not private without access)
            return {
                "is_valid": True,
                "message": f"Repository {organization}/{repo_name} is accessible",
                "repository": {
                    "name": repo_data.get("name"),
                    "full_name": repo_data.get("full_name"),
                    "description": repo_data.get("description"),
                    "private": repo_data.get("private", False),
                    "language": repo_data.get("language"),
                    "stars": repo_data.get("stargazers_count", 0),
                    "forks": repo_data.get("forks_count", 0),
                    "default_branch": repo_data.get("default_branch", "main")
                }
            }
        elif response.status_code == 404:
            return {
                "is_valid": False,
                "error": f"Repository '{organization}/{repo_name}' not found. Please check the organization and repository names.",
                "field": "both"
            }
        elif response.status_code == 403:
            # Could be rate limit or private repo without access
            rate_limit_remaining = response.headers.get('X-RateLimit-Remaining', 'unknown')
            if rate_limit_remaining == '0':
                return {
                    "is_valid": False,
                    "error": "GitHub API rate limit exceeded. Please try again later.",
                    "field": "both"
                }
            else:
                return {
                    "is_valid": False,
                    "error": f"Repository '{organization}/{repo_name}' is private or access is forbidden. Please check your GitHub token permissions.",
                    "field": "both"
                }
        elif response.status_code == 401:
            return {
                "is_valid": False,
                "error": "GitHub API authentication failed. Please check your GitHub token.",
                "field": "both"
            }
        else:
            return {
                "is_valid": False,
                "error": f"GitHub API returned status {response.status_code}. Please try again later.",
                "field": "both"
            }
    except requests.exceptions.Timeout:
        return {
            "is_valid": False,
            "error": "Request to GitHub API timed out. Please check your internet connection and try again.",
            "field": "both"
        }
    except requests.exceptions.ConnectionError:
        return {
            "is_valid": False,
            "error": "Failed to connect to GitHub API. Please check your internet connection.",
            "field": "both"
        }
    except Exception as e:
        return {
            "is_valid": False,
            "error": f"Error validating repository: {str(e)}",
            "field": "both"
        }


# ==================== HELPER FUNCTIONS FOR PIPELINE STEPS ====================

def update_runtime_state(owner: str, repo_name: str) -> dict:
    """
    Update runtime_state.json in S3 with the current repository information.
    This must be called before running pipeline steps that read from state.
    """
    print(f"🔵 Updating S3 runtime state to: {owner}/{repo_name}")
    
    try:
        # 1. Try to download existing state to preserve other data
        try:
            state = s3_manager.download_json(STATE_S3_KEY)
            if not isinstance(state, dict):
                state = {}
        except Exception:
            # If file doesn't exist or fails to load, start fresh
            print("⚠️ State file not found in S3, creating new state object.")
            state = {}

        # 2. Update curr_repo and user_default_repo
        repo_data = {
            "owner": owner,
            "name": repo_name
        }
        
        state["curr_repo"] = repo_data
        state["user_default_repo"] = repo_data
        state["last_updated"] = str(datetime.now())

        # 3. Upload updated state back to S3
        s3_manager.upload_json(state, STATE_S3_KEY)
        print("✅ Runtime state updated successfully in S3")
        
        return {
            "success": True,
            "message": f"Updated S3 runtime_state.json with {owner}/{repo_name}",
            "s3_key": STATE_S3_KEY
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": f"Failed to update runtime_state.json in S3: {str(e)}"
        }


async def async_run_data_collection(owner: str, repo: str) -> Dict[str, Any]:
    processor = AsyncRepositoryProcessor()

    async with AsyncGitHubClient(max_concurrent_requests=50) as github_client:
        ok = await processor.test_connection(github_client)
        if not ok:
            return {"success": False, "error": "GitHub API connection failed"}

        repo_data = await processor.process_repository(owner, repo)
        output_file = processor.save_repository_data(repo_data, owner, repo)

        return {
            "success": True,
            "output_file": str(output_file),
            "stats": repo_data.get("stats", {}),
            "message": f"Successfully collected data for {owner}/{repo}",
        }

def run_data_collection_sync(owner: str, repo: str) -> Dict[str, Any]:
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(async_run_data_collection(owner, repo))
    finally:
        loop.close()


def run_data_processing() -> Dict[str, Any]:
    """Run batch data processing with S3 verification"""
    try:
        import sys
        from pathlib import Path
        
        # Add the main directory to path
        main_dir = Path(__file__).resolve().parent.parent.parent / "main" / "DataProcessing"
        if str(main_dir) not in sys.path:
            sys.path.insert(0, str(main_dir.parent.parent))
        
        from main.DataProcessing.process_data import batch_process
        
        # 1. Run the processing (Assumes batch_process handles S3 upload internally)
        batch_process()
        
        # 2. Verify Output in S3 instead of local directory
        # Looking for files in the "DataProcessing/" prefix
        try:
            s3_files = s3_manager.list_files("DataProcessing/")
            # Filter for specific json files we expect
            processed_files = [
                f for f in s3_files 
                if f.endswith("_git_chunks.json") or f.endswith("_gmail_chunks.json")
            ]
        except Exception:
            processed_files = []
        
        return {
            "success": True,
            "processed_files": processed_files,
            "message": f"Successfully processed {len(processed_files)} files (verified in S3)"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def run_embedding_generation() -> Dict[str, Any]:
    """Run batch embedding generation with S3 verification"""
    try:
        from main.GenerateEmbedding.generate_embedding import batch_generate
        
        # Create args object for batch_generate
        class Args:
            output_dir = "../../data/Embeddings/" # Internal logic might still need this if it writes locally first
            provider = None
            model = None
            batch_size = 32
            cache_dir = "../../data/Embeddings/embeddings_cache"
            batch = True
        
        args = Args()
        batch_generate(args)
        
        # Verify Output in S3
        # We expect folders/keys under "Embeddings/" excluding cache
        try:
            # Listing files will return full keys (e.g., Embeddings/openai/data.pkl)
            all_objects = s3_manager.list_files("Embeddings/")
            
            # Extract unique "types" (immediate subfolders under Embeddings/)
            # e.g., Embeddings/openai/... -> openai
            embedding_types = set()
            for obj in all_objects:
                parts = obj.split('/')
                # If path is Embeddings/openai/file.pkl, parts[1] is 'openai'
                if len(parts) > 1 and parts[1] != "embeddings_cache":
                    embedding_types.add(parts[1])
            
            embedding_types_list = list(embedding_types)
            
        except Exception:
            embedding_types_list = []
        
        return {
            "success": True,
            "embedding_types": embedding_types_list,
            "message": f"Successfully generated embeddings for {len(embedding_types_list)} types (verified in S3)"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def run_vectordb_build() -> Dict[str, Any]:
    """Run vector database building with S3 state and verification"""
    try:
        from core.VectorDB.build_indices import main as build_indices_main
        
        # 1. Get current repo from S3 State (No local file check)
        try:
            state = s3_manager.download_json(STATE_S3_KEY)
        except Exception:
            return {"success": False, "error": f"Could not read {STATE_S3_KEY} from S3"}
        
        curr_repo = state.get("curr_repo", {})
        owner = curr_repo.get("owner")
        repo_name = curr_repo.get("name")
        
        if not owner or not repo_name:
            return {"success": False, "error": "curr_repo.owner or curr_repo.name missing in runtime_state.json"}
        
        # 2. Call build_indices main function
        # (Assumes this function reads from S3 state internally too)
        build_indices_main()
        
        # 3. Verify Output in S3
        # Expected path: VectorDB/<owner>/<repo_name>/<index_type>/faiss.index
        s3_prefix = f"VectorDB/{owner}/{repo_name}/"
        
        try:
            s3_files = s3_manager.list_files(s3_prefix)
            
            # Identify indices by looking for folders containing 'faiss.index'
            indices = set()
            for f in s3_files:
                if "faiss.index" in f:
                    # Path: VectorDB/owner/repo/git_index/faiss.index
                    # parts: [VectorDB, owner, repo, git_index, faiss.index]
                    parts = f.split('/')
                    # The index name is the folder immediately following the repo name
                    if len(parts) >= 4:
                        indices.add(parts[-2]) # -2 is the folder name containing the index file
            
            indices_list = list(indices)
            
            if not indices_list:
                return {"success": False, "error": f"No vector indices found in S3 at {s3_prefix}"}

            return {
                "success": True,
                "indices": indices_list,
                "message": f"Successfully built {len(indices_list)} vector indices for {owner}/{repo_name}",
                "repo": f"{owner}/{repo_name}"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to verify S3 files: {str(e)}"}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def run_onboarding(generators_to_run: list = None) -> Dict[str, Any]:
    """Run onboarding data generation using S3 state"""
    try:
        import sys
        from pathlib import Path
        # We assume get_database_path_for_repo is updated or we might need to handle the path differently
        from .chatbot_api import get_database_path_for_repo 
        
        # Add the main directory to path
        repo_root = Path(__file__).resolve().parent.parent.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        
        from main.Onboarding.generate_all_onboarding import generate_all_onboarding_data
        
        # 1. Get current repo from S3 State
        try:
            state = s3_manager.download_json(STATE_S3_KEY)
        except Exception:
            return {"success": False, "error": f"Could not read {STATE_S3_KEY} from S3"}
        
        curr_repo = state.get("curr_repo", {})
        owner = curr_repo.get("owner")
        repo_name = curr_repo.get("name")
        
        if not owner or not repo_name:
            return {"success": False, "error": "curr_repo.owner or curr_repo.name missing in runtime_state.json"}
        
        # 2. Handle VectorDB Path
        # Note: If generate_all_onboarding_data expects a local file path, you might need to
        # download the index from S3 to a temporary location here. 
        # For now, we assume get_database_path_for_repo returns a valid path (local or S3 URI) 
        # that the generator can handle.
        vectordb_path = get_database_path_for_repo(owner, repo_name)
        
        if not vectordb_path:
             # Fallback check in S3 just to be sure it exists before trying to run
             if not s3_manager.list_files(f"VectorDB/{owner}/{repo_name}"):
                 return {"success": False, "error": f"Vector database not found in S3 for {owner}/{repo_name}"}
        
        # 3. Run onboarding generation
        results = generate_all_onboarding_data(
            gmail_db_path=None,
            provider='openai',
            model=None,
            generators_to_run=generators_to_run
        )
        
        # 4. Check results
        successful = sum(1 for r in results.values() if r.get('status') == 'success')
        total = len(results)
        
        if successful == total:
            return {
                "success": True,
                "message": f"Successfully generated onboarding data ({successful}/{total} generators)",
                "results": results
            }
        else:
            return {
                "success": False,
                "error": f"Onboarding generation partially failed ({successful}/{total} successful)",
                "results": results
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def run_offboarding(steps_to_run: list = None, employee_name: str = None) -> Dict[str, Any]:
    try:
        if not employee_name:
            return {"success": False, "error": "Employee name is required"}

        import sys
        from pathlib import Path

        repo_root = Path(__file__).resolve().parent.parent.parent

        pipeline_script = repo_root / "main" / "Offboarding" / "new_logic" / "run_offboarding_pipeline.py"

        if not pipeline_script.exists():
            return {"success": False, "error": f"Pipeline not found: {pipeline_script}"}

        # Adjust this path according to your repo data location
        input_file = Path("/Users/vishalkeshari/Desktop/smarix/backend/data/DataCollectionFromGit/CCExtractor/taskwarrior-flutter/taskwarrior-flutter.json")
        output_dir = repo_root / "data" / "Offboarding" / employee_name
        output_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable,
            str(pipeline_script),
            "--employee_name", employee_name
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600
        )

        if result.returncode == 0:
            return {
                "success": True,
                "message": f"Offboarding pipeline executed successfully for {employee_name}",
                "output_dir": str(output_dir)
            }
        else:
            return {
                "success": False,
                "error": result.stderr or result.stdout
            }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Pipeline timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def verify_employee_exists(employee_name: str) -> Dict[str, Any]:
    """Verify if an employee exists in users.json or PR data"""
    try:
        from .chatbot_api import get_users_file_path
        
        repo_root = Path(__file__).resolve().parent.parent.parent
        users_file = get_users_file_path()
        
        # Check in users.json
        if users_file.exists():
            with open(users_file, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
                users = users_data.get('users', [])
                for user in users:
                    # Case-insensitive name matching
                    if user.get('name', '').lower() == employee_name.lower() or \
                       user.get('username', '').lower() == employee_name.lower():
                        return {
                            "exists": True,
                            "source": "users.json",
                            "employee": user
                        }
        
        # Check in PR data (1employees_with_ids.json)
        employees_file = repo_root / "data" / "Offboarding" / "1employees_with_ids.json"
        if not employees_file.exists():
            possible_paths = [
                repo_root / "backend" / "data" / "Offboarding" / "1employees_with_ids.json",
            ]
            for path in possible_paths:
                if path.exists():
                    employees_file = path
                    break
        
        if employees_file.exists():
            with open(employees_file, 'r', encoding='utf-8') as f:
                employees_data = json.load(f)
                employees = employees_data.get('employees', [])
                for emp in employees:
                    # Case-insensitive name matching
                    if emp.get('name', '').lower() == employee_name.lower():
                        return {
                            "exists": True,
                            "source": "pr_data",
                            "employee": emp
                        }
        
        return {"exists": False, "error": f"Employee '{employee_name}' not found in users.json or PR data"}
    except Exception as e:
        return {"exists": False, "error": f"Error verifying employee: {str(e)}"}


# ==================== ADMIN SETUP ENDPOINTS ====================

@router.post("/admin/setup/data-collection", response_model=SetupResponse)
async def admin_data_collection(request: SetupRequest):
    """Step 1: Data Collection"""
    try:
        # First update runtime_state.json
        state_result = update_runtime_state(request.organization, request.repo_name)
        if not state_result["success"]:
            raise HTTPException(status_code=500, detail=state_result.get("error", "Failed to update state"))
        
        # Then run data collection
        result = await async_run_data_collection(
            request.organization,
            request.repo_name
        )
        if result["success"]:
            return SetupResponse(
                status="success",
                message=result["message"],
                step="data-collection",
                details=result
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Data collection failed"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/setup/data-processing", response_model=SetupResponse)
async def admin_data_processing(request: SetupRequest):
    """Step 2: Data Processing"""
    try:
        # First update runtime_state.json
        state_result = update_runtime_state(request.organization, request.repo_name)
        if not state_result["success"]:
            raise HTTPException(status_code=500, detail=state_result.get("error", "Failed to update state"))
        
        # Then run data processing
        result = run_data_processing()
        if result["success"]:
            return SetupResponse(
                status="success",
                message=result["message"],
                step="data-processing",
                details=result
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Data processing failed"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/setup/embedding", response_model=SetupResponse)
async def admin_embedding(request: SetupRequest):
    """Step 3: Embedding Generation"""
    try:
        # First update runtime_state.json
        state_result = update_runtime_state(request.organization, request.repo_name)
        if not state_result["success"]:
            raise HTTPException(status_code=500, detail=state_result.get("error", "Failed to update state"))
        
        # Then run embedding generation
        result = run_embedding_generation()
        if result["success"]:
            return SetupResponse(
                status="success",
                message=result["message"],
                step="embedding",
                details=result
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Embedding generation failed"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/setup/vectordb", response_model=SetupResponse)
async def admin_vectordb(request: SetupRequest):
    """Step 4: VectorDB Building"""
    try:
        # First update runtime_state.json
        state_result = update_runtime_state(request.organization, request.repo_name)
        if not state_result["success"]:
            raise HTTPException(status_code=500, detail=state_result.get("error", "Failed to update state"))
        
        # Then run vectordb build
        result = run_vectordb_build()
        if result["success"]:
            return SetupResponse(
                status="success",
                message=result["message"],
                step="vectordb",
                details=result
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "VectorDB building failed"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/setup/cancel")
async def cancel_pipeline():
    """Cancel the currently running pipeline"""
    from .chatbot_api import pipeline_cancelled, current_pipeline_task
    
    pipeline_cancelled.set()
    if current_pipeline_task:
        current_pipeline_task.cancel()
    return {"status": "cancelled", "message": "Pipeline cancellation requested"}


# ==================== ADMIN ONBOARDING/OFFBOARDING ENDPOINTS ====================

@router.post("/admin/onboarding/run", response_model=SetupResponse)
async def admin_onboarding(request: OnboardingRequest = None):
    """Run onboarding data generation"""
    try:
        generators = None
        if request and request.generators:
            generators = request.generators
        result = run_onboarding(generators)
        if result["success"]:
            return SetupResponse(
                status="success",
                message=result["message"],
                step="onboarding",
                details=result
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Onboarding generation failed"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/offboarding/run", response_model=SetupResponse)
async def admin_offboarding(request: OffboardingRequest = Body(...)):
    try:
        if not request.employee_name:
            raise HTTPException(status_code=400, detail="Employee name required")

        result = run_offboarding(employee_name=request.employee_name)

        if result["success"]:
            return SetupResponse(
                status="success",
                message=result["message"],
                step="offboarding",
                details=result
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ==================== ADMIN HISTORY ENDPOINTS ====================

def get_admin_history_file_path() -> Path:
    """Get the path to the admin setup history JSON file"""
    # Try multiple possible locations
    possible_paths = [
        Path("../../data/Admin/admin_setup_history.json"),
        Path("data/Admin/admin_setup_history.json"),
        Path("../data/Admin/admin_setup_history.json"),
        Path(__file__).parent.parent.parent / "data" / "Admin" / "admin_setup_history.json",
    ]
    
    for path in possible_paths:
        abs_path = path.resolve()
        if abs_path.parent.exists():
            return abs_path
    
    # Default to relative to this file
    return Path(__file__).parent.parent.parent / "data" / "Admin" / "admin_setup_history.json"


def load_admin_history() -> list:
    """Load admin setup history from JSON file"""
    history_file = get_admin_history_file_path()
    
    try:
        if history_file.exists():
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
                # Backward compatibility: add execution_mode to old entries
                for entry in history:
                    if "execution_mode" not in entry:
                        entry["execution_mode"] = "full"  # Default old entries to full pipeline
                return history
        return []
    except Exception as e:
        print(f"Error loading admin history: {e}")
        return []


def save_admin_history(history: list) -> bool:
    """Save admin setup history to JSON file"""
    history_file = get_admin_history_file_path()
    
    try:
        # Ensure directory exists
        history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to file
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving admin history: {e}")
        return False


@router.get("/admin/history")
async def get_admin_history():
    """Get admin setup history"""
    history = load_admin_history()
    return {"status": "success", "history": history}


@router.post("/admin/history")
async def add_admin_history_entry(entry: dict):
    """Add a new entry to admin setup history"""
    history = load_admin_history()
    
    # Add new entry at the beginning
    history.insert(0, entry)
    
    # Keep only last 50 entries
    history = history[:50]
    
    if save_admin_history(history):
        return {"status": "success", "message": "History entry added", "history": history}
    else:
        raise HTTPException(status_code=500, detail="Failed to save history")


@router.delete("/admin/history")
async def clear_admin_history():
    """Clear all admin setup history"""
    if save_admin_history([]):
        return {"status": "success", "message": "History cleared"}
    else:
        raise HTTPException(status_code=500, detail="Failed to clear history")


# ==================== ADMIN USER MANAGEMENT ENDPOINTS ====================

@router.get("/admin/users")
async def get_all_users():
    """Get all users from users.json"""
    from .chatbot_api import get_users_file_path
    
    try:
        users_file = get_users_file_path()
        
        if not users_file.exists():
            return {"users": []}
        
        with open(users_file, 'r') as f:
            data = json.load(f)
        
        # Remove passwords from response for security
        users = data.get("users", [])
        safe_users = []
        for user in users:
            safe_user = {k: v for k, v in user.items() if k != "password"}
            safe_users.append(safe_user)
        
        return {"users": safe_users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading users: {str(e)}")


@router.post("/admin/users")
async def create_user(request: CreateUserRequest):
    """Create a new user"""
    from .chatbot_api import get_users_file_path
    
    try:
        users_file = get_users_file_path()
        
        # Create directory if it doesn't exist
        users_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Read existing users
        if users_file.exists():
            with open(users_file, 'r') as f:
                data = json.load(f)
        else:
            data = {"users": []}
        
        users = data.get("users", [])
        
        # Check if username already exists
        if any(u.get("username", "").lower() == request.username.lower() for u in users):
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Create new user
        new_user = {
            "username": request.username,
            "password": request.password,
            "role": request.role,
            "status": request.status or "general"
        }
        
        if request.name:
            new_user["name"] = request.name
        if request.employeeId:
            new_user["employeeId"] = request.employeeId
        if request.designation:
            new_user["designation"] = request.designation
        if request.lastDay:
            new_user["lastDay"] = request.lastDay
        
        users.append(new_user)
        data["users"] = users
        
        # Write back to file
        with open(users_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Return user without password
        safe_user = {k: v for k, v in new_user.items() if k != "password"}
        return {"status": "success", "message": "User created successfully", "user": safe_user}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")


@router.put("/admin/users/{username}")
async def update_user(username: str, request: UpdateUserRequest):
    """Update an existing user"""
    from .chatbot_api import get_users_file_path
    
    try:
        users_file = get_users_file_path()
        
        if not users_file.exists():
            raise HTTPException(status_code=404, detail="Users file not found")
        
        # Read existing users
        with open(users_file, 'r') as f:
            data = json.load(f)
        
        users = data.get("users", [])
        
        # Find user
        user_index = next((i for i, u in enumerate(users) if u.get("username", "").lower() == username.lower()), None)
        
        if user_index is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = users[user_index]
        
        # Update fields if provided
        if request.username is not None and request.username.lower() != username.lower():
            # Check if new username already exists
            if any(u.get("username", "").lower() == request.username.lower() for i, u in enumerate(users) if i != user_index):
                raise HTTPException(status_code=400, detail="Username already exists")
            user["username"] = request.username
        
        if request.password is not None and request.password.strip():
            user["password"] = request.password
        if request.role is not None:
            user["role"] = request.role
        if request.name is not None:
            user["name"] = request.name
        if request.employeeId is not None:
            user["employeeId"] = request.employeeId
        if request.designation is not None:
            user["designation"] = request.designation
        if request.status is not None:
            user["status"] = request.status
        if request.lastDay is not None:
            user["lastDay"] = request.lastDay
        
        users[user_index] = user
        data["users"] = users
        
        # Write back to file
        with open(users_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Return user without password
        safe_user = {k: v for k, v in user.items() if k != "password"}
        return {"status": "success", "message": "User updated successfully", "user": safe_user}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")


@router.delete("/admin/users/{username}")
async def delete_user(username: str):
    """Delete a user"""
    from .chatbot_api import get_users_file_path
    
    try:
        users_file = get_users_file_path()
        
        if not users_file.exists():
            raise HTTPException(status_code=404, detail="Users file not found")
        
        # Read existing users
        with open(users_file, 'r') as f:
            data = json.load(f)
        
        users = data.get("users", [])
        
        # Find and remove user
        original_length = len(users)
        users = [u for u in users if u.get("username", "").lower() != username.lower()]
        
        if len(users) == original_length:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prevent deleting the last admin
        admins = [u for u in users if u.get("role", "").lower() == "admin"]
        if len(admins) == 0:
            raise HTTPException(status_code=400, detail="Cannot delete the last admin user")
        
        data["users"] = users
        
        # Write back to file
        with open(users_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return {"status": "success", "message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")


# ==================== ADMIN WEBSOCKET HANDLERS ====================

@router.websocket("/ws/admin/pipeline")
async def websocket_pipeline(websocket: WebSocket):
    """WebSocket endpoint for real-time pipeline progress updates"""
    await websocket.accept()
    from .chatbot_api import pipeline_cancelled, current_pipeline_task
    
    try:
        # Wait for start message
        data = await websocket.receive_text()
        message = json.loads(data)
        
        if message.get("action") != "start":
            await websocket.send_json({"type": "error", "message": "Invalid action"})
            await websocket.close()
            return
        
        request_data = message.get("request", {})
        organization = request_data.get("organization")
        repo_name = request_data.get("repo_name")
        
        if not organization or not repo_name:
            await websocket.send_json({"type": "error", "message": "Missing organization or repo_name"})
            await websocket.close()
            return
        
        # Step 0: Update runtime_state.json BEFORE running any pipeline steps
        await websocket.send_json({
            "type": "step_start",
            "step": "state-update",
            "message": "Updating repository state..."
        })
        await asyncio.sleep(0.1)
        
        state_update_result = update_runtime_state(organization, repo_name)
        if not state_update_result["success"]:
            await websocket.send_json({
                "type": "step_error",
                "step": "state-update",
                "message": state_update_result.get("error", "Failed to update state")
            })
            await websocket.close()
            return
        
        await websocket.send_json({
            "type": "step_complete",
            "step": "state-update",
            "message": state_update_result.get("message", "State updated successfully")
        })
        await asyncio.sleep(0.1)
        
        # Reset cancellation flag
        pipeline_cancelled.clear()
        results = {}
        
        # Run pipeline in executor to avoid blocking
        executor = ThreadPoolExecutor(max_workers=1)
        
        def run_step(step_name: str, step_func, *args):
            """Run a single step and check for cancellation"""
            if pipeline_cancelled.is_set():
                return {"success": False, "error": "Pipeline cancelled", "cancelled": True}
            
            try:
                result = step_func(*args)
                return result
            except Exception as e:
                import traceback
                traceback.print_exc()
                return {"success": False, "error": str(e)}
        
        try:
            # Step 1: Data Collection
            await websocket.send_json({
                "type": "step_start",
                "step": "data-collection",
                "message": "Starting data collection..."
            })
            await asyncio.sleep(0.1)  # Small delay to ensure message is sent
            
            future = executor.submit(run_step, "data-collection", run_data_collection_sync, organization, repo_name)
            # Note: We can't set current_pipeline_task here as it's in another module
            # The global state will be updated by the module that owns it
            results["data_collection"] = future.result()
            
            if pipeline_cancelled.is_set():
                await websocket.send_json({
                    "type": "cancelled",
                    "message": "Pipeline was cancelled",
                    "step": "data-collection"
                })
                return
            
            if not results["data_collection"]["success"]:
                await websocket.send_json({
                    "type": "step_error",
                    "step": "data-collection",
                    "message": results["data_collection"].get("error", "Data collection failed")
                })
                return
            
            await websocket.send_json({
                "type": "step_complete",
                "step": "data-collection",
                "message": results["data_collection"].get("message", "Data collection completed")
            })
            await asyncio.sleep(0.1)  # Small delay to ensure message is sent
            
            # Step 2: Data Processing
            await websocket.send_json({
                "type": "step_start",
                "step": "data-processing",
                "message": "Starting data processing..."
            })
            await asyncio.sleep(0.1)  # Small delay to ensure message is sent
            
            future = executor.submit(run_step, "data-processing", run_data_processing)
            results["data_processing"] = future.result()
            
            if pipeline_cancelled.is_set():
                await websocket.send_json({
                    "type": "cancelled",
                    "message": "Pipeline was cancelled",
                    "step": "data-processing"
                })
                return
            
            if not results["data_processing"]["success"]:
                await websocket.send_json({
                    "type": "step_error",
                    "step": "data-processing",
                    "message": results["data_processing"].get("error", "Data processing failed")
                })
                return
            
            await websocket.send_json({
                "type": "step_complete",
                "step": "data-processing",
                "message": results["data_processing"].get("message", "Data processing completed")
            })
            await asyncio.sleep(0.1)  # Small delay to ensure message is sent
            
            # Step 3: Embedding Generation
            await websocket.send_json({
                "type": "step_start",
                "step": "embedding",
                "message": "Starting embedding generation..."
            })
            await asyncio.sleep(0.1)  # Small delay to ensure message is sent
            
            future = executor.submit(run_step, "embedding", run_embedding_generation)
            results["embedding"] = future.result()
            
            if pipeline_cancelled.is_set():
                await websocket.send_json({
                    "type": "cancelled",
                    "message": "Pipeline was cancelled",
                    "step": "embedding"
                })
                return
            
            if not results["embedding"]["success"]:
                await websocket.send_json({
                    "type": "step_error",
                    "step": "embedding",
                    "message": results["embedding"].get("error", "Embedding generation failed")
                })
                return
            
            await websocket.send_json({
                "type": "step_complete",
                "step": "embedding",
                "message": results["embedding"].get("message", "Embedding generation completed")
            })
            await asyncio.sleep(0.1)  # Small delay to ensure message is sent
            
            # Step 4: VectorDB Building
            await websocket.send_json({
                "type": "step_start",
                "step": "vectordb",
                "message": "Building vector database..."
            })
            await asyncio.sleep(0.1)  # Small delay to ensure message is sent
            
            future = executor.submit(run_step, "vectordb", run_vectordb_build)
            results["vectordb"] = future.result()
            
            if pipeline_cancelled.is_set():
                await websocket.send_json({
                    "type": "cancelled",
                    "message": "Pipeline was cancelled",
                    "step": "vectordb"
                })
                return
            
            if not results["vectordb"]["success"]:
                await websocket.send_json({
                    "type": "step_error",
                    "step": "vectordb",
                    "message": results["vectordb"].get("error", "VectorDB building failed")
                })
                return
            
            await websocket.send_json({
                "type": "step_complete",
                "step": "vectordb",
                "message": results["vectordb"].get("message", "VectorDB build completed")
            })
            
            # All steps completed
            await websocket.send_json({
                "type": "complete",
                "message": f"Complete pipeline executed successfully for {organization}/{repo_name}",
                "results": results
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            await websocket.send_json({
                "type": "error",
                "message": str(e),
                "results": results
            })
        finally:
            executor.shutdown(wait=False)
            
    except WebSocketDisconnect:
        print("Pipeline WebSocket disconnected")
        pipeline_cancelled.set()
    except Exception as e:
        print(f"Pipeline WebSocket error: {e}")
        await websocket.send_json({"type": "error", "message": str(e)})

