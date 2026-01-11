"""
Chat-related API routes for the RAG Chatbot
Contains all chat endpoints and WebSocket handlers
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
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

# Import shared state and utilities from main module
# Note: This creates a circular import, but Python handles it at runtime
# We import these at runtime in the functions that need them

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


# ==================== CHAT ENDPOINTS ====================

@router.get("/")
async def root():
    """Health check and status"""
    from .chatbot_api import chatbot_instance, chatbot_config, available_providers
    
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


@router.get("/health")
async def health_check():
    """Detailed health check"""
    from .chatbot_api import chatbot_instance, chatbot_config, available_providers
    
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
    from .chatbot_api import (
        chatbot_instance,
        chatbot_config,
        get_user_repo,
        ensure_chatbot_for_repo,
    )
    
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


@router.post("/new-session")
async def new_session():
    """Generate a fresh session ID and persist it immediately."""
    from .chatbot_api import chatbot_instance
    
    if chatbot_instance is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    new_session_id = chatbot_instance.start_new_session()
    print(f"🔄 NEW SESSION CREATED AND STORED: {new_session_id}")
    return {"session_id": new_session_id, "message": "New session created"}


@router.post("/clear-history")
async def clear_history(request: ChatRequest):
    """Clear conversation history for specific session"""
    from .chatbot_api import chatbot_instance
    
    if chatbot_instance is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    session_id = chatbot_instance.set_session(request.session_id)
    chatbot_instance.conversation_store.clear_session(session_id)
    print(f"History cleared for session {session_id[:8]}...\n")

    return {"status": "success", "message": "Session history cleared"}


@router.get("/sessions")
async def get_sessions(limit: int = 50):
    """List recent sessions with metadata"""
    from .chatbot_api import chatbot_instance
    
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


@router.get("/load-session/{session_id}")
async def load_session(session_id: str):
    """Load messages for a specific session"""
    from .chatbot_api import chatbot_instance
    
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


@router.delete("/delete-session/{session_id}")
async def delete_session(session_id: str):
    from .chatbot_api import chatbot_instance
    
    if chatbot_instance is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    try:
        chatbot_instance.conversation_store.delete_session(session_id)
        return {"status": "success", "message": "Session deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats():
    """Get chatbot statistics including GitHub and Gmail stats"""
    from .chatbot_api import chatbot_instance
    
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


@router.get("/semantic-cache-stats")
async def get_semantic_cache_stats():
    """Get universal semantic cache statistics with confidence breakdown"""
    from .chatbot_api import chatbot_instance
    
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


@router.post("/invalidate-cache/{session_id}")
async def invalidate_semantic_cache(session_id: str):
    """Invalidate semantic cache for a specific session"""
    from .chatbot_api import chatbot_instance
    
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


@router.post("/clear-all-cache")
async def clear_all_semantic_cache():
    """Clear entire semantic cache (admin operation)"""
    from .chatbot_api import chatbot_instance
    
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


@router.get("/config")
async def get_config():
    """Get current configuration"""
    from .chatbot_api import chatbot_config, available_providers
    
    return {
        "status": "success",
        "config": chatbot_config,
        "available_providers": available_providers,
    }


@router.post("/evaluate-submission", response_model=EvaluationResponse)
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

        # STEP 1: Deep Code Analysis
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
                model="gpt-4o",
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
            print(f"  → Equivalence: {analysis_result.get('equivalence_assessment', 'unknown')}")
            print(f"  → Functional Correctness: {analysis_result['functional_correctness']['score']}/100")

            # STEP 2: Rubric-Based Scoring
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

            print(f"  → Scores: C={correctness_score:.1f} Q={quality_score:.1f} CP={completeness_score:.1f}")

            # STEP 3: Educational Feedback
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
                "equivalence_level": analysis_result.get("equivalence_assessment", "unknown"),
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
                    "completeness": scoring_result.get("completeness_justification", ""),
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

    # STEP 4: Overall Summary
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


# ==================== WEBSOCKET HANDLERS ====================

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket for streaming responses with GitHub + Gmail support"""
    from .chatbot_api import chatbot_instance, get_user_repo, ensure_chatbot_for_repo
    
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

