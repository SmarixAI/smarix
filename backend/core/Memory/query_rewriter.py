from typing import List, Dict, Any, Optional
import json
import time
import logging
import re
from core.Memory.conversation_store import ConversationStore
from .redis_context_cache import RedisContextCache
from .redis_response_cache import RedisResponseCache
from .simple_semantic_cache import SimpleSemanticCache

logger = logging.getLogger(__name__)


class LLMQueryRewriter:
    def __init__(
        self,
        conversation_store: ConversationStore,
        llm_client=None,
        redis_client=None,
        embedding_function=None,
    ):
        self.conversation_store = conversation_store
        self.llm_client = llm_client
        self.redis_cache = RedisContextCache(redis_client) if redis_client else None
        self.response_cache = (
            RedisResponseCache(redis_client, ttl=3600) if redis_client else None
        )

        # NOTE: cache_failures=False so "no context" answers are not reused semantically.
        self.semantic_cache = (
            SimpleSemanticCache(
                redis_client=redis_client,
                embedding_function=embedding_function,
                dimension=1536,
                exact_threshold=0.98,
                high_threshold=0.85,
                medium_threshold=0.75,
                low_threshold=0.65,
                ttl=604800,
                max_cache_size=10000,
                cache_failures=False,
            )
            if redis_client and embedding_function
            else None
        )

        if self.semantic_cache:
            logger.info("Simple Semantic Cache enabled (embedding-based)")

    # OPTIONAL: helper if you want to check cache before full RAG in your app
    def try_semantic_cache(
        self, query: str, session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Try to resolve the query via semantic cache.
        Returns a response dict or None if cache miss / low confidence.
        """
        if not self.semantic_cache or not session_id:
            return None

        cached = self.semantic_cache.get(query, session_id)
        if not cached:
            return None

        # If cache suggests generation/augmentation, let upper layers handle it.
        if cached.get("_requires_generation") or cached.get("_requires_augmentation"):
            return None

        return cached

    def rewrite(self, raw_query: str, session_id: str, schema_name: str) -> str:
        if not session_id:
            return raw_query

        # Check Redis cache FIRST (cheapest operation, no DB needed)
        if self.redis_cache:
            cached = self.redis_cache.get_rewritten_query(session_id, raw_query)
            if cached:
                logger.info(f"REWRITE CACHE HIT | {cached[:50]}...")
                return cached

        # Now fetch messages once for both self_contained check and context building
        try:
            messages = self.conversation_store.get_messages(session_id, schema_name=schema_name, limit=6)
        except Exception:
            return raw_query

        if len(messages) < 2:
            return raw_query

        if self._is_self_contained(raw_query, session_id=session_id, messages=messages):
            return raw_query

        session_context = self._format_session_context(messages)
        rewritten_query = self._call_llm_rewriter(raw_query, session_context)

        if self.redis_cache and rewritten_query and rewritten_query != raw_query:
            self.redis_cache.set_rewritten_query(session_id, raw_query, rewritten_query)
            logger.info(f"REWRITE CACHED | session={session_id[:8]}")

        return rewritten_query if rewritten_query else raw_query

    def _is_self_contained(self, query: str, session_id: str = None, schema_name: str = None, messages: list = None) -> bool:
        q = query.strip()
        query_lower = q.lower()

        has_pr_ref = bool(re.search(r"\bpr[#\s-]?\d+|\bpull request[#\s-]?\d+", query_lower))
        has_issue_ref = bool(re.search(r"\bissue[#\s-]?\d+|\bbug[#\s-]?\d+", query_lower))

        if len(q.split()) >= 20:
            return True

        if any(word in query_lower for word in ["architecture", "structure", "overview", "diagram"]):
            return True

        tech_words = len(re.findall(r"\b(py|js|db|api|service|plugin|function|class|module)\b", query_lower))
        if tech_words >= 3:
            return True

        context_indicators = [
            "it", "this", "that", "these", "those", "they", "them",
            "what about", "how about", "tell me more", "explain", "also",
            "and", "but", "more details", "elaborate", "same", "similar",
            "related", "another", "there",
        ]
        if any(indicator in query_lower for indicator in context_indicators):
            logger.info(f"NEEDS CONTEXT | Conversational indicator: '{q[:60]}'")
            return False

        question_starters = ("what", "how", "why", "when", "where", "can you", "could you", "is", "are", "does", "do", "did")
        if query_lower.startswith(question_starters) and len(q.split()) <= 8:
            if has_pr_ref or has_issue_ref:
                logger.info(f"NEEDS CONTEXT | Short PR/issue question: '{q[:60]}'")
                return False
            logger.info(f"NEEDS CONTEXT | Short question: '{q[:60]}'")
            return False

        # Use pre-fetched messages if available, avoid DB call
        if session_id:
            try:
                recent_messages = messages if messages is not None else self.conversation_store.get_messages(
                    session_id, schema_name=schema_name, limit=4
                )
                if recent_messages:
                    recent_queries = [
                        msg.get("content", "").lower()
                        for msg in recent_messages
                        if msg.get("role") == "user"
                    ]
                    query_words = set(query_lower.split())
                    for recent_q in recent_queries[-2:]:
                        recent_words = set(recent_q.split())
                        if not query_words or not recent_words:
                            continue
                        overlap = len(query_words & recent_words) / len(query_words | recent_words)
                        if overlap >= 0.70:
                            logger.info(f"SKIP REWRITING | Very similar to recent (overlap={overlap * 100:.0f}%)")
                            return True
            except Exception as e:
                logger.debug(f"Could not check recent queries: {e}")

        if (has_pr_ref or has_issue_ref) and len(q.split()) >= 6:
            logger.info(f"SELF-CONTAINED | Specific PR/issue query: '{q[:60]}'")
            return True

        return False

    def _format_session_context(self, messages: List[Dict[str, Any]]) -> str:
        context_parts = []
        # Last few turns are usually most relevant.
        for msg in messages[-4:]:
            role = msg.get("role", "unknown").title()
            content = msg.get("content", "")[:300]
            context_parts.append(f"{role}: {content}")
        return "\n".join(context_parts[-8:])

    def _call_llm_rewriter(self, query: str, session_context: str) -> Optional[str]:
        prompt = f"""You are an expert code search assistant. Rewrite the user query to be more specific using ONLY the conversation context below.

CONVERSATION CONTEXT:
{session_context}

USER QUERY: {query}

TASK:
Rewrite the query to include specific technical context from the conversation.
- Keep it concise (under 30 words)
- ONLY use terms from the conversation context
- Make it more searchable for code chunks
- If the query has pronouns (it, this, that, they), replace them with specific terms
- If the query is a follow-up question, incorporate the previous topic (PR numbers, files, functions, etc.)
- If no relevant context, return the original query unchanged

REWRITTEN QUERY:"""

        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=50,
            )

            rewritten = response.choices[0].message.content.strip()

            if "REWRITTEN QUERY:" in rewritten:
                rewritten = rewritten.split("REWRITTEN QUERY:")[-1].strip()

            # Ensure rewrite is not just a truncated or lower-information version.
            if len(rewritten) >= len(query) * 0.8:
                return rewritten
            return None

        except Exception as e:
            logger.warning(f"LLM rewrite failed: {e}")
            return None
