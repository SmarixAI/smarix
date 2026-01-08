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
app.include_router(auth_routes.router)

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


class ChatRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    role: Optional[str] = None  # "onboarding", "offboarding", "general" (default)
    username: Optional[str] = None  # Username to determine which repo to use


class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    chunks_retrieved: int
    conversation_id: str
    related_knowledge: Optional[Dict[str, List[Dict[str, Any]]]] = None
    emails: Optional[List[Dict[str, Any]]] = None
    has_diagram: Optional[bool] = False
    flow_data: Optional[Dict[str, Any]] = None
    query_type: Optional[str] = None
    context_quality: Optional[float] = None


class InitRequest(BaseModel):
    github_db_path: Optional[str] = None
    gmail_db_path: Optional[str] = None
    provider: str = "openai"
    model: Optional[str] = None
    temperature: float = 0.7
    top_k: int = 5
    use_hybrid_retrieval: bool = True
    verbose: bool = False
    routing_method: str = "llm"


class EvaluationRequest(BaseModel):
    submission_id: str
    pr_number: int


class EvaluationResponse(BaseModel):
    submission_id: str
    pr_number: int
    overall_score: float
    correctness_score: float
    code_quality_score: float
    completeness_score: float
    evaluation_summary: str
    file_evaluations: List[Dict[str, Any]]
    suggestions: List[str]
    strengths: List[str]
    areas_for_improvement: List[str]
    evaluated_at: str


class SetupRequest(BaseModel):
    organization: str
    repo_name: str


class SetupResponse(BaseModel):
    status: str
    message: str
    step: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


def calculate_similarity(submitted_code: str, solution_code: str) -> float:
    """Calculate similarity between submitted and solution code"""
    sequence_matcher = difflib.SequenceMatcher(None, submitted_code, solution_code)
    return sequence_matcher.ratio()


def load_json_file(file_path: str) -> dict:
    """Load JSON file with error handling"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500, detail=f"Invalid JSON in file: {file_path}"
        )


@app.get("/")
async def root():
    """Health check and status"""
    return {
        "status": "online",
        "version": "2.1.0",
        "chatbot_ready": chatbot_instance is not None,
        "config": chatbot_config,
        "available_providers": available_providers,
        "endpoints": {
            "chat": "POST /chat",
            "init": "POST /init",
            "stats": "GET /stats",
            "clear": "POST /clear-history",
            "health": "GET /health",
            "config": "GET /config",
            "evaluate": "POST /evaluate-submission",
            "docs": "GET /docs",
        },
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    health = {
        "api": "healthy",
        "version": "2.1.0",
        "chatbot": "ready" if chatbot_instance else "not initialized",
        "api_keys": available_providers,
        "github_db": (
            "configured" if chatbot_config.get("github_db_path") else "not configured"
        ),
        "gmail_db": (
            "configured" if chatbot_config.get("gmail_db_path") else "not configured"
        ),
    }

    if chatbot_instance:
        try:
            stats = chatbot_instance.get_stats()

            health["github_chunks"] = stats.get("total_chunks", 0)
            health["conversation_length"] = stats.get("conversation_length", 0)

            if "gmail_indexed" in stats:
                health["gmail_emails"] = stats.get("gmail_indexed", 0)

            health["features"] = stats.get("features", [])

            # ✅ ADD SEMANTIC CACHE STATUS
            if chatbot_instance.query_rewriter and chatbot_instance.query_rewriter.semantic_cache:
                cache_stats = chatbot_instance.query_rewriter.semantic_cache.get_stats()
                health["semantic_cache"] = {
                    "enabled": True,
                    "cache_size": cache_stats.get("cache_size", 0),
                    "hit_rate": cache_stats.get("overall_hit_rate", 0),
                    "total_queries": cache_stats.get("total_queries", 0),
                    "cost_saved": cache_stats.get("cost_saved_usd", 0)
                }
            else:
                health["semantic_cache"] = {
                    "enabled": False,
                    "reason": "Redis or embeddings not configured"
                }

        except Exception as e:
            health["error"] = str(e)

    return health


@app.post("/init")
async def initialize_chatbot(config: InitRequest):
    """Initialize or reinitialize the chatbot"""
    global chatbot_instance, chatbot_config

    if config.provider == "openai" and not available_providers.get("openai"):
        raise HTTPException(status_code=400, detail="OpenAI API key not configured")

    if config.provider == "anthropic" and not available_providers.get("anthropic"):
        raise HTTPException(status_code=400, detail="Anthropic API key not configured")

    github_db_path = config.github_db_path
    gmail_db_path = config.gmail_db_path

    if not github_db_path and not gmail_db_path:
        github_db_path, gmail_db_path = find_vector_databases()

    if not github_db_path and not gmail_db_path:
        raise HTTPException(status_code=404, detail="No vector databases found")

    if github_db_path and not Path(github_db_path).exists():
        raise HTTPException(
            status_code=404, detail=f"GitHub DB not found: {github_db_path}"
        )

    if gmail_db_path and not Path(gmail_db_path).exists():
        raise HTTPException(
            status_code=404, detail=f"Gmail DB not found: {gmail_db_path}"
        )

    try:
        print(f"Reinitializing chatbot with {config.provider}...")

        chatbot_instance = RAGChatbot(
            vector_db_path=github_db_path,
            gmail_db_path=gmail_db_path,
            provider=config.provider,
            model=config.model,
            temperature=config.temperature,
            top_k=config.top_k,
            use_hybrid_retrieval=config.use_hybrid_retrieval,
            verbose=config.verbose,
            routing_method=getattr(config, "routing_method", "keyword"),
        )

        databases = []
        total_vectors = 0

        if github_db_path and chatbot_instance.db:
            github_vectors = chatbot_instance.db.index.ntotal
            databases.append(f"GitHub ({github_vectors} vectors)")
            total_vectors += github_vectors

        if gmail_db_path and chatbot_instance.gmail_db:
            gmail_vectors = chatbot_instance.gmail_db.index.ntotal
            databases.append(f"Gmail ({gmail_vectors} emails)")
            total_vectors += gmail_vectors

        chatbot_config = {
            "github_db_path": github_db_path,
            "gmail_db_path": gmail_db_path,
            "provider": config.provider,
            "model": config.model or chatbot_instance.model,
            "total_vectors": total_vectors,
            "databases": databases,
            "status": "ready",
        }

        print("Chatbot reinitialized\n")

        return {
            "status": "success",
            "message": "Chatbot initialized successfully",
            "config": chatbot_config,
        }

    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint - retrieves from GitHub first, then supplements with Gmail if needed"""
    if chatbot_instance is None:
        # Provide more detailed error message
        error_detail = "Chatbot not initialized"
        if chatbot_config:
            config_status = chatbot_config.get("status", "unknown")
            config_error = chatbot_config.get("error")
            if config_error:
                error_detail = f"Chatbot not initialized: {config_error}"
            elif config_status == "waiting":
                error_detail = "Chatbot not initialized: No API keys configured. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env file"
            elif config_status == "error":
                error_detail = f"Chatbot not initialized: {config_error or 'Unknown error during initialization'}"
            else:
                error_detail = f"Chatbot not initialized: Status = {config_status}"
        raise HTTPException(status_code=503, detail=error_detail)

    try:
        # Determine which repo to use based on username
        user_repo = get_user_repo(request.username)
        
        if user_repo:
            owner = user_repo.get("owner")
            repo_name = user_repo.get("name")
            
            if owner and repo_name:
                print(f"Using repo for user {request.username or 'anonymous'}: {owner}/{repo_name}")
                # Ensure chatbot is using the correct repo database
                if not ensure_chatbot_for_repo(owner, repo_name):
                    print(f"⚠ Warning: Could not switch to repo {owner}/{repo_name}, using current database")
        else:
            if request.username:
                print(f"⚠ Warning: No repo found for user {request.username}, using default database")
            else:
                print("Using default database (no username provided)")
        
        print(f"Query: {request.query[:100]}...")
        print(f"Session: {request.session_id or 'new'}")
        print(f"Role: {request.role or 'general'}")
        if request.username:
            print(f"User: {request.username}")

        result = chatbot_instance.chat(
            request.query, 
            request.filters,
            session_id=request.session_id,
            role=request.role or "general"
        )

        enriched_sources = []
        for source in result["sources"]:
            enriched_source = {
                **source,
                "file": source.get("file", "unknown"),
                "type": source.get("type", "unknown"),
                "score": source.get("score", 0.0),
                "context_role": source.get("context_role", "primary"),
            }
            enriched_sources.append(enriched_source)

        email_count = len(result.get("emails", []))
        print(f"Response: {result['chunks_retrieved']} code chunks", end="")
        if email_count > 0:
            print(f" + {email_count} emails")
        else:
            print()
        print()

        session_id = chatbot_instance.get_session_id()

        return ChatResponse(
            answer=result["answer"],
            sources=enriched_sources,
            chunks_retrieved=result["chunks_retrieved"],
            conversation_id=session_id,
            related_knowledge=result.get("related_knowledge"),
            emails=result.get("emails", []),
            has_diagram=result.get("has_diagram", False),
            flow_data=result.get("flow_data"),
            query_type=result.get("query_type"),
            context_quality=result.get("context_quality"),
        )

    except Exception as e:
        print(f"Error: {e}\n")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/new-session")
async def new_session():
    """Generate a fresh session ID and persist it immediately."""
    if chatbot_instance is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    new_session_id = chatbot_instance.start_new_session()
    print(f"🔄 NEW SESSION CREATED AND STORED: {new_session_id}")
    return {"session_id": new_session_id, "message": "New session created"}


@app.post("/clear-history")
async def clear_history(request: ChatRequest):
    """Clear conversation history for specific session"""
    if chatbot_instance is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    session_id = chatbot_instance.set_session(request.session_id)
    chatbot_instance.conversation_store.clear_session(session_id)
    print(f"History cleared for session {session_id[:8]}...\n")

    return {"status": "success", "message": "Session history cleared"}


@app.get("/sessions")
async def get_sessions(limit: int = 50):
    """List recent sessions with metadata"""
    if chatbot_instance is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    try:
        sessions = []
        all_sessions = chatbot_instance.conversation_store.get_all_sessions(limit=limit)

        for session_data in all_sessions:
            stats = chatbot_instance.conversation_store.get_session_stats(session_data['session_id'])
            sessions.append({
                'session_id': session_data['session_id'],
                'title': session_data.get('title', 'New Chat'),
                'message_count': stats.get('message_count', 0),
                'last_message': stats.get('last_message', ''),
                'first_message': stats.get('first_message', ''),
                'total_tokens': stats.get('total_tokens', 0)
            })

        return {'sessions': sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/load-session/{session_id}")
async def load_session(session_id: str):
    """Load messages for a specific session"""
    if chatbot_instance is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    try:
        messages = chatbot_instance.conversation_store.get_full_history(session_id)
        chatbot_instance.set_session(session_id)

        return {
            'session_id': session_id,
            'messages': messages,
            'stats': chatbot_instance.conversation_store.get_session_stats(session_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/delete-session/{session_id}")
async def delete_session(session_id: str):
    if chatbot_instance is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    try:
        chatbot_instance.conversation_store.delete_session(session_id)
        return {"status": "success", "message": "Session deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """Get chatbot statistics including GitHub and Gmail stats"""
    if chatbot_instance is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    try:
        stats = chatbot_instance.get_stats()

        enhanced_stats = {
            "status": "success",
            "stats": stats,
            "databases": {
                "github": {
                    "enabled": bool(chatbot_instance.db),
                    "vectors": (
                        chatbot_instance.db.index.ntotal if chatbot_instance.db else 0
                    ),
                },
                "gmail": {
                    "enabled": bool(chatbot_instance.gmail_db),
                    "emails": (
                        chatbot_instance.gmail_db.index.ntotal
                        if chatbot_instance.gmail_db
                        else 0
                    ),
                },
            },
        }

        return enhanced_stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/semantic-cache-stats")
async def get_semantic_cache_stats():
    """Get universal semantic cache statistics with confidence breakdown"""
    if chatbot_instance is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    try:
        # Check if semantic cache is enabled
        if not (chatbot_instance.query_rewriter and
                chatbot_instance.query_rewriter.semantic_cache):
            return {
                "status": "disabled",
                "message": "Semantic cache not enabled. Ensure Redis and embeddings are configured."
            }

        # Get comprehensive stats
        cache_stats = chatbot_instance.query_rewriter.semantic_cache.get_stats()

        return {
            "status": "success",
            "cache_stats": cache_stats,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/invalidate-cache/{session_id}")
async def invalidate_semantic_cache(session_id: str):
    """Invalidate semantic cache for a specific session"""
    if chatbot_instance is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    try:
        if not (chatbot_instance.query_rewriter and
                chatbot_instance.query_rewriter.semantic_cache):
            raise HTTPException(
                status_code=400,
                detail="Semantic cache not enabled"
            )

        # Invalidate cache
        count = chatbot_instance.query_rewriter.semantic_cache.invalidate_session(session_id)

        return {
            "status": "success",
            "message": f"Invalidated {count} cache entries for session",
            "session_id": session_id,
            "entries_cleared": count
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear-all-cache")
async def clear_all_semantic_cache():
    """Clear entire semantic cache (admin operation)"""
    if chatbot_instance is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    try:
        if not (chatbot_instance.query_rewriter and
                chatbot_instance.query_rewriter.semantic_cache):
            raise HTTPException(
                status_code=400,
                detail="Semantic cache not enabled"
            )

        # Clear in-memory index
        initial_size = len(chatbot_instance.query_rewriter.semantic_cache.cache_index)
        chatbot_instance.query_rewriter.semantic_cache.cache_index.clear()

        # Reset stats
        chatbot_instance.query_rewriter.semantic_cache.stats = {
            'total_queries': 0,
            'exact_matches': 0,
            'very_high_matches': 0,
            'high_matches': 0,
            'medium_matches': 0,
            'low_matches': 0,
            'no_matches': 0,
            'augmentations': 0,
            'context_hints': 0,
            'cost_saved_usd': 0.0,
        }

        return {
            "status": "success",
            "message": "Cleared all semantic cache",
            "entries_cleared": initial_size
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config")
async def get_config():
    """Get current configuration"""
    return {
        "status": "success",
        "config": chatbot_config,
        "available_providers": available_providers,
    }


@app.post("/evaluate-submission", response_model=EvaluationResponse)
async def evaluate_submission(request: EvaluationRequest):
    """
    Professional-grade code evaluation using multi-criteria rubric assessment.
    Inspired by educational grading systems and LLM evaluation frameworks.
    """

    current_dir = Path(__file__).resolve().parent

    # Try to find repo root
    repo_root = None
    test_path = current_dir
    for _ in range(5):
        if (test_path / "backend" / "data" / "Onboarding").exists():
            repo_root = test_path
            break
        test_path = test_path.parent
    
    if repo_root is None:
        repo_root = Path(__file__).resolve().parent.parent.parent
    
    possible_paths = [
        {
            "submitted": repo_root / "data" / "Onboarding" / "onboarding_bugfix_data" / "onboarding_challenge_submitted_code.json",
            "solution": repo_root / "data" / "Onboarding" / "onboarding_bugfix_data" / "onboarding_challenge_solution.json",
        },
        {
            "submitted": current_dir
            / "../../../backend/data/Onboarding/onboarding_bugfix_data/onboarding_challenge_submitted_code.json",
            "solution": current_dir
            / "../../../backend/data/Onboarding/onboarding_bugfix_data/onboarding_challenge_solution.json",
        },
        {
            "submitted": current_dir
            / "../../data/Onboarding/onboarding_bugfix_data/onboarding_challenge_submitted_code.json",
            "solution": current_dir
            / "../../data/Onboarding/onboarding_bugfix_data/onboarding_challenge_solution.json",
        },
        {
            "submitted": Path(
                "backend/data/Onboarding/onboarding_bugfix_data/onboarding_challenge_submitted_code.json"
            ),
            "solution": Path(
                "backend/data/Onboarding/onboarding_bugfix_data/onboarding_challenge_solution.json"
            ),
        },
    ]

    submitted_path = None
    solution_path = None

    for idx, paths in enumerate(possible_paths):
        sub_path = paths["submitted"].resolve()
        sol_path = paths["solution"].resolve()

        if sub_path.exists() and sol_path.exists():
            submitted_path = sub_path
            solution_path = sol_path
            break

    if not submitted_path or not solution_path:
        error_detail = {
            "error": "Could not find submission or solution files",
            "current_directory": str(Path.cwd()),
            "api_location": str(current_dir),
            "expected_files": [
                "backend/data/Onboarding/onboarding_bugfix_data/onboarding_challenge_submitted_code.json",
                "backend/data/Onboarding/onboarding_bugfix_data/onboarding_challenge_solution.json",
            ],
        }
        raise HTTPException(status_code=404, detail=error_detail)

    submitted_data = load_json_file(str(submitted_path))
    solution_data = load_json_file(str(solution_path))

    submission = None
    for sub in submitted_data.get("submissions", []):
        if sub["submission_id"] == request.submission_id:
            submission = sub
            break

    if not submission:
        raise HTTPException(
            status_code=404, detail=f"Submission {request.submission_id} not found"
        )

    solution_pr = None
    for pr in solution_data.get("pull_requests", []):
        if pr["pr_number"] == request.pr_number:
            solution_pr = pr
            break

    if not solution_pr:
        raise HTTPException(
            status_code=404, detail=f"Solution for PR #{request.pr_number} not found"
        )

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    client = OpenAI(api_key=openai_api_key)

    file_evaluations: List[Dict[str, Any]] = []
    total_correctness = 0.0
    total_quality = 0.0
    total_completeness = 0.0
    files_evaluated = 0

    for submitted_file in submission["file_changes"]:
        file_path = submitted_file["file_path"]
        submitted_code = submitted_file["submitted_code"]

        solution_file = None
        for sol_file in solution_pr["file_changes"]:
            if sol_file["file_path"] == file_path:
                solution_file = sol_file
                break

        if not solution_file:
            continue

        solution_code = solution_file["after_code"]
        before_code = solution_file.get("before_code", "")

        # Get PR context for better evaluation
        pr_title = solution_pr.get("title", "")
        pr_description = solution_pr.get("description", "")

        similarity_to_solution = calculate_similarity(submitted_code, solution_code)
        similarity_to_before = calculate_similarity(submitted_code, before_code)

        print(f"\n{'=' * 80}")
        print(f"Evaluating: {file_path}")
        print(f"{'=' * 80}")

        # STEP 1: Deep Code Analysis (like a senior developer would do)
        analysis_prompt = f"""You are a senior software engineer conducting a thorough code review for a bug fix. Analyze this submission with the rigor and depth that a professional code reviewer at a top tech company would use.

            **PR Context:**
            - Title: {pr_title}
            - Description: {pr_description}

            **Original Code (BROKEN - Contains Bug):**
            {before_code}

            **Expected Solution (FIXED - Correct Implementation):**
            {solution_code}

            **Student's Submitted Code:**
            {submitted_code}


            **Your Task - Comprehensive Analysis:**

            Conduct a detailed, multi-faceted analysis covering:

            1. **Functional Correctness Analysis:**
            - Does the submitted code actually fix the bug described in the PR?
            - Are the exact same changes present (or functionally equivalent)?
            - Would this code work correctly in production?
            - Are there any logical errors or missing fixes?

            2. **Implementation Quality:**
            - Is the implementation approach sound and well-reasoned?
            - Are there any code smells or anti-patterns?
            - Is the code maintainable and extensible?

            3. **Completeness Check:**
            - Are ALL necessary changes from the solution present?
            - Are there any partially implemented fixes?
            - Is anything missing that would cause the bug to persist?

            4. **Code Comparison:**
            - Line-by-line comparison: what changed vs what should have changed
            - Are differences cosmetic (formatting) or substantive (logic)?
            - Functional equivalence assessment

            5. **Edge Cases & Robustness:**
            - Does the fix handle edge cases properly?
            - Are there potential runtime errors?

            **Output Requirements:**

            Provide a comprehensive JSON analysis:

            {{
            "bug_actually_fixed": <true/false>,
            "functional_correctness": {{
                "score": <0-100>,
                "reasoning": "<Detailed explanation of why this score>"
            }},
            "implementation_quality": {{
                "score": <0-100>,
                "reasoning": "<Assessment of code quality>"
            }},
            "completeness": {{
                "score": <0-100>,
                "reasoning": "<All changes implemented?>"
            }},
            "changes_analysis": {{
                "required_changes": ["<change 1>", "<change 2>"],
                "implemented_changes": ["<change 1>", "<change 2>"],
                "missing_changes": ["<what's missing>"],
                "incorrect_changes": ["<what's wrong>"]
            }},
            "equivalence_assessment": "<identical/functionally-equivalent/partially-correct/incorrect/no-changes>",
            "critical_issues": ["<List any critical problems>"],
            "minor_issues": ["<List minor issues>"],
            "strengths": ["<What was done well>"],
            "overall_assessment": "<2-3 sentence professional summary>"
            }}

            Be thorough, precise, and honest. This is for learning - accuracy matters more than being nice."""

        try:
            # Get comprehensive analysis
            print("  → Running deep code analysis...")
            analysis_response = client.chat.completions.create(
                model="gpt-4o",  # Use GPT-4o for better analysis
                messages=[
                    {
                        "role": "system",
                        "content": "You are a principal software engineer with 15+ years of experience reviewing code. You provide thorough, accurate, and educational feedback. You understand functional equivalence vs textual similarity. You catch subtle bugs and appreciate elegant solutions.",
                    },
                    {"role": "user", "content": analysis_prompt},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )

            analysis_result = json.loads(analysis_response.choices[0].message.content)

            print(f"  → Bug Fixed: {analysis_result.get('bug_actually_fixed', False)}")
            print(
                f"  → Equivalence: {analysis_result.get('equivalence_assessment', 'unknown')}"
            )
            print(
                f"  → Functional Correctness: {analysis_result['functional_correctness']['score']}/100"
            )

            # STEP 2: Rubric-Based Scoring (like professional grading systems)
            scoring_prompt = f"""You are an experienced computer science educator creating detailed scores for a programming assignment using a professional rubric.

                **Code Analysis Results:**
                {json.dumps(analysis_result, indent=2)}

                **Similarity Metrics:**
                - To Solution: {similarity_to_solution:.1%}
                - To Original (Broken): {similarity_to_before:.1%}

                **Professional Evaluation Rubric:**

                **CORRECTNESS (0-10 points):**
                - 9.5-10: Perfect fix, all bugs resolved, works flawlessly
                - 8.5-9.4: Excellent fix, minor cosmetic differences only
                - 7.0-8.4: Good fix, works correctly with small issues
                - 5.0-6.9: Partial fix, some bugs addressed but not all
                - 3.0-4.9: Attempted fix but critical bugs remain
                - 0-2.9: No meaningful fix, bug persists

                **CODE QUALITY (0-10 points):**
                - 9.5-10: Exemplary code, professional standards
                - 8.5-9.4: High quality, clean and maintainable
                - 7.0-8.4: Good quality, minor improvements possible
                - 5.0-6.9: Acceptable but needs refinement
                - 3.0-4.9: Poor quality, multiple code smells
                - 0-2.9: Very poor quality

                **COMPLETENESS (0-10 points):**
                - 9.5-10: All required changes implemented perfectly
                - 8.5-9.4: All changes present, minor variations
                - 7.0-8.4: Most changes implemented correctly
                - 5.0-6.9: Some changes missing
                - 3.0-4.9: Many changes missing
                - 0-2.9: Critical changes not implemented

                **Your Task:**
                Based on the analysis results and rubric, assign precise scores. Be calibrated - a perfect solution should get 9.5-10, a complete failure should get 0-2.

                Respond in JSON:
                {{
                "correctness_score": <0-10, one decimal>,
                "correctness_justification": "<Why this specific score based on rubric>",
                "quality_score": <0-10, one decimal>,
                "quality_justification": "<Why this specific score based on rubric>",
                "completeness_score": <0-10, one decimal>,
                "completeness_justification": "<Why this specific score based on rubric>",
                "rubric_adherence": "<Explanation of how scores map to rubric criteria>",
                "calibration_check": "<Is this score fair compared to rubric standards?>"
                }}"""

            print("  → Applying evaluation rubric...")
            scoring_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a fair and experienced educator who applies grading rubrics consistently. You give credit where it's due and honestly assess shortcomings. Your scores are well-calibrated to the rubric standards.",
                    },
                    {"role": "user", "content": scoring_prompt},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )

            scoring_result = json.loads(scoring_response.choices[0].message.content)

            correctness_score = float(scoring_result.get("correctness_score", 0))
            quality_score = float(scoring_result.get("quality_score", 0))
            completeness_score = float(scoring_result.get("completeness_score", 0))

            print(
                f"  → Scores: C={correctness_score:.1f} Q={quality_score:.1f} CP={completeness_score:.1f}"
            )

            # STEP 3: Educational Feedback (like ChatGPT/Claude would provide)
            feedback_prompt = f"""You are an expert programming mentor providing constructive, educational feedback to a student. Your goal is to help them learn and improve.

                **Analysis:**
                {json.dumps(analysis_result, indent=2)}

                **Scores:**
                - Correctness: {correctness_score}/10 - {scoring_result.get('correctness_justification', '')}
                - Quality: {quality_score}/10 - {scoring_result.get('quality_justification', '')}
                - Completeness: {completeness_score}/10 - {scoring_result.get('completeness_justification', '')}

                **Your Task - Write Educational Feedback:**

                Create feedback that:
                1. Speaks directly to the student ("you", "your")
                2. Starts with an honest overall assessment
                3. Acknowledges what they did well (if anything)
                4. Clearly explains what's wrong and why
                5. Provides specific, actionable improvements
                6. Encourages learning and growth

                The feedback should be:
                - **Honest** but **kind**
                - **Specific** not generic
                - **Educational** not just critical
                - **Actionable** with concrete next steps

                Respond in JSON:
                {{
                "main_feedback": "<3-4 sentences honest overall assessment using 'you/your'>",
                "what_went_well": ["<Specific strength 1>", "<Specific strength 2>"],
                "what_needs_improvement": ["<Specific issue 1 with why it matters>", "<Specific issue 2 with why it matters>"],
                "specific_suggestions": ["<Actionable suggestion 1>", "<Actionable suggestion 2>", "<Actionable suggestion 3>"],
                "learning_resources": ["<Concept to study>", "<Topic to review>"],
                "encouragement": "<1 sentence encouragement appropriate to their performance level>"
                }}

                **Tone Guidance:**
                - If scores 8.5+: Enthusiastic praise, minor refinements
                - If scores 6-8.4: Positive recognition, constructive guidance
                - If scores 3-5.9: Supportive but clear about shortcomings
                - If scores <3: Honest that more work needed, but encouraging"""

            print("  → Generating educational feedback...")
            feedback_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a patient, knowledgeable programming mentor. You give honest feedback while maintaining a supportive, educational tone. You help students learn from mistakes without being harsh.",
                    },
                    {"role": "user", "content": feedback_prompt},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )

            feedback_result = json.loads(feedback_response.choices[0].message.content)

            file_eval = {
                "file_path": file_path,
                "similarity_to_solution": round(similarity_to_solution * 100, 2),
                "similarity_to_original": round(similarity_to_before * 100, 2),
                "bug_fixed": analysis_result.get("bug_actually_fixed", False),
                "equivalence_level": analysis_result.get(
                    "equivalence_assessment", "unknown"
                ),
                "correctness_score": round(correctness_score, 1),
                "quality_score": round(quality_score, 1),
                "completeness_score": round(completeness_score, 1),
                "feedback": feedback_result.get("main_feedback", ""),
                "strengths": feedback_result.get("what_went_well", []),
                "improvements": feedback_result.get("what_needs_improvement", []),
                "suggestions": feedback_result.get("specific_suggestions", []),
                "learning_topics": feedback_result.get("learning_resources", []),
                "critical_issues": analysis_result.get("critical_issues", []),
                "changes_analysis": analysis_result.get("changes_analysis", {}),
                "detailed_justifications": {
                    "correctness": scoring_result.get("correctness_justification", ""),
                    "quality": scoring_result.get("quality_justification", ""),
                    "completeness": scoring_result.get(
                        "completeness_justification", ""
                    ),
                },
            }

            file_evaluations.append(file_eval)

            total_correctness += correctness_score
            total_quality += quality_score
            total_completeness += completeness_score
            files_evaluated += 1

            print(f"  ✓ Evaluation complete for {file_path}\n")

        except Exception as e:
            print(f"  ✗ Error evaluating {file_path}: {e}")
            import traceback

            traceback.print_exc()
            continue

    if files_evaluated == 0:
        raise HTTPException(
            status_code=500,
            detail="Could not evaluate any files for this submission and PR",
        )

    avg_correctness = total_correctness / files_evaluated
    avg_quality = total_quality / files_evaluated
    avg_completeness = total_completeness / files_evaluated
    overall_score = (avg_correctness + avg_quality + avg_completeness) / 3

    is_excellent = overall_score >= 8.5
    is_good = 7.0 <= overall_score < 8.5
    is_passing = 6.0 <= overall_score < 7.0
    is_needs_work = 4.0 <= overall_score < 6.0
    is_failing = overall_score < 4.0

    print(f"\n{'='*80}")
    print(f"OVERALL EVALUATION")
    print(f"{'='*80}")
    print(f"Correctness: {avg_correctness:.1f}/10")
    print(f"Quality: {avg_quality:.1f}/10")
    print(f"Completeness: {avg_completeness:.1f}/10")
    print(f"Overall: {overall_score:.1f}/10")
    print(f"{'='*80}\n")

    # STEP 4: Overall Summary (Professional Report)
    summary_prompt = f"""You are writing the executive summary section of a professional code review report.

        **Overall Performance:**
        - Overall Score: {overall_score:.1f}/10
        - Correctness: {avg_correctness:.1f}/10
        - Code Quality: {avg_quality:.1f}/10  
        - Completeness: {avg_completeness:.1f}/10
        - Files Evaluated: {files_evaluated}

        **Performance Band:** {"EXCELLENT (8.5-10)" if is_excellent else "GOOD (7.0-8.4)" if is_good else "PASSING (6.0-6.9)" if is_passing else "NEEDS IMPROVEMENT (4.0-5.9)" if is_needs_work else "FAILING (<4.0)"}

        **Detailed Results:**
        {json.dumps(file_evaluations, indent=2)}

        **Your Task - Write Executive Summary:**

        Create a professional summary that synthesizes the evaluation:

        1. **Opening Statement:** Clear verdict on overall performance (2 sentences)
        2. **Key Strengths:** What worked well across files
        3. **Key Areas for Improvement:** Main issues that need attention
        4. **Actionable Next Steps:** Concrete actions to improve
        5. **Learning Path:** Topics/concepts to study

        Respond in JSON:
        {{
        "executive_summary": "<Professional 3-4 sentence summary of performance>",
        "performance_verdict": "<excellent/good/passing/needs-improvement/failing>",
        "key_strengths": ["<Strength 1>", "<Strength 2>"],
        "key_improvements": ["<Improvement 1>", "<Improvement 2>"],
        "priority_actions": ["<Action 1>", "<Action 2>", "<Action 3>"],
        "suggested_learning": ["<Topic 1>", "<Topic 2>"],
        "next_challenge_recommendation": "<Should they move forward or retry? Why?>"
        }}

        **Tone:** Professional, balanced, educational. Match tone to performance level."""

    try:
        print("Generating overall summary...")
        summary_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a technical lead writing code review summaries. You provide clear, actionable feedback that helps developers improve. You're honest but constructive.",
                },
                {"role": "user", "content": summary_prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        summary_data = json.loads(summary_response.choices[0].message.content)
        print("✓ Summary generated\n")

    except Exception as e:
        print(f"Error generating summary: {e}")
        # Fallback summary
        if is_excellent:
            summary_data = {
                "executive_summary": f"Outstanding work! Your submission scored {overall_score:.1f}/10, demonstrating excellent understanding of the bug fix requirements. Your implementation is nearly flawless, with all critical changes implemented correctly.",
                "performance_verdict": "excellent",
                "key_strengths": [
                    "Correctly identified and fixed the bug",
                    "Clean, maintainable code",
                    "All required changes implemented",
                ],
                "key_improvements": [
                    "Minor refinements possible in edge case handling"
                ],
                "priority_actions": [
                    "Continue to next challenge",
                    "Consider performance optimizations",
                ],
                "suggested_learning": [
                    "Advanced design patterns",
                    "Performance optimization techniques",
                ],
                "next_challenge_recommendation": "You're ready for more advanced challenges. Excellent work!",
            }
        elif is_failing:
            summary_data = {
                "executive_summary": f"Your submission scored {overall_score:.1f}/10. The bug was not successfully fixed, and critical implementation issues remain. This requires substantial revision before moving forward.",
                "performance_verdict": "failing",
                "key_strengths": ["Attempted the assignment"],
                "key_improvements": [
                    "Bug fix not implemented correctly",
                    "Critical logic errors present",
                    "Required changes missing",
                ],
                "priority_actions": [
                    "Review the PR description carefully",
                    "Compare your changes line-by-line with expected solution",
                    "Test your code thoroughly before submission",
                ],
                "suggested_learning": [
                    "Bug fixing fundamentals",
                    "Code comparison techniques",
                    "Testing strategies",
                ],
                "next_challenge_recommendation": "Please retry this challenge after reviewing the feedback and studying the required concepts.",
            }
        else:
            summary_data = {
                "executive_summary": f"Your submission scored {overall_score:.1f}/10. You've made progress on the bug fix, but there are important areas that need improvement before this can be considered complete.",
                "performance_verdict": "needs-improvement",
                "key_strengths": [
                    "Partial implementation of required changes",
                    "Attempted to address the bug",
                ],
                "key_improvements": [
                    "Some required changes are missing",
                    "Logic implementation needs refinement",
                ],
                "priority_actions": [
                    "Review missing implementation details",
                    "Test edge cases",
                    "Verify all required changes are present",
                ],
                "suggested_learning": [
                    "Complete implementation techniques",
                    "Edge case handling",
                ],
                "next_challenge_recommendation": "Address the feedback and consider resubmitting before moving to the next challenge.",
            }

    return EvaluationResponse(
        submission_id=request.submission_id,
        pr_number=request.pr_number,
        overall_score=round(overall_score, 2),
        correctness_score=round(avg_correctness, 2),
        code_quality_score=round(avg_quality, 2),
        completeness_score=round(avg_completeness, 2),
        evaluation_summary=summary_data.get("executive_summary", ""),
        file_evaluations=file_evaluations,
        suggestions=summary_data.get("priority_actions", []),
        strengths=summary_data.get("key_strengths", []),
        areas_for_improvement=summary_data.get("key_improvements", []),
        evaluated_at=datetime.now().isoformat(),
    )


# ==================== ADMIN ENDPOINTS ====================

# ==================== AUTHENTICATION ====================

class LoginRequest(BaseModel):
    username: str
    password: str

class ChangePasswordRequest(BaseModel):
    username: str
    old_password: str
    new_password: str

@app.post("/admin/auth/login")
async def admin_login(request: LoginRequest):
    """Authenticate admin user"""
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


@app.post("/admin/auth/change-password")
async def admin_change_password(request: ChangePasswordRequest):
    """Change user password (dummy implementation for now)"""
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


class OffboardingLoginRequest(BaseModel):
    username: str
    password: str
    role: str  # "manager" or "employee"

@app.post("/admin/auth/offboarding/login")
async def offboarding_login(request: OffboardingLoginRequest):
    """Authenticate offboarding user (manager or employee)"""
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


@app.get("/admin/test")
async def admin_test():
    """Test endpoint to verify admin routes are working"""
    return {"status": "ok", "message": "Admin endpoints are accessible"}


@app.get("/admin/routes")
async def list_admin_routes():
    """List all admin routes for debugging"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and route.path.startswith('/admin'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if hasattr(route, 'methods') else []
            })
    return {"status": "ok", "routes": routes}


class ValidateRepositoryRequest(BaseModel):
    organization: str
    repo_name: str


@app.post("/admin/validate-repository")
async def validate_repository(request: ValidateRepositoryRequest):
    """
    Validate if a GitHub repository exists and is accessible.
    Returns validation result with detailed error messages.
    """
    import requests
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
    import re
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


def run_data_collection(owner: str, repo: str) -> Dict[str, Any]:
    """Run data collection for a repository"""
    try:
        # Import here to avoid circular imports
        from core.DataCollection.DataCollectionFromGithub.repository_processor import RepositoryProcessor
        
        processor = RepositoryProcessor()
        if not processor.test_connection():
            return {"success": False, "error": "GitHub API connection failed. Check your token."}
        
        repo_data = processor.process_repository(owner, repo)
        output_file = processor.save_repository_data(repo_data, owner, repo)
        
        return {
            "success": True,
            "output_file": str(output_file),
            "stats": repo_data.get("stats", {}),
            "message": f"Successfully collected data for {owner}/{repo}"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


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
        import argparse
        
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


@app.post("/admin/setup/data-collection", response_model=SetupResponse)
async def admin_data_collection(request: SetupRequest):
    """Step 1: Data Collection"""
    try:
        result = run_data_collection(request.organization, request.repo_name)
        if result["success"]:
            return SetupResponse(
                status="success",
                message=result["message"],
                step="data-collection",
                details=result
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Data collection failed"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/setup/data-processing", response_model=SetupResponse)
async def admin_data_processing(request: SetupRequest):
    """Step 2: Data Processing"""
    try:
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/setup/embedding", response_model=SetupResponse)
async def admin_embedding(request: SetupRequest):
    """Step 3: Embedding Generation"""
    try:
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/setup/vectordb", response_model=SetupResponse)
async def admin_vectordb(request: SetupRequest):
    """Step 4: VectorDB Building"""
    try:
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def run_onboarding(generators_to_run: list = None) -> Dict[str, Any]:
    """Run onboarding data generation"""
    try:
        import sys
        from pathlib import Path
        
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


class OnboardingRequest(BaseModel):
    generators: Optional[List[str]] = None

@app.post("/admin/onboarding/run", response_model=SetupResponse)
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


def verify_employee_exists(employee_name: str) -> Dict[str, Any]:
    """Verify if an employee exists in users.json or PR data"""
    try:
        repo_root = Path(__file__).resolve().parent.parent.parent
        users_file = repo_root / "data" / "Admin" / "users.json"
        
        # Try alternative paths
        if not users_file.exists():
            possible_paths = [
                repo_root / "backend" / "data" / "Admin" / "users.json",
                Path(r"C:\Users\vishalke\Desktop\AI007\super-employee\backend\data\Admin\users.json"),
            ]
            for path in possible_paths:
                if path.exists():
                    users_file = path
                    break
        
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
                Path(r"C:\Users\vishalke\Desktop\AI007\super-employee\backend\data\Offboarding\1employees_with_ids.json"),
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


class OffboardingRequest(BaseModel):
    steps: Optional[List[str]] = None
    employee_name: str

@app.post("/admin/offboarding/run", response_model=SetupResponse)
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


@app.post("/admin/setup/cancel")
async def cancel_pipeline():
    """Cancel the currently running pipeline"""
    global pipeline_cancelled, current_pipeline_task
    pipeline_cancelled.set()
    if current_pipeline_task:
        current_pipeline_task.cancel()
    return {"status": "cancelled", "message": "Pipeline cancellation requested"}


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


@app.get("/admin/history")
async def get_admin_history():
    """Get admin setup history"""
    history = load_admin_history()
    return {"status": "success", "history": history}


@app.post("/admin/history")
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


@app.delete("/admin/history")
async def clear_admin_history():
    """Clear all admin setup history"""
    if save_admin_history([]):
        return {"status": "success", "message": "History cleared"}
    else:
        raise HTTPException(status_code=500, detail="Failed to clear history")


@app.websocket("/ws/admin/pipeline")
async def websocket_pipeline(websocket: WebSocket):
    """WebSocket endpoint for real-time pipeline progress updates"""
    await websocket.accept()
    global pipeline_cancelled, current_pipeline_task
    
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
            
            future = executor.submit(run_step, "data-collection", run_data_collection, organization, repo_name)
            current_pipeline_task = future
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
            current_pipeline_task = future
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
            current_pipeline_task = future
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
            current_pipeline_task = future
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
            current_pipeline_task = None
            
    except WebSocketDisconnect:
        print("Pipeline WebSocket disconnected")
        pipeline_cancelled.set()
    except Exception as e:
        print(f"Pipeline WebSocket error: {e}")
        await websocket.send_json({"type": "error", "message": str(e)})


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket for streaming responses with GitHub + Gmail support"""
    await websocket.accept()

    if chatbot_instance is None:
        await websocket.send_json(
            {"type": "error", "message": "Chatbot not initialized"}
        )
        await websocket.close()
        return

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            query = message.get("query")
            username = message.get("username")

            if not query:
                await websocket.send_json(
                    {"type": "error", "message": "No query provided"}
                )
                continue

            # Determine which repo to use based on username
            user_repo = get_user_repo(username)
            
            if user_repo:
                owner = user_repo.get("owner")
                repo_name = user_repo.get("name")
                
                if owner and repo_name:
                    # Ensure chatbot is using the correct repo database
                    if not ensure_chatbot_for_repo(owner, repo_name):
                        await websocket.send_json({
                            "type": "status",
                            "message": f"Warning: Could not switch to repo {owner}/{repo_name}, using current database"
                        })

            await websocket.send_json(
                {"type": "status", "message": "Searching GitHub codebase..."}
            )

            result = chatbot_instance.chat(query, message.get("filters"))

            if result.get("emails"):
                await websocket.send_json(
                    {
                        "type": "status",
                        "message": f"Found {len(result['emails'])} relevant emails",
                    }
                )

            import re

            sentences = re.split(r"(?<=[.!?])\s+", result["answer"])
            for sentence in sentences:
                await websocket.send_json({"type": "chunk", "content": sentence + " "})
                await asyncio.sleep(0.05)

            await websocket.send_json(
                {
                    "type": "complete",
                    "answer": result["answer"],
                    "sources": result["sources"],
                    "chunks_retrieved": result["chunks_retrieved"],
                    "related_knowledge": result.get("related_knowledge"),
                    "emails": result.get("emails", []),
                    "has_diagram": result.get("has_diagram", False),
                    "flow_data": result.get("flow_data"),
                    "query_type": result.get("query_type"),
                    "context_quality": result.get("context_quality"),
                }
            )

    except WebSocketDisconnect:
        print("Client disconnected\n")
    except Exception as e:
        print(f"WebSocket error: {e}\n")
        await websocket.send_json({"type": "error", "message": str(e)})


# ===================== USER MANAGEMENT ENDPOINTS =====================

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

@app.get("/admin/users")
async def get_all_users():
    """Get all users from users.json"""
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

@app.post("/admin/users")
async def create_user(request: CreateUserRequest):
    """Create a new user"""
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

@app.put("/admin/users/{username}")
async def update_user(username: str, request: UpdateUserRequest):
    """Update an existing user"""
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

@app.delete("/admin/users/{username}")
async def delete_user(username: str):
    """Delete a user"""
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


def start_server():
    """Start the FastAPI server"""
    import uvicorn

    print("Starting FastAPI server")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    start_server()
