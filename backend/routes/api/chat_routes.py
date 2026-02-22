"""
Chat-related API routes for the RAG Chatbot
Contains all chat endpoints and WebSocket handlers
"""

import time

import boto3
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from pathlib import Path
import os
import json
import asyncio
from datetime import datetime
import difflib
from openai import OpenAI
import re
from routes.api import shared
from botocore.exceptions import ClientError
from datetime import datetime
from utils.private_repo_state_manager import private_repo_state
from fastapi.responses import RedirectResponse, StreamingResponse

router = APIRouter()

S3_BUCKET = os.getenv("AWS_BUCKET_NAME", "smarix-data-apsouth1")
S3_REGION = os.getenv("AWS_DEFAULT_REGION", "ap-south-1")

s3_client = boto3.client(
    "s3",
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)


router = APIRouter()


# ==================== PYDANTIC MODELS ====================


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
    repo_name: str


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


class NewSessionRequest(BaseModel):
    username: str


class ClearHistoryRequest(BaseModel):
    session_id: str
    username: str


# ==================== HELPER FUNCTIONS ====================


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


def get_user_schema_name(username: str) -> str:
    """Generate schema name from username (must match logic in auth/routes.py)"""
    if not username:
        # Fallback for anonymous/public users, or raise HTTPException
        return "public"
    sanitized = re.sub(r"[^a-z0-9_]", "_", username.lower())
    return f"user_{sanitized}"


# ==================== CHAT ENDPOINTS ====================


@router.get("/")
async def root():
    """Health check and status"""
    from . import shared

    return {
        "status": "online",
        "version": "2.1.0",
        "chatbot_ready": shared.chatbot_instance is not None,
        "config": shared.chatbot_config,
        "available_providers": shared.available_providers,
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


# @router.get("/health")
# async def health_check():
#     """Detailed health check"""
#     from . import shared

#     health = {
#         "api": "healthy",
#         "version": "2.1.0",
#         "chatbot": "ready" if shared.chatbot_instance else "not initialized",
#         "api_keys": shared.available_providers,
#         "github_db": (
#             "configured" if shared.chatbot_config.get("github_db_path") else "not configured"
#         ),
#         "gmail_db": (
#             "configured" if shared.chatbot_config.get("gmail_db_path") else "not configured"
#         ),
#     }

#     if shared.chatbot_instance:
#         try:
#             stats = shared.chatbot_instance.get_stats()
#             health["github_chunks"] = stats.get("total_chunks", 0)
#             health["conversation_length"] = stats.get("conversation_length", 0)

#             if "gmail_indexed" in stats:
#                 health["gmail_emails"] = stats.get("gmail_indexed", 0)

#             health["features"] = stats.get("features", [])

#             # ✅ ADD SEMANTIC CACHE STATUS
#             if (
#                 shared.chatbot_instance.query_rewriter
#                 and shared.chatbot_instance.query_rewriter.semantic_cache
#             ):
#                 cache_stats = shared.chatbot_instance.query_rewriter.semantic_cache.get_stats()
#                 health["semantic_cache"] = {
#                     "enabled": True,
#                     "cache_size": cache_stats.get("cache_size", 0),
#                     "hit_rate": cache_stats.get("overall_hit_rate", 0),
#                     "total_queries": cache_stats.get("total_queries", 0),
#                     "cost_saved": cache_stats.get("cost_saved_usd", 0),
#                 }
#             else:
#                 health["semantic_cache"] = {
#                     "enabled": False,
#                     "reason": "Redis or embeddings not configured",
#                 }

#         except Exception as e:
#             health["error"] = str(e)

#     return health


@router.post("/init")
async def initialize_chatbot(config: InitRequest):
    """Initialize or reinitialize the chatbot"""
    # Import here to avoid circular dependency
    from . import chatbot_api
    from .chatbot_api import available_providers, RAGChatbot

    if config.provider == "openai" and not available_providers.get("openai"):
        raise HTTPException(status_code=400, detail="OpenAI API key not configured")

    if config.provider == "anthropic" and not available_providers.get("anthropic"):
        raise HTTPException(status_code=400, detail="Anthropic API key not configured")

    github_db_path = config.github_db_path
    gmail_db_path = config.gmail_db_path

    # Try to find databases if not provided
    if not github_db_path and not gmail_db_path:
        from .chatbot_api import find_vector_databases

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

        chatbot_api.chatbot_instance = RAGChatbot(
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

        if chatbot_api.chatbot_instance.db:
            github_vectors = chatbot_api.chatbot_instance.db.index.ntotal
            databases.append(f"GitHub ({github_vectors} vectors)")
            total_vectors += github_vectors

        if chatbot_api.chatbot_instance.gmail_db:
            gmail_vectors = chatbot_api.chatbot_instance.gmail_db.index.ntotal
            databases.append(f"Gmail ({gmail_vectors} emails)")
            total_vectors += gmail_vectors

        chatbot_api.chatbot_config = {
            "github_db_path": github_db_path,
            "gmail_db_path": gmail_db_path,
            "provider": config.provider,
            "model": config.model or chatbot_api.chatbot_instance.model,
            "total_vectors": total_vectors,
            "databases": databases,
            "status": "ready",
        }

        print("Chatbot reinitialized\n")

        return {
            "status": "success",
            "message": "Chatbot initialized successfully",
            "config": chatbot_api.chatbot_config,
        }

    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint - retrieves from GitHub first, then supplements with Gmail if needed"""
    # Import here to avoid circular dependency
    # Handle both relative (module) and absolute (script) imports
    import sys

    # Try to get chatbot_api module from sys.modules first (handles script execution)
    # chatbot_api_module = None
    # for module_name in ['__main__', 'routes.api.chatbot_api', 'chatbot_api']:
    #     if module_name in sys.modules:
    #         chatbot_api_module = sys.modules[module_name]
    #         break

    # if chatbot_api_module:
    #     # Use the already-loaded module
    #     chatbot_instance = chatbot_api_module.chatbot_instance
    #     chatbot_config = chatbot_api_module.chatbot_config
    #     get_user_repo = chatbot_api_module.get_user_repo
    #     ensure_chatbot_for_repo = chatbot_api_module.ensure_chatbot_for_repo
    # else:
    #     # Fallback to normal import
    #     try:
    #         from .chatbot_api import (
    #             chatbot_instance,
    #             chatbot_config,
    #             get_user_repo,
    #             ensure_chatbot_for_repo,
    #         )
    #     except (ImportError, ValueError):
    #         # When running as script, use absolute import
    #         from pathlib import Path
    #         current_dir = Path(__file__).parent
    #         backend_dir = current_dir.parent.parent
    #         if str(backend_dir) not in sys.path:
    #             sys.path.insert(0, str(backend_dir))
    #         from routes.api.chatbot_api import (
    #             chatbot_instance,
    #             chatbot_config,
    #             get_user_repo,
    #             ensure_chatbot_for_repo,
    #         )

    if shared.chatbot_instance is None:
        # Provide more detailed error message
        error_detail = "Chatbot not initialized"
        if shared.chatbot_config:
            config_status = shared.chatbot_config.get("status", "unknown")
            config_error = shared.chatbot_config.get("error")
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

        schema_name = get_user_schema_name(request.username)

        # Determine which repo to use based on username
        user_repo = shared.get_user_repo(request.username)

        if user_repo:
            owner = user_repo.get("owner")
            repo_name = user_repo.get("name")

            if owner and repo_name:
                print(
                    f"Using repo for user {request.username or 'anonymous'}: {owner}/{repo_name}"
                )
                # Ensure chatbot is using the correct repo database
                if not shared.ensure_chatbot_for_repo(owner, repo_name):
                    print(
                        f"⚠ Warning: Could not switch to repo {owner}/{repo_name}, using current database"
                    )
        else:
            if request.username:
                print(
                    f"⚠ Warning: No repo found for user {request.username}, using default database"
                )
            else:
                print("Using default database (no username provided)")

        print(f"Query: {request.query[:100]}...")
        print(f"Session: {request.session_id or 'new'}")
        print(f"Role: {request.role or 'general'}")
        if request.username:
            print(f"User: {request.username}")

        result = shared.chatbot_instance.chat(
            request.query,
            get_user_schema_name(request.username),
            request.filters,
            session_id=request.session_id,
            role=request.role or "general",
        )

        # 🔒 HARD NORMALIZATION (ADD THIS)
        result = result or {}

        result.setdefault("answer", "")
        result.setdefault("sources", [])
        result.setdefault("chunks_retrieved", 0)
        result.setdefault("related_knowledge", None)
        result.setdefault("emails", [])
        result.setdefault("has_diagram", False)
        result.setdefault("flow_data", None)
        result.setdefault("query_type", None)
        result.setdefault("context_quality", None)

        sources = result.get("sources", []) or []

        enriched_sources = []
        for source in sources:
            enriched_source = {
                **source,
                "file": source.get("file", "unknown"),
                "type": source.get("type", "unknown"),
                "score": source.get("score", 0.0),
                "context_role": source.get("context_role", "primary"),
            }
            enriched_sources.append(enriched_source)

        email_count = len(result.get("emails", []))

        chunks_retrieved = result.get("chunks_retrieved", 0)
        print(f"Response: {chunks_retrieved} code chunks", end="")

        if email_count > 0:
            print(f" + {email_count} emails")
        else:
            print()
        print()

        session_id = shared.chatbot_instance.get_session_id()

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


@router.post("/new-session")
async def new_session(request: NewSessionRequest):
    """Generate a fresh session ID in the user's schema."""

    if shared.chatbot_instance is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    schema_name = get_user_schema_name(request.username)

    new_session_id = shared.chatbot_instance.start_new_session(schema_name=schema_name)

    print(f"NEW SESSION CREATED: {new_session_id} in {schema_name}")
    return {"session_id": new_session_id, "message": "New session created"}


@router.post("/clear-history")
async def clear_history(request: ClearHistoryRequest):
    if shared.chatbot_instance is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    schema_name = get_user_schema_name(request.username)

    session_id = shared.chatbot_instance.set_session(request.session_id)

    shared.chatbot_instance.conversation_store.clear_session(
        session_id, schema_name=schema_name
    )
    print(f"History cleared for session {session_id[:8]} in {schema_name}...\n")

    return {"status": "success", "message": "Session history cleared"}


@router.get("/sessions")
async def get_sessions(username: str, limit: int = 50):
    if shared.chatbot_instance is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    try:
        schema_name = get_user_schema_name(username)

        all_sessions = shared.chatbot_instance.conversation_store.get_all_sessions(
            limit=limit, schema_name=schema_name
        )

        sessions = []
        for session_data in all_sessions:
            sessions.append(
                {
                    "session_id": session_data["session_id"],
                    "title": session_data.get("title", "New Chat"),
                    "message_count": session_data.get("message_count", 0),
                    "last_message": str(session_data.get("updated_at", "")),
                    "first_message": str(session_data.get("created_at", "")),
                    "total_tokens": 0,
                }
            )

        print(f"📋 Returning {len(sessions)} sessions to frontend")
        return {"sessions": sessions}

    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/load-session/{session_id}")
async def load_session(session_id: str, username: str):
    if shared.chatbot_instance is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    try:
        schema_name = get_user_schema_name(username)
        print(f"📖 Loading session {session_id} from schema: {schema_name}")  # Debug

        # Try to get messages - handle empty case
        try:
            messages = shared.chatbot_instance.conversation_store.get_full_history(
                session_id, schema_name=schema_name
            )
            print(f"📖 Retrieved {len(messages)} messages")  # Debug
        except Exception as msg_error:
            print(f"⚠️ Error fetching messages: {msg_error}")
            import traceback

            traceback.print_exc()  # Full traceback
            # Return empty messages instead of failing
            messages = []

        # Set current session
        shared.chatbot_instance.set_session(session_id, schema_name)

        # Try to get stats - handle empty case
        try:
            stats = shared.chatbot_instance.conversation_store.get_session_stats(
                session_id, schema_name=schema_name
            )
        except Exception as stats_error:
            print(f"⚠️ Error fetching stats: {stats_error}")
            # Return default stats instead of failing
            stats = {
                "message_count": 0,
                "last_message": "",
                "first_message": "",
                "total_tokens": 0,
            }

        return {"session_id": session_id, "messages": messages, "stats": stats}
    except Exception as e:
        print(f"❌ Full exception in /load-session: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-session/{session_id}")
async def delete_session(session_id: str, username: str):
    if shared.chatbot_instance is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    try:
        schema_name = get_user_schema_name(username)
        shared.chatbot_instance.conversation_store.delete_session(
            session_id, schema_name=schema_name
        )
        return {"status": "success", "message": "Session deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats():
    """Get chatbot statistics including GitHub and Gmail stats"""

    if shared.chatbot_instance is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    try:
        stats = shared.chatbot_instance.get_stats()

        enhanced_stats = {
            "status": "success",
            "stats": stats,
            "databases": {
                "github": {
                    "enabled": bool(shared.chatbot_instance.db),
                    "vectors": (
                        shared.chatbot_instance.db.index.ntotal
                        if shared.chatbot_instance.db
                        else 0
                    ),
                },
                "gmail": {
                    "enabled": bool(shared.chatbot_instance.gmail_db),
                    "emails": (
                        shared.chatbot_instance.gmail_db.index.ntotal
                        if shared.chatbot_instance.gmail_db
                        else 0
                    ),
                },
            },
        }

        return enhanced_stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/semantic-cache-stats")
async def get_semantic_cache_stats():
    """Get universal semantic cache statistics with confidence breakdown"""

    if shared.chatbot_instance is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    try:
        # Check if semantic cache is enabled
        if not (
            shared.chatbot_instance.query_rewriter
            and shared.chatbot_instance.query_rewriter.semantic_cache
        ):
            return {
                "status": "disabled",
                "message": "Semantic cache not enabled. Ensure Redis and embeddings are configured.",
            }

        # Get comprehensive stats
        cache_stats = shared.chatbot_instance.query_rewriter.semantic_cache.get_stats()

        return {
            "status": "success",
            "cache_stats": cache_stats,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invalidate-cache/{session_id}")
async def invalidate_semantic_cache(session_id: str):
    """Invalidate semantic cache for a specific session"""

    if shared.chatbot_instance is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    try:
        if not (
            shared.chatbot_instance.query_rewriter
            and shared.chatbot_instance.query_rewriter.semantic_cache
        ):
            raise HTTPException(status_code=400, detail="Semantic cache not enabled")

        # Invalidate cache
        count = (
            shared.chatbot_instance.query_rewriter.semantic_cache.invalidate_session(
                session_id
            )
        )

        return {
            "status": "success",
            "message": f"Invalidated {count} cache entries for session",
            "session_id": session_id,
            "entries_cleared": count,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-all-cache")
async def clear_all_semantic_cache():
    """Clear entire semantic cache (admin operation)"""

    if shared.chatbot_instance is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    try:
        if not (
            shared.chatbot_instance.query_rewriter
            and shared.chatbot_instance.query_rewriter.semantic_cache
        ):
            raise HTTPException(status_code=400, detail="Semantic cache not enabled")

        # Clear in-memory index
        initial_size = len(
            shared.chatbot_instance.query_rewriter.semantic_cache.cache_index
        )
        shared.chatbot_instance.query_rewriter.semantic_cache.cache_index.clear()

        # Reset stats
        shared.chatbot_instance.query_rewriter.semantic_cache.stats = {
            "total_queries": 0,
            "exact_matches": 0,
            "very_high_matches": 0,
            "high_matches": 0,
            "medium_matches": 0,
            "low_matches": 0,
            "no_matches": 0,
            "augmentations": 0,
            "context_hints": 0,
            "cost_saved_usd": 0.0,
        }

        return {
            "status": "success",
            "message": "Cleared all semantic cache",
            "entries_cleared": initial_size,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_config():
    """Get current configuration"""

    return {
        "status": "success",
        "config": shared.chatbot_config,
        "available_providers": shared.available_providers,
    }


# ==================== GITHUB APP INTEGRATION ====================


@router.get("/auth/github/callback")
async def github_callback(
    code: str, installation_id: int, setup_action: str, state: str = None
):
    """
    GitHub redirects here after app installation/configuration
    """
    print("=" * 80)
    print("🎉 GITHUB APP CALLBACK RECEIVED")
    print(f"⏰ Time: {time.strftime('%H:%M:%S')}")
    print(f"Installation ID: {installation_id}")
    print(f"Setup Action: {setup_action}")
    if state:
        print(f"State: {state}")
    print("=" * 80)

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    redirect_path = "/manager/pipeline"

    # Parse state for custom return URL
    if state:
        try:
            import base64
            import json

            state_data = json.loads(base64.b64decode(state))
            redirect_path = state_data.get("return_url", redirect_path)
        except Exception as e:
            print(f"⚠️ Failed to parse state: {e}")

    # Redirect with parameters for frontend to detect
    redirect_url = (
        f"{frontend_url}{redirect_path}"
        f"?github_connected=true"
        f"&installation_id={installation_id}"
        f"&setup_action={setup_action}"
    )

    print(f"🔄 Redirecting to: {redirect_url}")
    print("=" * 80)

    return RedirectResponse(url=redirect_url)


# ==================== GITHUB APP WEBHOOK ====================


@router.post("/webhooks/github")
async def github_webhook(request: Request):
    """
    GitHub sends webhooks here when:
    - App is installed/uninstalled
    - Repositories are added/removed

    Saves to private_runtime_state.json (single account only)
    """

    try:
        payload = await request.json()
        event_type = request.headers.get("X-GitHub-Event")
        action = payload.get("action", "N/A")

        print("=" * 80)
        print(f"📨 GITHUB WEBHOOK RECEIVED")
        print(f"Event Type: {event_type}")
        print(f"Action: {action}")
        print("=" * 80)

        if event_type == "installation":
            installation_id = payload["installation"]["id"]
            account = payload["installation"]["account"]
            account_login = account["login"]
            account_type = account["type"]  # 'User' or 'Organization'

            installer = payload.get("sender", {}).get("login", "unknown")

            if action == "created":
                repos = payload.get("repositories", [])
                repo_list = [
                    {
                        "name": r["name"],
                        "full_name": r["full_name"],
                        "private": r.get("private", False),
                    }
                    for r in repos
                ]

                print(f"✅ App installed on: {account_login} ({account_type})")
                print(f"   Installed by: {installer}")
                print(f"   Installation ID: {installation_id}")
                print(f"   Repositories granted: {len(repo_list)}")
                for r in repo_list:
                    print(
                        f"     - {r['full_name']} ({'🔒 private' if r['private'] else '🔓 public'})"
                    )

                # ✅ SAVE TO private_runtime_state.json
                success = private_repo_state.set_state(
                    owner=account_login,
                    installation_id=installation_id,
                    account_type=account_type,
                    repositories=repo_list,
                )
                if success:
                    print(f"✅ Saved to private_runtime_state.json")
                else:
                    print(f"❌ Failed to save to private_runtime_state.json")

            elif action == "deleted":
                print(f"❌ App uninstalled from: {account_login}")
                print(f"   Uninstalled by: {installer}")

                # ✅ CLEAR private_runtime_state.json
                current_owner = private_repo_state.get_owner()
                if current_owner == account_login:
                    success = private_repo_state.clear_state()
                    if success:
                        print(f"✅ Cleared private_runtime_state.json")
                    else:
                        print(f"⚠️ Failed to clear private_runtime_state.json")

        elif event_type == "installation_repositories":
            # ✅ THIS IS THE KEY EVENT FOR ADDING/REMOVING REPOS
            installation_id = payload["installation"]["id"]
            account = payload["installation"]["account"]
            account_login = account["login"]
            account_type = account["type"]  # 'User' or 'Organization'

            added = payload.get("repositories_added", [])
            removed = payload.get("repositories_removed", [])

            print(f"📝 Repository changes for: {account_login}")
            print(f"   Installation ID: {installation_id}")
            print(f"   Account Type: {account_type}")

            if added:
                print(f"➕ Repositories added: {len(added)}")
                for r in added:
                    print(f"     + {r['full_name']}")

            if removed:
                print(f"➖ Repositories removed: {len(removed)}")
                for r in removed:
                    print(f"     - {r['full_name']}")

            # ✅ UPDATE OR CREATE repositories in private_runtime_state.json
            try:
                current_state = private_repo_state.get_state()

                # ✅ FIX: If no state exists, CREATE it (reconnection scenario)
                if not current_state:
                    print(
                        f"⚠️ No existing state found - creating new state for {account_login}"
                    )
                    print(f"   This happens when reconnecting after disconnect")

                    # Create new state with added repos
                    repo_list = [
                        {
                            "name": r["name"],
                            "full_name": r["full_name"],
                            "private": r.get("private", False),
                        }
                        for r in added
                    ]

                    print(f"   Creating state with {len(repo_list)} repos")

                    success = private_repo_state.set_state(
                        owner=account_login,
                        installation_id=installation_id,
                        account_type=account_type,
                        repositories=repo_list,
                    )

                    if success:
                        print(f"✅ Created new state successfully!")
                        for r in repo_list:
                            print(f"     - {r['full_name']}")
                    else:
                        print(f"❌ Failed to create new state")

                    print("=" * 80)
                    return {"status": "received", "event": event_type, "action": action}

                # State exists - update it
                current_owner = current_state.get("owner")

                if current_owner == account_login:
                    print(f"🔄 Updating repos for connected account: {current_owner}")

                    current_repos = private_repo_state.get_repositories()
                    print(f"   Current repos count: {len(current_repos)}")

                    # Remove deleted repos
                    removed_names = [r["full_name"] for r in removed]
                    current_repos = [
                        r for r in current_repos if r["full_name"] not in removed_names
                    ]
                    print(f"   After removing: {len(current_repos)} repos")

                    # Add new repos (avoid duplicates)
                    existing_names = {r["full_name"] for r in current_repos}
                    for repo in added:
                        if repo["full_name"] not in existing_names:
                            new_repo = {
                                "name": repo["name"],
                                "full_name": repo["full_name"],
                                "private": repo.get("private", False),
                            }
                            current_repos.append(new_repo)
                            print(f"   Added: {new_repo['full_name']}")
                        else:
                            print(f"   Skipped (duplicate): {repo['full_name']}")

                    print(f"   Final repos count: {len(current_repos)}")

                    # Update in S3
                    success = private_repo_state.update_repositories(current_repos)
                    if success:
                        print(f"✅ Updated private_runtime_state.json")
                        print(f"   Total repos now: {len(current_repos)}")
                    else:
                        print(f"❌ Failed to update repositories")
                else:
                    print(
                        f"⚠️ Repository change for {account_login} but connected account is {current_owner}"
                    )
                    print(f"   This might be a different user reconnecting")
                    print(f"   Creating new state for {account_login}")

                    # Create new state for this account (replaces old account)
                    repo_list = [
                        {
                            "name": r["name"],
                            "full_name": r["full_name"],
                            "private": r.get("private", False),
                        }
                        for r in added
                    ]

                    success = private_repo_state.set_state(
                        owner=account_login,
                        installation_id=installation_id,
                        account_type=account_type,
                        repositories=repo_list,
                    )

                    if success:
                        print(
                            f"✅ Created new state for {account_login} with {len(repo_list)} repos"
                        )
                    else:
                        print(f"❌ Failed to create new state")

            except Exception as e:
                print(f"❌ Exception updating repositories: {e}")
                import traceback

                traceback.print_exc()

        else:
            print(f"ℹ️ Unhandled webhook event type: {event_type}")

        print("=" * 80)
        print()

        return {"status": "received", "event": event_type, "action": action}

    except Exception as e:
        print(f"❌ WEBHOOK ERROR: {e}")
        import traceback

        traceback.print_exc()
        print("=" * 80)
        return {"status": "error", "message": str(e)}


@router.get("/api/data-collection/private-repo-state")
async def get_private_repo_state():
    """
    Get the current private repository state
    Returns the connected account and its repositories
    """
    print("=" * 80)
    print("📊 API: Loading private repo state...")

    try:
        state = private_repo_state.get_state()

        if state:
            print(f"✅ Loaded private repo state")
            print(f"📍 S3 Key: Admin/state/private_runtime_state.json")
            print(f"   Owner: {state.get('owner')}")
            print(f"   Installation ID: {state.get('installation_id')}")
            print(f"   Repositories: {len(state.get('repositories', []))}")
            for repo in state.get("repositories", []):
                print(
                    f"     - {repo['full_name']} ({'🔒 private' if repo['private'] else '🔓 public'})"
                )
        else:
            print("⚠️ No private repo state found")
            print("💡 Connect your GitHub account to get started")

        print("=" * 80)

        return {"connected": state is not None, "state": state}

    except Exception as e:
        print(f"❌ Error loading private repo state: {e}")
        import traceback

        traceback.print_exc()
        print("=" * 80)
        return {"connected": False, "state": None, "error": str(e)}


@router.post("/api/data-collection/disconnect-github")
async def disconnect_github():
    """
    Disconnect the current GitHub account
    """
    print("=" * 80)
    print("🔌 API: Disconnecting GitHub account...")

    try:
        current_owner = private_repo_state.get_owner()

        if not current_owner:
            print("⚠️ No account connected")
            print("=" * 80)
            return {"success": False, "message": "No account connected"}

        success = private_repo_state.clear_state()

        if success:
            print(f"✅ Disconnected {current_owner}")
            print("=" * 80)
            return {"success": True, "message": f"Disconnected {current_owner}"}
        else:
            print(f"❌ Failed to disconnect {current_owner}")
            print("=" * 80)
            return {"success": False, "message": "Failed to disconnect account"}

    except Exception as e:
        print(f"❌ Error disconnecting: {e}")
        import traceback

        traceback.print_exc()
        print("=" * 80)
        return {"success": False, "message": str(e)}


def get_json_from_s3(key: str) -> Dict[str, Any]:
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=key)
        content = response["Body"].read().decode("utf-8")
        return json.loads(content)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchKey":
            print(f"File not found in S3: {key}")
            return None
        else:
            print(f"S3 Error: {str(e)}")
            raise e
    except Exception as e:
        print(f"Error parsing S3 file {key}: {str(e)}")
        raise e


# --- Helper: Similarity Calculation ---
import difflib


def calculate_similarity(code1: str, code2: str) -> float:
    return difflib.SequenceMatcher(None, code1, code2).ratio()


# --- Main Evaluation Route ---
@router.post("/evaluate-submission", response_model=EvaluationResponse)
async def evaluate_submission(request: EvaluationRequest):
    """
    Evaluates submission using data strictly from S3.
    """
    print(
        f"🚀 START: Evaluating Submission {request.submission_id} for PR {request.pr_number}"
    )

    # 1. Define S3 Paths based on Repo Name
    submitted_key = f"Onboarding/{request.repo_name}/bugfix/onboarding_challenge_submitted_code.json"
    solution_key = (
        f"Onboarding/{request.repo_name}/bugfix/onboarding_coding_questions.json"
    )

    print(f"Fetching from S3 bucket: {S3_BUCKET}")
    print(f"Submission Key: {submitted_key}")
    print(f"Solution Key: {solution_key}")

    # 2. Fetch Data from S3
    submitted_data = get_json_from_s3(submitted_key)
    solution_data = get_json_from_s3(solution_key)

    if not submitted_data:
        print(f"❌ Submission file missing at: {submitted_key}")
        raise HTTPException(
            status_code=404, detail=f"Submission file not found: {submitted_key}"
        )

    if not solution_data:
        print(f"❌ Solution file missing at: {solution_key}")
        raise HTTPException(
            status_code=404, detail=f"Solution file not found: {solution_key}"
        )

    # 3. Locate Specific Submission
    submission = None
    submissions_list = submitted_data.get("submissions", [])

    for sub in submissions_list:
        if sub["submission_id"] == request.submission_id:
            submission = sub
            break

    # Fallback: If exact ID not found (rare race condition), try finding latest by PR
    if not submission:
        print(
            f"⚠️ Submission ID {request.submission_id} not found immediately. Searching by PR..."
        )
        matching = [
            s
            for s in submissions_list
            if str(s.get("pr_number")) == str(request.pr_number)
        ]
        if matching:
            submission = matching[-1]  # Take latest
            print(
                f"✅ Found latest submission for PR {request.pr_number}: {submission['submission_id']}"
            )

    if not submission:
        raise HTTPException(
            status_code=404,
            detail=f"Submission ID {request.submission_id} not found in S3 file",
        )

    # 4. Locate Specific Solution (Robust Lookup)
    solution_pr = None

    # ✅ FIX: Added "questions" to the lookup list to match your JSON format
    pr_list = (
        solution_data.get("pull_requests")
        or solution_data.get("challenges")
        or solution_data.get("questions")  # <--- Added this!
        or []
    )

    available_ids = []

    for pr in pr_list:
        # Check multiple possible ID fields
        pr_id = str(pr.get("pr_number") or pr.get("question_number") or pr.get("id"))
        available_ids.append(pr_id)

        if pr_id == str(request.pr_number):
            solution_pr = pr
            break

    if not solution_pr:
        # LOGGING FOR DEBUGGING
        print(f"❌ PR {request.pr_number} not found.")
        print(f"ℹ️  IDs actually found in file: {available_ids}")

        raise HTTPException(
            status_code=404,
            detail=f"Solution for PR #{request.pr_number} not found in S3 file. Available IDs: {available_ids[:5]}...",
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

    # 5. Extract Files from Solution (Handling Nested Structure)
    # Your JSON has: "solution": { "files": [ ... ] }
    sol_files = []
    if "solution" in solution_pr and "files" in solution_pr["solution"]:
        sol_files = solution_pr["solution"]["files"]
    elif "file_changes" in solution_pr:
        sol_files = solution_pr["file_changes"]

    if not sol_files:
        print("⚠️ No solution files found in the PR object.")

    for submitted_file in submission["file_changes"]:
        file_path = submitted_file["file_path"]
        submitted_code = submitted_file["submitted_code"]

        solution_file = None
        for sol_file in sol_files:
            # Match your JSON's "filename" to the submission's "file_path"
            s_path = sol_file.get("filename") or sol_file.get("file_path")
            if s_path == file_path:
                solution_file = sol_file
                break

        if not solution_file:
            print(f"Warning: No matching solution file found for {file_path}")
            continue

        solution_code = solution_file.get("after_code", "")
        before_code = solution_file.get("before_code", "")

        # Get PR context for better evaluation
        pr_title = solution_pr.get("title", "")
        # Handle your JSON's nested scenario object
        pr_description = (
            solution_pr.get("description", "")
            or solution_pr.get("scenario", {}).get("problem_statement", "")
            or solution_pr.get("scenario", {}).get("context", "")
        )

        similarity_to_solution = calculate_similarity(submitted_code, solution_code)

        print(f"\n{'=' * 80}")
        print(f"Evaluating: {file_path}")
        print(f"{'=' * 80}")

        # STEP 1: Deep Code Analysis (Single Call Optimization)
        combined_prompt = f"""
        You are a senior software engineer conducting a code review for a bug fix/feature challenge.

        **CONTEXT:**
        - Challenge Title: {pr_title}
        - Problem: {pr_description}
        - File: {file_path}

        **CODE COMPARISON:**
        
        1. ORIGINAL CODE (Before):
        {before_code}

        2. EXPECTED SOLUTION (Gold Standard):
        {solution_code}

        3. STUDENT SUBMISSION:
        {submitted_code}

        **TASK:**
        Evaluate the student submission against the expected solution. 
        Note: The student might have different whitespace or variable names, focus on functional equivalence.

        **OUTPUT FORMAT (JSON ONLY):**
        {{
            "bug_fixed": <boolean>,
            "scores": {{
                "correctness": <0-10 score based on logic>,
                "quality": <0-10 score based on code style/safety>,
                "completeness": <0-10 score based on missing requirements>
            }},
            "feedback": {{
                "main_feedback": "<3-4 sentences speaking to the student about their approach>",
                "strengths": ["<strength 1>", "<strength 2>"],
                "improvements": ["<improvement 1>", "<improvement 2>"],
                "suggestions": ["<suggestion 1>"]
            }},
            "critical_issues": ["<critical issue 1>"]
        }}
        """

        try:
            analysis_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a principal software engineer. You provide strict but helpful feedback. Return only valid JSON.",
                    },
                    {"role": "user", "content": combined_prompt},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )

            result = json.loads(analysis_response.choices[0].message.content)

            scores = result.get("scores", {})
            feedback = result.get("feedback", {})

            correctness = float(scores.get("correctness", 0))
            quality = float(scores.get("quality", 0))
            completeness = float(scores.get("completeness", 0))

            file_eval = {
                "file_path": file_path,
                "similarity_to_solution": round(similarity_to_solution * 100, 2),
                "bug_fixed": result.get("bug_fixed", False),
                "correctness_score": correctness,
                "quality_score": quality,
                "completeness_score": completeness,
                "feedback": feedback.get("main_feedback", ""),
                "strengths": feedback.get("strengths", []),
                "improvements": feedback.get("improvements", []),
                "suggestions": feedback.get("suggestions", []),
                "critical_issues": result.get("critical_issues", []),
            }

            file_evaluations.append(file_eval)

            total_correctness += correctness
            total_quality += quality
            total_completeness += completeness
            files_evaluated += 1

            print(f"  ✅ Evaluated {file_path} - Score: {correctness}/10")

        except Exception as e:
            print(f"  ✗ Error evaluating {file_path}: {e}")
            continue

    if files_evaluated == 0:
        # Fallback if no files matched (avoid division by zero)
        print("⚠️ No files were evaluated. Returning 0 score.")
        avg_correctness = 0.0
        avg_quality = 0.0
        avg_completeness = 0.0
        overall_score = 0.0
        summary_text = (
            "No matching files found between submission and solution to evaluate."
        )
    else:
        avg_correctness = total_correctness / files_evaluated
        avg_quality = total_quality / files_evaluated
        avg_completeness = total_completeness / files_evaluated
        overall_score = (avg_correctness + avg_quality + avg_completeness) / 3
        summary_text = f"Evaluation complete. Overall Score: {overall_score:.1f}/10"

    # STEP 4: Generate Overall Summary (Optional - simple logic here to save time/cost)
    # You can add another OpenAI call here if you want a synthesized summary of all files.

    return EvaluationResponse(
        submission_id=request.submission_id,
        pr_number=request.pr_number,
        overall_score=round(overall_score, 2),
        correctness_score=round(avg_correctness, 2),
        code_quality_score=round(avg_quality, 2),
        completeness_score=round(avg_completeness, 2),
        evaluation_summary=summary_text,
        file_evaluations=file_evaluations,
        suggestions=[],  # Populated from individual files in frontend if needed
        strengths=[],
        areas_for_improvement=[],
        evaluated_at=datetime.now().isoformat(),
    )


# ==================== WEBSOCKET HANDLERS ====================

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    if shared.chatbot_instance is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    schema_name = get_user_schema_name(request.username)

    user_repo = shared.get_user_repo(request.username)
    if user_repo:
        owner = user_repo.get("owner")
        repo_name = user_repo.get("name")
        if owner and repo_name:
            if not shared.ensure_chatbot_for_repo(owner, repo_name):
                print(f"⚠ Warning: Could not switch to repo {owner}/{repo_name}")

    async def event_generator():
        try:
            loop = asyncio.get_event_loop()
            queue: asyncio.Queue = asyncio.Queue()

            def run_sync_generator():
                try:
                    gen = shared.chatbot_instance.chat_stream(
                        request.query,
                        schema_name,
                        request.filters,
                        session_id=request.session_id,
                        role=request.role or "general",
                    )
                    for chunk in gen:
                        loop.call_soon_threadsafe(queue.put_nowait, chunk)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    loop.call_soon_threadsafe(
                        queue.put_nowait,
                        {"type": "error", "content": str(e)}
                    )
                finally:
                    loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel

            from concurrent.futures import ThreadPoolExecutor
            executor = ThreadPoolExecutor(max_workers=1)
            loop.run_in_executor(executor, run_sync_generator)

            while True:
                chunk = await queue.get()
                if chunk is None:
                    break
                yield f"data: {json.dumps(chunk)}\n\n"

        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket for streaming responses with GitHub + Gmail support"""

    await websocket.accept()

    if shared.chatbot_instance is None:
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
            session_id = message.get("session_id")
            role = message.get("role", "general")

            if not query:
                await websocket.send_json(
                    {"type": "error", "message": "No query provided"}
                )
                continue

            schema_name = get_user_schema_name(username)

            # Swap to correct repo for this user
            user_repo = shared.get_user_repo(username)
            if user_repo:
                owner = user_repo.get("owner")
                repo_name = user_repo.get("name")
                if owner and repo_name:
                    if not shared.ensure_chatbot_for_repo(owner, repo_name):
                        await websocket.send_json(
                            {
                                "type": "status",
                                "content": f"Warning: Could not switch to repo {owner}/{repo_name}, using current database",
                            }
                        )

            # Stream via chat_stream generator
            try:
                loop = asyncio.get_event_loop()
                gen = shared.chatbot_instance.chat_stream(
                    query,
                    schema_name,
                    message.get("filters"),
                    session_id=session_id,
                    role=role,
                )
                for chunk in gen:
                    await websocket.send_json(chunk)
                    await asyncio.sleep(0) 

            except Exception as stream_err:
                import traceback

                traceback.print_exc()
                await websocket.send_json({"type": "error", "message": str(stream_err)})

    except WebSocketDisconnect:
        print("Client disconnected\n")
    except Exception as e:
        print(f"WebSocket error: {e}\n")
        import traceback

        traceback.print_exc()
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass  # socket already closed, ignore
