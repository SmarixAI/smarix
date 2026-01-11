"""
Enterprise-Grade RAG Chatbot v3.6
Enhanced with Multi-Query Technique, LLM-powered classification, and comprehensive logging
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
from sentence_transformers import SentenceTransformer


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
        routing_method: str = "llm"  # Default to LLM-based routing for better accuracy
    ):
        self.vector_db_path = vector_db_path
        self.gmail_db_path = gmail_db_path
        self.provider = provider
        self.temperature = temperature
        self.top_k = top_k
        self.use_hybrid_retrieval = use_hybrid_retrieval
        self.verbose = verbose
        self.enable_multi_query = enable_multi_query

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

        try:
            from core.Memory.redis_client import RedisClient
            self.redis_client = RedisClient(redis_host, redis_port, redis_db, redis_password)
            self.logger.info("Redis context cache ENABLED - DB: %s" % redis_db)
        except Exception as e:
            self.logger.warning(f"Redis unavailable, disabling cache: {e}")
            self.redis_client = None

        self.query_rewriter = LLMQueryRewriter(
            self.conversation_store,
            self.client,
            self.redis_client,
            embedding_function=self.get_query_embedding
        )
        self._last_semantic_cache_age_update = time.time()

        self.current_session_id: Optional[str] = None

        self.history: List[Dict[str, Any]] = []
        self.repo_info = self.load_repo_info()
        self.repo_metrics = self.load_repository_metrics()

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

    def _ensure_session(self, session_id: Optional[str] = None) -> str:
        if session_id:
            if not self.conversation_store.session_exists(session_id):
                self.conversation_store.create_session(session_id)
            self.current_session_id = session_id
            return session_id

        if self.current_session_id:
            return self.current_session_id

        new_id = str(uuid.uuid4())
        self.conversation_store.create_session(new_id)
        self.current_session_id = new_id
        return new_id

    def start_new_session(self) -> str:
        """Create a new empty session in DB and set it as current."""
        # force new id
        self.current_session_id = None
        new_session_id = self._ensure_session(None)

        try:
            self.conversation_store.create_session(new_session_id, user_id=None, metadata={})
            self.logger.info(f"CONVERSATION_STORE | Created new conversation row for {new_session_id[:8]}...")
        except Exception as e:
            self.logger.error(f"CONVERSATION_STORE | Failed to create new session row: {e}")

        return new_session_id

    def set_session(self, session_id: Optional[str]) -> str:
        return self._ensure_session(session_id)

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


    def chat(self, query: str, filters: Optional[Dict] = None, session_id: Optional[str] = None, role: Optional[str] = None) -> Dict[str, Any]:
        if role is None:
            role = "general"
        
        self.logger.info("=" * 80)
        self.logger.info(f"NEW QUERY | {query}")
        active_session_id = self._ensure_session(session_id)

        # STEP 1: UPDATE CACHE AGES (runs periodically)
        if self.query_rewriter and self.query_rewriter.semantic_cache:
            current_time = time.time()
            if current_time - self._last_semantic_cache_age_update > 300:
                self.query_rewriter.semantic_cache.update_ages()
                self._last_semantic_cache_age_update = current_time

        # STEP 2: SEMANTIC CACHE CHECK (uses ORIGINAL query)
        if self.query_rewriter and self.query_rewriter.semantic_cache:
            cached_result = self.query_rewriter.semantic_cache.get(query, active_session_id)

            if cached_result:
                # Handle augmentation
                if cached_result.get('_requires_augmentation'):
                    self.logger.info("🧩 AUGMENTING cached response with new context")
                    result = self._augment_cached_response(
                        cached_result['_cached_response'],
                        cached_result['_original_query'],
                        cached_result['_cached_query']
                    )

                    try:
                        self.conversation_store.add_message(active_session_id, 'user', query, tokens_used=0)
                        self.conversation_store.add_message(
                            active_session_id, 'assistant', result.get('answer', ''), tokens_used=0
                        )
                    except Exception as e:
                        self.logger.error(f"Failed to save augmented response: {e}")

                    return result

                # Handle generation with hints
                elif cached_result.get('_requires_generation'):
                    self.logger.info("💡 Will generate response with cache hints (proceeding to full generation)")
                    # Continue to full generation below

                # Direct cache hit - RETURN IMMEDIATELY
                else:
                    confidence = cached_result.get('cache_confidence', 'unknown')
                    cache_tier = cached_result.get('cache_tier', 'semantic')

                    self.logger.info(
                        f"✅ SEMANTIC CACHE HIT | confidence={confidence} | tier={cache_tier}"
                    )

                    try:
                        self.conversation_store.add_message(active_session_id, 'user', query, tokens_used=0)
                        self.conversation_store.add_message(
                            active_session_id, 'assistant', cached_result.get('answer', ''), tokens_used=0
                        )
                    except Exception as e:
                        self.logger.error(f"Failed to save cached exchange: {e}")

                    return cached_result

        # STEP 3: OLD CACHE CHECK
        if self.query_rewriter and self.query_rewriter.response_cache:
            cached_response = self.query_rewriter.response_cache.get(query, active_session_id)
            if cached_response:
                self.logger.info(f"OLD CACHE HIT | Returning cached response (legacy)")
                return cached_response

        query_lower = query.lower()

        if self.verbose:
            print(f"\n{'=' * 70}")
            print(f"Query: {query}")
            print(f"{'=' * 70}")

        # STEP 0: Check for greetings FIRST (before any rewriting)
        if self.is_greeting(query):
            query_type = QueryType.GREETING
            self.logger.info("CLASSIFICATION | Rule-based: GREETING (detected early)")
        else:
            # STEP 1: SESSION CONTEXT REWRITING
            if not self.is_greeting(query) and active_session_id:
                session_context_query = self.query_rewriter.rewrite(query, active_session_id)
                if session_context_query and session_context_query != query:
                    self.logger.info(f"🤖 SESSION REWRITE | '{query}' → '{session_context_query}'")
                    if self.verbose:
                        print(f"🤖 Session Context: {session_context_query}")
                    rewritten_query = session_context_query
                else:
                    rewritten_query = query
            else:
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
                    subqueries = self.split_into_subqueries(expanded_query)
                    if len(subqueries) > 1:
                        self.logger.info(f"MULTI-QUERY | Detected {len(subqueries)} sub-questions")
                        return self.handle_multi_query(subqueries, expanded_query, active_session_id)

            # STEP 3: Classify query into QueryType (using rewritten/expanded query)
            #         Determines query category: HOW_TO, CODE_LOCATION, CONCEPTUAL, etc.
            query_type = self.classify_query(expanded_query)

            # 👇 Direct lookup for Issue / PR numbers (skip semantic search)
            entity = self.extract_entity_from_query(expanded_query, query_type)
            if query_type == QueryType.PR_ISSUE_TUTORIAL and entity:
                self.logger.info(
                    f"PR-ISSUE TUTORIAL | Detected tutorial request for {entity['type']} #{entity['number']}"
                )

                result = self.handle_pr_issue_tutorial(entity, query, expanded_query)

                if self.query_rewriter and self.query_rewriter.semantic_cache:
                    quality_score = result.get('context_quality', 0.8)
                    self.query_rewriter.semantic_cache.set(
                        query, result, active_session_id, quality_score=quality_score
                    )

                if self.query_rewriter and self.query_rewriter.response_cache:
                    self.query_rewriter.response_cache.set(query, result, active_session_id)

                return result

                try:
                    self.conversation_store.add_message(active_session_id, "user", query, tokens_used=0)
                    self.conversation_store.add_message(
                        active_session_id, "assistant", result.get("answer", ""), tokens_used=0
                    )
                except Exception as e:
                    self.logger.error(f"CONVERSATION_STORE | Failed to save tutorial exchange: {e}")

                return result

            if query_type == QueryType.PR_ISSUE_CODING_QUESTION and entity:
                self.logger.info(
                    f"PR-ISSUE CODING QUESTION | Detected coding question request for {entity['type']} #{entity['number']}"
                )

                result = self.handle_pr_issue_coding_question(entity, query, expanded_query)

                if self.query_rewriter and self.query_rewriter.semantic_cache:
                    quality_score = result.get('context_quality', 0.8)
                    self.query_rewriter.semantic_cache.set(
                        query, result, active_session_id, quality_score=quality_score
                    )

                if self.query_rewriter and self.query_rewriter.response_cache:
                    self.query_rewriter.response_cache.set(query, result, active_session_id)

                return result

                try:
                    self.conversation_store.add_message(active_session_id, "user", query, tokens_used=0)
                    self.conversation_store.add_message(
                        active_session_id, "assistant", result.get("answer", ""), tokens_used=0
                    )
                except Exception as e:
                    self.logger.error(f"CONVERSATION_STORE | Failed to save coding-question exchange: {e}")

                return result

            if entity and entity.get("type") == "issue":
                num = str(entity["number"]).strip()
                self.logger.info(f"DIRECT LOOKUP | Searching issue metadata for #{num}")

                possible_keys = ["issue_number", "number", "id", "issue_id"]
                issue_results = []

                # Pick the ISSUE index metadata directly for debugging
                issue_index = self.vector_db.indices.get("issue")
                if issue_index and issue_index.metadata:
                    self.logger.info(f"DIRECT LOOKUP DEBUG | Issue metadata keys: {list(issue_index.metadata[0].keys())}")
                else:
                    self.logger.info("DIRECT LOOKUP DEBUG | Issue index has no metadata")

                for key in possible_keys:
                    issue_results = self.vector_db.find(where={key: num}, top_k=self.top_k)
                    if issue_results:
                        self.logger.info(f"DIRECT LOOKUP | Match via key '{key}' → {len(issue_results)} chunks")

                        result = self._respond_with_results(issue_results, query_type, query, expanded_query, role=role)

                        if self.query_rewriter and self.query_rewriter.semantic_cache:
                            quality_score = result.get('context_quality', 0.8)
                            self.query_rewriter.semantic_cache.set(
                                query, result, active_session_id, quality_score=quality_score
                            )

                        if self.query_rewriter and self.query_rewriter.response_cache:
                            self.query_rewriter.response_cache.set(query, result, active_session_id)

                        try:
                            self.conversation_store.add_message(active_session_id, "user", query, tokens_used=0)
                            self.conversation_store.add_message(
                                active_session_id, "assistant", result.get("answer", ""), tokens_used=0
                            )
                        except Exception as e:
                            self.logger.error(f"CONVERSATION_STORE | Failed to save issue direct-lookup exchange: {e}")

                        return result

                    # if issue_results:
                    #     self.logger.info(f"DIRECT LOOKUP | Match via key '{key}' → {len(issue_results)} chunks")
                    #     return self._respond_with_results(issue_results, query_type, query, expanded_query)

                # FINAL FALLBACK: substring match inside title
                issue_results = self.vector_db.find(where={"title": f"contains: {num}"}, top_k=self.top_k)
                if issue_results:
                    self.logger.info(f"DIRECT LOOKUP | Fallback match in title → {len(issue_results)} chunks")

                    result = self._respond_with_results(issue_results, query_type, query, expanded_query)

                    if self.query_rewriter and self.query_rewriter.semantic_cache:
                        quality_score = result.get('context_quality', 0.8)
                        self.query_rewriter.semantic_cache.set(
                            query, result, active_session_id, quality_score=quality_score
                        )

                    if self.query_rewriter and self.query_rewriter.response_cache:
                        self.query_rewriter.response_cache.set(query, result, active_session_id)

                    try:
                        self.conversation_store.add_message(active_session_id, "user", query, tokens_used=0)
                        self.conversation_store.add_message(
                            active_session_id, "assistant", result.get("answer", ""), tokens_used=0
                        )
                    except Exception as e:
                        self.logger.error(f"CONVERSATION_STORE | Failed to save issue fallback exchange: {e}")

                    return result

                self.logger.warning(f"DIRECT LOOKUP | No match for Issue #{num} across all metadata keys")

            # 🔥 DIRECT LOOKUP — PR
            if entity and entity.get("type") == "pr":
                num = str(entity["number"]).strip()

                possible_keys = ["pr_number", "number", "id", "pr_id"]
                for key in possible_keys:
                    pr_results = self.vector_db.find(where={key: num}, top_k=self.top_k)
                    if pr_results:
                        self.logger.info(f"DIRECT LOOKUP | Match via key '{key}' → {len(pr_results)} chunks")
                        result = self._respond_with_results(pr_results, QueryType.PR_SPECIFIC, query, expanded_query, role=role)

                        if self.query_rewriter and self.query_rewriter.semantic_cache:
                            quality_score = result.get('context_quality', 0.8)
                            self.query_rewriter.semantic_cache.set(
                                query, result, active_session_id, quality_score=quality_score
                            )

                        if self.query_rewriter and self.query_rewriter.response_cache:
                            self.query_rewriter.response_cache.set(query, result, active_session_id)

                        try:
                            self.conversation_store.add_message(active_session_id, "user", query, tokens_used=0)
                            self.conversation_store.add_message(
                                active_session_id, "assistant", result.get("answer", ""), tokens_used=0
                            )
                        except Exception as e:
                            self.logger.error(f"CONVERSATION_STORE | Failed to save user query: {e}")
                        return result

                # Fallback — match numeric substring inside title
                pr_results = self.vector_db.find(where={"title": f"contains: {num}"}, top_k=self.top_k)
                if pr_results:
                    self.logger.info(f"DIRECT LOOKUP | Fallback match in title → {len(pr_results)} chunks")
                    result = self._respond_with_results(pr_results, QueryType.PR_SPECIFIC, query, expanded_query, role=role)
                    if self.query_rewriter and self.query_rewriter.semantic_cache:
                        quality_score = result.get('context_quality', 0.8)
                        self.query_rewriter.semantic_cache.set(
                            query, result, active_session_id, quality_score=quality_score
                        )

                    if self.query_rewriter and self.query_rewriter.response_cache:
                        self.query_rewriter.response_cache.set(query, result, active_session_id)

                    try:
                        self.conversation_store.add_message(active_session_id, "user", query, tokens_used=0)
                        self.conversation_store.add_message(
                            active_session_id, "assistant", result.get("answer", ""), tokens_used=0
                        )
                    except Exception as e:
                        self.logger.error(f"CONVERSATION_STORE | Failed to save user query: {e}")

                    return result

                self.logger.warning(f"DIRECT LOOKUP | No match for PR #{num} across metadata keys")

            self.logger.info(f"QUERY TYPE | {query_type}")

            if query_type == QueryType.RANDOM_PR_GENERATOR:
                self.logger.info("RANDOM PR GENERATOR | Will retrieve merged PRs with code changes for LLM selection")

            raw_num = re.search(r'\b(\d+)\b', expanded_query.lower())
            pr_results = None  

            if raw_num and (
                query_type == QueryType.PR_SPECIFIC
                or "pr" in query_lower
                or "pull request" in query_lower
                or "merge request" in query_lower
                or "mr" in query_lower
            ):
                num = int(raw_num.group(1))
                self.logger.info(f"DIRECT LOOKUP (PR override) | PR #{num}")
                pr_results = self.vector_db.find(where={"pr_number": str(num)}, top_k=self.top_k)

                if pr_results:
                    self.logger.info(f"DIRECT LOOKUP (PR override) | {len(pr_results)} chunks returned")

                    try:
                        self.conversation_store.add_message(active_session_id, "user", query, tokens_used=0)
                    except Exception as e:
                        self.logger.error(f"CONVERSATION_STORE | Failed to save user query: {e}")

                    result = self._respond_with_results(pr_results, QueryType.PR_SPECIFIC, query, expanded_query, role=role)
                    if self.query_rewriter and self.query_rewriter.semantic_cache:
                        quality_score = result.get('context_quality', 0.8)
                        self.query_rewriter.semantic_cache.set(
                            query, result, active_session_id, quality_score=quality_score
                        )
                    if self.query_rewriter and self.query_rewriter.response_cache:
                        self.query_rewriter.response_cache.set(query, result, active_session_id)

                    return result
                else:
                    self.logger.warning(f"DIRECT LOOKUP (PR override) | No match for PR #{num}")

            # ❗ FINAL STOP: If PR is not found in metadata, do NOT do semantic search
            if query_type == QueryType.PR_SPECIFIC and raw_num and not pr_results:
                num = int(raw_num.group(1))
                self.logger.info(f"DIRECT LOOKUP FINAL | PR #{num} not found — stopping without semantic search")
                not_found_answer = f"PR #{num} was not found in the repository. It may not exist or was not indexed."
                result = self._package_response(not_found_answer, [], [], QueryType.PR_SPECIFIC)

                if self.query_rewriter and self.query_rewriter.semantic_cache:
                    quality_score = result.get('context_quality', 0.8)
                    self.query_rewriter.semantic_cache.set(
                        query, result, active_session_id, quality_score=quality_score
                    )

                if self.query_rewriter and self.query_rewriter.response_cache:
                    self.query_rewriter.response_cache.set(query, result, active_session_id)

                return result

            # Guaranteed ISSUE direct lookup override
            if query_type == QueryType.ISSUE_SPECIFIC and raw_num:
                num = int(raw_num.group(1))
                if any(t in query.lower() for t in ["issue", "bug", "ticket", "report"]):
                    self.logger.info(f"DIRECT LOOKUP (ISSUE override) | Issue #{num}")
                    issue_results = self.vector_db.find(where={"issue_number": str(num)}, top_k=self.top_k)
                    if issue_results:
                        result = self._respond_with_results(issue_results, QueryType.ISSUE_SPECIFIC, query,
                                                            expanded_query, role=role)
                        if self.query_rewriter and self.query_rewriter.semantic_cache:
                            quality_score = result.get('context_quality', 0.8)
                            self.query_rewriter.semantic_cache.set(
                                query, result, active_session_id, quality_score=quality_score
                            )

                        if self.query_rewriter and self.query_rewriter.response_cache:
                            self.query_rewriter.response_cache.set(query, result, active_session_id)
                        try:
                            self.conversation_store.add_message(active_session_id, "user", query, tokens_used=0)
                            self.conversation_store.add_message(
                                active_session_id, "assistant", result.get("answer", ""), tokens_used=0
                            )
                        except Exception as e:
                            self.logger.error(f"CONVERSATION_STORE | Failed to save user query: {e}")

                        return result
                    else:
                        self.logger.warning(f"DIRECT LOOKUP (ISSUE override) | No match for Issue #{num}")


        # STEP 4: Query routing happens in _retrieve_multi_index() using expanded_query
        #         Routes to appropriate index: docs, code, prs, commits, or combined
        #         Then searches both routed index AND combined index, merges results
        if query_type == QueryType.GREETING:
            greeting_response = ""
            for chunk in self.generate_greeting_response_streaming():
                greeting_response += chunk
                # printing is optional; caller may handle streaming
                try:
                    print(chunk, end='', flush=True)
                except Exception:
                    pass

            self.history.append({'role': 'user', 'content': query})
            self.history.append({'role': 'assistant', 'content': greeting_response})

            try:
                self.conversation_store.add_message(active_session_id, "user", query, tokens_used=0)
                self.conversation_store.add_message(active_session_id, "assistant", greeting_response, tokens_used=0)
                self.logger.info(f"CONVERSATION_STORE | Saved greeting exchange to session {active_session_id[:8]}...")
            except Exception as e:
                self.logger.error(f"CONVERSATION_STORE | Failed to save greeting: {e}")

            result = {
                'answer': greeting_response,
                'sources': [],
                'chunks_retrieved': 0,
                'query_type': query_type,
                'context_quality': 1.0,
                'emails': [],
                'has_diagram': False,
                'related_knowledge': None,
                'is_metrics_query': False
            }

            if self.query_rewriter and self.query_rewriter.semantic_cache:
                quality_score = result.get('context_quality', 0.8)
                self.query_rewriter.semantic_cache.set(
                    query, result, active_session_id, quality_score=quality_score
                )

            if self.query_rewriter and self.query_rewriter.response_cache:
                self.query_rewriter.response_cache.set(query, result, active_session_id)

            return result

        chrono_query = self.detect_chronological_query(expanded_query)

        # prepare commonly used variables
        entity = None
        keywords = self.extract_keywords(expanded_query)
        metrics_context = None

        if chrono_query:
            self.logger.info(f"CHRONOLOGICAL QUERY | Type: {chrono_query['type']}, Order: {chrono_query['order']}")

            if self.verbose:
                print(f"Chronological query detected: {chrono_query}")

            query_embedding = self.get_query_embedding(expanded_query)
            chrono_result = self.find_chronological_entity(
                chrono_query['type'],
                chrono_query['order'],
                query_embedding
            )

            if chrono_result:
                entity = {'type': chrono_result['type'], 'number': chrono_result['number']}
                github_results = chrono_result['results']

                self.logger.info(f"CHRONOLOGICAL RESULT | Found {chrono_query['type']} #{chrono_result['number']}")
                self.logger.info(f"RETRIEVAL | Retrieved {len(github_results)} chunks")

                for i, result in enumerate(github_results[:5], 1):
                    metadata = result.get('metadata', {})
                    self.logger.info(
                        f"CHUNK {i} | File: {metadata.get('file_path', 'N/A')}, Score: {result.get('score', 0):.4f}, Type: {metadata.get('type', 'N/A')}")

                query_type = QueryType.ISSUE_SPECIFIC if chrono_result['type'] == 'issue' else QueryType.PR_SPECIFIC

                if self.verbose:
                    print(f"Found {chrono_query['order']} {chrono_query['type']}: #{chrono_result['number']}")

                context = self.build_context_from_chunks(github_results, query_type)

                gmail_results = self.retrieve_gmail_correlated(
                    github_results, query_embedding, []
                )

                if gmail_results:
                    self.logger.info(f"EMAIL RETRIEVAL | Found {len(gmail_results)} correlated emails")

                email_context = self.build_email_context(gmail_results) if gmail_results else ""

                system_prompt = self.get_dynamic_system_prompt(query_type, expanded_query, role=role)
                user_prompt = self.build_user_prompt(
                    expanded_query, context, email_context, query_type, entity, None
                )

                if self.verbose:
                    print("Generating response...")

                self.logger.info("LLM GENERATION | Started")
                answer = self.call_llm(system_prompt, user_prompt)
                self.logger.info(f"LLM GENERATION | Completed, Length: {len(answer)} chars")

                self.logger.info("VERIFICATION | Starting response verification")
                refined_answer = self.verify_and_refine_response(answer, query, query_type)

                sources = []
                for i, result in enumerate(github_results[:5], 1):
                    metadata = result.get('metadata', {})
                    # Handle both file_path and file fields
                    file_path = metadata.get('file_path') or metadata.get('file') or 'unknown'
                    # Handle both type and source_type fields
                    chunk_type = metadata.get('type') or metadata.get('source_type') or metadata.get('chunk_type') or 'unknown'
                    sources.append({
                        'rank': i,
                        'file': file_path,
                        'type': chunk_type,
                        'score': result.get('score', 0.0),
                        'chunk_id': metadata.get('chunk_id', '')
                    })

                emails = []
                for email in gmail_results:
                    metadata = email.get('metadata', {})
                    emails.append({
                        'subject': metadata.get('subject', ''),
                        'from': metadata.get('from', ''),
                        'date': metadata.get('date', ''),
                        'relevance': email.get('relevance_score', 0)
                    })

                self.history.append({'role': 'user', 'content': query})
                self.history.append({'role': 'assistant', 'content': refined_answer})

                context_quality = min(github_results[0].get('score', 0), 1.0) if github_results else 0.0

                self.logger.info(
                    f"RESPONSE COMPLETE | Quality: {context_quality:.2f}, Sources: {len(sources)}, Emails: {len(emails)}")
                self.logger.info("=" * 80)

                # Store conversation to database
                try:
                    self.conversation_store.add_message(active_session_id, "user", query, tokens_used=0)
                    self.conversation_store.add_message(active_session_id, "assistant", refined_answer, tokens_used=0)
                    self.logger.info(
                        f"CONVERSATION_STORE | Saved chronological response to session {active_session_id[:8]}...")
                except Exception as e:
                    self.logger.error(f"CONVERSATION_STORE | Failed to save chrono response: {e}")

                result = {
                    'answer': refined_answer,
                    'sources': sources,
                    'chunks_retrieved': len(github_results),
                    'query_type': query_type,
                    'context_quality': context_quality,
                    'emails': emails,
                    'has_diagram': bool(re.search(r'```mermaid', refined_answer or '')),
                    'related_knowledge': None,
                    'is_metrics_query': False,
                    'chronological_entity': f"{chrono_query['order']} {chrono_query['type']} #{chrono_result['number']}"
                }

                if self.query_rewriter and self.query_rewriter.semantic_cache:
                    quality_score = result.get('context_quality', 0.8)
                    self.query_rewriter.semantic_cache.set(
                        query, result, active_session_id, quality_score=quality_score
                    )

                if self.query_rewriter and self.query_rewriter.response_cache:
                    self.query_rewriter.response_cache.set(query, result, active_session_id)

                return result

        # Non-chronological / general flow
        if query_type in [QueryType.REPOSITORY_METRICS, QueryType.TECH_STACK, QueryType.CODE_STRUCTURE]:
            if self.repo_metrics:
                metrics_context = self.build_metrics_context()
                self.logger.info("METRICS | Using repository metrics context")
                if self.verbose:
                    print("Including metrics context")
            else:
                try:
                    self.conversation_store.add_message(active_session_id, "user", query, tokens_used=0)
                    self.conversation_store.add_message(
                        active_session_id, "assistant",
                        "Repository metrics are not available.\n\nTo enable metrics-based queries, ensure aggregated_tech_stack_summary.json exists in the DataProcessing directory.",
                        tokens_used=0
                    )
                    self.logger.info(f"CONVERSATION_STORE | Saved metrics error to session {active_session_id[:8]}...")
                except Exception as e:
                    self.logger.error(f"CONVERSATION_STORE | Failed to save metrics error: {e}")
                result = {
                    'answer': ("Repository metrics are not available.\n\n"
                               "To enable metrics-based queries, ensure aggregated_tech_stack_summary.json "
                               "exists in the DataProcessing directory."),
                    'sources': [],
                    'chunks_retrieved': 0,
                    'query_type': query_type,
                    'context_quality': 0.0,
                    'has_diagram': False,
                    'emails': [],
                    'is_metrics_query': True
                }

                if self.query_rewriter and self.query_rewriter.semantic_cache:
                    quality_score = result.get('context_quality', 0.8)
                    self.query_rewriter.semantic_cache.set(
                        query, result, active_session_id, quality_score=quality_score
                    )

                if self.query_rewriter and self.query_rewriter.response_cache:
                    self.query_rewriter.response_cache.set(query, result, active_session_id)

                return result

        # retrieval (multi-query optional)
        if self.enable_multi_query and query_type not in [QueryType.REPOSITORY_METRICS, QueryType.TECH_STACK,
                                                          QueryType.CODE_STRUCTURE]:
            self.logger.info("MULTI-QUERY | Generating optimized query variations")
            queries = self.generate_multi_queries(expanded_query, query_type)

            github_results = self.retrieve_with_multi_query(
                queries, query_type, entity, keywords
            )
        else:
            query_embedding = self.get_query_embedding(expanded_query)
            github_results = self.retrieve_github_first(
                query_embedding, query_type, entity, keywords, query_text=expanded_query
            )

        self.logger.info(f"RETRIEVAL | Retrieved {len(github_results)} chunks from GitHub")
        for i, result in enumerate(github_results[:5], 1):
            metadata = result.get('metadata', {})
            # Handle both file_path and file fields
            file_path = metadata.get('file_path') or metadata.get('file') or 'N/A'
            # Handle both type and source_type fields
            chunk_type = metadata.get('type') or metadata.get('source_type') or metadata.get('chunk_type') or 'N/A'
            self.logger.info(
                f"CHUNK {i} | File: {file_path}, Score: {result.get('score', 0):.4f}, Type: {chunk_type}")

        if self.verbose:
            print(f"GitHub: {len(github_results)} chunks")

        # gmail correlated retrieval (use same query embedding)
        query_embedding = self.get_query_embedding(expanded_query)
        gmail_results = self.retrieve_gmail_correlated(
            github_results, query_embedding, keywords
        )

        if gmail_results:
            self.logger.info(f"EMAIL RETRIEVAL | Found {len(gmail_results)} correlated emails")

        if self.verbose:
            print(f"Gmail: {len(gmail_results)} emails")

        # Log context quality
        if not github_results:
            self.logger.warning(f"RETRIEVAL | No results retrieved for query type: {query_type}")
            self.logger.warning(f"RETRIEVAL | Consider checking if the routed index has content")
        elif len(github_results) < 3:
            self.logger.warning(f"RETRIEVAL | Only {len(github_results)} results retrieved, may be insufficient")

        context = self.build_context_from_chunks(github_results, query_type) if github_results else ""
        email_context = self.build_email_context(gmail_results) if gmail_results else ""

        # Log context length for debugging
        if context:
            self.logger.info(f"CONTEXT | Built context: {len(context)} characters from {len(github_results)} chunks")
        else:
            self.logger.warning(f"CONTEXT | Empty context - no information available to answer query")

        system_prompt = self.get_dynamic_system_prompt(query_type, expanded_query, role=role)
        user_prompt = self.build_user_prompt(
            expanded_query, context, email_context, query_type, entity, metrics_context
        )

        if self.verbose:
            print("Generating response...")

        self.logger.info("LLM GENERATION | Started")
        answer = self.call_llm(system_prompt, user_prompt)
        self.logger.info(f"LLM GENERATION | Completed, Length: {len(answer)} chars")

        self.logger.info("VERIFICATION | Starting response verification")
        refined_answer = self.verify_and_refine_response(answer, query, query_type)

        sources = []
        if github_results:
            for i, result in enumerate(github_results[:5], 1):
                metadata = result.get('metadata', {})
                sources.append({
                    'rank': i,
                    'file': metadata.get('file_path', 'unknown'),
                    'type': metadata.get('type', 'unknown'),
                    'score': result.get('score', 0.0),
                    'chunk_id': metadata.get('chunk_id', '')
                })

        emails = []
        for email in gmail_results:
            metadata = email.get('metadata', {})
            emails.append({
                'subject': metadata.get('subject', ''),
                'from': metadata.get('from', ''),
                'date': metadata.get('date', ''),
                'relevance': email.get('relevance_score', 0)
            })

        self.history.append({'role': 'user', 'content': query})
        self.history.append({'role': 'assistant', 'content': refined_answer})

        if metrics_context:
            context_quality = 1.0
        elif github_results and len(github_results) > 0:
            # github_results is a list; pick top score
            top_score = max((r.get('score', 0) for r in github_results), default=0.0)
            context_quality = min(top_score, 1.0)
        else:
            context_quality = 0.0

        self.logger.info(
            f"RESPONSE COMPLETE | Quality: {context_quality:.2f}, Sources: {len(sources)}, Emails: {len(emails)}")
        self.logger.info("=" * 80)

        try:
            self.conversation_store.add_message(active_session_id, "user", query, tokens_used=0)
            self.conversation_store.add_message(active_session_id, "assistant", refined_answer, tokens_used=0)
            self.logger.info(f"CONVERSATION_STORE | Saved main response to session {active_session_id[:8]}...")
        except Exception as e:
            self.logger.error(f"CONVERSATION_STORE | Failed to save main response: {e}")

        result = {
            'answer': refined_answer,
            'sources': sources,
            'chunks_retrieved': len(github_results) if github_results else 0,
            'query_type': query_type,
            'context_quality': context_quality,
            'emails': emails,
            'has_diagram': bool(re.search(r'```mermaid', str(refined_answer or ''))),
            'related_knowledge': None,
            'is_metrics_query': query_type in [
                QueryType.REPOSITORY_METRICS,
                QueryType.TECH_STACK,
                QueryType.CODE_STRUCTURE
            ]
        }

        if self.query_rewriter and self.query_rewriter.semantic_cache:
            quality_score = result.get('context_quality', 0.8)
            self.query_rewriter.semantic_cache.set(
                query, result, active_session_id, quality_score=quality_score
            )

        if self.query_rewriter and self.query_rewriter.response_cache:
            self.query_rewriter.response_cache.set(query, result, active_session_id)

        return result

    def _augment_cached_response(self,cached_response: Dict[str, Any],new_query: str,original_query: str) -> Dict[str, Any]:
            """
            Augment cached response to specifically answer the new query variant
            """
            # Extract differences between queries
            new_words = set(new_query.lower().split())
            orig_words = set(original_query.lower().split())
            unique_words = new_words - orig_words

            if not unique_words:
                # No significant differences, return as-is
                return cached_response

            query_diff = f"New emphasis on: {', '.join(unique_words)}"
            cached_answer = cached_response.get('answer', '')

            # Use fast LLM to augment
            augmentation_prompt = f"""You have a cached response for a similar question. Adjust it slightly to specifically answer the new question.

    Original Question: {original_query}
    New Question: {new_query}
    Key Differences: {query_diff}

    Cached Response:
    {cached_answer}

    Adjusted Response (keep all cached info, just reframe for new question):"""

            try:
                augmented_answer = self.call_llm(
                    "You are adjusting a response to better match a slightly different question.",
                    augmentation_prompt
                )

                result = cached_response.copy()
                result['answer'] = augmented_answer
                result['augmented'] = True
                result['original_cached_query'] = original_query

                self.logger.info(f"AUGMENTATION | Adjusted response from '{original_query[:40]}' to '{new_query[:40]}'")

                return result

            except Exception as e:
                self.logger.error(f"Augmentation failed: {e}, returning original cached response")
                return cached_response

    def handle_pr_issue_tutorial(
            self,
            entity: Dict[str, Any],
            original_query: str,
            expanded_query: str
    ) -> Dict[str, Any]:
        """
                Generate a step-by-step tutorial based on a specific PR or Issue.
                Retrieves comprehensive context about the PR/Issue and creates educational content.
                """
        entity_type = entity['type']
        entity_number = entity['number']

        self.logger.info(f"TUTORIAL GENERATION | Starting for {entity_type} #{entity_number}")

        # Retrieve comprehensive context (use higher top_k for tutorials)
        query_embedding = self.get_query_embedding(expanded_query)

        if entity_type == 'pr':
            github_results = self.vector_db.find(where={"pr_number": str(entity_number)}, top_k=20)
        else:  # issue
            github_results = self.vector_db.find(where={"issue_number": str(entity_number)}, top_k=20)

        if not github_results:
            self.logger.warning(f"TUTORIAL GENERATION | No data found for {entity_type} #{entity_number}")
            return self._package_response(
                f"I couldn't find any information about {entity_type} #{entity_number} in the repository.",
                [], [], QueryType.PR_ISSUE_TUTORIAL
            )

        self.logger.info(f"TUTORIAL GENERATION | Retrieved {len(github_results)} chunks")

        # Build comprehensive context
        context = self.build_context_from_chunks(github_results, QueryType.PR_ISSUE_TUTORIAL)

        # Create specialized tutorial prompt
        system_prompt = f"""You are an expert technical educator creating step-by-step tutorials from code changes.

        Your task: Create a comprehensive, beginner-friendly tutorial based on {entity_type.upper()} #{entity_number}.

        TUTORIAL STRUCTURE:
        1. **Overview** - What was changed and why
        2. **Problem Context** - What issue/challenge this addresses
        3. **Step-by-Step Implementation** - Detailed walkthrough of each change
        4. **Code Explanation** - Explain key code sections with inline comments
        5. **Testing** - How to test these changes
        6. **Key Takeaways** - Important concepts learned
        7. **Practice Exercises** - 2-3 exercises for learners to try

        GUIDELINES:
        - Use clear, simple language suitable for intermediate developers
        - Include code snippets with explanations
        - Explain the "why" behind each decision
        - Provide context about the broader system
        - Add helpful tips and best practices
        - Use markdown formatting with headers, code blocks, and lists
        - Be thorough but concise

        Generate a complete tutorial now."""

        user_prompt = f"""Generate a tutorial based on this {entity_type}:

        {context}

        Create a comprehensive, educational tutorial following the structure provided."""

        # Generate tutorial
        self.logger.info("TUTORIAL GENERATION | Calling LLM for tutorial content")
        tutorial_answer = self.call_llm(system_prompt, user_prompt)

        self.logger.info(f"TUTORIAL GENERATION | Completed, Length: {len(tutorial_answer)} chars")

        # Extract sources
        sources = []
        for i, result in enumerate(github_results[:10], 1):
            metadata = result.get('metadata', {})
            sources.append({
                'rank': i,
                'file': metadata.get('file_path') or metadata.get('file') or 'unknown',
                'type': metadata.get('type') or 'unknown',
                'score': result.get('score', 0.0),
                'chunk_id': metadata.get('chunk_id', '')
            })

        self.history.append({'role': 'user', 'content': original_query})
        self.history.append({'role': 'assistant', 'content': tutorial_answer})

        return {
            'answer': tutorial_answer,
            'sources': sources,
            'chunks_retrieved': len(github_results),
            'query_type': QueryType.PR_ISSUE_TUTORIAL,
            'context_quality': min(github_results[0].get('score', 0), 1.0) if github_results else 0.0,
            'emails': [],
            'has_diagram': False,
            'related_knowledge': None,
            'is_metrics_query': False,
            'entity': f"{entity_type} #{entity_number}"
        }

    def handle_pr_issue_coding_question(
            self,
            entity: Dict[str, Any],
            original_query: str,
            expanded_query: str
    ) -> Dict[str, Any]:
        """
                Generate a coding challenge/question based on a specific PR or Issue.
                Creates practice problems that help learners understand the concepts.
                """
        entity_type = entity['type']
        entity_number = entity['number']

        self.logger.info(f"CODING QUESTION GENERATION | Starting for {entity_type} #{entity_number}")

        # Retrieve comprehensive context
        query_embedding = self.get_query_embedding(expanded_query)

        if entity_type == 'pr':
            github_results = self.vector_db.find(where={"pr_number": str(entity_number)}, top_k=20)
        else:  # issue
            github_results = self.vector_db.find(where={"issue_number": str(entity_number)}, top_k=20)

        if not github_results:
            self.logger.warning(f"CODING QUESTION GENERATION | No data found for {entity_type} #{entity_number}")
            return self._package_response(
                f"I couldn't find any information about {entity_type} #{entity_number} in the repository.",
                [], [], QueryType.PR_ISSUE_CODING_QUESTION
            )

        self.logger.info(f"CODING QUESTION GENERATION | Retrieved {len(github_results)} chunks")

        # Build comprehensive context
        context = self.build_context_from_chunks(github_results, QueryType.PR_ISSUE_CODING_QUESTION)

        # Create specialized coding question prompt
        system_prompt = f"""You are an expert technical interviewer creating coding challenges based on real-world code changes.

        Your task: Create a coding question/challenge inspired by {entity_type.upper()} #{entity_number}.

        QUESTION STRUCTURE:
        1. **Problem Statement** - Clear description of what to build/fix
        2. **Background Context** - Why this problem matters
        3. **Requirements** - Specific functional requirements
        4. **Constraints** - Technical constraints and limitations
        5. **Input/Output Examples** - 2-3 test cases with expected results
        6. **Hints** (Optional) - Helpful hints for solving the problem
        7. **Solution Outline** - High-level approach (spoiler-protected with markdown)
        8. **Follow-up Questions** - 2-3 deeper thinking questions

        GUIDELINES:
        - Make the question realistic and practical
        - Base it on the concepts/patterns from the PR/Issue
        - Make it challenging but solvable
        - Include clear examples and edge cases
        - Provide hints without giving away the solution
        - Use markdown formatting
        - Focus on understanding, not memorization

        Generate a complete coding challenge now."""

        user_prompt = f"""Generate a coding question based on this {entity_type}:

        {context}

        Create a comprehensive coding challenge following the structure provided."""

        # Generate coding question
        self.logger.info("CODING QUESTION GENERATION | Calling LLM for question content")
        question_answer = self.call_llm(system_prompt, user_prompt)

        self.logger.info(f"CODING QUESTION GENERATION | Completed, Length: {len(question_answer)} chars")

        # Extract sources
        sources = []
        for i, result in enumerate(github_results[:10], 1):
            metadata = result.get('metadata', {})
            sources.append({
                'rank': i,
                'file': metadata.get('file_path') or metadata.get('file') or 'unknown',
                'type': metadata.get('type') or 'unknown',
                'score': result.get('score', 0.0),
                'chunk_id': metadata.get('chunk_id', '')
            })

        self.history.append({'role': 'user', 'content': original_query})
        self.history.append({'role': 'assistant', 'content': question_answer})

        return {
            'answer': question_answer,
            'sources': sources,
            'chunks_retrieved': len(github_results),
            'query_type': QueryType.PR_ISSUE_CODING_QUESTION,
            'context_quality': min(github_results[0].get('score', 0), 1.0) if github_results else 0.0,
            'emails': [],
            'has_diagram': False,
            'related_knowledge': None,
            'is_metrics_query': False,
            'entity': f"{entity_type} #{entity_number}"
        }

    def _respond_with_results(self, github_results, query_type, query, expanded_query, role: Optional[str] = None):
        context = self.build_context_from_chunks(github_results, query_type)
        email_results = self.retrieve_gmail_correlated(github_results, self.get_query_embedding(expanded_query), [])
        email_context = self.build_email_context(email_results)
        system_prompt = self.get_dynamic_system_prompt(query_type, expanded_query, role=role)
        user_prompt = self.build_user_prompt(expanded_query, context, email_context, query_type)
        answer = self.call_llm(system_prompt, user_prompt)
        refined = self.verify_and_refine_response(answer, query, query_type)
        return self._package_response(refined, github_results, email_results, query_type)

    def split_into_subqueries(self, query: str) -> List[str]:
        """
        Split query into sub-questions ONLY if clearly multi-part.
        Returns list with 2-3 questions, or single-item list.
        """
        # Skip splitting for short queries
        if len(query.strip()) < 40:
            return [query]

        parts = re.split(r'\?\s+|[.]\s+(?=(?:and|also|then|plus|what|how|where|when|why|tell)\b)', query,
                         flags=re.IGNORECASE)
        subqueries = [p.strip() for p in parts if p.strip() and len(p.strip()) > 10]

        if 2 <= len(subqueries) <= 3:
            self.logger.info(f"MULTI-QUERY SPLIT | '{query}' → {len(subqueries)} parts")
            for i, sq in enumerate(subqueries, 1):
                self.logger.info(f"  Sub-query {i}: {sq[:60]}...")
            return subqueries

            # Default: keep as single query
        return [query]

    def handle_multi_query(self, subqueries: List[str], original_query: str, session_id: str) -> Dict[str, Any]:
        """
        Process multiple sub-queries and merge results into SINGLE response.
        CRITICAL: Pass filters={'is_subquery': True} to skip rewrite/multi-query recursion.
        """
        self.logger.info(f"MULTI-QUERY | Processing {len(subqueries)} sub-queries for: '{original_query[:50]}...'")

        answers = []
        for i, sq in enumerate(subqueries, 1):
            self.logger.info(f"MULTI-QUERY | Sub-query {i}/{len(subqueries)}: '{sq[:60]}...'")

            # CRITICAL: Pass filters AND session_id to prevent:
            # 1. Recursive multi-query splitting
            # 2. Cache misses from new rewrites
            # 3. Session context loss
            result = self.chat(
                sq,
                filters={'is_subquery': True},  # Skip rewrite + multi-query
                session_id=session_id  # Preserve session context
            )
            answers.append(result)
            self.logger.info(f"MULTI-QUERY | Sub-query {i} completed: {len(result.get('answer', ''))} chars")

        # Merge into single response
        merged = self.merge_multi_answers(answers, original_query)

        # Save merged response to conversation store
        try:
            self.conversation_store.add_message(session_id, "user", original_query, tokens_used=0)
            self.conversation_store.add_message(session_id, "assistant", merged['answer'], tokens_used=0)
            self.logger.info(f"CONVERSATION_STORE | Saved multi-query merged response to session {session_id[:8]}...")
        except Exception as e:
            self.logger.error(f"CONVERSATION_STORE | Failed to save multi-query response: {e}")

        return merged

    def merge_multi_answers(self, results: List[Dict[str, Any]], original_query: str) -> Dict[str, Any]:
        """
        Merge multiple sub-query results into a SINGLE coherent response.
        Returns a properly formatted response dict (not fragmented UI messages).
        """
        if not results:
            return self._package_response(
                "No results found for your query.",
                [], [], QueryType.GENERAL
            )

        # If only ONE result, return it directly
        if len(results) == 1:
            return results[0]

        self.logger.info(f"MULTI-QUERY MERGE | Merging {len(results)} responses into single answer")

        # Collect all sources and emails
        all_sources = []
        all_emails = []
        total_chunks = 0
        avg_quality = 0.0

        for r in results:
            all_sources.extend(r.get('sources', []))
            all_emails.extend(r.get('emails', []))
            total_chunks += r.get('chunks_retrieved', 0)
            avg_quality += r.get('context_quality', 0.0)

        avg_quality = avg_quality / len(results) if results else 0.0

        # Deduplicate sources by chunk_id
        seen_chunks = set()
        unique_sources = []
        for src in all_sources:
            chunk_id = src.get('chunk_id', '')
            if chunk_id and chunk_id not in seen_chunks:
                seen_chunks.add(chunk_id)
                unique_sources.append(src)

        # Build merged answer (keep it concise, not repetitive)
        merged_answer_parts = []

        for i, result in enumerate(results, 1):
            answer_text = result.get('answer', '').strip()
            if answer_text:
                # Remove redundant headers if they exist
                answer_text = re.sub(r'^#+\s*(Combined Response|Answer|Response)\s*\n+', '', answer_text,
                                     flags=re.IGNORECASE)
                merged_answer_parts.append(answer_text)

        # Join with proper spacing
        final_answer = "\n\n".join(merged_answer_parts)

        self.logger.info(
            f"MULTI-QUERY MERGE | Final answer: {len(final_answer)} chars, {len(unique_sources)} unique sources")

        return {
            'answer': final_answer,
            'sources': unique_sources[:10],  # Top 10 sources
            'chunks_retrieved': total_chunks,
            'query_type': 'multi_query',
            'context_quality': avg_quality,
            'emails': all_emails[:5],  # Top 5 emails
            'has_diagram': any(r.get('has_diagram', False) for r in results),
            'related_knowledge': None,
            'is_metrics_query': False
        }

    def _package_response(self, answer, github_results, email_results, query_type):
        # Build GitHub sources list
        sources = []
        if github_results:
            for i, result in enumerate(github_results[:5], 1):
                meta = result.get("metadata", {})
                sources.append({
                    "rank": i,
                    "file": meta.get("file_path", "unknown"),
                    "type": meta.get("type", "unknown"),
                    "score": result.get("score", 0.0),
                    "chunk_id": meta.get("chunk_id", "")
                })

        # Build email list (optional)
        emails = []
        if email_results:
            for email in email_results:
                meta = email.get("metadata", {})
                emails.append({
                    "subject": meta.get("subject", ""),
                    "from": meta.get("from", ""),
                    "date": meta.get("date", ""),
                    "relevance": email.get("relevance_score", 0)
                })

        context_quality = (
            min(github_results[0].get("score", 0), 1.0)
            if github_results else 0.0
        )

        return {
            "answer": answer,
            "sources": sources,
            "chunks_retrieved": len(github_results) if github_results else 0,
            "query_type": query_type,
            "context_quality": context_quality,
            "emails": emails,
            "has_diagram": False,
            "related_knowledge": None,
            "is_metrics_query": False
        }


    def chat_stream(self, query: str, filters: Optional[Dict] = None, role: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        self.logger.info("=" * 80)
        self.logger.info(f"NEW STREAM QUERY | {query}")

        if self.verbose:
            print(f"\n{'=' * 70}")
            print(f"Query (streaming): {query}")
            print(f"{'=' * 70}")

        expanded_query = self.expand_query(query)
        if expanded_query != query:
            self.logger.info(f"QUERY EXPANSION | Original: '{query}' -> Expanded: '{expanded_query}'")

        yield {'type': 'status', 'content': 'Analyzing query...'}

        query_type = self.classify_query(expanded_query)
        self.logger.info(f"QUERY TYPE | {query_type}")

        if query_type == QueryType.RANDOM_PR_GENERATOR:
            self.logger.info("RANDOM PR GENERATOR | Will retrieve merged PRs with code changes for LLM selection")

        if query_type == QueryType.GREETING:
            self.history.append({'role': 'user', 'content': query})
            greeting_response = ""

            for chunk in self.generate_greeting_response_streaming():
                greeting_response += chunk
                yield {'type': 'chunk', 'content': chunk}

            self.history.append({'role': 'assistant', 'content': greeting_response})

            yield {
                'type': 'complete',
                'content': {
                    'answer': greeting_response,
                    'sources': [],
                    'chunks_retrieved': 0,
                    'query_type': query_type,
                    'context_quality': 1.0,
                    'emails': [],
                    'has_diagram': False,
                    'related_knowledge': None,
                    'is_metrics_query': False
                }
            }
            return

        chrono_query = self.detect_chronological_query(expanded_query)

        if chrono_query:
            self.logger.info(f"CHRONOLOGICAL QUERY | Type: {chrono_query['type']}, Order: {chrono_query['order']}")

            if self.verbose:
                print(f"Chronological query detected: {chrono_query}")

            yield {'type': 'status', 'content': f'Finding {chrono_query["order"]} {chrono_query["type"]}...'}

            query_embedding = self.get_query_embedding(expanded_query)
            chrono_result = self.find_chronological_entity(
                chrono_query['type'],
                chrono_query['order'],
                query_embedding
            )

            if chrono_result:
                entity = {'type': chrono_result['type'], 'number': chrono_result['number']}
                github_results = chrono_result['results']

                self.logger.info(f"CHRONOLOGICAL RESULT | Found {chrono_query['type']} #{chrono_result['number']}")

                query_type = QueryType.ISSUE_SPECIFIC if chrono_result['type'] == 'issue' else QueryType.PR_SPECIFIC

                yield {'type': 'status', 'content': f'Found {chrono_query["type"]} #{chrono_result["number"]}'}

                context = self.build_context_from_chunks(github_results, query_type)

                gmail_results = self.retrieve_gmail_correlated(
                    github_results, query_embedding, []
                )

                email_context = self.build_email_context(gmail_results) if gmail_results else ""
                if gmail_results:
                    yield {'type': 'status', 'content': f'Found {len(gmail_results)} related emails'}

                system_prompt = self.get_dynamic_system_prompt(query_type, expanded_query, role=role)
                user_prompt = self.build_user_prompt(
                    expanded_query, context, email_context, query_type, entity, None
                )

                yield {'type': 'status', 'content': 'Generating response...'}

                full_answer = ""
                buffer = ""
                for chunk in self.call_llm_stream(system_prompt, user_prompt):
                    full_answer += chunk
                    buffer += chunk

                    if '\n' in buffer or len(buffer) > 150:
                        yield {'type': 'chunk', 'content': buffer}
                        buffer = ""

                if buffer:
                    yield {'type': 'chunk', 'content': buffer}

                self.logger.info(f"LLM GENERATION | Completed streaming, Length: {len(full_answer)} chars")

                yield {'type': 'status', 'content': 'Verifying response...'}
                refined_answer = self.verify_and_refine_response(full_answer, query, query_type)

                if refined_answer != full_answer:
                    yield {'type': 'status', 'content': 'Response refined'}

                sources = []
                for i, result in enumerate(github_results[:5], 1):
                    metadata = result.get('metadata', {})
                    # Handle both file_path and file fields
                    file_path = metadata.get('file_path') or metadata.get('file') or 'unknown'
                    # Handle both type and source_type fields
                    chunk_type = metadata.get('type') or metadata.get('source_type') or metadata.get('chunk_type') or 'unknown'
                    sources.append({
                        'rank': i,
                        'file': file_path,
                        'type': chunk_type,
                        'score': result.get('score', 0.0),
                        'chunk_id': metadata.get('chunk_id', '')
                    })

                emails = []
                for email in gmail_results:
                    metadata = email.get('metadata', {})
                    emails.append({
                        'subject': metadata.get('subject', ''),
                        'from': metadata.get('from', ''),
                        'date': metadata.get('date', ''),
                        'relevance': email.get('relevance_score', 0)
                    })

                self.history.append({'role': 'user', 'content': query})
                self.history.append({'role': 'assistant', 'content': refined_answer})

                context_quality = min(github_results[0].get('score', 0), 1.0) if github_results else 0.0

                self.logger.info(f"RESPONSE COMPLETE | Quality: {context_quality:.2f}")
                self.logger.info("=" * 80)

                result = {
                        'answer': refined_answer,
                        'sources': sources,
                        'chunks_retrieved': len(github_results),
                        'query_type': query_type,
                        'context_quality': context_quality,
                        'emails': emails,
                        'has_diagram': bool(re.search(r'```mermaid', refined_answer or '')),
                        'related_knowledge': None,
                        'is_metrics_query': False,
                        'chronological_entity': f"{chrono_query['order']} {chrono_query['type']} #{chrono_result['number']}"
                    }

                yield {
                    'type': 'complete',
                    'content': {
                        'answer': refined_answer,
                        'sources': sources,
                        'chunks_retrieved': len(github_results),
                        'query_type': query_type,
                        'context_quality': context_quality,
                        'emails': emails,
                        'has_diagram': bool(re.search(r'```mermaid', refined_answer or '')),
                        'related_knowledge': None,
                        'is_metrics_query': False,
                        'chronological_entity': f"{chrono_query['order']} {chrono_query['type']} #{chrono_result['number']}"
                    }
                }
                return

        if self.verbose:
            print(f"Query Type: {query_type}")

        yield {'type': 'status', 'content': 'Searching codebase...'}

        entity = self.extract_entity_from_query(expanded_query, query_type)
        keywords = self.extract_keywords(expanded_query)

        metrics_context = None
        if query_type in [QueryType.REPOSITORY_METRICS, QueryType.TECH_STACK, QueryType.CODE_STRUCTURE]:
            if self.repo_metrics:
                metrics_context = self.build_metrics_context()
                yield {'type': 'status', 'content': 'Loading repository metrics...'}
            else:
                yield {
                    'type': 'complete',
                    'content': {
                        'answer': ("Repository metrics are not available.\n\n"
                                   "To enable metrics-based queries, ensure aggregated_tech_stack_summary.json "
                                   "exists in the DataProcessing directory."),
                        'sources': [],
                        'chunks_retrieved': 0,
                        'query_type': query_type,
                        'context_quality': 0.0,
                        'has_diagram': False,
                        'emails': [],
                        'is_metrics_query': True
                    }
                }
                return

        if self.enable_multi_query and query_type not in [QueryType.REPOSITORY_METRICS, QueryType.TECH_STACK,
                                                          QueryType.CODE_STRUCTURE]:
            yield {'type': 'status', 'content': 'Optimizing search queries...'}
            queries = self.generate_multi_queries(expanded_query, query_type)

            github_results = self.retrieve_with_multi_query(
                queries, query_type, entity, keywords
            )
        else:
            query_embedding = self.get_query_embedding(expanded_query)
            github_results = self.retrieve_github_first(
                query_embedding, query_type, entity, keywords, query_text=expanded_query
            )

        if github_results:
            yield {'type': 'status', 'content': f'Found {len(github_results)} relevant code chunks'}

        query_embedding = self.get_query_embedding(expanded_query)
        gmail_results = self.retrieve_gmail_correlated(
            github_results, query_embedding, keywords
        )

        if gmail_results:
            yield {'type': 'status', 'content': f'Found {len(gmail_results)} related emails'}

        context = self.build_context_from_chunks(github_results, query_type) if github_results else ""
        email_context = self.build_email_context(gmail_results) if gmail_results else ""

        system_prompt = self.get_dynamic_system_prompt(query_type, expanded_query, role=role)
        user_prompt = self.build_user_prompt(
            expanded_query, context, email_context, query_type, entity, metrics_context
        )

        yield {'type': 'status', 'content': 'Generating response...'}

        full_answer = ""
        buffer = ""
        for chunk in self.call_llm_stream(system_prompt, user_prompt):
            full_answer += chunk
            buffer += chunk

            if '\n' in buffer or len(buffer) > 150:
                yield {'type': 'chunk', 'content': buffer}
                buffer = ""

        if buffer:
            yield {'type': 'chunk', 'content': buffer}

        self.logger.info(f"LLM GENERATION | Completed streaming, Length: {len(full_answer)} chars")

        yield {'type': 'status', 'content': 'Verifying response...'}
        refined_answer = self.verify_and_refine_response(full_answer, query, query_type)

        if refined_answer != full_answer:
            yield {'type': 'status', 'content': 'Response refined'}

        sources = []
        if github_results:
            for i, result in enumerate(github_results[:5], 1):
                metadata = result.get('metadata', {})
                sources.append({
                    'rank': i,
                    'file': metadata.get('file_path', 'unknown'),
                    'type': metadata.get('type', 'unknown'),
                    'score': result.get('score', 0.0),
                    'chunk_id': metadata.get('chunk_id', '')
                })

        emails = []
        for email in gmail_results:
            metadata = email.get('metadata', {})
            emails.append({
                'subject': metadata.get('subject', ''),
                'from': metadata.get('from', ''),
                'date': metadata.get('date', ''),
                'relevance': email.get('relevance_score', 0)
            })

        self.history.append({'role': 'user', 'content': query})
        self.history.append({'role': 'assistant', 'content': refined_answer})

        if metrics_context:
            context_quality = 1.0
        elif github_results and len(github_results) > 0:
            top_score = max((r.get('score', 0) for r in github_results), default=0.0)
            context_quality = min(top_score, 1.0)
        else:
            context_quality = 0.0

        self.logger.info(f"RESPONSE COMPLETE | Quality: {context_quality:.2f}")
        self.logger.info("=" * 80)

        yield {
            'type': 'complete',
            'content': {
                'answer': refined_answer,
                'sources': sources,
                'chunks_retrieved': len(github_results) if github_results else 0,
                'query_type': query_type,
                'context_quality': context_quality,
                'emails': emails,
                'has_diagram': bool(re.search(r'```mermaid', str(refined_answer or ''))),
                'related_knowledge': None,
                'is_metrics_query': query_type in [
                    QueryType.REPOSITORY_METRICS,
                    QueryType.TECH_STACK,
                    QueryType.CODE_STRUCTURE
                ]
            }
        }


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
            if chatbot.query_rewriter and chatbot.query_rewriter.semantic_cache:
                cache_stats = chatbot.query_rewriter.semantic_cache.get_stats()
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
