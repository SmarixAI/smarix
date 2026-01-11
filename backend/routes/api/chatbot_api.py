"""
FastAPI Backend for RAG Chatbot v2.1
Exposes REST API endpoints for the chat interface
Supports both GitHub and Gmail vector databases
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import sys
from pathlib import Path
import os
from dotenv import load_dotenv
import asyncio
import json
from datetime import datetime
import difflib
from openai import OpenAI
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, Future

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

try:
    from core.ChatBot.chatbot import RAGChatbot
except Exception:
    try:
        from core.ChatBot.chatbot import RAGChatbot
    except Exception as e:
        raise ImportError(
            "Could not import RAGChatbot. Tried 'ChatBot.core.chatbot' and 'core.chatbot'. "
            "Make sure this project is on PYTHONPATH and package markers (__init__.py) exist."
        ) from e

# Global chatbot state - must be module-level variables
chatbot_instance = None
chatbot_config = {}
available_providers = {}

# Global state for pipeline cancellation
pipeline_cancelled = threading.Event()
current_pipeline_task: Optional[Future] = None

REQUIRED_ENV_VARS = {
    "openai": "OPENAI_API_KEY",
}


def check_api_keys():
    """Check which API keys are available"""
    available = {}
    for provider, env_var in REQUIRED_ENV_VARS.items():
        key = os.getenv(env_var)
        available[provider] = bool(key)
        if key:
            masked = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "***"
            print(f"{env_var}: {masked}")
        else:
            print(f"{env_var}: Not found")

    return available


def find_vector_databases():
    """Find multi-index vector database using repo-based structure"""
    import json
    
    # Try to find runtime_state.json to get current repo
    possible_state_files = [
        Path("../../data/Admin/state/runtime_state.json"),
        Path("data/Admin/state/runtime_state.json"),
        Path("backend/data/Admin/state/runtime_state.json"),
    ]
    
    state_file = None
    for sf in possible_state_files:
        if sf.exists():
            state_file = sf
            break
    
    github_db = None
    
    if state_file:
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # First try curr_repo, then fallback to user_default_repo
            repo_config = state.get("curr_repo", {})
            if not repo_config or not repo_config.get("owner") or not repo_config.get("name"):
                # Use user_default_repo if curr_repo is not available
                repo_config = state.get("user_default_repo", {})
            
            owner = repo_config.get("owner")
            repo_name = repo_config.get("name")
            
            if owner and repo_name:
                # New structure: data/VectorDB/{owner}/{repo_name}/
                possible_db_dirs = [
                    Path("../../data/VectorDB") / owner / repo_name,
                    Path("data/VectorDB") / owner / repo_name,
                    Path("backend/data/VectorDB") / owner / repo_name,
                    Path(__file__).resolve().parent.parent.parent / "data" / "VectorDB" / owner / repo_name,
                ]
                
                for db_dir in possible_db_dirs:
                    if db_dir.exists():
                        # Check if it has the expected structure (type subdirectories)
                        has_structure = any(
                            (db_dir / idx_type / "faiss.index").exists()
                            for idx_type in [
                                "code",
                                "commit",
                                "pr",
                                "issue",
                                "documentation",
                                "all",
                            ]
                        )
                        if has_structure:
                            github_db = str(db_dir)
                            print(f"Found Multi-Index DB: {db_dir} (repo: {owner}/{repo_name})")
                            break
        except Exception as e:
            print(f"⚠ Warning: Could not read runtime_state.json: {e}")

    return github_db, None


async def startup():
    """Initialize chatbot on startup"""
    global chatbot_instance, chatbot_config, available_providers

    print("\n" + "=" * 70)
    print("SUPER EMPLOYEE RAG CHATBOT API v2.1")
    print("=" * 70 + "\n")

    print("Checking API Keys...")
    available_providers = check_api_keys()

    default_provider = None
    if available_providers.get("openai"):
        default_provider = "openai"
    elif available_providers.get("anthropic"):
        default_provider = "anthropic"

    if not default_provider:
        print("\nWARNING: No API keys found!")
        print("   Please set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env file")
        chatbot_config = {"status": "waiting", "error": "No API keys configured"}
        return

    print(f"\nUsing provider: {default_provider}\n")

    print("Looking for vector databases...")
    github_db_path, gmail_db_path = find_vector_databases()

    if not github_db_path:
        print("No multi-index vector database found.")
        print("    Required: data/VectorDB/{owner}/{repo_name} directory with index files")
        print("    Run: python backend/core/VectorDB/build_indices.py")
        chatbot_config = {
            "status": "error",
            "error": "Multi-index database not found. Please build it first using build_indices.py",
        }
        return

    if not gmail_db_path:
        print("No Gmail database found (optional).")
        print("    Run: python build_gmail_vector_db.py\n")

    try:
        print("Initializing RAG Chatbot...")
        print("   Using Multi-Index mode (routing: llm)")

        chatbot_instance = RAGChatbot(
            vector_db_path=github_db_path,
            gmail_db_path=gmail_db_path,
            provider=default_provider,
            temperature=0.7,
            top_k=5,
            use_hybrid_retrieval=True,
            verbose=False,
            routing_method="llm",
        )

        databases = []
        total_vectors = 0

        if chatbot_instance.multi_index_store:
            stats = chatbot_instance.multi_index_store.get_statistics()
            total_vectors = stats.get("total_vectors", 0)
            databases.append(
                f"Multi-Index ({total_vectors} vectors across {stats.get('total_indices', 0)} indices)"
            )
            for idx_type, idx_stats in stats.get("by_index", {}).items():
                if "total_vectors" in idx_stats:
                    databases.append(
                        f"  - {idx_type}: {idx_stats['total_vectors']} vectors"
                    )

        features = [
            "GitHub + Gmail Integration",
            "Hybrid Retrieval",
            "Flow Diagrams",
            "Keyword Issue/PR Filtering",
            "Related Knowledge",
            "Email Context Support",
            "Multi-Index with Query Routing",
        ]

        chatbot_config = {
            "github_db_path": github_db_path,
            "gmail_db_path": gmail_db_path,
            "provider": default_provider,
            "model": chatbot_instance.model,
            "total_vectors": total_vectors,
            "databases": databases,
            "status": "ready",
            "available_providers": available_providers,
            "features": features,
        }

        print("\nChatbot Ready!")
        print(f"Databases: {', '.join(databases)}")
        print(f"Model: {chatbot_instance.model}")
        print(f"Total Vectors: {total_vectors}")
        print("Retrieval: Hybrid")
        if gmail_db_path:
            print("Gmail: Enabled")
        print()

    except Exception as e:
        print(f"\nFailed to initialize chatbot: {e}\n")
        import traceback

        traceback.print_exc()
        chatbot_config = {"status": "error", "error": str(e)}
        # Keep chatbot_instance as None - it will be initialized lazily on first request if possible
        chatbot_instance = None


async def shutdown():
    """Cleanup on shutdown"""
    print("\nShutting down chatbot API...\n")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup()
    yield
    await shutdown()


app = FastAPI(
    title="Super Employee RAG Chatbot API v2.1",
    description="AI-powered codebase and email intelligence API with GitHub + Gmail integration",
    version="2.1.0",
    lifespan=lifespan,
)

from core.Auth import routes as auth_routes

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://44.207.49.138:3000",
        "https://smarix.net",
        "https://www.smarix.net"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers from modular route files
app.include_router(auth_routes.router)

# Helper function to handle imports when running as script vs module
def _import_route_module(module_name: str):
    """Import route module handling both relative (module) and absolute (script) imports"""
    # Check if we're running as a script (__name__ == "__main__") or as a module
    import sys
    from pathlib import Path
    
    # Determine if we should use relative or absolute imports
    # When __name__ is "__main__", we're running as a script
    current_module = sys.modules.get(__name__)
    is_main_module = __name__ == "__main__" or (current_module and current_module.__package__ is None)
    
    if is_main_module:
        # Running as script - use absolute import
        current_dir = Path(__file__).parent
        backend_dir = current_dir.parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        return __import__(f"routes.api.{module_name}", fromlist=[module_name])
    else:
        # Running as module - use relative import
        try:
            from importlib import import_module
            return import_module(f".{module_name}", package=__package__)
        except (ImportError, ValueError, AttributeError):
            # Fallback to absolute import if relative fails
            current_dir = Path(__file__).parent
            backend_dir = current_dir.parent.parent
            if str(backend_dir) not in sys.path:
                sys.path.insert(0, str(backend_dir))
            return __import__(f"routes.api.{module_name}", fromlist=[module_name])

# Import and include chat routes
chat_routes = _import_route_module("chat_routes")
app.include_router(chat_routes.router)

# Import and include admin routes
admin_routes = _import_route_module("admin_routes")
app.include_router(admin_routes.router)

# ==================== SHARED HELPER FUNCTIONS ====================
# These are used by both chat and admin routes

# Note: All route handlers have been moved to chat_routes.py and admin_routes.py
# Only shared helper functions remain below

def get_users_file_path() -> Path:
    """Get the path to the users credentials JSON file"""
    repo_root = Path(__file__).resolve().parent.parent.parent
    possible_paths = [
        repo_root / "data" / "Admin" / "users.json",
        Path("data/Admin/users.json"),
        Path("../../data/Admin/users.json"),
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    # Return default path if none exist
    return repo_root / "data" / "Admin" / "users.json"


def get_runtime_state_file_path() -> Path:
    """Get the path to the runtime state JSON file"""
    repo_root = Path(__file__).resolve().parent.parent.parent
    possible_paths = [
        repo_root / "data" / "Admin" / "state" / "runtime_state.json",
        Path("data/Admin/state/runtime_state.json"),
        Path("../../data/Admin/state/runtime_state.json"),
        Path("backend/data/Admin/state/runtime_state.json"),
        Path(__file__).resolve().parent.parent.parent / "data" / "Admin" / "state" / "runtime_state.json",
    ]
    
    for path in possible_paths:
        abs_path = path.resolve() if path.is_absolute() or str(path).startswith("..") else path
        if abs_path.exists():
            return abs_path
    
    # Return default path if none exist
    return repo_root / "data" / "Admin" / "state" / "runtime_state.json"


def get_user_repo(username: Optional[str] = None) -> Optional[Dict[str, str]]:
    """
    Get the repository (owner/name) for a user.
    Priority order:
    1. User's active_repos from users.json (if username provided)
    2. curr_repo from runtime_state.json (for new setups)
    3. user_default_repo from runtime_state.json (final fallback)
    Returns dict with 'owner' and 'name' keys, or None if not found.
    """
    # Priority 1: Try to get from user's active_repos (if username provided)
    if username:
        try:
            users_file = get_users_file_path()
            if users_file.exists():
                with open(users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    users = data.get("users", [])
                    user = next((u for u in users if u.get("username") == username), None)
                    
                    if user:
                        active_repos = user.get("active_repos", [])
                        if active_repos and len(active_repos) > 0:
                            # Use the first active repo
                            repo_str = active_repos[0]
                            # Parse "owner/repo" format
                            if "/" in repo_str:
                                parts = repo_str.split("/", 1)
                                if len(parts) == 2 and parts[0].strip() and parts[1].strip():
                                    owner, repo_name = parts[0].strip(), parts[1].strip()
                                    return {"owner": owner, "name": repo_name}
                            else:
                                print(f"⚠ Warning: Invalid repo format in active_repos for user {username}: '{repo_str}' (expected 'owner/repo')")
        except Exception as e:
            print(f"⚠ Warning: Could not read user's active_repos: {e}")
    
    # Priority 2 & 3: Fallback to runtime_state.json (curr_repo first, then user_default_repo)
    try:
        state_file = get_runtime_state_file_path()
        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                
                # Priority 2: Try curr_repo (for new setups)
                curr_repo = state.get("curr_repo", {})
                owner = curr_repo.get("owner")
                repo_name = curr_repo.get("name")
                
                if owner and repo_name:
                    return {"owner": owner, "name": repo_name}
                
                # Priority 3: Fallback to user_default_repo (final fallback)
                user_default_repo = state.get("user_default_repo", {})
                owner = user_default_repo.get("owner")
                repo_name = user_default_repo.get("name")
                
                if owner and repo_name:
                    return {"owner": owner, "name": repo_name}
    except Exception as e:
        print(f"⚠ Warning: Could not read runtime_state.json: {e}")
    
    return None


def get_database_path_for_repo(owner: str, repo_name: str) -> Optional[str]:
    """
    Get the database path for a given owner/repo.
    Returns the path to the vector database directory, or None if not found.
    """
    possible_db_dirs = [
        Path("../../data/VectorDB") / owner / repo_name,
        Path("data/VectorDB") / owner / repo_name,
        Path("backend/data/VectorDB") / owner / repo_name,
        Path(__file__).resolve().parent.parent.parent / "data" / "VectorDB" / owner / repo_name,
    ]
    
    for db_dir in possible_db_dirs:
        if db_dir.exists():
            # Check if it has the expected structure (type subdirectories)
            has_structure = any(
                (db_dir / idx_type / "faiss.index").exists()
                for idx_type in [
                    "code",
                    "commit",
                    "pr",
                    "issue",
                    "documentation",
                    "all",
                ]
            )
            if has_structure:
                return str(db_dir)
    
    return None


def ensure_chatbot_for_repo(owner: str, repo_name: str) -> bool:
    """
    Ensure the chatbot is initialized with the correct repository database.
    Returns True if successful, False otherwise.
    """
    global chatbot_instance, chatbot_config, available_providers
    
    # Get the database path for this repo
    db_path = get_database_path_for_repo(owner, repo_name)
    
    if not db_path:
        print(f"⚠ Warning: Database not found for repo {owner}/{repo_name}")
        return False
    
    # Check if chatbot is already using this database
    current_db_path = chatbot_config.get("github_db_path")
    if current_db_path == db_path:
        # Already using the correct database
        return True
    
    # Need to reinitialize with the new database
    try:
        print(f"Switching chatbot to repo: {owner}/{repo_name}")
        
        # Get gmail_db_path from current config
        gmail_db_path = chatbot_config.get("gmail_db_path")
        
        # Get provider from current config or default
        provider = chatbot_config.get("provider", "openai")
        if not available_providers.get(provider):
            # Try to find an available provider
            if available_providers.get("openai"):
                provider = "openai"
            elif available_providers.get("anthropic"):
                provider = "anthropic"
            else:
                print("⚠ Warning: No API keys available")
                return False
        
        # Reinitialize chatbot
        chatbot_instance = RAGChatbot(
            vector_db_path=db_path,
            gmail_db_path=gmail_db_path,
            provider=provider,
            temperature=0.7,
            top_k=5,
            use_hybrid_retrieval=True,
            verbose=False,
            routing_method="llm",
        )
        
        # Update config
        databases = []
        total_vectors = 0
        
        if chatbot_instance.multi_index_store:
            stats = chatbot_instance.multi_index_store.get_statistics()
            total_vectors = stats.get("total_vectors", 0)
            databases.append(
                f"Multi-Index ({total_vectors} vectors across {stats.get('total_indices', 0)} indices)"
            )
            for idx_type, idx_stats in stats.get("by_index", {}).items():
                if "total_vectors" in idx_stats:
                    databases.append(
                        f"  - {idx_type}: {idx_stats['total_vectors']} vectors"
                    )
        
        chatbot_config = {
            "github_db_path": db_path,
            "gmail_db_path": gmail_db_path,
            "provider": provider,
            "model": chatbot_instance.model,
            "total_vectors": total_vectors,
            "databases": databases,
            "status": "ready",
            "available_providers": available_providers,
        }
        
        print(f"✅ Chatbot switched to {owner}/{repo_name}")
        return True
        
    except Exception as e:
        print(f"⚠ Error switching chatbot to {owner}/{repo_name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def start_server():
    """Start the FastAPI server"""
    import uvicorn

    print("Starting FastAPI server")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    start_server()
