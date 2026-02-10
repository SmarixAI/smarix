"""
Enterprise-Grade RAG Chatbot v3.6 - S3 OPTIMIZED
Enhanced with Multi-Query Technique, LLM-powered classification, and comprehensive logging
WITH S3 VECTOR DATABASE SUPPORT
"""
import json
import re
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator
from datetime import datetime
import time
import uuid
from dotenv import load_dotenv

load_dotenv()

from core.VectorDB.multi_index_store import MultiIndexVectorStore
from core.ChatBot.query_router import QueryRouter
from core.Memory.conversation_store import ConversationStore
from core.Memory.query_rewriter import LLMQueryRewriter
from core.Memory.semantic_cache_engine import UniversalSemanticCache
from .classifier import ClassifierMixin
from .retrieval import RetrievalMixin
from .llm_embeddings import LLMEmbeddingMixin
from .query_type import QueryType
from .handler import (
    PRHandler, IssueHandler, GreetingHandler, CommitHandler, 
    GeneralQueryHandler, ResponseHandler, TraceabilityHandler, 
    MultiQueryHandler, ChronologicalHandler, CacheHandler
)
from sentence_transformers import SentenceTransformer
from utils.s3 import s3_manager
from core.ChatBot.direct_lookup.pr_lookup import get_pr_lookup
from core.ChatBot.direct_lookup.issue_lookup import get_issue_lookup




S3_BUCKET = "smarix-data-apsouth1"
S3_DEFAULT_REGION = "ap-south-1"


def load_current_repo_from_state():
    """Reads the current active repository from S3 state file"""
    state_s3_key = "Admin/state/runtime_state.json"
    
    try:
        state = s3_manager.download_json(state_s3_key)
        curr_repo = state.get("curr_repo")
        if not curr_repo:
            return None, None
        return curr_repo.get("owner"), curr_repo.get("name")
    except Exception as e:
        print(f"⚠️  Warning: Could not read runtime_state.json from S3: {e}")
        return None, None
    
def update_runtime_state(owner: str, name: str):
    """
    Updates the active repository in the S3 state file.
    Required for Data Processing, Embedding, and VectorDB steps to know which repo to target.
    """
    state_s3_key = "Admin/state/runtime_state.json"
    
    print(f"🔵 Updating S3 runtime state to: {owner}/{name}")
    
    try:
        try:
            state = s3_manager.download_json(state_s3_key)
            if not isinstance(state, dict):
                state = {}
        except Exception:
            state = {}

        state["curr_repo"] = {
            "owner": owner,
            "name": name,
            "updated_at": str(datetime.now())
        }
        
        s3_manager.upload_json(state, state_s3_key)
        print("✅ Runtime state updated successfully in S3")
        
        return {
            "success": True, 
            "message": f"State updated to {owner}/{name}"
        }

    except Exception as e:
        error_msg = f"Failed to update runtime state: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False, 
            "error": error_msg
        }

class RAGChatbot(ClassifierMixin, RetrievalMixin, LLMEmbeddingMixin):

    
    def __init__(
        self,
        vector_db_path: str,
        gmail_db_path: Optional[str] = None,
        provider: str = "openai",
        model: Optional[str] = None,
        temperature: float = 0.7,
        top_k: int = 5,
        use_hybrid_retrieval: bool = True,
        verbose: bool = False,
        log_file: Optional[str] = None,
        enable_multi_query: bool = False,
        routing_method: str = "llm",  # Default to LLM-based routing for better accuracy
        repo_owner: Optional[str] = None,  # Repository owner for filtering
        repo_name: Optional[str] = None,    # Repository name for filtering
        disable_conversation_storage: bool = False  # Set to True to skip conversation storage (useful for generators)
    ):
        self.repo_owner, self.repo_name = load_current_repo_from_state()
        if not self.repo_owner and verbose:
            print("Warning: Repository state not found. Graph features (Impact Analysis) will be disabled.")
        self.vector_db_path = vector_db_path
        self.gmail_db_path = gmail_db_path
        self.provider = provider
        self.temperature = temperature
        self.top_k = top_k
        self.use_hybrid_retrieval = use_hybrid_retrieval
        self.verbose = verbose
        self.enable_multi_query = enable_multi_query
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        # Store repo_name string for filtering
        self.repo_full_name = f"{repo_owner}/{repo_name}" if repo_owner and repo_name else None

        self.cache_hints = None

        # Initialize multi-index store or single DB
        self.multi_index_store = None
        
        # Try to load multi-index store
        try:
            if self.verbose:
                print(f"Loading multi-index store: {vector_db_path}")
            # Try to detect dimension from existing index config
            # Default to 1536 (OpenAI) to match single-index, but will be updated when loading
            self.multi_index_store = MultiIndexVectorStore(
                base_dir=vector_db_path,
                dimension=1536,  # Default to OpenAI dimension (matches single-index)
                index_type="flat",
                metric="cosine"
            )
            self.multi_index_store.load(vector_db_path)

            self.vector_db = self.multi_index_store
            
            # Initialize query router (embedding model will be set after embedding initialization)
            self.query_router = QueryRouter(
                routing_method=routing_method,
                embedding_model=None,  # Will be set after embedding initialization
                llm_client=None  # Will be set after LLM initialization
            )
            
            if self.verbose:
                stats = self.multi_index_store.get_statistics()
                print(f"Multi-index loaded: {stats['total_indices']} indices, {stats['total_vectors']} vectors")
        except Exception as e:
            print(f"❌ Error: Failed to load multi-index store: {e}")
            print("💡 Tip: Ensure multi-index is built using build_indices.py")
            
            
        
        # Load Gmail database (optional, single-index for Gmail only)
        self.gmail_db = None
        if gmail_db_path and os.path.exists(gmail_db_path):
            try:
                if self.verbose:
                    print(f"Loading Gmail database: {gmail_db_path}")
                from core.VectorDB.vector_db.faiss_db import FAISSVectorDB
                self.gmail_db = FAISSVectorDB.load(gmail_db_path)
            except Exception as e:
                print(f"⚠️  Could not load Gmail database: {e}")
                self.gmail_db = None 

        # Initialize embeddings - detect dimension from loaded index
        self.initialize_embeddings()
        self.model = model or self.get_default_model()
        self.initialize_llm()
        
        # Set embedding model and LLM client for router if using multi-index
        if hasattr(self, 'query_router'):
            # Initialize embedding model for router if using sentence-transformers
            if self.embedding_provider == 'sentence-transformers':
                try:
                    self.query_router.embedding_model = SentenceTransformer(self.embedding_model)
                except ImportError:
                    if self.verbose:
                        print("Warning: sentence-transformers not available for router, using keyword routing")
                    self.query_router.routing_method = "keyword"
            self.query_router.llm_client = self.client if hasattr(self, 'client') else None
        
        self.setup_logging(log_file)

        memory_db_url = os.getenv("MEMORY_DB_URL", "")
        # Use SQLite if no PostgreSQL URL is provided
        if not memory_db_url or not memory_db_url.startswith("postgresql://"):
            # Use SQLite for local development
            from pathlib import Path
            db_path = Path(__file__).parent.parent.parent.parent / "data" / "local_db.sqlite"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            memory_db_url = f"sqlite:///{db_path}"
        
        # Try to initialize conversation store, but make it optional if database is not available
        # Or skip entirely if disable_conversation_storage is True (for generator scripts)
        if disable_conversation_storage:
            # Create a dummy conversation store that does nothing
            class DummyConversationStore:
                def create_session(self, *args, **kwargs): return None
                def add_message(self, *args, **kwargs): return None
                def get_full_history(self, *args, **kwargs): return []
                def clear_session(self, *args, **kwargs): pass
                def get_session_stats(self, *args, **kwargs): return {}
                def get_all_sessions(self, *args, **kwargs): return []
                def delete_session(self, *args, **kwargs): pass
                def session_exists(self, *args, **kwargs): return False
            self.conversation_store = DummyConversationStore()
            if self.verbose:
                print("ℹ️  Conversation storage disabled (generator mode)")
        else:
            try:
                self.conversation_store = ConversationStore(memory_db_url)
            except Exception as e:
                if self.verbose:
                    print(f"⚠️  Warning: Could not connect to conversation database: {e}")
                    print("   Conversation history will not be persisted, but chatbot will still work.")
                # Create a dummy conversation store that does nothing
                class DummyConversationStore:
                    def create_session(self, *args, **kwargs): return None
                    def add_message(self, *args, **kwargs): return None
                    def get_full_history(self, *args, **kwargs): return []
                    def clear_session(self, *args, **kwargs): pass
                    def get_session_stats(self, *args, **kwargs): return {}
                    def get_all_sessions(self, *args, **kwargs): return []
                    def delete_session(self, *args, **kwargs): pass
                    def session_exists(self, *args, **kwargs): return False
                self.conversation_store = DummyConversationStore()

        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_db = int(os.getenv("REDIS_DB", "0"))
        redis_password = os.getenv("REDIS_PASSWORD")
        
        # Check if Redis is explicitly required (if not set, it's optional for local dev)
        redis_required = os.getenv("REDIS_REQUIRED", "false").lower() == "true"

        try:
            from core.Memory.redis_client import RedisClient
            self.redis_client = RedisClient(redis_host, redis_port, redis_db, redis_password)
            self.logger.info("Redis context cache ENABLED - DB: %s" % redis_db)
        except Exception as e:
            # Only log warning if Redis is explicitly required, otherwise silently disable for local dev
            if redis_required:
                self.logger.warning(f"Redis unavailable, disabling cache: {e}")
            # Suppress warning for local development - Redis is optional
            self.redis_client = None

        self.query_rewriter = LLMQueryRewriter(
            self.conversation_store,
            self.client,
            self.redis_client,
            embedding_function=self.get_query_embedding
        )
        # Initialize handlers
        self.cache_handler = CacheHandler(self)
        self.pr_handler = PRHandler(self)
        self.issue_handler = IssueHandler(self)
        self.greeting_handler = GreetingHandler(self)
        self.commit_handler = CommitHandler(self)
        self.general_query_handler = GeneralQueryHandler(self)
        self.response_handler = ResponseHandler(self)
        self.traceability_handler = TraceabilityHandler(self)
        self.chronological_handler = ChronologicalHandler(self)
        self.multi_query_handler = MultiQueryHandler(self)

        self.current_session_id: Optional[str] = None

        self.history: List[Dict[str, Any]] = []
        self.repo_info = self.load_repo_info()
        self.repo_metrics = self.load_repository_metrics()

        # Initialize PR JSON direct lookup
        self.pr_lookup = get_pr_lookup()

        if self.pr_lookup and self.pr_lookup.is_loaded():
            self.logger.info("PR_DIRECT_LOOKUP | Loaded successfully")
        else:
            self.logger.warning("PR_DIRECT_LOOKUP | NOT loaded or empty")

        
        # Initialize Issue JSON direct lookup
        self.issue_lookup = get_issue_lookup()

        if self.issue_lookup and self.issue_lookup.is_loaded():
            self.logger.info("ISSUE_DIRECT_LOOKUP | Loaded successfully")
        else:
            self.logger.warning("ISSUE_DIRECT_LOOKUP | NOT loaded or empty")



        print("=" * 70)
        print("ENTERPRISE RAG CHATBOT v3.6 (Multi-Index)")
        print("=" * 70)
        if self.multi_index_store:
            try:
                stats = self.multi_index_store.get_statistics()
                print(f"✅ Multi-Index: {stats['total_indices']} indices, {stats['total_vectors']} vectors")
                for idx_type, idx_stats in stats['by_index'].items():
                    if 'total_vectors' in idx_stats:
                        print(f"   {idx_type}: {idx_stats['total_vectors']} vectors")
            except Exception as e:
                print(f"Multi-Index: (unable to read stats: {e})")
        elif self.db:
            try:
                print(f"GitHub: {self.db.index.ntotal} vectors")
            except Exception:
                print("GitHub: (unable to read ntotal)")
        if self.gmail_db:
            try:
                print(f"Gmail: {self.gmail_db.index.ntotal} emails")
            except Exception:
                print("Gmail: (unable to read ntotal)")
        if self.repo_metrics:
            print(f"Repository Metrics: Loaded")
            summary = self.repo_metrics.get('summary', {})
            print(f"  Repositories: {summary.get('total_repositories', 0)}")
            print(f"  Code Lines: {summary.get('total_code_lines', 0):,}")
            print(f"  Functions: {summary.get('total_functions', 0)}")
            print(f"  Classes: {summary.get('total_classes', 0)}")
        else:
            print(f"Repository Metrics: Not found")
        print(f"Provider: {self.provider}")
        print(f"Model: {self.model}")
        print(f"Retrieval: {'Hybrid' if self.use_hybrid_retrieval else 'Semantic'} (top-{self.top_k})")
        print(f"Multi-Query: {'Enabled' if self.enable_multi_query else 'Disabled'}")
        print(f"Multi-Index: Enabled (routing: {self.query_router.routing_method if hasattr(self, 'query_router') else 'N/A'})")
        if log_file:
            print(f"Logging: {log_file}")
        print("=" * 70)

    def _ensure_session(self, session_id: Optional[str] = None, schema_name: str = None) -> str:
        if not schema_name:
             self.logger.warning("No schema_name provided to _ensure_session")
             
        if session_id:
            if not self.conversation_store.session_exists(session_id, schema_name=schema_name):
                self.conversation_store.create_session(session_id, schema_name=schema_name)
            self.current_session_id = session_id
            return session_id

        if self.current_session_id:
            if not self.conversation_store.session_exists(self.current_session_id, schema_name=schema_name):
                 self.conversation_store.create_session(self.current_session_id, schema_name=schema_name)
            return self.current_session_id

        new_id = str(uuid.uuid4())
        self.conversation_store.create_session(new_id, schema_name=schema_name)
        self.current_session_id = new_id
        return new_id
    
    def retrieve_raw_chunks(
        self,
        query_text: str,
        top_k: int = 30,
        query_type: str = QueryType.QUESTION_GENERATION,
    ):
        """
        RAW retrieval for generators (practice, onboarding, analysis).
        Bypasses chat flow but still respects multi-index routing.
        """

        # 1. Build embedding
        query_embedding = self.get_query_embedding(query_text)

        # 2. Minimal safe defaults
        entity = None
        keywords = query_text.lower().split()

        # 3. Call canonical multi-index retrieval
        return self._retrieve_multi_index(
            query_embedding=query_embedding,
            query_type=query_type,
            entity=entity,
            keywords=keywords,
            top_k=top_k,
            query_text=query_text,
        ) or []
    
    from .query_type import QueryType

    def retrieve(self, query: str, top_k: int = 20):
        """
        Lightweight retrieval API for generators and tools.
        SAFE wrapper over multi-index retrieval.
        """

        query_embedding = self.get_query_embedding(query)

        return self._retrieve_multi_index(
            query_embedding=query_embedding,
            query_type=QueryType.QUESTION_GENERATION,
            entity=None,
            keywords=query.lower().split(),
            top_k=top_k,
            query_text=query
        ) or []

    def start_new_session(self, schema_name: str) -> str:
        """Create a new empty session in DB and set it as current."""
        self.current_session_id = None
        # Pass schema_name
        new_session_id = self._ensure_session(None, schema_name=schema_name)

        try:
            # Pass schema_name
            self.conversation_store.create_session(new_session_id, schema_name=schema_name, user_id=None, metadata={})
            self.logger.info(f"CONVERSATION_STORE | Created new conversation row for {new_session_id[:8]} in {schema_name}...")
        except Exception as e:
            self.logger.error(f"CONVERSATION_STORE | Failed to create new session row: {e}")

        return new_session_id

    def set_session(self, session_id: Optional[str], schema_name: str) -> str:
        return self._ensure_session(session_id, schema_name)

    def get_session_id(self) -> Optional[str]:
        return self.current_session_id

    def setup_logging(self, log_file: Optional[str] = None):
        if log_file is None:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / f"chatbot_{datetime.now().strftime('%Y%m%d')}.log"

        self.logger = logging.getLogger("RAGChatbot")
        self.logger.setLevel(logging.INFO)

        if self.logger.handlers:
            self.logger.handlers.clear()

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.info("=" * 80)
        self.logger.info("RAG Chatbot Session Started")
        self.logger.info("=" * 80)


    def chat(self, query: str, schema_name: str, filters: Optional[Dict] = None, session_id: Optional[str] = None, role: Optional[str] = None) -> Dict[str, Any]:
        if role is None:
            role = "general"

        is_subquery = filters.get("is_subquery", False) if filters else False

        def save_assistant_message(result_data):
            """Helper to save assistant response once before returning"""
            if result_data and not is_subquery:
                try:
                    self.conversation_store.add_message(
                        active_session_id, "assistant", result_data.get("answer", ""), 
                        schema_name=schema_name, tokens_used=result_data.get("tokens_used", 0)
                    )
                except Exception as e:
                    self.logger.error(f"CONVERSATION_STORE | Failed to save assistant message: {e}")
            return result_data
        
        self.logger.info("=" * 80)
        self.logger.info(f"NEW QUERY | {query}")
        active_session_id = self._ensure_session(session_id, schema_name=schema_name)

        if not is_subquery:
            try:
                self.conversation_store.add_message(
                    active_session_id, "user", query, schema_name=schema_name, tokens_used=0
                )
            except Exception as e:
                self.logger.error(f"CONVERSATION_STORE | Failed to save user message: {e}")

        # STEP 1: UPDATE CACHE AGES (runs periodically)
        self.cache_handler.update_cache_ages()

        # STEP 2: SEMANTIC CACHE CHECK FIRST (RAW QUERY - CRITICAL FIX)
        self.logger.info(f"CACHE LOOKUP | raw='{query[:60]}...' | session={active_session_id[:8]}")
        cached_result = self.cache_handler.get_semantic_cache(query, active_session_id)

        if cached_result:
            result = self.cache_handler.handle_cached_result(cached_result, query, active_session_id, schema_name=schema_name)
            if result:
                self.logger.info(f"DIRECT CACHE HIT | confidence={result.get('cache_confidence', 'N/A')}")
                return save_assistant_message(result)
            # If handle_cached_result returned None, it means requires_generation
            # Skip old cache and proceed to RAG
            self.logger.info(f"Semantic cache requires generation, skipping old cache")
        else:
            # STEP 3: OLD CACHE CHECK (only if NO semantic cache result)
            cached_response = self.cache_handler.get_response_cache(query, active_session_id)
            if cached_response:
                # Check if this is a failure response (no context found)
                answer = cached_response.get('answer', '')
                is_failure = (
                    len(answer) < 150 or
                    'no information' in answer.lower() or
                    'no context' in answer.lower() or
                    "don't have" in answer.lower() or
                    'not found' in answer.lower()
                )
                
                if is_failure:
                    self.logger.info(f"OLD CACHE HIT but response is failure, skipping cache")
                else:
                    self.logger.info(f"OLD CACHE HIT | Returning cached response (legacy)")
                    return save_assistant_message(cached_response)

        query_lower = query.lower()

        if self.verbose:
            print(f"\n{'=' * 70}")
            print(f"Query: {query}")
            print(f"{'=' * 70}")

        # STEP 0: Check for greetings FIRST (before any rewriting)
        if self.is_greeting(query):
            query_type = QueryType.GREETING
            self.logger.info("CLASSIFICATION | Rule-based: GREETING (detected early)")
            return save_assistant_message(self.greeting_handler.handle_greeting(query, query_type, active_session_id, schema_name=schema_name))

        # Early entity detection to decide if rewriting is needed
        has_pr = bool(re.search(r'\bPR\s*#?\s*\d+|\bpull request\s*#?\s*\d+', query, re.IGNORECASE))
        has_issue = bool(re.search(r'\bissue\s*#?\s*\d+|\bbug\s*#?\s*\d+', query, re.IGNORECASE))
        has_commit = bool(re.search(r'\b[a-f0-9]{7,40}\b', query, re.IGNORECASE))

        skip_rewrite = has_pr or has_issue or has_commit

        # SESSION CONTEXT REWRITING (skip for PR/Issue/Commit queries)
        if active_session_id and not skip_rewrite:
            session_context_query = self.query_rewriter.rewrite(query, active_session_id, schema_name=schema_name)
            if session_context_query and session_context_query != query:
                self.logger.info(f"SESSION REWRITE | '{query}' -> '{session_context_query}'")
                if self.verbose:
                    print(f"Session Context: {session_context_query}")
                rewritten_query = session_context_query
            else:
                rewritten_query = query
        else:
            if skip_rewrite:
                self.logger.info(f"SKIP REWRITE | Direct entity lookup query (PR/Issue/Commit)")
            rewritten_query = query

        # STEP 2: Expand query (for context from conversation history)
        #         Adds context from previous messages if needed
        expanded_query = self.expand_query(rewritten_query)
        if expanded_query != rewritten_query:
            self.logger.info(f"QUERY EXPANSION | Rewritten: '{rewritten_query}' -> Expanded: '{expanded_query}'")
        else:
            expanded_query = rewritten_query

        query_lower = expanded_query.lower()

        # MULTI-QUESTION DETECTION (run only for main call, not recursive subqueries)
        if not filters or not filters.get("is_subquery"):
            if self.enable_multi_query:
                subqueries = self.multi_query_handler.split_into_subqueries(query)
                if len(subqueries) > 1:
                    self.logger.info(f"MULTI-QUERY | Detected {len(subqueries)} sub-questions")
                    return save_assistant_message(self.multi_query_handler.handle_multi_query(subqueries, query, active_session_id, schema_name=schema_name))

        # STEP 3: Classify query into QueryType (using rewritten/expanded query)
        #Determines query category: HOW_TO, FILE_LOOKUP, CONCEPTUAL, etc.
        query_type = self.classify_query(expanded_query)

        # Direct lookup for Issue / PR numbers (skip semantic search)
        entity = self.extract_entity_from_query(expanded_query, query_type)
        if query_type == QueryType.PR_ISSUE_TUTORIAL and entity:
            self.logger.info(
                f"PR-ISSUE TUTORIAL | Detected tutorial request for {entity['type']} #{entity['number']}"
            )

            result = self.pr_handler.handle_pr_issue_tutorial(entity, query, expanded_query)

            # CRITICAL: Store RAW query, not expanded
            self.cache_handler.update_caches(query, result, active_session_id)

            return save_assistant_message(result)

        if query_type == QueryType.PR_ISSUE_CODING_QUESTION and entity:
            self.logger.info(
                f"PR-ISSUE CODING QUESTION | Detected coding question request for {entity['type']} #{entity['number']}"
            )

            result = self.pr_handler.handle_pr_issue_coding_question(entity, query, expanded_query)

            # CRITICAL: Store RAW query
            self.cache_handler.update_caches(query, result, active_session_id)

            return save_assistant_message(result)


        # DIRECT LOOKUP - Issue (JSON O(1) FIRST)
        if entity and entity.get("type") == "issue":

            issue_number = entity.get("number")

            # 1️⃣ Try JSON direct lookup first
            if self.issue_lookup:
                direct_issue = self.issue_lookup.lookup_by_number(issue_number)
            else:
                direct_issue = None

            if direct_issue:
                self.logger.info(f"ISSUE_DIRECT_LOOKUP | HIT for Issue #{issue_number}")

                wrapped_chunk = {
                    "source": "direct_lookup",
                    "content": direct_issue,
                    "score": 1.0
                }

                result = self._respond_with_results(
                    [wrapped_chunk],
                    QueryType.ISSUE_SPECIFIC,
                    query,
                    expanded_query,
                    role=role
                )

                self.cache_handler.update_caches(query, result, active_session_id)
                return save_assistant_message(result)

            else:
                self.logger.info(f"ISSUE_DIRECT_LOOKUP | MISS for Issue #{issue_number}")

                # 2️⃣ Fallback to metadata-based handler
                result = self.issue_handler.handle_issue_direct_lookup(
                    entity, query, expanded_query, query_type, active_session_id, role=role
                )

                if result:
                    self.cache_handler.update_caches(query, result, active_session_id)
                    return save_assistant_message(result)


        # DIRECT LOOKUP - PR (JSON-based O(1) lookup FIRST)
        if entity and entity.get("type") == "pr":

            pr_number = entity.get("number")

            # 1️⃣ Try JSON direct lookup first
            if self.pr_lookup:
                direct_pr = self.pr_lookup.lookup_by_number(pr_number)
            else:
                direct_pr = None

            if direct_pr:
                self.logger.info(f"PR_DIRECT_LOOKUP | HIT for PR #{pr_number}")

                wrapped_chunk = {
                    "source": "direct_lookup",
                    "content": direct_pr,
                    "score": 1.0
                }

                result = self._respond_with_results(
                    [wrapped_chunk],
                    QueryType.PR_SPECIFIC,
                    query,
                    expanded_query,
                    role=role
                )

                self.cache_handler.update_caches(query, result, active_session_id)
                return save_assistant_message(result)

            else:
                self.logger.info(f"PR_DIRECT_LOOKUP | MISS for PR #{pr_number}")

                # 2️⃣ Fallback to existing metadata-based handler
                result = self.pr_handler.handle_pr_direct_lookup(
                    entity, query, expanded_query, active_session_id, role=role
                )

                if result:
                    self.cache_handler.update_caches(query, result, active_session_id)
                    return save_assistant_message(result)


        # DIRECT LOOKUP - Commit
        if entity and entity.get("type") == "commit":
            result = self.commit_handler.handle_commit_direct_lookup(
                entity, query, expanded_query, query_type, active_session_id, role=role
            )
            if result:
                # Store RAW query if result found
                self.cache_handler.update_caches(query, result, active_session_id)
                return save_assistant_message(result)

        self.logger.info(f"QUERY TYPE | {query_type}")

        if query_type == QueryType.RANDOM_PR_GENERATOR:
            self.logger.info("RANDOM PR GENERATOR | Will retrieve merged PRs with code changes for LLM selection")

        raw_num = re.search(r'\b(\d+)\b', expanded_query.lower())
        pr_results = None  

        # Handle PR override
        if raw_num and (
            query_type == QueryType.PR_SPECIFIC
            or "pr" in query_lower
            or "pull request" in query_lower
            or "merge request" in query_lower
            or "mr" in query_lower
        ):
            result = self.pr_handler.handle_pr_override(
                raw_num, query, expanded_query, query_lower, query_type, active_session_id, role=role, schema_name=schema_name
            )
            if result:
                # Store RAW query
                self.cache_handler.update_caches(query, result, active_session_id)
                return save_assistant_message(result)
            # Mark that we tried to find PR but didn't find it
            pr_results = False

        # FINAL STOP: If PR is not found in metadata, do NOT do semantic search
        if query_type == QueryType.PR_SPECIFIC and raw_num and pr_results is False:
            result = self.pr_handler.handle_pr_not_found(raw_num, query_type, query, active_session_id)
            if result:
                # Even "not found" gets cached (exact match case)
                self.cache_handler.update_caches(query, result, active_session_id)
                return save_assistant_message(result)

        # Handle Issue override
        issue_results = None
        if raw_num and (
            query_type == QueryType.ISSUE_SPECIFIC
            or "issue" in query_lower
            or "bug" in query_lower
            or "ticket" in query_lower
            or "report" in query_lower
        ):
            result = self.issue_handler.handle_issue_override(
                raw_num, query, expanded_query, query_type, active_session_id, role=role, schema_name=schema_name
            )
            if result:
                # Store RAW query
                self.cache_handler.update_caches(query, result, active_session_id)
                return save_assistant_message(result)
            # Mark that we tried to find Issue but didn't find it
            issue_results = False

        # FINAL STOP: If Issue is not found in metadata, do NOT do semantic search
        if query_type == QueryType.ISSUE_SPECIFIC and raw_num and issue_results is False:
            result = self.issue_handler.handle_issue_not_found(raw_num, query_type, query, active_session_id)
            if result:
                # Store RAW query
                self.cache_handler.update_caches(query, result, active_session_id)
                return save_assistant_message(result)

        # Guaranteed COMMIT direct lookup override
        raw_sha = re.search(r'\b([a-f0-9]{7,40})\b', expanded_query.lower())
        if query_type == QueryType.COMMIT_SPECIFIC and raw_sha:
            result = self.commit_handler.handle_commit_override(
                raw_sha, query, expanded_query, query_lower, query_type, active_session_id, role=role, schema_name=schema_name
            )
            if result:
                # Store RAW query
                self.cache_handler.update_caches(query, result, active_session_id)
                return save_assistant_message(result)
            
            # If commit not found, handle not found case
            result = self.commit_handler.handle_commit_not_found(raw_sha, query_type, query, active_session_id)
            if result:
                # Store RAW query
                self.cache_handler.update_caches(query, result, active_session_id)
                return save_assistant_message(result)

        # STEP 4: Query routing happens in _retrieve_multi_index() using expanded_query
        #         Routes to appropriate index: docs, code, prs, commits, or combined
        #         Then searches both routed index AND combined index, merges results
        if query_type == QueryType.GREETING:
            return save_assistant_message(self.greeting_handler.handle_greeting(query, query_type, active_session_id, schema_name=schema_name))

        chrono_query = self.detect_chronological_query(expanded_query)

        # prepare commonly used variables
        entity = None
        keywords = self.extract_keywords(expanded_query)
        metrics_context = None

        if chrono_query:
            result = self.chronological_handler.handle_chronological(
                chrono_query, query, expanded_query, active_session_id, role=role, schema_name=schema_name
            )
            if result:
                # Store RAW query
                self.cache_handler.update_caches(query, result, active_session_id)
                return save_assistant_message(result)
            
        if query_type == QueryType.TRACEABILITY and entity:
            result = self.traceability_handler.handle_traceability(
                entity, query, expanded_query, active_session_id, role=role, schema_name=schema_name
            )
            if result:
                # Store RAW query
                self.cache_handler.update_caches(query, result, active_session_id)
                return save_assistant_message(result)

        # Non-chronological / general flow
        result = self.general_query_handler.handle_general_query(
            query, expanded_query, query_type, entity, keywords, active_session_id, role=role, schema_name=schema_name
        )
        # Store RAW query for general queries too
        self.cache_handler.update_caches(query, result, active_session_id)

        return save_assistant_message(result)

    def _respond_with_results(
        self,
        github_results,
        query_type,
        query,
        expanded_query,
        role: Optional[str] = None
    ):
        return self.response_handler.respond_with_results(
            github_results,
            query_type,
            query,
            expanded_query,
            role=role,
            intent=None
        )


    def split_into_subqueries(self, query: str) -> List[str]:
        """
        Split query into sub-questions ONLY if clearly multi-part.
        Returns list with 2-3 questions, or single-item list.
        """
        return self.multi_query_handler.split_into_subqueries(query)

    def handle_multi_query(self, subqueries: List[str], original_query: str, session_id: str, schema_name: str) -> Dict[str, Any]:
        """
        Process multiple sub-queries and merge results into SINGLE response.
        CRITICAL: Pass filters={'is_subquery': True} to skip rewrite/multi-query recursion.
        """
        return self.multi_query_handler.handle_multi_query(subqueries, original_query, session_id, schema_name=schema_name)

    def merge_multi_answers(self, results: List[Dict[str, Any]], original_query: str) -> Dict[str, Any]:
        """
        Merge multiple sub-query results into a SINGLE coherent response.
        Returns a properly formatted response dict (not fragmented UI messages).
        """
        return self.response_handler.merge_multi_answers(results, original_query)

    def _package_response(self, answer, github_results, email_results, query_type):
        return self.response_handler.package_response(answer, github_results, email_results, query_type)


    def chat_stream(self, query: str, filters: Optional[Dict] = None, role: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        self.logger.info("=" * 80)
        self.logger.info(f"NEW STREAM QUERY | {query}")

        active_session_id = self._ensure_session(None)

        if self.verbose:
            print(f"\n{'=' * 70}")
            print(f"Query (streaming): {query}")
            print(f"{'=' * 70}")

        # MULTI-QUERY DETECTION (EARLY)
        if not filters or not filters.get("is_subquery"):
            if self.enable_multi_query:
                subqueries = self.multi_query_handler.split_into_subqueries(query)
                if len(subqueries) > 1:
                    self.logger.info(f"MULTI-QUERY | Detected {len(subqueries)} sub-questions")
                    return self.multi_query_handler.handle_multi_query(
                        subqueries, query, active_session_id
                    )


        yield {'type': 'status', 'content': 'Analyzing query...'}
        expanded_query = self.expand_query(query)

        query_type = self.classify_query(expanded_query)
        entity = self.extract_entity_from_query(expanded_query, query_type)


        if query_type == QueryType.RANDOM_PR_GENERATOR:
            self.logger.info("RANDOM PR GENERATOR | Will retrieve merged PRs with code changes for LLM selection")

        if query_type == QueryType.GREETING:
            for response in self.greeting_handler.handle_greeting_stream(query, query_type):
                yield response
            return

        chrono_query = self.detect_chronological_query(expanded_query)

        if chrono_query:
            for response in self.chronological_handler.handle_chronological_stream(
                chrono_query, query, expanded_query, active_session_id, role=role
            ):
                yield response
            return

        if self.verbose:
            print(f"Query Type: {query_type}")

        entity = self.extract_entity_from_query(expanded_query, query_type)
        keywords = self.extract_keywords(expanded_query)

        # Use general query handler for streaming
        for response in self.general_query_handler.handle_general_query_stream(
            query, expanded_query, query_type, entity, keywords, role=role
        ):
            yield response


    def clear_history(self):
        self.history = []
        self.logger.info("HISTORY | Cleared conversation history")


    def get_stats(self) -> Dict[str, Any]:
        stats = {
            'total_chunks': self.repo_info.get('total_chunks', 0),
            'conversation_length': len(self.history) // 2,
            'has_metrics': bool(self.repo_metrics),
            'multi_query_enabled': self.enable_multi_query,
            'features': [
                'Multi-Query Technique',
                'LLM-powered query classification',
                'Dynamic query-aware prompts',
                'Zero hallucination enforcement',
                'GitHub-first retrieval',
                'Gmail correlation',
                'Repository metrics intelligence',
                'Tech stack analysis',
                'Structure insights',
                'Query expansion',
                'Diagram generation',
                'Grammar correction',
                'Chronological entity retrieval',
                'Streaming responses',
                'Extended code context',
                'Greeting detection',
                'Self-verification',
                'Comprehensive logging',
                'PR/Issue Tutorial Generation',
                'PR/Issue Coding Question Generation',
                'Random PR Generator'
            ]
        }

        if self.gmail_db:
            try:
                stats['gmail_indexed'] = self.gmail_db.index.ntotal
            except Exception:
                stats['gmail_indexed'] = None

        if self.repo_metrics:
            summary = self.repo_metrics.get('summary', {})
            stats['metrics_summary'] = {
                'total_repositories': summary.get('total_repositories', 0),
                'total_code_lines': summary.get('total_code_lines', 0),
                'total_functions': summary.get('total_functions', 0),
                'total_classes': summary.get('total_classes', 0)
            }

        return stats


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Enterprise RAG Chatbot v3.6")
    parser.add_argument('--db', required=True, help='GitHub vector DB path')
    parser.add_argument('--gmail-db', help='Gmail vector DB path')
    parser.add_argument('--provider', default='openai', choices=['openai', 'anthropic', 'ollama'])
    parser.add_argument('--model', help='Model name')
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--log-file', help='Log file path')
    parser.add_argument('--disable-multi-query', action='store_true', help='Disable multi-query technique')

    args = parser.parse_args()

    chatbot = RAGChatbot(
        vector_db_path=args.db,
        gmail_db_path=args.gmail_db,
        provider=args.provider,
        model=args.model,
        verbose=args.verbose,
        log_file=args.log_file,
        enable_multi_query=not args.disable_multi_query
    )


    while True:
        try:
            query = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break

        if not query:
            continue
        if query == 'exit':
            break
        if query == 'clear':
            chatbot.clear_history()
            print("History cleared")
            continue
        if query == 'stats':
            print(json.dumps(chatbot.get_stats(), indent=2))
            continue
        if query == 'cache-stats':
            cache_stats = chatbot.cache_handler.get_cache_stats()
            if cache_stats:
                print(json.dumps(cache_stats, indent=2))
            else:
                print("Semantic cache not enabled")
            continue


        response = chatbot.chat(query)
        print(f"\n{response['answer']}\n")

        if response.get('chronological_entity'):
            print(f"[Chronological: {response['chronological_entity']}]")
        elif response.get('is_metrics_query'):
            print("[Metrics Query]")
        elif response['emails']:
            print(f"[{len(response['emails'])} related emails]")

        print(f"[Type: {response['query_type']}, Quality: {response['context_quality']:.2f}]\n")

    

if __name__ == "__main__":
    main()
