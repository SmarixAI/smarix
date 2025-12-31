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
            embedding_function=None
    ):
        self.conversation_store = conversation_store
        self.llm_client = llm_client
        self.redis_cache = RedisContextCache(redis_client) if redis_client else None
        self.response_cache = RedisResponseCache(redis_client, ttl=3600) if redis_client else None

        self.semantic_cache = SimpleSemanticCache(
            redis_client=redis_client,
            embedding_function=embedding_function,
            dimension=1536,
            exact_threshold=0.98,
            high_threshold=0.85,
            medium_threshold=0.75,
            low_threshold=0.65,
            ttl=604800,
            max_cache_size=10000
        ) if redis_client and embedding_function else None

        if self.semantic_cache:
            logger.info("Simple Semantic Cache enabled (embedding-based)")
        else:
            logger.warning("Semantic cache disabled (missing redis or embedding function)")

    def rewrite(self, raw_query: str, session_id: str) -> str:
        if not session_id:
            return raw_query

        if self._is_self_contained(raw_query, session_id):
            return raw_query

        if self.redis_cache:
            cached = self.redis_cache.get_rewritten_query(session_id, raw_query)
            if cached:
                logger.info(f"REWRITE CACHE HIT | {cached[:50]}...")
                return cached

        try:
            messages = self.conversation_store.get_messages(session_id, limit=6)
        except:
            return raw_query

        if len(messages) < 2:
            return raw_query

        session_context = self._format_session_context(messages)
        rewritten_query = self._call_llm_rewriter(raw_query, session_context)

        if self.redis_cache and rewritten_query and rewritten_query != raw_query:
            self.redis_cache.set_rewritten_query(session_id, raw_query, rewritten_query)
            logger.info(f"REWRITE CACHED | session={session_id[:8]}")

        return rewritten_query if rewritten_query else raw_query

    def _is_self_contained(self, query: str, session_id: str = None) -> bool:
        query_lower = query.lower()

        # Check for specific identifiers (always self-contained)
        if any(pattern in query_lower for pattern in ['#', 'pr #', 'issue #', 'pr-', 'issue-']):
            return True

        # Check for architecture/overview queries
        if any(word in query_lower for word in ['architecture', 'structure', 'overview', 'diagram']):
            return True

        # Check for technical complexity
        tech_words = len(re.findall(r'\b(py|js|db|api|service|plugin|function)\b', query_lower))
        if tech_words >= 2:
            return True

        # Long queries are likely self-contained
        if len(query.split()) >= 8:
            return True

        # Check for conversational indicators (NEEDS CONTEXT)
        context_indicators = [
            'it', 'this', 'that', 'these', 'those', 'they', 'them',
            'what about', 'how about', 'tell me more', 'explain',
            'also', 'and', 'but', 'more details', 'elaborate',
            'same', 'similar', 'related', 'another', 'there'
        ]

        if any(indicator in query_lower for indicator in context_indicators):
            logger.info(f"NEEDS CONTEXT | Query contains conversational indicator: '{query[:60]}'")
            return False

        # Check for question continuations (short questions need context)
        question_starters = ('what', 'how', 'why', 'when', 'where', 'can you', 'could you', 'is', 'are', 'does')
        if query_lower.startswith(question_starters):
            if len(query.split()) <= 6:
                logger.info(f"NEEDS CONTEXT | Short question likely needs context: '{query[:60]}'")
                return False

        # Session-based similarity check (INCREASED threshold)
        if session_id:
            try:
                recent_messages = self.conversation_store.get_messages(session_id, limit=4)

                if recent_messages:
                    recent_queries = [
                        msg.get('content', '').lower()
                        for msg in recent_messages
                        if msg.get('role') == 'user'
                    ]

                    query_words = set(query_lower.split())

                    # Only check last 2 queries (not 3)
                    for recent_q in recent_queries[-2:]:
                        recent_words = set(recent_q.split())

                        if not query_words or not recent_words:
                            continue

                        overlap = len(query_words & recent_words) / len(query_words | recent_words)

                        # INCREASED from 0.40 to 0.70 - only skip if VERY similar
                        if overlap >= 0.70:
                            logger.info(f"SKIP REWRITING | Query very similar to recent (overlap={overlap * 100:.0f}%)")
                            return True

            except Exception as e:
                logger.debug(f"Could not check recent queries: {e}")
                pass

        # Default: query likely needs context
        return False

    def _format_session_context(self, messages: List[Dict[str, Any]]) -> str:
        context_parts = []
        for msg in messages[-4:]:
            role = msg.get('role', 'unknown').title()
            content = msg.get('content', '')[:300]
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
- If query has pronouns (it, this, that, they), replace them with specific terms
- If query is a follow-up question, incorporate the previous topic
- If no relevant context, return the original query unchanged

EXAMPLE:
Context: "Added Redis caching for super-employee backend using redis-py v4.2"
Query: "Fix Redis"
→ "Fix Redis caching issue in super-employee backend using redis-py v4.2"

Context: "User: What is the authentication system? Assistant: We use JWT-based authentication with Redis session storage."
Query: "How does it work?"
→ "How does JWT-based authentication with Redis session storage work?"

REWRITTEN QUERY:"""

        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=50
            )

            rewritten = response.choices[0].message.content.strip()

            if "REWRITTEN QUERY:" in rewritten:
                rewritten = rewritten.split("REWRITTEN QUERY:")[-1].strip()

            return rewritten if len(rewritten) > len(query) * 0.8 else None

        except Exception as e:
            logger.warning(f"LLM rewrite failed: {e}")
            return None
