"""
Admin-related API routes for the RAG Chatbot
Contains all admin endpoints and WebSocket handlers
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
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
    steps: Optional[List[str]] = None
    employee_name: str


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

def update_runtime_state(owner: str, repo_name: str) -> Dict[str, Any]:
    """
    Update runtime_state.json with the current repository information.
    This must be called before running pipeline steps that read from state.
    """
    try:
        from .chatbot_api import get_runtime_state_file_path
        
        state_file = get_runtime_state_file_path()
        
        # Create directory if it doesn't exist
        state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Read existing state or create new
        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
        else:
            state = {}
        
        # Update curr_repo and user_default_repo
        state["curr_repo"] = {
            "owner": owner,
            "name": repo_name
        }
        state["user_default_repo"] = {
            "owner": owner,
            "name": repo_name
        }
        
        # Write updated state
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "message": f"Updated runtime_state.json with {owner}/{repo_name}",
            "state_file": str(state_file)
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": f"Failed to update runtime_state.json: {str(e)}"
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
    """Run batch data processing"""
    try:
        # Import the batch_process function from the main module
        import sys
        from pathlib import Path
        
        # Add the main directory to path
        main_dir = Path(__file__).resolve().parent.parent.parent / "main" / "DataProcessing"
        if str(main_dir) not in sys.path:
            sys.path.insert(0, str(main_dir.parent.parent))
        
        from main.DataProcessing.process_data import batch_process
        
        # Call batch_process directly
        batch_process()
        
        # Check if output files were created
        output_dir = Path("../../data/DataProcessing")
        processed_files = list(output_dir.glob("*_git_chunks.json")) + list(output_dir.glob("*_gmail_chunks.json"))
        
        return {
            "success": True,
            "processed_files": [str(f.name) for f in processed_files],
            "message": f"Successfully processed {len(processed_files)} files"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def run_embedding_generation() -> Dict[str, Any]:
    """Run batch embedding generation"""
    try:
        from main.GenerateEmbedding.generate_embedding import batch_generate
        
        # Create args object for batch_generate
        class Args:
            output_dir = "../../data/Embeddings/"
            provider = None
            model = None
            batch_size = 32
            cache_dir = "../../data/Embeddings/embeddings_cache"
            batch = True
        
        args = Args()
        batch_generate(args)
        
        # Check if embeddings were created
        embeddings_dir = Path("../../data/Embeddings")
        embedding_dirs = [d for d in embeddings_dir.iterdir() if d.is_dir() and d.name != "embeddings_cache"]
        
        return {
            "success": True,
            "embedding_types": [d.name for d in embedding_dirs],
            "message": f"Successfully generated embeddings for {len(embedding_dirs)} types"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def run_vectordb_build() -> Dict[str, Any]:
    """Run vector database building"""
    try:
        from core.VectorDB.build_indices import main as build_indices_main
        from .chatbot_api import get_runtime_state_file_path, get_database_path_for_repo
        
        # Get current repo from runtime state
        state_file = get_runtime_state_file_path()
        if not state_file.exists():
            return {"success": False, "error": "runtime_state.json not found"}
        
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        curr_repo = state.get("curr_repo", {})
        owner = curr_repo.get("owner")
        repo_name = curr_repo.get("name")
        
        if not owner or not repo_name:
            return {"success": False, "error": "curr_repo.owner or curr_repo.name missing in runtime_state.json"}
        
        # Call build_indices main function
        build_indices_main()
        
        # Check if indices were created using new structure
        repo_root = Path(__file__).resolve().parent.parent.parent
        possible_vectordb_roots = [
            repo_root / "data" / "VectorDB" / owner / repo_name,
            Path("../../data/VectorDB") / owner / repo_name,
            Path("data/VectorDB") / owner / repo_name,
            Path("backend/data/VectorDB") / owner / repo_name,
        ]
        
        vectordb_root = None
        for path in possible_vectordb_roots:
            if path.exists():
                vectordb_root = path
                break
        
        if not vectordb_root:
            return {"success": False, "error": f"VectorDB directory not found for {owner}/{repo_name}"}
        
        indices = [d.name for d in vectordb_root.iterdir() if d.is_dir() and (d / "faiss.index").exists()]
        
        return {
            "success": True,
            "indices": indices,
            "message": f"Successfully built {len(indices)} vector indices for {owner}/{repo_name}",
            "repo": f"{owner}/{repo_name}"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def run_onboarding(generators_to_run: list = None) -> Dict[str, Any]:
    """Run onboarding data generation"""
    try:
        import sys
        from pathlib import Path
        from .chatbot_api import get_runtime_state_file_path, get_database_path_for_repo
        
        # Add the main directory to path
        repo_root = Path(__file__).resolve().parent.parent.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        
        from main.Onboarding.generate_all_onboarding import generate_all_onboarding_data
        
        # Get current repo from runtime state
        state_file = get_runtime_state_file_path()
        if not state_file.exists():
            return {"success": False, "error": "runtime_state.json not found"}
        
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        curr_repo = state.get("curr_repo", {})
        owner = curr_repo.get("owner")
        repo_name = curr_repo.get("name")
        
        if not owner or not repo_name:
            return {"success": False, "error": "curr_repo.owner or curr_repo.name missing in runtime_state.json"}
        
        # Find vector database path using new repo-based structure
        vectordb_path = get_database_path_for_repo(owner, repo_name)
        
        if not vectordb_path:
            return {"success": False, "error": f"Vector database not found for {owner}/{repo_name}. Please run data pipeline first."}
        
        # Run onboarding generation
        results = generate_all_onboarding_data(
            github_db_path=vectordb_path,
            gmail_db_path=None,
            provider='openai',
            model=None,
            generators_to_run=generators_to_run  # Use selected generators
        )
        
        # Check results
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
    """Run offboarding data generation"""
    try:
        import sys
        from pathlib import Path
        
        # Add the main directory to path
        repo_root = Path(__file__).resolve().parent.parent.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        
        # Get the offboarding script path
        offboarding_script = repo_root / "main" / "Offboarding" / "generateOffboardingData.py"
        
        if not offboarding_script.exists():
            return {"success": False, "error": f"Offboarding script not found: {offboarding_script}"}
        
        # Run the offboarding script with better error capture
        # Set UTF-8 encoding for Windows compatibility (handles emoji characters)
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUTF8'] = '1'
        
        # Build command with selected steps if provided
        cmd = [sys.executable, str(offboarding_script)]
        if steps_to_run:
            cmd.extend(['--steps'] + steps_to_run)
        if employee_name:
            cmd.extend(['--employee', employee_name])
        
        result = subprocess.run(
            cmd,
            cwd=str(offboarding_script.parent),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',  # Replace problematic characters instead of failing
            timeout=3600,  # 1 hour timeout
            env=env
        )
        
        # Get output for debugging
        stdout_output = result.stdout if result.stdout else ""
        stderr_output = result.stderr if result.stderr else ""
        
        if result.returncode == 0:
            # Check if output files were created
            output_dir = repo_root / "data" / "Offboarding"
            
            # Map step IDs to their expected output files
            STEP_TO_OUTPUT_FILE = {
                "extract_users": "1employees_with_ids.json",
                "extract_files": "2employee_changed_files.json",
                "add_criticality": "3employee_prs_with_criticality.json",
                "add_metadata": "4employee_tasks_with_metadata_finalCallData.json",
                "generate_handovers": "5employee_handovers.json",
                "generate_documents": "6employee_documents.json"
            }
            
            # Determine which files to check based on selected steps
            if steps_to_run:
                expected_files = [STEP_TO_OUTPUT_FILE[step] for step in steps_to_run if step in STEP_TO_OUTPUT_FILE]
            else:
                # If no steps specified, check all files (backward compatibility)
                expected_files = list(STEP_TO_OUTPUT_FILE.values())
            
            created_files = []
            for filename in expected_files:
                if (output_dir / filename).exists():
                    created_files.append(filename)
            
            # Build success message
            if steps_to_run:
                message = f"Successfully generated offboarding data ({len(created_files)}/{len(expected_files)} files) for {len(steps_to_run)} selected step(s)"
            else:
                message = f"Successfully generated offboarding data ({len(created_files)}/{len(expected_files)} files)"
            
            return {
                "success": True,
                "message": message,
                "output_files": created_files,
                "output_dir": str(output_dir),
                "steps_run": steps_to_run if steps_to_run else "all",
                "expected_steps": len(expected_files)
            }
        else:
            # Return detailed error information
            error_msg = f"Offboarding script failed with exit code {result.returncode}"
            if stderr_output:
                # Get last few lines of stderr for context
                stderr_lines = stderr_output.strip().split('\n')
                last_error = '\n'.join(stderr_lines[-10:])  # Last 10 lines
                error_msg += f"\n\nError output:\n{last_error}"
            elif stdout_output:
                # Sometimes errors go to stdout
                stdout_lines = stdout_output.strip().split('\n')
                last_output = '\n'.join(stdout_lines[-10:])  # Last 10 lines
                error_msg += f"\n\nLast output:\n{last_output}"
            
            return {
                "success": False,
                "error": error_msg,
                "exit_code": result.returncode,
                "stderr_preview": stderr_output[:1000] if stderr_output else None,
                "stdout_preview": stdout_output[:1000] if stdout_output else None
            }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Offboarding process timed out after 1 hour"}
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return {
            "success": False,
            "error": f"Exception while running offboarding: {str(e)}",
            "traceback": error_trace
        }


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
async def admin_offboarding(request: OffboardingRequest):
    """Run offboarding data generation"""
    try:
        if not request:
            raise HTTPException(status_code=400, detail="Request body is required")
        
        steps = request.steps
        employee_name = request.employee_name
        
        if not employee_name or not employee_name.strip():
            raise HTTPException(
                status_code=400,
                detail="Employee name is required and cannot be empty"
            )
        
        # Verify employee exists
        verification = verify_employee_exists(employee_name.strip())
        if not verification.get("exists"):
            raise HTTPException(
                status_code=404,
                detail=verification.get("error", f"Employee '{employee_name}' not found")
            )
        
        result = run_offboarding(steps, employee_name.strip())
        if result["success"]:
            return SetupResponse(
                status="success",
                message=result["message"],
                step="offboarding",
                details=result
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Offboarding generation failed"))
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

